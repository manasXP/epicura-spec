---
created: 2026-02-15
modified: 2026-11-04
version: 6.1
status: Draft
---

# Epicura Hardware Architecture & Wiring Diagrams

## 1. Overview

This document provides the comprehensive hardware architecture, wiring diagrams, and interface specifications for the Epicura autonomous kitchen robot. The system uses a dual-processor architecture: a Rockchip RV1106G3 (Luckfox Pico Zero) running Buildroot Linux for AI/vision/UI, and an STM32G4 microcontroller running FreeRTOS for real-time motor control, sensing, and safety.

---

## 2. System Block Diagram

```
                              ┌─────────────────────────────────┐
                              │          AC Mains Input         │
                              │      220-240V 50Hz <2kW         │
                              └────────────────┬────────────────┘
                                               │
                                        ┌──────▼──────┐
                                        │  EMI Filter  │
                                        │  + IEC C14   │
                                        └──────┬──────┘
                                               │
                              ┌────────────────▼────────────────┐
                              │       Mean Well LRS-75-24       │
                              │  AC-DC Single Output + PFC      │
                              └────────────────┬────────────────┘
                                               │
                                            24V/3.2A
                                               │
          ┌────────────────────────────────────┼──────────────────────────────┐
          │          Unified PCB               │                              │
          │   24V→12V (MP1584EN), 12V→5V (TPS54531)                           │
          │   USB-C VBUS→5V, Li-Ion→MT3608→5V (3-way OR→AMS1117→3.3V)       │
          │                                    │                              │
          │        5V (via 40-pin header)       │    3.3V                      │
          │              │                      │      │                       │
          │              ▼                      ▼      ▼                       │
          │  ┌───────────────────────┐      ┌────────────────────────────┐  │
          │  │  Luckfox Pico Zero    │      │  STM32G474RE               │  │
          │  │  RV1106G3 (Buildroot) │      │  (FreeRTOS)                │  │
          │  │                       │      │                            │  │
          │  │  - Recipe Engine      │      │  - PID Heat Control        │  │
          │  │  - CV Inference (NPU) │      │  - Servo Motor Control     │  │
          │  │  - UI Rendering (LVGL)│      │  - Sensor Acquisition      │  │
          │  │  - Cloud/WiFi/BT      │      │  - Dispensing Logic        │  │
          │  │  - OTA Updates        │      │  - Safety Monitoring       │  │
          │  │                       │      │                            │  │
          │  │  ┌─────┐  ┌────────┐  │      │  ┌──────┐  ┌───────────┐  │  │
          │  │  │CSI-2│  │SPI0/I2C│  │      │  │ PWM  │  │ ADC/GPIO  │  │  │
          │  │  └──┬──┘  └───┬────┘  │      │  └──┬───┘  └─────┬─────┘  │  │
          │  └─────┼─────────┼───────┘      └─────┼─────────────┼───────┘  │
          │        │         │    ▲                │             │          │
          │        │         │    │ UART 1 Mbps    │             │          │
          │        │         │    │ (USART2)       │             │          │
          │        │         │    └───────────────►│             │          │
          │        ▼         ▼                      ▼             ▼            │
          │   ┌────────┐ ┌──────────┐      ┌──────────────┐ ┌──────────────┐   │
          │   │IMX415  │ │4" ST7796S│      │Microwave     │ │  Sensors     │   │
          │   │3 MP    │ │480x320   │      │Induction     │ │  MLX90614    │   │
          │   │Camera  │ │(SPI+I2C) │      │Surface (CAN) │ │  HX711       │   │
          │   └────────┘ └──────────┘      └──────────────┘ │              │   │
          │                                                 └──────────────┘   │
          │   ┌────────┐ ┌──────────┐      ┌──────────────┐ ┌──────────────┐   │
          │   │WiFi 6  │ │eMMC 8 GB │      │24V BLDC      │ │DSB Servos x4 │   │
          │   │2.4 GHz │ │+ microSD │      │Stirring Motor│ │FID 3 + CID 1 │   │
          │   │BLE 5.2 │ │Storage   │      │(integrated)  │ │SLD Pumps x2  │   │
          │   └────────┘ └──────────┘      └──────────────┘ └──────────────┘   │
          │                                                                    │
          │   ┌────────────────────────────────────────────────────────────┐   │
          │   │  LED Ring (WS2812B x 12-16) ── STM32 PB14 (TIM15_CH1 PWM)  │   │
          │   │  via 74AHCT1G125 level shifter; AP sends SET_LED over UART │   │
          │   └────────────────────────────────────────────────────────────┘   │
          └────────────────────────────────────────────────────────────────────┘
```

---

## 3. Main Component List

| Component | Part Number | Interface | Connected To | Purpose |
|-----------|-------------|-----------|--------------|---------|
| Compute Module | Luckfox Pico Zero (RV1106G3) | 40-pin header / CSI / USB-C | Unified PCB (40-pin header) | AI/vision (NPU), recipe engine, LVGL UI, networking |
| Motor Controller | STM32G474RE (LQFP-64) | - | Unified PCB | Real-time control: PID, servos, sensors, safety |
| Camera Module | IMX415-98 IR-CUT (8 MP) | MIPI CSI-2 (4-lane FPC) | Pico Zero CSI connector | Overhead food monitoring, CV inference |
| IR Thermometer | MLX90614ESF-BAA | I2C | STM32 I2C1 | Non-contact food surface temperature |
| BLDC Stirring Motor | 24V BLDC (integrated ESC) | PWM (10kHz) + EN + DIR | STM32 PA8 + PA4 + PA5 | Stirring arm rotation |
| Dispenser Servos (DSB) | DS3218-class 270° digital servo (x4) | 50 Hz PWM via PCA9685 | PCA9685 CH0-CH3 → J_DSB1-4 | CID carousel index (C1); FID carousel index, dose, steam gate (F1-F3) |
| PCA9685 Servo Driver (DSB) | PCA9685PW | I2C | STM32 I2C1 (PA15/PB7) addr 0x41, OE on PB4 | Single PWM control block for FID + CID servos |
| SLD Peristaltic Pumps | 12V DC (x2) via TB6612 | GPIO (PWM/DIR) | STM32 PC3-PC6 | Oil and water dispensing |
| SLD Solenoid Valves | 12V NC (x2) | I2C (GPIO expander) | PCF8574 #2 P0/P1 (0x21) via MOSFET | Liquid drip prevention |
| Exhaust Fans | 2× 120mm 12V DC brushless | PWM (25kHz) | STM32 PA6, PB10 via MOSFET | Fume extraction, independent control |
| Piezo Buzzer | 5V active | PWM | STM32 PC7 via MOSFET | Audio alerts |
| USB-C Receptacle | Mid-mount 16-pin | USB 2.0 FS | STM32 PA11/PA12 (native USB) | DFU programming, CDC serial debug |
| Li-Ion Battery | Single cell 3.7V (JST-PH) | Analog | TP4056 charger on Unified PCB | Micro-UPS for STM32 state retention |
| Microwave Induction Surface | Commercial module w/ CAN | CAN 2.0B (500kbps) | STM32 FDCAN1 (PB8/PB9) | Self-contained induction heating with internal coil, driver, and safety |
| 4" Touchscreen | 4" 480x320 IPS, ST7796S + FT6336 | SPI (LCD) + I2C (touch) | RV1106 SPI0 + I2C3 | User interface display |
| PSU Module | Mean Well LRS-75-24 | AC-DC 24V | AC mains input | 24V DC to Unified PCB (derives 12V, 5V, 3.3V for all subsystems) |
| Safety Relay | Omron G5V-2 or equiv. | GPIO (via MOSFET) | STM32 GPIO | Induction mains disconnect |
| LED Ring | WS2812B strip (12-16 LEDs) | Single-wire data (800 kHz) | STM32 PB14 (TIM15_CH1) via 74AHCT1G125 | Pot illumination for camera |
| E-Stop Button | Normally-closed mushroom | GPIO (interrupt) | STM32 GPIO + relay | Emergency power cutoff |
| Pot Detection | Internal to microwave surface | CAN status | Module-reported via CAN | Detect pot presence (module-internal) |

