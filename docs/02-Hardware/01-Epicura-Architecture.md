---
created: 2026-02-15
modified: 2026-11-05
version: 8.13
status: Draft
---

# Epicura Hardware Architecture & Wiring Diagrams

## 1. Overview

This document provides the comprehensive hardware architecture, wiring diagrams, and interface specifications for the Epicura autonomous kitchen robot. The system uses three controllers: a Rockchip RV1106G3 (Luckfox Pico Zero) running Buildroot Linux for AI/vision/UI/recipe logic, and two STM32G0B1 microcontrollers running FreeRTOS — the **DU STM32** on the Unified PCB (dispensing, LED ring, buzzer, battery/dock monitor, DU CAN node and host-link gateway for the RV1106) and the **CSC STM32** in the base (stirring motor, exhaust fans and safety). There is no IR thermometer: the cooking surface runs its own temperature loop and reports its temperature over CAN.

Epicura is physically **three units** with two boards:

| Unit | Short | Mains? | Contents |
|------|-------|--------|----------|
| **Cooking Surface** | CS | Yes (IEC C14 inlet, fuse, EMI filter) | Donor Philips OneChef NX5300/00 body (heating plate, controller with own AC + CAN; air-fryer lid removed — the DU seats in its place; its round inner pot and glass lid are set aside), 25 × 25 × 12 cm rounded-square rounded-square non-stick pot (6 L max fill) in an opened-out well, three Mean Well PSUs (LRS-75-24 #1 DU via the dock; LRS-75-24 #2 SU with a floating output; LRS-35-12 for the controller), **Cooking Surface Controller PCB (CSC, STM32G0B1RE)** powered by its own LRS-35-12 (J_12V_IN), safety relays K_SAFE (heating unit AC inlet) and K_SU (SU PSU), E-stop button (front), 2× exhaust fans + filter cartridge (rear), two rear pillars that carry the stirring unit and the dock block |
| **Stirring Unit** | SU | No — fed 24 V by its own PSU (LRS-75-24 #2 in the CS, floating 24V_SU / GND_SU, AC input through K_SU) | Gantry bridge between the rear pillars over the pot: 24 V CAN servo stir motor, vertical shaft, paddle, fume hood. One port **J_SU** at the pillar; harness inside the right pillar to the CSC |
| **Dispensing Unit** | DU | No — **battery is the primary supply** | **Ø350 mm disc, ≤ 150 mm tall** (2026-11-05). **Unified PCB v5.3** (annular-sector board in the outer service ring: Pico Zero in J_AP, DU STM32G0B1RE, dispenser drivers, DU CAN node), 2S2P Li-ion pack, 4" LCD on the front face (tilted 15–30°), IMX415-98 camera + white LED ring in the hub on the underside looking straight down into the pot, FID ring (inner) + CID ring (outer), SLD oil (200 mL) + water (500 mL) drawer tanks in the service ring with the pumps in the body (Hall tachs) and check-valve nozzle cartridges through the underside, buzzer. Dock pads on the underside over the left pillar |

Only one cable exists between units (CS → SU, inside the right pillar). The DU lifts straight off with no cable: it docks onto the CS left pillar through an 8-contact magnetic pogo connector (**J_DOCK**) that carries charge (24 V) and the isolated CAN bus. The DU lifts off to load ingredients and to clean individual coarse slots between sessions; on a mains outage the DU (the brain) keeps running on its battery and the session resumes when mains returns. Footprint 500 × 400 mm (set by the donor body and the pillars); CS ≈ 110 mm high, DU a Ø350 mm disc ≤ 150 mm high on top (robot-vacuum form factor with concentric dispensers, [[04-Mechanical-Design|Mechanical Design]] §4.2), overall ≈ 370 mm (to be confirmed); DU mass target ≤ 4 kg fully loaded (two-hand lift); camera-to-pot-rim distance 20–30 cm.

---

## 2. System Block Diagram

```
  ┌──────────────────────────── DISPENSING UNIT (DU) — lifts off, battery primary ─────────────────────────────┐
  │                                                                                                              │
  │   Unified PCB v5.3 (annular sector)                                                                          │
  │   VSYS = DOCK_24V ⊕ BAT+ (SS54) → TPS54531 → 5V_MAIN → AMS1117 → 3.3 V;  VSYS → MP1584EN #2 → 6V_DSP (switched)│
  │   DOCK_24V → MP1584EN #1 → 12 V → TP5100 (1.0 A) → 2S Li-ion pack (J_BAT, INA219 #2)                          │
  │                                                                                                              │
  │   ┌───────────────────────┐        ┌───────────────────────────┐  I2C1 ┌──────────────────────────────────┐ │
  │   │  Luckfox Pico Zero    │ UART2  │  DU STM32G0B1RE (FreeRTOS)│──────►│ PCA9685 0x41 → DSB servos ×4     │ │
  │   │  RV1106G3 (Buildroot) │◄──────►│  USART1 (921,600, COBS)   │       │ PCF8574 #2 0x21 → pump DIR ×2,   │ │
  │   │                       │ host   │  - Link/Gateway task      │       │   6V_DSP en, CHRG/STDBY in       │ │
  │   │  - Recipe Engine      │ link   │  - Dispense task (50 Hz)  │       │ Hall ×6: tank low/present, tachs │ │
  │   │  - CV Inference (NPU) │        │  - Monitor (battery/dock) │       │ INA219 #1 0x40 · INA219 #2 0x44  │ │
  │   │  - UI Rendering (LVGL)│ GPIO   │                           │  TIM  └──────────────────────────────────┘ │
  │   │  - Dispense client    │ 32/38 ►│  BOOT0 / NRST             │──────► TB6612 pumps ×2 · LED ring (Q_LED) │
  │   │  - Cloud/WiFi/BT/OTA  │        │  PB3/PB5 ◄── DOCK_SENSE_A,│        · buzzer                           │
  │   │  - Heater setpoints   │        │              DOCK_PWR_OK  │  FDCAN1 ┌─────────────────────────────┐    │
  │   │  CSI-2 → IMX415 8 MP  │        │                           │────────►│ SN65HVD230 (DU CAN node,    │    │
  │   │  (underside, down)    │        └───────────────────────────┘         │ 3.3 V, DU GND; no isolation)│    │
  │   │                       │  SPI0  ┌─────────────┐  I2C3 ┌──────────┐    └──────────────┬──────────────┘    │
  │   │                       │───────►│ 4" ST7796S  │──────►│ FT6336   │                   │                   │
  │   └───────────────────────┘        │ 480×320     │       │ touch    │                   │                   │
  │   WiFi 6 / BLE 5.2 · eMMC 8 GB     └─────────────┘       └──────────┘                   │                   │
  │                                                     J_DOCK pads (8) ───┼────────────────┘ 24V, GND, sense   │
  └────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┘
                              8-pin magnetic pogo dock on the CS left pillar│ (CAN_H, CAN_L, GND_ISO→DU GND, 5V_ISO reserved)
  ┌────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┐
  │  COOKING SURFACE (CS) — mains                                           │                                    │
  │                                                                         │                                    │
  │  AC Mains 220-240 V ──► IEC C14 + fuse + EMI filter ──┬──► Mean Well LRS-75-24 #1 (24 V / 3.2 A, DU only)   │
  │                                                       │                 │                                    │
  │                                                       ├──► Mean Well LRS-35-12 (12 V / 3 A) ──► CSC J_12V_IN │
  │                                                       ├──► K_SU (PB4) ──► LRS-75-24 #2 (24 V, SU, floating) │
  │                                                       └──► K_SAFE (PB0) ──► Electric Heating Unit (AC inlet)│
  │                                                            (own AC, own PID, CAN node HEAT; not opened —     │
  │                                                             only its CAN port is used, nothing is tapped)    │
  │  ┌──────────────── Cooking Surface Controller (CSC, ~100 × 70 mm) ──────┼──────────────────────────────┐     │
  │  │  J_12V_IN ── 12V_IN (fans, relay coils) ── MP1584EN → 5 V → 3.3 V · B0505S #1/#2 → 5V_ISO/5V_ISO2   │     │
  │  │  J_DU_IN ── 24V_DU (LRS #1, −V bonded to GND) ──► Q_DOCK only        │                              │     │
  │  │  ┌─────────────────────────┐   FDCAN1 ──► ISO1050DUB #1 ──┬── J_CAN_HEAT (120 Ω) ──► heating unit    │     │
  │  │  │  STM32G0B1RE (FreeRTOS) │                              └── J_DOCK pins 3–5 ──► DU (stub ≤ 30 cm)   │     │
  │  │  │  - Stir motor (FDCAN2)  │   FDCAN2 ──► ISO1050 #3 ──► J_CAN_STIR ─┐                               │     │
  │  │  │  - Safety monitor       │   J_SU_IN (LRS #2) ─ F_SU ─► J_STIR_PWR ─┤ harness in the right pillar   │     │
  │  │  │  - Thermal / fans       │   PB5 ──► Q_DOCK (24 V) ──► J_DOCK pin 1 │                               │     │
  │  │  │  - CAN comms (FDCAN1)   │   PB0 ──► relay · PB2 ◄── E-stop · PB3 ◄── DOCK_SENSE_B · PA6/PB10 ──► fans│     │
  │  │  └─────────────────────────┘   J_SWD · J_USB (DFU, bench) · J_DBG      │                               │     │
  │  └───────────────────────────────────────────────────────────────────────┼───────────────────────────────┘     │
  │  E-stop button (front) · 2× 120 mm exhaust fans + filter (rear)           │                                    │
  └───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┘
                                                                              │ J_SU (Micro-Fit 3.0, 5-way) — the only inter-unit cable
  ┌───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────┐
  │  STIRRING UNIT (SU) — gantry between the rear pillars                      ▼                                    │
  │  24V_SU + isolated CAN (1 Mbps) ──► 24 V CAN servo stir motor ──► vertical shaft ──► paddle · fume hood         │
  └────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Main Component List

| Component | Part Number | Interface | Connected To | Purpose |
|-----------|-------------|-----------|--------------|---------|
| Compute Module | Luckfox Pico Zero (RV1106G3) | 40-pin header / CSI / USB-C | Unified PCB v5.0 slot J_AP (2x20 socket + 4 standoffs), in the DU | AI/vision (NPU), recipe engine, heater setpoints, LVGL UI, networking; commands dispensing through the DU STM32 |
| Unified PCB v5.3 | Annular sector R 135–172 mm × ≈ 150° (TBC), 4-layer | - | Dispensing Unit (outer service ring) | Hosts the Pico Zero, the DU STM32, the DU CAN node, the battery charger, the dispenser drivers and the dock pads |
| DU STM32 | STM32G0B1RET6 (LQFP-64) on the Unified PCB v5.0 | USART1 host link (RV1106 UART2, 921,600 baud), FDCAN1, I2C1, TIM PWM, GPIO | RV1106 (UART2 + BOOT0/NRST), SN65HVD230, every dispenser driver, LED ring, buzzer, INA219 ×2, dock sense | DU CAN node and transparent host-link gateway for the RV1106; dispensing (FID/CID/SLD), LED ring, buzzer, battery/dock monitor. No safety authority |
| CAN Transceiver (DU node) | SN65HVD230 (3.3 V, non-isolated) | DU STM32 FDCAN1 (PB8/PB9) | Unified PCB; referenced to the DU logic ground, which dock pad 5 (GND_ISO) is tied to | Puts the DU (RV1106 behind the DU STM32 gateway, node AP) on the CSC's isolated CAN port 1; the barrier for this bus is the ISO1050 #1 on the CSC |
| Cooking Surface Controller (CSC) | ~100 × 70 mm, 4-layer PCB with STM32G0B1RE (LQFP-64) | - | Cooking Surface base, beside the three Mean Well PSUs; powered by its own LRS-35-12 (J_12V_IN) | Real-time control: stirring motor, exhaust fans, relays (K_SAFE, K_SU), E-stop, dock power switch; isolated CAN node (FDCAN1) and isolated stir-motor CAN master (FDCAN2); floating pass-through of the SU's 24 V |
| Dock Connector | 8-contact magnetic pogo pair, 2.54 mm pitch, 2 A per pin (J_DOCK) | DOCK_24V, GND, CAN_H/L, GND_ISO (tied to DU GND), 5V_ISO (reserved), DOCK_SENSE_A/B | Spring pins in a keyed recess on the CS left pillar (harness to the CSC); gold pads on the DU underside (Unified PCB) | Charge + isolated CAN between the CS and the DU; dead when the DU is lifted |
| Camera Module | IMX415-98 IR-CUT (8 MP) | MIPI CSI-2 (4-lane FPC) | Pico Zero CSI connector; DU underside, centred over the pot behind a sealed borosilicate window | Overhead food monitoring, CV inference |
| Stirring Motor | 24V integrated BLDC servo with CAN (CyberGear/RobStride-class, model TBD) | CAN 2.0B 1 Mbps (isolated port #2) + 24V_SU from its own PSU | STM32 FDCAN2 (PB12/PB13) via ISO1050DUB #3 → J_CAN_STIR; 24V_SU from LRS-75-24 #2 via J_SU_IN → F_SU → J_STIR_PWR; both bundled to J_SU on the SU pillar | Stirring arm rotation with encoder feedback |
| Stir-Motor CAN Transceiver | ISO1050DUB #3 + B0505S-1WR3 #2 (5V_ISO2 / GND_SU) | FDCAN2 | CSC, isolated CAN port #2 on the floating SU island | Isolated CAN port to the stirring motor; GND_SU is never bonded to the CS ground |
| Dispenser Servos (DSB) | DS3218 270° (C1), MG996R (F1, F2), MG90S (F3) | 50 Hz PWM via PCA9685 | PCA9685 CH0-CH3 → J_DSB1-4, all on the switched 6.0 V rail (6V_DSP) | CID carousel index (C1); FID carousel index, dose, steam gate (F1-F3) |
| PCA9685 Servo Driver (DSB) | PCA9685PW | I2C | DU STM32 I2C1 addr 0x41, OE on DU STM32 PB0 | Single PWM control block for FID + CID servos |
| SLD Hall Switches | 6× digital Hall switch (AH3572-class): pump tach ×2, tank present ×2, tank low ×2 (float magnet) | Digital GPIO | DU STM32 PC0–PC5 via J_SLD (tachs on EXTI0/1, present on EXTI2/4, low polled) | Open-loop liquid metering (pulses × calibrated mL/pulse), prime arming, level and tank-absent alerts (replace the NAU7802 load cells, 2026-11-05) |
| Current Monitors | INA219 ×2 | I2C | DU STM32 I2C1: #1 0x40 (6V_DSP rail shunt), #2 0x44 (10 mΩ in the BAT+ path) | Servo stall detection; battery voltage, current and state of charge |
| SLD Pumps | 6 V peristaltic (oil, ≈ 0.4 mL/rev) + 6 V diaphragm (water, ≈ 1 L/min), in the DU body under the drawer-tank bays, via TB6612 (VM on 6V_DSP) | PWM (DU STM32 TIM3) + DIR (PCF8574 #2 P3/P5) | Unified PCB | Oil and water dispensing from the 200 mL / 500 mL drawer tanks |
| SLD Nozzle Check Valves | Spring poppet ≈ 5 kPa in each snap-out nozzle cartridge (x2), passive | — | DU underside | Drip, siphon and steam blocking (replace the 6 V solenoid valves, 2026-11-05) |
| Exhaust Fans | 2× 120mm 12V DC brushless | PWM (25kHz) | STM32 PA6, PB10 via MOSFET → J_FAN on the CSC | Fume extraction, independent control; rear of the CS with the filter cartridge |
| Piezo Buzzer | 5V active | PWM | DU STM32 TIM14 PWM via 2N7002 → J_BUZZER (Unified PCB) | Audio alerts |
| USB-C Receptacle | Mid-mount 16-pin (J_USB on the CSC) | USB 2.0 FS | STM32 PA11/PA12 (native USB) | DFU programming, CDC serial debug (bench only) |
| Li-Ion Battery | 2S2P 18650 pack, 7.4V, 5,200 mAh (~38 Wh), with PCM + NTC (JST-XH 3-pin, J_BAT) | Analog | TP5100 charger (1.0 A) + VSYS diode-OR on the Unified PCB; monitored by INA219 #2 | **Primary supply of the DU**: ≈ 3 W lifted-unit load → > 12 h; docked, the DU draws from DOCK_24V and the pack does not discharge |
| Electric Heating Unit | Philips OneChef NX5300/00-class unit (donor body; 25 cm rounded-square pot, Mechanical Design §2.2) w/ OEM CAN control board and internal temperature control, 1,300 W (assumed; base plate of the 2,280 W nameplate) | CAN 2.0B (500kbps) | Isolated CAN port J_CAN_HEAT on the CSC (STM32 FDCAN1); the DU STM32 (gateway for the RV1106) joins the same bus over the dock; nothing is tapped from the unit (its internal wiring and control-board supply are untouched) | Self-contained resistive heating plate with internal relay/triac power stage, spring-loaded centre sensor, PID and safety; setpoints from the RV1106, forced off by the STM32 (K_SAFE on its AC inlet loom) |
| 4" Touchscreen | 4" 480x320 IPS, ST7796S + FT6336 | SPI (LCD) + I2C (touch) | RV1106 SPI0 + I2C3; DU front face, tilted 15–30° | User interface display |
| PSU Modules | Mean Well LRS-75-24 ×2 (#1 DU, #2 SU) + Mean Well LRS-35-12 ×1 (CSC) | AC-DC 24V ×2, AC-DC 12V ×1 | AC mains input, in the CS rear; #2 through K_SU, the LRS-35-12 unswitched | #1: the Dispensing Unit's supply only — 24V_DU to the CSC (J_DU_IN), which hands it on as DOCK_24V over the dock through Q_DOCK and draws nothing from it (the CSC runs from the LRS-35-12); its −V is bonded to the CSC ground at J_DU_IN. #2: floating 24V_SU / GND_SU to J_SU_IN → F_SU → J_STIR_PWR for the SU, never bonded to the CS ground. LRS-35-12: 12 V, 3 A, 36 W to J_12V_IN — the CSC, both relay coils and the two fans (~1.3 A typical); its −V is the CSC ground; live whenever the appliance is on |
| Safety Relays | Omron G5V-2 or equiv. ×2 (12 V coil): K_SAFE, K_SU | GPIO (via MOSFET) | STM32 PB0 → Q_RLY → J_SAFE pin 1 (K_SAFE); STM32 PB4 → Q_KSU → J_SAFE pin 5 (K_SU) on the CSC | Heating unit AC disconnect (K_SAFE, on the unit's AC inlet loom; the CSC stays up on its own PSU); SU PSU AC disconnect (K_SU) |
| LED Ring | White LED ring, 12–16 LEDs, 5000 K, CRI ≥ 90 | PWM (1 kHz) | DU STM32 TIM1 PWM → Q_LED (IRLML6344 low-side) → J_LED (5V_MAIN / LED_RET) | Pot illumination for camera, on the DU underside around the lens |
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

The Pico Zero is a complete single-board module: no carrier board is needed. It seats pin-down into the Unified PCB v5.0's slot **J_AP** (2x20 socket, four M2.5 standoffs on the module's 3.0 mm holes) in the Dispensing Unit for 5V power and all logic signals. The camera attaches to the module's CSI connector directly; the display's SPI0/I2C3 lines are routed through the PCB to a 14-pin break-out (J_LCD). Its only link to the rest of the machine is the **host link** to the DU STM32 on the same board: UART2 (header pins 8/10) ↔ STM32 USART1 at 921,600 baud, plus GPIO 32 → BOOT0 and GPIO 38 → NRST so the RV1106 can flash the DU STM32 through the ST system bootloader. The DU STM32 is the DU's CAN node and forwards the RV1106's bus traffic transparently (§10); the RV1106 itself has no CAN controller, no I2C peripheral other than the touch controller, and drives no dispenser.

```
┌───────────────────────────────────────────────────────────────┐
│              Luckfox Pico Zero (RV1106G3)                     │
│                                                               │
│  MIPI CSI (FPC) ──► IMX415 camera module (4-lane, underside)  │
│  SPI0 ──────────► 4" ST7796S LCD (fbtft, 50 MHz, DMA) on CS0  │
│                   (CS1 unused)                                │
│  I2C3 ──────────► FT6336 touch only                           │
│  PWM10 ─────────► LCD backlight                               │
│  UART2 ◄───────► DU STM32 USART1 — host link, 921,600 baud,   │
│                   COBS/CRC framed CAN-shaped frames (§10)     │
│  GPIO 32 / 38 ──► DU STM32 BOOT0 / NRST (system bootloader)   │
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
| 19 (SPI0_MOSI) | LCD MOSI | Output | 50 MHz, fbtft with DMA |
| 21 (SPI0_MISO) | LCD MISO | Input | Reserved (fbtft is write-only) |
| 23 (SPI0_CLK) | LCD clock | Output | 50 MHz |
| 24 (SPI0_CS0) | LCD chip select | Output | Active-low; SPI0_CS1 (GPIO 58) is unused since v5.0 (the MCP2518FD is gone) |
| 22 (GPIO) | LCD DC (data/command) | Output | |
| 26 (GPIO) | LCD RST | Output | |
| 12 (PWM10) | LCD backlight PWM | Output | Dimmable |
| 16 (I2C3_SDA, M0) | I2C3 SDA — touch only | Bidirectional | 400 kHz, 4.7k pull-ups to 3.3 V. Device: FT6336 touch 0x38 (via J_LCD). Every other I2C device of the DU is on the DU STM32's I2C1 (§5.3) |
| 18 (I2C3_SCL, M0) | I2C3 SCL | Bidirectional | as above |
| 36 (GPIO) | Touch INT | Input | Active-low, evdev |
| GPIO (fixed at layout) | Touch RST | Output | |
| 8 (UART2_TX, M1) | Host link TX → DU STM32 USART1 RX (PA10) | Output | 921,600 baud 8N1, 33R series; `/dev/ttyS2`, `epicurad` `link` thread |
| 10 (UART2_RX, M1) | Host link RX ← DU STM32 USART1 TX (PA9) | Input | as above |
| GPIO 32 | DU STM32 BOOT0 | Output | 10k pull-down on the PCB; driven high only for a firmware update |
| GPIO 38 | DU STM32 NRST | Output (open-drain) | 10k pull-up + 100 nF on the PCB; pulsed low to reset the DU STM32 |
| 35 / 37 (UART0, M0) | Debug console TX / RX | - | Luckfox default |
| CSI (FPC) | Camera data lanes | Input | 4-lane MIPI, IMX415-98 |
| Freed in v5.0 | SPI0_CS1, MCP2518FD INT, PCA9685 OE, DOCK_SENSE_A, DOCK_PWR_OK, PWM ×4 (pumps, LED ring, buzzer) | - | All moved to the DU STM32 (§5.3) |
| Spare | UART3, UART4, I2C1, I2C2, PWM, GPIO | - | Available |

Linux kernel drivers (all mainline in 5.10): `fbtft` (ST7796S), `edt-ft5x06` (touch), `pwm-rockchip` (backlight), 8250/DW UART for the host link. No CAN, no `pwm-pca9685`, `gpio-pcf857x`, `ina2xx`, `i2c-mux-pca954x` or `nau7802` drivers on the RV1106 any more: those devices hang off the DU STM32.

---

## 5. STM32 Cooking Surface Controller (CSC)

### 5.1 STM32G0B1RE Specifications

The STM32 now lives on its own board, the **Cooking Surface Controller (CSC) v1.0**: ~100 × 70 mm, 4-layer (isolation slot), in the Cooking Surface base beside the three Mean Well PSUs. It keeps only what belongs to the cooking surface: the isolated stir-motor CAN master, the isolated CAN node, the floating pass-through of the SU's 24 V, the safety relays (K_SAFE, K_SU), the E-stop, the exhaust fans and the dock power switch. Dispensing, sensing, the LED ring and the buzzer are on the DU STM32 (a second STM32G0B1RE, §5.3) on the Unified PCB in the Dispensing Unit. It runs from its own Mean Well LRS-35-12 (J_12V_IN), not from either LRS-75-24 and not from the heating unit. Its twelve connectors are J_12V_IN, J_DU_IN, J_SU_IN, J_CAN_HEAT, J_CAN_STIR, J_STIR_PWR, J_DOCK, J_FAN, J_SAFE, J_DBG, J_SWD, J_USB. FreeRTOS tasks: Motor Control 50 Hz (FDCAN2 stir servo), Safety Monitor 10 Hz, CAN Comms 20 Hz (FDCAN1), Thermal/Fan 1 Hz; the Dispense and Sensor Poll tasks are removed.

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
| Supply | 3.3V (CSC AMS1117-3.3 from the 5 V buck off 12V_IN, the LRS-35-12 rail; 5V_USB OR'd in on the bench) |
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
│  │  and J_DOCK pins 3–5 to the pillar dock block (DU STM32). │
│  │  500 kbps; nodes: DU STM32 (gateway for the RV1106, over  │
│  │  the dock),                                               │
│  │  STM32, heating unit MCU. Host commands + telemetry       │
│  │  + the CAN bootloader (0x7E0/0x7E8) ride this bus.        │
│  └─────────────────────────────────┘                         │
│                                                              │
│  ┌─── FDCAN2: Isolated bus #2 to the stirring motor ───┐     │
│  │  PB12 (FDCAN2_RX) ◄── ISO1050DUB #3 (bus side 5V_ISO2 /   │
│  │  PB13 (FDCAN2_TX) ──► GND_SU from B0505S #2) ──►          │
│  │                       J_CAN_STIR (JST-XH 3, pin 3 GND_SU) │
│  │  1 Mbps; velocity/position commands at 50 Hz, feedback;   │
│  │  120 Ω at J_CAN_STIR + in the motor                       │
│  │  J_SU_IN (XT30, 24V_SU / GND_SU from LRS-75-24 #2,        │
│  │  floating) ──► F_SU 5 A ──► J_STIR_PWR (XT30); the SU     │
│  │  island has no copper to the CS GND                       │
│  │  PB4  (GPIO)      ──► 2N7002 (Q_KSU) ──► K_SU (G5V-2 #2,  │
│  │                       12 V coil) ──► J_SAFE 5: AC input   │
│  │                       of LRS-75-24 #2; default OFF        │
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
│  │  disable, K_SU off, Q_DOCK off, STATUS DU_UNDOCKED)       │
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
│  │  PB0  (GPIO)      ──► Q_RLY (2N7002) ──► K_SAFE: Omron    │
│  │                       G5V-2 coil (12 V) ──► J_SAFE 1 (AC  │
│  │                       to the unit's AC inlet; NC: open)   │
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

### 5.3 Second Instance: DU STM32 on the Unified PCB

The same STM32G0B1RET6 is fitted a second time on the **Unified PCB v5.0** in the Dispensing Unit (added 2026-11-04). It exists because the Pico Zero header cannot drive the camera, LCD, SLD, CID and FID cleanly: the DU STM32 takes every dispenser, the LED ring, the buzzer and the battery/dock monitor, and is the DU's CAN node, acting as a transparent gateway between the RV1106's UART host link and the isolated bus. On the bus it is still node **AP (src_node 3)**; the CAN ID map is unchanged. It has **no safety authority**: it never originates HEAT_ON_OFF or E_STOP, only forwards the RV1106's. Its one safety-adjacent rule is local: no HB_AP from the RV1106 for 5 s → dispensers off (6V_DSP off, PCA9685 OE high, pumps off) and LED ring off. `epicura-firmware` builds it as a second image (`du`) from the same tree as the CSC (`csc`): same HAL, FreeRTOS, MISRA C, CAN codec and Class B start-up self-tests. Tasks: Link/Gateway (event-driven, USART1 DMA + FDCAN1 RX FIFO, COBS codec, ID routing, ≤ 5 ms), Dispense (50 Hz while a move is active), Monitor (1 Hz + EXTI → DU_STATUS). Board detail: [[../../../epi-Design/PCB/01-Unified-PCB-Design|Unified PCB Design]]; requirements: [[../03-Software/05-MCU-Functional-Specification|MCU Functional Specification]] §10; host-link protocol: [[../03-Software/02-Controller-Software-Architecture#7.4 Host Link (RV1106 ↔ DU STM32)|Controller Software Architecture §7.4]].

| Pin | Function | Signal | Circuit |
|-----|----------|--------|---------|
| PA9 / PA10 | USART1 TX / RX | HOST_TX / HOST_RX | ↔ J_AP pin 10 (UART2 RX) / pin 8 (UART2 TX); 33R series; 921,600 baud; also the ST system-bootloader UART |
| PA14 (SWCLK/BOOT0) | BOOT0 | BOOT0 | ← J_AP GPIO 32, 10k pull-down |
| NRST | reset | NRST | ← J_AP GPIO 38 (open-drain), 10k pull-up, 100 nF |
| PA13 / PA14 | SWDIO / SWCLK | SWD | J_SWD 2x5 1.27 mm (bench) |
| PB8 / PB9 | FDCAN1 RX / TX | CAN | SN65HVD230 R / D (Rs 10k to GND) → dock pads 3–4; no isolation on the DU, the barrier is ISO1050 #1 on the CSC |
| PB6 / PB7 | I2C1 SCL / SDA | I2C1 400 kHz | PCA9685 0x41, PCF8574 #2 0x21, INA219 #1 0x40, INA219 #2 0x44; 4.7k pull-ups |
| PA6 / PA7 | TIM3_CH1 / CH2 | PWM_PUMP_OIL / PWM_PUMP_WATER | TB6612 PWMA / PWMB via 100R, 20 kHz |
| PA8 | TIM1_CH1 | PWM_LED | Q_LED gate (IRLML6344) via 100R, 1 kHz |
| PA4 | TIM14_CH1 | PWM_BUZZER | Q_BUZZ gate (2N7002) via 100R, 2–4 kHz |
| PB0 | GPIO out | PCA9685_OE | 10k pull-up (servos off at boot / in reset) |
| PB3 | GPIO EXTI | DOCK_SENSE_A | J_DOCK pad 7, 10k pull-up, low = docked |
| PB5 | GPIO EXTI | DOCK_PWR_OK | Q_PWR drain, 10k pull-up, low = DOCK_24V present |
| PC7 | GPIO out | Status LED | green, 330R (PCF8574 #2 P2 freed → spare) |
| PF0 / PF1 | HSE | 8 MHz | Y1 + 2x 15 pF |
| PC14 / PC15 | LSE pads | — | unpopulated |
| PB12 / PB13 | FDCAN2 | — | unused on the DU (no regular CAN port) |
| PA11 / PA12 | USB | — | not used (no USB-C on the DU; the RV1106 flashes it over USART1) |

All PWM lines keep their 10k pull-downs. Power: 3.3 V rail (AMS1117), ≈ 30 mA (+0.1 W); the pack keeps it alive when the DU is lifted.

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
DU STM32 PA8 (TIM1_CH1, 1 kHz)
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

Note: The ring is driven by the DU STM32; epicurad sets the duty before
a capture with SET_LED (0x220) on the host link — a DU-local frame that
never reaches the CAN bus. No colour control.
```

---

## 7. Stirring Motor CAN Port (Isolated, Own Supply)

### 7.1 Wiring

```
STM32G0B1RE                  CSC (in the CS base)                             J_SU (pillar)    Stirring Unit (24 V CAN servo)
┌───────────────────┐        ┌─────────────────────────────┐                  ┌─────────────┐  ┌──────────────────────┐
│ PB13 (FDCAN2_TX) ─┼──► TXD │ ISO1050DUB #3 (5 kV)  CANH ─┼── J_CAN_STIR 1 ──┼── 3 CAN_H ──┼──┼ CAN_H                │
│ PB12 (FDCAN2_RX) ◄┼─── RXD │  bus side 5V_ISO2 /   CANL ─┼── J_CAN_STIR 2 ──┼── 4 CAN_L ──┼──┼ CAN_L  (120 Ω in     │
│                   │        │  GND_SU (B0505S #2) GND_SU ─┼── J_CAN_STIR 3 ──┼── 2 GND_SU ─┼──┼ GND     the motor)   │
│                   │        │  R_TERM2 120 Ω, PESD1CAN    │                  │             │  │                      │
│                   │        │ J_SU_IN 1 ─ F_SU ── 24V_SU ─┼── J_STIR_PWR 1 ──┼── 1 24V_SU ─┼──┼ +24 V                │
│                   │        │ J_SU_IN 2 ───────── GND_SU ─┼── J_STIR_PWR 2 ──┼── 2 GND_SU  │  │                      │
│                   │        │ floating SU island  shield ─┼──────────────────┼── 5 SHIELD  │  │                      │
│ PB4 ──► 2N7002 ───┼──► Q_KSU ──► K_SU (G5V-2 #2) ──► J_SAFE 5 ──► AC input of LRS-75-24 #2 (SU PSU) ──► J_SU_IN     │
└───────────────────┘        └─────────────────────────────┘                  └─────────────┘  └──────────────────────┘

Bus:      CAN 2.0B, 1 Mbps, 29-bit IDs (motor protocol); classic frames on FDCAN2, isolated by
          ISO1050DUB #3 (bus side 5V_ISO2 / GND_SU from B0505S #2, same parts as port #1)
Supply:   LRS-75-24 #2 in the CS rear, output floating (24V_SU / GND_SU, never bonded to the CS
          ground); AC input through K_SU; J_SU_IN → F_SU 5 A → J_STIR_PWR across the CSC's SU island.
          The only galvanic links between CS and SU are the ISO1050 barrier and the B0505S transformer
Port:     J_SU — Molex Micro-Fit 3.0, 5-way (24V_SU, GND_SU, CAN_H, CAN_L, SHIELD) at the pillar; the
          only inter-unit cable. The harness (J_CAN_STIR + J_STIR_PWR bundled) runs inside the right
          rear pillar from the CSC to J_SU; shield to GND_SU at the CSC end; nothing on it references
          the CS ground
Cable:    twisted pair ≤ 1 m to the gantry, bundled with the 24 V pair
Traffic:  50 Hz velocity (stir) / position (home, park) commands; 50 Hz feedback (rpm, angle,
          current, temperature, faults). Motor command timeout ≤ 500 ms configured at start-up.
Safety:   motor command timeout (≤ 500 ms) → STM32 stir disable frame on FDCAN2 → K_SU opens (SU PSU
          AC cut, motor de-energised within ~50 ms) on E-stop, heartbeat loss, FDCAN2 fault or DU undock
          (DOCK_SENSE_B open). K_SU is OFF at reset/boot; ~300 ms PSU start-up after it closes, the
          Motor Control task waits for the motor's boot frame.
```

### 7.2 Why a Second Bus

The stirring motor is the only node on this bus. It is kept separate from the isolated heater bus so that the heating unit's mains-side EMI domain never shares a transceiver with the motor, the 1 Mbps motor protocol does not load the 500 kbps host bus, and each port keeps its own galvanic barrier: port #1's to the mains-side unit, port #2's to the Stirring Unit, which runs from its own supply and whose ground must not tie to the CS ground.

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
| 5 | GND_ISO | CS → DU | Bus reference of the CSC's isolated port 1; **tied to the DU logic ground on the Unified PCB** (0 Ω link next to the pads) — this is the single point that references the isolated bus domain to the 24 V SELV ground |
| 6 | 5V_ISO | CS → DU | From the B0505S-1WR3 on the CSC, F_CAN 100 mA; **reserved — not connected on the DU board** (the DU transceiver runs from its own 3.3 V) |
| 7 | DOCK_SENSE_A | CS → DU | Tied to GND on the CS; 10k pull-up on the DU → DU STM32 PB3 (EXTI); low = docked; reported to the RV1106 in DU_STATUS (0x311) |
| 8 | DOCK_SENSE_B | DU → CS | Tied to GND on the DU; 10k pull-up on the CSC → STM32 PB3; low = DU present (enables Q_DOCK) |

The isolated bus domain (5V_ISO / GND_ISO) is generated once, on the CSC, and extended over dock pins 3–5; on the DU it is referenced to the DU logic ground at pad 5 and the DU transceiver is a plain SN65HVD230. The dock → Unified PCB run is a stub ≤ 30 cm off the terminated CSC ↔ module segment (see §10). On the DU, DOCK_PWR_OK (100k/10k divider on DOCK_24V → 2N7002 → DU STM32 PB5, active-low) tells the DU STM32, and through the DU_STATUS flags `epicurad`, whether the dock is actually delivering 24 V, independently of DOCK_SENSE_A.

### 8.2 Lift / Undock Behaviour

Lifting the DU opens the bus and the 24 V at the same instant. Nothing is latched on either side, so the sequence is passive and the same whether the lift is deliberate or accidental:

| Where | Trigger | Response |
|-------|---------|----------|
| Heating unit | HEAT_SET_TEMP / HEAT_SET_POWER keep-alive from the RV1106 stops (the AP is gone from the bus) | Drops to zero power ≤ 1 s after the last keep-alive (unit rule, unchanged) |
| STM32 (CSC) | DOCK_SENSE_B goes high | Immediate **safe hold**: HEAT_ON_OFF = 0, stir disable frame on FDCAN2, K_SU off (SU PSU de-energised), Q_DOCK off (pads de-energised), STATUS with fault 0x17 DU_UNDOCKED. Not an E_STOP. Back to NORMAL when DOCK_SENSE_B is low again and HB_AP returns |
| DU STM32 → RV1106 (DU) | DOCK_SENSE_A goes high (PB3 EXTI → DU_STATUS docked = 0, FDCAN1 bus-off → can_bus_ok = 0) | VSYS falls over to the 2S pack with no gap (Schottky-OR); state machine → PAUSED (reason UNIT_LIFTED); UI shows the battery indicator. Resume only by user tap after re-docking (no auto-resume); same 30 min food-safety ceiling as an AC outage |
| DU STM32 → RV1106 (DU) | DOCK_PWR_OK inactive (DU_STATUS dock_power = 0) while DOCK_SENSE_A still says docked, confirmed by TELEMETRY timeout (300 ms) | AC power failure: DU keeps running on its pack; auto-resume to RESUMING when TELEMETRY returns within 5 min (the STM32 reboots in < 1 s after mains returns), prompt if < 30 min, ERROR beyond |

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

## 10. Isolated CAN Bus (DU STM32 ↔ CSC STM32 ↔ Electric Heating Unit)

One isolated CAN 2.0B bus at 500 kbps connects three nodes: the DU STM32 (on the Unified PCB in the Dispensing Unit, node AP — the gateway for the Luckfox RV1106 behind it), the CSC STM32G0B1 (on the Cooking Surface Controller in the Cooking Surface, node STIR) and the electric heating unit's own MCU (node HEAT). The bus is the CSC's **isolated CAN port (J_CAN_HEAT)** to the unit, extended to the DU over dock pins 3–5 (Section 8); the stirring motor is on the separate regular port of Section 7. The RV1106 has no CAN peripheral: it reaches the bus through the DU STM32, which is a transparent gateway between the RV1106's UART host link (UART2 ↔ USART1, 921,600 baud, COBS/CRC-framed CAN-shaped frames) and its own FDCAN1 + SN65HVD230 (non-isolated, referenced to the DU logic ground); the CSC STM32 keeps FDCAN1 + ISO1050DUB #1, which is the only barrier on this bus. The gateway adds nothing and changes nothing on the bus, so the node names, the ID map and the CSC firmware are unchanged from the MCP2518FD design it replaces. The isolated domain (5 V_ISO and GND_ISO) is generated once, by the B0505S-1WR3 on the CSC, and referenced to the 24 V SELV ground at one point only: dock pad 5, tied to the DU logic ground on the Unified PCB (never on the CSC). The ISO1050 #1 is therefore a signal-reference / ground-loop barrier between the CSC logic ground and the bus, not a mains-safety barrier: the DU ground already meets the CS ground through dock pad 2. Mains safety rests on the Mean Well PSUs and on the heating unit's own board — **its CAN port must be SELV (isolated inside the unit from its mains-side electronics), a selection requirement** (§12.1). Termination is 120 Ω on the CSC at J_CAN_HEAT and 120 Ω inside the unit; the dock → Unified PCB run is a stub ≤ 30 cm. Lifting the DU opens the bus and the 24 V at the same instant. The heating unit runs its own temperature loop; the RV1106 sends setpoints and reads status (through the gateway), and the CSC STM32 can only force the heater off; the DU STM32 has no safety authority. Message IDs are owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]].

### 10.1 CAN Bus Wiring (Primary Link)

```
Luckfox Pico Zero (40-pin)    Unified PCB v5.0 (DU)                       J_DOCK         CSC (CS)                                 Electric Heating Unit
┌───────────────────┐    ┌───────────────────────────────────────┐    ┌─────────┐   ┌───────────────────────────────────┐   ┌────────────────┐
│ Pin 8  UART2_TX ──┼───►│ DU STM32 USART1 RX (PA10)              │    │         │   │ STM32 FDCAN1 ──► ISO1050DUB #1 ─┐ │   │  Onboard CAN   │
│ Pin 10 UART2_RX ◄─┼────│ DU STM32 USART1 TX (PA9)  921,600 baud │    │         │   │ PB8 RX / PB9 TX                 │ │   │  controller    │
│ GPIO 32 ──────────┼───►│ BOOT0      FDCAN1 ──► SN65HVD230 ────┐ │    │         │   │                                 │ │   │                │
│ GPIO 38 ──────────┼───►│ NRST       PB8 RX / PB9 TX   CANH ───┼─┼────┼ 3 CAN_H ┼───┼── CANH ─────────────────────────┼─┼───┼── CAN_H        │
│                   │    │                              CANL ───┼─┼────┼ 4 CAN_L ┼───┼── CANL ─────────────────────────┼─┼───┼── CAN_L        │
│                   │    │ DU GND ◄── 0 Ω ────────── GND_ISO ───┼─┼────┼ 5 GND_ISO───┼── GND_ISO ──────────────────────┼─┼───┼── GND          │
│                   │    │ (3.3 V, no isolation)  n.c. ◄────────┼─┼────┼ 6 5V_ISO┼───┼── 5V_ISO ◄── B0505S-1WR3 ◄── 5 V │ │   │  120 Ω term    │
│ Pin 24 SPI0_CS0 ──┼──► LCD (SPI0 is the LCD's alone)  (stub ≤ 30 cm)│    │         │   │ R_TERM1 120 Ω + PESD1CAN at     │ │   └────────────────┘
└───────────────────┘    └───────────────────────────────────────┘    └─────────┘   │ J_CAN_HEAT (JST-XH 4: H, L,     │ │
                                                                                     │ GND_ISO, 5V_ISO) ───────────────┘ │
                                                                                     └───────────────────────────────────┘

CAN Configuration:
  Bit rate:     500 kbps, CAN 2.0B, 11-bit IDs (classic frames on FDCAN1 of both STM32s)
  Nodes:        AP (DU STM32 as gateway for the RV1106, in the DU), STIR (CSC STM32), HEAT (module MCU, own PID)
  Isolation:    on the CSC only — ISO1050DUB #1 (bus side on 5V_ISO / GND_ISO from the B0505S-1WR3).
                The DU node is an SN65HVD230 on 3.3 V referenced to the DU logic ground; dock pad 5
                ties GND_ISO to that ground (the one reference point of the bus domain), pad 6 (5V_ISO,
                F_CAN 100 mA) is reserved and not connected on the DU. No isolation slot on the
                Unified PCB. The heating unit's CAN port must be SELV (selection requirement).
  Termination:  120 Ω at J_CAN_HEAT on the CSC and inside the module; the dock → Unified PCB run
                to the DU STM32 node is a stub ≤ 30 cm
  Dock:         the bus crosses the 8-pin magnetic pogo dock; lifting the DU opens the bus and the
                24 V together (Section 8.2); the DU STM32 goes bus-off and recovers on re-dock
  Host link:    RV1106 UART2 (pins 8/10) ↔ DU STM32 USART1, 921,600 baud 8N1, COBS-encoded frames
                {id16, dlc, data[≤8], crc16} — see Controller Software Architecture §7.4. Bus
                frames are forwarded unchanged in both directions; DU-local IDs (0x220 SET_LED,
                0x226 SET_BUZZER, 0x230–0x239 dispensing, 0x311 DU_STATUS, 0x3FE DU_ACK) stop at
                the DU STM32 and never appear on the bus. epicurad `link` thread (SCHED_FIFO) on
                /dev/ttyS2; no SocketCAN on the RV1106
  Cable:        shielded twisted pair ≤1 m from J_CAN_HEAT to the module; shield to GND_ISO at the
                CSC end only
```

### 10.2 STM32 Firmware Update (CSC over CAN, DU STM32 over USART1)

```
Luckfox Pico Zero (swupdate handler)     DU STM32 (gateway)        STM32G0B1RE on the CSC
┌──────────────────────────┐             ┌──────────────┐          ┌──────────────────────────────┐
│  epicurad streams the    │ 0x7E0 FW_UPDATE_REQ (host link → CAN) │  In-application CAN           │
│  CSC image over the      ┼────────────►┼ forwarded ───┼─────────►┼  bootloader (OpenBLT-style)   │
│  host link, through the  │ 0x7E8 FW_UPDATE_RSP (CAN → host link) │  ERASE / WRITE / VERIFY / BOOT│
│  DU STM32 and the dock   ◄┼─────────────┼ forwarded ◄──┼──────────┼  dual-bank flash, CRC check   │
│                          │             │              │          └──────────────────────────────┘
│  DU STM32 image: GPIO 32 ┼──► BOOT0    │ ST system    │
│  high, GPIO 38 reset     ┼──► NRST     │ bootloader   │
│  pulse, then the ST      ◄┼───────────►┼ on USART1    │
│  bootloader protocol     │  UART2      │ (PA9/PA10)   │
│  on UART2                │             └──────────────┘
└──────────────────────────┘

Update paths:
  CSC (field):   RV1106 → host link → DU STM32 gateway → isolated CAN bus (over the dock) →
                 in-application CAN bootloader. 0x7E0 FW_UPDATE_REQ (AP → STIR): seq, op
                 (ERASE/WRITE/VERIFY/BOOT), 5 data bytes. 0x7E8 FW_UPDATE_RSP (STIR → AP): seq, op,
                 result, 4 data bytes. Update mode only, lowest-priority IDs on the bus; the heater
                 and stir motor are idle during an update and the old image stays bootable until
                 VERIFY passes. Unchanged by the DU STM32: the gateway forwards 0x7E0/0x7E8 like any
                 other frame.
  CSC (bench):   USB-C J_USB on the CSC — ST USB DFU (SW_BOOT + SW_RST), also USB CDC console.
  CSC (factory): SWD via J_SWD (2×5 1.27 mm).
  DU STM32:      RV1106 drives GPIO 32 → BOOT0 high, pulses GPIO 38 → NRST, talks the ST system
                 bootloader protocol on USART1 (the host-link UART, 921,600 baud → bootloader
                 autobaud), verifies, releases BOOT0 and resets. No in-application bootloader and
                 no USB-C on the DU STM32; J_SWD on the Unified PCB is the bench path. The RV1106
                 holds the dispensers off (PCA9685 OE high, 6V_DSP off) during the update.
  CSC USART2:    (PA2/PA3) remains a local debug console on J_DBG; there is still no UART between
                 the CS and the DU — the units share only the CAN bus over the dock.
```

### 10.3 Message Map (CAN)

Identifiers are owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]; this table mirrors the blocks. Command frames carry a sequence byte first; ACK/NAK (0x3FF) echoes it. Node names are unchanged: AP = the DU (RV1106 behind the DU STM32 gateway, src_node 3), STIR = CSC STM32 (src_node 2), HEAT = heating unit.

> [!note] Host link (not on the bus)
> The RV1106 ↔ DU STM32 host link carries the same CAN-shaped frames plus a DU-local block that the DU STM32 terminates: 0x220 SET_LED, 0x226 SET_BUZZER, 0x230–0x239 dispensing (DISPENSE_FID/CID/SLD, SLD_PRIME, QUERY_SLD, PREFLIGHT, SLD_CAL, DISPENSER_HOME, DISPENSER_STATUS), 0x311 DU_STATUS (battery, dock, dispenser state, 1 Hz + on change) and 0x3FE DU_ACK/NAK. Definitions: [[../03-Software/02-Controller-Software-Architecture#7.4 Host Link (RV1106 ↔ DU STM32)|Controller Software Architecture §7.4]].

| CAN ID block | Messages | Direction | Notes |
|--------------|----------|-----------|-------|
| 0x001 | E_STOP | any -> all | src_node, reason_code; no ACK, highest priority |
| 0x010 | HB_AP | RV1106 -> all (via the gateway) | seq, uptime_ms; every 2 s, CSC safe state after 5 s without it; the DU STM32 also drops its dispensers after 5 s without it |
| 0x100–0x103 | HEAT_SET_TEMP, HEAT_ON_OFF, HEAT_QUERY, HEAT_SET_POWER | RV1106 -> module (STM32 sends HEAT_ON_OFF = 0 only) | Temperature setpoint (unit PID) or power 0–100 %, re-sent at 2 Hz as keep-alive; unit drops to 0 after 1 s without a refresh |
| 0x180–0x182 | HEAT_STATUS, HEAT_FAULT, HEAT_ACK | module -> all | Pot-bottom (centre sensor) temperature, element temperature, pot detection, faults (10 Hz); read by the RV1106 engine and the STM32 safety monitor |
| 0x202, 0x221–0x225 | SET_STIR, SET_SPEED, ARM_STOP, ARM_HOME, ARM_STATUS, SET_RAMP | RV1106 -> STM32 | Stirring arm block (see [[../05-Subsystems/02-Robotic-Arm|Robotic Arm]] §8.2). 0x220 SET_LED is not a bus message: it is a DU-local host-link frame to the DU STM32 |
| 0x260–0x262 | SET_EXHAUST, GET_EXHAUST, EXHAUST_AUTO | RV1106 -> STM32 | Exhaust fans on the CSC (codes 0x60–0x62 of [[../05-Subsystems/05-Exhaust-Fume-Management|Exhaust]] §3.4): SET_EXHAUST (seq, duty_pct); GET_EXHAUST (seq → ACK data duty_pct, rpm1, rpm2); EXHAUST_AUTO (seq, stage_id) |
| 0x310, 0x312 | TELEMETRY (20 Hz), STATUS | STM32 -> RV1106 | Motor rpm and current, safety state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok) and fault codes. 0x311 is not on the bus (it is DU_STATUS on the host link); STATUS fault_detail no longer carries batt_mV. Fault codes: 0x01–0x05, 0x10 STIR_STALL, 0x15 STIR_CAN_FAULT, 0x17 DU_UNDOCKED (Info), 0x20; 0x11–0x14, 0x16 and 0x21 are gone with the dispensers, battery and I2C |
| 0x3FF | ACK/NAK | STM32 -> RV1106 | seq, cmd_type, result_code, up to 5 data bytes |
| 0x7E0 / 0x7E8 | FW_UPDATE_REQ / FW_UPDATE_RSP | RV1106 <-> STM32 | CAN bootloader (§10.2); update mode only, lowest priority |

Not on the bus: 0x220 SET_LED, 0x226 SET_BUZZER and the 0x230–0x239 dispensing block (DISPENSE_FID/CID/SLD, SLD_PRIME, QUERY_SLD, PREFLIGHT, SLD_CAL, DISPENSER_HOME, DISPENSER_STATUS; see [[../05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]] §7.3). Dispensing, the SLD tank sensing, the LED ring and the buzzer are local to the DU: the same commands, names and semantics travel on the host link from the RV1106 `dispense` thread to the DU STM32, which executes them and answers with 0x3FE.

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
│  IEC C14 Inlet    │                    │  Electric Heating Unit   │
│  + Fuse (10A)     │ ─ AC via K_SAFE ──►│  (rice-cooker class)     │
│  + EMI Filter     │  (CSC J_SAFE 1,    │  OEM control board + PSU │
│  (X2 cap + CMs)   │   PB0; NC: open    │  — not opened, nothing   │
└────────┬──────────┘   = unit off)      │  tapped from it          │
         │                               │  1,300W max (assumed)    │
         │                               │  CAN bus, isolated: the  │
         │                               │  only link to the CSC    │
         │                               └──────────────────────────┘
         ├───────────────────────────────────────────────┬───────────────────────────────────────┐
         │                                               │ K_SU relay (CSC J_SAFE 5, PB4;        │ (unswitched: live
         ▼                                               ▼ NC: open = SU PSU off)                ▼  whenever on)
┌────────────────────────────────────┐  ┌────────────────────────────────────┐  ┌────────────────────────────────────┐
│  Mean Well LRS-75-24 #1 (DU)       │  │  Mean Well LRS-75-24 #2 (SU)       │  │  Mean Well LRS-35-12 (CSC)         │
│  24V / 3.2A / 76.8W                │  │  24V / 3.2A / 76.8W                │  │  12V / 3A / 36W                    │
│  Universal input: 85-264VAC        │  │  Output floating: 24V_SU / GND_SU  │  │  99 x 82 x 30 mm                   │
│  Efficiency: >87%                  │  │  never bonded to the CS ground     │  │  −V = CSC ground; the CSC, fans    │
│  PFC built-in                      │  │  (same part as #1)                 │  │  and relay coils, ~1.3 A typical   │
└────────────────┬───────────────────┘  └────────────────┬───────────────────┘  └────────────────┬───────────────────┘
                 │                                       │                                       │ 12V_IN (XT30)
                 │ 24V_DU (XT30, DU only)                │ 24V_SU (XT30, floating)               │ to J_12V_IN
                 ▼ J_DU_IN                               ▼ J_SU_IN                               │
┌───────────────────────────────────────────────────────────┐                                    │
│  Cooking Surface Controller — CSC (J_12V_IN, J_DU_IN,     │◄───────────────────────────────────┘
│  J_SU_IN)                                                 │
│  J_12V_IN ◄── 12V_IN from the LRS-35-12 (F1 2 A, SS34,    │
│     SMBJ12A, 100 µF; ~1.3 A typ / 1.4 A peak) ──► fans    │
│     J_FAN, K_SAFE + K_SU relay coils, 5 V buck            │
│  12V_IN ──► MP1584EN ──► 5V ──► AMS1117 ──► 3.3V (STM32,  │
│                          ISO1050 #1 + #3 logic)           │
│  5V  ──► B0505S #1 ──► 5V_ISO / GND_ISO (bus domain:      │
│                          J_CAN_HEAT + J_DOCK 5/6, F_CAN)  │
│  5V  ──► B0505S #2 ──► 5V_ISO2 / GND_SU (ISO1050 #3 bus   │
│                          side, on the SU island)          │
│  SU island (floating, no copper to the CS GND):           │
│  J_SU_IN ──► F_SU 5 A ──► J_STIR_PWR ──► J_SU ──►         │
│          Stirring Unit (24V_SU / GND_SU); K_SU (PB4,      │
│          J_SAFE 5) cuts the SU PSU's AC input             │
│  24V_DU (F_DU 3 A, SS54, SMBJ24A; LRS #1 −V bonded to the │
│  CSC GND here; nothing on the CSC runs from it) ──►       │
│          Q_DOCK (PB5, only while DOCK_SENSE_B is low) ──► │
│          F_DOCK 2 A ──► J_DOCK pin 1 (DOCK_24V)           │
└────────────────────────────┬──────────────────────────────┘
                             │ 8-pin magnetic pogo dock (CS left pillar)
                             │ DOCK_24V + GND (pins 1–2), CAN (3–6), sense (7–8)
                             ▼
┌───────────────────────────────────────────────────────────┐
│     Unified PCB v5.0 — Dispensing Unit (DU)               │
│                                                           │
│  DOCK_24V ──► MP1584EN #1 ──► 12V ──► TP5100 (1.0 A,      │
│               R_CS 0.1 Ω) ──► 2S Li-ion pack (J_BAT)      │
│               INA219 #2 (0x44, 10 mΩ) in the BAT+ path    │
│  VSYS = DOCK_24V ⊕ BAT+ (SS54 Schottky-OR, passive)       │
│         docked ≈ 23.5 V; lifted / mains lost 6.0–8.4 V    │
│  VSYS ──► TPS54531 ──► 5V_MAIN (Pico Zero, LCD, white LED │
│           ring ≤ 1 A, buzzer) ──► AMS1117 ──► 3.3V (DU    │
│           STM32, I2C devices, SN65HVD230, TB6612)         │
│  VSYS ──► MP1584EN #2 ──► 6V_DSP, switched by Q_DSB       │
│           (PCF8574 #2 P4), 3 A PTC, 1000 µF: DSB servos   │
│           ×4, TB6612 pumps (6 V, one at a time)           │
│  No isolated domain on this board (pad 5 GND_ISO → GND)   │
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

Note: The electric heating unit has its own AC feed from
the inlet through K_SAFE (not through the DC PSUs); the
OEM unit is not opened and nothing is tapped from it. The
CSC, the fans and the relay coils run from their own
LRS-35-12 (J_12V_IN). LRS-75-24 #1 feeds only the dock
(24V_DU → Q_DOCK); its −V is bonded to the CSC ground at
J_DU_IN. LRS-75-24 #2 feeds the Stirring Unit
through the CSC's floating SU island (J_SU_IN → F_SU →
J_STIR_PWR); K_SU cuts its AC input, so the SU ground
never meets the CS ground. The Pico
Zero is powered via the Unified PCB's 5V_MAIN rail through
the J_AP slot (pins 2, 4); its on-board regulators derive
the SoC, camera and Wi-Fi rails. It draws ~1 W.
The battery is the DU's PRIMARY supply: docked, VSYS comes
from DOCK_24V and the pack does not discharge (a full
session docked draws from the dock, not the pack); lifted
or on mains loss the pack carries the ≈ 3 W DU load for
> 12 h with no gap (Schottky-OR). Charge ≈ 5.5 h from empty
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
| Quantity | 2 — #1 DU (J_DU_IN on the CSC: dock charge feed only; the CSC runs from a third PSU, a Mean Well LRS-35-12: 12 V, 3 A, 36 W, 99 × 82 × 30 mm, AC input unswitched); #2 SU (J_SU_IN on the CSC, output floating, AC input through K_SU) |
| Output Voltage | 24V DC |
| Output Current | 3.2A max |
| Output Power | 76.8W |
| Input Range | 85-264VAC (universal) |
| Efficiency | >87% |
| Dimensions | 129 x 97 x 30mm |
| Protections | Short circuit, overload, over-voltage |
| Certifications | UL, CE, CB |

### 11.3 Power Budget Table

**Heating unit — AC direct from the inlet through K_SAFE; CSC PSU — Mean Well LRS-35-12 (12V_IN → J_12V_IN) feeds the CSC, the fans and the relay coils**

| Rail | Subsystem | Typical (W) | Peak (W) | Notes |
|------|-----------|-------------|----------|-------|
| AC direct | Electric heating unit | 450 | 1,300 | Self-contained unit (1,300 W assumed, unit TBD), fed straight from the inlet through K_SAFE, which cuts the unit's AC inlet; nothing is tapped from the unit |
| 12V_IN (CSC) | Exhaust fans (x2) | 1 | 6 | 12V DC, 120mm, 0.3-0.5A each, J_FAN |
| 12V_IN (CSC) | Relay coils K_SAFE + K_SU | 1 | 2 | Omron G5V-2 ×2: AC inlet disconnect for the heating unit, AC disconnect for the SU PSU |
| 12V_IN → 5V → 3.3V (CSC) | STM32G0B1RE, ISO1050 #1 and #3 logic side | 0.2 | 0.4 | AMS1117 LDO on the CSC |
| 5V → B0505S #1 (CSC) | 5V_ISO bus domain (ISO1050 #1 bus side; optional heater pin 4; dock pad 6 reserved, the DU draws nothing) | 0.2 | 0.5 | F_CAN 100 mA |
| 5V → B0505S #2 (CSC) | 5V_ISO2 / GND_SU (ISO1050 #3 bus side, SU island) | 0.2 | 0.3 | Stays up with the SU PSU off |
| - | Regulator losses | 1 | 2 | Buck + LDO inefficiency (CSC on-board dissipation ~3.5 W) |
| **12V_IN Total (LRS-35-12, 36 W)** | | **~4W** | **~17W** | **~1.3 A typical / ~1.4 A peak at 12 V (CSC §4.10, ≈ 17 W) against the 3 A LRS-35-12, > 50 % headroom; the PSU's AC input is unswitched, so the CSC boots independently of K_SAFE and K_SU** |

**Dispensing Unit PSU — LRS-75-24 #1 via the CSC: the dock feed only (nothing on the CSC runs from it)**

| Rail | Subsystem | Typical (W) | Peak (W) | Notes |
|------|-----------|-------------|----------|-------|
| 24V_DU via Q_DOCK (CSC) | DOCK_24V to the Dispensing Unit (table below) | 5 | 30 | J_DU_IN (F_DU 3 A, SS54, SMBJ24A) → Q_DOCK → F_DOCK 2 A; DU load + charger while docked; LRS #1 −V bonded to the CSC ground at J_DU_IN |
| **24V PSU #1 Total** | | **~5W** | **~30W** | **The stir motor, the CSC, the fans and the relays are no longer on this PSU; ~0.6 A typical / ~1.6 A peak (CSC §4.10), within the 3.2 A LRS-75-24 #1 (an LRS-50-24 would do; kept for a single part number)** |

**Stirring Unit (SU) — LRS-75-24 #2 (floating 24V_SU / GND_SU) through the CSC's SU island**

| Rail | Subsystem | Typical (W) | Peak (W) | Notes |
|------|-----------|-------------|----------|-------|
| 24V_SU via J_SU_IN → F_SU → J_STIR_PWR (CSC) | CAN servo stirring motor (SU, via J_SU) | 24 | 72 | 1.0 A typical, 3.0 A peak; F_SU 5 A; AC input through K_SU (motor de-energised within ~50 ms of K_SU opening, ~300 ms PSU start-up after it closes) |
| **24V PSU #2 Total** | | **~24W** | **~72W** | **Within the 76.8 W LRS-75-24 #2; both 24 V PSUs are the same part number** |

**Dispensing Unit (DU) — from DOCK_24V while docked, from the 2S pack when lifted or on mains loss**

| Rail | Subsystem | Typical (W) | Peak (W) | Notes |
|------|-----------|-------------|----------|-------|
| VSYS → 5V_MAIN (TPS54531) | Luckfox Pico Zero (RV1106G3) | 1 | 2 | 5V via 40-pin header; includes eMMC, Wi-Fi/BT, IMX415-98 camera, NPU/ISP load |
| 5V_MAIN | 4" SPI LCD + backlight | 0.5 | 0.8 | ST7796S panel + LED backlight, PWM dimmed |
| 5V_MAIN via Q_LED | White LED ring (12–16 LEDs) | 0 | 5 | ≤ 1 A at CAPTURE (100 %), NIGHT 30 %, off otherwise |
| 5V_MAIN | Buzzer | 0 | 0.2 | DU STM32 TIM14 PWM via 2N7002 |
| 5V_MAIN → 3.3V | DU STM32G0B1RE (≈ 30 mA, 0.1 W), PCA9685, PCF8574 #2, INA219 ×2, SLD Hall switches ×6, SN65HVD230, TB6612 VCC | 0.4 | 0.6 | AMS1117 LDO on the Unified PCB |
| VSYS → 6V_DSP (MP1584EN #2) | Dispenser servos DSB (x4, one moving at a time) | 0 | 15 | 6.0 V rail switched on only during a dispense; ≤ 2.5A stall (DS3218 2.2A, MG996R ~2.5A), INA219 #1 window |
| VSYS → 6V_DSP | SLD pumps (6 V peristaltic oil ≈ 0.3 A, 6 V diaphragm water ≈ 0.6 A; one at a time) | 0 | 4 | TB6612 VM on 6V_DSP, only during dispense; no solenoids since 2026-11-05 |
| DOCK_24V → 12V (MP1584EN #1) | TP5100 battery charger | 0 | 10 | 1.0 A into the 2S pack while charging (≈ 3 h from empty), 0 when full; docked only |
| - | Regulator losses | 1 | 3 | Buck + LDO inefficiency |
| **DU Total (docked, from DOCK_24V)** | | **~3W** | **~25W** | **Charge and dispense peaks rarely coincide; F_DOCK 2 A (48 W)** |
| **DU Total (lifted, from the pack)** | | **~3W** | — | **RV1106 + LCD + logic on 38 Wh → > 12 h** |

| | | Typical (W) | Peak (W) | |
|------|-----------|-------------|----------|-------|
| **System Total (incl. heater)** | | **~490W** | **~1,450W** | **Within 2kW limit (1,300 W heater assumed); CS + SU + DU peaks summed** |

---

## 12. Electric Heating Unit

### 12.1 Heating Unit Integration

The electric heating unit is a self-contained commercial unit of the premium rice-cooker class with its own AC power inlet, relay/triac mains power stage, resistive heating plate, spring-loaded centre temperature sensor (pressed by the pot) with closed-loop control, and onboard safety circuits. It replaced the induction surface on 2026-11-04 as a drop-in CAN node (same HEAT_* message set); see [[../05-Subsystems/01-Electric-Heating|Electric Heating]]. It sits in the Cooking Surface with the CSC.

The reference unit is the **Philips OneChef NX5300/00** (Electric Heating §2.3): its body becomes the Cooking Surface (modified for the stirrer gantry and the dock pillars), its air-fryer lid is dropped and the Dispensing Unit docks in its place, and its round 6 L inner pot is set aside: Epicura's pot is a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot (≈ 7.3 L brim, 6 L max fill at ~100 mm; [[04-Mechanical-Design|Mechanical Design]] §2.2) sitting on the same plate in an opened-out well. Its 2,280 W nameplate covers the base plate **and** the air-fryer lid heater together; the base plate alone is expected at 1,000–1,300 W, so 1,300 W stays the planning figure. The plate's temperature range is 80–200 °C (Epicura requests 60–200 °C): sear and tadka stages are ≤ 200 °C and the STM32 limits on `surface_temp` are re-based to > 220 °C CRITICAL / > 230 °C E_STOP (`element_temp` > 250 °C WARNING unchanged). The OEM unit ships with a control board exposing HEAT_* on CAN (confirmed 2026-11-04); the retail touch-panel board is not used. Epicura interfaces with the unit exclusively via the isolated CAN port **J_CAN_HEAT on the CSC** — no high-voltage wiring touches the CSC or the Unified PCB, and no temperature sensor is needed in Epicura.

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
                    │ J_CAN_HEAT+120Ω term│ pins   │  J_DOCK pads 3–5    │
                    │  5 V_ISO (B0505S)   ├─ 3–5 ──┤  (stub ≤ 30 cm)     │
                    │  ISO1050DUB #1      │        │  SN65HVD230 (DU GND)│
                    │     │               │        │       │             │
                    │  STM32 FDCAN1       │        │  DU STM32 FDCAN1    │
                    │  PB8/PB9            │        │  ◄─UART─ RV1106     │
                    │  off-switch + relay │        │  setpoint (gateway) │
                    └─────────────────────┘        └─────────────────────┘

System Safety:
  - Unit-internal: pot detection (centre sensor), thermal fuse, over-temperature cut-off (cannot be overridden)
  - System-level: safety relay K_SAFE on the heating unit's AC inlet loom (STM32 PB0 ──► Q_RLY ──► relay,
    J_SAFE 1 on the CSC); the CSC stays up on its own LRS-35-12 while the unit is disconnected
  - RV1106 sends HEAT_SET_TEMP / HEAT_SET_POWER setpoints (unit PID regulates); STM32
    can force HEAT_ON_OFF=0, broadcast E_STOP on the bus, or open the relay on fault/E-stop
  - Lifting the DU takes the DU node (RV1106 via the DU STM32) off the bus: the unit drops to zero ≤ 1 s after the
    last keep-alive and the STM32 holds safe on DOCK_SENSE_B (Section 8.2)
```

---

## 13. Ingredient Dispensing System (FID / CID / SLD)

The dispensing system comprises three subsystems, all in the Dispensing Unit and all driven by the DU STM32 on the Unified PCB v5.0 over I2C1, TIM PWM and GPIO — the CSC STM32 has no part in dispensing. FID and CID share one electrical control block, the Dispenser Servo Block (DSB). The RV1106 `epicurad` `dispense` thread is a thin client: it sends the 0x230–0x239 commands over the host link and waits for 0x3FE DU_ACK. The DU STM32 **Dispense task** (FreeRTOS, 50 Hz while a move is active) does the work: PCA9685 ramped moves (≤ 3°/tick), 6V_DSP rail enable, one servo at a time, stall detection (INA219 #1 current > 2.5 A for 300 ms, 3 s move timeout, I2C NACK → retry once with 10° back-off → DSB_STALL), SLD open-loop metering (tank present / low check, prime if pending, pump tach pulses counted to target), prime, calibration, preflight, home and status; faults come back as NAK result codes / DU_STATUS error_code. See [[03-Ingredient-Dispensing|Ingredient Dispensing System]] for full details.

### 13.1 DSB — FID + CID Servo Wiring

```
  VSYS ──► MP1584EN #2 (6.0 V, 3 A) ──► Q_DSB P-MOSFET high-side switch ──► 6V_DSP rail
                                               ▲                            (1000 µF bulk, 3 A PTC)
                                   PCF8574 #2 P4 (rail enable, I2C1 0x21)

  DU STM32 I2C1 (PB6/PB7) ──► PCA9685 (addr 0x41, on Unified PCB)
                        ├── CH0 ──► J_DSB1 ──► C1  CID carousel index servo, DS3218 270° (4:3 gear-up)
                        ├── CH1 ──► J_DSB2 ──► F1  FID carousel index servo, MG996R (5:3 gear-up)
                        ├── CH2 ──► J_DSB3 ──► F2  FID dose servo, MG996R (canister ¼ tsp measure wheel)
                        └── CH3 ──► J_DSB4 ──► F3  FID steam-gate servo, MG90S (6.0 V directly, D_DSB4 removed)
  DU STM32 PB0 ──► PCA9685 OE (active-low; 10k pull-up → servos off at boot, in reset and on host loss)

  I2C1 devices (DU STM32): PCF8574 #2 (0x21), INA219 #1 (0x40, 6V_DSP shunt), INA219 #2 (0x44, battery), PCA9685 (0x41)
                (the SLD tank / pump Hall switches are GPIO on PC0–PC5, §13.2)
  (FT6336 touch 0x38 stays on the RV1106 I2C3)

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
  │      PWMA ◄── DU STM32 PA6 (TIM3_CH1, 20 kHz)
  │      AIN1 ◄── PCF8574 #2 P3 (I2C1, 0x21)
  │
  ├──► Peristaltic Pump (Water, 6 V DC) — TB6612 Channel B on Unified PCB
  │      PWMB ◄── DU STM32 PA7 (TIM3_CH2, 20 kHz)
  │      BIN1 ◄── PCF8574 #2 P5 (I2C1, 0x21)
  │
  │   (oil pump: peristaltic, ≈ 0.4 mL/rev; water pump: diaphragm, ≈ 0.25 mL/stroke, ≈ 1 L/min;
  │    both in the DU body under the drawer-tank bays; no solenoid valves — spring check valves
  │    in the nozzle cartridges block drip, siphon and steam)

  PCF8574 #2 (0x21) map: P0/P1 spare (solenoids removed 2026-11-05), P2 spare (status LED now on DU STM32 PC7), P3 TB6612 AIN1,
    P4 6V_DSP rail enable, P5 TB6612 BIN1, P6 TP5100 CHRG (in), P7 TP5100 STDBY (in)

  SLD Hall switches (6×, AH3572-class, open-drain, 10k pull-ups + 100R on the Unified PCB) via J_SLD:
    J_SLD 7  OIL_TACH    ──► PC0 (EXTI0)   2 pulses per roller-head rev ≈ 0.2 mL each
    J_SLD 8  H2O_TACH    ──► PC1 (EXTI1)   1 pulse per motor rev ≈ 0.25 mL
    J_SLD 9  OIL_PRESENT ──► PC2 (EXTI2)   fixed magnet in the tank wall; rising edge arms the prime routine
    J_SLD 10 OIL_LOW     ──► PC3 (polled)  float magnet, ≈ 20 mL left
    J_SLD 11 H2O_PRESENT ──► PC4 (EXTI4)
    J_SLD 12 H2O_LOW     ──► PC5 (polled)  float magnet, ≈ 50 mL left
    Metering: volume = pulses × cal_ul (per channel, SLD_CAL 0x237); prime before the next dose after a tank re-seat
    Faults: no tach pulse within 1 s / rate < 25 % / INA219 #1 current out of window → SLD_DISPENSE_ERROR;
            tank absent → SLD_TANK_ABSENT; float low → SLD_LOW_LEVEL (DU STM32-detected, NAK / DU_STATUS error_code)
```

### 13.3 Dispensing Summary

| Subsystem | Actuators | Metering | Min Dispense |
|-----------|-----------|----------|-------------|
| FID (fine / seasonings) | 3× servo on DSB (F1 index, F2 dose, F3 steam gate), 6 canisters with ¼ tsp measure wheels | Volumetric per dose stroke (±10%) | ¼ tsp (~0.5 g) |
| CID (coarse) | 1× servo on DSB (C1 index), 5-slot carousel + cover sector | Whole slot / user pre-measured | One slot (~200 mL) |
| SLD (liquids) | 6 V peristaltic pump (oil) + 6 V diaphragm pump (water) on the TB6612, Hall tach each; 200 mL / 500 mL drawer tanks with float + presence Hall switches; check-valve nozzle cartridges | Open loop, tach pulses × calibrated mL/pulse (±5 %) + low-level / tank-absent alerts | ~2 mL |
| Exhaust | 2× 120mm fans on the CSC (independent PWM control, SET_EXHAUST over CAN) | Temperature/fume-based control | — |

**Unified PCB On-Board Routing:** All dispensing signals run from the DU STM32 directly to their driver ICs (PCA9685, TB6612, PCF8574 #2, INA219 ×2, Q_LED) on the same board. The four DSB servo leads plug into J_DSB1-4 (3-pin JR headers on the switched 6.0 V rail); the SLD harness (two pumps, six Hall switches) into the 12-pin J_SLD. No inter-board connector is required inside the DU. The Luckfox Pico Zero sits in the J_AP slot, which carries 5V_MAIN power, the UART2 host link and BOOT0/NRST lines to the DU STM32, and the display lines (SPI0, I2C3 touch, re-emerging on J_LCD).

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

- DU STM32 I2C1 stays on the Unified PCB (PCA9685, PCF8574 #2, INA219 ×2); RV1106 I2C3 carries only the FT6336 via J_LCD; 4.7k pull-ups on each bus. Keep the 921,600-baud host link (J_AP pins 8/10 → DU STM32 PA9/PA10) short, with 33R series resistors at the driver ends
- Keep the two CAN buses apart: the isolated stir-motor bus (J_CAN_STIR, CSC, SU domain GND_SU) must not run alongside the isolated heater bus (J_CAN_HEAT, CSC) or cross any isolation slot (the CSC has one under each port); the isolated bus to the DU runs in the pillar dock harness and lands on the Unified PCB's J_DOCK pads 3–5 (ordinary SELV spacing, no slot on the DU; pad 5 tied to DU GND), as a stub ≤ 30 cm
- SLD Hall switches: six digital open-drain lines (< 30 cm) from the tank bays and pump brackets to J_SLD; route them away from the 6V_DSP switch node and the pump leads; nothing analog leaves the Unified PCB
- The stirring-unit harness (J_CAN_STIR + J_STIR_PWR: 24V_SU, GND_SU, CAN_H, CAN_L, SHIELD — nothing on it references the CS ground) runs inside the right rear pillar to J_SU; the dock harness (J_DOCK, 8-way) inside the left rear pillar
- The CSC's supply lead (J_12V_IN, 2-wire: 12V_IN + GND from the LRS-35-12) and the CAN cable to J_CAN_HEAT both stay away from the heating unit's AC inlet loom, where K_SAFE's power relay switches the unit's current
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
│  (LRS-75-24 #1 −V, bonded to  │                      │
│   the CSC GND at J_DU_IN)     │                      │
│                               │                      │
│  Signal Ground (CS) ◄─────────┘                      │
│  (CSC: STM32, ISO1050 logic,  │                      │
│   low-current digital) = the  │                      │
│   LRS-35-12 −V on J_12V_IN;   │                      │
│   LRS #1 −V bonded at J_DU_IN │ dock pin 2 (GND)     │
│                               ▼                      │
│  Signal Ground (DU) ◄── joins the CS ground ONLY     │
│  (Unified PCB: RV1106,        through dock pin 2     │
│   sensors, dispensers)        while docked; floats   │
│                               on the pack when lifted│
│                                                      │
│  Isolated bus ground (GND_ISO): made on the CSC by   │
│  B0505S #1, carried over dock pin 5 and tied to the  │
│  DU logic ground there (one point); never on the CSC │
│                                                      │
│  SU ground (GND_SU): the floating −V of LRS-75-24 #2,│
│  ISO1050 #3 bus side (B0505S #2) and the J_SU harness│
│  — never bonded to any CS ground or to GND_ISO       │
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
| **MCU** | STM32G0B1RE Nucleo Board (proto, CSC) | 1 | $11 | $11 |
| | STM32G0B1RET6 IC (CSC production + DU STM32 on the Unified PCB) | 2 | $3.50 | $7 |
| | 8 MHz crystal + caps, J_SWD (DU STM32) | 1 | $0.50 | $0.50 |
| **Display** | 4" ST7796S SPI LCD with FT6336 touch | 1 | $15 | $15 |
| **Camera** | Luckfox IMX415-98 IR-CUT 8 MP camera module (incl. 22-pin FPC) | 1 | $54 | $54 |
| **Sensors** | Hall switches ×6 (SLD pump tachs, tank present, tank low) + Ø3 mm magnets | 1 lot | $2 | $2 |
| | INA219 #2 current/voltage monitor (battery, 10 mΩ shunt) | 1 | $1 | $1 |
| | Reed switch (pot detect — backup/optional) | 1 | $1 | $1 |
| **Battery** | 2S2P 18650 Li-ion pack, 5,200 mAh (~38 Wh), PCM + NTC | 1 | $22 | $22 |
| **Actuators** | 24V CAN servo stirring motor (CyberGear/RobStride-class) | 1 | $45 | $45 |
| | DS3218 270° servo (DSB: C1 CID index) | 1 | $10 | $10 |
| | MG996R servos (DSB: F1 FID index, F2 dose) | 2 | $4 | $8 |
| | MG90S micro servo (DSB: F3 steam gate) + 1N4007 | 1 | $2.50 | $2.50 |
| | PCA9685 servo driver (DSB) | 1 | $1.50 | $1.50 |
| | FID canisters w/ ¼ tsp measure wheels | 6 | $3 | $18 |
| | FID + CID carousel rings, base plate, chutes, gears, bearings | 1 set | $26 | $26 |
| | 6V peristaltic pump (SLD oil, Hall tach) | 1 | $10 | $10 |
| | 6V diaphragm pump (SLD water, ≈ 1 L/min, Hall tach) | 1 | $5 | $5 |
| | SLD drawer tanks (200 mL oil, 500 mL water; PP, self-sealing poppet, float) | 2 | $6 | $12 |
| | SLD nozzle cartridges with check valve | 2 | $1.50 | $3 |
| | 120mm 12V DC brushless fans (exhaust) | 2 | $5 | $10 |
| | 5V piezo buzzer (active) | 1 | $2 | $2 |
| **Heater** | Donor cooker: Philips OneChef NX5300/00 or equivalent — heating unit, controller, base body (its round pot and lid are not used) | 1 | $230 | $230 |
| | 25 × 25 × 12 cm rounded-square non-stick pot + glass lid | 1 | $25 | $25 |
| **Power** | Mean Well LRS-75-24 (24V/3.2A) — #1 DU only, #2 SU (floating output, AC via K_SU) | 2 | $20 | $40 |
| | Mean Well LRS-35-12 (12 V / 3 A / 36 W) — CSC, relay coils and fans (J_12V_IN); AC input unswitched | 1 | $12 | $12 |
| | IEC C14 inlet + EMI filter | 1 | $8 | $8 |
| | Safety relays (Omron G5V-2: K_SAFE heating unit AC inlet, K_SU SU PSU) | 2 | $5 | $10 |
| **Misc** | White LED ring (12–16 LEDs, 5000 K, CRI ≥ 90) | 1 | $4 | $4 |
| | E-Stop mushroom button | 1 | $4 | $4 |
| | ISO1050DUB isolated CAN transceivers (#1 and #3, both on the CSC) | 2 | $3.50 | $7.00 |
| | SN65HVD230 CAN transceiver (DU node, Unified PCB) | 1 | $0.80 | $0.80 |
| | B0505S-1WR3 isolated DC-DC (CSC: #1 5V_ISO, #2 5V_ISO2 for the stir port) | 2 | $1.40 | $2.80 |
| | TP5100 2S charger + inductor + sense resistor (1.0 A) | 1 | $1 | $1 |
| | 8-pin magnetic pogo connector pair (J_DOCK, 2 A pins) | 1 | $6 | $6 |
| | Molex Micro-Fit 3.0 5-way pair (J_SU) | 1 | $2 | $2 |
| | Passive components (R, C, etc.) | Lot | - | $20 |
| | Unified PCB v5.3 (4-layer annular sector, 1 board; arc outline price TBC) | 1 | $41 | $41 |
| | Cooking Surface Controller PCB (4-layer, 5 pcs) | 1 | $25 | $25 |
| | Wiring, connectors, FFC cables | Lot | - | $25 |
| **Enclosure** | 3D-printed enclosure (prototype) | 1 | $80 | $80 |
| | Gantry hardware (rods, brackets) | Lot | - | $30 |

**Estimated Prototype BOM Total: $860 - $970 USD** (robot-mop SLD 2026-11-05: −$4 NAU7802 ×2, −$1 TCA9543A, −$8 load cells, −$8 solenoids, −$5 pumps (diaphragm for water), +$12 drawer tanks, +$3 check-valve cartridges, +$2 Hall switches, net ≈ −$9, was $869 - $979; dedicated CSC PSU 2026-11-05: +$12 Mean Well LRS-35-12, IRM-20-12 fallback line removed, was $857 - $967; CSC powered from the heating unit's 12 V rail 2026-11-05: −1 MP1584EN inside the passives lot, +1 JST-XH 2-pin, no line change; IRM-20-12 fallback listed but not added; DU node non-isolated 2026-11-04: −$3.50 ISO1050DUB #2 + $0.80 SN65HVD230, net ≈ −$2.70, was $860 - $970; isolated stir port + SU PSU 2026-11-04: +$20 LRS-75-24 #2, +$5 G5V-2 K_SU, +$3.50 ISO1050DUB #3, +$1.40 B0505S #2, −$0.90 SN65HVD230, net ≈ +$29, was $830 - $940; DU STM32 added 2026-11-04: +$3.50 STM32G0B1RET6 + $0.50 crystal/SWD + $1 board, −$3 MCP2518FD, net ≈ +$2; DU pack 2,600 → 5,200 mAh, $12 → $22, and 25 cm rounded-square pot + glass lid $25 added back 2026-11-04; donor cooker $230 replaces the $45 heating unit, was $635 - $745; production: OEM heating unit, bulk, ≈ $50 + pressed pot ≈ $10; three-unit split: net ≈ +$32 for the CSC PCB, dock pair, NAU7802 ×2, TCA9543A, INA219 #2, white LED ring and J_SU, less the HX711 ×2, WS2812B ring and 74AHCT1G125; electric heating unit −$15 against the induction surface)

*Note: Production BOM would be lower per unit at volume. Prototype uses a Nucleo dev board for the CSC that would be replaced with a bare STM32G0B1RET6; the DU STM32 is a bare STM32G0B1RET6 on the Unified PCB from the first build. The Luckfox Pico Zero is used as-is (off-the-shelf module, no carrier board) in both prototype and production.*

---

## 18. Hardware Validation Checklist

### 18.1 Power Supply
- [ ] Verify 24V rail from Mean Well PSU within spec (24V +/-5%)
- [ ] Verify the 12 V rail from the LRS-35-12 at the CSC J_12V_IN within spec (12V +/-5%) and present with K_SAFE and K_SU both open (its AC input is unswitched)
- [ ] Measure ripple on each rail of the CSC and the Unified PCB (<50mV peak-to-peak)
- [ ] Load test at full power (heating unit 1,300 W assumed + all subsystems)
- [ ] Verify standby power <5W
- [ ] Test EMI filter effectiveness (conducted emissions)
- [ ] Verify fuse blows at rated overcurrent
- [ ] Dock charge: DOCK_24V appears on J_DOCK pin 1 only while DOCK_SENSE_B is low; 0 V on the pads with the DU lifted; F_DOCK trips at 2 A
- [ ] Dock power: VSYS ≈ 23.5 V docked with zero pack discharge (INA219 #2); TP5100 charges at ~1.0 A, full from empty in ≈ 3 h; CHRG/STDBY read on PCF8574 #2

### 18.2 Compute (RV1106)
- [ ] Luckfox Pico Zero boots Buildroot Linux from eMMC; A/B rootfs fallback verified
- [ ] Host link up on `/dev/ttyS2` (UART2 ↔ DU STM32 USART1, 921,600 baud): COBS/CRC frames both ways, zero CRC errors over 1 h, ≤ 5 ms gateway latency; DU_STATUS (0x311) arrives at 1 Hz
- [ ] CAN bus through the DU STM32 gateway (FDCAN1 + SN65HVD230, 500 kbps) across the dock; continuity between dock pad 5 and the DU logic ground, none between pad 5 and the CSC logic ground; commands to the CSC STM32 and 20 Hz TELEMETRY exchanged while the LCD is refreshing; no error frames on the ≤ 30 cm dock stub; bus-off on lift and recovery on re-dock
- [ ] CSC firmware load over the CAN bootloader (0x7E0/0x7E8) from the RV1106 swupdate handler through the gateway; USB DFU on the CSC J_USB as the bench fallback
- [ ] DU STM32 firmware load from the RV1106 via GPIO 32 BOOT0 / GPIO 38 NRST and the ST system bootloader on USART1; dispensers stay off during the update; J_SWD on the Unified PCB as the bench path
- [ ] Camera captures 1280x720 @ 30fps frames via MIPI CSI (IMX415-98, ISP tuning loaded) through the underside window
- [ ] NPU runs the INT8 stage classifier in <20 ms
- [ ] Display renders LVGL UI via SPI0 (fbtft, full-frame refresh ~50 ms)
- [ ] Touch input (FT6336, I2C3) registers on all screen areas
- [ ] LED ring: SET_LED (0x220) over the host link → DU STM32 TIM1 duty 0 / 30 / 100 % gives OFF / NIGHT / CAPTURE; ≤ 1 A on 5V_MAIN at 100 %
- [ ] Buzzer: SET_BUZZER (0x226) → DU STM32 TIM14 drives all alert patterns
- [ ] All DU STM32 I2C1 devices enumerate (0x21, 0x40, 0x41, 0x44); FT6336 0x38 on RV1106 I2C3
- [ ] Host-loss rule: stopping HB_AP for 5 s drops 6V_DSP, raises PCA9685 OE and turns the ring off on the DU STM32
- [ ] WiFi connects to AP, achieves >10 Mbps throughput
- [ ] BLE advertises and pairs with test phone
- [ ] eMMC read/write speed adequate (>50 MB/s sequential)

### 18.3 Electric Heating Unit
- [ ] Unit responds to CAN queries (HEAT_QUERY → HEAT_STATUS)
- [ ] CAN power level commands correctly modulate heating
- [ ] Unit heats water from 20C to 100C within 10 minutes (1.5L, 1,300 W assumed)
- [ ] Setpoint step 25 → 100C at the centre sensor rises in < 180 s (plate-limited ramp ~2-4 C/s)
- [ ] Unit holds a HEAT_SET_TEMP setpoint within +/-5C (its own PID); RV1106 keep-alive at 2 Hz never drops out while the LCD refreshes
- [ ] OEM unit: its CAN control board answers HEAT_* on the isolated bus; its CAN port is SELV (no continuity to its mains side, confirmed before the DU is docked)
- [ ] Sear stage reaches 200C at the centre sensor with the 25 cm pot; injected surface_temp > 220C raises CRITICAL and > 230C triggers E_STOP
- [ ] All four power profiles (sear/boil/simmer/warm) verified
- [ ] Unit-internal pot detection (spring-loaded centre sensor) prevents heating without pot
- [ ] Safety relay K_SAFE (CSC Q_RLY, J_SAFE 1) disconnects AC to the heating unit at its inlet on E-stop or fault; the CSC (on its own LRS-35-12) and the SU PSU stay up while the unit is disconnected
- [ ] STM32 HEAT_ON_OFF=0 and E_STOP broadcast stop heating within 500ms; unit drops to 0 power 1 s after the HEAT_SET_TEMP keep-alive stops
- [ ] Undock: lifting the DU mid-cook stops the unit ≤ 1 s (keep-alive loss), the STM32 reports DU_UNDOCKED, K_SU (SU PSU) and Q_DOCK open; re-docking returns to NORMAL once HB_AP resumes
- [ ] E-stop on the CS front (CSC PB2) and the soft stop on the DU UI (E_STOP over CAN) both stop the heater and the stir motor

### 18.4 Servo System
- [ ] Main arm (24V CAN servo) rotates full 360 degrees smoothly; motor enumerates on FDCAN2 at 1 Mbps
- [ ] Stirring speed controllable from 10-60 RPM; reported RPM within ±5 of commanded
- [ ] Motor stops within 500 ms when FDCAN2 traffic stops; 0 V on J_STIR_PWR / J_SU within ~50 ms of K_SU opening; motor boot frame seen ~300 ms after K_SU closes; K_SU stays open through reset and boot until the Safety Monitor enables it
- [ ] Stirring-unit harness through the right pillar: J_SU mates one way, shield continuity to GND_SU at the CSC end; no continuity between GND_SU and the CS ground or GND_ISO
- [ ] Arm torque sufficient to stir thick curry/dal
- [ ] Each DSB servo (x4) reaches commanded angle within ±2° via PCA9685 on DU STM32 I2C1
- [ ] 6V_DSP rail switches off after each dispense (no idle jitter or buzz); 6.0 V ±5 % under a 2.5 A servo stall
- [ ] PCA9685 OE high on soft stop / boot leaves all four servos limp

### 18.5 Sensors
- [ ] Camera: white balance calibrated, image sharp across full pot FOV
- [ ] Unit surface_temp (centre sensor, HEAT_STATUS) tracks a thermocouple on the pot bottom within +/-5C at 100C
- [ ] Battery: pack charges to 8.4 V at ~1.0 A; CHRG/STDBY read on PCF8574 #2; INA219 #2 voltage within 2 %, current within 5 %
- [ ] Battery: pulling mains with the DU docked keeps the Pico Zero and LCD running (no reboot); DOCK_PWR_OK goes inactive, PAUSED (AC Power Failure) after the 300 ms TELEMETRY timeout, auto-resume when mains returns
- [ ] Battery: lifted DU runs > 12 h at ≈ 3 W; warning banner at 6.4 V, checkpoint + halt at 6.2 V, RECOVERING on next power
- [ ] SLD Hall inputs: tank present / low follow the tanks (out, full, ≈ 20 / 50 mL left); pump tachs count every pulse at 25 / 50 / 100 % PWM
- [ ] SLD prime: re-seating a tank sets prime_pending; the next dose primes first and reports primed_ml; SLD_PRIME is refused while lifted
- [ ] Dock sense: DOCK_SENSE_A edge reaches the RV1106 within 10 ms of lift; state machine enters PAUSED (UNIT_LIFTED); no auto-resume on re-dock
- [ ] Pot detection: reliably detects pot on/off

### 18.6 Dispensing (FID / CID / SLD)
- [ ] FID: Each canister doses ¼ tsp (1.23 mL) within ±10% per stroke
- [ ] FID: Jiggle routine clears a hand-packed canister without a stall
- [ ] FID: Steam gate closes by spring with servo unpowered
- [ ] CID: Each slot empties into the pot on index; cover sector closes aperture at home
- [ ] CID: Out-of-order slot command is NACKed, carousel does not move
- [ ] DSB: Stall detection (INA219 #1 window on 6V_DSP, DU STM32 Dispense task) fires when a carousel is blocked by hand and comes back as NAK DSB_STALL on the host link
- [ ] SLD: after SLD_CAL each pump (TB6612, DU STM32 TIM3 PWM) dispenses 10 mL oil / 300 mL water within ±5 % by tach pulse count; 500 mL water in ≤ 40 s
- [ ] SLD: nozzle check valves hold with a full tank over a 200 °C pot (no drip in 10 min); drawer tanks seal when out
- [ ] Both exhaust fans (CSC J_FAN): PWM control from 0-100% via SET_EXHAUST over CAN, no audible whine
- [ ] Both exhaust fans: Independent control verified (each can run separately); GET_EXHAUST reports duty and rpm
- [ ] Buzzer: All alert patterns audible and distinct
- [ ] No cross-contamination between subsystems
- [ ] Unified PCB and CSC: All subsystem signal routes verified on-board; STM32 free pins and the unpopulated I2C1 pads confirmed on the CSC; DU STM32 pin map (§5.3) confirmed on the Unified PCB

---

## 19. Safety Considerations

### 19.1 Electrical Safety

- **Galvanic Isolation:** The electric heating unit is a self-contained AC unit — no mains voltage reaches the CSC or the Unified PCB. The CSC's ISO1050DUB #1 (behind J_CAN_HEAT and the dock) isolates the CSC logic ground from the bus domain (5V_ISO / GND_ISO from the B0505S #1); the DU node is a non-isolated SN65HVD230 and dock pad 5 ties GND_ISO to the DU logic ground, so the bus domain is referenced to the 24 V SELV ground at that one point. Since the DU ground also meets the CS ground through dock pin 2, this barrier is a signal-reference / ground-loop barrier, not a mains-safety one: mains safety relies on the transformer isolation of the three Mean Well PSUs and on the heating unit's own board, whose CAN port must be SELV (isolated inside the unit from its mains-side electronics) — a selection requirement for the OEM board; a mains-referenced port is a hard reject, since it would put the CSC ground, the dock, the E-stop and the USB-C port at mains potential. The stir-motor CAN bus (J_CAN_STIR) is isolated as well (ISO1050DUB #3 + B0505S #2 on the CSC, bus side 5V_ISO2 / GND_SU): the Stirring Unit runs from its own LRS-75-24 #2 whose output (24V_SU / GND_SU) is never bonded to the CS ground, so the only galvanic links between the CS and the SU are the ISO1050 barrier and the B0505S transformer. All three PSUs provide transformer-isolated DC outputs.
- **Undock:** Lifting the DU opens the bus and the 24 V together: the unit drops to zero ≤ 1 s (keep-alive), the STM32 holds safe on DOCK_SENSE_B, and the dock pads are de-energised by Q_DOCK so no live 24 V is exposed on the pillar.
- **Battery Safety:** 2S Li-ion pack with per-cell protection (PCM), NTC-gated charging (0–45 °C); the pack now lives in the DU, away from the heat; IEC 62133-2 / IS 16046 cells.
- **Earth Bonding:** Metal enclosure parts of the CS connected to AC earth via IEC C14 inlet. Chassis ground bonded to PSU earth.
- **Fuse Protection:** 10A ceramic fuse in IEC C14 inlet. Polyfuses on the CSC 12V_IN input (F1 2 A), the DU feed (F_DU 3 A), the SU feed (F_SU 5 A, on the floating SU island), the dock feed (F_DOCK 2 A) and 5V_ISO (F_CAN 100 mA); 3 A PTC on 6V_DSP.

### 19.2 Thermal Safety

- **Unit Thermal:** The heating unit has an internal over-temperature cut-off and thermal fuse. It reports element temperature via CAN status. The plate stores heat after power-off; the UI shows a hot-surface warning while surface_temp is above 60C.
- **Surface Over-Temperature:** The unit's centre sensor reports the pot-bottom temperature (surface_temp) in HEAT_STATUS. If >230C (unit ceiling 200C; >220C raises CRITICAL first), the STM32 sends the CAN off command and opens the safety relay, independently of the unit's internal cut-off.
- **Enclosure Thermal:** Exhaust fans on the CSC provide ventilation of the CS. The unit reports its element temperature via CAN for enclosure monitoring.

### 19.3 Mechanical Safety

- **E-Stop Button:** Red mushroom-head button on the Cooking Surface front panel, wired to the CSC (STM32 PB2 interrupt via J_SAFE 3) AND the safety relay. Pressing E-stop: (1) STM32 sends HEAT_ON_OFF=0 and broadcasts E_STOP on the isolated CAN bus, (2) K_SAFE disconnects AC to the heating unit at its inlet (the CSC stays up on its own LRS-35-12), (3) stir motor disabled on FDCAN2 and its PSU de-energised (K_SU opens the AC input of LRS-75-24 #2). The DU's UI has a soft stop that broadcasts E_STOP over CAN while docked; on receipt the RV1106 also drops PCA9685 OE so the DSB servos go limp.
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
| 8.6 | 2026-11-04 | Manas Pradhan | Pot changed to a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot (≈ 7.3 L brim, 6 L max fill; Mechanical Design §2.2): the donor's round inner pot and glass lid are set aside and the pot well opened out; unit table, heating-unit row, §12 reference-unit paragraph and sear checklist item updated. §17 BOM: pot + glass lid $25 line added, total $795-905 → $820-930 |
| 8.7 | 2026-11-04 | Manas Pradhan | Dispensing Unit battery doubled to 2S2P 18650, 5,200 mAh (~38 Wh; was 2S1P 2,600 mAh): lifted run time > 5 h → > 12 h at ≈ 3 W, charge ≈ 3 h → ≈ 5.5 h at the unchanged 1.0 A TP5100 rate; unit table, §9 power text, DU power budget, BOM ($12 → $22, total $820-930 → $830-940) and checklist updated |
| 8.10 | 2026-11-04 | Manas Pradhan | DU CAN node no longer isolated: ISO1050DUB #2 and its isolation slot leave the Unified PCB (v5.1), replaced by an SN65HVD230 on 3.3 V referenced to the DU logic ground; dock pad 5 (GND_ISO) is tied to the DU ground on the Unified PCB (single reference point of the bus domain), pad 6 (5V_ISO) reserved / not connected on the DU; isolation stays on the CSC's two ports only (ISO1050 #1 heater/DU, ISO1050 #3 SU). §10 and §19.1 restate the barrier as a signal-reference / ground-loop barrier and add the selection requirement that the heating unit's CAN port be SELV; §2/§3/§5.3/§8.1/§10.1/§11/§12/§16/§17/§18 updated; BOM −$2.70 |
| 8.9 | 2026-11-04 | Manas Pradhan | Both CSC CAN ports isolated and the Stirring Unit on its own PSU (CSC v1.3): FDCAN2 moves from the SN65HVD230 to ISO1050DUB #3 + B0505S #2 (5V_ISO2 / GND_SU); a second Mean Well LRS-75-24 (#2, output floating, AC input through the new pilot relay K_SU on PB4 / J_SAFE 5) feeds the SU through the CSC's floating SU island (J_SU_IN → F_SU → J_STIR_PWR); Q_STIR and F_STIR dropped, heater relay named K_SAFE, 24V_STIR → 24V_SU, J_SU pins re-referenced to GND_SU (never bonded to the CS ground); unit table, system diagram, component list, §5.1 (11 connectors), CSC pin block, §7 rewritten, dock table, power diagram, §11.2–11.3 (CS and SU budgets split, system ~490 W / ~1,450 W peak), routing, ground diagram, BOM ($830-940 → $860-970), checklist and safety updated |
| 8.8 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: a second STM32G0B1RET6 (the DU STM32) on the Unified PCB v5.0 takes dispensing (DSB, SLD on I2C1 / TIM3), the LED ring (TIM1), buzzer (TIM14), battery/dock monitoring (INA219 ×2, DOCK_SENSE_A PB3, DOCK_PWR_OK PB5) and the DU CAN node (FDCAN1 + ISO1050 #2); the MCP2518FD, SPI0 CS1 and SocketCAN are removed. RV1106 ↔ DU STM32 host link: UART2 (pins 8/10) ↔ USART1, 921,600 baud, COBS/CRC-framed CAN-shaped frames; the DU STM32 is a transparent gateway (bus node still AP, CAN ID map unchanged) and terminates the DU-local block 0x220, 0x226, 0x230–0x239, 0x311 DU_STATUS, 0x3FE DU_ACK; GPIO 32/38 = BOOT0/NRST for flashing it through the ST system bootloader; CSC update still over CAN through the gateway. RV1106 header: SPI0 LCD only, I2C3 touch only. New §5.3 (DU STM32 pin map); §1, §2, §3, §4.2–4.3, §6.2, §8, §10, §11.3, §13, §16.2, §17.1 (+$2), §18 updated |
| 8.3 | 2026-11-04 | Manas Pradhan | Three-unit physical architecture: Cooking Surface (CS: induction module, LRS-75-24, new Cooking Surface Controller PCB with the STM32G0B1RE, relay, E-stop, fans), Stirring Unit (SU: 24 V CAN servo on J_SU, the only inter-unit cable) and Dispensing Unit (DU: Unified PCB v4.0 with the Pico Zero, 2S pack as primary supply, dispensers, camera + white LED ring on the underside). New §8 dock (J_DOCK, 8-pin magnetic pogo: DOCK_24V via Q_DOCK, isolated CAN pins 3–6, DOCK_SENSE_A/B) and undock behaviour; STM32 pin box rewritten for the CSC (PB3 DOCK_SENSE_B, PB4 Q_STIR, PB5 Q_DOCK, no I2C/dispensing); UART service link and BOOT0/NRST replaced by the CAN bootloader (0x7E0/0x7E8) + USB DFU; dispensing moved to the RV1106 over I2C3/PWM (PCA9685, PCF8574 #2, TB6612 on 6 V, NAU7802 ×2 via TCA9543A replace the HX711, INA219 #2 on the pack); WS2812B + 74AHCT1G125 replaced by a white PWM ring; 6.5 V DSB rail → 6.0 V, pumps/solenoids re-specified 6 V, D_DSB4 dropped, TP5100 at 1.0 A; CAN map: SET_LED, dispensing block and LOADCELLS removed, SET_EXHAUST/GET_EXHAUST/EXHAUST_AUTO and FW_UPDATE added, DU_UNDOCKED fault; block diagram, component list, header table, power (split per unit), induction, routing, ground, BOM ($650-760), checklist and safety updated; sections 8–20 renumbered 9–21 |
| 8.11 | 2026-11-05 | Manas Pradhan | CSC, relay coils and fans powered from the heating unit (CSC v1.5): 12V_HU, a 12 V SELV tap off the OneChef control-board supply, enters the CSC on the new J_HU_PWR (F1 2 A, SS34, SMBJ12A, 470 µF); the 24 → 12 V MP1584EN #1 is dropped and J_24V_IN becomes J_DU_IN (F_DU 3 A, 24V_DU), carrying LRS-75-24 #1 to Q_DOCK only (−V bonded to the CSC ground there; ~0.6 / 1.6 A). K_SAFE re-specified onto the heating element loom downstream of the OEM board's relay so the control board, its CAN port and 12V_HU stay live. Requirements on the donor rail (SELV, 10.8–13.2 V, ≥ 1.5 A spare, live whenever on; IRM-20-12 fallback, characterisation open) in §11.3, §18.1 and §19.1; unit table, system diagram, component rows, §5.1 (12 connectors), pin block, §7 SELV note, power diagram and budget (12V_HU ~1.3 / 1.4 A), §12.1 safety bullet, routing, ground diagram, BOM (no total change) and E-stop wording updated |
| 8.13 | 2026-11-05 | Manas Pradhan | Robot-mop SLD and the Ø350 mm DU disc: the Dispensing Unit becomes a Ø350 × ≤ 150 mm disc with concentric dispensers (camera hub, FID ring, CID ring, outer service ring holding the SLD drawer tanks, pack and an annular-sector Unified PCB v5.3); overall height ≈ 350 → ≈ 370 mm (TBC). SLD: 200 mL oil / 500 mL water drawer tanks with a bottom self-sealing coupling, float + presence magnets on Hall switches; pumps in the body (6 V peristaltic oil, 6 V diaphragm water) with Hall tachs; spring check valves in snap-out nozzle cartridges; open-loop metering by tach pulses × cal_ul (SLD_CAL 0x237), prime routine (SLD_PRIME 0x233), QUERY_WEIGHT → QUERY_SLD, SLD_LOAD_CELL_DRIFT → SLD_TANK_ABSENT. Removed: 2× 6 V solenoids, 2× 2 kg load cells, NAU7802 ×2, TCA9543A; DU STM32 PC0–PC5 added; J_SLD 12-pin. Unit table, footprint line, system diagram, component list, §5.3 pin map, §10 bus note, power diagram and DU budget (~25 W peak), §13, §16.2, BOM ($869 - $979 → $860 - $970), checklists updated |
| 8.12 | 2026-11-05 | Manas Pradhan | Dedicated CSC supply (CSC v1.6), reversing 8.11: the CSC, both relay coils and the fans run from a third PSU, a Mean Well LRS-35-12 (12 V / 3 A / 36 W) on the new J_12V_IN (12V_IN; F1 2 A, SS34, SMBJ12A, 100 µF); J_HU_PWR / 12V_HU, the donor-rail requirements, the characterisation task and the IRM-20-12 fallback are withdrawn and nothing is tapped from the heating unit (not opened, CAN port only). K_SAFE returns to the unit's AC inlet loom; the CSC stays up on its own PSU during E-stop. Unit table, system diagram, component rows, §5.1 (connector list), pin block, §10 SELV note (CAN port only), power diagram (three PSU boxes) and budget (12V_IN ~1.3 / 1.4 A of 36 W), §12.1 safety bullet, routing, ground diagram, BOM (+$12 LRS-35-12, IRM-20-12 line removed, total $857 - $967 → $869 - $979), §18 / §19 checklists and E-stop wording updated |
