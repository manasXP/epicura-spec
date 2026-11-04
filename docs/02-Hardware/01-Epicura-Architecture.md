---
created: 2026-02-15
modified: 2026-11-04
version: 8.5
status: Draft
---

# Epicura Hardware Architecture & Wiring Diagrams

## 1. Overview

This document provides the comprehensive hardware architecture, wiring diagrams, and interface specifications for the Epicura autonomous kitchen robot. The system uses a dual-processor architecture: a Rockchip RV1106G3 (Luckfox Pico Zero) running Buildroot Linux for AI/vision/UI/dispensing, and an STM32G0B1 microcontroller running FreeRTOS for the stirring motor, exhaust fans and safety. There is no IR thermometer: the cooking surface runs its own temperature loop and reports its temperature over CAN.

Epicura is physically **three units** with two boards:

| Unit | Short | Mains? | Contents |
|------|-------|--------|----------|
| **Cooking Surface** | CS | Yes (IEC C14 inlet, fuse, EMI filter) | Donor Philips OneChef NX5300/00 body (heating plate, controller with own AC + CAN, 6 L non-stick inner pot, glass lid; air-fryer lid removed — the DU seats in its place), Mean Well LRS-75-24, **Cooking Surface Controller PCB (CSC, STM32G0B1RE)**, safety relay, E-stop button (front), 2× exhaust fans + filter cartridge (rear), two rear pillars that carry the stirring unit and the dock block |
| **Stirring Unit** | SU | No — fed 24 V by the CS | Gantry bridge between the rear pillars over the pot: 24 V CAN servo stir motor, vertical shaft, paddle, fume hood. One port **J_SU** at the pillar; harness inside the right pillar to the CSC |
| **Dispensing Unit** | DU | No — **battery is the primary supply** | **Unified PCB v4.0** (Pico Zero in J_AP, 2S Li-ion pack, dispenser drivers, RV1106 CAN node), 4" LCD on the front face (tilted 15–30°), IMX415-98 camera + white LED ring on the underside looking straight down into the pot, FID carousel (rear) + CID carousel (front), SLD oil + water reservoirs (sides) with pumps, solenoids, load cells and nozzles through the underside, buzzer. Dock pads on the underside over the left pillar |

Only one cable exists between units (CS → SU, inside the right pillar). The DU lifts straight off with no cable: it docks onto the CS left pillar through an 8-contact magnetic pogo connector (**J_DOCK**) that carries charge (24 V) and the isolated CAN bus. The DU lifts off to load ingredients and to clean individual coarse slots between sessions; on a mains outage the DU (the brain) keeps running on its battery and the session resumes when mains returns. Footprint 500 × 400 mm; CS ≈ 110 mm high, DU ≈ 130 mm high on top, overall ≈ 350 mm (to be confirmed); DU mass target ≤ 4 kg fully loaded (two-hand lift); camera-to-pot-rim distance 20–30 cm.

---

## 2. System Block Diagram

```
  ┌──────────────────────────── DISPENSING UNIT (DU) — lifts off, battery primary ─────────────────────────────┐
  │                                                                                                              │
  │   Unified PCB v4.0 (160 × 90 mm)                                                                             │
  │   VSYS = DOCK_24V ⊕ BAT+ (SS54) → TPS54531 → 5V_MAIN → AMS1117 → 3.3 V;  VSYS → MP1584EN #2 → 6V_DSP (switched)│
  │   DOCK_24V → MP1584EN #1 → 12 V → TP5100 (1.0 A) → 2S Li-ion pack (J_BAT, INA219 #2)                          │
  │                                                                                                              │
  │   ┌───────────────────────┐   I2C3 ┌──────────────────────────────────────────────────────────────────┐    │
  │   │  Luckfox Pico Zero    │──────►│ PCA9685 0x41 → DSB servos ×4 (FID 3 + CID 1) on 6V_DSP             │    │
  │   │  RV1106G3 (Buildroot) │        │ PCF8574 #2 0x21 → solenoids ×2, pump DIR, 6V_DSP enable, CHRG/STDBY │    │
  │   │                       │        │ TCA9543A 0x71 → NAU7802 ×2 0x2A (SLD load cells)                   │    │
  │   │  - Recipe Engine      │        │ INA219 #1 0x40 (6V_DSP current) · INA219 #2 0x44 (battery)         │    │
  │   │  - CV Inference (NPU) │        │ FT6336 touch 0x38                                                  │    │
  │   │  - UI Rendering (LVGL)│   PWM  └──────────────────────────────────────────────────────────────────┘    │
  │   │  - Dispensing thread  │──────► TB6612 pumps ×2 (6 V) · white LED ring (Q_LED) · buzzer                  │
  │   │  - Cloud/WiFi/BT/OTA  │   SPI0 ┌─────────────┐ ┌────────────────────────────────────┐                   │
  │   │  - Heater setpoints   │──────►│ 4" ST7796S  │ │ MCP2518FD + ISO1050DUB #2 (CAN node)│                   │
  │   │  - Dock/battery mon.  │        │ 480×320     │ │ bus side powered from dock 5V_ISO   │                   │
  │   │  CSI-2 → IMX415 8 MP  │        └─────────────┘ └──────────────────┬─────────────────┘                   │
  │   │  (underside, down)    │   GPIO ◄── DOCK_SENSE_A, DOCK_PWR_OK      │                                     │
  │   └───────────────────────┘                                            │                                     │
  │   WiFi 6 / BLE 5.2 · eMMC 8 GB + microSD                               │                                     │
  │                                                     J_DOCK pads (8) ───┼──── DOCK_24V, GND, DOCK_SENSE_A/B  │
  └────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┘
                              8-pin magnetic pogo dock on the CS left pillar│ (CAN_H, CAN_L, GND_ISO, 5V_ISO)
  ┌────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┐
  │  COOKING SURFACE (CS) — mains                                           │                                    │
  │                                                                         │                                    │
  │  AC Mains 220-240 V ──► IEC C14 + fuse + EMI filter ──┬──► Mean Well LRS-75-24 (24 V / 3.2 A)               │
  │                                                       │                 │                                    │
  │                                                       └──► safety relay ──► Electric Heating Unit            │
  │                                                                         │   (own AC, own PID, CAN node HEAT) │
  │  ┌──────────────── Cooking Surface Controller (CSC, ~100 × 70 mm) ──────┼──────────────────────────────┐     │
  │  │  J_24V_IN ── MP1584EN #1 → 12 V (fans, relay coil) · MP1584EN #2 → 5 V → 3.3 V · B0505S → 5V_ISO   │     │
  │  │                                                                      │                             │     │
  │  │  ┌─────────────────────────┐   FDCAN1 ──► ISO1050DUB #1 ──┬── J_CAN_HEAT (120 Ω) ──► heating unit    │     │
  │  │  │  STM32G0B1RE (FreeRTOS) │                              └── J_DOCK pins 3–6 ──► DU (stub ≤ 30 cm)   │     │
  │  │  │  - Stir motor (FDCAN2)  │   FDCAN2 ──► SN65HVD230 ──► J_CAN_STIR ─┐                               │     │
  │  │  │  - Safety monitor       │   PB4 ──► Q_STIR (24 V) ──► J_STIR_PWR ──┤ harness in the right pillar   │     │
  │  │  │  - Thermal / fans       │   PB5 ──► Q_DOCK (24 V) ──► J_DOCK pin 1 │                               │     │
  │  │  │  - CAN comms (FDCAN1)   │   PB0 ──► relay · PB2 ◄── E-stop · PB3 ◄── DOCK_SENSE_B · PA6/PB10 ──► fans│     │
  │  │  └─────────────────────────┘   J_SWD · J_USB (DFU, bench) · J_DBG      │                               │     │
  │  └───────────────────────────────────────────────────────────────────────┼───────────────────────────────┘     │
  │  E-stop button (front) · 2× 120 mm exhaust fans + filter (rear)           │                                    │
  └───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┘
                                                                              │ J_SU (Micro-Fit 3.0, 5-way) — the only inter-unit cable
  ┌───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┐
  │  STIRRING UNIT (SU) — gantry between the rear pillars                      ▼                                    │
  │  24V_STIR + CAN (1 Mbps) ──► 24 V CAN servo stir motor ──► vertical shaft ──► paddle · fume hood                │
  └────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Main Component List

| Component | Part Number | Interface | Connected To | Purpose |
|-----------|-------------|-----------|--------------|---------|
| Compute Module | Luckfox Pico Zero (RV1106G3) | 40-pin header / CSI / USB-C | Unified PCB v4.0 slot J_AP (2x20 socket + 4 standoffs), in the DU | AI/vision (NPU), recipe engine, heater setpoints, dispensing, LVGL UI, networking, dock/battery monitoring |
| Unified PCB v4.0 | 160 × 90 mm, 4-layer | - | Dispensing Unit | Hosts the Pico Zero, the RV1106 CAN node, the battery charger, the dispenser drivers and the dock pads |
| CAN Controller (RV1106 node) | MCP2518FD (SPI, 40 MHz crystal) + ISO1050DUB #2 | SPI0 CS1 + INT GPIO | Unified PCB, via the 40-pin header; bus side powered from dock 5V_ISO | Puts the RV1106 on the isolated CAN bus (SocketCAN `can0`) |
| Cooking Surface Controller (CSC) | ~100 × 70 mm, 4-layer PCB with STM32G0B1RE (LQFP-64) | - | Cooking Surface base, beside the LRS-75-24 | Real-time control: stirring motor, exhaust fans, relay, E-stop, dock power switch; isolated CAN node (FDCAN1) and stir-motor CAN master (FDCAN2) |
| Dock Connector | 8-contact magnetic pogo pair, 2.54 mm pitch, 2 A per pin (J_DOCK) | DOCK_24V, GND, CAN_H/L, GND_ISO, 5V_ISO, DOCK_SENSE_A/B | Spring pins in a keyed recess on the CS left pillar (harness to the CSC); gold pads on the DU underside (Unified PCB) | Charge + isolated CAN between the CS and the DU; dead when the DU is lifted |
| Camera Module | IMX415-98 IR-CUT (8 MP) | MIPI CSI-2 (4-lane FPC) | Pico Zero CSI connector; DU underside, centred over the pot behind a sealed borosilicate window | Overhead food monitoring, CV inference |
| Stirring Motor | 24V integrated BLDC servo with CAN (CyberGear/RobStride-class, model TBD) | CAN 2.0B 1 Mbps (regular port) + switched 24V | STM32 FDCAN2 (PB12/PB13) via SN65HVD230 → J_CAN_STIR; 24V via Q_STIR → J_STIR_PWR; both bundled to J_SU on the SU pillar | Stirring arm rotation with encoder feedback |
| Stir-Motor CAN Transceiver | SN65HVD230DR | FDCAN2 | CSC, non-isolated | Regular CAN port to the stirring motor |
| Dispenser Servos (DSB) | DS3218 270° (C1), MG996R (F1, F2), MG90S (F3) | 50 Hz PWM via PCA9685 | PCA9685 CH0-CH3 → J_DSB1-4, all on the switched 6.0 V rail (6V_DSP) | CID carousel index (C1); FID carousel index, dose, steam gate (F1-F3) |
| PCA9685 Servo Driver (DSB) | PCA9685PW | I2C | RV1106 I2C3 addr 0x41, OE on an RV1106 GPIO | Single PWM control block for FID + CID servos |
| SLD Load-Cell ADCs | NAU7802 24-bit ×2 behind TCA9543A I2C mux | I2C | RV1106 I2C3: TCA9543A 0x71, one NAU7802 (0x2A) per mux channel | Oil and water reservoir weight (replaces HX711 bit-bang) |
| Current Monitors | INA219 ×2 | I2C | RV1106 I2C3: #1 0x40 (6V_DSP rail shunt), #2 0x44 (10 mΩ in the BAT+ path) | Servo stall detection; battery voltage, current and state of charge |
| SLD Peristaltic Pumps | 6V DC (x2) via TB6612 (VM on 6V_DSP) | PWM (RV1106) + DIR (PCF8574 #2 P3/P5) | Unified PCB | Oil and water dispensing |
| SLD Solenoid Valves | 6V NC (x2) | I2C (GPIO expander) | PCF8574 #2 P0/P1 (0x21) via IRLML6344 | Liquid drip prevention |
| Exhaust Fans | 2× 120mm 12V DC brushless | PWM (25kHz) | STM32 PA6, PB10 via MOSFET → J_FAN on the CSC | Fume extraction, independent control; rear of the CS with the filter cartridge |
| Piezo Buzzer | 5V active | PWM | RV1106 PWM via 2N7002 → J_BUZZER (Unified PCB) | Audio alerts |
| USB-C Receptacle | Mid-mount 16-pin (J_USB on the CSC) | USB 2.0 FS | STM32 PA11/PA12 (native USB) | DFU programming, CDC serial debug (bench only) |
| Li-Ion Battery | 2S1P 18650 pack, 7.4V, 2,600 mAh, with PCM + NTC (JST-XH 3-pin, J_BAT) | Analog | TP5100 charger (1.0 A) + VSYS diode-OR on the Unified PCB; monitored by INA219 #2 | **Primary supply of the DU**: ≈ 3 W lifted-unit load → > 5 h; docked, the DU draws from DOCK_24V and the pack does not discharge |
| Electric Heating Unit | Philips OneChef NX5300/00-class unit (donor body + 6 L non-stick pot) w/ OEM CAN control board and internal temperature control, 1,300 W (assumed; base plate of the 2,280 W nameplate) | CAN 2.0B (500kbps) | Isolated CAN port J_CAN_HEAT on the CSC (STM32 FDCAN1); RV1106 joins the same bus over the dock | Self-contained resistive heating plate with internal relay/triac power stage, spring-loaded centre sensor, PID and safety; setpoints from the RV1106, forced off by the STM32 |
| 4" Touchscreen | 4" 480x320 IPS, ST7796S + FT6336 | SPI (LCD) + I2C (touch) | RV1106 SPI0 + I2C3; DU front face, tilted 15–30° | User interface display |
| PSU Module | Mean Well LRS-75-24 | AC-DC 24V | AC mains input, in the CS | 24V DC to the CSC (J_24V_IN); derives 12 V / 5 V / 3.3 V for the CS, 24V_STIR for the SU and DOCK_24V for the DU |
| Safety Relay | Omron G5V-2 or equiv. (12 V coil) | GPIO (via MOSFET) | STM32 PB0 → Q_RLY → J_SAFE pin 1 on the CSC | Heater mains disconnect |
| LED Ring | White LED ring, 12–16 LEDs, 5000 K, CRI ≥ 90 | PWM (1 kHz) | RV1106 PWM → Q_LED (IRLML6344 low-side) → J_LED (5V_MAIN / LED_RET) | Pot illumination for camera, on the DU underside around the lens |
| E-Stop Button | Normally-closed mushroom, CS front | GPIO (interrupt) | STM32 PB2 via J_SAFE pin 3 on the CSC | Emergency power cutoff |
| Pot Detection | Internal to the heating unit (spring-loaded centre sensor) | CAN status | Unit-reported via CAN (`pot_detected` in HEAT_STATUS; reed switch backup on STM32 PB1 via J_SAFE pin 2, optional) | Detect pot presence (unit-internal) |

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
| Video Output | None on-board; 4" SPI LCD on SPI0 (see Section 9) |
| Camera | 1x 4-lane MIPI CSI-2 (FPC connector) |
| Networking | On-board 2.4 GHz Wi-Fi 6, Bluetooth 5.2 LE; on-board antenna + external antenna connector. No Ethernet |
| USB | 1x USB-C (power + flashing) |
| Header | 40-pin RPi-style, 28 GPIO, 3.3V logic |
| Other | On-board mic, MX1.25 speaker header, RTC battery header, user LED, RESET/BOOT buttons |
| Power / Thermal | ~1 W class, no heatsink; ambient -20 to +85C, Tj max 125C |
| Operating System | Buildroot Linux (Luckfox SDK, kernel 5.10), read-only squashfs rootfs |
| Form Factor | 65 x 30 mm, four 3.0 mm mounting holes |

### 4.2 Board Integration (Slot on the Unified PCB)

The Pico Zero is a complete single-board module: no carrier board is needed. It seats pin-down into the Unified PCB v4.0's slot **J_AP** (2x20 socket, four M2.5 standoffs on the module's 3.0 mm holes) in the Dispensing Unit for 5V power and all logic signals. The camera attaches to the module's CSI connector directly; the display's SPI0/I2C3 lines are routed through the PCB to a 14-pin break-out (J_LCD). There is no link of any kind to the STM32 other than the isolated CAN bus over the dock: the former UART service link and BOOT0/NRST lines are gone (the STM32 is in a different unit).

```
┌───────────────────────────────────────────────────────────────┐
│              Luckfox Pico Zero (RV1106G3)                     │
│                                                               │
│  MIPI CSI (FPC) ──► IMX415 camera module (4-lane, underside)  │
│  SPI0 ──────────► 4" ST7796S LCD (fbtft, 50 MHz, DMA) on CS0  │
│                   MCP2518FD CAN controller on CS1 (+ INT)     │
│  I2C3 ──────────► FT6336 touch, PCF8574 #2, PCA9685, INA219   │
│                   ×2, TCA9543A → NAU7802 ×2 (single DU bus)   │
│  PWM ───────────► LCD backlight (PWM10), pump oil, pump       │
│                   water, white LED ring, buzzer               │
│  GPIO ──────────► PCA9685 OE; ◄── DOCK_SENSE_A, DOCK_PWR_OK   │
│  UART0 ─────────► Debug console                               │
│  USB-C ─────────► Flashing (rkdevtool) / alternate 5V input   │
│  Wi-Fi 6 / BT 5.2 ► On-board module, antenna connector        │
│  40-pin header ──► Unified PCB slot J_AP (5V in, all signals  │
│                    above; LCD lines re-emerge on J_LCD)       │
│                                                               │
│  Power Input: 5V_MAIN / 1A from the Unified PCB (J_AP pins   │
│               2, 4); VSYS = DOCK_24V ⊕ 2S pack (diode-OR),    │
│               so the module never sees a gap when lifted      │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 RV1106 Header Pin Allocation

