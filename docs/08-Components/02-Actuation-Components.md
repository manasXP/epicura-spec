---
created: 2026-02-15
modified: 2026-11-04
version: 10.0
status: Draft
---

# Actuation Components

## 1. Overview

This document details the actuation subsystem components for the Epicura kitchen robot prototype, including the induction heating element, servo stirring arm, and ingredient dispensing mechanisms.

## 2. Actuation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Actuation Subsystem                          │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │  STM32G474RE │── CAN  ►│  24V CAN     │                     │
│  │  (Controller)│ FDCAN2  │  Servo Motor │                     │
│  │              │ + 24V sw└──────────────┘                     │
│  │              │                                               │
│  │              │── I2C  ►┌──────────────┐  ┌──────────────┐   │
│  │              │ PCA9685 │  DSB: FID x3 │─►│ Carousels    │   │
│  │              │  + OE   │  + CID x1    │  │ (FID + CID)  │   │
│  │              │         └──────────────┘  └──────────────┘   │
│  │              │                                               │
│  │              │── PWM  ►┌──────────────┐                     │
│  │              │  +GPIO  │  SLD: Pump x2│                     │
│  │              │         │  + Solenoid x2│                    │
│  │              │         └──────────────┘                     │
│  │              │                                               │
│  │              │── GPIO ►┌──────────────┐    ┌────────────┐   │
│  │              │         │  Relay x2    │───►│ Induction  │   │
│  │              │         │  (10A)       │    │ Hob 1800W  │   │
│  └──────────────┘         └──────────────┘    └────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component List

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Microwave Induction Surface (1800W, CAN) | Commercial module | 1 | $60.00 | $60.00 | Supplier TBD | Self-contained module with CAN bus port; no teardown needed |
| 24V CAN Servo Motor (stirring) | CyberGear/RobStride-class integrated BLDC servo, ≥ 3 N·m continuous, CAN 1 Mbps (model TBD) | 1 | $45.00 | $45.00 | AliExpress / Robstride | Main stirring arm; encoder feedback, velocity + position modes; on the Unified PCB's regular CAN port (FDCAN2) with switched 24 V |
| SN65HVD230 CAN Transceiver (stir-motor port) | SN65HVD230DR (SOIC-8) | 1 | $0.90 | $0.90 | TI / LCSC | Non-isolated 3.3 V transceiver on STM32 FDCAN2 → J_CAN_STIR |
| Stir-Motor Bus Passives + 24 V Switch | 120Ω, PESD1CAN, AO4407A + 2N7002, 5 A polyfuse | 1 lot | $0.30 | $0.30 | LCSC | Termination/ESD at J_CAN_STIR; Q_STIR high-side switch costed with PCB passives |
| Dispenser Servo (DSB) — FID x3 + CID x1 | DS3218-class, 270°, 20 kg·cm, metal gear | 4 | $10.00 | $40.00 | AliExpress | C1 CID index, F1 FID index, F2 FID dose, F3 FID steam gate; one part number |
| PCA9685 16-ch PWM Servo Driver — DSB | PCA9685PW (TSSOP-28) | 1 | $1.50 | $1.50 | LCSC / Mouser | I2C1 addr 0x41, CH0-CH3 used, OE → PB4 |
| DSB 6.5 V Rail Parts | AO3401 P-MOSFET + 3 A PTC + 1000 µF | 1 lot | $1.00 | $1.00 | LCSC | Rail from MP1584EN #2, switched by PCF8574 #2 P4 |
| FID Canisters (6x, PP, ¼ tsp measure wheel) | Custom 60mL, food-grade PP | 6 | $3.00 | $18.00 | Custom/3D print | Threaded cap + O-ring + desiccant; rotary 1.23 mL pocket in base, blade coupling |
| FID Carousel Ring + Dosing Station | Custom, 6 bays, Ø170 mm | 1 | $8.00 | $8.00 | Custom/3D print | Ring gear, F2 coupling, steam-gate flap, removable chute |
| CID Carousel Ring (5 bins + cover, 200 mL) | Custom, food-grade PP/PETG, Ø230 mm | 1 | $8.00 | $8.00 | Custom/3D print | Lift-off, keyed hub, ring gear |
| CID Base Plate + Drop Chute | Custom | 1 | $4.00 | $4.00 | Custom/3D print | Fixed plate with 50° rear aperture; removable for washing |
| Index Gear Pairs (4:3 gear-up) | POM or printed spur gears, 32T/24T | 2 | $1.00 | $2.00 | Custom/3D print | Servo 225° → carousel 300° (CID + FID) |
| Carousel Bearings (thin-section) | 6808-2RS or equiv. | 2 | $2.00 | $4.00 | AliExpress | One per carousel hub |
| 12V Peristaltic Pump — SLD | Generic 12V DC gear motor | 2 | $10.00 | $20.00 | Amazon / AliExpress | SLD liquid dispensing (oil + water) |
| 12V NC Solenoid Valve — SLD | Generic 12V, normally closed | 2 | $4.00 | $8.00 | Amazon / AliExpress | SLD drip prevention |
| 2 kg Load Cell + HX711 — SLD (oil) | Generic 2 kg strain gauge + HX711 | 1 | $8.00 | $8.00 | Amazon | SLD oil reservoir closed-loop metering + level alert |
| 2 kg Load Cell + HX711 — SLD (water) | Generic 2 kg strain gauge + HX711 | 1 | $8.00 | $8.00 | Amazon | SLD water reservoir closed-loop metering + level alert |
| PCF8574 #2 I2C GPIO Expander — SLD/LED | PCF8574 (SOIC-16) | 1 | $0.50 | $0.50 | LCSC / Mouser | SLD solenoids + status LED + LED ring power (I2C1, addr 0x21) |
| ISO1050DUB #1 (isolated CAN transceiver, STM32 node) | ISO1050DUBR | 1 | $3.50 | $3.50 | TI / Mouser | 5 kV RMS galvanic isolation, SOIC-8; on the Unified PCB's isolated CAN port (J_CAN_HEAT), 3-node bus shared with the RV1106 (ISO1050DUB #2 + MCP2518FD costed under Compute) and the induction module |
| CAN Termination + Decoupling | 120Ω + MLCC caps | 1 lot | $0.13 | $0.13 | LCSC | CAN bus passives on Driver PCB |
| Relay Module (5V, 10A) | SRD-05VDC-SL-C | 2 | $3.00 | $6.00 | Amazon | Induction on/off and power cycling control (prototype) |
| Motor Driver Board | L298N or custom | 1 | $8.00 | $8.00 | Amazon | Servo power distribution and level shifting |
| Power Connectors (XT60) | XT60 male+female | 4 | $1.00 | $4.00 | Amazon | High-current connections for induction and servo power |
| Wiring Harness (18AWG silicone) | 18AWG, 5m assorted | 1 lot | $10.00 | $10.00 | Amazon | Internal wiring; silicone insulation for heat resistance |
| Servo Extension Cables (300mm) | 300mm JR/Futaba | 4 | $1.00 | $4.00 | Amazon | DSB servo wiring to J_DSB1-4 headers |
| Exhaust Fan (60mm, PWM) | Noctua NF-A6x25 or generic | 1 | $8.00 | $8.00 | Amazon | 4-pin PWM, 12V, fume extraction |
| Grease Mesh + Carbon Filter | 304 SS mesh + coconut carbon | 1 set | $8.00 | $8.00 | Amazon / AliExpress | Dual-stage filtration cartridge |
| Filter Housing + Duct | 3D printed ABS + sheet metal | 1 | $6.00 | $6.00 | Self-fabricated | Slide-out cartridge + 60mm duct |
| Fan MOSFET (PWM driver) | IRLZ44N | 1 | $0.50 | $0.50 | LCSC | Logic-level gate for STM32 PWM |
| Piezo Buzzer (5V, PWM) | MLT-5030 or generic | 1 | $0.80 | $0.80 | Amazon / Mouser | Audio feedback for alerts, errors, task completion |
| Buzzer MOSFET | 2N7002 (SOT-23) | 1 | $0.05 | $0.05 | LCSC | Logic-level gate for buzzer PWM |

