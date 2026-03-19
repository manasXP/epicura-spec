# Unified PCB Schematic Review -- Issues Found

**Date:** 2026-03-19
**Project:** Epicura -- Autonomous Kitchen Robot
**Files Reviewed:**
- `Unified_v1.kicad_sch` (root sheet)
- `Control.kicad_sch` (STM32G474 + power)
- `Connector.kicad_sch` (all external connectors)
- `Driver.kicad_sch` (MOSFETs, regulators, motor drivers)

---

## CRITICAL Issues

### 1. Driver Sheet is Completely Disconnected
The `Driver.kicad_sch` sub-sheet (page 4) has **zero hierarchical pins** defined on the root sheet. The Driver sheet block has no `(pin ...)` entries at all -- meaning none of its internal signals are connected to the rest of the design. This makes the entire driver section electrically isolated from Control and Connector sheets.

### 2. CAN Transceiver Missing from Control Sheet
The Control sheet defines `PB8_MW_FDCAN1_RX` and `PB9_MW_FDCAN1_TX` labels but has **no CAN transceiver IC** (ISO1050DUB is specified in the docs). The Driver sheet reportedly contains U3 (ISO1050DUB), but since the Driver sheet is disconnected (issue #1), CAN_TX/RX from the STM32 cannot reach the transceiver.

### 3. 24V Input Connector Severely Undersized
The Connector sheet uses **B2B-XH-A** (JST XH 2-pin, rated 3A/pin = 6A max) for J_VIN1. The documentation specifies **XT30** connectors. At 24V with up to 3.2A continuous draw (and BLDC motor peaks), the JST XH is marginal. The docs also call for 5A polyfuse + SS54 + SMBJ24A TVS -- verify these match.

### 4. Connector Types Don't Match Documentation

| Connector | Doc Specifies | Schematic Has |
|-----------|--------------|---------------|
| J_24V_IN | XT30 or JST-VH | B2B-XH-A (JST XH 2-pin) |
| J_12V_UPS | XT30 | B2B-XH-A (JST XH 2-pin) |
| J_BLDC | Hirose DF11-6DP-2DS | B6B-XH-A (JST XH 6-pin) |
| J_PASD | Hirose DF11-16DP-2DS | B16B-XH-A (JST XH 16-pin) |
| J_SLD | Hirose DF11-16DP-2DS | B12B-XH-A (JST XH 12-pin) -- **also wrong pin count** |
| J_CID | Hirose DF11-14DP-2DS | B4B-XH-A (JST XH 4-pin) -- **also wrong pin count** |
| J_IR_LED | Hirose DF11-8DP-2DS (merged) | Separate J_IR1 (SM04B-SRSS 4-pin) + J_LED1 (B3B-XH-A 3-pin) |
| J_SWD | 10-pin 1.27mm | Conn_01x06 (6-pin 1.27mm) |

### 5. Missing Pin Assignments vs Documentation
The docs specify these pins but the schematic uses different assignments:

| Function | Doc Pin | Schematic Pin |
|----------|---------|---------------|
| SPI2_NSS | PB12 | Labeled as `SPI2_NSS_CM5_IO8` (root sheet) -- pin mapping unclear |
| SPI2_SCK | PB13 | Labeled differently |
| SPI2_MISO | PB14 | Labeled differently |
| SPI2_MOSI | PB15 | Labeled differently |
| HSE Crystal | PF0/PF1 | Schematic shows HSE_IN/HSE_OUT (verify actual STM32 pins) |
| Oil HX711 | PC11 (SCK), PC12 (DOUT) | Schematic only has `PC0_LOADCELL_SCLK`, `PC1_LOADCELL_DOUT` (single HX711, not two) |
| Water HX711 | PC9 (SCK), PC10 (DOUT) | **Missing entirely** |
| CID-1 Home Limit | PB6 | **Missing** |
| CID-2 Home Limit | PD2 | **Missing** |

---

## HIGH Severity Issues

### 6. Missing NRST Pull-up and Filter
No 10k pull-up resistor to VDD on NRST pin, and no 100nF filter capacitor to GND. SW1 (reset switch) also has **no footprint assigned**.

### 7. Missing USB Circuit Components
PA11 (USB_DM) and PA12 (USB_DP) are labeled but the schematic is missing:
- USB-C connector (docs specify 16-pin mid-mount)
- USBLC6-2SC6 ESD protection (exists in Driver sheet but disconnected)
- 22 ohm series resistors on D+/D-
- 1.5k pull-up on D+ for device enumeration

### 8. Missing Flyback Diodes on Inductive Loads
The Driver sheet analysis shows no explicit SS14 flyback Schottky diodes on the 6x solenoid valve MOSFET outputs (Q_SW1-Q_SW6). The docs specify SS14 on every IRLML6344 drain. Without these, inductive kickback will destroy the MOSFETs.

### 9. HSE Crystal Load Caps Potentially Wrong
C4 and C5 are 18pF each. For most 8MHz crystals with ~20pF load capacitance:
- Effective load = (C4 x C5)/(C4 + C5) + C_stray = 9pF + 5pF = 14pF (may be low)
- Or if formula is (C_L1 + C_L2)/2 + stray, then 18pF + 5pF = 23pF (slightly high)
- **Must verify against the specific crystal datasheet**

### 10. Only One Load Cell Interface Instead of Two
The schematic has `PC0_LOADCELL_SCLK` and `PC1_LOADCELL_DOUT` for a single HX711. The docs specify **two separate HX711s** -- one for oil reservoir (PC11/PC12) and one for water reservoir (PC9/PC10). The second load cell is completely missing.

---

## MEDIUM Severity Issues

### 11. Missing PCF8574 I2C GPIO Expanders
The docs specify **two PCF8574 expanders** (0x20 for P-ASD solenoids + CID-1 stepper ENA, 0x21 for SLD solenoids + LED control). The schematic routes solenoid control directly from STM32 GPIO pins instead. This is a fundamental architecture mismatch -- either the docs or schematic needs updating.

### 12. No CAN Bus Termination Resistor Visible
Neither the Connector sheet nor Driver sheet shows a 120 ohm termination resistor between CAN_H and CAN_L. The docs specify one on J_CAN.

### 13. Missing TVS/ESD Protection on GPIO Lines
No TVS diode arrays on SPI signals to CM5, I2C lines, or safety I/O pins. The docs specify PRTR5V0U2X on SPI and TVS on safety I/O.

### 14. Missing BOOT0 Pin Circuit
The docs specify a tactile switch to 3.3V with 10k pull-down on BOOT0. Not present in the schematic.

### 15. No Battery Backup Circuit
The docs specify a complete Li-Ion battery backup system (TP4056 charger, DW01A/FS8205A protection, MT3608 boost converter, SS14 Schottky-OR). While some of these ICs appear in the Driver sheet, the Driver sheet is disconnected, and J_BAT connector is missing from the Connector sheet.

### 16. Missing B0505S-1WR3 Isolated DC-DC Converter
The docs specify this for powering the isolated side (VCC2) of the ISO1050 CAN transceiver. Not clearly present in the schematic despite the recent commit message suggesting it was added.

### 17. VDDA Decoupling Unclear
The docs specify a ferrite bead + 1uF MLCC for VDDA isolation from the main 3.3V rail. The schematic has FB1 (600 ohm ferrite) but its connection to VDDA specifically is not clear.

---

## LOW Severity Issues

### 18. J_SLD Pin Count Mismatch
Connector sheet uses B12B-XH-A (12-pin) but docs specify Hirose DF11-16DP-2DS (16-pin). With 2 pumps (4 wires), 2 solenoids (2 wires), 2 HX711s (4 wires each = 8 wires), plus power/GND -- 12 pins is likely insufficient.

### 19. Missing INA219 Current Monitor
The docs specify U5 (INA219) on I2C1 for power monitoring. It may be in the Driver sheet but is disconnected.

### 20. 7 P-ASD Solenoid Outputs Instead of 6
The Connector sheet has PSOL1_D through PSOL7_D (7 outputs), but the docs specify only 6 solenoid valves for the P-ASD. The 7th may be the pump, but labeling is inconsistent.

---

## Summary

| Severity | Count | Key Theme |
|----------|-------|-----------|
| **CRITICAL** | 5 | Driver sheet disconnected, CAN missing, connectors wrong |
| **HIGH** | 5 | Missing protection, wrong crystal, missing HX711 |
| **MEDIUM** | 7 | Architecture mismatches vs docs, missing protection ICs |
| **LOW** | 3 | Pin counts, labeling inconsistencies |

The **most urgent fix** is reconnecting the Driver sheet to the root schematic with proper hierarchical pins. Without that, most of the power electronics, MOSFET drivers, regulators, and CAN transceiver are electrically orphaned.
