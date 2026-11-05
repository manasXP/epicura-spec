---
created: 2026-02-15
modified: 2026-11-05
version: 10.15
status: Draft
---

# Total Component Cost Summary

## 1. Overview

This document provides a consolidated view of all component costs for the Epicura kitchen robot prototype, including electronic components, mechanical parts, and projected production costs.

---

## 2. Category Summary

| Category | Subtotal | % of Total | Details |
|----------|----------|------------|---------|
| [[01-Compute-Module-Components|Compute Modules]] | $89.80 | 10% | Luckfox Pico Zero (RV1106G3, DU), DU STM32G0B1RET6 (dispensing + DU CAN node, DU), STM32 (CSC, CS), 4" SPI LCD, SN65HVD230 (DU CAN node, non-isolated), J_DOCK magnetic pogo pair, INA219 #2 battery monitor, cables |
| [[02-Actuation-Components|Actuation]] | $463.98 | 49% | Donor cooker (Philips OneChef NX5300/00: heating unit, controller, body; its round pot and lid are not used), Dispenser Servo Block (4 servos + PCA9685, FID/CID carousels + canisters), PCF8574 #2 GPIO expander, SLD drawer tanks with 6 V pumps (Hall tachs) and check-valve nozzles, ISO1050DUB #1 + #3 with B0505S #1 + #2 (two isolated CAN ports, CSC), 24V CAN servo stirring motor + J_SU port, K_SAFE / K_SU relays, exhaust fan, filters |
| [[03-Sensor-Components|Sensors]] | $59.50 | 6% | IMX415-98 camera, reed switch, white LED ring (no thermometer: heating-unit-reported temperature) |
| **Component Total** | **$613.28** | **65%** | Electronic components only |

---

## 3. Detailed Component Breakdown

### 3.1 Compute Modules ($89.80)

| Item | Cost |
|------|------|
| Luckfox Pico Zero (RV1106G3, 256MB, 8GB eMMC) | $47.00 |
| STM32G0B1RE Nucleo (stands in for the CSC) | $11.00 |
| 4" ST7796S SPI LCD + FT6336 touch | $15.00 |
| DU STM32G0B1RET6 + crystal + J_SWD (dispensing, DU CAN node) | $4.00 |
| SN65HVD230 (DU CAN node transceiver, non-isolated) | $0.80 |
| Dock connector J_DOCK (8-pin magnetic pogo pair) | $6.00 |
| INA219 #2 battery monitor + shunt | $1.00 |
| Cables | $5.00 |

### 3.2 Actuation ($463.98)