---

## 4. Cost Summary

| Item | Cost |
|------|------|
| Microwave Induction Surface (CAN) | $60.00 |
| 24V CAN Servo Motor (main arm) | $45.00 |
| SN65HVD230 + stir-bus passives | $1.20 |
| Dispenser Servos — DSB (4x) | $40.00 |
| PCA9685 + DSB Rail Parts | $2.50 |
| FID Canisters (6x) | $18.00 |
| FID Carousel Ring + Dosing Station | $8.00 |
| CID Carousel Ring + Base Plate + Chute | $12.00 |
| Index Gears + Carousel Bearings | $6.00 |
| Peristaltic Pumps — SLD (2x) | $20.00 |
| Solenoid Valves — SLD (2x) | $8.00 |
| Load Cells + HX711 — SLD (2×) | $16.00 |
| PCF8574 #2 I2C GPIO Expander (SLD/LED) | $0.50 |
| ISO1050DUB (isolated CAN transceiver) | $3.50 |
| CAN Termination + Decoupling | $0.13 |
| Relay Module (safety, 2x) | $6.00 |
| Motor Driver Board | $8.00 |
| Connectors + Wiring | $18.00 |
| Exhaust Fan + Filtration | $22.50 |
| Piezo Buzzer + MOSFET | $0.85 |
| **Category Subtotal** | **$296.18** |

