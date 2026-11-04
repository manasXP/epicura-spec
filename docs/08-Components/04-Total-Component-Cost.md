---
created: 2026-02-15
modified: 2026-11-04
version: 10.7
status: Draft
---

# Total Component Cost Summary

## 1. Overview

This document provides a consolidated view of all component costs for the Epicura kitchen robot prototype, including electronic components, mechanical parts, and projected production costs.

---

## 2. Category Summary

| Category | Subtotal | % of Total | Details |
|----------|----------|------------|---------|
| [[01-Compute-Module-Components|Compute Modules]] | $91.50 | 11% | Luckfox Pico Zero (RV1106G3, DU), STM32 (CSC, CS), 4" SPI LCD, RV1106 CAN node (MCP2518FD + ISO1050DUB #2), J_DOCK magnetic pogo pair, INA219 #2 battery monitor, cables |
| [[02-Actuation-Components|Actuation]] | $467.18 | 54% | Donor cooker (Philips OneChef NX5300/00: heating unit, controller, 6 L pot, lid, body), Dispenser Servo Block (4 servos + PCA9685, FID/CID carousels + canisters), PCF8574 #2 GPIO expander, SLD 6 V pumps/solenoids, load cells + NAU7802 ADCs + TCA9543A, ISO1050DUB #1 + SN65HVD230 CAN transceivers (CSC), 24V CAN servo stirring motor + J_SU port, relays, exhaust fan, filters |
| [[03-Sensor-Components|Sensors]] | $59.50 | 7% | IMX415-98 camera, reed switch, white LED ring (no thermometer: heating-unit-reported temperature) |
| **Component Total** | **$618.18** | **71%** | Electronic components only |

---

## 3. Detailed Component Breakdown

### 3.1 Compute Modules ($91.50)

