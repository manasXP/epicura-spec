---
created: 2026-02-15
modified: 2026-11-04
version: 8.2
status: Draft
---

# Epicura Hardware Architecture & Wiring Diagrams

## 1. Overview

This document provides the comprehensive hardware architecture, wiring diagrams, and interface specifications for the Epicura autonomous kitchen robot. The system uses a dual-processor architecture: a Rockchip RV1106G3 (Luckfox Pico Zero) running Buildroot Linux for AI/vision/UI, and an STM32G4 microcontroller running FreeRTOS for real-time motor control, sensing, and safety. Both sit on one Unified PCB: the Pico Zero in a slot (J_AP), the STM32 soldered down, with the CID/FID/SLD dispenser drivers, two CAN ports (isolated to the cooking surface, regular to the stirring motor) and a 2-cell Li-ion backup on the same board. There is no IR thermometer: the cooking surface runs its own temperature loop and reports its temperature over CAN.

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
          │   24V→12V, 24V→6.5V (MP1584EN); VSYS = 24V ⊕ 2S battery → TPS54531 → 5V │
          │   TP5100 2S charger; USB-C→5V (STM32 only); AMS1117 → 3.3V        │
          │                                    │                              │
          │        5V (J_AP slot, 40-pin)       │    3.3V                      │
          │              │                      │      │                       │
          │              ▼                      ▼      ▼                       │
          │  ┌───────────────────────┐      ┌────────────────────────────┐  │
          │  │  Luckfox Pico Zero    │      │  STM32G0B1RE               │  │
          │  │  RV1106G3 (Buildroot) │      │  (FreeRTOS)                │  │
          │  │                       │      │                            │  │
          │  │  - Recipe Engine      │      │  - Heater Interlock        │  │
          │  │  - CV Inference (NPU) │      │  - Servo Motor Control     │  │
          │  │  - UI Rendering (LVGL)│      │  - Sensor Acquisition      │  │
          │  │  - Cloud/WiFi/BT/OTA  │      │  - Dispensing Logic        │  │
          │  │  - Heater setpoints   │      │  - Safety Monitoring       │  │
          │  │                       │      │                            │  │
          │  │  ┌─────┐  ┌────────┐  │      │  ┌──────┐  ┌───────────┐  │  │
          │  │  │CSI-2│  │SPI0/I2C│  │      │  │ PWM  │  │ ADC/GPIO  │  │  │
          │  │  └──┬──┘  └───┬────┘  │      │  └──┬───┘  └─────┬─────┘  │  │
          │  └─────┼─────────┼───────┘      └─────┼─────────────┼───────┘  │
          │        │         │    ▲                │             │          │
          │        │         │    │ CAN 500 kbps   │             │          │
          │        │         │    │ (isolated bus) │             │          │
          │        │         │    └───────────────►│             │          │
          │        ▼         ▼                      ▼             ▼            │
          │   ┌────────┐ ┌──────────┐      ┌──────────────┐ ┌──────────────┐   │
          │   │IMX415  │ │4" ST7796S│      │Microwave     │ │  Sensors     │   │
          │   │8 MP    │ │480x320   │      │Induction     │ │  HX711 x2    │   │
          │   │Camera  │ │(SPI+I2C) │      │Surface (CAN, │ │  INA219      │   │
          │   └────────┘ └──────────┘      │own temp loop)│ │  Battery ADC │   │
          │                                └──────────────┘ └──────────────┘   │
          │   ┌────────┐ ┌──────────┐      ┌──────────────┐ ┌──────────────┐   │
          │   │WiFi 6  │ │eMMC 8 GB │      │24V CAN Servo │ │DSB Servos x4 │   │
          │   │2.4 GHz │ │+ microSD │      │Stirring Motor│ │FID 3 + CID 1 │   │
          │   │BLE 5.2 │ │Storage   │      │(FDCAN2 port) │ │SLD Pumps x2  │   │
          │   └────────┘ └──────────┘      └──────────────┘ └──────────────┘   │
          │                                                                    │
          │   ┌────────────────────────────────────────────────────────────┐   │
          │   │  LED Ring (WS2812B x 12-16) ── STM32 PB14 (TIM15_CH1 PWM)  │   │
          │   │  via 74AHCT1G125 level shifter; AP sends SET_LED over CAN  │   │
          │   │  2S Li-ion pack (J_BAT) keeps the 5 V domain alive on AC loss│   │
          │   └────────────────────────────────────────────────────────────┘   │
          └────────────────────────────────────────────────────────────────────┘