---

## 4. Compute Platform (Luckfox Pico Zero / RV1106G3)

### 4.1 Luckfox Pico Zero Module Specifications

| Specification | Value |
|--------------|-------|
| SoC | Rockchip RV1106G3, 1x Cortex-A7 (32-bit) @ 1.2 GHz |
| RAM | 256 MB DDR3L (in-package) |
| Storage | 8 GB eMMC (on-board), microSD slot (storage expansion only) |
| Accelerators | 1 TOPS INT8 NPU, 5 MP hardware ISP, H.264/H.265 encoder (no decoder), RGA 2D engine |
| GPU | None (LVGL software rendering) |
| Video Output | None on-board; 4" SPI LCD on SPI0 (see Section 8) |
| Camera | 1x 4-lane MIPI CSI-2 (FPC connector) |
| Networking | On-board 2.4 GHz Wi-Fi 6, Bluetooth 5.2 LE; on-board antenna + external antenna connector. No Ethernet |
| USB | 1x USB-C (power + flashing) |
| Header | 40-pin RPi-style, 28 GPIO, 3.3V logic |
| Other | On-board mic, MX1.25 speaker header, RTC battery header, user LED, RESET/BOOT buttons |
| Power / Thermal | ~1 W class, no heatsink; ambient -20 to +85C, Tj max 125C |
| Operating System | Buildroot Linux (Luckfox SDK, kernel 5.10), read-only squashfs rootfs |
| Form Factor | 65 x 30 mm, four 3.0 mm mounting holes |

### 4.2 Board Integration (No Carrier Board)

The Pico Zero is a complete single-board module: no carrier board is needed. It plugs into the Unified PCB's 40-pin header (J_CM5) for 5V power and all logic signals; the camera and display attach to the module directly.

```
┌───────────────────────────────────────────────────────────────┐
│              Luckfox Pico Zero (RV1106G3)                     │
│                                                               │
│  MIPI CSI (FPC) ──► IMX415 camera module (4-lane)             │
│  SPI0 ──────────► 4" ST7796S LCD (fbtft, 50 MHz, DMA)         │
│  I2C3 ──────────► FT6336 touch controller                     │
│  UART2 ─────────► STM32 USART2 bridge (1 Mbps)                │
│  GPIO 32 / 38 ──► STM32 BOOT0 / NRST (firmware update)        │
│  PWM10 ─────────► LCD backlight                               │
│  UART0 ─────────► Debug console                               │
│  USB-C ─────────► Flashing (rkdevtool) / alternate 5V input   │
│  Wi-Fi 6 / BT 5.2 ► On-board module, antenna connector        │
│  40-pin header ──► Unified PCB (5V in, all signals above)     │
│                                                               │
│  Power Input: 5V / 1A from Unified PCB (via 40-pin pins 2, 4) │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 RV1106 Header Pin Allocation

| Header pin | Function | Direction | Notes |
|------------|----------|-----------|-------|
| 8 (UART2_TX, M1) | UART TX to STM32 USART2 RX (PA3) | Output | 1,000,000 baud, 8N1, 3.3V logic |
| 10 (UART2_RX, M1) | UART RX from STM32 USART2 TX (PA2) | Input | 1,000,000 baud, 8N1, 3.3V logic |
| 19 (SPI0_MOSI) | LCD MOSI | Output | 50 MHz, fbtft with DMA |
| 21 (SPI0_MISO) | LCD MISO | Input | Reserved (fbtft is write-only) |
| 23 (SPI0_CLK) | LCD clock | Output | 50 MHz |
| 24 (SPI0_CS0) | LCD chip select | Output | Active-low |
| 22 (GPIO) | LCD DC (data/command) | Output | |
| 26 (GPIO) | LCD RST | Output | |
| 12 (PWM10) | LCD backlight PWM | Output | Dimmable |
| 16 (I2C3_SDA, M0) | Touch SDA (FT6336) | Bidirectional | 400kHz, pull-up to 3.3V |
| 18 (I2C3_SCL, M0) | Touch SCL (FT6336) | Bidirectional | 400kHz, pull-up to 3.3V |
| 36 (GPIO) | Touch INT | Input | Active-low, evdev |
| GPIO 32 | STM32 BOOT0 | Output | Driven high to enter the ST system bootloader for firmware update |
| GPIO 38 | STM32 NRST | Output | Reset pulse during firmware update |
| 35 / 37 (UART0, M0) | Debug console TX / RX | - | Luckfox default |
| CSI (FPC) | Camera data lanes | Input | 4-lane MIPI, IMX415-98 |
| Spare | UART3, UART4, I2C1, I2C2, PWM | - | Available |

---

## 5. STM32 Motor Controller

### 5.1 STM32G474RE Specifications

| Specification | Value |
|--------------|-------|
| Core | ARM Cortex-M4F @ 170 MHz |
| Flash | 512 KB |
| RAM | 128 KB SRAM |
| ADC | 5x 12-bit ADC (up to 4 Msps) |
| Timers | 17 timers (advanced, general, basic) |
| UART | 5x USART/UART |
| I2C | 4x I2C |
| SPI | 4x SPI |
| CAN | 3x FDCAN |
| PWM | Multiple channels across timers |
| GPIO | Up to 51 I/O pins (LQFP-64) |
| Supply | 3.3V (from PSU 3.3V rail) |
| RTOS | FreeRTOS |

### 5.2 STM32 Pin Allocation

```
STM32G474RE (LQFP-64)
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌─── USART2: RV1106 Bridge + System Bootloader ───────┐     │
│  │  PA2  (USART2_TX) ──► RV1106 UART2_RX (header 10)   │     │
│  │  PA3  (USART2_RX) ◄── RV1106 UART2_TX (header 8)    │     │
│  │  1,000,000 baud, 8N1, 3.3 V, DMA RX ring buffer     │     │
│  │  Also the ST system-bootloader UART (firmware OTA)  │     │
│  │  Freed from bridge: PB12, PB13, PB15, PB3 (spare)   │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─── CAN: Microwave Surface ─────┐                          │
│  │  PB8  (FDCAN1_RX) ◄── ISO1050DUB on-board (CAN_RX)        │
│  │  PB9  (FDCAN1_TX) ──► ISO1050DUB on-board (CAN_TX)        │
│  │  Bit rate: 500 kbps, isolation + termination on Unified PCB│
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── PWM+GPIO: BLDC Stirring Motor ─┐                       │
│  │  PA8  (TIM1_CH1)  ──► BLDC Motor PWM (10 kHz speed)       │
│  │  PA4  (GPIO)      ──► BLDC Motor EN (enable)              │
│  │  PA5  (GPIO)      ──► BLDC Motor DIR (CW/CCW)             │
│  └─────────────────────────────────────┘                     │
│                                                              │
│  ┌─── Dispenser Servo Block (FID + CID servos) ───┐          │
│  │  I2C1 (PA15/PB7)  ──► PCA9685 PWM driver (addr 0x41)      │
│  │    CH0 ──► C1 CID carousel index servo                    │
│  │    CH1 ──► F1 FID carousel index servo                    │
│  │    CH2 ──► F2 FID dose servo (¼ tsp measure wheel)        │
│  │    CH3 ──► F3 FID steam-gate servo                        │
│  │  PB4  (GPIO)      ──► PCA9685 OE (active-low; high = off) │
│  │  PCF8574 #2 P4    ──► DSB 6.5 V rail enable (P-MOSFET)    │
│  │  Rail: MP1584EN #2, 6.5 V / 3 A, one servo at a time      │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── SLD Subsystem (Standard Liquid Dispenser) ──┐          │
│  │  PC3  (GPIO)       ──► SLD-OIL Pump PWM (TB6612 PWMA)     │
│  │  PC4  (GPIO)       ──► SLD-OIL Pump DIR (TB6612 AIN1)     │
│  │  PC5  (GPIO)       ──► SLD-WATER Pump PWM (TB6612 PWMB)   │
│  │  PC6  (GPIO)       ──► SLD-WATER Pump DIR (TB6612 BIN1)   │
│  │  PCF8574 #2 P0     ──► SLD-OIL Solenoid (via MOSFET)      │
│  │  PCF8574 #2 P1     ──► SLD-WATER Solenoid (via MOSFET)   │
│  │    (I2C1 addr 0x21, on Unified PCB)                       │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── Exhaust Fans (2x 120mm) ────┐                          │
│  │  PA6  (TIM3_CH1)  ──► Exhaust Fan 1 PWM (25 kHz, HW PWM)  │
│  │  PB10 (GPIO)      ──► Exhaust Fan 2 PWM (25 kHz, SW PWM)  │
│  │  Independent control for optimal airflow                  │
│  │  Note: PB10 uses software PWM (TIM2_CH3 conflicts with PA2)
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── Audio ───────────────────────┐                         │
│  │  PC7  (TIM8_CH2)  ──► Piezo Buzzer PWM                    │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── LED Ring (WS2812B) ──────────┐                         │
│  │  PB14 (TIM15_CH1) ──► 74AHCT1G125 ──► WS2812B DIN (5 V)   │
│  │  PWM + DMA, 800 kHz bit timing; 5 V ring power switched   │
│  │  by PCF8574 #2 P3. Modes requested by RV1106 via SET_LED  │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── USB: Programming & Debug (Native USB 2.0 FS) ───┐     │
│  │  PA11 (USB_DM)    ◄─► USB-C D- (22R + USBLC6 ESD)        │
│  │  PA12 (USB_DP)    ◄─► USB-C D+ (22R + USBLC6 ESD)        │
│  │  PC0  (ADC)       ◄── VBUS detect (100k/100k divider)    │
│  │  Modes: DFU bootloader (BOOT0 HIGH), USB CDC serial       │
│  │  5.1kR CC pulldowns for UFP/device identification         │
│  │  500mA polyfuse on VBUS                                   │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─── I2C: IR Thermometer ────────┐                          │
│  │  PA15 (I2C1_SCL) ──► MLX90614 SCL                         │
│  │  PB7  (I2C1_SDA) ◄─► MLX90614 SDA                         │
│  │  100 kHz, pull-ups 4.7k to 3.3V                           │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── GPIO: Safety & Control ─────┐                          │
│  │  PB0  (GPIO)      ──► Safety Relay (via MOSFET driver)    │
│  │  PB1  (GPIO)      ◄── Pot Detection (reed switch)         │
│  │  PB2  (GPIO)      ◄── E-Stop Button (interrupt, act-low)  │
│  │  PCF8574 #2 P2    ──► Status LED (on-board, 0x21)         │
│  └─────────────────────────────────┘                         │
│                                                              │
│  Power: 3.3V / GND from PSU rail                             │
│  Debug: SWD (PA13/PA14) via TagConnect or 10-pin header      │
│                                                              │
│  Note: All actuator signals route directly on-board to       │
│  power driver ICs on the Unified PCB. No stacking connector  │
│  is needed — STM32 and driver electronics share one board.   │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Camera Interface

