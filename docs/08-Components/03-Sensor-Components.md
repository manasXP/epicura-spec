---
created: 2026-02-15
modified: 2026-11-04
version: 2.5
status: Draft
---

# Sensor Components

## 1. Overview

This document details the sensing subsystem components for the Epicura kitchen robot prototype: the vision camera, pot detection, LED ring and supporting components. The camera and the white LED ring sit on the underside of the Dispensing Unit (DU), centred over the pot and looking straight down through a sealed borosilicate window, and connect to the RV1106 on the Unified PCB v4.0; the pot reed switch is wired to the Cooking Surface Controller (CSC) in the Cooking Surface (CS). There is no thermometer in Epicura: cooking temperature comes from the electric heating unit's own centre (pot-bottom) sensor over CAN (see [[01-Electric-Heating|Electric Heating]]); SLD load cells and their NAU7802 ADCs are costed under [[02-Actuation-Components|Actuation]].

## 2. Sensor Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sensor Subsystem                             │
│                                                                 │
│  DISPENSING UNIT (DU) — Unified PCB v4.0                        │
│  ┌──────────────┐ MIPI CSI ┌──────────────┐                     │
│  │  IMX415-98   │─────────►│  RV1106      │                     │
│  │  Camera      │          │  (Luckfox    │                     │
│  │  (underside) │          │  Pico Zero)  │                     │
│  └──────────────┘          └──────┬───────┘                     │
│  ┌──────────────┐                 │ PWM (Q_LED, 1 kHz)          │
│  │  White LED   │◄────────────────┘                             │
│  │  Ring 5000 K │  5V_MAIN, ≤ 1 A                               │
│  └──────────────┘                                               │
│ ═════════ J_DOCK (isolated CAN 500 kbps, CS ◄──► DU) ═════════  │
│  COOKING SURFACE (CS) — CSC                                     │
│  ┌──────────────┐  CAN     ┌──────────────┐                     │
│  │  Heating unit│─────────►│  STM32G0B1RE │  surface_temp in    │
│  │  centre temp │ (isolated│  (CSC) +     │  HEAT_STATUS; no    │
│  │  sensor      │   port)  │  RV1106 (DU) │  sensor on Epicura  │
│  └──────────────┘          │              │                     │
│  ┌──────────────┐  GPIO    │              │                     │
│  │  Reed Switch │─────────►│  PB1 (J_SAFE)│                     │
│  │  (Pot Detect)│          └──────────────┘                     │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component List

### 3.1 Camera

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Camera Module IMX415-98 | Luckfox IMX415-98 IR-CUT 8 MP (MIPI CSI 4-lane, 22-pin FPC included) | 1 | $54.00 | $54.00 | Luckfox / Waveshare | 8 MP 3840x2160, 98 deg F2.0 lens, IR-CUT; run at 1280x720 @ 30fps into the RV1106 ISP; ISP tuning file shipped with the Pico Zero image |

### 3.2 Thermal Sensors

None. The MLX90614 IR thermometer is removed: the commercial electric heating unit regulates on its own centre sensor and reports `surface_temp` at 10 Hz on the isolated CAN bus. Food-state decisions are made by the camera and CV pipeline.

### 3.3 Detection & Illumination

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Reed Switch | MKA-14103 | 1 | $1.00 | $1.00 | Amazon | Pot detection (magnet in pot base); in the CS, read by the CSC on STM32 PB1 via J_SAFE as an optional backup to the module's own pot detection |
| White LED Ring | 12–16 LED ring, 5000 K, CRI ≥ 90, 5 V | 1 | $4.00 | $4.00 | AliExpress / Adafruit | Camera illumination, consistent lighting; on the DU underside around the camera window; 5V_MAIN ≤ 1 A, switched/dimmed by Q_LED (IRLML6344 low-side) from an RV1106 PWM at 1 kHz (OFF 0 %, CAPTURE 100 %, NIGHT 30 %) via J_LED 2-pin; no colour control, no CAN SET_LED |