```

---

## 3. Main Component List

| Component | Part Number | Interface | Connected To | Purpose |
|-----------|-------------|-----------|--------------|---------|
| Compute Module | Luckfox Pico Zero (RV1106G3) | 40-pin header / CSI / USB-C | Unified PCB slot J_AP (2x20 socket + 4 standoffs) | AI/vision (NPU), recipe engine, heater setpoints, LVGL UI, networking |
| CAN Controller (RV1106 node) | MCP2518FD (SPI, 40 MHz crystal) + ISO1050DUB #2 | SPI0 CS1 + INT GPIO | Unified PCB, via the 40-pin header | Puts the RV1106 on the isolated CAN bus (SocketCAN `can0`) |
| Motor Controller | STM32G0B1RE (LQFP-64) | - | Unified PCB | Real-time control: stirring, dispensers, sensors, safety; isolated CAN node (FDCAN1) and stir-motor CAN master (FDCAN2) |
| Camera Module | IMX415-98 IR-CUT (8 MP) | MIPI CSI-2 (4-lane FPC) | Pico Zero CSI connector | Overhead food monitoring, CV inference |
| Stirring Motor | 24V integrated BLDC servo with CAN (CyberGear/RobStride-class, model TBD) | CAN 2.0B 1 Mbps (regular port) + switched 24V | STM32 FDCAN2 (PB12/PB13) via SN65HVD230 → J_CAN_STIR; 24V via Q_STIR → J_STIR_PWR | Stirring arm rotation with encoder feedback |
| Stir-Motor CAN Transceiver | SN65HVD230DR | FDCAN2 | Unified PCB, non-isolated | Regular CAN port to the stirring motor |
| Dispenser Servos (DSB) | DS3218 270° (C1), MG996R (F1, F2), MG90S (F3) | 50 Hz PWM via PCA9685 | PCA9685 CH0-CH3 → J_DSB1-4; J_DSB4 V+ via D_DSB4 (1N4007) | CID carousel index (C1); FID carousel index, dose, steam gate (F1-F3) |
| PCA9685 Servo Driver (DSB) | PCA9685PW | I2C | STM32 I2C1 (PB6/PB7) addr 0x41, OE on PB4 | Single PWM control block for FID + CID servos |
| SLD Peristaltic Pumps | 12V DC (x2) via TB6612 | GPIO (PWM/DIR) | STM32 PC3-PC6 | Oil and water dispensing |
| SLD Solenoid Valves | 12V NC (x2) | I2C (GPIO expander) | PCF8574 #2 P0/P1 (0x21) via MOSFET | Liquid drip prevention |
| Exhaust Fans | 2× 120mm 12V DC brushless | PWM (25kHz) | STM32 PA6, PB10 via MOSFET | Fume extraction, independent control |
| Piezo Buzzer | 5V active | PWM | STM32 PA8 (TIM1_CH1) via MOSFET | Audio alerts |
| USB-C Receptacle | Mid-mount 16-pin | USB 2.0 FS | STM32 PA11/PA12 (native USB) | DFU programming, CDC serial debug |
| Li-Ion Battery | 2S1P 18650 pack, 7.4V, 2,600 mAh, with PCM + NTC (JST-XH 3-pin, J_BAT) | Analog | TP5100 charger + VSYS diode-OR on Unified PCB; voltage to STM32 PC1 | Backup for the whole 5V logic domain (RV1106, LCD, STM32, CAN) through outages, > 4 h |
| Microwave Induction Surface | Commercial module w/ CAN and internal temperature control | CAN 2.0B (500kbps) | Isolated CAN port J_CAN_HEAT (RV1106 MCP2518FD + STM32 FDCAN1) | Self-contained induction heating with internal coil, driver, surface sensor, PID and safety; setpoints from the RV1106, forced off by the STM32 |
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

### 4.2 Board Integration (Slot on the Unified PCB)

The Pico Zero is a complete single-board module: no carrier board is needed. It seats pin-down into the Unified PCB's slot **J_AP** (2x20 socket, four M2.5 standoffs on the module's 3.0 mm holes) for 5V power and all logic signals. The camera attaches to the module's CSI connector directly; the display's SPI0/I2C3 lines are routed through the PCB to a 14-pin break-out (J_LCD).

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
│  40-pin header ──► Unified PCB slot J_AP (5V in, all signals  │
│                    above; LCD lines re-emerge on J_LCD)       │
│                                                               │
│  Power Input: 5V / 1A from Unified PCB (via J_AP pins 2, 4),  │
│               battery-backed (2S pack through VSYS diode-OR)  │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 RV1106 Header Pin Allocation

| Header pin | Function | Direction | Notes |
|------------|----------|-----------|-------|
| 8 (UART2_TX, M1) | Service UART TX to STM32 USART2 RX (PA3) | Output | 1,000,000 baud, 8N1, 3.3V; STM32 firmware flashing (ST bootloader) and debug only, no runtime traffic |
| 10 (UART2_RX, M1) | Service UART RX from STM32 USART2 TX (PA2) | Input | as above |
| SPI0_CS1 (GPIO 58) | MCP2518FD chip select | Output | CAN controller on the Unified PCB, ≤ 20 MHz; shares MOSI/MISO/CLK (pins 19/21/23) with the LCD |
| GPIO (spare) | MCP2518FD INT | Input | Active-low RX/TX FIFO interrupt; pin fixed at PCB layout |
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

### 5.1 STM32G0B1RE Specifications

The MCU was downsized from the STM32G474RE on 2026-11-04: with no control loop on the MCU (the induction module regulates itself, the stirring motor is a CAN servo) nothing needs an FPU or 170 MHz. The G0B1 is the cheapest ST part with two FDCAN controllers and keeps the same HAL, FreeRTOS, USART system bootloader and X-CUBE-CLASSB safety library. Pin map and rationale: [[../03-Software/05-MCU-Functional-Specification|MCU Functional Specification]].

| Specification | Value |
|--------------|-------|
| Part | STM32G0B1RET6 (256 KB RCT6 is a drop-in cost-down) |
| Core | ARM Cortex-M0+ @ 64 MHz, no FPU |
| Flash | 512 KB, dual-bank, ECC |
| RAM | 144 KB SRAM with parity |
| ADC | 1x 12-bit ADC (2.5 Msps, 16 channels, hardware oversampling) |
| Timers | TIM1 (advanced), TIM2/3/4, TIM14/15/16/17, TIM6/7, LPTIM1/2 |
| UART | 6x USART + 2x LPUART |
| I2C | 3x I2C |
| SPI | 3x SPI |
| CAN | 2x FDCAN (FDCAN1 isolated host/heater bus, FDCAN2 stir-motor bus) |
| USB | USB 2.0 FS (PA11/PA12) |
| GPIO | Up to 60 I/O pins (LQFP-64) |
| Safety | IWDG (LSI), WWDG, SRAM parity, flash ECC, CRC unit; X-CUBE-CLASSB (IEC 60730-1 Annex H Class B) |
| Supply | 3.3V (from PSU 3.3V rail) |
| RTOS | FreeRTOS |

### 5.2 STM32 Pin Allocation

```
STM32G0B1RE (LQFP-64)
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌─── USART2: Service Link (ST Bootloader + Debug) ────┐     │
│  │  PA2  (USART2_TX) ──► RV1106 UART2_RX (header 10)   │     │
│  │  PA3  (USART2_RX) ◄── RV1106 UART2_TX (header 8)    │     │
│  │  Firmware flashing via BOOT0/NRST; optional console │     │
│  │  No runtime traffic: host link is the CAN bus       │     │
│  │  Freed from bridge: PB12, PB13, PB15, PB3 (spare)   │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─── CAN: Isolated 3-node bus ───┐                          │
│  │  PB8  (FDCAN1_RX) ◄── ISO1050DUB #1 on-board (CAN_RX)     │
│  │  PB9  (FDCAN1_TX) ──► ISO1050DUB #1 on-board (CAN_TX)     │
│  │  500 kbps; nodes: RV1106 (MCP2518FD), STM32, induction    │
│  │  surface MCU. Host commands + telemetry ride this bus.    │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── FDCAN2: Regular bus to the stirring motor ───┐         │
│  │  PB12 (FDCAN2_RX) ◄── SN65HVD230 (non-isolated)           │
│  │  PB13 (FDCAN2_TX) ──► SN65HVD230 ──► J_CAN_STIR           │
│  │  1 Mbps; velocity/position commands at 50 Hz, feedback    │
│  │  PCF8574 #2 P5    ──► Q_STIR 24 V switch → J_STIR_PWR     │
│  │  Freed: PA5 (old DIR); PA4→battery ADC, PA8→buzzer        │
│  └─────────────────────────────────────┘                     │
│                                                              │
│  ┌─── Dispenser Servo Block (FID + CID servos) ───┐          │
│  │  I2C1 (PB6/PB7)   ──► PCA9685 PWM driver (addr 0x41)      │
│  │    CH0 ──► C1 CID carousel index servo (DS3218 270°)      │
│  │    CH1 ──► F1 FID carousel index servo (MG996R)           │
│  │    CH2 ──► F2 FID dose servo, ¼ tsp wheel (MG996R)        │
│  │    CH3 ──► F3 FID steam-gate servo (MG90S, 1N4007 drop)   │
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
│  │  PA8  (TIM1_CH1)  ──► Piezo Buzzer PWM                    │
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
│  │  PA0  (ADC_IN0)   ◄── VBUS detect (100k/100k divider)    │
│  │  Modes: DFU bootloader (BOOT0 HIGH), USB CDC serial       │
│  │  5.1kR CC pulldowns for UFP/device identification         │
│  │  500mA polyfuse on VBUS                                   │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─── I2C1 bus / Battery ───────────┐                        │
│  │  PB6  (I2C1_SCL), PB7 (I2C1_SDA): PCA9685 0x41,           │
│  │  PCF8574 #2 0x21, INA219 0x40 — 100 kHz, 4.7k pull-ups    │
│  │  PA4  (ADC_IN4)   ◄── 2S pack voltage (100k/22k divider)  │
│  │  PCF8574 #2 P6/P7 ◄── TP5100 CHRG / STDBY                 │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── GPIO: Safety & Control ─────┐                          │
│  │  PB0  (GPIO)      ──► Safety Relay (via MOSFET driver)    │
│  │  PB1  (GPIO)      ◄── Pot Detection (reed switch)         │
│  │  PB2  (GPIO)      ◄── E-Stop Button (interrupt, act-low)  │
│  │  PCF8574 #2 P2    ──► Status LED (on-board, 0x21)         │
│  └─────────────────────────────────┘                         │
│                                                              │
│  Power: 3.3V from the on-board LDO (5V_MAIN, battery-backed)  │
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
(CAN 0x220) over the shared CAN bus.
```

---

## 7. Stirring Motor CAN Port (Regular, Non-Isolated)

### 7.1 Wiring

```
STM32G0B1RE                 Unified PCB                              Stirring motor (24 V CAN servo)
┌──────────────────┐        ┌──────────────────────────────┐        ┌──────────────────────────┐
│ PB13 (FDCAN2_TX) ─┼──► D   │ SN65HVD230 (3.3 V)   CANH ──┼── J_CAN_STIR 1 ──┼── CAN_H              │
│ PB12 (FDCAN2_RX) ◄┼─── R   │  Rs 10k, 120 Ω term  CANL ──┼── J_CAN_STIR 2 ──┼── CAN_L  (120 Ω in   │
│                  │        │                      GND  ──┼── J_CAN_STIR 3 ──┼── GND     the motor) │
│ PCF8574 #2 P5 ───┼──► Q_STIR (AO4407A high-side) ── 24V_STIR ── J_STIR_PWR 1 ──┼── +24 V             │
│                  │        │  F_STIR 5 A                 GND ── J_STIR_PWR 2 ──┼── GND                │
└──────────────────┘        └──────────────────────────────┘        └──────────────────────────┘

