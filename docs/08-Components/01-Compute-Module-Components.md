---
created: 2026-02-15
modified: 2026-11-04
version: 1.5
status: Draft
---

# Compute Module Components

## 1. Overview

This document details the compute subsystem components for the Epicura kitchen robot prototype, including the Luckfox Pico Zero (RV1106G3; AI/vision processing), STM32G474RE (motor/safety control), display module, and supporting components.

## 2. Compute Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Compute Subsystem                            │
│                                                                 │
│  ┌──────────────┐  CAN (iso)  ┌──────────────┐                 │
│  │  Luckfox     │◄───────────►│  STM32G474RE │                 │
│  │  Pico Zero   │   500 kbps  │  Nucleo      │                 │
│  │  (RV1106G3)  │             │  (FreeRTOS)  │                 │
│  └──────┬───────┘             └──────┬───────┘                 │
│         │                            │                         │
│ MIPI CSI│  SPI0/I2C3             PWM │  ADC  I2C              │
│         │    │                    │  │    │    │               │
│         ▼    ▼                    ▼  ▼    ▼    ▼               │
│      Camera Display           Servos Load MLX                 │
│      IMX415 4" LCD            Arm   Cell  90614               │
│             480x320           Gates       HX711               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component List

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Luckfox Pico Zero (RV1106G3, 256MB DDR3L, 8GB eMMC) | Luckfox Pico Zero | 1 | $47.00 | $47.00 | Waveshare / Luckfox store (₹3,339 Hubtronics India) | Core compute: NPU inference, ISP vision, LVGL UI, recipe engine, cloud sync; on-board Wi-Fi 6 + BT 5.2; no carrier board needed |
| STM32G474RE Nucleo | NUCLEO-G474RE | 1 | $18.00 | $18.00 | STMicroelectronics / Mouser | Motor controller dev board; CAN-FD + advanced timers |
| 4" IPS Display (480x320) with capacitive touch | 4.0" ST7796S + FT6336U SPI module (108 x 60.88 mm incl. header) | 1 | $15.00 | $15.00 | Waveshare / AliExpress | SPI0 display (50 MHz, fbtft) + I2C3 touch (evdev); prototype and production display |
| IMX415-98 IR-CUT Camera Module (8 MP, MIPI CSI) | IMX415-98 | 1 | - | - | See [[03-Sensor-Components\|Sensor Components]] | Costed under Sensors ($54.00, FPC included); plugs into the Pico Zero MIPI CSI FPC connector |
| (Storage on eMMC) | - | - | - | - | Included | 8GB eMMC on Pico Zero for A/B OS slots, models and data; microSD slot for expansion only |
| MCP2518FD CAN Controller (RV1106 node) | MCP2518FD-E/SL + 40 MHz crystal | 1 | $3.00 | $3.00 | Microchip / Mouser | On the Unified PCB, SPI0 CS1 of the Pico Zero header (≤ 20 MHz); kernel `mcp251xfd`, SocketCAN `can0` |
| ISO1050DUB Isolated CAN Transceiver #2 (RV1106 node) | ISO1050DUBR | 1 | $3.50 | $3.50 | TI / Mouser | Shares the isolated 5 V_ISO domain (B0505S-1WR3) and J_CAN with the STM32's ISO1050DUB #1 (costed under Actuation) |
| USB-C Cable (debug/power) | - | 1 | $5.00 | $5.00 | Generic | Pico Zero power, eMMC flashing and USB debug |

---

## 4. Cost Summary

| Item | Cost |
|------|------|
| Luckfox Pico Zero (RV1106G3) | $47.00 |
| STM32G474RE Nucleo | $18.00 |
| 4" SPI Display with touch | $15.00 |
| MCP2518FD CAN controller + crystal (RV1106 node) | $3.00 |
| ISO1050DUB #2 isolated transceiver (RV1106 node) | $3.50 |
| Cables | $5.00 |
| **Category Subtotal** | **$91.50** |

---

## 5. Design Notes

### 5.1 RV1106 (Luckfox Pico Zero) Selection Rationale

Why the RV1106G3:
- **1 TOPS INT8 NPU** runs MobileNetV2 INT8 in 5-10 ms via `rknn_api` (target < 20 ms), against 100+ ms for CPU inference; the CPU never touches pixels
- **5 MP hardware ISP** (3A, 2D/3D noise reduction, dehaze, LSC, sharpening) handles steam and haze over the pot in hardware; no OpenCV on the CPU
- **~1 W class**, no heatsink or fan, -20 to +85°C ambient; suited to an enclosure next to an induction surface
- **$47 complete board** with 256MB DDR3L in-package, 8GB eMMC, Wi-Fi 6 + BT 5.2 and antenna; replaces $85 of CM5 + CM5IO with no carrier board
- **H.264/H.265 hardware encoder** gives the on-demand phone live view (RTSP, 720p @ 15 fps) for free
- 40-pin RPi-style header (28 GPIO, 3.3 V): SPI0 CS0 for the display and CS1 for the MCP2518FD CAN controller, I2C3 for touch, UART2 as the STM32 service link (flashing/debug), GPIO 32/38 for STM32 BOOT0/NRST