| Header pin | Function | Direction | Notes |
|------------|----------|-----------|-------|
| SPI0_CS1 (GPIO 58) | MCP2518FD chip select | Output | CAN controller on the Unified PCB, ≤ 20 MHz; shares MOSI/MISO/CLK (pins 19/21/23) with the LCD |
| GPIO (spare) | MCP2518FD INT | Input | Active-low RX/TX FIFO interrupt; pin fixed at PCB layout |
| 19 (SPI0_MOSI) | LCD MOSI | Output | 50 MHz, fbtft with DMA |
| 21 (SPI0_MISO) | LCD MISO | Input | Reserved (fbtft is write-only) |
| 23 (SPI0_CLK) | LCD clock | Output | 50 MHz |
| 24 (SPI0_CS0) | LCD chip select | Output | Active-low |
| 22 (GPIO) | LCD DC (data/command) | Output | |
| 26 (GPIO) | LCD RST | Output | |
| 12 (PWM10) | LCD backlight PWM | Output | Dimmable |
| 16 (I2C3_SDA, M0) | I2C3 SDA — single I2C bus of the DU | Bidirectional | 400 kHz, 4.7k pull-ups to 3.3 V. Devices: FT6336 touch 0x38 (via J_LCD), PCF8574 #2 0x21, NAU7802 ×2 0x2A behind TCA9543A 0x71, INA219 #1 0x40, INA219 #2 0x44, PCA9685 0x41 (I2C1 stays spare if layout prefers separation) |
| 18 (I2C3_SCL, M0) | I2C3 SCL | Bidirectional | as above |
| 36 (GPIO) | Touch INT | Input | Active-low, evdev |
| GPIO (fixed at layout) | PCA9685 OE | Output | Active-low; 10k pull-up → servos off at boot and on soft stop |
| GPIO (fixed at layout) | DOCK_SENSE_A | Input | 10k pull-up; low = docked (dock pin 7 tied to GND on the CS); edge-triggered |
| GPIO (fixed at layout) | DOCK_PWR_OK | Input | Active-low; 100k/10k divider on DOCK_24V → 2N7002; low = 24 V present on the dock |
| PWM (fixed at layout) | Pump oil (TB6612 PWMA) | Output | `pwm-rockchip` |
| PWM (fixed at layout) | Pump water (TB6612 PWMB) | Output | `pwm-rockchip` |
| PWM (fixed at layout) | White LED ring (Q_LED) | Output | 1 kHz; OFF 0 %, CAPTURE 100 %, NIGHT 30 % |
| PWM (fixed at layout) | Buzzer (2N7002) | Output | Alert patterns |
| 35 / 37 (UART0, M0) | Debug console TX / RX | - | Luckfox default |
| CSI (FPC) | Camera data lanes | Input | 4-lane MIPI, IMX415-98 |
| 8 / 10 (UART2), GPIO 32, GPIO 38 | Freed | - | Former UART2 service link to the STM32 USART2 and BOOT0 / NRST lines — gone, the STM32 is on the CSC in a different unit (STM32 updates go over CAN, see §10.2) |
| Spare | UART3, UART4, I2C1, I2C2, PWM | - | Available |

Linux kernel drivers (all mainline in 5.10): `pwm-pca9685`, `gpio-pcf857x`, `ina2xx` (hwmon), `i2c-mux-pca954x`, `nau7802` (IIO), `pwm-rockchip`, `mcp251xfd`.

---

## 5. STM32 Cooking Surface Controller (CSC)

### 5.1 STM32G0B1RE Specifications

The STM32 now lives on its own board, the **Cooking Surface Controller (CSC) v1.0**: ~100 × 70 mm, 4-layer (isolation slot), in the Cooking Surface base beside the LRS-75-24. It keeps only what belongs to the cooking surface: the stir-motor CAN master, the isolated CAN node, the safety relay, the E-stop, the exhaust fans and the dock power switch. Dispensing, sensing, the LED ring and the buzzer moved to the RV1106 on the Unified PCB in the Dispensing Unit. Its ten connectors are J_24V_IN, J_CAN_HEAT, J_CAN_STIR, J_STIR_PWR, J_DOCK, J_FAN, J_SAFE, J_DBG, J_SWD, J_USB. FreeRTOS tasks: Motor Control 50 Hz (FDCAN2 stir servo), Safety Monitor 10 Hz, CAN Comms 20 Hz (FDCAN1), Thermal/Fan 1 Hz; the Dispense and Sensor Poll tasks are removed.

