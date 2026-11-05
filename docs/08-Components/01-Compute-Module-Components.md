---
created: 2026-02-15
modified: 2026-11-05
version: 1.12
status: Draft
---

# Compute Module Components

## 1. Overview

This document details the compute subsystem components for the Epicura kitchen robot prototype, including the Luckfox Pico Zero (RV1106G3; AI/vision processing), two STM32G0B1RE (the DU STM32 for dispensing, battery/dock monitoring and the DU's CAN node; the CSC STM32 for stir, heater off-switch and safety), display module, and supporting components. Three controllers in two units: the Pico Zero and the DU STM32 sit on the Unified PCB v5.0 inside the battery-powered Dispensing Unit (DU), linked by a UART host link (UART2 ↔ USART1, 921,600 baud); the CSC STM32G0B1RE is on the Cooking Surface Controller (CSC) PCB in the mains-powered Cooking Surface (CS). The units meet only on the isolated CAN bus, which crosses the 8-pin magnetic pogo dock (J_DOCK) together with the DU's 24 V charge feed.

## 2. Compute Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Compute Subsystem                            │
│                                                                 │
│  DISPENSING UNIT (DU) — Unified PCB v5.0, battery-powered       │
│  ┌──────────────┐ UART2↔USART1 ┌──────────────┐ FDCAN1 ┌───────┐│
│  │  Luckfox     │─────────────►│  DU STM32    │───────►│HVD230 ││
│  │  Pico Zero   │ 921,600 baud │  G0B1RE      │        │  #2   ││
│  │  (RV1106G3)  │ BOOT0/NRST   │  (FreeRTOS)  │        └───┬───┘│
│  └──┬───┬───────┘              └──┬───────────┘  CAN (iso) │    │
│ CSI │   │ SPI0 + I2C3 (touch)     │ I2C1 / TIM PWM / GPIO  │    │
│     ▼   ▼                         ▼                        │    │
│  Camera LCD         PCA9685 · PCF8574 #2 · Hall ×6         │    │
│  IMX415 4"          INA219 ×2 · LED ring · buzzer          │    │
│                     DOCK_SENSE_A · DOCK_PWR_OK             │    │
│ ═════════ J_DOCK (8-pin pogo: DOCK_24V + CAN) ═╪═════════════   │
│  COOKING SURFACE (CS) — CSC PCB, mains         │                │
│  ┌──────────────┐  FDCAN1    ┌──────────────┐  │  ┌──────────┐  │
│  │  STM32G0B1RE │◄──────────►│  ISO1050 #1  │◄─┴─►│ Heating  │  │
│  │  (CSC,       │            │  + B0505S    │     │ unit     │  │
│  │   FreeRTOS)  │            └──────────────┘     └──────────┘  │
│  └──────┬───────┘                                               │
│  FDCAN2 │ ISO1050 #3 + 24V_SU (K_SU) ─► J_SU ──► Stir servo (SU)│
│  GPIO   │ Q_RLY relay · E-stop · pot reed · fans ×2 · Q_DOCK    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component List

| Component | Part Number | Qty | Unit Price | Subtotal | Supplier | Notes |
|-----------|-------------|-----|------------|----------|----------|-------|
| Luckfox Pico Zero (RV1106G3, 256MB DDR3L, 8GB eMMC) | Luckfox Pico Zero | 1 | $47.00 | $47.00 | Waveshare / Luckfox store (₹3,339 Hubtronics India) | Core compute: NPU inference, ISP vision, LVGL UI, recipe engine, cloud sync; on-board Wi-Fi 6 + BT 5.2; no carrier board needed |
| STM32G0B1RE Nucleo | NUCLEO-G0B1RE | 1 | $11.00 | $11.00 | STMicroelectronics / Mouser | Controller dev board (MB1360); 2x FDCAN, ST-LINK; stands in for the Cooking Surface Controller (CSC) in the CS base; production part STM32G0B1RET6 ~$3.50 on the CSC PCB (costed under [[04-Total-Component-Cost\|Additional Costs]]) |
| 4" IPS Display (480x320) with capacitive touch | 4.0" ST7796S + FT6336U SPI module (108 x 60.88 mm incl. header) | 1 | $15.00 | $15.00 | Waveshare / AliExpress | SPI0 display (50 MHz, fbtft) + I2C3 touch (evdev); prototype and production display |
| IMX415-98 IR-CUT Camera Module (8 MP, MIPI CSI) | IMX415-98 | 1 | - | - | See [[03-Sensor-Components\|Sensor Components]] | Costed under Sensors ($54.00, FPC included); plugs into the Pico Zero MIPI CSI FPC connector |
| (Storage on eMMC) | - | - | - | - | Included | 8GB eMMC on Pico Zero for A/B OS slots, models and data; microSD slot for expansion only |
| STM32G0B1RET6 (DU STM32) + 8 MHz crystal + J_SWD | STM32G0B1RET6 (LQFP-64) | 1 | $4.00 | $4.00 | STMicroelectronics / Mouser | On the Unified PCB v5.0 (DU): dispensers (I2C1, TIM3 pumps), LED ring, buzzer, battery/dock monitor and the DU's CAN node (FDCAN1), transparent gateway for the RV1106 over the UART host link (UART2 ↔ USART1, 921,600 baud; BOOT0/NRST from GPIO 32/38 for flashing). Replaces the MCP2518FD + 40 MHz crystal ($3.00) |
| SN65HVD230 CAN Transceiver (DU STM32 node, non-isolated) | SN65HVD230DR | 1 | $0.80 | $0.80 | TI / Mouser | On the Unified PCB v5.0 behind the J_DOCK pads, driven by the DU STM32 FDCAN1, 3.3 V, referenced to the DU logic ground (dock pad 5 GND_ISO is tied to it); the only barrier on this bus is the CSC's ISO1050DUB #1 (costed under Actuation). Replaces ISO1050DUB #2 (2026-11-04) |
| Dock Connector (J_DOCK) | 8-pin magnetic pogo pair, 2.54 mm pitch, spring pins 2 A each + flat gold pad plate | 1 pair | $6.00 | $6.00 | AliExpress / Mouser | Keyed recess on the CS left pillar (pins) and the DU underside (pads): DOCK_24V charge, GND, CAN_H/CAN_L, GND_ISO (→ DU GND), 5V_ISO (reserved), DOCK_SENSE_A/B; pads de-energised by Q_DOCK on the CSC when the DU is lifted |
| INA219 #2 Battery Monitor | INA219AIDCNR + 10 mΩ shunt | 1 | $1.00 | $1.00 | TI / LCSC | On the Unified PCB v5.0 in the BAT+ path (DU STM32 I2C1, addr 0x44): pack voltage + current → state of charge, reported to the RV1106 in DU_STATUS (warning 6.4 V, checkpoint + halt 6.2 V) |
| USB-C Cable (debug/power) | - | 1 | $5.00 | $5.00 | Generic | Pico Zero power, eMMC flashing and USB debug; also the CSC's bench USB-C DFU port |

---

## 4. Cost Summary

| Item | Cost |
|------|------|
| Luckfox Pico Zero (RV1106G3) | $47.00 |
| STM32G0B1RE Nucleo | $11.00 |
| 4" SPI Display with touch | $15.00 |
| STM32G0B1RET6 (DU STM32) + crystal + J_SWD | $4.00 |
| SN65HVD230 transceiver (DU STM32 node, non-isolated) | $0.80 |
| Dock connector J_DOCK (8-pin magnetic pogo pair) | $6.00 |
| INA219 #2 battery monitor + shunt | $1.00 |
| Cables | $5.00 |
| **Category Subtotal** | **$89.80** |

---

## 5. Design Notes

### 5.1 RV1106 (Luckfox Pico Zero) Selection Rationale

Why the RV1106G3:
- **1 TOPS INT8 NPU** runs MobileNetV2 INT8 in 5-10 ms via `rknn_api` (target < 20 ms), against 100+ ms for CPU inference; the CPU never touches pixels
- **5 MP hardware ISP** (3A, 2D/3D noise reduction, dehaze, LSC, sharpening) handles steam and haze over the pot in hardware; no OpenCV on the CPU
- **~1 W class**, no heatsink or fan, -20 to +85°C ambient; suited to an enclosure next to an electric heating unit
- **$47 complete board** with 256MB DDR3L in-package, 8GB eMMC, Wi-Fi 6 + BT 5.2 and antenna; replaces $85 of CM5 + CM5IO with no carrier board
- **H.264/H.265 hardware encoder** gives the on-demand phone live view (RTSP, 720p @ 15 fps) for free
- 40-pin RPi-style header (28 GPIO, 3.3 V): SPI0 CS0 for the display (the only SPI0 device); I2C3 for the FT6336 touch only; PWM10 for the backlight; UART2 (pins 8/10) as the host link to the DU STM32 USART1 and GPIO 32/38 as its BOOT0/NRST. Every dispenser, load cell, power monitor, the LED ring, buzzer and the dock sense lines hang off the DU STM32, which is why the header budget now fits the camera, LCD and link comfortably

What it cannot do, and how the stack adapts:
- **256MB RAM, one Cortex-A7 @ 1.2 GHz:** no Docker, PostgreSQL, Node.js or Python on the device. One native C11 application (`epicurad`) with SQLite, libmosquitto and libcurl; steady state ~80MB, peak ~95MB
- **No 3D GPU:** no Kivy. LVGL 9, software rendered at 20 Hz on a 480x320 framebuffer
- **No DSI/HDMI output, and the Pico Zero does not break out the RGB LCD pins:** the 10.1" 1280x800 panel is dropped for a 4" 480x320 SPI LCD
- **No CAN peripheral, one SPI controller and few free GPIO:** the display takes SPI0 CS0; the DU STM32 (FDCAN1 + SN65HVD230, non-isolated) is the DU's node on the CSC's isolated CAN port #1 shared with the CSC STM32 and the electric heating unit (which runs its own PID), and acts as a transparent gateway for the RV1106 over the UART2 host link; the bus reaches the DU over dock pins 3–5 (pin 5 GND_ISO tied to the DU ground). The CSC image is streamed over CAN (0x7E0/0x7E8) through the gateway; the DU STM32 is flashed by the RV1106 through the ST system bootloader on USART1 (BOOT0/NRST on GPIO 32/38)
- **Narrow camera driver list:** the IMX415-98 IR-CUT is the only colour camera Luckfox supports on the Pico Zero (the SC3336 module is marked incompatible with the Zero); IMX219/IMX477 are dropped
- **2.4 GHz Wi-Fi only, no Ethernet on the board:** cloud sync and SSH go over Wi-Fi; UART0 is the debug console
- **8GB eMMC:** A/B boot + rootfs slots (2x32MB + 2x256MB), 64MB `oem` (models, ISP tuning, LVGL assets), ~6GB `data`

See [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]] for datasheet facts and the CM5 comparison, and [[02-Controller-Software-Architecture|Controller & Software Architecture]] for the resulting stack.