### 3.4 Passive Components

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Decoupling Caps (100nF) | 0603, X7R | 5 | $0.10 | $0.50 | Any | I2C/SPI line filtering and bypass |

---

## 4. Cost Summary

| Item | Cost |
|------|------|
| IMX415-98 Camera | $54.00 |
| Reed Switch | $1.00 |
| White LED Ring (5000 K, RV1106 PWM) | $4.00 |
| Passive Components | $0.50 |
| **Category Subtotal** | **$59.50** |

---

## 5. Design Notes

### 5.1 Camera Selection

- **IMX415-98 IR-CUT (8 MP)** is the colour camera Luckfox supports on the Pico Zero; the SDK ships its ISP tuning file. Luckfox's SC3336 module is listed as not compatible with the Pico Zero, and IMX219 and IMX477 are dropped because no RV1106 ISP tuning file exists for them.
- Runs at 1280x720 @ 30 fps (not 1080p). ISP main path 1280x720 NV12 for the on-demand phone stream and LCD preview; ISP self-path 224x224 RGB888 sampled at 2 fps straight into the NPU.
- Dehaze, 2D/3D noise reduction, LSC, sharpening, AWB and AE run in the ISP, so steam over the pot is handled in hardware.
- Fixed focus simplifies mounting. 3 MP is more than sufficient for food stage classification (model input is 224x224 pixels).
- Same module for prototype and production; the FPC plugs directly into the Pico Zero MIPI CSI connector on the Unified PCB v4.0.
- Mounted on the DU underside, centred over the pot and looking straight down behind a sealed borosilicate window, 20–30 cm above the pot rim; the white LED ring surrounds the window. The whole assembly lifts off with the DU, so there is no camera cable between units.

### 5.2 Cooking Temperature Without a Thermometer
- The heating unit's spring-loaded centre sensor (pot-bottom temperature) is reported in HEAT_STATUS (0x180) at 0.1 °C / 10 Hz and used for stage transitions and the STM32 over-temperature cut-off
- Removes the IR sensor, its emissivity calibration, the steam shroud and one I2C device from the Unified PCB (−$12.20)
- Recipe `temp_target` values are pot-bottom targets; browning/boiling detection is the camera's job

---

## 6. Related Documentation

- [[01-Compute-Module-Components|Compute Module Components]]
- [[02-Actuation-Components|Actuation Components]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]

---

#epicura #components #sensors #bom

---

## 7. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-20 | Manas Pradhan | Removed NTC thermistors (coil temp via CAN, ambient not needed); subtotal $64.90 → $62.70 |
| 2.1 | 2026-11-04 | Manas Pradhan | Camera changed to SC3336 for the RV1106 ISP (IMX219/IMX477 dropped); LED ring now driven by STM32 PB14 via 74AHCT1G125 (+$0.30); subtotal $43.70 → $31.00 |
| 2.2 | 2026-11-04 | Manas Pradhan | Camera changed to IMX415-98 IR-CUT ($54): SC3336 not compatible with the Pico Zero; subtotal $31.00 → $73.00 |
| 2.3 | 2026-11-04 | Manas Pradhan | MLX90614 IR thermometer and its pull-ups removed (cooking temperature from the induction module over CAN); subtotal $73.00 → $60.80 |
| 2.4 | 2026-11-04 | Manas Pradhan | Three-unit split: WS2812B ring (−$5.00) + 74AHCT1G125 (−$0.30) replaced by a white 5000 K LED ring (+$4.00) on an RV1106 PWM (Q_LED); camera + ring on the DU underside; reed switch wired to the CSC; diagram redrawn; subtotal $60.80 → $59.50 |
| 2.5 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, same CAN contract): temperature source is the unit's centre (pot-bottom) sensor; diagram and notes reworded; subtotal unchanged ($59.50) |
