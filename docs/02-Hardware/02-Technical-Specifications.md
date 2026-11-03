---
created: 2026-02-15
modified: 2026-11-04
version: 5.5
status: Draft
---

# Technical Specifications

## 1. Heating System

### 1.1 Induction Heater (Microwave Surface Module)

The primary cooking element is a commercial microwave induction surface — a self-contained module with its own power coil, driver electronics, and AC power stage. The module handles all high-voltage power electronics internally and exposes a CAN bus interface for external control. This eliminates the need for custom IGBT driver circuits.

- **Rated Power:** 1,800W maximum
- **AC Input:** 220-240V, 50Hz single-phase (standard Indian household outlet) — connected directly to module
- **Coil Diameter:** 180-220mm (matched to pot base, internal to module)
- **Temperature Range:** 60-250C surface temperature
- **Control:** Temperature loop inside the module on its own under-glass sensor; the RV1106 sends a setpoint (HEAT_SET_TEMP) or power level (HEAT_SET_POWER) over the shared isolated CAN bus and reads the measured temperature back; the STM32 can only force the module off. No IR thermometer in Epicura
- **Control Interface:** CAN 2.0B at 500 kbps, isolated 3-node bus (RV1106 via MCP2518FD, STM32 FDCAN1, module MCU) on the Unified PCB's isolated CAN port (J_CAN_HEAT)
- **Pot Detection:** Internal to module (won't heat without compatible pot)
- **Internal Safety:** Pot detection, thermal cutoff, overcurrent protection (all module-internal)

### 1.2 Power Level Profiles

| Profile | Power (W) | Temp Range (C) | Use Case | Duty Cycle |
|---------|-----------|-----------------|----------|------------|
| **Sear** | 1,800 | 200-250 | Browning onions, tempering spices | 100% |
| **Boil** | 1,500 | 100 | Bringing water/gravy to boil | 85% |
| **Simmer** | 400-600 | 80-95 | Slow cooking dal, curry reduction | 25-35% |
| **Warm** | 200 | 60-70 | Keep-warm after cooking complete | 10-15% |
| **Off** | 0 | Ambient | Idle, cool-down | 0% |

### 1.3 Temperature Control Parameters

- **Setpoint Source:** Recipe state machine (engine thread → heat thread, same `epicurad` process on the RV1106)
- **Loop:** Module-internal PID on the module's under-glass surface sensor; no control loop in Epicura firmware
- **Feedback to Epicura:** HEAT_STATUS (0x180, 10 Hz) `surface_temp_dC` — pot-bottom temperature, used for stage transitions (±5C for 3 readings) and the STM32 cut-off
- **Command:** HEAT_SET_TEMP (0x100: target, ramp ≤ 5C/s, max power) or HEAT_SET_POWER (0x103) re-sent at 2 Hz as keep-alive; the module drops to 0 after 1 s without a refresh
- **Overshoot:** Module-internal; recipe tolerance ±5C
- **Safety Cutoff:** CAN coil over-temp, surface_temp >270C or HEAT_FAULT → STM32 sends HEAT_ON_OFF=0, broadcasts E_STOP and opens the relay, independently of the RV1106

## 2. Sensor Specifications

### 2.1 Camera Module

| Parameter | Value |
|-----------|-------|
| Module | IMX415-98 8 MP camera module (Luckfox, ISP tuning file in SDK) |
| Resolution | 1280x720 at 30fps (720p; sensor native 3840×2160) |
| Interface | MIPI CSI-2 (4-lane FPC) to the RV1106 hardware ISP |
| Sensor Size | 1/2.8" |
| Field of View | 98 deg diagonal, 84 deg horizontal, 44 deg vertical (3.95 mm F2.0 lens, distortion < 1%) |
| White Balance | ISP auto white balance with LED ring compensation |
| Illumination | WS2812B LED ring (12-16 LEDs, STM32-driven) or white LED ring with diffuser |
| Mounting | Overhead gantry, ~30cm above pot rim (44 deg vertical FOV covers ~24cm at 30cm) |
| Purpose | Food color/texture analysis, stage detection via CV |

### 2.2 Cooking Temperature

No IR thermometer. The induction module's under-glass sensor is the only cooking-temperature source; it is reported in HEAT_STATUS at 10 Hz with 0.1C resolution (see §1.3 and [[03-Sensors-Acquisition|Sensors & Acquisition]] §3). Food-state decisions come from the camera.

### 2.3 Battery Pack Monitoring

| Parameter | Value |
|-----------|-------|
| Pack voltage | 100k/22k divider → STM32 PC1 (ADC1_IN7), 1 Hz, ±2% |
| Charger status | TP5100 CHRG / STDBY → PCF8574 #2 P6 / P7 |
| Pack temperature | 10k NTC on the cells → TP5100 TEMP pin (charge inhibit outside 0-45C) |

## 3. Data Storage

### 3.1 Storage Architecture

| Storage | Medium | Capacity | Purpose |
|---------|--------|----------|---------|
| **eMMC** | On-board Luckfox Pico Zero | 8 GB | A/B boot + rootfs (squashfs), oem, data (SQLite DB, images, logs, OTA staging), userdata |
| **SD Card** | MicroSD slot on Pico Zero | 16-64 GB (optional) | Storage expansion only: recipe backup, logs archive, user media |
| **RAM** | DDR3L in-package on RV1106G3 | 256 MB | Runtime, NPU inference, LVGL frame buffer (~80 MB steady, ~95 MB peak) |

### 3.2 Recipe Database

- **Format:** JSON or YAML per recipe file
- **Recipe Count:** 100+ initial, expandable via OTA
- **Size per Recipe:** ~30-50 KB (steps, temps, timings, images)
- **Total DB Size:** ~5-10 MB initial
- **Storage:** SQLite index + individual recipe files on eMMC
- **Sync:** Cloud download to local, offline fallback guaranteed

### 3.3 Cooking Logs

- **Format:** SQLite database
- **Fields:** Timestamp, recipe ID, step transitions, temperatures (module surface + coil, from CAN), weights, durations, errors, user feedback
- **Retention:** Last 500 cook sessions (~50 MB)
- **Export:** JSON via app or USB

### 3.4 User Preferences

- **Format:** JSON configuration file
- **Contents:** Spice levels, allergens, dietary restrictions, portion sizes, WiFi credentials
- **Backup:** Synced to cloud account when connected

## 4. Power Specifications

| Parameter | Specification |
|-----------|---------------|
| **AC Input** | 220-240V, 50Hz, single-phase |
| **Maximum Draw** | <2,000W (1,800W induction + 75W system) |
| **Fuse Rating** | 10A (IEC C14 inlet with integrated fuse) |
| **PSU** | Mean Well LRS-75-24 (24V / 3.2A / 76.8W) |
| **24V Rail** | 24V / 3.2A — main bus from PSU; feeds actuators (12V, 6.5V rails), switched 24V to the stirring motor, safety relay, VSYS |
| **VSYS** | Schottky-OR of the 24V rail and the 2S battery (SS54 ×2, 100µF hold-up) — input of the TPS54531 5V buck; passive switch-over to battery on PSU loss |
| **5V Rail** | 5V_MAIN from TPS54531 (VSYS→5V, 5A) — Luckfox Pico Zero (J_AP), 4" LCD, LED ring, B0505S isolated CAN supply, AMS1117; two-source Schottky-OR with 5V_USB → 5V_MERGED → 3.3V |
| **USB-C Power** | 5V from USB-C VBUS via 500mA polyfuse — enables standalone STM32 programming/debug without 24V PSU |
| **Li-Ion Battery** | 2S1P Li-ion 18650 pack (7.4V nominal, 2,500-3,000 mAh, ~19 Wh) with protection module and NTC, on J_BAT (JST-XH 3-pin) — TP5100 switching charger on the Unified PCB (8.4V, 0.5A from the 12V rail) — keeps the whole 5V logic domain (RV1106 + LCD + STM32 + CAN) alive through outages |
| **3.3V Rail** | 3.3V / 500mA (LDO from 5V_MERGED on Unified PCB) — STM32, I2C devices, CAN transceiver logic sides |
| **Standby Power** | <5W (RV1106 idle, display off, induction off) |
| **PSU Type** | Mean Well enclosed AC-DC, single 24V output |
| **Efficiency** | >87% at full load (Mean Well LRS-75 series) |

### 4.1 Battery Backup Specifications

A 2-cell Li-ion pack on the Unified PCB replaces the external 12V UPS and the single-cell micro-UPS of earlier revisions. It powers the 5V logic domain only, so the system can detect AC loss, checkpoint the cooking session, keep the UI and Wi-Fi alive, and resume when mains returns.

| Parameter | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| Configuration | 2S1P Li-ion | 2S1P 18650, 2,600 mAh (~19 Wh) | 6.0-8.4V into the TPS54531 (VIN 3.5-28V) via the VSYS diode-OR |
| Protection | Pack PCM: per-cell OV/UV, OC, SC | PCM with balancing | IEC 62133-2 / IS 16046 certified cells and pack (BIS) |
| Charger | TP5100 on the Unified PCB, 2S mode (8.4V) | — | 0.5A CC/CV from the 12V rail, NTC-gated (0-45C), CHRG/STDBY to the STM32 |
| Charge time | — | 5-6 h from empty | Charges whenever the PSU is on |
| Runtime | 2 h | > 4 h | ~3W logic load (RV1106 + 4" LCD + STM32 + CAN) |
| Switch-over | Passive diode-OR | — | No gap: VSYS falls from ~23.5V to the pack voltage; the buck keeps regulating |
| Monitoring | Pack voltage on STM32 PC1 (1 Hz) | — | Warning at 6.4V, shutdown request at 6.2V, PCM cut-off ~5.6V |
| Connector | J_BAT, JST-XH 2.5 mm 3-pin (B+, B−, NTC) | — | Pack in the enclosure's cool zone (< 45C), away from the induction module and PSU |

> [!tip]
> During AC power failure only the 5V domain (RV1106 + LCD + STM32 + CAN transceivers) remains powered. The 24V rail (stirring motor, dispensers, induction) goes down immediately. The STM32 detects 24V loss via the COMP1 comparator (<100µs), turns the LED ring off, and reports POWER_FAIL with the pack voltage to the RV1106, which checkpoints the session. If power returns within 5 minutes cooking auto-resumes; otherwise the user is prompted. At 6.2V the RV1106 syncs and halts and the STM32 enters STOP mode.

### 4.2 Power Budget Breakdown

| Subsystem | Typical (W) | Peak (W) |
|-----------|-------------|----------|
| Induction heater | 600 | 1,800 |
| RV1106 + camera + 4" LCD | 1.5 | 3 |
| STM32 + sensors | 2 | 3 |
| CAN servo stirring motor (24V) | 12 | 48 |
| Battery charger (TP5100, while charging) | 4 | 5 |
| Dispenser servos (FID 3 + CID 1, 6.5V, one at a time) | 0.5 | 20 |
| SLD pumps (x2) + solenoids (x2) | 0 | 16 |
| LED ring | 2 | 5 |
| Exhaust fan | 1 | 3 |
| PSU losses | 10 | 30 |
| **Total** | **634** | **1,846** |

## 5. Performance Requirements

| Parameter | Target | Notes |
|-----------|--------|-------|
| CV Inference Latency | <500ms | Food stage classification per frame |
| Temperature Setpoint Keep-alive | 2Hz | HEAT_SET_TEMP refresh from the RV1106 `heat` thread; the module regulates internally |
| Motor Control Loop | 50Hz (20ms) | Stir motor velocity commands and feedback on the STM32 (FDCAN2) |
| UI Response Time | <200ms | Touch-to-visual feedback on display |
| System Boot Time | <30s | Power-on to recipe selection screen |
| Temperature Accuracy | +/-5C | Module surface_temp to a thermocouple on the pot bottom |
| Dispensing Accuracy | ±10% per ¼ tsp dose (FID), ±5% (SLD) | FID by volumetric measure wheel (open loop), CID whole slot, SLD by dedicated per-reservoir load cells (2× 2 kg) |
| Camera Latency | <100ms | Capture to frame available in memory |
| Recipe Step Transition | <2s | From stage detection to actuator response |
| WiFi Connection | <10s | Auto-reconnect to saved network |
| OTA Update | <5 min | Full recipe DB refresh over WiFi |

## 6. Communication Interfaces

| Interface | Protocol | Speed | Endpoints | Purpose |
|-----------|----------|-------|-----------|---------|
| RV1106 <-> STM32 <-> Microwave Surface | CAN 2.0B (isolated port) | 500 kbps | RV1106 SPI0 CS1 → MCP2518FD + ISO1050DUB #2; STM32 FDCAN1 (PB8/PB9) + ISO1050DUB #1; J_CAN_HEAT <-> module CAN port | Commands, telemetry, heartbeat, heater setpoints and status (RV1106), heater off-switch (STM32); 5 kV isolation |
| STM32 <-> Stirring Motor | CAN 2.0B (regular port) | 1 Mbps | STM32 FDCAN2 (PB12/PB13) + SN65HVD230; J_CAN_STIR <-> motor CAN; 24V on J_STIR_PWR | Velocity/position commands at 50 Hz, motor feedback (rpm, current, temperature) |
| RV1106 <-> STM32 (service) | UART | 1,000,000 baud | RV1106 UART2 (header 8/10) <-> STM32 USART2 (PA2/PA3) | STM32 firmware update (ST bootloader via BOOT0/NRST) and debug only |
| RV1106 <-> Camera | MIPI CSI-2 | 4-lane | Pico Zero CSI FPC <-> IMX415-98 | 720p frames into the hardware ISP for CV |
| RV1106 <-> Display | SPI | 50 MHz | RV1106 SPI0 <-> 4" ST7796S 480x320 (FT6336U touch module, 14-pin) | UI rendering (fbtft, LVGL) |
| RV1106 <-> Touch | I2C | 400 kHz | RV1106 I2C3 <-> FT6336 | Touch input events |
| STM32 <-> SLD Load Cells | SPI-like GPIO | 10 Hz | STM32 GPIO <-> 2× HX711 | SLD reservoir weight measurements |
| STM32 <-> Exhaust Fan | PWM | 25 kHz | STM32 TIM4 CH3 <-> fan 4-pin | Fume extraction speed |
| RV1106 <-> WiFi | 802.11ax (WiFi 6, 2.4 GHz) | - | Onboard Pico Zero radio | Cloud, OTA, on-demand RTSP live view |
| RV1106 <-> BT | BLE 5.2 | 2 Mbps | Onboard Pico Zero radio | Initial app pairing, WiFi provisioning |

## 7. Related Documentation

- [[01-Epicura-Architecture|Hardware Architecture & Wiring Diagrams]]
- [[03-Sensors-Acquisition|Sensors & Data Acquisition]]
- [[04-Mechanical-Design|Mechanical Design]]
- [[05-Exhaust-Fume-Management|Exhaust & Fume Management]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]

#epicura #technical-specifications #hardware

---

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-16 | Manas Pradhan | Update power budget and dispensing accuracy for P-ASD pneumatic redesign |
| 3.0 | 2026-02-20 | Manas Pradhan | Updated CAN interface row: transceiver (ISO1050DUB) now on Driver PCB, FDCAN1 signals route via J_STACK pins 19-20 |
| 5.0 | 2026-03-09 | Manas Pradhan | Updated power specifications for 3-source 5V architecture (USB-C + Li-Ion battery + UPS), added USB-C and battery power entries |
| 4.0 | 2026-02-20 | Manas Pradhan | Replaced DS3225 servo with 24V BLDC motor in communication interfaces and power budget; servo PWM row → BLDC PWM+EN+DIR row |
| 5.1 | 2026-11-04 | Manas Pradhan | Application processor changed from Raspberry Pi CM5 to Luckfox Pico Zero (RV1106G3): SC3336 camera at 720p, 8 GB eMMC / 256 MB RAM, 4" ST7796S SPI LCD + FT6336 touch, UART 1 Mbps bridge on USART2, Wi-Fi 6 / BT 5.2; power budget and UPS runtime updated |
| 5.2 | 2026-11-04 | Manas Pradhan | Power budget and dispensing accuracy updated for servo-carousel FID/CID (Dispenser Servo Block replaces P-ASD pneumatics and CID stepper/linear actuator) |
| 5.3 | 2026-11-04 | Manas Pradhan | Camera IMX415-98 IR-CUT with specified FOV; CAN alternative for the STM32 link removed; display module part named |
| 5.4 | 2026-11-04 | Manas Pradhan | Isolated CAN bus shared by RV1106, STM32 and the induction surface replaces the UART bridge (UART2 kept as service link); temperature PID moved to the RV1106 heat thread; control, PID and interface rows updated |
| 5.5 | 2026-11-04 | Manas Pradhan | IR thermometer dropped (module-internal temperature control, HEAT_SET_TEMP + HEAT_STATUS surface_temp); stirring motor is a CAN servo on the Unified PCB's regular CAN port (FDCAN2); external 12V UPS and single-cell micro-UPS replaced by a 2S Li-ion pack with on-board TP5100 charger and VSYS diode-OR; power, performance and interface tables updated |