Bus:      CAN 2.0B, 1 Mbps, 29-bit IDs (motor protocol); classic frames on FDCAN2
Cable:    twisted pair ≤ 1 m to the gantry, bundled with the 24 V pair; shield to GND at the PCB
Traffic:  50 Hz velocity (stir) / position (home, park) commands; 50 Hz feedback (rpm, angle,
          current, temperature, faults). Motor command timeout ≤ 500 ms configured at start-up.
Safety:   STM32 sends a disable frame AND opens Q_STIR on E-stop, heartbeat loss or FDCAN2 fault.
```

### 7.2 Why a Second Bus

The stirring motor is the only node on this bus. It is kept separate from the isolated heater bus so that the induction module's EMI domain never shares a transceiver with the motor, the 1 Mbps motor protocol does not load the 500 kbps host bus, and the galvanic barrier stays dedicated to the mains-side module.

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

## 9. Isolated CAN Bus (RV1106 ↔ STM32 ↔ Induction Surface)

One isolated CAN 2.0B bus at 500 kbps connects the three controllers: the Luckfox RV1106 (application processor), the STM32G0B1 (controller MCU on the Unified PCB) and the induction surface's own MCU. This is the Unified PCB's **isolated CAN port (J_CAN_HEAT)**; the stirring motor is on the separate regular port of Section 7. The RV1106 has no CAN peripheral, so it joins through an MCP2518FD SPI CAN controller on the Unified PCB (SPI0 CS1 through the J_AP slot) with its own ISO1050DUB; the STM32 keeps FDCAN1 + ISO1050DUB #1. Both transceivers share the isolated bus domain (5 V_ISO and GND_ISO from the B0505S-1WR3) and one 120 Ω termination at J_CAN_HEAT; the module terminates the far end. The induction module runs its own temperature loop; the RV1106 sends setpoints and reads status, and the STM32 can only force the heater off. Message IDs are owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]].

### 9.1 CAN Bus Wiring (Primary Link)

```
Luckfox Pico Zero (40-pin)        Unified PCB                                  Induction Surface
┌───────────────────┐    ┌──────────────────────────────────────────────┐     ┌────────────────┐
│ Pin 19 SPI0_MOSI ─┼───►│ MCP2518FD ─────► ISO1050DUB #2 ─┐            │     │  Onboard CAN   │
│ Pin 21 SPI0_MISO ◄┼────│ (SPI ≤20 MHz, 40 MHz xtal)      │            │     │  controller    │
│ Pin 23 SPI0_CLK ──┼───►│                                 ├─ CANH ─────┼─────┼── CAN_H        │
│ SPI0_CS1 (GPIO58)─┼───►│ CS                              ├─ CANL ─────┼─────┼── CAN_L        │
│ GPIO (INT) ◄──────┼────│ INT                             │  GND_ISO ──┼─────┼── GND          │
│                   │    │                            120 Ω│ J_CAN_HEAT │     │  120 Ω term    │
│ Pin 24 SPI0_CS0 ──┼──► LCD                               │            │     └────────────────┘
└───────────────────┘    │ STM32 FDCAN1 ───► ISO1050DUB #1 ┘            │
                         │ PB8 RX / PB9 TX                              │
                         │ 5 V_ISO + GND_ISO from B0505S-1WR3           │
                         └──────────────────────────────────────────────┘