| Item | Cost |
|------|------|
| Donor cooker: Philips OneChef NX5300/00 or equivalent (heating unit, controller, base body; its round 6 L pot and glass lid are not used — pot costed in §4) | $230.00 |
| 24V CAN Servo Motor (main arm) | $45.00 |
| ISO1050DUB #3 + B0505S #2 + stir-bus passives (isolated CAN port #2, CSC) | $5.20 |
| K_SU SU-PSU relay + J_SU_IN + J_SAFE DF11-6DP (CSC) | $3.80 |
| Dispenser Servos — DSB (4x DS3218-class) | $40.00 |
| PCA9685 + DSB 6.0 V Rail Parts | $2.50 |
| FID Canisters (6x, ¼ tsp measure wheels) | $18.00 |
| FID Carousel Ring + Dosing Station | $8.00 |
| CID Carousel Ring + Base Plate + Chute | $12.00 |
| Index Gears + Carousel Bearings | $6.00 |
| PCF8574 #2 GPIO Expander | $0.50 |
| Pumps — SLD (6 V peristaltic oil + 6 V diaphragm water, Hall tachs) | $15.00 |
| Nozzle Check-Valve Cartridges — SLD (2x) | $3.00 |
| Drawer Tanks — SLD (200 mL oil + 500 mL water) | $12.00 |
| Hall Switches ×6 + Magnets — SLD | $2.00 |
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
| Custom PCB (Unified PCB v5.3, Dispensing Unit) | $25.50 | 4-layer annular-sector board in the Ø350 mm DU's service ring (R 135–172 mm × ≈ 150°, TBC; arc-outline price to be re-quoted), 5 pcs (JLCPCB); the DU board: Pico Zero slot, DU STM32G0B1RE (dispensing, host link, CAN node with a non-isolated SN65HVD230; no isolation island), dispenser drivers on the 6V_DSP rail, SLD pump drivers + six Hall inputs, TP5100 charger (1 A), J_DOCK pads |
| Custom PCB (Cooking Surface Controller, CSC v1.0) | $25.00 | 4-layer ~100 × 70 mm with isolation slot, 5 pcs (JLCPCB); in the CS base beside the three Mean Well PSUs, powered from its own LRS-35-12 (J_12V_IN; neither LRS-75-24 feeds it and nothing is tapped from the heating unit; one MP1584EN 12 → 5 V): STM32G0B1RE, ISO1050DUB #1 + B0505S #1 (isolated bus to the heating unit and the dock), ISO1050DUB #3 + B0505S #2 isolated stir-motor port with the floating SU island (J_SU_IN → F_SU → J_STIR_PWR), Q_DOCK dock charge switch on the LRS-75-24 #1 feed (J_DU_IN, DU only), K_SAFE / K_SU relay drivers and fan drivers |
| Power Supply Module + Battery | $94.00 | Three PSUs in the CS rear: 2× Mean Well LRS-75-24 (24V/3.2A/76.8W) $30 each — #1 for the Dispensing Unit only (dock charge feed), #2 for the Stirring Unit (floating 24V_SU / GND_SU output, AC input through the CSC relay K_SU) — + 1× Mean Well LRS-35-12 (12V/3A/36W) $12 for the CSC, the fans and the relay coils (AC input unswitched; nothing is tapped from the heating unit) + 2S2P 18650 Li-ion pack (5,200 mAh, ~38 Wh) with PCM and NTC $22 in the DU: the Dispensing Unit's primary supply, charged at 1 A by the TP5100 whenever docked (no external 12V UPS) |
| Wiring / Connectors / Misc | $30.00 | JST, Dupont, ring terminals, heat shrink, cable ties |
| Pot (25 × 25 × 12 cm rounded-square non-stick pot + glass lid) | $25.00 | Commercial 25 cm square casserole pot for prototypes; the donor cooker's round 6 L inner pot is not used ([[../02-Hardware/04-Mechanical-Design|Mechanical Design]] §2.2) |
| **Additional Total** | **$329.50** | $80.00 + $50.00 + $25.50 + $25.00 + $94.00 + $30.00 + $25.00 |

---

## 5. Prototype Total BOM

| Category | Cost |
|----------|------|
| Electronic Components ($89.80 + $463.98 + $59.50) | $613.28 |
| Mechanical / Other | $329.50 |
| **Total BOM (Prototype)** | **$942.78** |
| **With Contingency (+20%)** | **~$1,145** |
| **With Tools & Consumables** | **$1,220-1,520** |

---

## 6. Prototype vs Production Cost Comparison