What it cannot do, and how the stack adapts:
- **256MB RAM, one Cortex-A7 @ 1.2 GHz:** no Docker, PostgreSQL, Node.js or Python on the device. One native C11 application (`epicurad`) with SQLite, libmosquitto and libcurl; steady state ~80MB, peak ~95MB
- **No 3D GPU:** no Kivy. LVGL 9, software rendered at 20 Hz on a 480x320 framebuffer
- **No DSI/HDMI output, and the Pico Zero does not break out the RGB LCD pins:** the 10.1" 1280x800 panel is dropped for a 4" 480x320 SPI LCD
- **No CAN peripheral and one SPI controller:** the display takes SPI0 CS0; an MCP2518FD on SPI0 CS1 (+ ISO1050DUB #2) puts the RV1106 on the isolated CAN bus it shares with the STM32 and the induction surface, where it also runs the heater PID; UART2 is kept only to flash the STM32
- **Narrow camera driver list:** the IMX415-98 IR-CUT is the only colour camera Luckfox supports on the Pico Zero (the SC3336 module is marked incompatible with the Zero); IMX219/IMX477 are dropped
- **2.4 GHz Wi-Fi only, no Ethernet on the board:** cloud sync and SSH go over Wi-Fi; UART0 is the debug console
- **8GB eMMC:** A/B boot + rootfs slots (2x32MB + 2x256MB), 64MB `oem` (models, ISP tuning, LVGL assets), ~6GB `data`

See [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]] for datasheet facts and the CM5 comparison, and [[02-Controller-Software-Architecture|Controller & Software Architecture]] for the resulting stack.

### 5.2 STM32G474RE Selection Rationale
- **Cortex-M4F @ 170 MHz** with FPU for motor control and filtering (the temperature PID runs on the RV1106)
- **FDCAN1** on the shared isolated CAN bus (host commands from the RV1106, telemetry, heater off-switch)
- **Advanced timers** (TIM1, TIM8) with complementary PWM for servo control
- **12-bit ADC** (5 Msps) for analog sensor reading
- **USART2 (PA2/PA3)** as the service link to the RV1106: ST system-bootloader port for firmware updates and debug; no runtime traffic
- Nucleo board provides ST-Link debugger and Arduino-compatible headers. Caveat: on the NUCLEO-G474RE (MB1367) PA2/PA3 are tied to the ST-LINK VCP through SB17 and SB23 (ON by default, UM2505 rev 4); remove SB17/SB23 and fit SB18/SB22 to route them to Arduino D1/D0 on CN9, or take them from morpho CN10 pins 35 (PA2) and 37 (PA3), or use the custom controller PCB

### 5.3 Display Choice
- 4" 480x320 IPS LCD with ST7796S controller on SPI0 (fbtft, 50 MHz with DMA); the RV1106 has no DSI or HDMI output
- Full-frame refresh is ~50 ms; LVGL partial redraws keep the UI responsive at a 20 Hz tick
- FT6336 capacitive touch on I2C3 (evdev), read directly by the RV1106
- The display stays SPI in production (same panel/controller, bezel-mounted)

### 5.4 Production Upgrade Path

| Item | Prototype | Production |
|------|-----------|------------|
| Application processor | Luckfox Pico Zero (complete board) | Bare RV1106G3 (QFN128, 12.3 mm, 0.35 mm pitch) on the custom PCB, or Luckfox Core1106 SoM on the PCB |
| STM32 | Nucleo dev board | Bare STM32G474RE on controller PCB |
| Display | 4" ST7796S SPI LCD module + FT6336 touch | Same 4" SPI panel, bezel-mounted; stays SPI |
| Storage | 8GB eMMC on Pico Zero | 8GB eMMC on SoM or on PCB |
| Software | Buildroot image, `epicurad`, swupdate A/B | Same image; no orchestration layer |

---

## 6. Related Documentation

- [[02-Actuation-Components|Actuation Components]]
- [[03-Sensor-Components|Sensor Components]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]

---

#epicura #components #compute #bom

---

## 7. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-02-20 | Manas Pradhan | Added ISO1050DUB isolated CAN transceiver to component list and cost summary |
| 1.2 | 2026-02-20 | Manas Pradhan | Moved ISO1050DUB ($3.50) to Actuation Components (now on Driver PCB); subtotal $199.50 → $196.00 |
| 1.3 | 2026-11-04 | Manas Pradhan | Replaced Raspberry Pi CM5 + CM5IO + 10.1" HDMI display with Luckfox Pico Zero (RV1106G3) + 4" ST7796S SPI LCD; CSI/HDMI cables removed; subtotal $196.00 → $85.00 |
| 1.4 | 2026-11-04 | Manas Pradhan | Camera IMX415-98 IR-CUT (SC3336 incompatible with the Pico Zero); 4" display module part named; Nucleo SB numbers; CAN alternative removed |
| 1.5 | 2026-11-04 | Manas Pradhan | RV1106 CAN node added (MCP2518FD $3.00 + ISO1050DUB #2 $3.50 on the Unified PCB, SPI0 CS1); UART2 demoted to STM32 flashing/debug; STM32 notes updated (PID on the RV1106); subtotal $85.00 → $91.50 |