CAN Configuration:
  Bit rate:     500 kbps, CAN 2.0B, 11-bit IDs (classic frames on FDCAN1)
  Nodes:        AP (RV1106 via MCP2518FD), STIR (STM32), HEAT (module MCU, own PID)
  Isolation:    2x ISO1050DUB on the Unified PCB in one isolated 5 V domain (B0505S-1WR3, 5 kV RMS)
  Termination:  120 Ω at J_CAN_HEAT (both on-board nodes are a short stub) and inside the module
  Linux:        mcp251xfd kernel driver → SocketCAN can0; epicurad `can` thread (SCHED_FIFO)
  SPI sharing:  MCP2518FD shares SPI0 MOSI/MISO/CLK with the LCD (CS0); an LCD DMA chunk holds
                the bus ≤10 ms, the MCP2518FD 32-object RX FIFO absorbs frames meanwhile
  Cable:        shielded twisted pair ≤1 m to the module; shield to GND_ISO at the PCB end only
```

### 9.2 UART Service Link (STM32 Flashing and Debug)

```
Luckfox Pico Zero (UART2, M1)      STM32G0B1RE (USART2)
┌──────────────────┐               ┌──────────────────┐
│                  │               │                  │
│  Pin 8  (TX)   ──┼──────────────►┼── PA3 (RX)       │
│  Pin 10 (RX)   ◄─┼───────────────┼── PA2 (TX)       │
│  GPIO 32       ──┼──────────────►┼── PA14-BOOT0     │
│  GPIO 38       ──┼──────────────►┼── NRST           │
│  GND ────────────┼───────────────┼── GND            │
│                  │               │                  │
└──────────────────┘               └──────────────────┘