The MCU was downsized from the STM32G474RE on 2026-11-04: with no control loop on the MCU (the heating unit regulates itself, the stirring motor is a CAN servo) nothing needs an FPU or 170 MHz. The G0B1 is the cheapest ST part with two FDCAN controllers and keeps the same HAL, FreeRTOS, USB DFU bootloader and X-CUBE-CLASSB safety library. Pin map and rationale: [[../03-Software/05-MCU-Functional-Specification|MCU Functional Specification]].

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
| CAN | 2x FDCAN (FDCAN1 isolated host/heater bus over J_CAN_HEAT + the dock, FDCAN2 stir-motor bus) |
| USB | USB 2.0 FS (PA11/PA12), J_USB on the CSC — DFU + CDC, bench only |
| GPIO | Up to 60 I/O pins (LQFP-64) |
| Safety | IWDG (LSI), WWDG, SRAM parity, flash ECC, CRC unit; X-CUBE-CLASSB (IEC 60730-1 Annex H Class B) |
| Clock | 8 MHz HSE |
| Supply | 3.3V (CSC AMS1117-3.3 from the 5 V buck; 5V_USB OR'd in on the bench) |
| RTOS | FreeRTOS |

### 5.2 STM32 Pin Allocation

```
STM32G0B1RE (LQFP-64) on the Cooking Surface Controller (CSC)
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌─── FDCAN1: Isolated 3-node bus ───┐                       │
│  │  PB8  (FDCAN1_RX) ◄── ISO1050DUB #1 on-board (CAN_RX)     │
│  │  PB9  (FDCAN1_TX) ──► ISO1050DUB #1 on-board (CAN_TX)     │
│  │  B0505S-1WR3 makes 5V_ISO / GND_ISO (from 5 V); isolated  │
│  │  side: R_TERM1 120 Ω, PESD1CAN, J_CAN_HEAT (JST-XH 4-pin: │
│  │  CAN_H, CAN_L, GND_ISO, 5V_ISO) to the heating unit       │
│  │  and J_DOCK pins 3–6 to the pillar dock block (RV1106).   │
│  │  500 kbps; nodes: RV1106 (MCP2518FD, over the dock),      │
│  │  STM32, heating unit MCU. Host commands + telemetry       │
│  │  + the CAN bootloader (0x7E0/0x7E8) ride this bus.        │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── FDCAN2: Regular bus to the stirring motor ───┐         │
│  │  PB12 (FDCAN2_RX) ◄── SN65HVD230 (non-isolated)           │
│  │  PB13 (FDCAN2_TX) ──► SN65HVD230 ──► J_CAN_STIR (JST-XH 3)│
│  │  1 Mbps; velocity/position commands at 50 Hz, feedback;   │
│  │  120 Ω at J_CAN_STIR + in the motor                       │
│  │  PB4  (GPIO)      ──► 2N7002 ──► Q_STIR (AO4407A, F_STIR  │
│  │                       5 A) ──► J_STIR_PWR (XT30)          │
│  │  Both bundled into the stirring-unit harness → J_SU       │
│  └─────────────────────────────────────┘                     │
│                                                              │
│  ┌─── Dock (DU charge + presence) ───┐                       │
│  │  PB3  (GPIO)      ◄── DOCK_SENSE_B (10k pull-up; low =    │
│  │                       DU present, dock pin 8)             │
│  │  PB5  (GPIO)      ──► 2N7002 ──► Q_DOCK (AO4407A) ──►     │
│  │                       F_DOCK 2 A ──► J_DOCK pin 1         │
│  │                       (DOCK_24V); only while PB3 is low   │
│  │  DOCK_SENSE_B open → safe hold (HEAT_ON_OFF = 0, stir     │
│  │  disable, Q_STIR off, Q_DOCK off, STATUS DU_UNDOCKED)     │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── Exhaust Fans (2x 120mm) ────┐                          │
│  │  PA6  (TIM3_CH1)  ──► Exhaust Fan 1 PWM (25 kHz, HW PWM)  │
│  │  PB10 (GPIO)      ──► Exhaust Fan 2 PWM (25 kHz, SW PWM)  │
│  │  IRLML6344 + SS14 low-side ──► J_FAN (12 V)               │
│  │  Independent control for optimal airflow                  │
│  │  Note: PB10 uses software PWM (TIM2_CH3 conflicts with PA2)
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── GPIO: Safety & Control ─────┐                          │
│  │  PB0  (GPIO)      ──► Q_RLY (2N7002) ──► Omron G5V-2 coil │
│  │                       (12 V) ──► J_SAFE 1 (AC to module;  │
│  │                       NC wiring = de-energised is open)   │
│  │  PB1  (GPIO)      ◄── Pot reed switch, J_SAFE 2 (optional)│
│  │  PB2  (GPIO)      ◄── E-Stop NC button, J_SAFE 3 (EXTI,   │
│  │                       10k pull-up + 100 nF)               │
│  │  PC7  (GPIO)      ──► Status LED (on-board)               │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── USB: Programming & Debug (Native USB 2.0 FS) ───┐     │
│  │  PA11 (USB_DM)    ◄─► USB-C D- (22R + USBLC6 ESD)        │
│  │  PA12 (USB_DP)    ◄─► USB-C D+ (22R + USBLC6 ESD)        │
│  │  PA0  (ADC_IN0)   ◄── VBUS detect (100k/100k divider)    │
│  │  Modes: DFU bootloader (SW_BOOT + SW_RST), USB CDC serial │
│  │  5V_USB OR'd into 3.3 V — bench only, 500mA polyfuse      │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─── USART2: Debug console (no host link) ───┐              │
│  │  PA2  (USART2_TX), PA3 (USART2_RX) ──► J_DBG 3-pin header │
│  │  The RV1106 has no UART to this board any more; firmware  │
│  │  updates arrive over the CAN bootloader (§10.2)           │
│  └─────────────────────────────────┘                         │
│                                                              │
│  Dropped vs the Unified PCB STM32 side: PCF8574 (all outputs │
│  are direct GPIO), INA219 (the CAN servo reports its own     │
│  current), PA1 24 V comparator, PA4 battery ADC, PCA9685 /   │
│  TB6612 / HX711 / solenoids / buzzer / LED ring (on the DU), │
│  UART service link to the RV1106.                            │
│  Free pins: PA1, PA4, PA5, PA7, PA8, PA9, PA10, PA15, PB6/PB7 │
│  (I2C1 pads unpopulated), PB11, PB14, PB15, PC0–PC6,         │
│  PC8–PC12, PD2.                                              │
│                                                              │
│  Power: 3.3V from the CSC LDO (24 V → 5 V → 3.3 V), 8 MHz HSE │
│  Debug: SWD (PA13/PA14) via J_SWD 2×5 1.27 mm                │
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
Mount: DU underside, centred over the pot, looking straight down behind a
       sealed borosilicate window; lens-to-pot-rim distance 20–30 cm
```

### 6.2 LED Ring Illumination

```
RV1106 PWM (header pin fixed at layout, 1 kHz)
      │
      │  3.3V logic
      ▼
┌───────────────┐
│ Q_LED         │  IRLML6344 low-side switch on the Unified PCB
│ (IRLML6344)   │
└───────┬───────┘
        │  LED_RET
        ▼
┌───────────────────────────────────────┐
│          White LED Ring               │
│    (12-16 white LEDs, J_LED 2-pin)    │
│                                       │
│  5V_MAIN ◄── J_LED pin 1              │
│  LED_RET ──► J_LED pin 2 ──► Q_LED    │
│                                       │
│  Mounted: Ring around the camera lens │
│           on the DU underside         │
│  Color: White 5000 K, CRI ≥ 90        │
│  Modes: OFF 0 %, CAPTURE 100 %,       │
│         NIGHT 30 % (PWM duty)         │
│  Total: ≤ 1 A on 5V_MAIN              │
└───────────────────────────────────────┘

Note: The ring is driven directly by the RV1106 (epicurad sets the PWM
duty before a capture). No colour control and no CAN message: SET_LED
(0x220) is removed from the message map.
```

---

## 7. Stirring Motor CAN Port (Regular, Non-Isolated)

### 7.1 Wiring

```
STM32G0B1RE                 CSC (in the CS base)                    J_SU (right pillar)     Stirring Unit (24 V CAN servo)
┌──────────────────┐        ┌──────────────────────────────┐        ┌─────────────────┐     ┌──────────────────────────┐
│ PB13 (FDCAN2_TX) ─┼──► D   │ SN65HVD230 (3.3 V)   CANH ──┼── J_CAN_STIR 1 ──┼── 3 CAN_H ──┼── CAN_H              │
│ PB12 (FDCAN2_RX) ◄┼─── R   │  Rs 10k, 120 Ω term  CANL ──┼── J_CAN_STIR 2 ──┼── 4 CAN_L ──┼── CAN_L  (120 Ω in   │
│                  │        │                      GND  ──┼── J_CAN_STIR 3 ──┼── 2 GND ────┼── GND     the motor) │
│ PB4 ──► 2N7002 ──┼──► Q_STIR (AO4407A high-side) ── 24V_STIR ── J_STIR_PWR 1 ──┼── 1 24V_STIR ┼── +24 V             │
│                  │        │  F_STIR 5 A                 GND ── J_STIR_PWR 2 ──┼── 2 GND     │                      │
│                  │        │                             shield ──────────────┼── 5 SHIELD  │                      │
└──────────────────┘        └──────────────────────────────┘        └─────────────────┘     └──────────────────────────┘

Bus:      CAN 2.0B, 1 Mbps, 29-bit IDs (motor protocol); classic frames on FDCAN2
Port:     J_SU — Molex Micro-Fit 3.0, 5-way (24V_STIR, GND, CAN_H, CAN_L, SHIELD) at the pillar; the
          only inter-unit cable. The harness (J_CAN_STIR + J_STIR_PWR bundled) runs inside the right
          rear pillar from the CSC to J_SU; shield to GND at the CSC end
Cable:    twisted pair ≤ 1 m to the gantry, bundled with the 24 V pair
Traffic:  50 Hz velocity (stir) / position (home, park) commands; 50 Hz feedback (rpm, angle,
          current, temperature, faults). Motor command timeout ≤ 500 ms configured at start-up.
Safety:   STM32 sends a disable frame AND opens Q_STIR on E-stop, heartbeat loss, FDCAN2 fault or
          DU undock (DOCK_SENSE_B open).
```

### 7.2 Why a Second Bus

The stirring motor is the only node on this bus. It is kept separate from the isolated heater bus so that the heating unit's mains-side EMI domain never shares a transceiver with the motor, the 1 Mbps motor protocol does not load the 500 kbps host bus, and the galvanic barrier stays dedicated to the mains-side module.

---

## 8. Dock Connector (J_DOCK)

The Dispensing Unit docks onto the top of the Cooking Surface's left rear pillar through an 8-contact magnetic pogo connector (2.54 mm pitch): spring pins rated 2 A each sit in a keyed recess on the pillar and are wired by a short harness to the CSC's 8-pin JST-XH J_DOCK header; flat gold pads on the DU underside land on the Unified PCB's J_DOCK pad array. The DU can only seat one way. No wireless link exists anywhere between the units: the dock carries charge power and the isolated CAN bus, nothing else.

### 8.1 J_DOCK Pinout

| Pin | Signal | Direction | Notes |
|-----|--------|-----------|-------|
| 1 | DOCK_24V | CS → DU | Charge input. Switched on the CSC by Q_DOCK (AO4407A P-MOSFET, STM32 PB5 via 2N7002) only while DOCK_SENSE_B is low; F_DOCK 2 A polyfuse. Pads are dead when the unit is lifted |
| 2 | GND | — | Charge return; also ties the DU logic ground to the CS ground while docked |
| 3 | CAN_H | bus | Isolated 500 kbps bus (same bus as the heating unit) |
| 4 | CAN_L | bus | |
| 5 | GND_ISO | — | Isolated bus ground |
| 6 | 5V_ISO | CS → DU | From the B0505S-1WR3 on the CSC, F_CAN 100 mA; powers the bus side of the DU's ISO1050DUB #2 |
| 7 | DOCK_SENSE_A | CS → DU | Tied to GND on the CS; 10k pull-up on the DU → RV1106 GPIO; low = docked |
| 8 | DOCK_SENSE_B | DU → CS | Tied to GND on the DU; 10k pull-up on the CSC → STM32 PB3; low = DU present (enables Q_DOCK) |

The isolated CAN domain (5V_ISO / GND_ISO) is generated once, on the CSC, and extended over dock pins 3–6; the dock → Unified PCB run is a stub ≤ 30 cm off the terminated CSC ↔ module segment (see §10). On the DU, DOCK_PWR_OK (100k/10k divider on DOCK_24V → 2N7002 → RV1106 GPIO, active-low) tells `epicurad` whether the dock is actually delivering 24 V, independently of DOCK_SENSE_A.

### 8.2 Lift / Undock Behaviour

Lifting the DU opens the bus and the 24 V at the same instant. Nothing is latched on either side, so the sequence is passive and the same whether the lift is deliberate or accidental:

| Where | Trigger | Response |
|-------|---------|----------|
| Heating unit | HEAT_SET_TEMP / HEAT_SET_POWER keep-alive from the RV1106 stops (the AP is gone from the bus) | Drops to zero power ≤ 1 s after the last keep-alive (unit rule, unchanged) |
| STM32 (CSC) | DOCK_SENSE_B goes high | Immediate **safe hold**: HEAT_ON_OFF = 0, stir disable frame on FDCAN2, Q_STIR off, Q_DOCK off (pads de-energised), STATUS with fault 0x17 DU_UNDOCKED. Not an E_STOP. Back to NORMAL when DOCK_SENSE_B is low again and HB_AP returns |
| RV1106 (DU) | DOCK_SENSE_A goes high (GPIO edge) | VSYS falls over to the 2S pack with no gap (Schottky-OR); state machine → PAUSED (reason UNIT_LIFTED); UI shows the battery indicator. Resume only by user tap after re-docking (no auto-resume); same 30 min food-safety ceiling as an AC outage |
| RV1106 (DU) | DOCK_PWR_OK inactive while DOCK_SENSE_A still says docked, confirmed by TELEMETRY timeout (300 ms) | AC power failure: DU keeps running on its pack; auto-resume to RESUMING when TELEMETRY returns within 5 min (the STM32 reboots in < 1 s after mains returns), prompt if < 30 min, ERROR beyond |

Re-docking restores DOCK_SENSE_A/B first (the sense pins are the shortest contacts in the stack by convention), then Q_DOCK re-applies DOCK_24V, VSYS rises to ≈ 23.5 V, the CAN stub rejoins the bus and HB_AP resumes.

---

## 9. Display Interface

### 9.1 SPI LCD Wiring

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

### 9.2 Display Specifications

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

## 10. Isolated CAN Bus (RV1106 ↔ STM32 ↔ Electric Heating Unit)

One isolated CAN 2.0B bus at 500 kbps connects the three controllers: the Luckfox RV1106 (application processor, on the Unified PCB in the Dispensing Unit), the STM32G0B1 (on the Cooking Surface Controller in the Cooking Surface) and the electric heating unit's own MCU. The bus is the CSC's **isolated CAN port (J_CAN_HEAT)** to the unit, extended to the DU over dock pins 3–6 (Section 8); the stirring motor is on the separate regular port of Section 7. The RV1106 has no CAN peripheral, so it joins through an MCP2518FD SPI CAN controller on the Unified PCB (SPI0 CS1 through the J_AP slot) with ISO1050DUB #2, whose bus side is powered from the dock's 5V_ISO; the STM32 keeps FDCAN1 + ISO1050DUB #1 on the CSC. The isolated domain (5 V_ISO and GND_ISO) is generated once, by the B0505S-1WR3 on the CSC. Termination is 120 Ω on the CSC at J_CAN_HEAT and 120 Ω inside the unit; the dock → Unified PCB run is a stub ≤ 30 cm. Lifting the DU opens the bus and the 24 V at the same instant. The heating unit runs its own temperature loop; the RV1106 sends setpoints and reads status, and the STM32 can only force the heater off. Message IDs are owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]].

### 10.1 CAN Bus Wiring (Primary Link)

```
Luckfox Pico Zero (40-pin)    Unified PCB v4.0 (DU)              J_DOCK         CSC (CS)                                 Electric Heating Unit
┌───────────────────┐    ┌──────────────────────────────┐    ┌─────────┐   ┌───────────────────────────────────┐   ┌────────────────┐
│ Pin 19 SPI0_MOSI ─┼───►│ MCP2518FD ──► ISO1050DUB #2 ─┐│    │         │   │ STM32 FDCAN1 ──► ISO1050DUB #1 ─┐ │   │  Onboard CAN   │
│ Pin 21 SPI0_MISO ◄┼────│ (SPI ≤20 MHz, 40 MHz xtal)   ││    │         │   │ PB8 RX / PB9 TX                 │ │   │  controller    │
│ Pin 23 SPI0_CLK ──┼───►│                      CANH ───┼┼────┼ 3 CAN_H ┼───┼── CANH ─────────────────────────┼─┼───┼── CAN_H        │
│ SPI0_CS1 (GPIO58)─┼───►│ CS                   CANL ───┼┼────┼ 4 CAN_L ┼───┼── CANL ─────────────────────────┼─┼───┼── CAN_L        │
│ GPIO (INT) ◄──────┼────│ INT               GND_ISO ───┼┼────┼ 5 GND_ISO───┼── GND_ISO ──────────────────────┼─┼───┼── GND          │
│                   │    │ bus-side VCC ◄─── 5V_ISO ────┼┼────┼ 6 5V_ISO┼───┼── 5V_ISO ◄── B0505S-1WR3 ◄── 5 V │ │   │  120 Ω term    │
│ Pin 24 SPI0_CS0 ──┼──► LCD    (stub ≤ 30 cm)          ││    │         │   │ R_TERM1 120 Ω + PESD1CAN at     │ │   └────────────────┘
└───────────────────┘    └──────────────────────────────┘    └─────────┘   │ J_CAN_HEAT (JST-XH 4: H, L,     │ │
                                                                            │ GND_ISO, 5V_ISO) ───────────────┘ │
                                                                            └───────────────────────────────────┘

CAN Configuration:
  Bit rate:     500 kbps, CAN 2.0B, 11-bit IDs (classic frames on FDCAN1)
  Nodes:        AP (RV1106 via MCP2518FD, in the DU), STIR (STM32, on the CSC), HEAT (module MCU, own PID)
  Isolation:    ISO1050DUB #1 on the CSC, ISO1050DUB #2 on the Unified PCB, both in one isolated 5 V
                domain made once by the B0505S-1WR3 on the CSC (5 kV RMS) and carried over dock pins
                3–6 (F_CAN 100 mA on 5V_ISO). Isolation slot around ISO1050 #2 and the dock pins on
                the Unified PCB.
  Termination:  120 Ω at J_CAN_HEAT on the CSC and inside the module; the dock → Unified PCB run
                to the RV1106 node is a stub ≤ 30 cm
  Dock:         the bus crosses the 8-pin magnetic pogo dock; lifting the DU opens the bus and the
                24 V together (Section 8.2)
  Linux:        mcp251xfd kernel driver → SocketCAN can0; epicurad `can` thread (SCHED_FIFO)
  SPI sharing:  MCP2518FD shares SPI0 MOSI/MISO/CLK with the LCD (CS0); an LCD DMA chunk holds
                the bus ≤10 ms, the MCP2518FD 32-object RX FIFO absorbs frames meanwhile
  Cable:        shielded twisted pair ≤1 m from J_CAN_HEAT to the module; shield to GND_ISO at the
                CSC end only
```

### 10.2 STM32 Firmware Update (CAN Bootloader + USB DFU)

```
Luckfox Pico Zero (swupdate handler)             STM32G0B1RE on the CSC
┌──────────────────────────┐                     ┌──────────────────────────────┐
│  epicurad streams the    │  0x7E0 FW_UPDATE_REQ│  In-application CAN           │
│  STM32 image over        ┼────────────────────►┼  bootloader (OpenBLT-style)   │
│  SocketCAN can0, through │  0x7E8 FW_UPDATE_RSP│  ERASE / WRITE / VERIFY / BOOT│
│  the dock                ◄┼─────────────────────┼  dual-bank flash, CRC check   │
└──────────────────────────┘                     └──────────────────────────────┘

Update paths:
  Field:      RV1106 → isolated CAN bus (over the dock) → in-application CAN bootloader.
              0x7E0 FW_UPDATE_REQ (AP → STIR): seq, op (ERASE/WRITE/VERIFY/BOOT), 5 data bytes.
              0x7E8 FW_UPDATE_RSP (STIR → AP): seq, op, result, 4 data bytes.
              Update mode only, lowest-priority IDs on the bus; the heater and stir motor are
              idle during an update and the old image stays bootable until VERIFY passes.
  Bench:      USB-C J_USB on the CSC — ST USB DFU (SW_BOOT + SW_RST), also USB CDC console.
  Factory:    SWD via J_SWD (2×5 1.27 mm).
  No UART:    there is no UART2/USART2 link, BOOT0 or NRST line from the RV1106 any more; the two
              controllers are in different units and share only the CAN bus. USART2 (PA2/PA3)
              is a local debug console on J_DBG.
```

### 10.3 Message Map (CAN)

Identifiers are owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]; this table mirrors the blocks. Command frames carry a sequence byte first; ACK/NAK (0x3FF) echoes it. Node names are unchanged: AP = RV1106, STIR = STM32 (now on the CSC, src_node 2), HEAT = heating unit.