### 5.2 STM32G0B1RE Selection Rationale
- **No control loop on the MCU**: the heating unit regulates its own temperature and the stirring motor is a CAN servo with its own controller, so the MCU is an IO, CAN and safety node. Its fastest task runs at 50 Hz; a Cortex-M0+ @ 64 MHz without FPU is ample. The STM32G474RE (Cortex-M4F @ 170 MHz, ~$8) it replaces was sized for a PID loop and a PWM motor that no longer exist
- **Two FDCAN controllers**: FDCAN1 on the isolated host/heater bus (ISO1050DUB #1 + B0505S on the CSC, extended to the DU over the dock), FDCAN2 on the isolated stir-motor bus (ISO1050DUB #3 + B0505S #2 → J_CAN_STIR → J_SU in the right pillar; floating Stirring Unit domain, GND_SU). The G0B1 is the cheapest ST part with two; the G431/G441 have one
- **Same toolchain and safety story as the G474**: STM32 HAL + CubeMX, FreeRTOS, an in-application CAN bootloader (the RV1106 streams the image over the isolated bus, IDs 0x7E0/0x7E8; USB-C DFU on the CSC is the bench fallback, SWD for factory), IWDG on its own LSI clock, SRAM parity, flash ECC, and the VDE-certified X-CUBE-CLASSB library for IEC 60730-1 / IEC 60335-1 Annex R Class B software
- **Why not an RP2040** (~$1): no CAN peripheral (two external controllers at $2–3 each, or a PIO soft-CAN on the heater kill path), no internal flash, no ROM DFU bootloader (bench recovery path would need a redesign), no MISRA/Class B ecosystem. Once the missing parts are added it costs about the same as the G0B1 and carries more certification risk
- **Pin budget**: LQFP-64 (STM32G0B1RET6) on the CSC. With dispensing, SLD sensing, LED ring and buzzer on the DU STM32, the CSC uses only PA0 (VBUS), PA2/PA3 (debug console), PA6 (fan PWM), PB0–PB5 (K_SAFE relay, pot reed, E-stop, DOCK_SENSE_B, K_SU relay, Q_DOCK), PB8/PB9 (FDCAN1), PB10 (fan 2), PB12/PB13 (FDCAN2) and PC7 (status LED); PA1, PA4, PA5, PA7–PA10, PA15, PB6/PB7, PB11, PB14, PB15, PC0–PC6, PC8–PC12 and PD2 are free (see the [[../03-Software/05-MCU-Functional-Specification|MCU Functional Specification]] pin table)
- **USART2 (PA2/PA3)** goes only to J_DBG, a 3-pin debug console header on the CSC; there is no host link to the RV1106 (different unit, no cable). On the G0 BOOT0 is PA14-BOOT0 and needs option bit nBOOT_SEL = 0 programmed once at factory for SW_BOOT DFU entry
- Nucleo board NUCLEO-G0B1RE (MB1360, ~$11) provides ST-LINK and Arduino headers. PA2/PA3 go to the ST-LINK VCP by default; re-route via the solder bridges in UM2324 or use the CSC PCB

### 5.3 Display Choice
- 4" 480x320 IPS LCD with ST7796S controller on SPI0 (fbtft, 50 MHz with DMA); the RV1106 has no DSI or HDMI output
- Full-frame refresh is ~50 ms; LVGL partial redraws keep the UI responsive at a 20 Hz tick
- FT6336 capacitive touch on I2C3 (evdev), read directly by the RV1106
- The display stays SPI in production (same panel/controller, bezel-mounted)

### 5.4 Production Upgrade Path

| Item | Prototype | Production |
|------|-----------|------------|
| Application processor | Luckfox Pico Zero (complete board) | Bare RV1106G3 (QFN128, 12.3 mm, 0.35 mm pitch) on the custom PCB, or Luckfox Core1106 SoM on the PCB |
| STM32 | NUCLEO-G0B1RE dev board | Bare STM32G0B1RET6 on the Cooking Surface Controller (CSC) PCB in the CS |
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
| 1.6 | 2026-11-04 | Manas Pradhan | STM32G474RE → STM32G0B1RE (NUCLEO-G0B1RE $11, production STM32G0B1RET6 ~$3.50); §5.2 rewritten with the RP2040 comparison; subtotal $91.50 → $84.50 |
| 1.7 | 2026-11-04 | Manas Pradhan | Three-unit split: STM32G0B1RE moves to the Cooking Surface Controller (CSC) in the CS; the Unified PCB v4.0 is the Dispensing Unit board (Pico Zero, battery, dispenser drivers, RV1106 CAN node); J_DOCK 8-pin magnetic pogo pair (+$6.00) and INA219 #2 battery monitor (+$1.00) added; UART2/BOOT0/NRST service link replaced by the CAN bootloader; diagram redrawn; subtotal $84.50 → $91.50 |
| 1.8 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, same CAN contract): diagram and notes reworded; subtotal unchanged ($91.50) |
| 1.9 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: STM32G0B1RET6 (DU STM32, +$4.00 incl. crystal and J_SWD) on the Unified PCB v5.0 takes dispensing, LED/buzzer, battery/dock monitoring and the DU CAN node (FDCAN1 + ISO1050 #2) as a gateway for the RV1106 over the UART2 ↔ USART1 host link; MCP2518FD + crystal (−$3.00) removed; diagram redrawn; subtotal $91.50 → $92.50 |
| 1.11 | 2026-11-04 | Manas Pradhan | DU CAN node non-isolated: SN65HVD230 ($0.80) replaces ISO1050DUB #2 ($3.50) on the Unified PCB v5.1; subtotal $92.50 → $89.80; dock pin notes updated |
| 1.12 | 2026-11-05 | Manas Pradhan | Robot-mop SLD: DU STM32 diagram line (six Hall inputs instead of NAU7802 ×2) and pin-budget wording; no price change |
| 1.10 | 2026-11-04 | Manas Pradhan | Aligned to CSC v1.3: the CSC's FDCAN2 stir-motor bus is isolated (ISO1050DUB #3 + B0505S #2, floating SU domain) and the motor runs from the SU's own LRS-75-24 #2 cut by the relay K_SU on PB4 (was SN65HVD230 + Q_STIR); diagram line, FDCAN note and pin-budget list updated; no price change here (CSC parts costed under Actuation), subtotal $92.50 |