UART Configuration:
  Role:       Service link only — ST system-bootloader protocol for STM32
              firmware updates (BOOT0/NRST driven by the RV1106) and an
              optional debug console. No commands or telemetry at runtime.
  Baud:       1,000,000 (bootloader auto-bauds), 8N1, no flow control
  Logic:      3.3V (both RV1106 and STM32 are 3.3V native)
  Cable:      5-wire JST-SH, <30cm length
  BOOT0:      On the G0 BOOT0 is multiplexed on PA14 (PA14-BOOT0, also SWCLK)
              and is only honoured when option bit nBOOT_SEL = 0; program it
              once over SWD at factory. A blank part enters the bootloader
              by itself (empty-flash check), so first programming still works.
  Nucleo:     NUCLEO-G0B1RE (MB1360): PA2/PA3 reach the ST-LINK VCP by
              default; re-route them to Arduino D1/D0 via the solder bridges
              in UM2324, or use the custom controller PCB
```

### 9.3 Message Map (CAN)

Identifiers are owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]; this table mirrors the blocks. Command frames carry a sequence byte first; ACK/NAK (0x3FF) echoes it.

| CAN ID block | Messages | Direction | Notes |
|--------------|----------|-----------|-------|
| 0x001 | E_STOP | any -> all | src_node, reason_code; no ACK, highest priority |
| 0x010 | HB_AP | RV1106 -> all | seq, uptime_ms; every 2 s, STM32 safe state after 5 s without it |
| 0x100–0x103 | HEAT_SET_TEMP, HEAT_ON_OFF, HEAT_QUERY, HEAT_SET_POWER | RV1106 -> module (STM32 sends HEAT_ON_OFF = 0 only) | Temperature setpoint (module PID) or power 0–100 %, re-sent at 2 Hz as keep-alive; module drops to 0 after 1 s without a refresh |
| 0x180–0x182 | HEAT_STATUS, HEAT_FAULT, HEAT_ACK | module -> all | Surface temperature, coil temperature, pot detection, faults (10 Hz); read by the RV1106 engine and the STM32 safety monitor |
| 0x202, 0x220–0x225 | SET_STIR, SET_LED, SET_SPEED, ARM_STOP, ARM_HOME, ARM_STATUS, SET_RAMP | RV1106 -> STM32 | Stirring arm and LED ring block (see [[../05-Subsystems/02-Robotic-Arm|Robotic Arm]] §8.2) |
| 0x230–0x239 | DISPENSE_FID/CID/SLD, QUERY_WEIGHT, PREFLIGHT, TARE, DISPENSER_HOME/STATUS | RV1106 -> STM32 | Dispensing block (see [[../05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]] §7.3) |
| 0x310–0x312 | TELEMETRY (20 Hz), LOADCELLS, STATUS | STM32 -> RV1106 | Motor rpm and current, load cells, safety state, battery/power-fail flags and fault codes |
| 0x3FF | ACK/NAK | STM32 -> RV1106 | seq, cmd_type, result_code, up to 5 data bytes |

### 9.4 Frame Conventions (CAN)

```
Standard frame: 11-bit ID | DLC 0–8 | payload
Commands (0x2xx):  byte 0 = seq (0–255, wraps), bytes 1..7 = payload (little-endian)
ACK/NAK (0x3FF):   byte 0 = seq, byte 1 = cmd_type, byte 2 = result, bytes 3..7 = data
Reports (0x3xx):   unsolicited; TELEMETRY at 20 Hz carries motor_rpm, motor_current_dA,
                   safety_state, flags, error_code, seq
