---
created: 2026-02-15
modified: 2026-11-04
version: 10.2
status: Draft
---

# Actuation Components

## 1. Overview

This document details the actuation subsystem components for the Epicura kitchen robot prototype, including the electric heating unit, servo stirring arm, and ingredient dispensing mechanisms. Actuators are split across the three units: the heating unit, safety relay, exhaust fans and the stir-motor port are driven by the Cooking Surface Controller (CSC, STM32G0B1RE) in the Cooking Surface (CS); the stirring servo sits in the Stirring Unit (SU) on the only inter-unit cable (J_SU); the dispensers, pumps, solenoids and load cells are in the Dispensing Unit (DU) and are driven directly by the RV1106 on the Unified PCB v4.0.

## 2. Actuation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Actuation Subsystem                          │
│                                                                 │
│  COOKING SURFACE (CS) — CSC (STM32G0B1RE)                       │
│  ┌──────────────┐ FDCAN2 + ┌──────────────┐  ┌──────────────┐   │
│  │  STM32G0B1RE │ 24V sw   │  J_SU (right │─►│  24V CAN     │   │
│  │  (CSC)       │─────────►│  pillar)     │  │  Servo (SU)  │   │
│  │              │          └──────────────┘  └──────────────┘   │
│  │              │── GPIO  ►┌──────────────┐    ┌────────────┐   │
│  │              │  Q_RLY   │  Relay       │───►│ Heating    │   │
│  │              │          │  (AC cut)    │    │ unit 1300W │   │
│  │              │          └──────────────┘    └────────────┘   │
│  │              │── PWM   ► Exhaust fans ×2 (12 V, J_FAN)       │
│  └──────┬───────┘                                               │
│  FDCAN1 │ ISO1050 #1 ◄── isolated CAN 500 kbps ──► heating unit │
│ ════════╪════════ J_DOCK (8-pin pogo: DOCK_24V + CAN) ════════  │
│  DISPENSING UNIT (DU) — Unified PCB v4.0 (RV1106)               │
│  ┌──────────────┐── I2C3 ►┌──────────────┐  ┌──────────────┐    │
│  │  RV1106      │ PCA9685 │  DSB: FID x3 │─►│ Carousels    │    │
│  │  (dispense   │  + OE   │  + CID x1    │  │ (FID + CID)  │    │
│  │   thread)    │         └──────────────┘  └──────────────┘    │
│  │              │── PWM  ►┌──────────────┐                      │
│  │              │ +PCF8574│  SLD: Pump x2│  6V_DSP rail         │
│  │              │   #2    │  + Solenoid x2│ (MP1584EN #2)       │
│  │              │         └──────────────┘                      │
│  │              │── I2C3 ► NAU7802 ×2 ◄── 2 kg load cells       │
│  └──────────────┘ TCA9543A                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component List

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Electric Heating Unit (rice-cooker class, 1,300 W assumed, CAN) | Commercial unit, TBD | 1 | $45.00 | $45.00 | Supplier TBD | Self-contained unit with heating plate, centre sensor, own PID and CAN bus port; replaces the induction surface (2026-11-04); no teardown needed |
| 24V CAN Servo Motor (stirring) | CyberGear/RobStride-class integrated BLDC servo, ≥ 3 N·m continuous, CAN 1 Mbps (model TBD) | 1 | $45.00 | $45.00 | AliExpress / Robstride | Main stirring arm in the Stirring Unit (SU); encoder feedback, velocity + position modes; on the CSC's regular CAN port (STM32 FDCAN2) with switched 24 V, reached through J_SU in the right pillar |
| SN65HVD230 CAN Transceiver (stir-motor port) | SN65HVD230DR (SOIC-8) | 1 | $0.90 | $0.90 | TI / LCSC | Non-isolated 3.3 V transceiver on STM32 FDCAN2 → J_CAN_STIR; on the CSC |
| Stir-Motor Bus Passives + 24 V Switch | 120Ω, PESD1CAN, AO4407A + 2N7002, 5 A polyfuse | 1 lot | $0.30 | $0.30 | LCSC | Termination/ESD at J_CAN_STIR; Q_STIR high-side switch (STM32 PB4) → J_STIR_PWR, costed with CSC passives |
| Stirring-Unit Port (J_SU) | Molex Micro-Fit 3.0, 5-way receptacle + plug (24V_STIR, GND, CAN_H, CAN_L, SHIELD) | 1 pair | $2.00 | $2.00 | Molex / Mouser | The only inter-unit cable: CS right pillar → SU; harness inside the pillar bundles J_CAN_STIR + J_STIR_PWR from the CSC |
| Dispenser Servo (DSB) — FID x3 + CID x1 | DS3218-class, 270°, 20 kg·cm, metal gear | 4 | $10.00 | $40.00 | AliExpress | C1 CID index, F1 FID index, F2 FID dose, F3 FID steam gate; one part number; all on 6.0 V directly (D_DSB4 dropped) |
| PCA9685 16-ch PWM Servo Driver — DSB | PCA9685PW (TSSOP-28) | 1 | $1.50 | $1.50 | LCSC / Mouser | RV1106 I2C3 addr 0x41, CH0-CH3 used, OE → RV1106 GPIO (10k pull-up, servos off at boot); on the Unified PCB v4.0 |
| DSB 6.0 V Rail Parts (6V_DSP) | AO3401 P-MOSFET + 3 A PTC + 1000 µF | 1 lot | $1.00 | $1.00 | LCSC | Switched dispenser rail from MP1584EN #2 (Q_DSB, PCF8574 #2 P4); also feeds the TB6612 pumps and the solenoids; off when idle |
| FID Canisters (6x, PP, ¼ tsp measure wheel) | Custom 60mL, food-grade PP | 6 | $3.00 | $18.00 | Custom/3D print | Threaded cap + O-ring + desiccant; rotary 1.23 mL pocket in base, blade coupling |
| FID Carousel Ring + Dosing Station | Custom, 6 bays, Ø170 mm | 1 | $8.00 | $8.00 | Custom/3D print | Ring gear, F2 coupling, steam-gate flap, removable chute |
| CID Carousel Ring (5 bins + cover, 200 mL) | Custom, food-grade PP/PETG, Ø230 mm | 1 | $8.00 | $8.00 | Custom/3D print | Lift-off, keyed hub, ring gear |
| CID Base Plate + Drop Chute | Custom | 1 | $4.00 | $4.00 | Custom/3D print | Fixed plate with 50° rear aperture; removable for washing |
| Index Gear Pairs (4:3 gear-up) | POM or printed spur gears, 32T/24T | 2 | $1.00 | $2.00 | Custom/3D print | Servo 225° → carousel 300° (CID + FID) |
| Carousel Bearings (thin-section) | 6808-2RS or equiv. | 2 | $2.00 | $4.00 | AliExpress | One per carousel hub |
| 6V Peristaltic Pump — SLD | Generic 6V DC gear motor | 2 | $10.00 | $20.00 | Amazon / AliExpress | SLD liquid dispensing (oil + water); on the 6V_DSP rail via TB6612FNG, speed from RV1106 PWM, direction via PCF8574 #2 P3/P5 |
| 6V NC Solenoid Valve — SLD | Generic 6V, normally closed | 2 | $4.00 | $8.00 | Amazon / AliExpress | SLD drip prevention; 6V_DSP rail, IRLML6344 low-side via PCF8574 #2 P0/P1 |
| 2 kg Load Cell — SLD (oil) | Generic 2 kg strain gauge | 1 | $5.00 | $5.00 | Amazon | SLD oil reservoir closed-loop metering + level alert; read by NAU7802 #1 |
| 2 kg Load Cell — SLD (water) | Generic 2 kg strain gauge | 1 | $5.00 | $5.00 | Amazon | SLD water reservoir closed-loop metering + level alert; read by NAU7802 #2 |
| NAU7802 24-bit Load-Cell ADC — SLD | NAU7802SGI (SOP-16) | 2 | $2.00 | $4.00 | Nuvoton / LCSC | Replace the HX711 bit-bang; I2C3 addr 0x2A, one per TCA9543A channel, kernel `nau7802` (IIO), 10 Hz closed loop in the RV1106 `dispense` thread; on the Unified PCB v4.0 |
| TCA9543A I2C Mux — SLD | TCA9543APWR (TSSOP-14) | 1 | $1.00 | $1.00 | TI / LCSC | Addr 0x71 on RV1106 I2C3; separates the two fixed-address NAU7802s; kernel `i2c-mux-pca954x` |
| PCF8574 #2 I2C GPIO Expander — SLD/rail/charger | PCF8574 (SOIC-16) | 1 | $0.50 | $0.50 | LCSC / Mouser | RV1106 I2C3, addr 0x21: P0/P1 solenoids, P2 status LED, P3/P5 pump direction, P4 6V_DSP rail enable, P6/P7 TP5100 CHRG/STDBY (in); on the Unified PCB v4.0 |
| ISO1050DUB #1 (isolated CAN transceiver, STM32 node) | ISO1050DUBR | 1 | $3.50 | $3.50 | TI / Mouser | 5 kV RMS galvanic isolation, SOIC-8; on the CSC's isolated CAN port (J_CAN_HEAT + J_DOCK pins 3–6), 5V_ISO/GND_ISO from the B0505S-1WR3 on the CSC; 3-node bus shared with the RV1106 (ISO1050DUB #2 + MCP2518FD on the Unified PCB v4.0, costed under Compute) and the heating unit |
| CAN Termination + Decoupling | 120Ω + MLCC caps | 1 lot | $0.13 | $0.13 | LCSC | CAN bus passives on the CSC (R_TERM1 at J_CAN_HEAT, PESD1CAN); the dock → Unified PCB run is an unterminated stub ≤ 30 cm |
| Relay Module (5V, 10A) | SRD-05VDC-SL-C | 2 | $3.00 | $6.00 | Amazon | Heater on/off and power cycling control (prototype); driven from the CSC Q_RLY (STM32 PB0) via J_SAFE |
| Motor Driver Board | L298N or custom | 1 | $8.00 | $8.00 | Amazon | Servo power distribution and level shifting |
| Power Connectors (XT60) | XT60 male+female | 4 | $1.00 | $4.00 | Amazon | High-current connections for heater and servo power |
| Wiring Harness (18AWG silicone) | 18AWG, 5m assorted | 1 lot | $10.00 | $10.00 | Amazon | Internal wiring; silicone insulation for heat resistance |
| Servo Extension Cables (300mm) | 300mm JR/Futaba | 4 | $1.00 | $4.00 | Amazon | DSB servo wiring to J_DSB1-4 headers |
| Exhaust Fan (60mm, PWM) | Noctua NF-A6x25 or generic | 1 | $8.00 | $8.00 | Amazon | 4-pin PWM, 12V, fume extraction; J_FAN on the CSC (CS rear, 12 V from MP1584EN #1) |
| Grease Mesh + Carbon Filter | 304 SS mesh + coconut carbon | 1 set | $8.00 | $8.00 | Amazon / AliExpress | Dual-stage filtration cartridge |
| Filter Housing + Duct | 3D printed ABS + sheet metal | 1 | $6.00 | $6.00 | Self-fabricated | Slide-out cartridge + 60mm duct |
| Fan MOSFET (PWM driver) | IRLML6344 + SS14 (per channel) | 1 lot | $0.50 | $0.50 | LCSC | Logic-level low-side switches on the CSC (STM32 PA6 TIM3_CH1, PB10) |
| Piezo Buzzer (5V, PWM) | MLT-5030 or generic | 1 | $0.80 | $0.80 | Amazon / Mouser | Audio feedback for alerts, errors, task completion; in the DU on 5V_MAIN, driven by an RV1106 PWM |
| Buzzer MOSFET | 2N7002 (SOT-23) | 1 | $0.05 | $0.05 | LCSC | Logic-level gate for the RV1106 buzzer PWM (Unified PCB v4.0) |

---

## 4. Cost Summary

| Item | Cost |
|------|------|
| Electric Heating Unit (rice-cooker class, CAN) | $45.00 |
| 24V CAN Servo Motor (main arm) | $45.00 |
| SN65HVD230 + stir-bus passives (CSC) | $1.20 |
| Dispenser Servos — DSB (4x) | $40.00 |
| PCA9685 + DSB 6.0 V Rail Parts | $2.50 |
| FID Canisters (6x) | $18.00 |
| FID Carousel Ring + Dosing Station | $8.00 |
| CID Carousel Ring + Base Plate + Chute | $12.00 |
| Index Gears + Carousel Bearings | $6.00 |
| Peristaltic Pumps — SLD (2x, 6 V) | $20.00 |
| Solenoid Valves — SLD (2x, 6 V NC) | $8.00 |
| Load Cells — SLD (2×, 2 kg) | $10.00 |
| NAU7802 ×2 + TCA9543A — SLD | $5.00 |
| PCF8574 #2 I2C GPIO Expander (SLD/rail/charger) | $0.50 |
| ISO1050DUB #1 (isolated CAN transceiver, CSC) | $3.50 |
| CAN Termination + Decoupling | $0.13 |
| Relay Module (safety, 2x) | $6.00 |
| Motor Driver Board | $8.00 |
| Connectors + Wiring (XT60, J_SU pair, harness, servo cables) | $20.00 |
| Exhaust Fan + Filtration | $22.50 |
| Piezo Buzzer + MOSFET | $0.85 |
| **Category Subtotal** | **$282.18** |

---

## 5. Design Notes

### 5.1 Electric Heating Unit Strategy
- **Both Prototype and Production:** Commercial electric heating unit of the premium rice-cooker class with CAN bus port (replaces the induction surface, 2026-11-04; same CAN contract, no controller change)
  - Self-contained unit: resistive heating plate, spring-loaded centre temperature sensor, relay/triac mains power stage, safety circuits; any flat-bottomed pot
  - RV1106 sends temperature setpoints (HEAT_SET_TEMP) or power levels (HEAT_SET_POWER) via CAN 2.0B at 500 kbps on the shared isolated bus; the unit runs its own temperature loop on its centre sensor (no IR thermometer in Epicura); the STM32 can force the unit off (HEAT_ON_OFF=0)
  - No custom mains power electronics needed
  - Safety relay on AC mains (CSC Q_RLY → J_SAFE) provides system-level hard disconnect; the hard E-stop button is on the CS front, wired to the CSC
  - Unit-internal pot detection (centre sensor, `pot_detected`) and thermal cutoff
  - Lifting the DU opens the bus and the dock 24 V together: the unit drops to zero ≤ 1 s on keep-alive loss and the STM32 holds safe on DOCK_SENSE_B (fault 0x17 DU_UNDOCKED, not an E_STOP)

### 5.2 24V CAN Servo Motor Selection
- **≥ 3 N·m (30 kg-cm) continuous torque** provides ample margin for thick curries and dals; current limit set in the motor
- **Integrated BLDC + planetary gearbox + encoder + driver** in one housing; true continuous rotation
- **CAN interface (1 Mbps)** on the CSC's regular CAN port (STM32 FDCAN2, SN65HVD230, 120 Ω at J_CAN_STIR + in the motor): velocity mode for stirring, position mode for parking; feedback of rpm, angle, current and temperature replaces the FG tachometer, Hall homing and INA219 stall heuristic
- **Switched 24V** from Q_STIR on the CSC (STM32 PB4, F_STIR 5 A → J_STIR_PWR); J_CAN_STIR + J_STIR_PWR are bundled into one harness inside the right pillar ending at J_SU (Micro-Fit 3.0, 5-way), the only cable between units; motor command timeout ≤ 500 ms configured at start-up
- **Specific model TBD** — document generically as "24V integrated CAN servo, ≥ 3 N·m, 1 Mbps CAN" (CyberGear/RobStride-class or industrial equivalent)

### 5.3 Dispenser Servo Block (FID + CID)
- **One control block for both carousels**: 4× identical DS3218-class 270° servos on a PCA9685 (RV1106 I2C3, 0x41), OE on an RV1106 GPIO, switched 6.0 V rail (6V_DSP) from MP1584EN #2 on the Unified PCB v4.0; the whole block is in the DU and is driven by the RV1106 `dispense` thread, not the STM32
- **FID**: 6-canister carousel; F1 indexes (4:3 gear-up, 60° per box), F2 drives the selected canister's integral ¼ tsp (1.23 mL) measure wheel through a blade coupling, F3 opens a spring-closed steam gate only while dosing
- **CID**: 5-slot + cover carousel on a fixed base plate with one rear aperture; C1 indexes a slot over the aperture and its contents free-fall into the pot (ascending slot order)
- **No sensors in the block**: servos are open loop; stall/jam detected by the INA219 #1 current window on the 6V_DSP rail (> 2.5 A for 300 ms) + 3 s move timeout in the RV1106 `dispense` thread; anti-bridging by servo jiggle in software
- **BOM cost**: ~$86.50 for both dispensers (vs ~$127.50 for P-ASD pneumatics + CID stepper/linear actuator) — net −$40 and 9 freed STM32/expander pins

### 5.5 SLD Peristaltic Pumps (×2) + Solenoid Valves (×2)
- Peristaltic: fluid only touches food-grade silicone tubing (no contamination)
- Pumps re-specified to 6 V DC so they share the switched 6V_DSP rail with the servos (TB6612FNG, RV1106 PWM); flow rate 5–50 mL/min, adjustable via PWM motor speed
- Solenoid valves (6V NC, IRLML6344 low-side via PCF8574 #2) prevent dripping when pumps are off
- Dedicated 2 kg load cell per reservoir, read by a NAU7802 24-bit I2C ADC (one per TCA9543A mux channel) at 10 Hz by the RV1106 for closed-loop liquid metering (±5%, stop at 95 % of target); reservoirs, pumps and nozzles are on the DU sides and underside

### 5.6 Production Cost Reduction

| Item | Prototype | Production (1000 qty) | Savings |
|------|-----------|----------------------|---------|
| Electric heating unit | $45 | $30 (bulk) | 33% |
| 24V CAN servo motor | $45 | $30 (bulk) | 33% |
| FID + CID servo carousels (4 servos, PCA9685, rings, canisters) | $86.50 | $45 (bulk, molded rings/canisters) | 48% |
| Peristaltic pumps x2 (SLD, 6 V) | $20 | $10 (bulk) | 50% |
| Solenoid valves x2 (SLD, 6 V NC) | $8 | $4 (bulk) | 50% |
| CAN transceiver (ISO1050DUB) | $3.50 (on the CSC) | $2.50 (bulk) | 29% |
| Wiring | $20 | $8 (harness) | 60% |

---

## 6. Related Documentation

- [[01-Compute-Module-Components|Compute Module Components]]
- [[03-Sensor-Components|Sensor Components]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]
- [[05-Exhaust-Fume-Management|Exhaust & Fume Management]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]

---

#epicura #components #actuation #bom

---

## 7. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-16 | Manas Pradhan | Replace ASD (3× SG90 servo hoppers) with P-ASD pneumatic puff-dosing system (pump + 6× solenoid valves + sealed cartridges) |
| 3.0 | 2026-02-16 | Manas Pradhan | Added PCF8574 I2C GPIO expander ($0.50) for P-ASD solenoid control |
| 4.0 | 2026-02-20 | Manas Pradhan | Moved CAN transceiver (now ISO1050DUB) to Compute Modules; replaced with CAN termination + decoupling passives ($0.13); subtotal $289.85 → $286.98 |
| 5.0 | 2026-02-20 | Manas Pradhan | Moved ISO1050DUB ($3.50) back from Compute Modules to Actuation (now on Driver PCB); subtotal $286.98 → $290.48 |
| 6.0 | 2026-02-20 | Manas Pradhan | Replaced DS3225 servo ($15) with 24V BLDC motor w/ integrated ESC ($25); net +$10; subtotal $290.48→$300.48 |
| 7.0 | 2026-03-11 | Manas Pradhan | CID-1: replaced DC linear actuator ($8) + DRV8876 ($2.50) with NEMA 23 stepper ($15) + external driver ($10); CID-2 unchanged; limit switches 4→3; net +$14.00; subtotal $300.48→$314.48 |
| 8.0 | 2026-03-11 | Manas Pradhan | Added PCF8574 #2 ($0.50) for GPIO headroom; SLD solenoid gates now via PCF8574 #2 (0x21); subtotal $314.48→$314.98 |
| 9.0 | 2026-11-04 | Manas Pradhan | Replaced P-ASD pneumatic system ($90) + PCF8574 #1 ($0.50) and CID stepper/driver/linear actuator/DRV8876/limit switches ($37) with the Dispenser Servo Block: 4× DS3218-class servos ($40), PCA9685 + rail parts ($2.50), FID canisters ($18), FID/CID carousels, base plate, gears, bearings ($26); servo cables 3→4; net −$40.00; subtotal $314.98→$274.98 |
| 9.1 | 2026-11-04 | Manas Pradhan | ISO1050DUB row renamed #1 (STM32 node) on the 3-node isolated CAN bus; induction note: power commanded by the RV1106, STM32 off-switch only |
| 10.0 | 2026-11-04 | Manas Pradhan | 24V BLDC (PWM/EN/DIR, $25) replaced by a 24V CAN servo motor ($45) on the Unified PCB's regular CAN port; SN65HVD230 transceiver + stir-bus passives added ($1.20); induction note updated for module-internal temperature control; subtotal $274.98 → $296.18 |
| 10.1 | 2026-11-04 | Manas Pradhan | Three-unit split: stir-motor port (SN65HVD230, Q_STIR), ISO1050DUB #1 + B0505S, relay and fan drivers now on the CSC in the CS; dispensers, pumps, solenoids and load cells driven by the RV1106 on the Unified PCB v4.0 (6.0 V rail); pumps/solenoids re-specified 6 V (same price); 2× HX711 (−$6.00) replaced by 2× NAU7802 (+$4.00) + TCA9543A (+$1.00); J_SU Micro-Fit pair added (+$2.00); diagram redrawn; subtotal $296.18 → $297.18 |
| 10.2 | 2026-11-04 | Manas Pradhan | Heater changed from the Microwave Induction Surface ($60, bulk $40) to a commercial Electric Heating Unit of the rice-cooker class with own PID and CAN port ($45, bulk $30; 1,300 W assumed, unit TBD); same CAN contract, no controller change; §5.1 strategy rewritten, diagram and notes reworded; subtotal $297.18 → $282.18 |