| CAN ID block | Messages | Direction | Notes |
|--------------|----------|-----------|-------|
| 0x001 | E_STOP | any -> all | src_node, reason_code; no ACK, highest priority |
| 0x010 | HB_AP | RV1106 -> all | seq, uptime_ms; every 2 s, STM32 safe state after 5 s without it |
| 0x100–0x103 | HEAT_SET_TEMP, HEAT_ON_OFF, HEAT_QUERY, HEAT_SET_POWER | RV1106 -> module (STM32 sends HEAT_ON_OFF = 0 only) | Temperature setpoint (unit PID) or power 0–100 %, re-sent at 2 Hz as keep-alive; unit drops to 0 after 1 s without a refresh |
| 0x180–0x182 | HEAT_STATUS, HEAT_FAULT, HEAT_ACK | module -> all | Pot-bottom (centre sensor) temperature, element temperature, pot detection, faults (10 Hz); read by the RV1106 engine and the STM32 safety monitor |
| 0x202, 0x221–0x225 | SET_STIR, SET_SPEED, ARM_STOP, ARM_HOME, ARM_STATUS, SET_RAMP | RV1106 -> STM32 | Stirring arm block (see [[../05-Subsystems/02-Robotic-Arm|Robotic Arm]] §8.2). 0x220 SET_LED is removed: the LED ring is driven locally by the RV1106 |
| 0x260–0x262 | SET_EXHAUST, GET_EXHAUST, EXHAUST_AUTO | RV1106 -> STM32 | Exhaust fans on the CSC (codes 0x60–0x62 of [[../05-Subsystems/05-Exhaust-Fume-Management|Exhaust]] §3.4): SET_EXHAUST (seq, duty_pct); GET_EXHAUST (seq → ACK data duty_pct, rpm1, rpm2); EXHAUST_AUTO (seq, stage_id) |
| 0x310, 0x312 | TELEMETRY (20 Hz), STATUS | STM32 -> RV1106 | Motor rpm and current, safety state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok) and fault codes. 0x311 LOADCELLS is removed; STATUS fault_detail no longer carries batt_mV. Fault codes: 0x01–0x05, 0x10 STIR_STALL, 0x15 STIR_CAN_FAULT, 0x17 DU_UNDOCKED (Info), 0x20; 0x11–0x14, 0x16 and 0x21 are gone with the dispensers, battery and I2C |
| 0x3FF | ACK/NAK | STM32 -> RV1106 | seq, cmd_type, result_code, up to 5 data bytes |
| 0x7E0 / 0x7E8 | FW_UPDATE_REQ / FW_UPDATE_RSP | RV1106 <-> STM32 | CAN bootloader (§10.2); update mode only, lowest priority |