### 6.1 MIPI CSI Wiring (Pico Zero to IMX415-98 Camera Module)

```
Luckfox Pico Zero                    IMX415-98 Camera Module
(MIPI CSI FPC Connector)             (FPC supplied with module)
┌──────────────────┐                ┌──────────────────┐
│                  │   FPC cable    │                  │
│  CSI_D0_P/N ─────┼────────────────┼──── MIPI_D0_P/N  │
│  CSI_D1_P/N ─────┼────────────────┼──── MIPI_D1_P/N  │
│  CSI_D2_P/N ─────┼────────────────┼──── MIPI_D2_P/N  │
│  CSI_D3_P/N ─────┼────────────────┼──── MIPI_D3_P/N  │
│  CSI_CLK_P/N ────┼────────────────┼──── MIPI_CLK_P/N │
│  SCL (I2C) ──────┼────────────────┼──── SCCB_SCL     │
│  SDA (I2C) ──────┼────────────────┼──── SCCB_SDA     │
│  MCLK ───────────┼────────────────┼──── MCLK         │
│  Power ──────────┼────────────────┼──── VCC          │
│  GND ────────────┼────────────────┼──── GND          │
│  GPIO (CAM_EN) ──┼────────────────┼──── PWDN/RESET   │
│                  │                │                  │
└──────────────────┘                └──────────────────┘

Cable: FPC supplied with the Luckfox IMX415-98 module, <20cm length
Signal: 4-lane MIPI CSI-2; IMX415-98 configured for 1280x720 @ 30 fps
ISP: RV1106 hardware ISP (IMX415-98 tuning file from the Luckfox SDK)
```

### 6.2 LED Ring Illumination

```
STM32 PB14 (TIM15_CH1, PWM + DMA)
      │
      │  Data (3.3V logic, 800 kHz)
      ▼
┌───────────────┐
│ 74AHCT1G125   │  3.3V → 5V level shifter
│ (OE tied low) │
└───────┬───────┘
        │  Data (5V logic)
        ▼
┌───────────────────────────────────────┐
│          WS2812B LED Ring             │
│    (12-16 addressable RGB LEDs)       │
│                                       │
│  DIN ◄── Data from 74AHCT1G125        │
│  VCC ◄── 5V from PSU rail, switched   │
│          by PCF8574 #2 P3 (MOSFET)    │
│  GND ◄── Common ground                │
│                                       │
│  Mounted: Ring around camera lens     │
│  Color: Neutral white (5000-6000K)    │
│  Brightness: Software-adjustable      │
│  Current: ~60mA per LED at max white  │
│  Total: ~1A max (16 LEDs full white)  │
└───────────────────────────────────────┘

Note: The ring is driven by the STM32, not the RV1106. The RV1106
requests OFF/CAPTURE/NIGHT mode, colour and brightness via SET_LED
(0x20) over the UART bridge.
```

---

## 7. IR Thermometer Interface

### 7.1 MLX90614 I2C Wiring

```
STM32G474RE                        MLX90614ESF-BAA
┌──────────────────┐             ┌──────────────────┐
│                  │             │                  │
│  PA15 (I2C1_SCL) ─┼──────┬──────┼── SCL (Pin 3)    │
│                  │      │      │                  │
│  PB7 (I2C1_SDA) ─┼──────┼──┬───┼── SDA (Pin 1)    │
│                  │      │  │   │                  │
│  3.3V ───────────┼──┬───┘  │   │                  │
│                  │  │      │   │  VDD (Pin 2) ────┼─── 3.3V
│                  │  │   4.7k   │                  │
│                  │  │      │   │  VSS (Pin 4) ────┼─── GND
│                  │  4.7k   │   │                  │
│                  │  │      │   │  I2C Addr: 0x5A  │
│  GND ────────────┼──┴──────┴───┼── GND            │
│                  │             │                  │
└──────────────────┘             └──────────────────┘

Decoupling: 100nF ceramic cap on VDD close to MLX90614
Pull-ups: 4.7k ohm to 3.3V on both SCL and SDA
Bus speed: 100 kHz (SMBus compatible)
Cable length: <30cm (keep short for I2C reliability)
```

### 7.2 MLX90614 Mounting

- Mounted on a bracket angled ~30 degrees toward pot center
- Distance from food surface: 5-10cm
- FOV of 90 degrees covers pot diameter at this distance
- Protected from steam with small shroud or filter window
- Emissivity configurable in firmware (default 0.95 for food/water)

