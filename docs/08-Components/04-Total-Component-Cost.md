---
created: 2026-02-15
modified: 2026-11-04
version: 9.1
status: Draft
---

# Total Component Cost Summary

## 1. Overview

This document provides a consolidated view of all component costs for the Epicura kitchen robot prototype, including electronic components, mechanical parts, and projected production costs.

---

## 2. Category Summary

| Category | Subtotal | % of Total | Details |
|----------|----------|------------|---------|
| [[01-Compute-Module-Components|Compute Modules]] | $85.00 | 12% | Luckfox Pico Zero (RV1106G3), STM32, 4" SPI LCD, cables |
| [[02-Actuation-Components|Actuation]] | $314.98 | 46% | Induction hob, P-ASD pneumatic system + PCF8574 #1 I2C expander, PCF8574 #2 GPIO headroom expander, CID-1 NEMA 23 stepper + driver, CID-2 linear actuator, SLD pumps/solenoids/load cell, ISO1050DUB CAN transceiver, 24V BLDC motor, relays, exhaust fan, filters |
| [[03-Sensor-Components|Sensors]] | $31.00 | 5% | SC3336 camera, IR thermo, reed switch, LED ring + level shifter |
| **Component Total** | **$430.98** | **63%** | Electronic components only |

---

## 3. Detailed Component Breakdown

### 3.1 Compute Modules ($85.00)

| Item | Cost |
|------|------|
| Luckfox Pico Zero (RV1106G3, 256MB, 8GB eMMC) | $47.00 |
| STM32G474RE Nucleo | $18.00 |
| 4" ST7796S SPI LCD + FT6336 touch | $15.00 |
| Cables | $5.00 |

### 3.2 Actuation ($314.48)

