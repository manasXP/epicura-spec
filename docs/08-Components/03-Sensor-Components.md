---
created: 2026-02-15
modified: 2026-11-04
version: 2.1
status: Draft
---

# Sensor Components

## 1. Overview

This document details the sensing subsystem components for the Epicura kitchen robot prototype, including the vision camera, infrared thermometer, load cells, temperature sensors, and supporting components.

## 2. Sensor Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sensor Subsystem                             │
│                                                                 │
│  ┌──────────────┐ MIPI CSI ┌──────────────┐                   │
│  │  SC3336      │─────────►│  RV1106      │                   │
│  │  Camera      │          │  (Luckfox    │                   │
│  └──────────────┘          │  Pico Zero)  │                   │
│                            └──────────────┘                   │
│  ┌──────────────┐                                              │
│  │  WS2812B     │◄── STM32 PB14 (TIM15 PWM+DMA)                │
│  │  LED Ring    │    via 74AHCT1G125 3.3→5 V                   │
│  └──────────────┘                                              │
│                                                                 │
│  ┌──────────────┐  I2C     ┌──────────────┐                   │
│  │  MLX90614    │─────────►│  STM32G474RE │                   │
│  │  IR Thermo   │          │  (Controller)│                   │
│  └──────────────┘          │              │                   │
│                            │              │                   │
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
| Camera Module SC3336 | Luckfox SC3336 3MP (MIPI CSI, FPC included) | 1 | $12.00 | $12.00 | Luckfox / Waveshare | 3MP, run at 1280x720 @ 30fps into the RV1106 ISP; fixed focus; ISP tuning file shipped in the Luckfox SDK |

### 3.2 Thermal & Weight Sensors

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| IR Thermometer | MLX90614ESF-BAA | 1 | $12.00 | $12.00 | Mouser / DigiKey | Non-contact, I2C, 90° FOV, -70 to +380°C |

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
| Pull-up Resistors (4.7k ohm) | 0603, 1% | 2 | $0.10 | $0.20 | Any | I2C bus pull-ups for MLX90614 |

---

## 4. Cost Summary

| Item | Cost |
|------|------|
| SC3336 Camera | $12.00 |
| MLX90614 IR Thermometer | $12.00 |
| Reed Switch | $1.00 |
| LED Ring (WS2812B) | $5.00 |
| 74AHCT1G125 Level Shifter | $0.30 |
| Passive Components | $0.70 |
| **Category Subtotal** | **$31.00** |

---

## 5. Design Notes

### 5.1 Camera Selection

- **SC3336 (3 MP)** is the Luckfox-supported sensor for the RV1106; the SDK ships its ISP tuning file. IMX219 and IMX477 are dropped because no RV1106 ISP tuning file exists for them.
- Runs at 1280x720 @ 30 fps (not 1080p). ISP main path 1280x720 NV12 for the on-demand phone stream and LCD preview; ISP self-path 224x224 RGB888 sampled at 2 fps straight into the NPU.
- Dehaze, 2D/3D noise reduction, LSC, sharpening, AWB and AE run in the ISP, so steam over the pot is handled in hardware.
- Fixed focus simplifies mounting. 3 MP is more than sufficient for food stage classification (model input is 224x224 pixels).
- Same module for prototype and production; the FPC plugs directly into the Pico Zero MIPI CSI connector.

### 5.2 MLX90614ESF-BAA IR Thermometer
- **90° FOV (BAA variant):** Covers entire pot surface from overhead mounting
- **Temperature range:** -70°C to +380°C (food range: 20°C to 250°C)
- **Accuracy:** ±0.5°C in 0-50°C range, ±2°C at higher temperatures
- **Interface:** I2C (SMBus compatible), default address 0x5A
- **Mounting:** 15-20 cm above pot surface for full pot coverage

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