---

## 8. Display Interface

### 8.1 SPI LCD Wiring

```
Luckfox Pico Zero (40-pin header)    4" ST7796S IPS LCD (480x320)
┌──────────────────┐               ┌──────────────────────────┐
│                  │               │                          │
│  Pin 19 (MOSI) ──┼──────────────►┼──── SDI (MOSI)           │
│  Pin 21 (MISO) ◄─┼───────────────┼──── SDO (MISO, unused)   │
│  Pin 23 (CLK) ───┼──────────────►┼──── SCK                  │
│  Pin 24 (CS0) ───┼──────────────►┼──── CS                   │
│  Pin 22 (GPIO) ──┼──────────────►┼──── DC (data/command)    │
│  Pin 26 (GPIO) ──┼──────────────►┼──── RESET                │
│  Pin 12 (PWM10) ─┼──────────────►┼──── LED (backlight PWM)  │
│  3.3V ───────────┼───────────────┼──── VCC                  │
│  GND ────────────┼───────────────┼──── GND                  │
│                  │               │                          │
└──────────────────┘               │  Touch Controller:       │
                                   │  ┌────────────────────┐  │
Luckfox Pico Zero I2C3             │  │  FT6336 Capacitive │  │
┌──────────────────┐               │  │  Touch (I2C 0x38)  │  │
│  Pin 16 (SDA) ───┼───────────────┼──┼── SDA              │  │
│  Pin 18 (SCL) ───┼───────────────┼──┼── SCL              │  │
│  Pin 36 (INT) ◄──┼───────────────┼──┼── INT (touch event)│  │
│  GND ────────────┼───────────────┼──┼── GND              │  │
└──────────────────┘               │  └────────────────────┘  │
                                   └──────────────────────────┘

SPI Configuration:
  Bus:        SPI0 (M0), 50 MHz, Mode 0, DMA
  Driver:     fbtft (ST7796S) → /dev/fb0, RGB565
  Refresh:    ~50 ms full frame; LVGL partial redraws
  Touch:      I2C3 (M0), 400 kHz, evdev; INT active-low on pin 36
  Backlight:  PWM10 on header pin 12
  Cable:      FPC or ribbon to the LCD module, <20cm length
```

### 8.2 Display Specifications

| Parameter | Value |
|-----------|-------|
| Size | 4.0 inches diagonal |
| Resolution | 480 x 320 pixels (HVGA) |
| Panel Type | IPS TFT LCD |
| Controller | ST7796S (4-wire SPI) |
| Module | 4.0" 480x320 IPS SPI module with ST7796S + FT6336U (e.g. the lcdwiki "4.0inch Capacitive SPI Module ST7796" or equivalent): glass 60.88 x 94.57 mm, active area 83.52 x 55.68 mm (landscape), module 108.0 x 60.88 x 14.8 mm incl. 14-pin header (also 0.5 mm FPC) |
| Interface | SPI0 at 50 MHz (fbtft driver with DMA) |
| Touch | Capacitive (I2C, FT6336 controller) |
| Backlight | LED, PWM dimmable via RV1106 PWM10 |
| Viewing Angle | 170 degrees (IPS) |
| Brightness | 300-400 cd/m2 (adequate for kitchen ambient) |
| Supply | 5 V module supply (3.3 V tolerated), 3.3 V logic; backlight 8 white LEDs, ~103 mA (0.5 W), PWM dimmed |

---

## 9. RV1106-STM32 Communication

### 9.1 UART Wiring (Primary)

```
Luckfox Pico Zero (UART2, M1)      STM32G474RE (USART2)
┌──────────────────┐               ┌──────────────────┐
│                  │               │                  │
│  Pin 8  (TX)   ──┼──────────────►┼── PA3 (RX)       │
│  Pin 10 (RX)   ◄─┼───────────────┼── PA2 (TX)       │
│  GPIO 32       ──┼──────────────►┼── BOOT0          │
│  GPIO 38       ──┼──────────────►┼── NRST           │
│  GND ────────────┼───────────────┼── GND            │
│                  │               │                  │
└──────────────────┘               └──────────────────┘

UART Configuration:
  Baud:       1,000,000 (1 Mbps), 8N1, no flow control
  Framing:    SOF 0x7E, 0x7D byte-stuffing, CRC-16/CCITT
  Data-ready: None; STM32 pushes TELEMETRY at 20 Hz unsolicited
  DMA:        Enabled on STM32 USART2 RX (ring buffer) and TX
  Logic:      3.3V (both RV1106 and STM32 are 3.3V native)
  Bootloader: USART2 is an ST system-bootloader UART; the BOOT0/NRST
              lines let the RV1106 flash STM32 firmware over this link
  Cable:      5-wire JST-SH, <30cm length
  Nucleo:     NUCLEO-G474RE (MB1367): PA2/PA3 reach the ST-LINK VCP via
              SB17/SB23 (ON by default, UM2505 rev 4). Remove SB17+SB23 and
              fit SB18+SB22 for Arduino D1/D0 (CN9), or use morpho CN10
              pins 35 (PA2) / 37 (PA3). Check the MB1367-G474RE-C04
              schematic before soldering, or use the custom controller PCB
```

### 9.2 CAN Bus Wiring (Microwave Surface)

CAN bus is used for controlling the microwave induction surface module. The STM32's FDCAN1 logic signals (PB8/PB9) connect directly to an on-board ISO1050DUB isolated CAN transceiver (5 kV RMS) on the **Unified PCB**, which converts them to differential CAN_H/CAN_L signals on J_CAN.

```
Microwave Surface              Unified PCB
(built-in CAN port)            (STM32 FDCAN1 + ISO1050DUB + J_CAN)
┌──────────────────┐           ┌──────────────────────────────────┐
│  Onboard         │           │  STM32 FDCAN1    ISO1050DUB      │
│  CAN controller  │           │  PB8 (RX) ◄──── RXD  │           │
│           │      │           │  PB9 (TX) ────► TXD  │           │
│  CAN_H ───┼──────┼───────────┼──────────────── CANH │  R_TERM   │
│  CAN_L ───┼──────┼───────────┼──────────────── CANL │  120Ω     │
│  GND ─────┼──────┼───────────┼──────────────── GND_ISO          │
│           │      │           │                                  │
│       120 ohm    │           │  VCC1=3.3V  VCC2=5V              │
│      termination │           │  (5kV isolation)                 │
└──────────────────┘           └──────────────────────────────────┘

CAN Configuration:
  Bit Rate:    500 kbps (standard CAN 2.0B)
  Termination: 120 ohm at each end (module + Unified PCB)
  Isolation:   ISO1050DUB on Unified PCB (5 kV RMS, ≥6.4mm creepage)
  Nodes:       Microwave surface (required), STM32 on Unified PCB (required)
```

### 9.3 Message Protocol (UART)

Type codes are owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]; this table mirrors it. Blocks: `0x0x` core, `0x1x` STM32 → RV1106 reports, `0x2x` LED ring + arm, `0x3x` dispensing (see [[../05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]] §7.3), `0xFF` ACK/NAK.