| Item | Cost |
|------|------|
| Microwave Induction Surface (CAN) | $60.00 |
| 24V BLDC Motor (main arm) | $25.00 |
| P-ASD Pneumatic System (pump, valves, accumulator, regulator, sensor, tubing, cartridges, relief valve, PCF8574 #1) | $90.50 |
| PCF8574 #2 GPIO Headroom Expander | $0.50 |
| NEMA 23 Stepper Motor — CID-1 | $15.00 |
| External Stepper Driver — CID-1 | $10.00 |
| Linear Actuator — CID-2 (1x) | $8.00 |
| Peristaltic Pumps — SLD (2x) | $20.00 |
| Solenoid Valves — SLD (2x) | $8.00 |
| Load Cells + HX711 — SLD (2×) | $16.00 |
| H-Bridge Driver — CID-2 (1x) | $2.50 |
| Limit Switches — CID (3x) | $1.50 |
| ISO1050DUB (isolated CAN transceiver) | $3.50 |
| CAN Termination + Decoupling | $0.13 |
| Safety Relay Module (2x) | $6.00 |
| Motor Driver Board | $8.00 |
| Connectors + Wiring | $17.00 |
| Exhaust Fan + Filtration | $22.50 |
| Piezo Buzzer + MOSFET | $0.85 |

### 3.3 Sensors ($31.00)

| Item | Cost |
|------|------|
| SC3336 Camera | $12.00 |
| MLX90614 IR Thermometer | $12.00 |
| Reed Switch + LED Ring + 74AHCT1G125 | $6.30 |
| Passive Components | $0.70 |

---

## 4. Additional Costs

| Item | Cost | Notes |
|------|------|-------|
| Enclosure (3D printed) | $80.00 | PLA/PETG filament, prototype enclosure + internal brackets |
| Mechanical Parts (shaft, brackets, fasteners) | $50.00 | Stainless steel shaft (8mm), aluminum brackets, M3/M4 fasteners |
| Custom PCB (Unified PCB) | $25.50 | Single 4-layer board, 5 pcs (JLCPCB) |
| Power Supply Module | $30.00 | Mean Well LRS-75-24 (24V/3.2A/76.8W) + buck converters (24V→5V) |
| Wiring / Connectors / Misc | $30.00 | JST, Dupont, ring terminals, heat shrink, cable ties |
| Pot (induction-compatible) | $20.00 | Stainless steel 304, 3-4L capacity, flat base |
| **Additional Total** | **$250.00** | |

---

## 5. Prototype Total BOM

| Category | Cost |
|----------|------|
| Electronic Components | $430.98 |
| Mechanical / Other | $250.00 |
| **Total BOM (Prototype)** | **$680.98** |
| **With Contingency (+20%)** | **~$817** |
| **With Tools & Consumables** | **$950-1,250** |

---

## 6. Prototype vs Production Cost Comparison

| Item | Prototype | Production (1000 qty) | Notes |
|------|-----------|----------------------|-------|
| Luckfox Pico Zero (RV1106G3) | $47.00 | $18.00 | Bare RV1106G3 (QFN128) on custom PCB, or Core1106 SoM, at volume |
| STM32G474 | $18.00 (Nucleo) | $5.00 (bare chip) | Custom PCB eliminates dev board |
| Display (4" SPI) | $15.00 | $8.00 | Same ST7796S panel, bulk pricing; stays SPI |
| Microwave Induction Surface | $60.00 (CAN module) | $40.00 (bulk pricing) | Self-contained module, no custom driver |
| P-ASD system (pump+valves+cartridges) | $90.00 | $50.00 | Bulk pricing, simplified assembly |
| NEMA 23 stepper + driver (CID-1) | $25.00 | $15.00 | Bulk pricing |
| Linear Actuator — CID-2 (1x) | $8.00 | $4.00 | Bulk pricing |
| Pumps + Solenoids — SLD | $28.00 | $14.00 | Bulk pricing |
| 24V BLDC Stirring Motor | $25.00 | $15.00 | Bulk pricing |
| Sensors (all) | $31.00 | $18.00 | Direct from manufacturer, MOQ pricing |
| Enclosure | $80.00 (3D print) | $15.00 (injection mold) | Mold cost amortized over production run |
| PCBs | $25.50 (prototype) | $8.00 (panel production) | Single unified PCB (controller + driver merged) |
| Power Supply | $30.00 | $12.00 | Integrated SMPS on main PCB |
| Mechanical | $50.00 | $15.00 | Stamped brackets, bulk fasteners |
| Pot + Accessories | $20.00 | $10.00 | OEM sourcing |
| Wiring / Connectors | $30.00 | $10.00 | Custom harness, bulk connectors |
| Exhaust + Filters | $22.50 | $8.00 (OEM blower + bulk filters) | Custom blower + injection-molded housing |
| Other (CAN, relays, drivers, load cell, cables, buzzer) | $94.85 | $20.00 (integrated into PCB + bulk) | Small components absorbed into custom PCB at volume |
| **Total Unit** | **~$681** | **~$285** | **~58% cost reduction** |

---

## 7. Cost Breakdown Chart

```
┌────────────────────────────────────────────────────────────────────────────┐
│                 Epicura Prototype Component Costs                         │
│                                                                          │
│  Compute Modules (12%)  ████████████                                     │
│  └─ RV1106 board (7%)   ███████                                          │
│  └─ Display (2%)        ██                                               │
│  └─ STM32 (3%)          ███                                              │
│  └─ Other (1%)          █                                                │
│                                                                          │
│  Actuation (46%)        ██████████████████████████████████████████████   │
│  └─ P-ASD system (13%)  █████████████                                    │
│  └─ Induction (9%)      █████████                                        │
│  └─ CID/SLD (12%)       ████████████                                     │
│  └─ Other (12%)         ████████████                                     │
│                                                                          │
│  Sensors (5%)           █████                                            │
│  └─ Camera (2%)         ██                                               │
│  └─ Other (3%)          ███                                              │
│                                                                          │
│  Additional (37%)       █████████████████████████████████████            │
│  └─ Enclosure (12%)     ████████████                                     │
│  └─ Mechanical (7%)     ███████                                          │
│  └─ PCBs/PSU (8%)       ████████                                         │
│                                                                          │
│  Total Prototype BOM: ~$681                                              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Budget Planning by Development Phase

| Phase | Description | Estimated Spend | Cumulative |
|-------|-------------|----------------|------------|
| Phase 1 | Hardware Setup (Luckfox Pico Zero + STM32 + 4" LCD + PSU) | $150-250 | $150-250 |
| Phase 2-3 | Induction + Arm (hob + servos + load cells + mechanical) | $200-300 | $350-550 |
| Phase 4 | Vision (SC3336 camera + LED ring + level shifter + training data ingredients) | $30-60 | $380-610 |
| Phase 5 | Dispensing (P-ASD pneumatic system, CID actuators, SLD pumps/solenoids/2× load cells) | $168-208 | $548-818 |
| Phase 6 | UI (display already counted; app dev = $0 software) | $0-20 | $548-838 |
| Phase 7 | Integration (consumables, replacements, debugging) | $50-100 | $598-938 |
| Contingency | Unexpected costs, rework, replacement parts | $200-400 | $798-1,338 |
| Tools | Soldering station, multimeter, 3D printer access | $100-200 | $898-1,538 |
| Ingredients | 30+ cook sessions for testing and training data | $50-100 | $948-1,638 |
| **Total Project Budget** | | **$1,500-2,500** | |

---

## 9. Cost Drivers Analysis

### 9.1 Highest Cost Components

| Rank | Component | Cost | % of BOM | Notes |
|------|-----------|------|----------|-------|
| 1 | P-ASD Pneumatic System | $90.00 | 13% | Pump+valves+cartridges; bulk: $50 |
| 2 | Enclosure (3D print) | $80.00 | 12% | Prototype only; injection mold: $15/unit |
| 3 | Microwave Induction Surface | $60.00 | 9% | Self-contained CAN module; bulk: $40 |
| 4 | Mechanical Parts | $50.00 | 7% | Shaft, brackets, fasteners |
| 5 | Luckfox Pico Zero (RV1106G3) | $47.00 | 7% | Bare RV1106G3 or Core1106 SoM on custom PCB: ~$18 |
| 6 | Unified PCB | $25.50 | 4% | Single board; panel production: $8/unit |

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
