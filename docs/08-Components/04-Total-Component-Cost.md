---
created: 2026-02-15
modified: 2026-11-04
version: 10.3
status: Draft
---

# Total Component Cost Summary

## 1. Overview

This document provides a consolidated view of all component costs for the Epicura kitchen robot prototype, including electronic components, mechanical parts, and projected production costs.

---

## 2. Category Summary

| Category | Subtotal | % of Total | Details |
|----------|----------|------------|---------|
| [[01-Compute-Module-Components|Compute Modules]] | $91.50 | 13% | Luckfox Pico Zero (RV1106G3), STM32, 4" SPI LCD, RV1106 CAN node (MCP2518FD + ISO1050DUB #2), cables |
| [[02-Actuation-Components|Actuation]] | $296.18 | 42% | Induction hob, Dispenser Servo Block (4 servos + PCA9685, FID/CID carousels + canisters), PCF8574 #2 GPIO expander, SLD pumps/solenoids/load cells, ISO1050DUB + SN65HVD230 CAN transceivers, 24V CAN servo stirring motor, relays, exhaust fan, filters |
| [[03-Sensor-Components|Sensors]] | $60.80 | 9% | IMX415-98 camera, reed switch, LED ring + level shifter (no thermometer: module-reported temperature) |
| **Component Total** | **$448.48** | **63%** | Electronic components only |

---

## 3. Detailed Component Breakdown

### 3.1 Compute Modules ($91.50)