| Item | Cost |
|------|------|
| Luckfox Pico Zero (RV1106G3, 256MB, 8GB eMMC) | $47.00 |
| STM32G0B1RE Nucleo (stands in for the CSC) | $11.00 |
| 4" ST7796S SPI LCD + FT6336 touch | $15.00 |
| RV1106 CAN node (MCP2518FD + crystal, ISO1050DUB #2) | $6.50 |
| Dock connector J_DOCK (8-pin magnetic pogo pair) | $6.00 |
| INA219 #2 battery monitor + shunt | $1.00 |
| Cables | $5.00 |

### 3.2 Actuation ($467.18)

| Item | Cost |
|------|------|
| Donor cooker: Philips OneChef NX5300/00 or equivalent (heating unit, controller, 6 L non-stick pot, glass lid, base body) | $230.00 |
| 24V CAN Servo Motor (main arm) | $45.00 |
| SN65HVD230 + stir-bus passives (regular CAN port, CSC) | $1.20 |
| Dispenser Servos — DSB (4x DS3218-class) | $40.00 |
| PCA9685 + DSB 6.0 V Rail Parts | $2.50 |
| FID Canisters (6x, ¼ tsp measure wheels) | $18.00 |
| FID Carousel Ring + Dosing Station | $8.00 |
| CID Carousel Ring + Base Plate + Chute | $12.00 |
| Index Gears + Carousel Bearings | $6.00 |
| PCF8574 #2 GPIO Expander | $0.50 |
| Peristaltic Pumps — SLD (2x, 6 V) | $20.00 |
| Solenoid Valves — SLD (2x, 6 V NC) | $8.00 |
| Load Cells — SLD (2×, 2 kg) | $10.00 |
| NAU7802 ×2 + TCA9543A — SLD | $5.00 |
| ISO1050DUB #1 (isolated CAN transceiver, STM32 node, CSC) | $3.50 |
| CAN Termination + Decoupling | $0.13 |
| Safety Relay Module (2x) | $6.00 |
| Motor Driver Board | $8.00 |
| Connectors + Wiring (incl. J_SU Micro-Fit pair) | $20.00 |
| Exhaust Fan + Filtration | $22.50 |
| Piezo Buzzer + MOSFET | $0.85 |

### 3.3 Sensors ($59.50)

| Item | Cost |
|------|------|
| IMX415-98 Camera | $54.00 |
| Reed Switch + White LED Ring | $5.00 |
| Passive Components | $0.50 |

---

## 4. Additional Costs

| Item | Cost | Notes |
|------|------|-------|
| Enclosure (3D printed) | $80.00 | PLA/PETG filament, prototype enclosure + internal brackets |
| Mechanical Parts (shaft, brackets, fasteners) | $50.00 | Stainless steel shaft (8mm), aluminum brackets, M3/M4 fasteners |
| Custom PCB (Unified PCB v4.0, Dispensing Unit) | $25.50 | 4-layer 160 × 90 mm, 5 pcs (JLCPCB); the DU board: Pico Zero slot, RV1106 CAN node (MCP2518FD + ISO1050DUB #2), dispenser drivers on the 6V_DSP rail, NAU7802 load-cell ADCs, TP5100 charger (1 A), J_DOCK pads |
| Custom PCB (Cooking Surface Controller, CSC v1.0) | $25.00 | 4-layer ~100 × 70 mm with isolation slot, 5 pcs (JLCPCB); in the CS base beside the LRS-75-24: STM32G0B1RE, ISO1050DUB #1 + B0505S (isolated bus to the heating unit and the dock), SN65HVD230 + Q_STIR stir-motor port, Q_DOCK dock charge switch, safety relay and fan drivers |
| Power Supply Module + Battery | $42.00 | Mean Well LRS-75-24 (24V/3.2A/76.8W) $30 in the CS + 2S1P 18650 Li-ion pack with PCM and NTC $12 in the DU: the Dispensing Unit's primary supply, charged at 1 A by the TP5100 whenever docked (no external 12V UPS) |
| Wiring / Connectors / Misc | $30.00 | JST, Dupont, ring terminals, heat shrink, cable ties |
| **Additional Total** | **$252.50** | $80.00 + $50.00 + $25.50 + $25.00 + $42.00 + $30.00 (pot supplied by the donor cooker, Actuation) |

---

## 5. Prototype Total BOM

| Category | Cost |
|----------|------|
| Electronic Components ($91.50 + $467.18 + $59.50) | $618.18 |
| Mechanical / Other | $252.50 |
| **Total BOM (Prototype)** | **$870.68** |
| **With Contingency (+20%)** | **~$1,045** |
| **With Tools & Consumables** | **$1,125-1,425** |

---

## 6. Prototype vs Production Cost Comparison

| Item | Prototype | Production (1000 qty) | Notes |
|------|-----------|----------------------|-------|
| Luckfox Pico Zero (RV1106G3) | $47.00 | $18.00 | Bare RV1106G3 (QFN128) on custom PCB, or Core1106 SoM, at volume |
| STM32G0B1 | $11.00 (Nucleo) | $3.50 (bare chip) | CSC PCB eliminates dev board |
| Display (4" SPI) | $15.00 | $8.00 | Same ST7796S panel, bulk pricing; stays SPI |
| Donor cooker: Philips OneChef NX5300/00 or equivalent (heating unit, controller, 6 L pot, glass lid, base body) | $230.00 (retail) | $60.00 (OEM heating unit + pot, bulk) | Self-contained unit with own PID, no custom mains electronics; OEM control board with CAN ships with the unit |
| FID + CID servo carousels (4 servos, PCA9685, rings, canisters) | $86.50 | $45.00 | Bulk servos, injection-molded rings and canisters |
| Pumps + Solenoids — SLD (6 V) | $28.00 | $14.00 | Bulk pricing |
| 24V CAN Servo Stirring Motor | $45.00 | $30.00 | Bulk pricing |
| Sensors (all) | $59.50 | $27.00 | Direct from manufacturer, MOQ pricing |
| Enclosure | $80.00 (3D print) | $15.00 (injection mold) | Mold cost amortized over production run |
| PCBs (Unified PCB v4.0 + CSC) | $50.50 (prototype) | $14.00 (panel production) | Two boards: DU board (Unified PCB v4.0) + Cooking Surface Controller (CSC) |
| Power Supply + 2S battery pack | $42.00 | $20.00 | Integrated SMPS on the CSC; bulk cells for the DU pack |
| Mechanical | $50.00 | $15.00 | Stamped brackets, bulk fasteners |
| Wiring / Connectors | $30.00 | $10.00 | Custom harness, bulk connectors |
| Exhaust + Filters | $22.50 | $8.00 (OEM blower + bulk filters) | Custom blower + injection-molded housing |
| Other (CAN nodes + stir-bus transceiver, J_DOCK pogo pair, J_SU, INA219 #2, relays, load cells + NAU7802 + mux, cables, buzzer) | $73.68 | $24.00 (integrated into PCBs + bulk) | Small components absorbed into the two custom PCBs at volume |
| **Total Unit** | **~$871** | **~$312** | **~64% cost reduction** |

---

## 7. Cost Breakdown Chart

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                 Epicura Prototype Component Costs                              │
│                                                                                │
│  Compute Modules (11%) ███████████                                             │
│  └─ RV1106 board (5%)  █████                                                   │
│  └─ Display (2%)       ██                                                      │
│  └─ STM32 (1%)         █                                                       │
│  └─ CAN node+dock+cables (2%) ██                                               │
│                                                                                │
│  Actuation (54%)       ██████████████████████████████████████████████████████  │
│  └─ FID/CID (10%)      ██████████                                              │
│  └─ Donor cooker (26%) ██████████████████████████                              │
│  └─ Stir motor (5%)    █████                                                   │
│  └─ SLD (5%)           █████                                                   │
│  └─ Other (7%)         ███████                                                 │
│                                                                                │
│  Sensors (7%)          ███████                                                 │
│  └─ Camera (6%)        ██████                                                  │
│  └─ Other (1%)         █                                                       │
│                                                                                │
│  Additional (29%)      █████████████████████████████                           │
│  └─ Enclosure (9%)     █████████                                               │
│  └─ Mechanical (6%)    ██████                                                  │
│  └─ PCBs/PSU/battery (11%) ███████████                                         │
│  └─ Wiring (3%)        ███                                                     │
│                                                                                │
│  Total Prototype BOM: ~$871                                                    │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Budget Planning by Development Phase

| Phase | Description | Estimated Spend | Cumulative |
|-------|-------------|----------------|------------|
| Phase 1 | Hardware Setup (Luckfox Pico Zero + STM32 + 4" LCD + PSU + 2S battery pack + Unified PCB v4.0 + CSC + J_DOCK pogo pair) | $190-290 | $190-290 |
| Phase 2-3 | Heater + Arm (OneChef NX5300/00 donor cooker + CAN servo motor + J_SU harness + mechanical) | $390-490 | $580-780 |
| Phase 4 | Vision (IMX415-98 camera + white LED ring + training data ingredients) | $75-105 | $655-885 |
| Phase 5 | Dispensing (Dispenser Servo Block: 4 servos + PCA9685, FID/CID carousels + canisters, SLD 6 V pumps/solenoids, 2× load cells + NAU7802 + TCA9543A) | $130-170 | $785-1,055 |
| Phase 6 | UI (display already counted; app dev = $0 software) | $0-20 | $785-1,075 |
| Phase 7 | Integration (consumables, replacements, debugging) | $50-100 | $835-1,175 |
| Contingency | Unexpected costs, rework, replacement parts | $200-400 | $1,035-1,575 |
| Tools | Soldering station, multimeter, 3D printer access | $100-200 | $1,135-1,775 |
| Ingredients | 30+ cook sessions for testing and training data | $50-100 | $1,185-1,875 |
| **Total Project Budget** | | **$1,500-2,500** | |

---

## 9. Cost Drivers Analysis

### 9.1 Highest Cost Components

| Rank | Component | Cost | % of BOM | Notes |
|------|-----------|------|----------|-------|
| 1 | Donor cooker: Philips OneChef NX5300/00 (heating unit, controller, 6 L pot, lid, body) | $230.00 | 26% | Retail donor for prototypes; production: OEM heating unit + pot $60 |
| 2 | Enclosure (3D print) | $80.00 | 9% | Prototype only; injection mold: $15/unit |
| 3 | IMX415-98 IR-CUT camera | $54.00 | 6% | Only Luckfox colour camera supported on the Pico Zero; bulk: ~$30 |
| 4 | Mechanical Parts | $50.00 | 6% | Shaft, brackets, fasteners |
| 5 | Luckfox Pico Zero (RV1106G3) | $47.00 | 5% | Bare RV1106G3 or Core1106 SoM on custom PCB: ~$18 |
| 6 | 24V CAN Servo Stirring Motor | $45.00 | 5% | CyberGear/RobStride-class; bulk: ~$30 |
| 7 | Dispenser Servos (4x, DSB) | $40.00 | 5% | DS3218-class; bulk: ~$6 each |
| 8 | Unified PCB v4.0 (DU board) | $25.50 | 3% | Panel production: $8/unit |
| 9 | Cooking Surface Controller PCB (CSC) | $25.00 | 3% | New board in the CS base; panel production: $6/unit |

### 9.2 Cost Reduction Opportunities

| Opportunity | Potential Savings | Effort | Risk |
|-------------|-------------------|--------|------|
| Volume pricing (1000 qty) | 40-50% overall | Low | Low |
| Unified PCB v4.0 + CSC volume production | $30-36/unit | Low | Low |
| Bare RV1106G3 / Core1106 SoM on custom PCB (replaces Pico Zero) | $25-30/unit | Medium | Low |
| Custom heater power stage (replace the commercial unit) | $15/unit | High | Medium |
| Injection-molded enclosure | $65/unit | High (tooling) | Low |
| Direct manufacturer sourcing (sensors) | $25-30/unit | Medium | Low |

---

## 10. Target Pricing (Production)

| Volume | Unit BOM Cost | Target Selling Price | Gross Margin |
|--------|--------------|---------------------|-------------|
| 100 units | $360-410 | Not viable (pre-production) | - |
| 1,000 units | $280-330 | $599-799 | 45-65% |
| 10,000 units | $225-265 | $499-699 | 47-68% |

> [!note] 2026-11-04 — the §6 production estimate moved ~$292 → ~$312 (OEM heating unit + pot at $60 replaces the $30 heating unit + $10 pot); it still sits inside the 1,000-unit band, so the bands above are unchanged.

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
| 10.4 | 2026-11-04 | Manas Pradhan | STM32G474RE → STM32G0B1RE: Nucleo $18 → $11, production chip $5 → $3.50; Compute $91.50 → $84.50; component total $448.48 → $441.48; prototype BOM $710.48 → $703.48; production ~$283 |
| 10.3 | 2026-11-04 | Manas Pradhan | MLX90614 removed (Sensors $73.00 → $60.80); CAN servo stirring motor + SN65HVD230 port (Actuation $274.98 → $296.18); 2S Li-ion pack added to Power ($30 → $42, replaces the external 12V UPS); component total $439.48 → $448.48; prototype BOM $689.48 → $710.48; production ~$285 |
| 10.5 | 2026-11-04 | Manas Pradhan | Three-unit split: CSC PCB ($25.00) added to Additional Costs; Compute $84.50 → $91.50 (J_DOCK pogo pair + INA219 #2), Actuation $296.18 → $297.18 (NAU7802 ×2 + TCA9543A + J_SU replace HX711 ×2), Sensors $60.80 → $59.50 (white LED ring replaces WS2812B + level shifter); component total $441.48 → $448.18; Additional Total re-summed from its rows ($262.00 shown, rows summed to $247.50) → $272.50; prototype BOM $703.48 → $720.68; production ~$302; battery reworded as the DU primary supply; chart, phases, ranking and targets recomputed |
| 10.6 | 2026-11-04 | Manas Pradhan | Heater changed from the Microwave Induction Surface ($60, bulk $40) to a commercial Electric Heating Unit of the rice-cooker class ($45, bulk $30; same CAN contract): Actuation $297.18 → $282.18, component total $448.18 → $433.18, prototype BOM $720.68 → $705.68 (contingency ~$847), production ~$302 → ~$292 (~59% reduction); percentages (Actuation 40%, component 61%, Additional 39%), chart, phase budget (Phase 2-3 $205-305, cumulatives −$15), ranking and cost-reduction rows recomputed; pot no longer needs to be induction-compatible |
| 10.7 | 2026-11-04 | Manas Pradhan | Heating unit referenced to the Philips OneChef NX5300/00: heater line → donor cooker (heating unit, controller, 6 L non-stick pot, glass lid, base body) $45 → $230, separate pot line ($20) removed from Additional Costs and §6; production heater + pot $30 + $10 → $60 (OEM heating unit + pot, bulk): Actuation $282.18 → $467.18, component total $433.18 → $618.18, Additional $272.50 → $252.50, prototype BOM $705.68 → $870.68 (contingency ~$1,045), production ~$292 → ~$312 (~64% reduction); percentages (Actuation 54%, component 71%, Additional 29%), chart, phase budget (Phase 2-3 $390-490, cumulatives +$185), §9.1 ranking recomputed; §10 note |