| Message ID | Name | Direction | Payload | Description |
|------------|------|-----------|---------|-------------|
| 0x01 | SET_TEMP | RV1106 -> STM32 | target_temp (C), ramp_rate | Set induction PID setpoint |
| 0x02 | SET_STIR | RV1106 -> STM32 | pattern, speed_rpm, direction | Set stirring pattern, speed and direction |
| 0x04 | E_STOP | RV1106 -> STM32 | reason_code | Emergency shutdown command (no ACK) |
| 0x05 | HEARTBEAT | RV1106 -> STM32 | uptime_ms | Watchdog keepalive (every 2 s; STM32 IWDG 5 s) |
| 0x10 | TELEMETRY | STM32 -> RV1106 | IR temp, coil temp (via induction CAN), motor rpm, weight, state | Periodic sensor data (20 Hz, unsolicited) |
| 0x11 | SENSOR_DATA | STM32 -> RV1106 | adc_values[], ir_temp, load_cells[] | Raw sensor snapshot on request |
| 0x12 | STATUS | STM32 -> RV1106 | safety_state, error_code, flags | Safety state and fault codes (on change) |
| 0x20 | SET_LED | RV1106 -> STM32 | mode (OFF/CAPTURE/NIGHT), r, g, b, brightness_pct | LED ring control (ring is driven by STM32 PB14) |
| 0x21–0x25 | SET_SPEED, ARM_STOP, ARM_HOME, ARM_STATUS, SET_RAMP | RV1106 -> STM32 | see [[../05-Subsystems/02-Robotic-Arm|Robotic Arm]] §8.2 | Stirring arm block |
| 0x30–0x39 | DISPENSE_FID/CID/SLD, QUERY_WEIGHT, PREFLIGHT, TARE, DISPENSER_HOME/STATUS | RV1106 -> STM32 | see Ingredient Dispensing §7.3 | Dispensing block |
| 0xFF | ACK/NAK | STM32 -> RV1106 | ack_msg_id, result_code | Command acknowledgment |

### 9.4 Protocol Format (UART)

```
┌──────┬────────┬──────────┬─────────┬───────────────┬──────────┐
│ SOF  │ MSG_ID │ MSG_TYPE │ LENGTH  │   PAYLOAD     │  CRC-16  │
│ 0x7E │ 1 byte │  1 byte  │ 2 bytes │  0-64 bytes   │ 2 bytes  │
└──────┴────────┴──────────┴─────────┴───────────────┴──────────┘

Everything after SOF is byte-stuffed: 0x7E and 0x7D in the body are
escaped with 0x7D (see the Controller Software Architecture for the
exact scheme). CRC-16/CCITT covers MSG_ID..PAYLOAD. The receiver
discards bytes until SOF and validates the CRC before dispatch.
No data-ready line: STM32 pushes TELEMETRY at 20 Hz unsolicited.
RV1106 sends HEARTBEAT every 2 s; STM32 IWDG timeout is 5 s.
ACK timeout 500 ms, 3 retries. E_STOP needs no ACK.
Bandwidth: ~28 kbit/s worst case (<3% of link capacity).
```

---

## 10. Power Supply

### 10.1 AC-DC Power Supply Architecture

```
AC Mains (220-240V 50Hz)
        │
        ├──────────────────────────────────────────────┐
        ▼                                              ▼
┌───────────────────┐                    ┌──────────────────────────┐
│  IEC C14 Inlet    │                    │  Microwave Induction     │
│  + Fuse (10A)     │                    │  Surface Module          │
│  + EMI Filter     │                    │  (self-contained AC      │
│  (X2 cap + CMs)   │                    │   power + coil + driver) │
└────────┬──────────┘                    │  1,800W max              │
         │                               │  CAN bus ──► STM32       │
         ▼                               └──────────────────────────┘
┌────────────────────────────────────┐
│  Mean Well LRS-75-24               │
│  24V / 3.2A / 76.8W                │
│  Universal input: 85-264VAC        │
│  Efficiency: >87%                  │
│  PFC built-in                      │
└────────────────┬───────────────────┘
                 │
                 │ 24V DC Bus
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│             Unified PCB (J_24V_IN)               │
│                                                  │
│  24V ──► MP1584EN #1 ──► 12V (actuators)         │
│  24V ──► Direct 24V (BLDC motor, safety relay)   │
│                                                  │
│  12V ──► UPS battery ──► TPS54531 ──► 5V/5A      │
│  5V  ──► AMS1117 LDO ──► 3.3V (STM32, sensors)  │
│                                                  │
└────────┬─────────────────────────────────────────┘
         │
         │ 40-pin GPIO connector (J_CM5)
         │ (5V on pins 2,4; GND on pins 6,9,etc.)
         │ Direction: Unified PCB → Luckfox Pico Zero
         ▼
┌──────────────────┐
│ Luckfox Pico Zero│
│ (receives 5V)    │
│ ──► RV1106G3     │
│ ──► 4" LCD + cam │
│ USB-C for flash  │
└──────────────────┘

Note: Microwave induction surface has its own AC power
inlet (not through the 24V PSU). The PSU only feeds
logic, sensors, actuators, and display. The Pico Zero is
powered via the Unified PCB's 5V rail through the
40-pin header (pins 2, 4); its on-board regulators derive
the SoC, camera and Wi-Fi rails. It draws ~1 W.
STM32 controls the module via CAN bus (FDCAN1).
```

### 10.2 Mean Well LRS-75-24 Specifications

| Parameter | Value |
|-----------|-------|
| Output Voltage | 24V DC |
| Output Current | 3.2A max |
| Output Power | 76.8W |
| Input Range | 85-264VAC (universal) |
| Efficiency | >87% |
| Dimensions | 129 x 97 x 30mm |
| Protections | Short circuit, overload, over-voltage |
| Certifications | UL, CE, CB |

### 10.3 Power Budget Table