| Item | Prototype | Production (1000 qty) | Notes |
|------|-----------|----------------------|-------|
| Luckfox Pico Zero (RV1106G3) | $47.00 | $18.00 | Bare RV1106G3 (QFN128) on custom PCB, or Core1106 SoM, at volume |
| STM32G0B1 | $11.00 (Nucleo) | $3.50 (bare chip) | CSC PCB eliminates dev board |
| Display (4" SPI) | $15.00 | $8.00 | Same ST7796S panel, bulk pricing; stays SPI |
| Donor cooker: Philips OneChef NX5300/00 or equivalent (heating unit, controller, base body; its round pot and lid are not used) | $230.00 (retail) | $50.00 (OEM heating unit, bulk) | Self-contained unit with own PID, no custom mains electronics; OEM control board with CAN ships with the unit |
| Pot: 25 × 25 × 12 cm rounded-square non-stick pot + glass lid | $25.00 | $10.00 | Commercial square casserole pot for prototypes; custom pressed, bulk at volume |
| FID + CID servo carousels (4 servos, PCA9685, rings, canisters) | $86.50 | $45.00 | Bulk servos, injection-molded rings and canisters |
| Pumps + check-valve cartridges + drawer tanks — SLD (6 V) | $30.00 | $14.00 | Bulk pricing; molded tanks |
| 24V CAN Servo Stirring Motor | $45.00 | $30.00 | Bulk pricing |
| Sensors (all) | $59.50 | $27.00 | Direct from manufacturer, MOQ pricing |
| Enclosure | $80.00 (3D print) | $15.00 (injection mold) | Mold cost amortized over production run |
| PCBs (Unified PCB v5.3 + CSC) | $50.50 (prototype) | $14.00 (panel production) | Two boards: DU board (Unified PCB v5.3, annular sector) + Cooking Surface Controller (CSC) |
| Power Supply (2× LRS-75-24: DU + SU; 1× LRS-35-12: CSC) + 2S2P 18650 battery pack (5,200 mAh) | $94.00 | $53.00 | Three bulk SMPS in the CS (the SU one floating, behind K_SU; the 12 V one for the controller, fans and relays); bulk cells for the DU pack |
| Mechanical | $50.00 | $15.00 | Stamped brackets, bulk fasteners |
| Wiring / Connectors | $30.00 | $10.00 | Custom harness, bulk connectors |
| Exhaust + Filters | $22.50 | $8.00 (OEM blower + bulk filters) | Custom blower + injection-molded housing |
| Other (DU STM32 + CAN transceivers incl. the isolated stir-bus ISO1050DUB #3 + B0505S #2, K_SU relay + J_SU_IN, J_DOCK pogo pair, J_SU, INA219 #2, relays, SLD Hall switches + magnets, cables, buzzer) | $66.78 | $27.00 (integrated into PCBs + bulk) | Small components absorbed into the two custom PCBs at volume |
| **Total Unit** | **~$943** | **~$348** | **~64% cost reduction** |

---

## 7. Cost Breakdown Chart

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                 Epicura Prototype Component Costs                              │
│                                                                                │
│  Compute Modules (10%) ██████████                                              │
│  └─ RV1106 board (5%)  █████                                                   │
│  └─ Display (2%)       ██                                                      │
│  └─ STM32 (1%)         █                                                       │
│  └─ CAN node+dock+cables (2%) ██                                               │
│                                                                                │
│  Actuation (50%)       ██████████████████████████████████████████████████      │
│  └─ FID/CID (9%)       █████████                                               │
│  └─ Donor cooker (24%) ████████████████████████                                │
│  └─ Stir motor (5%)    █████                                                   │
│  └─ SLD (5%)           █████                                                   │
│  └─ Other (7%)         ███████                                                 │
│                                                                                │
│  Sensors (6%)          ██████                                                  │
│  └─ Camera (6%)        ██████                                                  │
│  └─ Other (1%)         █                                                       │
│                                                                                │
│  Additional (34%)      ██████████████████████████████████                      │
│  └─ Enclosure (8%)     ████████                                                │
│  └─ Mechanical (5%)    █████                                                   │
│  └─ PCBs/PSU/battery (15%) ███████████████                                     │
│  └─ Wiring (3%)        ███                                                     │
│  └─ Pot + lid (3%)     ███                                                     │
│                                                                                │
│  Total Prototype BOM: ~$954                                                    │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Budget Planning by Development Phase

| Phase | Description | Estimated Spend | Cumulative |
|-------|-------------|----------------|------------|
| Phase 1 | Hardware Setup (Luckfox Pico Zero + 2× STM32 + 4" LCD + 3× PSU (DU, SU, CSC) + 2S2P 18650 battery pack + Unified PCB v5.0 + CSC + J_DOCK pogo pair) | $242-342 | $242-342 |
| Phase 2-3 | Heater + Arm (OneChef NX5300/00 donor cooker + 25 cm rounded-square pot with lid + CAN servo motor + J_SU harness + mechanical) | $415-515 | $657-857 |
| Phase 4 | Vision (IMX415-98 camera + white LED ring + training data ingredients) | $75-105 | $732-962 |
| Phase 5 | Dispensing (Dispenser Servo Block: 4 servos + PCA9685, FID/CID carousels + canisters, SLD drawer tanks + 6 V pumps with Hall tachs + check-valve nozzles) | $120-160 | $852-1,122 |
| Phase 6 | UI (display already counted; app dev = $0 software) | $0-20 | $852-1,142 |
| Phase 7 | Integration (consumables, replacements, debugging) | $50-100 | $902-1,242 |
| Contingency | Unexpected costs, rework, replacement parts | $200-400 | $1,102-1,642 |
| Tools | Soldering station, multimeter, 3D printer access | $100-200 | $1,212-1,852 |
| Ingredients | 30+ cook sessions for testing and training data | $50-100 | $1,262-1,952 |
| **Total Project Budget** | | **$1,500-2,500** | |

---

## 9. Cost Drivers Analysis

### 9.1 Highest Cost Components

| Rank | Component | Cost | % of BOM | Notes |
|------|-----------|------|----------|-------|
| 1 | Donor cooker: Philips OneChef NX5300/00 (heating unit, controller, body; pot not used) | $230.00 | 24% | Retail donor for prototypes; production: OEM heating unit $50 |
| 2 | Enclosure (3D print) | $80.00 | 8% | Prototype only; injection mold: $15/unit |
| 3 | IMX415-98 IR-CUT camera | $54.00 | 6% | Only Luckfox colour camera supported on the Pico Zero; bulk: ~$30 |
| 4 | Mechanical Parts | $50.00 | 5% | Shaft, brackets, fasteners |
| 5 | Luckfox Pico Zero (RV1106G3) | $47.00 | 5% | Bare RV1106G3 or Core1106 SoM on custom PCB: ~$18 |
| 6 | 24V CAN Servo Stirring Motor | $45.00 | 5% | CyberGear/RobStride-class; bulk: ~$30 |
| 7 | Dispenser Servos (4x, DSB) | $40.00 | 4% | DS3218-class; bulk: ~$6 each |
| 8 | Unified PCB v5.0 (DU board) | $25.50 | 3% | Panel production: $8/unit |
| 9 | Cooking Surface Controller PCB (CSC) | $25.00 | 3% | New board in the CS base; panel production: $6/unit |
| 10 | Pot (25 cm rounded-square non-stick + glass lid) | $25.00 | 3% | Commercial square casserole; custom pressed at volume: $10 |

### 9.2 Cost Reduction Opportunities

| Opportunity | Potential Savings | Effort | Risk |
|-------------|-------------------|--------|------|
| Volume pricing (1000 qty) | 40-50% overall | Low | Low |
| Unified PCB v5.0 + CSC volume production | $30-36/unit | Low | Low |
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

> [!note] 2026-11-04 — the §6 production estimate moved ~$292 → ~$312 (OEM heating unit + pot at $60 replaces the $30 heating unit + $10 pot); it still sits inside the 1,000-unit band, so the bands above are unchanged. Later the same day the pot became a separate line again (25 cm rounded-square pot: OEM heating unit $50 + pressed pot $10), total still ~$312; the 5,200 mAh DU pack (+$5 at volume) then took it to ~$317. With CSC v1.3 the Stirring Unit gets its own LRS-75-24 (+$20 at volume) and an isolated stir port + K_SU (+$3), taking the estimate to ~$340 — above the 1,000-unit band; the bands are left for the next pricing review. A dedicated LRS-35-12 for the CSC (+$8 at volume, 2026-11-05) takes it to ~$348.

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
| 10.8 | 2026-11-04 | Manas Pradhan | Pot changed to a 25 × 25 × 12 cm rounded-square non-stick pot (Mechanical Design §2.2): pot + glass lid $25 added to Additional Costs (production $10, custom pressed; OEM heating unit $60 → $50 without pot): Additional $252.50 → $277.50, prototype BOM $870.68 → $895.68 (contingency ~$1,075, with tools $1,150-1,450), production ~$312 unchanged (~65% reduction); percentages (Compute 10%, Actuation 52%, component 69%, Additional 31%), chart, phase budget (Phase 2-3 $415-515, cumulatives +$25), §9.1 rank 10 and §10 note updated |
| 10.9 | 2026-11-04 | Manas Pradhan | Dispensing Unit battery doubled to 2S2P 18650, 5,200 mAh (~38 Wh): pack $12 → $22 (production $20 → $25 with the PSU): Additional $277.50 → $287.50, prototype BOM $895.68 → $905.68 (contingency ~$1,085, with tools $1,160-1,460), production ~$312 → ~$317; component 68%, Additional 32%, donor cooker 25%, PCBs/PSU/battery 11%; chart, Phase 1 $200-300 (cumulatives +$10), §9.1 and §10 note updated |
| 10.10 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: DU STM32G0B1RET6 + crystal + J_SWD ($4.00) replaces the MCP2518FD + crystal ($3.00) in Compute, ISO1050DUB #2 now the DU STM32's transceiver: Compute $91.50 → $92.50, component total $618.18 → $619.18, prototype BOM $905.68 → $906.68 (contingency ~$1,090), production ~$317 unchanged; Unified PCB renamed v5.0 in Additional Costs, comparison, Phase 1, §9.1 and §9.2 |
| 10.12 | 2026-11-04 | Manas Pradhan | DU CAN node non-isolated (Unified PCB v5.1): SN65HVD230 ($0.80) replaces ISO1050DUB #2 ($3.50) in Compute ($92.50 → $89.80); component total $626.98 → $624.28; prototype BOM $944.48 → $941.78 (~$942); Other $82.48 → $79.78; production unchanged |
| 10.11 | 2026-11-04 | Manas Pradhan | Aligned to CSC v1.3 (both CAN ports isolated, Stirring Unit on its own PSU): Actuation $467.18 → $474.98 (SN65HVD230 −$0.90; ISO1050DUB #3 +$3.50, B0505S-1WR3 #2 +$1.40, K_SU G5V-2 + Q_KSU + XT30 J_SU_IN + DF11-6DP J_SAFE lot +$3.80), component total $619.18 → $626.98; second Mean Well LRS-75-24 for the SU (+$30) in Power Supply ($52 → $82), Additional $287.50 → $317.50; prototype BOM $906.68 → $944.48 (contingency ~$1,135, with tools $1,210-1,510); production PSU $25 → $45, Other $24 → $27, ~$317 → ~$340 (above the 1,000-unit band, noted in §10); percentages (Actuation 50%, Sensors 6%, component 66%, Additional 34%), chart, Phase 1 $230-330 (cumulatives +$30), §9.1 and CSC PCB description updated |
| 10.13 | 2026-11-05 | Manas Pradhan | Aligned to CSC v1.5: the CSC, fans and relay coils run from the heating unit's control-board 12 V SELV rail (J_HU_PWR), LRS-75-24 #1 is the DU's dock feed only; CSC PCB and Power Supply description lines updated. No price change (the dropped MP1584EN is not itemised; the IRM-20-12 fallback is listed as "if needed" and not added), totals unchanged |
| 10.14 | 2026-11-05 | Manas Pradhan | Aligned to CSC v1.6 (reversing 10.13): the CSC, fans and relay coils run from a dedicated Mean Well LRS-35-12 (+$12) and nothing is tapped from the heating unit; the IRM-20-12 "if needed" note is removed. Power Supply $82.00 → $94.00 (2× $30 LRS-75-24 + $12 LRS-35-12 + $22 pack), Additional $317.50 → $329.50, prototype BOM $941.78 → $953.78 (contingency ~$1,145, with tools $1,220-1,520); production PSU $45 → $53, ~$340 → ~$348 (~64% reduction unchanged, §10 note); PCBs/PSU/battery 14% → 15% in the chart (other percentages move < 1 point and are left); Phase 1 $230-330 → $242-342 (cumulatives +$12); CSC PCB description updated |
| 10.15 | 2026-11-05 | Manas Pradhan | Robot-mop SLD (Actuation v10.8): pumps $20 → $15, solenoids $8 → check-valve cartridges $3, load cells $10 → drawer tanks $12, NAU7802 + TCA9543A $5 → Hall switches + magnets $2; Actuation $474.98 → $463.98, component total $624.28 → $613.28, prototype BOM $953.78 → $942.78; Unified PCB v5.3 annular-sector note (price to be re-quoted); Phase 5 and cumulative ranges −$10 |