---

## 5. Design Notes

### 5.1 Microwave Induction Surface Strategy
- **Both Prototype and Production:** Commercial microwave induction surface with CAN bus port
  - Self-contained module: internal coil, driver, safety circuits
  - RV1106 sends temperature setpoints (HEAT_SET_TEMP) or power levels (HEAT_SET_POWER) via CAN 2.0B at 500 kbps on the shared isolated bus; the module runs its own temperature loop on its own sensor (no IR thermometer in Epicura); the STM32 can force the module off (HEAT_ON_OFF=0)
  - No custom IGBT driver design needed
  - Safety relay on AC mains provides system-level hard disconnect
  - Module-internal pot detection and thermal cutoff

### 5.2 24V CAN Servo Motor Selection
- **≥ 3 N·m (30 kg-cm) continuous torque** provides ample margin for thick curries and dals; current limit set in the motor
- **Integrated BLDC + planetary gearbox + encoder + driver** in one housing; true continuous rotation
- **CAN interface (1 Mbps)** on the Unified PCB's regular CAN port (STM32 FDCAN2, SN65HVD230): velocity mode for stirring, position mode for parking; feedback of rpm, angle, current and temperature replaces the FG tachometer, Hall homing and INA219 stall heuristic
- **Switched 24V** from Q_STIR on the PCB (J_STIR_PWR); motor command timeout ≤ 500 ms configured at start-up
- **Specific model TBD** — document generically as "24V integrated CAN servo, ≥ 3 N·m, 1 Mbps CAN" (CyberGear/RobStride-class or industrial equivalent)

### 5.3 Dispenser Servo Block (FID + CID)
- **One control block for both carousels**: 4× identical DS3218-class 270° servos on a PCA9685 (I2C1, 0x41), OE on PB4, switched 6.5 V rail from MP1584EN #2 (previously retained for future use)
- **FID**: 6-canister carousel; F1 indexes (4:3 gear-up, 60° per box), F2 drives the selected canister's integral ¼ tsp (1.23 mL) measure wheel through a blade coupling, F3 opens a spring-closed steam gate only while dosing
- **CID**: 5-slot + cover carousel on a fixed base plate with one rear aperture; C1 indexes a slot over the aperture and its contents free-fall into the pot (ascending slot order)
- **No sensors in the block**: servos are open loop; stall/jam detected by INA219 current window + move timeout; anti-bridging by servo jiggle in software
- **BOM cost**: ~$86.50 for both dispensers (vs ~$127.50 for P-ASD pneumatics + CID stepper/linear actuator) — net −$40 and 9 freed STM32/expander pins

### 5.5 SLD Peristaltic Pumps (×2) + Solenoid Valves (×2)
- Peristaltic: fluid only touches food-grade silicone tubing (no contamination)
- Flow rate 5–50 mL/min, adjustable via PWM motor speed
- Solenoid valves (12V NC) prevent dripping when pumps are off
- Dedicated 1 kg load cell + HX711 for closed-loop liquid metering (±5%)

### 5.6 Production Cost Reduction

| Item | Prototype | Production (1000 qty) | Savings |
|------|-----------|----------------------|---------|
| Microwave surface | $60 | $40 (bulk) | 33% |
| 24V CAN servo motor | $45 | $30 (bulk) | 33% |
| FID + CID servo carousels (4 servos, PCA9685, rings, canisters) | $86.50 | $45 (bulk, molded rings/canisters) | 48% |
| Peristaltic pumps x2 (SLD) | $20 | $10 (bulk) | 50% |
| Solenoid valves x2 (SLD) | $8 | $4 (bulk) | 50% |
| CAN transceiver (ISO1050DUB) | $3.50 (on Driver PCB) | $2.50 (bulk) | 29% |
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