Hardware ACK + 15-bit CRC come from CAN itself; no software framing or CRC.
Timeouts: application ACK 500 ms, 3 retries. E_STOP needs no ACK.
Bus load: ~6 kbit/s worst case (~1% of 500 kbps).
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
         │                               │  CAN bus, isolated       │
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
│  24V ──► MP1584EN #1 ──► 12V (fans, SLD, charger)│
│  24V ──► MP1584EN #2 ──► 6.5V (DSB servos)       │
│  24V ──► Q_STIR ──► 24V_STIR (CAN servo motor)   │
│  24V ⊕ 2S battery (diode-OR) ──► VSYS            │
│  VSYS ──► TPS54531 ──► 5V/5A (RV1106, LCD, STM32)│
│  12V ──► TP5100 ──► 2S Li-ion pack (J_BAT)       │
│  5V  ──► AMS1117 LDO ──► 3.3V (STM32, I2C, CAN) │
│                                                  │
└────────┬─────────────────────────────────────────┘
         │
         │ J_AP slot (2x20, Pico Zero plugs in)
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
powered via the Unified PCB's 5V rail through the J_AP
slot (pins 2, 4); its on-board regulators derive the SoC,
camera and Wi-Fi rails. It draws ~1 W. On AC loss the 2S
battery takes over the 5V domain through the VSYS diode-OR
(> 4 h); the 24V loads stop.
The RV1106 sends temperature/power setpoints to the module
over the isolated CAN bus (the module runs its own PID);
the STM32 can force it off on the same bus.
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
| 24V via Q_STIR | CAN servo stirring motor | 12 | 48 | 24V_STIR switched rail, ~0.5A typical, ~2A peak |
| 24V → 12V | TP5100 battery charger | 4 | 5 | 0.5 A into the 2S pack while charging |
| 24V → 6.5V buck (MP1584EN #2) | Dispenser servos DSB (x4, one moving at a time) | 0.5 | 20 | 6.5V rail switched on only during a dispense; ≤ 2.5A stall (DS3218 2.2A, MG996R ~2.5A) |
| 24V → 12V | SLD peristaltic pumps (x2) | 0 | 6 | 12V, only during dispense |
| 24V → 12V | SLD solenoid valves (x2) | 0 | 10 | 5W each when energized |
| 24V → 5V buck | LED ring (WS2812B) | 2 | 5 | 16 LEDs at partial brightness |
| 24V direct | Safety relay coil | 0.5 | 1 | Mains disconnect for microwave surface |
| 24V → 12V | Exhaust fans (x2) | 1 | 6 | 12V DC, 120mm, 0.3-0.5A each |
| 5V → 3.3V (on Unified PCB) | STM32G0B1RE | 0.1 | 0.2 | AMS1117 LDO on Unified PCB |
| 5V → 3.3V (on Unified PCB) | HX711, PCA9685, PCF8574, INA219, CAN transceivers | 0.3 | 0.5 | Low-power logic |
| - | Regulator losses | 5 | 10 | Buck + LDO inefficiency |
| **24V PSU Total** | | **~20W** | **~50W** | **Within 76.8W PSU capacity** |
| **System Total (incl. induction)** | | **~620W** | **~1,850W** | **Within 2kW limit** |

---

## 11. Microwave Induction Surface Module

### 11.1 Module Integration

The microwave induction surface is a self-contained commercial module with its own AC power inlet, power electronics, induction coil, under-glass temperature sensor with closed-loop control, and onboard safety circuits. Epicura interfaces with the module exclusively via the isolated CAN port — no high-voltage wiring touches the Unified PCB, and no temperature sensor is needed in Epicura.

```
┌──────────────────────────────────────────────────────────┐
│              Microwave Induction Surface                   │
│                                                            │
│  AC Mains ──► EMI Filter ──► Rectifier ──► Driver ──► Coil │
│                                                            │
│  Internal safety: pot detection, thermal cutoff,           │
│  overcurrent protection; internal PID on surface sensor    │
│                                                            │
│  Exposed CAN Port:                                         │
│    CAN_H ──────────────────┐                               │
│    CAN_L ──────────────────┤                               │
│    GND ────────────────────┤                               │
└────────────────────────────┼───────────────────────────────┘
                             │
                    ┌─────────────────────┐
                    │  Unified PCB        │
                    │ J_CAN_HEAT+120Ω term│
                    │  5 V_ISO (B0505S)   │
                    │  ISO1050DUB #1  #2  │
                    │     │          │    │
                    │  STM32      MCP2518 │
                    │  FDCAN1     FD (SPI)│
                    │  PB8/PB9    RV1106  │
                    │  off-switch setpoint│
                    └─────────────────────┘

System Safety:
  - Module-internal: pot detection, thermal fuse, overcurrent (cannot be overridden)
  - System-level: safety relay on AC mains to module (STM32 GPIO ──► relay)
  - RV1106 sends HEAT_SET_TEMP / HEAT_SET_POWER setpoints (module PID regulates); STM32
    can force HEAT_ON_OFF=0, broadcast E_STOP on the bus, or open the relay on fault/E-stop
```

---

## 12. Ingredient Dispensing System (FID / CID / SLD)

The dispensing system comprises three subsystems. FID and CID share one electrical control block, the Dispenser Servo Block (DSB). See [[03-Ingredient-Dispensing|Ingredient Dispensing System]] for full details.

### 12.1 DSB — FID + CID Servo Wiring

```
  24V Rail ──► MP1584EN #2 (6.5 V, 3 A) ──► P-MOSFET high-side switch ──► 6.5 V DSB rail
                                               ▲                            (1000 µF bulk, 3 A PTC)
                                   PCF8574 #2 P4 (rail enable, I2C1 0x21)

  I2C1 (PB6/PB7) ──► PCA9685 (addr 0x41, on Unified PCB)
                        ├── CH0 ──► J_DSB1 ──► C1  CID carousel index servo, DS3218 270° (4:3 gear-up)
                        ├── CH1 ──► J_DSB2 ──► F1  FID carousel index servo, MG996R (5:3 gear-up)
                        ├── CH2 ──► J_DSB3 ──► F2  FID dose servo, MG996R (canister ¼ tsp measure wheel)
                        └── CH3 ──► J_DSB4 ──► F3  FID steam-gate servo, MG90S (J_DSB4 V+ via D_DSB4 1N4007 ≈ 5.8 V)
  PB4 (GPIO) ──► PCA9685 OE (active-low; held high in boot-safe state and on E-stop)

  I2C1 devices: PCF8574 #2 (0x21), INA219 (0x40), PCA9685 (0x41)

  Note: replaces the P-ASD pneumatics (pump, 6 solenoids, ADS1015, PCF8574 #1) and the
  CID stepper / linear actuator (external driver, DRV8876 #2, J_CID). Freed STM32 pins:
  PA10, PB5, PB11, PC2, PD2 (PA0 and PB6 were reused for VBUS sense and I2C1_SCL on the
  G0B1). Stall detection via INA219 24 V current window.
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
    SCL ◄── PB6 (I2C1_SCL)
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

**Unified PCB On-Board Routing:** All STM32 control signals connect directly to their corresponding driver ICs (PCA9685, TB6612, ISO1050DUB, SN65HVD230, PCF8574 #2, MOSFETs) on the same board. The four DSB servo leads plug into J_DSB1-4 (3-pin JR headers on the switched 6.5 V rail); the SLD harness into J_SLD. No inter-board stacking connector is required. The Luckfox Pico Zero sits in the J_AP slot, which carries 5V power, the SPI0 CS1 lines of the on-board MCP2518FD CAN controller, the UART service link, BOOT0/NRST and the display lines (re-emerging on J_LCD).

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

- I2C1 stays on the Unified PCB (PCA9685, PCF8574 #2, INA219); 4.7k pull-ups near the STM32
- Keep the two CAN buses apart: the regular stir-motor bus (J_CAN_STIR) must not run alongside the isolated heater bus (J_CAN_HEAT) or cross the isolation slot
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
| **MCU** | STM32G0B1RE Nucleo Board (proto) | 1 | $11 | $11 |
| | STM32G0B1RET6 IC (production) | 1 | $3.50 | $3.50 |
| **Display** | 4" ST7796S SPI LCD with FT6336 touch | 1 | $15 | $15 |
| **Camera** | Luckfox IMX415-98 IR-CUT 8 MP camera module (incl. 22-pin FPC) | 1 | $54 | $54 |
| **Sensors** | HX711 breakout board | 2 | $3 | $6 |
| | 2kg load cells (SLD reservoirs) | 2 | $4 | $8 |
| | Reed switch (pot detect — backup/optional) | 1 | $1 | $1 |
| **Battery** | 2S1P 18650 Li-ion pack, 2,600 mAh, PCM + NTC | 1 | $12 | $12 |
| **Actuators** | 24V CAN servo stirring motor (CyberGear/RobStride-class) | 1 | $45 | $45 |
| | DS3218 270° servo (DSB: C1 CID index) | 1 | $10 | $10 |
| | MG996R servos (DSB: F1 FID index, F2 dose) | 2 | $4 | $8 |
| | MG90S micro servo (DSB: F3 steam gate) + 1N4007 | 1 | $2.50 | $2.50 |
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
| | ISO1050DUB isolated CAN transceivers (STM32 node + RV1106 node) | 2 | $3.50 | $7 |
| | MCP2518FD CAN controller + 40 MHz crystal (RV1106 node) | 1 | $3 | $3 |
| | SN65HVD230 CAN transceiver (stir-motor port) | 1 | $0.90 | $0.90 |
| | TP5100 2S charger + inductor + sense resistor | 1 | $1 | $1 |
| | Passive components (R, C, etc.) | Lot | - | $20 |
| | Unified PCB (4-layer, 1 board) | 1 | $40 | $40 |
| | Wiring, connectors, FFC cables | Lot | - | $25 |
| **Enclosure** | 3D-printed enclosure (prototype) | 1 | $80 | $80 |
| | Pot (off-shelf induction-compatible) | 1 | $25 | $25 |
| | Gantry hardware (rods, brackets) | Lot | - | $30 |

**Estimated Prototype BOM Total: $620 - $720 USD**

*Note: Production BOM would be lower per unit at volume. Prototype uses Nucleo dev board that would be replaced with bare STM32G0B1RET6 on the Unified PCB. The Luckfox Pico Zero is used as-is (off-the-shelf module, no carrier board) in both prototype and production.*

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
- [ ] CAN bus up on `can0` (MCP2518FD on SPI0 CS1, 500 kbps); commands to the STM32 and 20 Hz TELEMETRY exchanged while the LCD is refreshing
- [ ] STM32 firmware load over USART2 via BOOT0/NRST from the RV1106
- [ ] Camera captures 1280x720 @ 30fps frames via MIPI CSI (IMX415-98, ISP tuning loaded)
- [ ] NPU runs the INT8 stage classifier in <20 ms
- [ ] Display renders LVGL UI via SPI0 (fbtft, full-frame refresh ~50 ms)
- [ ] Touch input (FT6336, I2C3) registers on all screen areas
- [ ] LED ring responds to SET_LED (OFF/CAPTURE/NIGHT) over CAN
- [ ] WiFi connects to AP, achieves >10 Mbps throughput
- [ ] BLE advertises and pairs with test phone
- [ ] eMMC read/write speed adequate (>50 MB/s sequential)

### 17.3 Microwave Induction Surface
- [ ] Module responds to CAN queries (HEAT_QUERY → HEAT_STATUS)
- [ ] CAN power level commands correctly modulate heating
- [ ] Module heats water from 20C to 100C within 5 minutes (1.5L)
- [ ] Module holds a HEAT_SET_TEMP setpoint within +/-5C (its own PID); RV1106 keep-alive at 2 Hz never drops out while the LCD refreshes
- [ ] All four power profiles (sear/boil/simmer/warm) verified
- [ ] Module-internal pot detection prevents heating without pot
- [ ] Safety relay disconnects AC to module on E-stop or fault
- [ ] STM32 HEAT_ON_OFF=0 and E_STOP broadcast stop heating within 500ms; module drops to 0 power 1 s after the HEAT_SET_TEMP keep-alive stops

### 17.4 Servo System
- [ ] Main arm (24V CAN servo) rotates full 360 degrees smoothly; motor enumerates on FDCAN2 at 1 Mbps
- [ ] Stirring speed controllable from 10-60 RPM; reported RPM within ±5 of commanded
- [ ] Motor stops within 500 ms when FDCAN2 traffic stops; 0 V on J_STIR_PWR with Q_STIR off
- [ ] Arm torque sufficient to stir thick curry/dal
- [ ] Each DSB servo (x4) reaches commanded angle within ±2° via PCA9685
- [ ] DSB rail switches off after each dispense (no idle jitter or buzz)
- [ ] PCA9685 OE high on E-stop leaves all four servos limp

### 17.5 Sensors
- [ ] Camera: white balance calibrated, image sharp across full pot FOV
- [ ] Module surface_temp (HEAT_STATUS) tracks a thermocouple on the pot bottom within +/-5C at 100C
- [ ] Battery: pack charges to 8.4 V at ~0.5 A; CHRG/STDBY read on PCF8574 #2; PA4 voltage within 2 %
- [ ] Battery: pulling the 24 V input keeps the Pico Zero, LCD and STM32 running (no reboot); POWER_FAIL reported; LED ring off
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

- **Galvanic Isolation:** The microwave induction surface is a self-contained AC module — no mains voltage reaches the Unified PCB. The two ISO1050DUB isolated CAN transceivers behind J_CAN_HEAT provide 5 kV RMS galvanic isolation between the heater CAN bus and the logic. The stir-motor CAN bus (J_CAN_STIR) is not isolated: the motor shares the 24 V PSU ground. PSU provides transformer-isolated DC outputs.
- **Battery Safety:** 2S Li-ion pack with per-cell protection (PCM), NTC-gated charging (0–45 °C), mounted in the cool zone away from the induction module; IEC 62133-2 / IS 16046 cells.
- **Earth Bonding:** Metal enclosure parts connected to AC earth via IEC C14 inlet. Chassis ground bonded to PSU earth.
- **Fuse Protection:** 10A ceramic fuse in IEC C14 inlet. Self-resetting PTC fuse on 5V rail (3A).

### 18.2 Thermal Safety

- **Module Thermal:** Microwave surface has internal thermal cutoff. Module reports coil temperature via CAN status.
- **Surface Over-Temperature:** The module's own sensor reports surface temperature in HEAT_STATUS. If >270C (beyond any recipe requirement), the STM32 sends the CAN off command and opens the safety relay, independently of the module's internal cut-off.
- **Enclosure Thermal:** Exhaust fan provides ventilation. Module reports internal temp via CAN for enclosure monitoring.

### 18.3 Mechanical Safety

- **E-Stop Button:** Red mushroom-head button on front panel. Normally-closed contact wired to STM32 interrupt AND safety relay. Pressing E-stop: (1) STM32 sends HEAT_ON_OFF=0 and broadcasts E_STOP on the isolated CAN bus, (2) relay disconnects AC to microwave surface, (3) stir motor disabled on FDCAN2 and its 24 V removed (Q_STIR), DSB servos limp.
- **Pot Detection Interlock:** Handled internally by microwave surface module. Module will not heat without compatible pot detected. Status reported via CAN.
- **Pinch Protection:** Arm mechanism has limited torque (current limit set in the CAN servo, reported current monitored by the STM32). Arm speed limited in firmware to prevent splash/injury.

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
| 8.0 | 2026-11-04 | Manas Pradhan | Single Unified PCB hosts the Luckfox Pico Zero in a slot (J_AP, replaces the J_CM5 header; display re-emerges on J_LCD), the STM32 and the CID/FID/SLD drivers; two CAN ports: isolated J_CAN_HEAT (FDCAN1 + RV1106 MCP2518FD) to the cooking surface and regular J_CAN_STIR (FDCAN2 PB12/PB13, SN65HVD230, 1 Mbps) to a 24 V CAN servo stirring motor with switched 24 V (Q_STIR, J_STIR_PWR) — PWM/EN/DIR on PA8/PA4/PA5 retired; MLX90614 IR thermometer dropped (module runs its own temperature loop, HEAT_SET_TEMP 0x100 / HEAT_SET_POWER 0x103, surface_temp in HEAT_STATUS); external 12 V UPS and single-cell micro-UPS replaced by a 2S Li-ion pack (J_BAT, TP5100 charger, VSYS diode-OR feeding the 5 V buck); §7 rewritten for the motor CAN port, block diagram, component list, pin allocation, power, induction, BOM, checklist and safety sections updated |
| 8.2 | 2026-11-04 | Manas Pradhan | DSB servos sized per axis: DS3218 270° on C1 only, MG996R on F1 and F2, MG90S on F3 with D_DSB4 (1N4007) dropping the J_DSB4 V+ to ≈ 5.8 V; F1 gear-up 5:3; component list, block diagram, §12.1 wiring, power budget note and BOM (servos $40 → $20.50) updated |
| 8.1 | 2026-11-04 | Manas Pradhan | MCU changed from STM32G474RE to STM32G0B1RET6 (Cortex-M0+ @ 64 MHz, 2x FDCAN; no control loop left on the MCU so no FPU needed; ~$4.50 cheaper per unit, Nucleo $11): §5.1 rewritten; pin moves for the G0 alternate-function map — I2C1_SCL PA15 → PB6, VBUS detect PC0 → PA0, battery sense PC1 → PA4, buzzer PC7/TIM8_CH2 → PA8/TIM1_CH1, FDCAN AF9 → AF3, BOOT0 on PA14 (nBOOT_SEL); NUCLEO-G0B1RE (MB1360) note; power budget and BOM ($620-720) updated |
| 7.0 | 2026-11-04 | Manas Pradhan | Isolated CAN bus now has three nodes: RV1106 (MCP2518FD on SPI0 CS1 + ISO1050DUB #2 on the Unified PCB, SocketCAN), STM32 (FDCAN1 + ISO1050DUB #1) and the induction surface MCU; it carries host commands and telemetry (UART2/USART2 demoted to a service link for flashing/debug); temperature PID moves to the RV1106, which commands HEAT_SET_POWER directly while the STM32 keeps the off-switch and relay; §9 rewritten, block diagram, component list, header pins, STM32 pin blocks, induction section, BOM and checklist updated |
