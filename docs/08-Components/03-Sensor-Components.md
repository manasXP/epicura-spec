---
created: 2026-02-15
modified: 2026-11-04
version: 2.3
status: Draft
---

# Sensor Components

## 1. Overview

This document details the sensing subsystem components for the Epicura kitchen robot prototype: the vision camera, pot detection, LED ring and supporting components. There is no thermometer in Epicura: cooking temperature comes from the induction module's own under-glass sensor over CAN (see [[01-Induction-Heating|Induction Heating]]); SLD load cells are costed under [[02-Actuation-Components|Actuation]].

## 2. Sensor Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sensor Subsystem                             │
│                                                                 │
│  ┌──────────────┐ MIPI CSI ┌──────────────┐                   │
│  │  IMX415-98   │─────────►│  RV1106      │                   │
│  │  Camera      │          │  (Luckfox    │                   │
│  └──────────────┘          │  Pico Zero)  │                   │
│                            └──────────────┘                   │
│  ┌──────────────┐                                              │
│  │  WS2812B     │◄── STM32 PB14 (TIM15 PWM+DMA)                │
│  │  LED Ring    │    via 74AHCT1G125 3.3→5 V                   │
│  └──────────────┘                                              │
│                                                                 │
│  ┌──────────────┐  CAN     ┌──────────────┐                   │
│  │  Induction   │─────────►│  STM32G0B1RE │  surface_temp in  │
│  │  module temp │ (isolated│  + RV1106    │  HEAT_STATUS; no  │
│  │  sensor      │   port)  │              │  sensor on Epicura│
│  └──────────────┘          │              │                   │
│  ┌──────────────┐  GPIO    │              │                   │
│  │  Reed Switch │─────────►│              │                   │
│  │  (Pot Detect)│          └──────────────┘                   │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component List

### 3.1 Camera

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Camera Module IMX415-98 | Luckfox IMX415-98 IR-CUT 8 MP (MIPI CSI 4-lane, 22-pin FPC included) | 1 | $54.00 | $54.00 | Luckfox / Waveshare | 8 MP 3840x2160, 98 deg F2.0 lens, IR-CUT; run at 1280x720 @ 30fps into the RV1106 ISP; ISP tuning file shipped with the Pico Zero image |

### 3.2 Thermal Sensors

None. The MLX90614 IR thermometer is removed: the commercial induction surface regulates on its own under-glass sensor and reports `surface_temp` at 10 Hz on the isolated CAN bus. Food-state decisions are made by the camera and CV pipeline.

### 3.3 Detection & Illumination

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Reed Switch | MKA-14103 | 1 | $1.00 | $1.00 | Amazon | Pot detection (magnet in pot base) |
| LED Ring (WS2812B) | 12-LED NeoPixel Ring | 1 | $5.00 | $5.00 | Adafruit / Amazon | Camera illumination, consistent lighting; data driven by STM32 PB14 (TIM15_CH1 PWM + DMA, 800 kHz) via 74AHCT1G125; 5 V power switched by PCF8574 #2 P3; RV1106 requests modes via SET_LED |
| Level Shifter 3.3→5 V | 74AHCT1G125 (SOT-23-5) | 1 | $0.30 | $0.30 | Mouser / LCSC | Buffers the STM32 PB14 WS2812B data line to 5 V logic |

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
| LED Ring (WS2812B) | $5.00 |
| 74AHCT1G125 Level Shifter | $0.30 |
| Passive Components | $0.50 |
| **Category Subtotal** | **$60.80** |

---

## 5. Design Notes

### 5.1 Camera Selection

- **IMX415-98 IR-CUT (8 MP)** is the colour camera Luckfox supports on the Pico Zero; the SDK ships its ISP tuning file. Luckfox's SC3336 module is listed as not compatible with the Pico Zero, and IMX219 and IMX477 are dropped because no RV1106 ISP tuning file exists for them.
- Runs at 1280x720 @ 30 fps (not 1080p). ISP main path 1280x720 NV12 for the on-demand phone stream and LCD preview; ISP self-path 224x224 RGB888 sampled at 2 fps straight into the NPU.
- Dehaze, 2D/3D noise reduction, LSC, sharpening, AWB and AE run in the ISP, so steam over the pot is handled in hardware.
- Fixed focus simplifies mounting. 3 MP is more than sufficient for food stage classification (model input is 224x224 pixels).
- Same module for prototype and production; the FPC plugs directly into the Pico Zero MIPI CSI connector.

### 5.2 Cooking Temperature Without a Thermometer
- The induction module's under-glass sensor (pot-bottom temperature) is reported in HEAT_STATUS (0x180) at 0.1 °C / 10 Hz and used for stage transitions and the STM32 over-temperature cut-off
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