Removed from the bus: 0x220 SET_LED and the 0x230–0x239 dispensing block (DISPENSE_FID/CID/SLD, QUERY_WEIGHT, PREFLIGHT, TARE, DISPENSER_HOME, DISPENSER_STATUS; see [[../05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]] §7.3). Dispensing, the load cells and the LED ring are local to the RV1106 in the DU: the same commands, names and semantics now travel on an internal queue from the recipe engine to the `dispense` thread.

### 10.4 Frame Conventions (CAN)

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

## 11. Power Supply

### 11.1 AC-DC Power Supply Architecture

```
AC Mains (220-240V 50Hz) — Cooking Surface (CS)
        │
        ├──────────────────────────────────────────────┐
        ▼                                              ▼
┌───────────────────┐                    ┌──────────────────────────┐
│  IEC C14 Inlet    │    safety relay    │  Electric Heating Unit   │
│  + Fuse (10A)     │ ── (CSC J_SAFE 1) ►│  (rice-cooker class)     │
│  + EMI Filter     │                    │  (self-contained AC      │
│  (X2 cap + CMs)   │                    │   power stage + plate)   │
└────────┬──────────┘                    │  1,300W max (assumed)    │
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
                 │ 24V DC (XT30)
                 ▼
┌───────────────────────────────────────────────────────────┐
│     Cooking Surface Controller — CSC (J_24V_IN)           │
│     F1 5 A polyfuse, SS54 reverse, SMBJ24A TVS            │
│                                                           │
│  24V ──► MP1584EN #1 ──► 12V (fans J_FAN, relay coil)     │
│  24V ──► MP1584EN #2 ──► 5V ──► AMS1117 ──► 3.3V (STM32,  │
│                          SN65HVD230, ISO1050 #1 logic)    │
│  5V  ──► B0505S-1WR3 ──► 5V_ISO / GND_ISO (bus domain:    │
│                          J_CAN_HEAT + J_DOCK 5/6, F_CAN)  │
│  24V ──► Q_STIR (PB4) ──► F_STIR 5 A ──► J_STIR_PWR ──►   │
│          J_SU ──► Stirring Unit (24V_STIR)                │
│  24V ──► Q_DOCK (PB5, only while DOCK_SENSE_B is low) ──► │
│          F_DOCK 2 A ──► J_DOCK pin 1 (DOCK_24V)           │
└────────────────────────────┬──────────────────────────────┘
                             │ 8-pin magnetic pogo dock (CS left pillar)
                             │ DOCK_24V + GND (pins 1–2), CAN (3–6), sense (7–8)
                             ▼
┌───────────────────────────────────────────────────────────┐
│     Unified PCB v4.0 — Dispensing Unit (DU)               │
│                                                           │
│  DOCK_24V ──► MP1584EN #1 ──► 12V ──► TP5100 (1.0 A,      │
│               R_CS 0.1 Ω) ──► 2S Li-ion pack (J_BAT)      │
│               INA219 #2 (0x44, 10 mΩ) in the BAT+ path    │
│  VSYS = DOCK_24V ⊕ BAT+ (SS54 Schottky-OR, passive)       │
│         docked ≈ 23.5 V; lifted / mains lost 6.0–8.4 V    │
│  VSYS ──► TPS54531 ──► 5V_MAIN (Pico Zero, LCD, white LED │
│           ring ≤ 1 A, buzzer) ──► AMS1117 ──► 3.3V (I2C   │
│           devices, MCP2518FD, ISO1050 #2 logic, TB6612)   │
│  VSYS ──► MP1584EN #2 ──► 6V_DSP, switched by Q_DSB       │
│           (PCF8574 #2 P4), 3 A PTC, 1000 µF: DSB servos   │
│           ×4, TB6612 pumps (6 V), solenoids (6 V NC)      │
│  5V_ISO comes from the dock — no isolated DC-DC here      │
│  No 12 V loads on this board (fans are on the CSC)        │
└────────┬──────────────────────────────────────────────────┘
         │
         │ J_AP slot (2x20, Pico Zero plugs in)
         │ (5V_MAIN on pins 2,4; GND on pins 6,9,etc.)
         │ Direction: Unified PCB → Luckfox Pico Zero
         ▼
┌──────────────────┐
│ Luckfox Pico Zero│
│ (receives 5V)    │
│ ──► RV1106G3     │
│ ──► 4" LCD + cam │
│ USB-C for flash  │
└──────────────────┘

Note: The electric heating unit has its own AC power
inlet (not through the 24V PSU). The PSU feeds the CSC,
which derives the CS rails and hands 24 V on to the
Stirring Unit (Q_STIR) and the dock (Q_DOCK). The Pico
Zero is powered via the Unified PCB's 5V_MAIN rail through
the J_AP slot (pins 2, 4); its on-board regulators derive
the SoC, camera and Wi-Fi rails. It draws ~1 W.
The battery is the DU's PRIMARY supply: docked, VSYS comes
from DOCK_24V and the pack does not discharge (a full
session docked draws from the dock, not the pack); lifted
or on mains loss the pack carries the ≈ 3 W DU load for
> 5 h with no gap (Schottky-OR). Charge ≈ 3 h from empty
at 1.0 A while docked; CHRG/STDBY on PCF8574 #2 P6/P7.
The RV1106 self-manages the pack from INA219 #2: warning
banner at 6.4 V, checkpoint + halt at 6.2 V, pack PCM
cut-off ≈ 5.6 V as last resort. At an empty pack (6.2 V)
MP1584EN #2 drops out to ≈ 6.0 V, acceptable.
The RV1106 sends temperature/power setpoints to the module
over the isolated CAN bus (the module runs its own PID);
the STM32 can force it off on the same bus.
```

### 11.2 Mean Well LRS-75-24 Specifications

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

### 11.3 Power Budget Table

**Cooking Surface (CS) — LRS-75-24 via the CSC, plus the Stirring Unit and the dock feed**