| Rail | Subsystem | Typical (W) | Peak (W) | Notes |
|------|-----------|-------------|----------|-------|
| AC direct | Microwave induction surface | 600 | 1,800 | Self-contained module, own AC inlet |
| 5V (from Unified PCB) | Luckfox Pico Zero (RV1106G3) | 1 | 2 | 5V via 40-pin header; includes eMMC, Wi-Fi/BT, IMX415-98 camera, NPU/ISP load |
| 5V → 3.3V (on Unified PCB) | 4" SPI LCD + backlight | 0.5 | 0.8 | ST7796S panel + LED backlight, PWM dimmed |
| 24V direct | BLDC stirring motor | 12 | 48 | 24V direct to integrated ESC, ~0.5A typical, ~2A peak |
| 24V → 6.5V buck (MP1584EN #2) | Dispenser servos DSB (x4, one moving at a time) | 0.5 | 20 | 6.5V rail switched on only during a dispense; ~2.5A stall |
| 24V → 12V | SLD peristaltic pumps (x2) | 0 | 6 | 12V, only during dispense |
| 24V → 12V | SLD solenoid valves (x2) | 0 | 10 | 5W each when energized |
| 24V → 5V buck | LED ring (WS2812B) | 2 | 5 | 16 LEDs at partial brightness |
| 24V direct | Safety relay coil | 0.5 | 1 | Mains disconnect for microwave surface |
| 24V → 12V | Exhaust fans (x2) | 1 | 6 | 12V DC, 120mm, 0.3-0.5A each |
| 5V → 3.3V (on Unified PCB) | STM32G474RE | 0.3 | 0.5 | AMS1117 LDO on Unified PCB |
| 5V → 3.3V (on Unified PCB) | MLX90614 + HX711 | 0.05 | 0.1 | Low-power I2C/SPI devices |
| - | Regulator losses | 5 | 10 | Buck + LDO inefficiency |
| **24V PSU Total** | | **~16W** | **~45W** | **Within 76.8W PSU capacity** |
| **System Total (incl. induction)** | | **~616W** | **~1,845W** | **Within 2kW limit** |

---

## 11. Microwave Induction Surface Module

### 11.1 Module Integration

The microwave induction surface is a self-contained commercial module with its own AC power inlet, power electronics, induction coil, and onboard safety circuits. Epicura interfaces with the module exclusively via CAN bus — no high-voltage wiring touches the Unified PCB.

```
┌──────────────────────────────────────────────────────────┐
│              Microwave Induction Surface                   │
│                                                            │
│  AC Mains ──► EMI Filter ──► Rectifier ──► Driver ──► Coil │
│                                                            │
│  Internal safety: pot detection, thermal cutoff,           │
│  overcurrent protection                                    │
│                                                            │
│  Exposed CAN Port:                                         │
│    CAN_H ──────────────────┐                               │
│    CAN_L ──────────────────┤                               │
│    GND ────────────────────┤                               │
└────────────────────────────┼───────────────────────────────┘
                             │
                    ┌─────────────────────┐
                    │  Unified PCB        │
                    │  ISO1050DUB         │
                    │  (5kV isolation)    │
                    │  + 120Ω term        │
                    │  + J_CAN conn       │
                    │        │            │
                    │  STM32 FDCAN1       │
                    │  PB8 (CAN_RX)       │
                    │  PB9 (CAN_TX)       │
                    └─────────────────────┘

System Safety:
  - Module-internal: pot detection, thermal fuse, overcurrent (cannot be overridden)
  - System-level: safety relay on AC mains to module (STM32 GPIO ──► relay)
  - STM32 can send CAN off command or open relay on fault/E-stop
```

---

## 12. Ingredient Dispensing System (FID / CID / SLD)

The dispensing system comprises three subsystems. FID and CID share one electrical control block, the Dispenser Servo Block (DSB). See [[03-Ingredient-Dispensing|Ingredient Dispensing System]] for full details.

### 12.1 DSB — FID + CID Servo Wiring

```
  24V Rail ──► MP1584EN #2 (6.5 V, 3 A) ──► P-MOSFET high-side switch ──► 6.5 V DSB rail
                                               ▲                            (1000 µF bulk, 3 A PTC)
                                   PCF8574 #2 P4 (rail enable, I2C1 0x21)

  I2C1 (PA15/PB7) ──► PCA9685 (addr 0x41, on Unified PCB)
                        ├── CH0 ──► J_DSB1 ──► C1  CID carousel index servo (4:3 gear-up)
                        ├── CH1 ──► J_DSB2 ──► F1  FID carousel index servo (4:3 gear-up)
                        ├── CH2 ──► J_DSB3 ──► F2  FID dose servo (canister ¼ tsp measure wheel)
                        └── CH3 ──► J_DSB4 ──► F3  FID steam-gate servo
  PB4 (GPIO) ──► PCA9685 OE (active-low; held high in boot-safe state and on E-stop)

  I2C1 devices: PCF8574 #2 (0x21), INA219 (0x40), PCA9685 (0x41), MLX90614 (0x5A)

  Note: replaces the P-ASD pneumatics (pump, 6 solenoids, ADS1015, PCF8574 #1) and the
  CID stepper / linear actuator (external driver, DRV8876 #2, J_CID). Freed STM32 pins:
  PA0, PA10, PB5, PB6, PB11, PC2, PD2. Stall detection via INA219 24 V current window.
```

### 12.2 SLD — Liquid Dispensing Wiring

```
  12V Rail (from on-board MP1584EN #1)
  │
  ├──► Peristaltic Pump (Oil) — TB6612 Channel A on Unified PCB
  │      PWMA ◄── PC3 (GPIO)
  │      AIN1 ◄── PC4 (GPIO)
  │
  ├──► Peristaltic Pump (Water) — TB6612 Channel B on Unified PCB
  │      PWMB ◄── PC5 (GPIO)
  │      BIN1 ◄── PC6 (GPIO)
  │
  ├──► Solenoid Valve (Oil)   ◄── PCF8574 #2 P0 (I2C1, 0x21), MOSFET + flyback
  └──► Solenoid Valve (Water) ◄── PCF8574 #2 P1 (I2C1, 0x21), MOSFET + flyback

  I2C for INA219 current monitor (on Unified PCB):
    SCL ◄── PA15 (I2C1_SCL)
    SDA ◄── PB7 (I2C1_SDA)

  SLD Load Cells (2× 2 kg, one per reservoir):
    HX711 #1 (oil):   SCK ◄── PC11 (GPIO), DOUT ──► PC12 (GPIO)
    HX711 #2 (water): SCK ◄── PC9  (GPIO), DOUT ──► PC10 (GPIO)
    Low-level alert when reservoir weight < configurable threshold
```

### 12.3 Dispensing Summary

| Subsystem | Actuators | Metering | Min Dispense |
|-----------|-----------|----------|-------------|
| FID (fine / seasonings) | 3× servo on DSB (F1 index, F2 dose, F3 steam gate), 6 canisters with ¼ tsp measure wheels | Volumetric per dose stroke (±10%) | ¼ tsp (~0.5 g) |
| CID (coarse) | 1× servo on DSB (C1 index), 5-slot carousel + cover sector | Whole slot / user pre-measured | One slot (~200 mL) |
| SLD (liquids) | 2× peristaltic pump (TB6612) + 2× solenoid + 2× 2 kg load cell | Closed-loop via dedicated per-reservoir load cells + low-level alerts | ~5 g |
| Exhaust | 2× 120mm fans (independent PWM control) | Temperature/fume-based control | — |

**Unified PCB On-Board Routing:** All STM32 control signals connect directly to their corresponding driver ICs (PCA9685, TB6612, ISO1050DUB, PCF8574 #2, MOSFETs) on the same board. The four DSB servo leads plug into J_DSB1-4 (3-pin JR headers on the switched 6.5 V rail). No inter-board stacking connector is required. The Unified PCB connects to the Luckfox Pico Zero via the 40-pin GPIO header for UART communication and 5V power.

---

## 13. WiFi / Bluetooth

### 13.1 RV1106 Onboard Wireless

The Luckfox Pico Zero includes onboard WiFi and Bluetooth. No external modules are needed.

| Feature | Specification |
|---------|---------------|
| WiFi Standard | 802.11ax (WiFi 6), 2.4GHz single-band |
| Max Throughput | 2.4GHz only; ample for recipe sync, MQTT telemetry and the 1.5 Mbps H.264 live view |
| Bluetooth | BLE 5.2 |
| Antenna | Onboard antenna, plus external antenna connector |
| Security | WPA3, WPA2 |

### 13.2 Wireless Use Cases

| Function | Protocol | Description |
|----------|----------|-------------|
| App Pairing | BLE 5.2 | Initial device discovery and WiFi credential transfer |
| Recipe Download | HTTPS | Fetch new recipes from cloud API |
| Live Camera Feed | RTSP (H.264 720p) | On-demand stream to companion app (same LAN direct, otherwise via cloud relay) |
| Telemetry Upload | MQTT/HTTPS | Cooking session data to cloud (optional) |
| OTA Firmware Update | HTTPS + swupdate | RV1106 OS/app (A/B slots) and STM32 firmware updates |
| Remote Monitoring | MQTT | Telemetry to cloud every 10 s while cooking; cloud pushes status to the app |
| NTP Time Sync | NTP (UDP) | Clock synchronization on boot |

### 13.3 Antenna Considerations

- Pico Zero onboard antenna sufficient for typical kitchen distances (<10m)
- If mounted inside metal enclosure, use the external antenna connector to an antenna on rear panel
- Keep antenna away from induction coil EMI (rear-top placement preferred)

---

## 14. Storage Architecture

### 14.1 RV1106 Storage

```
┌────────────────────────────────────────────────────────┐
│            Luckfox Pico Zero Storage Layout            │
│                                                        │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │  eMMC (on-board) │    │  MicroSD Slot    │          │
│  │  8 GB            │    │  (on-board)      │          │
│  └────────┬─────────┘    └────────┬─────────┘          │
│           │                       │                    │
│  ┌────────▼─────────┐    ┌────────▼─────────┐          │
│  │  Partition Map:  │    │  Optional Use:   │          │
│  │                  │    │  (expansion only)│          │
│  │  boot_a/b 2x32MB │    │  Recipe backup   │          │
│  │  rootfs_a/b      │    │  Cooking logs    │          │
│  │     2x256MB      │    │  User media      │          │
│  │  oem      64MB   │    │  Debug dumps     │          │
│  │  data    ~6GB    │    │                  │          │
│  │  userdata 64MB   │    │                  │          │
│  └──────────────────┘    └──────────────────┘          │
│                                                        │
│  File Systems:                                         │
│  - boot_a/b: kernel + DTB (A/B slots, swupdate)        │
│  - rootfs_a/b: squashfs, read-only (Buildroot root)    │
│  - oem: models, ISP tuning, LVGL assets, recipes       │
│  - data: ext4 (/data/epicura.db, images, logs, OTA)    │
│  - userdata: Wi-Fi credentials, identity, calibration  │
│  - SD: FAT32 or ext4 (removable, user-accessible)      │
└────────────────────────────────────────────────────────┘
```

---

## 15. PCB Layout Considerations

### 15.1 Induction EMI Shielding

- The induction coil radiates strong magnetic fields at 20-40 kHz
- **Shielding:** Ferrite sheet between coil and electronics compartment
- **Distance:** Maintain minimum 50mm between coil and sensitive PCBs
- **Orientation:** Route I2C/SPI traces perpendicular to coil field lines
- **Grounding:** Copper ground pour on Unified PCB, connected to chassis ground

### 15.2 Sensor Signal Routing

- Keep I2C lines (MLX90614) short (<30cm), with 4.7k pull-ups near STM32
- HX711 clock/data lines: shielded twisted pair if >20cm, ground guard traces
- Camera CSI-2: differential pairs, matched length, <20cm FFC cable

### 15.3 Power / Signal Ground Separation

```
┌─────────────────────────────────────────────────────┐
│                  Ground Architecture                 │
│                                                      │
│  AC Mains Earth ──────────────┐                      │
│                               │                      │
│  Chassis Ground ◄─────────────┤                      │
│  (metal enclosure)            │                      │
│                               │                      │
│  Power Ground ◄───────────────┤ (star connection)    │
│  (PSU output returns,         │                      │
│   induction power stage)      │                      │
│                               │                      │
│  Signal Ground ◄──────────────┘                      │
│  (RV1106, STM32, sensors,                            │
│   low-current digital/analog)                        │
│                                                      │
│  Single-point star ground at PSU output              │
│  Ferrite bead between power GND and signal GND       │
└─────────────────────────────────────────────────────┘
```

### 15.4 Thermal Relief

- Microwave surface module: internal cooling; ensure adequate ventilation around module
- STM32: thermal vias under exposed pad to ground plane
- RV1106 (Pico Zero): ~1 W, no heatsink required; adequate ventilation space
- PSU: ventilated enclosure area, thermal shutdown at 85C internal

---

## 16. BOM Summary

### 16.1 Prototype Bill of Materials

| Category | Component | Quantity | Est. Unit Cost (USD) | Est. Total (USD) |
|----------|-----------|----------|---------------------|-------------------|
| **Compute** | Luckfox Pico Zero (RV1106G3, 8 GB eMMC) | 1 | $47 | $47 |
| | MicroSD 32GB | 1 | $10 | $10 |
| **MCU** | STM32G474RE Nucleo Board (proto) | 1 | $20 | $20 |
| | STM32G474RE IC (production) | 1 | $8 | $8 |
| **Display** | 4" ST7796S SPI LCD with FT6336 touch | 1 | $15 | $15 |
| **Camera** | Luckfox IMX415-98 IR-CUT 8 MP camera module (incl. 22-pin FPC) | 1 | $54 | $54 |
| **Sensors** | MLX90614ESF-BAA (IR thermo) | 1 | $12 | $12 |
| | HX711 breakout board | 1 | $3 | $3 |
| | 5kg load cells | 4 | $4 | $16 |
| | Reed switch (pot detect — backup/optional) | 1 | $1 | $1 |
| **Actuators** | 24V BLDC motor w/ integrated ESC | 1 | $25 | $25 |
| | DS3218-class 270° servos (DSB: FID x3 + CID x1) | 4 | $10 | $40 |
| | PCA9685 servo driver (DSB) | 1 | $1.50 | $1.50 |
| | FID canisters w/ ¼ tsp measure wheels | 6 | $3 | $18 |
| | FID + CID carousel rings, base plate, chutes, gears, bearings | 1 set | $26 | $26 |
| | 12V peristaltic pumps (SLD) | 2 | $10 | $20 |
| | 12V NC solenoid valves (SLD) | 2 | $4 | $8 |
| | 120mm 12V DC brushless fans (exhaust) | 2 | $5 | $10 |
| | 5V piezo buzzer (active) | 1 | $2 | $2 |
| **Induction** | Microwave induction surface (CAN-enabled) | 1 | $60 | $60 |
| **Power** | Mean Well LRS-75-24 (24V/3.2A) | 1 | $20 | $20 |
| | IEC C14 inlet + EMI filter | 1 | $8 | $8 |
| | Safety relay (Omron G5V-2) | 1 | $5 | $5 |
| **Misc** | WS2812B LED ring (16 LEDs) | 1 | $5 | $5 |
| | 74AHCT1G125 level shifter (LED ring) | 1 | $0.30 | $0.30 |
| | E-Stop mushroom button | 1 | $4 | $4 |
| | CAN transceiver (for FDCAN1) | 1 | $3 | $3 |
| | Passive components (R, C, etc.) | Lot | - | $20 |
| | Unified PCB (4-layer, 1 board) | 1 | $40 | $40 |
| | Wiring, connectors, FFC cables | Lot | - | $25 |
| **Enclosure** | 3D-printed enclosure (prototype) | 1 | $80 | $80 |
| | Pot (off-shelf induction-compatible) | 1 | $25 | $25 |
| | Gantry hardware (rods, brackets) | Lot | - | $30 |

**Estimated Prototype BOM Total: $620 - $720 USD**

*Note: Production BOM would be lower per unit at volume. Prototype uses Nucleo dev board that would be replaced with bare STM32G474RE on the Unified PCB. The Luckfox Pico Zero is used as-is (off-the-shelf module, no carrier board) in both prototype and production.*

---

## 17. Hardware Validation Checklist

### 17.1 Power Supply
- [ ] Verify 24V rail from Mean Well PSU within spec (24V +/-5%)
- [ ] Measure ripple on each rail (<50mV peak-to-peak)
- [ ] Load test at full power (microwave surface 1800W + all subsystems)
- [ ] Verify standby power <5W
- [ ] Test EMI filter effectiveness (conducted emissions)
- [ ] Verify fuse blows at rated overcurrent

### 17.2 Compute (RV1106)
- [ ] Luckfox Pico Zero boots Buildroot Linux from eMMC; A/B rootfs fallback verified
- [ ] UART communication to STM32 at 1 Mbps (loopback test, then bidirectional with framing + CRC)
- [ ] STM32 firmware load over USART2 via BOOT0/NRST from the RV1106
- [ ] Camera captures 1280x720 @ 30fps frames via MIPI CSI (IMX415-98, ISP tuning loaded)
- [ ] NPU runs the INT8 stage classifier in <20 ms
- [ ] Display renders LVGL UI via SPI0 (fbtft, full-frame refresh ~50 ms)
- [ ] Touch input (FT6336, I2C3) registers on all screen areas
- [ ] LED ring responds to SET_LED (OFF/CAPTURE/NIGHT) over the bridge
- [ ] WiFi connects to AP, achieves >10 Mbps throughput
- [ ] BLE advertises and pairs with test phone
- [ ] eMMC read/write speed adequate (>50 MB/s sequential)

### 17.3 Microwave Induction Surface
- [ ] Module responds to CAN queries (HEAT_QUERY → HEAT_STATUS)
- [ ] CAN power level commands correctly modulate heating
- [ ] Module heats water from 20C to 100C within 5 minutes (1.5L)
- [ ] PID holds temperature within +/-5C of setpoint
- [ ] All four power profiles (sear/boil/simmer/warm) verified
- [ ] Module-internal pot detection prevents heating without pot
- [ ] Safety relay disconnects AC to module on E-stop or fault
- [ ] CAN off command stops heating within 500ms

### 17.4 Servo System
- [ ] Main arm (24V BLDC motor) rotates full 360 degrees smoothly
- [ ] Stirring speed controllable from 10-60 RPM
- [ ] Arm torque sufficient to stir thick curry/dal
- [ ] Each DSB servo (x4) reaches commanded angle within ±2° via PCA9685
- [ ] DSB rail switches off after each dispense (no idle jitter or buzz)
- [ ] PCA9685 OE high on E-stop leaves all four servos limp

### 17.5 Sensors
- [ ] Camera: white balance calibrated, image sharp across full pot FOV
- [ ] IR (MLX90614): reads boiling water as 98-102C
- [ ] IR: reads room temp object within +/-1C of reference thermometer
- [ ] Load cells: tare on boot, measure 500g calibration weight within +/-5g
- [ ] Load cells: track water evaporation over 30-minute simmer
- [ ] Pot detection: reliably detects pot on/off

### 17.6 Dispensing (FID / CID / SLD)
- [ ] FID: Each canister doses ¼ tsp (1.23 mL) within ±10% per stroke
- [ ] FID: Jiggle routine clears a hand-packed canister without a stall
- [ ] FID: Steam gate closes by spring with servo unpowered
- [ ] CID: Each slot empties into the pot on index; cover sector closes aperture at home
- [ ] CID: Out-of-order slot command is NACKed, carousel does not move
- [ ] DSB: Stall detection (INA219 window) fires when a carousel is blocked by hand
- [ ] SLD: Each pump (TB6612) dispenses 50g liquid within ±5%
- [ ] SLD: Solenoid valves seal (no drips when idle)
- [ ] Both exhaust fans: PWM control from 0-100%, no audible whine
- [ ] Both exhaust fans: Independent control verified (each can run separately)
- [ ] Buzzer: All alert patterns audible and distinct
- [ ] No cross-contamination between subsystems
- [ ] Unified PCB: All subsystem signal routes verified on-board

---

## 18. Safety Considerations

### 18.1 Electrical Safety

- **Galvanic Isolation:** The microwave induction surface is a self-contained AC module — no mains voltage reaches the Unified PCB. The ISO1050DUB isolated CAN transceiver on the Unified PCB provides 5 kV RMS galvanic isolation between the CAN bus and STM32 logic. PSU provides transformer-isolated DC outputs.
- **Earth Bonding:** Metal enclosure parts connected to AC earth via IEC C14 inlet. Chassis ground bonded to PSU earth.
- **Fuse Protection:** 10A ceramic fuse in IEC C14 inlet. Self-resetting PTC fuse on 5V rail (3A).

### 18.2 Thermal Safety

- **Module Thermal:** Microwave surface has internal thermal cutoff. Module reports coil temperature via CAN status.
- **Food Over-Temperature:** IR thermometer monitors food surface. If >270C (beyond any recipe requirement), STM32 sends CAN off command and opens safety relay.
- **Enclosure Thermal:** Exhaust fan provides ventilation. Module reports internal temp via CAN for enclosure monitoring.

### 18.3 Mechanical Safety

- **E-Stop Button:** Red mushroom-head button on front panel. Normally-closed contact wired to STM32 interrupt AND safety relay. Pressing E-stop: (1) STM32 sends CAN off to module, (2) relay disconnects AC to microwave surface, (3) servos return to safe position.
- **Pot Detection Interlock:** Handled internally by microwave surface module. Module will not heat without compatible pot detected. Status reported via CAN.
- **Pinch Protection:** Arm mechanism has limited torque (BLDC motor current monitored via INA219). Arm speed limited in firmware to prevent splash/injury.

### 18.4 Overcurrent Protection

- **Mains:** 10A fuse (IEC C14)
- **DC Rails:** PTC self-resetting fuses on each rail
- **Induction Module:** Internal overcurrent protection (module-handled)
- **Servos:** Individual PTC fuses or current-limited driver

---

## 19. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[03-Sensors-Acquisition|Sensors & Data Acquisition]]
- [[04-Mechanical-Design|Mechanical Design]]
- [[../09-PCB/01-Unified-PCB-Design|Unified PCB Design]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[01-Tech-Stack|Tech Stack]]
- [[01-Prototype-Development-Plan|Prototype Development Plan]]

---

#epicura #hardware-architecture #wiring #system-design

---

## 20. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-20 | Manas Pradhan | Updated CAN bus architecture: ISO1050DUB transceiver and J_CAN connector moved from Controller PCB to Driver PCB; FDCAN1 logic signals route via J_STACK pins 19-20; updated block diagrams, wiring, safety notes, and J_STACK organization |
| 3.0 | 2026-02-20 | Manas Pradhan | Replaced DS3225 servo with 24V BLDC motor (integrated ESC); updated component list, STM32 pin allocation (PA4→BLDC_EN, PA5→BLDC_DIR, PA8→10kHz PWM), power budget, J_STACK pinout, and BOM |
| 5.2 | 2026-03-10 | Manas Pradhan | Datasheet review: PA1 COMP2→COMP1; buzzer PB11/TIM2_CH4→PC7/TIM8_CH2 (timer conflict fix); status LED PC13→PC8 (3mA limit) |
| 5.1 | 2026-03-10 | Manas Pradhan | Fixed I2C1_SCL pin: PB6 → PA15 (AF4) — PB6 lacks I2C1_SCL on LQFP-64 per DS12288 |
| 5.0 | 2026-03-09 | Manas Pradhan | Added USB-C programming port (native USB on PA11/PA12) and Li-Ion battery charger (TP4056+MT3608) to block diagram, component list, and STM32 pin allocation; buzzer moved from PA11 to PB11; 3-source 5V Schottky-OR power architecture |
| 4.0 | 2026-03-06 | Manas Pradhan | Merged Controller PCB and Driver PCB into single Unified PCB; removed J_STACK inter-board connector references — all signals now route directly on-board; updated CAN, dispensing, power, safety, and BOM sections; 2-board stack (CM5IO + Unified PCB) replaces prior 3-board stack |
| 5.3 | 2026-11-04 | Manas Pradhan | Application processor changed from Raspberry Pi CM5 + CM5IO to Luckfox Pico Zero (RV1106G3): STM32 bridge moved from SPI2 to USART2 (PA2/PA3, 1 Mbps UART framing), SC3336 camera at 720p on 4-lane CSI, 4" ST7796S SPI LCD + FT6336 touch replaces 10.1" DSI display, WS2812B ring driven by STM32 PB14 via 74AHCT1G125, on-board Wi-Fi 6 / BT 5.2, 8 GB eMMC A/B layout; VBUS detect moved PA3 → PC0; power budget, BOM and validation checklist updated |
| 6.0 | 2026-11-04 | Manas Pradhan | Dispensers redesigned: P-ASD pneumatics and CID stepper/linear actuator replaced by servo carousels (FID 3 servos, CID 1 servo) on one Dispenser Servo Block (PCA9685 @ 0x41, switched 6.5 V rail from MP1584EN #2, OE on PB4); removed PCF8574 #1, ADS1015, DRV8876 #2, J_CID; freed PA0, PA10, PB5, PB6, PB11, PC2, PD2; component list, pin allocation, power budget, wiring, BOM and checklist updated |
| 6.1 | 2026-11-04 | Manas Pradhan | Camera IMX415-98 IR-CUT ($54); 4" display module part and dimensions; Nucleo SB17/SB23 → SB18/SB22 note; message codes aligned to the software doc §7.2; CAN alternative for the bridge removed; BOM $620-720 |