| Item | Cost |
|------|------|
| Luckfox Pico Zero (RV1106G3, 256MB, 8GB eMMC) | $47.00 |
| STM32G474RE Nucleo | $18.00 |
| 4" ST7796S SPI LCD + FT6336 touch | $15.00 |
| RV1106 CAN node (MCP2518FD + crystal, ISO1050DUB #2) | $6.50 |
| Cables | $5.00 |

### 3.2 Actuation ($296.18)

| Item | Cost |
|------|------|
| Microwave Induction Surface (CAN, internal temperature control) | $60.00 |
| 24V CAN Servo Motor (main arm) | $45.00 |
| SN65HVD230 + stir-bus passives (regular CAN port) | $1.20 |
| Dispenser Servos — DSB (4x DS3218-class) | $40.00 |
| PCA9685 + DSB Rail Parts | $2.50 |
| FID Canisters (6x, ¼ tsp measure wheels) | $18.00 |
| FID Carousel Ring + Dosing Station | $8.00 |
| CID Carousel Ring + Base Plate + Chute | $12.00 |
| Index Gears + Carousel Bearings | $6.00 |
| PCF8574 #2 GPIO Expander | $0.50 |
| Peristaltic Pumps — SLD (2x) | $20.00 |
| Solenoid Valves — SLD (2x) | $8.00 |
| Load Cells + HX711 — SLD (2×) | $16.00 |
| ISO1050DUB #1 (isolated CAN transceiver, STM32 node) | $3.50 |
| CAN Termination + Decoupling | $0.13 |
| Safety Relay Module (2x) | $6.00 |
| Motor Driver Board | $8.00 |
| Connectors + Wiring | $18.00 |
| Exhaust Fan + Filtration | $22.50 |
| Piezo Buzzer + MOSFET | $0.85 |

### 3.3 Sensors ($60.80)

| Item | Cost |
|------|------|
| IMX415-98 Camera | $54.00 |
| Reed Switch + LED Ring + 74AHCT1G125 | $6.30 |
| Passive Components | $0.50 |

---

## 4. Additional Costs

| Item | Cost | Notes |
|------|------|-------|
| Enclosure (3D printed) | $80.00 | PLA/PETG filament, prototype enclosure + internal brackets |
| Mechanical Parts (shaft, brackets, fasteners) | $50.00 | Stainless steel shaft (8mm), aluminum brackets, M3/M4 fasteners |
| Custom PCB (Unified PCB) | $25.50 | Single 4-layer board, 5 pcs (JLCPCB); hosts the Pico Zero slot, both CAN ports, dispenser drivers and the TP5100 charger |
| Power Supply Module + Battery | $42.00 | Mean Well LRS-75-24 (24V/3.2A/76.8W) $30 + 2S1P 18650 Li-ion pack with PCM and NTC $12 (replaces the external 12V UPS, $15-30, previously outside the BOM) |
| Wiring / Connectors / Misc | $30.00 | JST, Dupont, ring terminals, heat shrink, cable ties |
| Pot (induction-compatible) | $20.00 | Stainless steel 304, 3-4L capacity, flat base |
| **Additional Total** | **$262.00** | |

---

## 5. Prototype Total BOM

| Category | Cost |
|----------|------|
| Electronic Components | $448.48 |
| Mechanical / Other | $262.00 |
| **Total BOM (Prototype)** | **$710.48** |
| **With Contingency (+20%)** | **~$853** |
| **With Tools & Consumables** | **$950-1,250** |

---

## 6. Prototype vs Production Cost Comparison

| Item | Prototype | Production (1000 qty) | Notes |
|------|-----------|----------------------|-------|
| Luckfox Pico Zero (RV1106G3) | $47.00 | $18.00 | Bare RV1106G3 (QFN128) on custom PCB, or Core1106 SoM, at volume |
| STM32G474 | $18.00 (Nucleo) | $5.00 (bare chip) | Custom PCB eliminates dev board |
| Display (4" SPI) | $15.00 | $8.00 | Same ST7796S panel, bulk pricing; stays SPI |
| Microwave Induction Surface | $60.00 (CAN module) | $40.00 (bulk pricing) | Self-contained module, no custom driver |
| FID + CID servo carousels (4 servos, PCA9685, rings, canisters) | $86.50 | $45.00 | Bulk servos, injection-molded rings and canisters |
| Pumps + Solenoids — SLD | $28.00 | $14.00 | Bulk pricing |
| 24V CAN Servo Stirring Motor | $45.00 | $30.00 | Bulk pricing |
| Sensors (all) | $60.80 | $28.00 | Direct from manufacturer, MOQ pricing |
| Enclosure | $80.00 (3D print) | $15.00 (injection mold) | Mold cost amortized over production run |
| PCBs | $25.50 (prototype) | $8.00 (panel production) | Single unified PCB (controller + driver merged) |
| Power Supply + 2S battery pack | $42.00 | $20.00 | Integrated SMPS on main PCB; bulk cells |
| Mechanical | $50.00 | $15.00 | Stamped brackets, bulk fasteners |
| Pot + Accessories | $20.00 | $10.00 | OEM sourcing |
| Wiring / Connectors | $30.00 | $10.00 | Custom harness, bulk connectors |
| Exhaust + Filters | $22.50 | $8.00 (OEM blower + bulk filters) | Custom blower + injection-molded housing |
| Other (CAN nodes + stir-bus transceiver, relays, load cells, cables, buzzer) | $80.18 | $22.00 (integrated into PCB + bulk) | Small components absorbed into custom PCB at volume |
| **Total Unit** | **~$710** | **~$285** | **~60% cost reduction** |

---

## 7. Cost Breakdown Chart

```
┌────────────────────────────────────────────────────────────────────────────┐
│                 Epicura Prototype Component Costs                         │
│                                                                          │
│  Compute Modules (13%)  █████████████                                    │
│  └─ RV1106 board (7%)   ███████                                          │
│  └─ Display (2%)        ██                                               │
│  └─ STM32 (3%)          ███                                              │
│  └─ CAN node+cables (2%)██                                               │
│                                                                          │
│  Actuation (42%)        ██████████████████████████████████████████       │
│  └─ FID/CID (12%)       ████████████                                     │
│  └─ Induction (8%)      ████████                                         │
│  └─ Stir motor (6%)     ██████                                           │
│  └─ SLD (4%)            ████                                             │
│  └─ Other (12%)         ████████████                                     │
│                                                                          │
│  Sensors (9%)           █████████                                        │
│  └─ Camera (8%)         ████████                                         │
│  └─ Other (1%)          █                                                │
│                                                                          │
│  Additional (37%)       █████████████████████████████████████            │
│  └─ Enclosure (11%)     ███████████                                      │
│  └─ Mechanical (7%)     ███████                                          │
│  └─ PCBs/PSU/battery (10%) ██████████                                    │
│                                                                          │
│  Total Prototype BOM: ~$710                                              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Budget Planning by Development Phase

| Phase | Description | Estimated Spend | Cumulative |
|-------|-------------|----------------|------------|
| Phase 1 | Hardware Setup (Luckfox Pico Zero + STM32 + 4" LCD + PSU + 2S battery pack) | $160-260 | $160-260 |
| Phase 2-3 | Induction + Arm (hob + CAN servo motor + load cells + mechanical) | $220-320 | $380-580 |
| Phase 4 | Vision (IMX415-98 camera + LED ring + level shifter + training data ingredients) | $75-105 | $455-685 |
| Phase 5 | Dispensing (Dispenser Servo Block: 4 servos + PCA9685, FID/CID carousels + canisters, SLD pumps/solenoids/2× load cells) | $130-170 | $585-855 |
| Phase 6 | UI (display already counted; app dev = $0 software) | $0-20 | $585-875 |
| Phase 7 | Integration (consumables, replacements, debugging) | $50-100 | $635-975 |
| Contingency | Unexpected costs, rework, replacement parts | $200-400 | $835-1,375 |
| Tools | Soldering station, multimeter, 3D printer access | $100-200 | $935-1,575 |
| Ingredients | 30+ cook sessions for testing and training data | $50-100 | $985-1,675 |
| **Total Project Budget** | | **$1,500-2,500** | |

---

## 9. Cost Drivers Analysis

### 9.1 Highest Cost Components

| Rank | Component | Cost | % of BOM | Notes |
|------|-----------|------|----------|-------|
| 1 | Enclosure (3D print) | $80.00 | 11% | Prototype only; injection mold: $15/unit |
| 2 | Microwave Induction Surface | $60.00 | 8% | Self-contained CAN module with internal temperature control; bulk: $40 |
| 3 | IMX415-98 IR-CUT camera | $54.00 | 8% | Only Luckfox colour camera supported on the Pico Zero; bulk: ~$30 |
| 4 | Mechanical Parts | $50.00 | 7% | Shaft, brackets, fasteners |
| 5 | Luckfox Pico Zero (RV1106G3) | $47.00 | 7% | Bare RV1106G3 or Core1106 SoM on custom PCB: ~$18 |
| 6 | 24V CAN Servo Stirring Motor | $45.00 | 6% | CyberGear/RobStride-class; bulk: ~$30 |
| 7 | Dispenser Servos (4x, DSB) | $40.00 | 6% | DS3218-class; bulk: ~$6 each |
| 8 | Unified PCB | $25.50 | 4% | Single board; panel production: $8/unit |

### 9.2 Cost Reduction Opportunities

| Opportunity | Potential Savings | Effort | Risk |
|-------------|-------------------|--------|------|
| Volume pricing (1000 qty) | 40-50% overall | Low | Low |
| Unified PCB volume production | $15-20/unit | Low | Low |
| Bare RV1106G3 / Core1106 SoM on custom PCB (replaces Pico Zero) | $25-30/unit | Medium | Low |
| Custom induction driver | $20/unit | High | Medium |
| Injection-molded enclosure | $65/unit | High (tooling) | Low |
| Direct manufacturer sourcing (sensors) | $25-30/unit | Medium | Low |

---

## 10. Target Pricing (Production)

| Volume | Unit BOM Cost | Target Selling Price | Gross Margin |
|--------|--------------|---------------------|-------------|
| 100 units | $340-390 | Not viable (pre-production) | - |
| 1,000 units | $260-310 | $599-799 | 48-67% |
| 10,000 units | $210-250 | $499-699 | 50-70% |

---

## 11. Related Documentation

- [[01-Compute-Module-Components|Compute Module Components]]
- [[02-Actuation-Components|Actuation Components]]
- [[03-Sensor-Components|Sensor Components]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Prototype-Development-Plan|Prototype Development Plan]]

---

#epicura #components #bom #cost-analysis

---

## 12. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-16 | Manas Pradhan | Update costs for P-ASD pneumatic redesign (+$84 to actuation); new prototype BOM ~$784 |
| 3.0 | 2026-02-16 | Manas Pradhan | Added PCF8574 I2C GPIO expander (+$0.50); prototype BOM ~$785 |
| 4.0 | 2026-02-20 | Manas Pradhan | Moved CAN transceiver from Actuation to Compute (ISO1050DUB $3.50 replaces $3.00 non-isolated); updated all totals; prototype BOM ~$793 |
| 5.0 | 2026-02-20 | Manas Pradhan | Removed NTC thermistors ($2.00) and divider resistors ($0.20) from sensors; coil temp via CAN, ambient not needed; prototype BOM ~$791 |
| 6.0 | 2026-02-20 | Manas Pradhan | Moved ISO1050DUB ($3.50) from Compute Modules to Actuation (now on Driver PCB); Compute $199.50→$196.00, Actuation $278.85→$282.35; component total unchanged ($541.05) |
| 7.0 | 2026-02-20 | Manas Pradhan | Replaced DS3225 servo ($15) with 24V BLDC motor ($25); Actuation $282.35→$292.35; component total $541.05→$551.05; prototype BOM $791.05→$801.05 |
| 8.0 | 2026-03-11 | Manas Pradhan | CID-1: replaced linear actuator+DRV8876 with NEMA 23 stepper+external driver; Actuation $300.48→$314.48 (net +$14); component total→$573.18; prototype BOM→$823.18 |
| 9.0 | 2026-03-11 | Manas Pradhan | Added PCF8574 #2 ($0.50) for GPIO headroom; Actuation $314.48→$314.98; component total→$573.68; prototype BOM→$823.68 |
| 9.1 | 2026-11-04 | Manas Pradhan | Application processor changed to Luckfox Pico Zero (RV1106G3) with 4" SPI LCD and SC3336 camera: Compute $196.00→$85.00, Sensors $43.70→$31.00; component total $554.68→$430.98; prototype BOM $804.68→$680.98; production unit ~$345→~$285 |
| 10.0 | 2026-11-04 | Manas Pradhan | Dispensers redesigned as servo carousels (Dispenser Servo Block): Actuation $314.98→$274.98 (−$40); component total $430.98→$390.98; prototype BOM $680.98→$640.98; production unit ~$285→~$261 |
| 10.1 | 2026-11-04 | Manas Pradhan | Camera IMX415-98 ($54): Sensors $31.00 → $73.00, component total $390.98 → $432.98, prototype BOM $640.98 → $682.98, production ~$273; chart, phases and ranking recomputed |
| 10.2 | 2026-11-04 | Manas Pradhan | RV1106 CAN node (MCP2518FD + ISO1050DUB #2, $6.50) added to Compute: $85.00 → $91.50; component total $432.98 → $439.48; prototype BOM $682.98 → $689.48; production ~$275 |
| 10.3 | 2026-11-04 | Manas Pradhan | MLX90614 removed (Sensors $73.00 → $60.80); CAN servo stirring motor + SN65HVD230 port (Actuation $274.98 → $296.18); 2S Li-ion pack added to Power ($30 → $42, replaces the external 12V UPS); component total $439.48 → $448.48; prototype BOM $689.48 → $710.48; production ~$285 |