| Rail | Subsystem | Typical (W) | Peak (W) | Notes |
|------|-----------|-------------|----------|-------|
| AC direct | Electric heating unit | 450 | 1,300 | Self-contained unit (1,300 W assumed, unit TBD), own AC inlet, through the safety relay |
| 24V via Q_STIR (CSC) | CAN servo stirring motor (SU, via J_SU) | 12 | 48 | 24V_STIR switched rail, ~0.5A typical, ~2A peak; F_STIR 5 A |
| 24V → 12V (CSC) | Exhaust fans (x2) | 1 | 6 | 12V DC, 120mm, 0.3-0.5A each, J_FAN |
| 24V → 12V (CSC) | Safety relay coil | 0.5 | 1 | Omron G5V-2, mains disconnect for the heating unit |
| 24V → 5V → 3.3V (CSC) | STM32G0B1RE, SN65HVD230, ISO1050 #1 logic side | 0.2 | 0.4 | AMS1117 LDO on the CSC |
| 5V → B0505S (CSC) | 5V_ISO bus domain (both transceivers' bus side, over the dock) | 0.3 | 0.5 | F_CAN 100 mA |
| 24V via Q_DOCK (CSC) | DOCK_24V to the Dispensing Unit (table below) | 5 | 30 | F_DOCK 2 A; DU load + charger while docked |
| - | Regulator losses | 2 | 4 | Buck + LDO inefficiency |
| **24V PSU Total** | | **~21W** | **~55W** | **Stir peak and dispense/charge peak do not coincide; within 76.8W PSU capacity** |

**Dispensing Unit (DU) — from DOCK_24V while docked, from the 2S pack when lifted or on mains loss**

| Rail | Subsystem | Typical (W) | Peak (W) | Notes |
|------|-----------|-------------|----------|-------|
| VSYS → 5V_MAIN (TPS54531) | Luckfox Pico Zero (RV1106G3) | 1 | 2 | 5V via 40-pin header; includes eMMC, Wi-Fi/BT, IMX415-98 camera, NPU/ISP load |
| 5V_MAIN | 4" SPI LCD + backlight | 0.5 | 0.8 | ST7796S panel + LED backlight, PWM dimmed |
| 5V_MAIN via Q_LED | White LED ring (12–16 LEDs) | 0 | 5 | ≤ 1 A at CAPTURE (100 %), NIGHT 30 %, off otherwise |
| 5V_MAIN | Buzzer | 0 | 0.2 | RV1106 PWM via 2N7002 |
| 5V_MAIN → 3.3V | PCA9685, PCF8574 #2, INA219 ×2, TCA9543A, NAU7802 ×2, MCP2518FD, ISO1050 #2 logic side, TB6612 VCC | 0.3 | 0.5 | AMS1117 LDO on the Unified PCB |
| VSYS → 6V_DSP (MP1584EN #2) | Dispenser servos DSB (x4, one moving at a time) | 0 | 15 | 6.0 V rail switched on only during a dispense; ≤ 2.5A stall (DS3218 2.2A, MG996R ~2.5A), INA219 #1 window |
| VSYS → 6V_DSP | SLD peristaltic pumps (x2, 6 V) | 0 | 4 | TB6612 VM on 6V_DSP, only during dispense |
| VSYS → 6V_DSP | SLD solenoid valves (x2, 6 V NC) | 0 | 6 | Only during dispense |
| DOCK_24V → 12V (MP1584EN #1) | TP5100 battery charger | 0 | 10 | 1.0 A into the 2S pack while charging (≈ 3 h from empty), 0 when full; docked only |
| - | Regulator losses | 1 | 3 | Buck + LDO inefficiency |
| **DU Total (docked, from DOCK_24V)** | | **~3W** | **~30W** | **Charge and dispense peaks rarely coincide; F_DOCK 2 A (48 W)** |
| **DU Total (lifted, from the pack)** | | **~3W** | — | **RV1106 + LCD + logic on 19 Wh → > 5 h** |

| | | Typical (W) | Peak (W) | |
|------|-----------|-------------|----------|-------|
| **System Total (incl. heater)** | | **~470W** | **~1,350W** | **Within 2kW limit (1,300 W heater assumed)** |

---

## 12. Electric Heating Unit

### 12.1 Heating Unit Integration

The electric heating unit is a self-contained commercial unit of the premium rice-cooker class with its own AC power inlet, relay/triac mains power stage, resistive heating plate, spring-loaded centre temperature sensor (pressed by the pot) with closed-loop control, and onboard safety circuits. It replaced the induction surface on 2026-11-04 as a drop-in CAN node (same HEAT_* message set); see [[../05-Subsystems/01-Electric-Heating|Electric Heating]]. It sits in the Cooking Surface with the CSC.

The reference unit is the **Philips OneChef NX5300/00** (Electric Heating §2.3): its body becomes the Cooking Surface (modified for the stirrer gantry and the dock pillars), its air-fryer lid is dropped and the Dispensing Unit docks in its place, and its 6 L non-stick inner pot (~4.8 L usable) is Epicura's pot. Its 2,280 W nameplate covers the base plate **and** the air-fryer lid heater together; the base plate alone is expected at 1,000–1,300 W, so 1,300 W stays the planning figure. The plate's temperature range is 80–200 °C (Epicura requests 60–200 °C): sear and tadka stages are ≤ 200 °C and the STM32 limits on `surface_temp` are re-based to > 220 °C CRITICAL / > 230 °C E_STOP (`element_temp` > 250 °C WARNING unchanged). The OEM unit ships with a control board exposing HEAT_* on CAN (confirmed 2026-11-04); the retail touch-panel board is not used. Epicura interfaces with the unit exclusively via the isolated CAN port **J_CAN_HEAT on the CSC** — no high-voltage wiring touches the CSC or the Unified PCB, and no temperature sensor is needed in Epicura.

```
┌──────────────────────────────────────────────────────────┐
│              Electric Heating Unit (rice-cooker class)     │
│                                                            │
│  AC Mains ──► Filter ──► Relay/triac ──► Heating plate     │
│                                                            │
│  Internal safety: pot detection, thermal cutoff,           │
│  thermal fuse; internal PID on the centre sensor           │
│                                                            │
│  Exposed CAN Port:                                         │
│    CAN_H ──────────────────┐                               │
│    CAN_L ──────────────────┤                               │
│    GND ────────────────────┤                               │
└────────────────────────────┼───────────────────────────────┘
                             │
                    ┌─────────────────────┐        ┌─────────────────────┐
                    │  CSC (CS)           │  dock  │  Unified PCB (DU)   │
                    │ J_CAN_HEAT+120Ω term│ pins   │  J_DOCK pads 3–6    │
                    │  5 V_ISO (B0505S)   ├─ 3–6 ──┤  (stub ≤ 30 cm)     │
                    │  ISO1050DUB #1      │        │  ISO1050DUB #2      │
                    │     │               │        │       │             │
                    │  STM32 FDCAN1       │        │  MCP2518FD (SPI)    │
                    │  PB8/PB9            │        │  RV1106             │
                    │  off-switch + relay │        │  setpoint           │
                    └─────────────────────┘        └─────────────────────┘

System Safety:
  - Unit-internal: pot detection (centre sensor), thermal fuse, over-temperature cut-off (cannot be overridden)
  - System-level: safety relay on AC mains to the unit (STM32 PB0 ──► Q_RLY ──► relay, J_SAFE 1 on the CSC)
  - RV1106 sends HEAT_SET_TEMP / HEAT_SET_POWER setpoints (unit PID regulates); STM32
    can force HEAT_ON_OFF=0, broadcast E_STOP on the bus, or open the relay on fault/E-stop
  - Lifting the DU takes the RV1106 off the bus: the unit drops to zero ≤ 1 s after the
    last keep-alive and the STM32 holds safe on DOCK_SENSE_B (Section 8.2)
```

---

## 13. Ingredient Dispensing System (FID / CID / SLD)

The dispensing system comprises three subsystems, all in the Dispensing Unit and all driven by the RV1106 on the Unified PCB v4.0 over I2C3 and PWM — the STM32 has no part in dispensing any more. FID and CID share one electrical control block, the Dispenser Servo Block (DSB). The `epicurad` `dispense` thread (SCHED_OTHER, 50 Hz while active) does what the STM32 Dispense task used to do: PCA9685 ramped moves (≤ 3°/tick), 6V_DSP rail enable, one servo at a time, stall detection (INA219 #1 current > 2.5 A for 300 ms, 3 s move timeout, I2C NACK → retry once with 10° back-off → DSB_STALL), SLD closed loop on the NAU7802 at 10 Hz stopping at 95 % of target, solenoid + pump sequencing, tare, preflight, home and status. See [[03-Ingredient-Dispensing|Ingredient Dispensing System]] for full details.

### 13.1 DSB — FID + CID Servo Wiring

```
  VSYS ──► MP1584EN #2 (6.0 V, 3 A) ──► Q_DSB P-MOSFET high-side switch ──► 6V_DSP rail
                                               ▲                            (1000 µF bulk, 3 A PTC)
                                   PCF8574 #2 P4 (rail enable, I2C3 0x21)

  RV1106 I2C3 (header 16/18) ──► PCA9685 (addr 0x41, on Unified PCB)
                        ├── CH0 ──► J_DSB1 ──► C1  CID carousel index servo, DS3218 270° (4:3 gear-up)
                        ├── CH1 ──► J_DSB2 ──► F1  FID carousel index servo, MG996R (5:3 gear-up)
                        ├── CH2 ──► J_DSB3 ──► F2  FID dose servo, MG996R (canister ¼ tsp measure wheel)
                        └── CH3 ──► J_DSB4 ──► F3  FID steam-gate servo, MG90S (6.0 V directly, D_DSB4 removed)
  RV1106 GPIO ──► PCA9685 OE (active-low; 10k pull-up → servos off at boot and on soft stop)

  I2C3 devices: FT6336 (0x38), PCF8574 #2 (0x21), NAU7802 ×2 (0x2A, behind TCA9543A 0x71),
                INA219 #1 (0x40, 6V_DSP shunt), INA219 #2 (0x44, battery), PCA9685 (0x41)

  Note: all four servos are rated for 6.0 V, so the rail dropped from 6.5 V to 6.0 V and the
  J_DSB4 series diode is gone. Rail off when idle; at an empty pack (6.2 V) the buck drops out
  to ≈ 6.0 V, acceptable. Stall detection via the INA219 #1 current window on the 6V_DSP rail
  (shunt moved there from the old 24 V input).
```

### 13.2 SLD — Liquid Dispensing Wiring

```
  6V_DSP Rail (switched, from MP1584EN #2 on the Unified PCB)
  │
  ├──► Peristaltic Pump (Oil, 6 V DC) — TB6612 Channel A on Unified PCB
  │      PWMA ◄── RV1106 PWM (pin fixed at layout)
  │      AIN1 ◄── PCF8574 #2 P3 (I2C3, 0x21)
  │
  ├──► Peristaltic Pump (Water, 6 V DC) — TB6612 Channel B on Unified PCB
  │      PWMB ◄── RV1106 PWM (pin fixed at layout)
  │      BIN1 ◄── PCF8574 #2 P5 (I2C3, 0x21)
  │
  ├──► Solenoid Valve (Oil, 6 V NC)   ◄── PCF8574 #2 P0 (I2C3, 0x21), IRLML6344 + flyback
  └──► Solenoid Valve (Water, 6 V NC) ◄── PCF8574 #2 P1 (I2C3, 0x21), IRLML6344 + flyback

  PCF8574 #2 (0x21) map: P0 oil solenoid, P1 water solenoid, P2 status LED, P3 TB6612 AIN1,
    P4 6V_DSP rail enable, P5 TB6612 BIN1, P6 TP5100 CHRG (in), P7 TP5100 STDBY (in)

  SLD Load Cells (2× 2 kg, one per reservoir), 24-bit NAU7802 ADCs on I2C3:
    TCA9543A (0x71) channel 0 ──► NAU7802 #1 (0x2A, oil)
    TCA9543A (0x71) channel 1 ──► NAU7802 #2 (0x2A, water)
    Kernel: i2c-mux-pca954x + nau7802 (IIO); 10 Hz closed loop in the dispense thread
    Load-cell fault = NAU7802 I2C NACK / no data-ready (RV1106-detected)
    Low-level alert when reservoir weight < configurable threshold
```

### 13.3 Dispensing Summary

| Subsystem | Actuators | Metering | Min Dispense |
|-----------|-----------|----------|-------------|
| FID (fine / seasonings) | 3× servo on DSB (F1 index, F2 dose, F3 steam gate), 6 canisters with ¼ tsp measure wheels | Volumetric per dose stroke (±10%) | ¼ tsp (~0.5 g) |
| CID (coarse) | 1× servo on DSB (C1 index), 5-slot carousel + cover sector | Whole slot / user pre-measured | One slot (~200 mL) |
| SLD (liquids) | 2× 6 V peristaltic pump (TB6612) + 2× 6 V solenoid + 2× 2 kg load cell on NAU7802 | Closed-loop via dedicated per-reservoir load cells (NAU7802 via TCA9543A) + low-level alerts | ~5 g |
| Exhaust | 2× 120mm fans on the CSC (independent PWM control, SET_EXHAUST over CAN) | Temperature/fume-based control | — |

**Unified PCB On-Board Routing:** All RV1106 dispensing signals connect through the J_AP slot directly to their driver ICs (PCA9685, TB6612, PCF8574 #2, TCA9543A + NAU7802, INA219 ×2, MOSFETs) on the same board. The four DSB servo leads plug into J_DSB1-4 (3-pin JR headers on the switched 6.0 V rail); the SLD harness into J_SLD (re-pinned for 6 V). No inter-board connector is required inside the DU. The Luckfox Pico Zero sits in the J_AP slot, which carries 5V_MAIN power, the SPI0 CS1 lines of the on-board MCP2518FD CAN controller, I2C3, the four PWM lines, the OE / dock-sense GPIOs and the display lines (re-emerging on J_LCD).

---

## 14. WiFi / Bluetooth

### 14.1 RV1106 Onboard Wireless

The Luckfox Pico Zero includes onboard WiFi and Bluetooth. No external modules are needed.

| Feature | Specification |
|---------|---------------|
| WiFi Standard | 802.11ax (WiFi 6), 2.4GHz single-band |
| Max Throughput | 2.4GHz only; ample for recipe sync, MQTT telemetry and the 1.5 Mbps H.264 live view |
| Bluetooth | BLE 5.2 |
| Antenna | Onboard antenna, plus external antenna connector |
| Security | WPA3, WPA2 |

### 14.2 Wireless Use Cases

| Function | Protocol | Description |
|----------|----------|-------------|
| App Pairing | BLE 5.2 | Initial device discovery and WiFi credential transfer |
| Recipe Download | HTTPS | Fetch new recipes from cloud API |
| Live Camera Feed | RTSP (H.264 720p) | On-demand stream to companion app (same LAN direct, otherwise via cloud relay) |
| Telemetry Upload | MQTT/HTTPS | Cooking session data to cloud (optional) |
| OTA Firmware Update | HTTPS + swupdate | RV1106 OS/app (A/B slots) and STM32 firmware updates (streamed on to the CSC over the CAN bootloader, §10.2) |
| Remote Monitoring | MQTT | Telemetry to cloud every 10 s while cooking; cloud pushes status to the app |
| NTP Time Sync | NTP (UDP) | Clock synchronization on boot |

### 14.3 Antenna Considerations

- Pico Zero onboard antenna sufficient for typical kitchen distances (<10m)
- The Pico Zero sits in the Dispensing Unit, the topmost unit; if the DU shell is metal, use the external antenna connector to an antenna in the DU top
- Keep antenna away from the heating unit's relay/triac switching and the PSU (the DU top is the farthest point from the mains electronics)

---

## 15. Storage Architecture

### 15.1 RV1106 Storage

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

## 16. PCB Layout Considerations

### 16.1 Mains-Side EMI

- The heating unit has no RF switching; the EMI sources in the CS are the unit's relay/triac mains switching, the switching PSU and the stirring servo
- **Distance:** Maintain minimum 50mm between the mains-side electronics (heating unit power stage, PSU) and sensitive PCBs; the Unified PCB is in the DU above the pot
- **Grounding:** Copper ground pour on the CSC and the Unified PCB, connected to chassis ground

### 16.2 Sensor Signal Routing

- I2C3 stays on the Unified PCB (PCA9685, PCF8574 #2, INA219 ×2, TCA9543A → NAU7802 ×2, FT6336 via J_LCD); 4.7k pull-ups near the J_AP slot
- Keep the two CAN buses apart: the regular stir-motor bus (J_CAN_STIR, CSC) must not run alongside the isolated heater bus (J_CAN_HEAT, CSC) or cross either board's isolation slot; the isolated bus to the DU runs in the pillar dock harness and lands on the Unified PCB's J_DOCK pads 3–6 inside its isolation slot, as a stub ≤ 30 cm
- Load cells: NAU7802 ADCs sit at the reservoirs' load cells on the Unified PCB; keep the analog bridge leads short and twisted, the I2C mux run is noise-tolerant
- The stirring-unit harness (J_CAN_STIR + J_STIR_PWR) runs inside the right rear pillar to J_SU; the dock harness (J_DOCK, 8-way) inside the left rear pillar
- Camera CSI-2: differential pairs, matched length, <20cm FFC cable

### 16.3 Power / Signal Ground Separation

```
┌─────────────────────────────────────────────────────┐
│                  Ground Architecture                 │
│                                                      │
│  AC Mains Earth ──────────────┐                      │
│                               │                      │
│  Chassis Ground ◄─────────────┤                      │
│  (CS metal enclosure)         │                      │
│                               │                      │
│  Power Ground ◄───────────────┤ (star connection)    │
│  (PSU output returns,         │                      │
│   heater power stage)         │                      │
│                               │                      │
│  Signal Ground (CS) ◄─────────┘                      │
│  (CSC: STM32, SN65HVD230,     │                      │
│   low-current digital)        │ dock pin 2 (GND)     │
│                               ▼                      │
│  Signal Ground (DU) ◄── joins the CS ground ONLY     │
│  (Unified PCB: RV1106,        through dock pin 2     │
│   sensors, dispensers)        while docked; floats   │
│                               on the pack when lifted│
│                                                      │
│  Isolated bus ground (GND_ISO): made on the CSC by   │
│  the B0505S, carried over dock pin 5; never tied     │
│  to either signal ground                             │
│                                                      │
│  Single-point star ground at PSU output              │
│  Ferrite bead between power GND and signal GND       │
└─────────────────────────────────────────────────────┘
```

### 16.4 Thermal Relief

- Electric heating unit: the plate stores heat and radiates after power-off; ensure adequate ventilation around the unit
- STM32 (on the CSC): thermal vias under exposed pad to ground plane; the CSC sits in the CS rear in the exhaust airflow
- RV1106 (Pico Zero, in the DU): ~1 W, no heatsink required; adequate ventilation space
- Battery (in the DU): cool zone by definition, away from the heating unit
- PSU: ventilated enclosure area, thermal shutdown at 85C internal

---

## 17. BOM Summary

### 17.1 Prototype Bill of Materials

| Category | Component | Quantity | Est. Unit Cost (USD) | Est. Total (USD) |
|----------|-----------|----------|---------------------|-------------------|
| **Compute** | Luckfox Pico Zero (RV1106G3, 8 GB eMMC) | 1 | $47 | $47 |
| | MicroSD 32GB | 1 | $10 | $10 |
| **MCU** | STM32G0B1RE Nucleo Board (proto) | 1 | $11 | $11 |
| | STM32G0B1RET6 IC (production) | 1 | $3.50 | $3.50 |
| **Display** | 4" ST7796S SPI LCD with FT6336 touch | 1 | $15 | $15 |
| **Camera** | Luckfox IMX415-98 IR-CUT 8 MP camera module (incl. 22-pin FPC) | 1 | $54 | $54 |
| **Sensors** | NAU7802 24-bit load-cell ADC (SLD, one per reservoir) | 2 | $2 | $4 |
| | TCA9543A I2C mux (NAU7802 address split) | 1 | $1 | $1 |
| | INA219 #2 current/voltage monitor (battery, 10 mΩ shunt) | 1 | $1 | $1 |
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
| | 6V peristaltic pumps (SLD) | 2 | $10 | $20 |
| | 6V NC solenoid valves (SLD) | 2 | $4 | $8 |
| | 120mm 12V DC brushless fans (exhaust) | 2 | $5 | $10 |
| | 5V piezo buzzer (active) | 1 | $2 | $2 |
| **Heater** | Donor cooker: Philips OneChef NX5300/00 or equivalent — heating unit, controller, 6 L non-stick pot, glass lid, base body | 1 | $230 | $230 |
| **Power** | Mean Well LRS-75-24 (24V/3.2A) | 1 | $20 | $20 |
| | IEC C14 inlet + EMI filter | 1 | $8 | $8 |
| | Safety relay (Omron G5V-2) | 1 | $5 | $5 |
| **Misc** | White LED ring (12–16 LEDs, 5000 K, CRI ≥ 90) | 1 | $4 | $4 |
| | E-Stop mushroom button | 1 | $4 | $4 |
| | ISO1050DUB isolated CAN transceivers (#1 on the CSC, #2 on the Unified PCB) | 2 | $3.50 | $7 |
| | MCP2518FD CAN controller + 40 MHz crystal (RV1106 node, Unified PCB) | 1 | $3 | $3 |
| | SN65HVD230 CAN transceiver (stir-motor port, CSC) | 1 | $0.90 | $0.90 |
| | TP5100 2S charger + inductor + sense resistor (1.0 A) | 1 | $1 | $1 |
| | 8-pin magnetic pogo connector pair (J_DOCK, 2 A pins) | 1 | $6 | $6 |
| | Molex Micro-Fit 3.0 5-way pair (J_SU) | 1 | $2 | $2 |
| | Passive components (R, C, etc.) | Lot | - | $20 |
| | Unified PCB v4.0 (4-layer, 1 board) | 1 | $40 | $40 |
| | Cooking Surface Controller PCB (4-layer, 5 pcs) | 1 | $25 | $25 |
| | Wiring, connectors, FFC cables | Lot | - | $25 |
| **Enclosure** | 3D-printed enclosure (prototype) | 1 | $80 | $80 |
| | Gantry hardware (rods, brackets) | Lot | - | $30 |

**Estimated Prototype BOM Total: $795 - $905 USD** (donor cooker $230 replaces the $45 heating unit and the $25 pot line: +$160, was $635 - $745; production: OEM heating unit + pot, bulk, ≈ $60; three-unit split: net ≈ +$32 for the CSC PCB, dock pair, NAU7802 ×2, TCA9543A, INA219 #2, white LED ring and J_SU, less the HX711 ×2, WS2812B ring and 74AHCT1G125; electric heating unit −$15 against the induction surface)

*Note: Production BOM would be lower per unit at volume. Prototype uses Nucleo dev board that would be replaced with bare STM32G0B1RET6 on the Cooking Surface Controller. The Luckfox Pico Zero is used as-is (off-the-shelf module, no carrier board) in both prototype and production.*

---

## 18. Hardware Validation Checklist

### 18.1 Power Supply
- [ ] Verify 24V rail from Mean Well PSU within spec (24V +/-5%)
- [ ] Measure ripple on each rail of the CSC and the Unified PCB (<50mV peak-to-peak)
- [ ] Load test at full power (heating unit 1,300 W assumed + all subsystems)
- [ ] Verify standby power <5W
- [ ] Test EMI filter effectiveness (conducted emissions)
- [ ] Verify fuse blows at rated overcurrent
- [ ] Dock charge: DOCK_24V appears on J_DOCK pin 1 only while DOCK_SENSE_B is low; 0 V on the pads with the DU lifted; F_DOCK trips at 2 A
- [ ] Dock power: VSYS ≈ 23.5 V docked with zero pack discharge (INA219 #2); TP5100 charges at ~1.0 A, full from empty in ≈ 3 h; CHRG/STDBY read on PCF8574 #2

### 18.2 Compute (RV1106)
- [ ] Luckfox Pico Zero boots Buildroot Linux from eMMC; A/B rootfs fallback verified
- [ ] CAN bus up on `can0` (MCP2518FD on SPI0 CS1, 500 kbps) across the dock; commands to the STM32 on the CSC and 20 Hz TELEMETRY exchanged while the LCD is refreshing; no error frames on the ≤ 30 cm dock stub
- [ ] STM32 firmware load over the CAN bootloader (0x7E0/0x7E8) from the RV1106 swupdate handler; USB DFU on the CSC J_USB as the bench fallback
- [ ] Camera captures 1280x720 @ 30fps frames via MIPI CSI (IMX415-98, ISP tuning loaded) through the underside window
- [ ] NPU runs the INT8 stage classifier in <20 ms
- [ ] Display renders LVGL UI via SPI0 (fbtft, full-frame refresh ~50 ms)
- [ ] Touch input (FT6336, I2C3) registers on all screen areas
- [ ] LED ring: RV1106 PWM duty 0 / 30 / 100 % gives OFF / NIGHT / CAPTURE; ≤ 1 A on 5V_MAIN at 100 %
- [ ] Buzzer: RV1106 PWM drives all alert patterns
- [ ] All I2C3 devices enumerate (0x21, 0x2A via both TCA9543A channels, 0x38, 0x40, 0x41, 0x44, 0x71)
- [ ] WiFi connects to AP, achieves >10 Mbps throughput
- [ ] BLE advertises and pairs with test phone
- [ ] eMMC read/write speed adequate (>50 MB/s sequential)

### 18.3 Electric Heating Unit
- [ ] Unit responds to CAN queries (HEAT_QUERY → HEAT_STATUS)
- [ ] CAN power level commands correctly modulate heating
- [ ] Unit heats water from 20C to 100C within 10 minutes (1.5L, 1,300 W assumed)
- [ ] Setpoint step 25 → 100C at the centre sensor rises in < 180 s (plate-limited ramp ~2-4 C/s)
- [ ] Unit holds a HEAT_SET_TEMP setpoint within +/-5C (its own PID); RV1106 keep-alive at 2 Hz never drops out while the LCD refreshes
- [ ] OEM unit: its CAN control board answers HEAT_* on the isolated bus
- [ ] Sear stage reaches 200C at the centre sensor with the 6 L pot; injected surface_temp > 220C raises CRITICAL and > 230C triggers E_STOP
- [ ] All four power profiles (sear/boil/simmer/warm) verified
- [ ] Unit-internal pot detection (spring-loaded centre sensor) prevents heating without pot
- [ ] Safety relay (CSC Q_RLY, J_SAFE 1) disconnects AC to the unit on E-stop or fault
- [ ] STM32 HEAT_ON_OFF=0 and E_STOP broadcast stop heating within 500ms; unit drops to 0 power 1 s after the HEAT_SET_TEMP keep-alive stops
- [ ] Undock: lifting the DU mid-cook stops the unit ≤ 1 s (keep-alive loss), the STM32 reports DU_UNDOCKED, Q_STIR and Q_DOCK open; re-docking returns to NORMAL once HB_AP resumes
- [ ] E-stop on the CS front (CSC PB2) and the soft stop on the DU UI (E_STOP over CAN) both stop the heater and the stir motor

### 18.4 Servo System
- [ ] Main arm (24V CAN servo) rotates full 360 degrees smoothly; motor enumerates on FDCAN2 at 1 Mbps
- [ ] Stirring speed controllable from 10-60 RPM; reported RPM within ±5 of commanded
- [ ] Motor stops within 500 ms when FDCAN2 traffic stops; 0 V on J_STIR_PWR / J_SU with Q_STIR off
- [ ] Stirring-unit harness through the right pillar: J_SU mates one way, shield continuity to the CSC
- [ ] Arm torque sufficient to stir thick curry/dal
- [ ] Each DSB servo (x4) reaches commanded angle within ±2° via PCA9685 on I2C3
- [ ] 6V_DSP rail switches off after each dispense (no idle jitter or buzz); 6.0 V ±5 % under a 2.5 A servo stall
- [ ] PCA9685 OE high on soft stop / boot leaves all four servos limp

### 18.5 Sensors
- [ ] Camera: white balance calibrated, image sharp across full pot FOV
- [ ] Unit surface_temp (centre sensor, HEAT_STATUS) tracks a thermocouple on the pot bottom within +/-5C at 100C
- [ ] Battery: pack charges to 8.4 V at ~1.0 A; CHRG/STDBY read on PCF8574 #2; INA219 #2 voltage within 2 %, current within 5 %
- [ ] Battery: pulling mains with the DU docked keeps the Pico Zero and LCD running (no reboot); DOCK_PWR_OK goes inactive, PAUSED (AC Power Failure) after the 300 ms TELEMETRY timeout, auto-resume when mains returns
- [ ] Battery: lifted DU runs > 5 h at ≈ 3 W; warning banner at 6.4 V, checkpoint + halt at 6.2 V, RECOVERING on next power
- [ ] Load cells (NAU7802 via TCA9543A): tare on boot, measure 500g calibration weight within +/-5g on both channels
- [ ] Load cells: track water evaporation over 30-minute simmer; I2C NACK / no data-ready raises the load-cell fault
- [ ] Dock sense: DOCK_SENSE_A edge reaches the RV1106 within 10 ms of lift; state machine enters PAUSED (UNIT_LIFTED); no auto-resume on re-dock
- [ ] Pot detection: reliably detects pot on/off

### 18.6 Dispensing (FID / CID / SLD)
- [ ] FID: Each canister doses ¼ tsp (1.23 mL) within ±10% per stroke
- [ ] FID: Jiggle routine clears a hand-packed canister without a stall
- [ ] FID: Steam gate closes by spring with servo unpowered
- [ ] CID: Each slot empties into the pot on index; cover sector closes aperture at home
- [ ] CID: Out-of-order slot command is NACKed, carousel does not move
- [ ] DSB: Stall detection (INA219 #1 window on 6V_DSP, RV1106 dispense thread) fires when a carousel is blocked by hand
- [ ] SLD: Each 6 V pump (TB6612, RV1106 PWM) dispenses 50g liquid within ±5%, stopping at 95 % of target on the NAU7802 loop
- [ ] SLD: 6 V solenoid valves seal (no drips when idle)
- [ ] Both exhaust fans (CSC J_FAN): PWM control from 0-100% via SET_EXHAUST over CAN, no audible whine
- [ ] Both exhaust fans: Independent control verified (each can run separately); GET_EXHAUST reports duty and rpm
- [ ] Buzzer: All alert patterns audible and distinct
- [ ] No cross-contamination between subsystems
- [ ] Unified PCB and CSC: All subsystem signal routes verified on-board; STM32 free pins and the unpopulated I2C1 pads confirmed on the CSC

---

## 19. Safety Considerations

### 19.1 Electrical Safety

- **Galvanic Isolation:** The electric heating unit is a self-contained AC unit — no mains voltage reaches the CSC or the Unified PCB. The two ISO1050DUB isolated CAN transceivers (one per board: #1 on the CSC behind J_CAN_HEAT, #2 on the Unified PCB behind the dock) provide 5 kV RMS galvanic isolation between the heater CAN bus and the logic, in one 5V_ISO domain made on the CSC. The isolated bus crosses the dock on pins 3–6; the DU logic ground joins the CS ground only through dock pin 2. The stir-motor CAN bus (J_CAN_STIR) is not isolated: the motor shares the 24 V PSU ground. PSU provides transformer-isolated DC outputs.
- **Undock:** Lifting the DU opens the bus and the 24 V together: the unit drops to zero ≤ 1 s (keep-alive), the STM32 holds safe on DOCK_SENSE_B, and the dock pads are de-energised by Q_DOCK so no live 24 V is exposed on the pillar.
- **Battery Safety:** 2S Li-ion pack with per-cell protection (PCM), NTC-gated charging (0–45 °C); the pack now lives in the DU, away from the heat; IEC 62133-2 / IS 16046 cells.
- **Earth Bonding:** Metal enclosure parts of the CS connected to AC earth via IEC C14 inlet. Chassis ground bonded to PSU earth.
- **Fuse Protection:** 10A ceramic fuse in IEC C14 inlet. Polyfuses on the CSC 24 V input (F1 5 A), the stir feed (F_STIR 5 A), the dock feed (F_DOCK 2 A) and 5V_ISO (F_CAN 100 mA); 3 A PTC on 6V_DSP.

### 19.2 Thermal Safety

- **Unit Thermal:** The heating unit has an internal over-temperature cut-off and thermal fuse. It reports element temperature via CAN status. The plate stores heat after power-off; the UI shows a hot-surface warning while surface_temp is above 60C.
- **Surface Over-Temperature:** The unit's centre sensor reports the pot-bottom temperature (surface_temp) in HEAT_STATUS. If >230C (unit ceiling 200C; >220C raises CRITICAL first), the STM32 sends the CAN off command and opens the safety relay, independently of the unit's internal cut-off.
- **Enclosure Thermal:** Exhaust fans on the CSC provide ventilation of the CS. The unit reports its element temperature via CAN for enclosure monitoring.

### 19.3 Mechanical Safety

- **E-Stop Button:** Red mushroom-head button on the Cooking Surface front panel, wired to the CSC (STM32 PB2 interrupt via J_SAFE 3) AND the safety relay. Pressing E-stop: (1) STM32 sends HEAT_ON_OFF=0 and broadcasts E_STOP on the isolated CAN bus, (2) relay disconnects AC to the heating unit, (3) stir motor disabled on FDCAN2 and its 24 V removed (Q_STIR). The DU's UI has a soft stop that broadcasts E_STOP over CAN while docked; on receipt the RV1106 also drops PCA9685 OE so the DSB servos go limp.
- **Pot Detection Interlock:** Handled internally by the heating unit: the pot presses the spring-loaded centre sensor and the unit reports `pot_detected`; it will not heat without a pot. Status reported via CAN.
- **Pinch Protection:** Arm mechanism has limited torque (current limit set in the CAN servo, reported current monitored by the STM32). Arm speed limited in firmware to prevent splash/injury.
- **Lift Safety:** The DU is ≤ 4 kg fully loaded (two-hand lift) and only seats one way on the keyed dock recess; a mis-seated unit leaves DOCK_SENSE_A/B open, so nothing powers up.

### 19.4 Overcurrent Protection

- **Mains:** 10A fuse (IEC C14)
- **DC Rails:** PTC self-resetting fuses on each rail of the CSC and the Unified PCB
- **Heating Unit:** Internal thermal fuse and over-temperature cut-off (unit-handled)
- **Servos:** 3 A PTC on 6V_DSP plus the INA219 #1 stall window in the dispense thread

---

## 20. Related Documentation

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

## 21. Revision History

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
| 8.4 | 2026-11-04 | Manas Pradhan | Heater changed from the commercial induction surface to a commercial electric heating unit of the premium rice-cooker class (resistive plate, spring-loaded centre sensor, own relay/triac power stage, own PID, CAN port); drop-in CAN node — HEAT_* messages, J_CAN_HEAT, dock, CSC, Unified PCB, `epicurad` and STM32 firmware unchanged. Power 1,800 W → 1,300 W (assumed, unit TBD), pot detection by the centre sensor (no ferromagnetic pot), `coil_temp` → `element_temp`; unit table, block diagrams, component list, §10, §12, EMI (§16.1 — no induction field, ferrite sheet dropped), thermal, power budget (system ~470 W / ~1,350 W peak), BOM (heater $60 → $45, total $635-745), checklist and safety updated |
| 8.5 | 2026-11-04 | Manas Pradhan | Reference unit fixed: Philips OneChef NX5300/00 — donor body is the Cooking Surface, 6 L non-stick pot, DU seats in the air-fryer lid position; §12 notes the 2,280 W nameplate (base plate 1,000–1,300 W, planning 1,300 W), 200 °C ceiling, STM32 surface_temp limits 220 °C CRITICAL / 230 °C E_STOP (were 270) and the Case A / Case B CAN-board risk; BOM heater $45 → $230 donor cooker, $25 pot line removed, total $635-745 → $795-905; checklist items added |
| 8.3 | 2026-11-04 | Manas Pradhan | Three-unit physical architecture: Cooking Surface (CS: induction module, LRS-75-24, new Cooking Surface Controller PCB with the STM32G0B1RE, relay, E-stop, fans), Stirring Unit (SU: 24 V CAN servo on J_SU, the only inter-unit cable) and Dispensing Unit (DU: Unified PCB v4.0 with the Pico Zero, 2S pack as primary supply, dispensers, camera + white LED ring on the underside). New §8 dock (J_DOCK, 8-pin magnetic pogo: DOCK_24V via Q_DOCK, isolated CAN pins 3–6, DOCK_SENSE_A/B) and undock behaviour; STM32 pin box rewritten for the CSC (PB3 DOCK_SENSE_B, PB4 Q_STIR, PB5 Q_DOCK, no I2C/dispensing); UART service link and BOOT0/NRST replaced by the CAN bootloader (0x7E0/0x7E8) + USB DFU; dispensing moved to the RV1106 over I2C3/PWM (PCA9685, PCF8574 #2, TB6612 on 6 V, NAU7802 ×2 via TCA9543A replace the HX711, INA219 #2 on the pack); WS2812B + 74AHCT1G125 replaced by a white PWM ring; 6.5 V DSB rail → 6.0 V, pumps/solenoids re-specified 6 V, D_DSB4 dropped, TP5100 at 1.0 A; CAN map: SET_LED, dispensing block and LOADCELLS removed, SET_EXHAUST/GET_EXHAUST/EXHAUST_AUTO and FW_UPDATE added, DU_UNDOCKED fault; block diagram, component list, header table, power (split per unit), induction, routing, ground, BOM ($650-760), checklist and safety updated; sections 8–20 renumbered 9–21 |
