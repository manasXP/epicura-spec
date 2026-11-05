---
created: 2026-02-15
modified: 2026-11-05
version: 10.8
status: Draft
---

# Actuation Components

## 1. Overview

This document details the actuation subsystem components for the Epicura kitchen robot prototype, including the electric heating unit, servo stirring arm, and ingredient dispensing mechanisms. Actuators are split across the three units: the heating unit, safety relay, exhaust fans and the stir-motor port are driven by the Cooking Surface Controller (CSC, STM32G0B1RE) in the Cooking Surface (CS); the stirring servo sits in the Stirring Unit (SU) on the only inter-unit cable (J_SU); the dispensers, pumps, solenoids and load cells are in the Dispensing Unit (DU) and are driven by the DU STM32 (STM32G0B1RET6) on the Unified PCB v5.0, commanded by the RV1106 over the UART host link.

## 2. Actuation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Actuation Subsystem                          │
│                                                                 │
│  COOKING SURFACE (CS) — CSC (STM32G0B1RE)                       │
│  ┌──────────────┐ ISO CAN2 ┌──────────────┐  ┌──────────────┐   │
│  │  STM32G0B1RE │ +24V_SU  │  J_SU (right │─►│  24V CAN     │   │
│  │  (CSC)       │─────────►│  pillar)     │  │  Servo (SU)  │   │
│  │              │          └──────────────┘  └──────────────┘   │
│  │              │── GPIO  ►┌──────────────┐    ┌────────────┐   │
│  │              │  Q_RLY   │  K_SAFE relay│───►│ Heating    │   │
│  │              │          │  (AC cut)    │    │ unit 1300W │   │
│  │              │          └──────────────┘    └────────────┘   │
│  │              │── GPIO  ►┌──────────────┐    ┌────────────┐   │
│  │              │  Q_KSU   │  K_SU relay  │───►│ SU PSU     │   │
│  │              │          │  (AC cut)    │    │ LRS-75-24#2│   │
│  │              │          └──────────────┘    └────────────┘   │
│  │              │── PWM   ► Exhaust fans ×2 (12 V, J_FAN)       │
│  └──────┬───────┘                                               │
│  FDCAN1 │ ISO1050 #1 ◄── isolated CAN 500 kbps ──► heating unit │
│ ════════╪════════ J_DOCK (8-pin pogo: DOCK_24V + CAN) ════════  │
│  DISPENSING UNIT (DU) — Unified PCB v5.0 (RV1106 + DU STM32)    │
│  ┌───────┐UART ┌───────────┐── I2C1 ►┌────────────┐ ┌──────────┐│
│  │RV1106 │────►│ DU STM32  │ PCA9685 │ DSB: FID x3│►│ Carousels││
│  │(disp. │host │ G0B1RE    │  + OE   │  + CID x1  │ │(FID+CID) ││
│  │thread)│link │ (Dispense │         └────────────┘ └──────────┘│
│  └───────┘     │  task)    │── TIM3 ►┌────────────┐             │
│                │           │ +PCF8574│ SLD: Pump x2  6V_DSP rail│
│                │           │   #2    │ + Hall tachs (MP1584EN)  │
│                │           │         └────────────┘             │
│                │           │── GPIO ► Hall ×6 ◄ tank low/present│
│                └───────────┘ + pump tachs (robot-mop SLD)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component List

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Donor cooker: Philips OneChef NX5300/00 or equivalent (heating unit, controller, base body; its round 6 L pot and glass lid are not used) | NX5300/00 | 1 | $230.00 | $230.00 | Retail (₹19,995 MRP) | Heating plate (1,300 W assumed), centre sensor, own PID; air-fryer lid dropped; the OEM unit ships with a control board exposing HEAT_* on CAN (confirmed 2026-11-04; the retail board has no CAN and is not used); the pot (25 cm rounded-square + glass lid, $25) is costed in [[04-Total-Component-Cost]] §4 |
| 24V CAN Servo Motor (stirring) | CyberGear/RobStride-class integrated BLDC servo, ≥ 3 N·m continuous, CAN 1 Mbps (model TBD) | 1 | $45.00 | $45.00 | AliExpress / Robstride | Main stirring arm in the Stirring Unit (SU); encoder feedback, velocity + position modes; on the CSC's isolated CAN port #2 (STM32 FDCAN2, ISO1050DUB #3) with its own floating 24 V from the SU's LRS-75-24 #2 (AC cut by K_SU), reached through J_SU in the right pillar |
| ISO1050DUB #3 + B0505S-1WR3 #2 (stir-motor port, isolated CAN #2) | ISO1050DUBR (SOIC-8) + B0505S-1WR3 (SIP-4) | 1 each | $3.50 + $1.40 | $4.90 | TI / Mornsun / Mouser | Second isolated port on the CSC: STM32 FDCAN2 → ISO1050DUB #3 → J_CAN_STIR, bus side on 5V_ISO2 / GND_SU from B0505S #2 (replaces the non-isolated SN65HVD230) |
| Stir-Motor Bus Passives + SU Island | 120Ω, PESD1CAN, F_SU 5 A polyfuse, SMBJ24A, 100 µF | 1 lot | $0.30 | $0.30 | LCSC | Termination/ESD at J_CAN_STIR; pass-through of the SU's floating 24 V (J_SU_IN → F_SU → J_STIR_PWR) on the CSC's SU island, costed with CSC passives |
| SU PSU Cut (K_SU) + J_SU_IN + J_SAFE 2x3 | Omron G5V-2 #2 + 2N7002 Q_KSU (STM32 PB4), XT30 pair (J_SU_IN), DF11-6DP-2DS instead of DF11-4DP | 1 lot | $3.80 | $3.80 | Omron / Hirose / LCSC | Pilot relay cutting the AC input of LRS-75-24 #2 (de-energised = SU off; opened on E-stop, faults, DU_UNDOCKED); $3.20 + $0.40 + $0.20 |
| Stirring-Unit Port (J_SU) | Molex Micro-Fit 3.0, 5-way receptacle + plug (24V_SU, GND_SU, CAN_H, CAN_L, SHIELD) | 1 pair | $2.00 | $2.00 | Molex / Mouser | The only inter-unit cable: CS right pillar → SU; harness inside the pillar bundles J_CAN_STIR + J_STIR_PWR from the CSC; nothing on it references the CS ground |
| Dispenser Servo (DSB) — FID x3 + CID x1 | DS3218-class, 270°, 20 kg·cm, metal gear | 4 | $10.00 | $40.00 | AliExpress | C1 CID index, F1 FID index, F2 FID dose, F3 FID steam gate; one part number; all on 6.0 V directly (D_DSB4 dropped) |
| PCA9685 16-ch PWM Servo Driver — DSB | PCA9685PW (TSSOP-28) | 1 | $1.50 | $1.50 | LCSC / Mouser | DU STM32 I2C1 addr 0x41, CH0-CH3 used, OE → DU STM32 PB0 (10k pull-up, servos off at boot); on the Unified PCB v5.0 |
| DSB 6.0 V Rail Parts (6V_DSP) | AO3401 P-MOSFET + 3 A PTC + 1000 µF | 1 lot | $1.00 | $1.00 | LCSC | Switched dispenser rail from MP1584EN #2 (Q_DSB, PCF8574 #2 P4); also feeds the TB6612 pumps; off when idle |
| FID Canisters (6x, PP, ¼ tsp measure wheel) | Custom 60mL, food-grade PP | 6 | $3.00 | $18.00 | Custom/3D print | Threaded cap + O-ring + desiccant; rotary 1.23 mL pocket in base, blade coupling |
| FID Carousel Ring + Dosing Station | Custom, 6 bays, Ø170 mm | 1 | $8.00 | $8.00 | Custom/3D print | Ring gear, F2 coupling, steam-gate flap, removable chute |
| CID Carousel Ring (5 bins + cover, 200 mL) | Custom, food-grade PP/PETG, Ø230 mm | 1 | $8.00 | $8.00 | Custom/3D print | Lift-off, keyed hub, ring gear |
| CID Base Plate + Drop Chute | Custom | 1 | $4.00 | $4.00 | Custom/3D print | Fixed plate with 50° rear aperture; removable for washing |
| Index Gear Pairs (4:3 gear-up) | POM or printed spur gears, 32T/24T | 2 | $1.00 | $2.00 | Custom/3D print | Servo 225° → carousel 300° (CID + FID) |
| Carousel Bearings (thin-section) | 6808-2RS or equiv. | 2 | $2.00 | $4.00 | AliExpress | One per carousel hub |
| 6V Peristaltic Pump — SLD oil | Generic 6V DC gear-motor peristaltic, ≈ 0.4 mL/rev, 30–60 mL/min; 2 rotor magnets for the Hall tach | 1 | $10.00 | $10.00 | Amazon / AliExpress | In the DU body under the oil tank bay; 6V_DSP rail via TB6612FNG channel A, speed from DU STM32 TIM3 PWM (PA6), direction via PCF8574 #2 P3 |
| 6V Diaphragm Pump — SLD water | Generic 6V mini diaphragm pump, ≈ 1 L/min, ≈ 0.25 mL/stroke, food-grade EPDM; 1 shaft magnet for the Hall tach | 1 | $5.00 | $5.00 | Amazon / AliExpress | In the DU body under the water tank bay; TB6612FNG channel B, TIM3 PWM (PA7), direction P5 (robot-mop SLD, 2026-11-05) |
| Nozzle Check-Valve Cartridge — SLD | Spring poppet ≈ 5 kPa, food-grade PP/silicone, snap-out | 2 | $1.50 | $3.00 | AliExpress / custom | Drip, siphon and steam blocking at the DU underside; replaces the two 6 V NC solenoid valves |
| Drawer Tank — SLD (oil 200 mL, water 500 mL) | Custom food-grade PP, bottom self-sealing poppet, vented cap, float + magnet, presence magnet | 2 | $6.00 | $12.00 | Custom / 3D print + off-the-shelf poppet | Slide into the DU service-ring bays; dishwasher safe; replace the two bottles + 2 kg load cells |
| Hall Switches ×6 + Magnets — SLD | AH3572 (SOT-23) ×6 + Ø3 mm NdFeB discs | 1 lot | $2.00 | $2.00 | LCSC / AliExpress | Pump tachs (PC0/PC1), tank present (PC2/PC4), tank low (PC3/PC5) on DU STM32 GPIO via the 12-pin J_SLD; replace NAU7802 ×2 + TCA9543A |
| PCF8574 #2 I2C GPIO Expander — SLD/rail/charger | PCF8574 (SOIC-16) | 1 | $0.50 | $0.50 | LCSC / Mouser | DU STM32 I2C1, addr 0x21: P0/P1 spare (solenoids removed), P2 spare (status LED on STM32 PC7), P3/P5 pump direction, P4 6V_DSP rail enable, P6/P7 TP5100 CHRG/STDBY (in); on the Unified PCB v5.3 |
| ISO1050DUB #1 (isolated CAN transceiver, STM32 node) | ISO1050DUBR | 1 | $3.50 | $3.50 | TI / Mouser | 5 kV RMS galvanic isolation, SOIC-8; on the CSC's isolated CAN port #1 (J_CAN_HEAT + J_DOCK pins 3–5), 5V_ISO/GND_ISO from the B0505S-1WR3 #1 on the CSC, referenced to the DU ground at dock pin 5; the only barrier on this bus — the DU STM32 node is a non-isolated SN65HVD230 on FDCAN1 of the Unified PCB v5.0 (gateway for the RV1106; costed under Compute); 3-node bus shared with the heating unit, whose CAN port must be SELV |
| CAN Termination + Decoupling | 120Ω + MLCC caps | 1 lot | $0.13 | $0.13 | LCSC | CAN bus passives on the CSC (R_TERM1 at J_CAN_HEAT, PESD1CAN); the dock → Unified PCB run is an unterminated stub ≤ 30 cm |
| Relay Module (5V, 10A) | SRD-05VDC-SL-C | 2 | $3.00 | $6.00 | Amazon | Prototype AC-side relays: heater on/off (K_SAFE pilot, CSC Q_RLY, STM32 PB0, J_SAFE 1) and SU PSU on/off (K_SU pilot, CSC Q_KSU, STM32 PB4, J_SAFE 5) |
| Motor Driver Board | L298N or custom | 1 | $8.00 | $8.00 | Amazon | Servo power distribution and level shifting |
| Power Connectors (XT60) | XT60 male+female | 4 | $1.00 | $4.00 | Amazon | High-current connections for heater and servo power |
| Wiring Harness (18AWG silicone) | 18AWG, 5m assorted | 1 lot | $10.00 | $10.00 | Amazon | Internal wiring; silicone insulation for heat resistance |
| Servo Extension Cables (300mm) | 300mm JR/Futaba | 4 | $1.00 | $4.00 | Amazon | DSB servo wiring to J_DSB1-4 headers |
| Exhaust Fan (60mm, PWM) | Noctua NF-A6x25 or generic | 1 | $8.00 | $8.00 | Amazon | 4-pin PWM, 12V, fume extraction; J_FAN on the CSC (CS rear, 12 V from MP1584EN #1) |
| Grease Mesh + Carbon Filter | 304 SS mesh + coconut carbon | 1 set | $8.00 | $8.00 | Amazon / AliExpress | Dual-stage filtration cartridge |
| Filter Housing + Duct | 3D printed ABS + sheet metal | 1 | $6.00 | $6.00 | Self-fabricated | Slide-out cartridge + 60mm duct |
| Fan MOSFET (PWM driver) | IRLML6344 + SS14 (per channel) | 1 lot | $0.50 | $0.50 | LCSC | Logic-level low-side switches on the CSC (STM32 PA6 TIM3_CH1, PB10) |
| Piezo Buzzer (5V, PWM) | MLT-5030 or generic | 1 | $0.80 | $0.80 | Amazon / Mouser | Audio feedback for alerts, errors, task completion; in the DU on 5V_MAIN, driven by DU STM32 TIM14 PWM (PA4) |
| Buzzer MOSFET | 2N7002 (SOT-23) | 1 | $0.05 | $0.05 | LCSC | Logic-level gate for the DU STM32 buzzer PWM (Unified PCB v5.0) |

---

## 4. Cost Summary

| Item | Cost |
|------|------|
| Donor cooker: Philips OneChef NX5300/00 or equivalent (heating unit, controller, body; pot and lid not used) | $230.00 |
| 24V CAN Servo Motor (main arm) | $45.00 |
| ISO1050DUB #3 + B0505S #2 + stir-bus passives (isolated CAN port #2, CSC) | $5.20 |
| K_SU SU-PSU relay + J_SU_IN + J_SAFE DF11-6DP (CSC) | $3.80 |
| Dispenser Servos — DSB (4x) | $40.00 |
| PCA9685 + DSB 6.0 V Rail Parts | $2.50 |
| FID Canisters (6x) | $18.00 |
| FID Carousel Ring + Dosing Station | $8.00 |
| CID Carousel Ring + Base Plate + Chute | $12.00 |
| Index Gears + Carousel Bearings | $6.00 |
| Pumps — SLD (6 V peristaltic oil + 6 V diaphragm water, Hall tachs) | $15.00 |
| Nozzle Check-Valve Cartridges — SLD (2x) | $3.00 |
| Drawer Tanks — SLD (200 mL oil + 500 mL water) | $12.00 |
| Hall Switches ×6 + Magnets — SLD | $2.00 |
| PCF8574 #2 I2C GPIO Expander (SLD/rail/charger) | $0.50 |
| ISO1050DUB #1 (isolated CAN transceiver, CSC) | $3.50 |
| CAN Termination + Decoupling | $0.13 |
| Relay Module (safety, 2x) | $6.00 |
| Motor Driver Board | $8.00 |
| Connectors + Wiring (XT60, J_SU pair, harness, servo cables) | $20.00 |
| Exhaust Fan + Filtration | $22.50 |
| Piezo Buzzer + MOSFET | $0.85 |
| **Category Subtotal** | **$463.98** |

---

## 5. Design Notes

### 5.1 Electric Heating Unit Strategy
- **Both Prototype and Production:** Commercial electric heating unit of the premium rice-cooker class with CAN bus port (replaces the induction surface, 2026-11-04; same CAN contract, no controller change)
  - Reference unit: Philips OneChef NX5300/00 (see [[01-Electric-Heating]] §2.3) — prototypes use the retail cooker as a donor (body, plate, controller; air-fryer lid dropped; its round inner pot and glass lid are set aside — Epicura's pot is a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot, Mechanical Design §2.2, costed in [[04-Total-Component-Cost]] §4 at $25); temperature range 80–200 °C, so sear/tadka stages stop at 200 °C. The OEM unit ships with a control board exposing HEAT_* on CAN (confirmed 2026-11-04); the retail touch-panel board is not used
  - Self-contained unit: resistive heating plate, spring-loaded centre temperature sensor, relay/triac mains power stage, safety circuits; any flat-bottomed pot
  - RV1106 sends temperature setpoints (HEAT_SET_TEMP) or power levels (HEAT_SET_POWER) via CAN 2.0B at 500 kbps on the shared isolated bus; the unit runs its own temperature loop on its centre sensor (no IR thermometer in Epicura); the STM32 can force the unit off (HEAT_ON_OFF=0)
  - No custom mains power electronics needed
  - Safety relay on AC mains (CSC Q_RLY → J_SAFE) provides system-level hard disconnect; the hard E-stop button is on the CS front, wired to the CSC
  - Unit-internal pot detection (centre sensor, `pot_detected`) and thermal cutoff
  - Lifting the DU opens the bus and the dock 24 V together: the unit drops to zero ≤ 1 s on keep-alive loss and the STM32 holds safe on DOCK_SENSE_B (fault 0x17 DU_UNDOCKED, not an E_STOP)

### 5.2 24V CAN Servo Motor Selection
- **≥ 3 N·m (30 kg-cm) continuous torque** provides ample margin for thick curries and dals; current limit set in the motor
- **Integrated BLDC + planetary gearbox + encoder + driver** in one housing; true continuous rotation
- **CAN interface (1 Mbps)** on the CSC's isolated CAN port #2 (STM32 FDCAN2, ISO1050DUB #3 + B0505S #2 on 5V_ISO2 / GND_SU, 120 Ω at J_CAN_STIR + in the motor): velocity mode for stirring, position mode for parking; feedback of rpm, angle, current and temperature replaces the FG tachometer, Hall homing and INA219 stall heuristic
- **Own floating 24 V supply**: Mean Well LRS-75-24 #2 in the CS rear (24V_SU / GND_SU, never bonded to the CS ground), AC input cut by the CSC pilot relay K_SU (STM32 PB4 via Q_KSU; default off, opened on E-stop, faults, DU_UNDOCKED), passed through the CSC on J_SU_IN → F_SU 5 A → J_STIR_PWR; J_CAN_STIR + J_STIR_PWR are bundled into one harness inside the right pillar ending at J_SU (Micro-Fit 3.0, 5-way), the only cable between units; the Motor Control task waits for the motor's boot frame (~300 ms PSU start-up) and the motor command timeout ≤ 500 ms is configured at start-up
- **Specific model TBD** — document generically as "24V integrated CAN servo, ≥ 3 N·m, 1 Mbps CAN" (CyberGear/RobStride-class or industrial equivalent)

### 5.3 Dispenser Servo Block (FID + CID)
- **One control block for both carousels**: 4× identical DS3218-class 270° servos on a PCA9685 (DU STM32 I2C1, 0x41), OE on DU STM32 PB0, switched 6.0 V rail (6V_DSP) from MP1584EN #2 on the Unified PCB v5.0; the whole block is in the DU and is driven by the DU STM32 Dispense task under host-link commands (0x230–0x239) from the RV1106 `dispense` thread, never by the CSC STM32
- **FID**: 6-canister carousel; F1 indexes (4:3 gear-up, 60° per box), F2 drives the selected canister's integral ¼ tsp (1.23 mL) measure wheel through a blade coupling, F3 opens a spring-closed steam gate only while dosing
- **CID**: 5-slot + cover carousel on a fixed base plate with one rear aperture; C1 indexes a slot over the aperture and its contents free-fall into the pot (ascending slot order)
- **No sensors in the block**: servos are open loop; stall/jam detected by the INA219 #1 current window on the 6V_DSP rail (> 2.5 A for 300 ms) + 3 s move timeout in the DU STM32 Dispense task; anti-bridging by servo jiggle in software
- **BOM cost**: ~$86.50 for both dispensers (vs ~$127.50 for P-ASD pneumatics + CID stepper/linear actuator) — net −$40 and 9 freed STM32/expander pins

### 5.5 SLD Pumps (×2), Drawer Tanks (×2) + Check-Valve Nozzles (×2) — robot-mop pattern (2026-11-05)
- Drawer tanks (200 mL oil, 500 mL water) slide into the DU service ring; bottom self-sealing poppet mates the bay port, vented cap; float + magnet for low level and a fixed magnet for presence, read by Hall switches in the bay
- Pumps in the DU body on the shared 6V_DSP rail (TB6612FNG, DU STM32 TIM3 PWM): a 6 V peristaltic for oil (≈ 0.4 mL/rev, oil touches only the tube) and a 6 V diaphragm for water (≈ 1 L/min, 500 mL in ≈ 30 s); each carries a Hall tach, and the DU STM32 meters open loop by pulses × calibrated mL/pulse (±5 %) with a prime routine after a tank re-seat
- Spring check valve in each snap-out nozzle cartridge blocks drip, siphoning and steam; no solenoid valves and no load cells remain

### 5.6 Production Cost Reduction

| Item | Prototype | Production (1000 qty) | Savings |
|------|-----------|----------------------|---------|
| Donor cooker (heating unit, body) | $230 | $50 (OEM heating unit, bulk) | 78% |
| Pot (25 cm rounded-square non-stick + glass lid; costed in Total Component Cost §4) | $25 | $10 (custom pressed, bulk) | 60% |
| 24V CAN servo motor | $45 | $30 (bulk) | 33% |
| FID + CID servo carousels (4 servos, PCA9685, rings, canisters) | $86.50 | $45 (bulk, molded rings/canisters) | 48% |
| Pumps (SLD: 6 V peristaltic oil + 6 V diaphragm water) | $15 | $7 (bulk) | 53% |
| Drawer tanks x2 + check-valve nozzle cartridges x2 (SLD) | $15 | $5 (molded, bulk) | 67% |
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
| 10.3 | 2026-11-04 | Manas Pradhan | Heating unit referenced to the Philips OneChef NX5300/00: heater line becomes the donor cooker (heating unit, controller, 6 L non-stick pot, glass lid, base body) $45 → $230; production $30 → $60 (OEM heating unit + pot, bulk); Case A / Case B CAN note in §5.1; subtotal $282.18 → $467.18 |
| 10.4 | 2026-11-04 | Manas Pradhan | Pot changed to a 25 × 25 × 12 cm rounded-square non-stick pot (Mechanical Design §2.2): the donor's round pot and lid are not used (§3, §4, §5.1 rows); pot + lid costed in Total Component Cost §4 ($25, production $10); §5.6 production split OEM heating unit $50 + pot $10 |
| 10.5 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: dispensers, pumps, solenoids, load cells and buzzer are driven by the DU STM32 (STM32G0B1RET6 on the Unified PCB v5.0: I2C1, TIM3/TIM14 PWM, PB0 OE) under host-link commands from the RV1106; ISO1050DUB #1 row names the DU STM32 as the other Epicura node; diagram redrawn; no price change, subtotal $467.18 |
| 10.7 | 2026-11-04 | Manas Pradhan | ISO1050DUB #1 row: DU node is now a non-isolated SN65HVD230 (Unified PCB v5.1), GND_ISO referenced to the DU ground at dock pin 5, heating-unit CAN port must be SELV; no price change in this category |
| 10.8 | 2026-11-05 | Manas Pradhan | Robot-mop SLD: 2× 6 V peristaltic ($20) → 6 V peristaltic oil ($10) + 6 V diaphragm water ($5); 2× solenoid ($8) → 2× check-valve nozzle cartridge ($3); 2× 2 kg load cell ($10) → 2× drawer tank ($12); NAU7802 ×2 + TCA9543A ($5) → Hall switches ×6 + magnets ($2); PCF8574 #2 P0/P1 spare; diagram, §5.5 and cost summary updated; subtotal $474.98 → $463.98 |
| 10.6 | 2026-11-04 | Manas Pradhan | Aligned to CSC v1.3: stir-motor port is the CSC's second isolated CAN port — SN65HVD230 (−$0.90) replaced by ISO1050DUB #3 ($3.50) + B0505S-1WR3 #2 ($1.40); the SU runs from its own LRS-75-24 #2 (costed under Total Component Cost §4) with the pilot relay K_SU (G5V-2 #2 + Q_KSU), XT30 J_SU_IN and the DF11-6DP J_SAFE added as one lot (+$3.80); Q_STIR / F_STIR dropped from the passives row; J_SU signals 24V_SU / GND_SU; diagram gains K_SAFE / K_SU; subtotal $467.18 → $463.98 |
