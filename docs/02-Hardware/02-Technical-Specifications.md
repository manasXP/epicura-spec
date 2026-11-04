---
created: 2026-02-15
modified: 2026-11-04
version: 5.8
status: Draft
---

# Technical Specifications

## 1. Heating System

### 1.1 Electric Heating Unit (Rice-Cooker Class)

The primary cooking element is a commercial electric heating unit of the premium rice-cooker class — a self-contained unit with a resistive heating plate, a spring-loaded centre temperature sensor pressed by the pot, its own relay/triac mains power stage and its own controller. The unit handles all high-voltage power electronics internally and exposes a CAN bus interface for external control. This eliminates the need for any custom mains electronics. It replaced the induction surface on 2026-11-04 as a drop-in CAN node (same HEAT_* message set); see [[../05-Subsystems/01-Electric-Heating|Electric Heating]]. Reference unit: **Philips OneChef NX5300/00** (Electric Heating §2.3) — its body is the Cooking Surface, its 6 L non-stick inner pot is Epicura's pot; its 2,280 W nameplate includes the air-fryer lid heater, the base plate alone is expected at 1,000–1,300 W.

- **Rated Power:** 1,300W maximum (assumed, unit TBD; premium rice-cooker units are 1,000-1,400W)
- **AC Input:** 220-240V, 50Hz single-phase (standard Indian household outlet) — connected directly to the unit
- **Plate Diameter:** Matched to the 6 L inner pot base (pot 228.6 mm Ø × 150 mm; plate est. ~220mm, internal to the unit)
- **Temperature Range:** 60-200C at the centre sensor (reference unit 80-200C; keep-warm at 60-70C to be confirmed with the OEM)
- **Preheat Ramp:** ~2-4 C/s (plate-limited); preheat 1-2 min
- **Control:** Temperature loop inside the unit on its own centre (pot-bottom) sensor; the RV1106 sends a setpoint (HEAT_SET_TEMP) or power level (HEAT_SET_POWER) over the shared isolated CAN bus and reads the measured temperature back; the STM32 can only force the unit off. No IR thermometer in Epicura
- **Control Interface:** CAN 2.0B at 500 kbps, isolated 3-node bus (RV1106 via MCP2518FD on the Unified PCB v4.0 in the Dispensing Unit, STM32 FDCAN1 on the Cooking Surface Controller, heating unit MCU) on the CSC's isolated CAN port (J_CAN_HEAT); the bus reaches the DU over the dock (J_DOCK pins 3-6)
- **Pot Detection:** Internal to the unit — the pot presses the spring-loaded centre sensor and the unit reports `pot_detected` (won't heat without a pot); the unit's own 6 L non-stick inner pot (~4.8 L usable); any flat-bottomed pot of the same base fits
- **Internal Safety:** Pot detection, over-temperature cut-off, thermal fuse (all unit-internal)

### 1.2 Power Level Profiles

| Profile | Power (W) | Temp Range (C) | Use Case | Duty Cycle |
|---------|-----------|-----------------|----------|------------|
| **Sear** | 1,300 | 180-200 | Browning onions, tempering spices (200C is the unit's ceiling) | 100% |
| **Boil** | 1,040 | 100 | Bringing water/gravy to boil | 80% |
| **Simmer** | 390-520 | 80-95 | Slow cooking dal, curry reduction | 30-40% |
| **Warm** | 150 | 60-70 | Keep-warm after cooking complete | 10-15% |
| **Off** | 0 | Ambient | Idle, cool-down | 0% |

### 1.3 Temperature Control Parameters

- **Setpoint Source:** Recipe state machine (engine thread → heat thread, same `epicurad` process on the RV1106)
- **Loop:** Unit-internal PID on the unit's centre (pot-bottom) sensor; no control loop in Epicura firmware
- **Feedback to Epicura:** HEAT_STATUS (0x180, 10 Hz) `surface_temp_dC` — pot-bottom temperature, used for stage transitions (±5C for 3 readings) and the STM32 cut-off
- **Command:** HEAT_SET_TEMP (0x100: target, ramp ≤ 5C/s, max power) or HEAT_SET_POWER (0x103) re-sent at 2 Hz as keep-alive; the unit drops to 0 after 1 s without a refresh
- **Overshoot:** Unit-internal; the plate stores heat, so the pot-bottom temperature lags the command by tens of seconds; recipe tolerance ±5C
- **Safety Cutoff:** CAN element over-temp, surface_temp >230C (CRITICAL at >220C) or HEAT_FAULT → STM32 sends HEAT_ON_OFF=0, broadcasts E_STOP and opens the relay, independently of the RV1106

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
| Illumination | White LED ring (12-16 LEDs, 5000 K, CRI ≥ 90) with diffuser, PWM-dimmed by the RV1106 (Q_LED on the Unified PCB, 1 kHz; OFF 0 % / NIGHT 30 % / CAPTURE 100 %, ≤ 1 A on 5V_MAIN) |
| Mounting | Dispensing Unit underside, centred over the pot and looking straight down behind a sealed borosilicate window, 20-30 cm above the pot rim (nominal 30 cm; 44 deg vertical FOV covers ~24cm at 30cm) |
| Purpose | Food color/texture analysis, stage detection via CV |

### 2.2 Cooking Temperature

No IR thermometer. The heating unit's centre (pot-bottom) sensor is the only cooking-temperature source; it is reported in HEAT_STATUS at 10 Hz with 0.1C resolution (see §1.3 and [[03-Sensors-Acquisition|Sensors & Acquisition]] §3). Food-state decisions come from the camera.

### 2.3 Battery Pack Monitoring

| Parameter | Value |
|-----------|-------|
| Pack voltage + current | INA219 #2 (0x44, 10 mΩ shunt in the BAT+ path) on the Unified PCB v4.0, read by the RV1106 over I2C3 at 1 Hz → state of charge; warning at 6.4 V, checkpoint + halt at 6.2 V |
| Charger status | TP5100 CHRG / STDBY → PCF8574 #2 P6 / P7 (RV1106 I2C3) |
| Dock | DOCK_SENSE_A (low = docked) and DOCK_PWR_OK (DOCK_24V present, active-low) → RV1106 GPIO; edge + 1 Hz poll |
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
- **Fields:** Timestamp, recipe ID, step transitions, temperatures (unit pot-bottom + element, from CAN), weights, durations, errors, user feedback
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
| **Maximum Draw** | <2,000W (1,300W heater, assumed + 75W system) |
| **Fuse Rating** | 10A (IEC C14 inlet with integrated fuse) |
| **PSU** | Mean Well LRS-75-24 (24V / 3.2A / 76.8W) |
| **24V Rail** | 24V / 3.2A from the LRS-75-24 in the Cooking Surface — feeds the CSC (12V fans + relay coil, 5V/3.3V logic), switched 24V to the stirring motor (Q_STIR → J_STIR_PWR, in the J_SU harness) and switched DOCK_24V (Q_DOCK, F_DOCK 2A) to the Dispensing Unit over the dock |
| **CS Rails (CSC)** | MP1584EN #1 24→12V (fans, relay coil); MP1584EN #2 24→5V → AMS1117-3.3 (STM32, SN65HVD230, ISO1050DUB #1 logic side); B0505S-1WR3 → 5V_ISO/GND_ISO, the single isolated CAN domain, extended to the DU over dock pins 3-6 |
| **Dock (J_DOCK)** | 8-contact magnetic pogo connector (2A/pin): DOCK_24V, GND, CAN_H, CAN_L, GND_ISO, 5V_ISO, DOCK_SENSE_A, DOCK_SENSE_B — pads are dead when the DU is lifted (Q_DOCK enabled only while DOCK_SENSE_B is low) |
| **VSYS (DU)** | Schottky-OR (SS54) of DOCK_24V and BAT+ on the Unified PCB v4.0 — input of the TPS54531 5V buck and the 6V dispenser buck; docked ≈ 23.5V and the pack does not discharge; lifted or mains lost 6.0-8.4V from the pack; passive, no gap |
| **5V Rail (DU)** | 5V_MAIN from TPS54531 (VSYS→5V, 5A) — Luckfox Pico Zero (J_AP), 4" LCD, white LED ring (≤ 1A, PWM), buzzer, AMS1117-3.3 → 3.3V logic (PCA9685, PCF8574 #2, INA219 ×2, TCA9543A, NAU7802 ×2, MCP2518FD, ISO1050DUB #2 logic side, TB6612 VCC) |
| **6V Dispenser Rail (DU)** | 6V_DSP from MP1584EN #2 (VSYS→6.0V), switched by Q_DSB (PCF8574 #2 P4), 3A PTC, 1000µF — DSB servos (J_DSB1-4), 6V peristaltic pumps (TB6612 VM), 6V NC solenoids; one servo at a time, rail off when idle |
| **USB-C Power** | 5V from the CSC's USB-C (J_USB, bench only) OR'd into its 3.3V — standalone STM32 DFU/CDC without the 24V PSU; no USB-C on the Dispensing Unit |
| **Li-Ion Battery** | 2S1P Li-ion 18650 pack (7.4V nominal, 2,600 mAh, ~19 Wh) with protection module and NTC, on J_BAT (JST-XH 3-pin) — the Dispensing Unit's primary supply; TP5100 switching charger on the Unified PCB (8.4V, 1.0A from DOCK_24V via MP1584EN #1 12V) charges only while docked |
| **3.3V Rail** | AMS1117-3.3 on each board: Unified PCB (I2C devices, MCP2518FD, ISO1050DUB #2 logic) and CSC (STM32, SN65HVD230, ISO1050DUB #1 logic, B0505S input) |
| **Standby Power** | <5W (RV1106 idle, display off, heater off) |
| **PSU Type** | Mean Well enclosed AC-DC, single 24V output |
| **Efficiency** | >87% at full load (Mean Well LRS-75 series) |

### 4.1 Battery Specifications (Dispensing Unit Primary Supply)

A 2-cell Li-ion pack on the Unified PCB v4.0 is the Dispensing Unit's primary supply: the DU has no cable, so the pack runs the RV1106, LCD, logic and dispensers whenever the unit is lifted off, and keeps the brain alive through a mains outage so the session can be checkpointed and resumed when mains returns. While docked, VSYS is fed from DOCK_24V and the pack only charges.

| Parameter | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| Configuration | 2S1P Li-ion | 2S1P 18650, 2,600 mAh (~19 Wh) | 6.0-8.4V into the TPS54531 (VIN 3.5-28V) via the VSYS diode-OR |
| Protection | Pack PCM: per-cell OV/UV, OC, SC | PCM with balancing | IEC 62133-2 / IS 16046 certified cells and pack (BIS) |
| Charger | TP5100 on the Unified PCB, 2S mode (8.4V) | — | 1.0A CC/CV (R_CS = 0.1 Ω) from DOCK_24V via MP1584EN #1 (12V), NTC-gated (0-45C), CHRG/STDBY to the RV1106 via PCF8574 #2 |
| Charge time | — | ≈ 3 h from empty | Charges only while docked |
| Runtime (lifted) | 2 h | > 5 h | ~3W load (RV1106 + 4" LCD + logic); a full session docked draws from the dock, not the pack |
| Switch-over | Passive diode-OR | — | No gap: VSYS falls from ~23.5V to the pack voltage; the buck keeps regulating |
| Monitoring | INA219 #2 (voltage + current → state of charge) on RV1106 I2C3, 1 Hz | — | RV1106 self-manages: warning banner at 6.4V, checkpoint + halt at 6.2V, PCM cut-off ~5.6V last resort; battery indicator always visible on the DU UI |
| Connector | J_BAT, JST-XH 2.5 mm 3-pin (B+, B−, NTC) | — | Pack in the Dispensing Unit — cool zone by definition (< 45C), away from the heating unit and PSU |

> [!tip]
> **AC power failure (docked):** DOCK_PWR_OK goes inactive while DOCK_SENSE_A still reads docked, confirmed by a TELEMETRY timeout (300 ms). The DU keeps running on its pack; the heater and stir motor are already down with the 24V rail. The RV1106 checkpoints the session and auto-resumes when TELEMETRY returns within 5 minutes (the STM32 reboots in < 1 s after mains returns), prompts the user if < 30 minutes, ERROR beyond. **Unit lifted:** DOCK_SENSE_A goes high → PAUSED (UNIT_LIFTED); the heater stops ≤ 1 s by keep-alive loss and the STM32 holds safe on DOCK_SENSE_B; resume only by user tap after re-docking. At 6.2V the RV1106 checkpoints and halts; the next boot enters RECOVERING.

### 4.2 Power Budget Breakdown

| Unit | Subsystem | Typical (W) | Peak (W) |
|------|-----------|-------------|----------|
| CS | Electric heating unit (1,300W assumed) | 450 | 1,300 |
| CS | CSC (STM32, transceivers, relay coil) | 1 | 2 |
| CS | Exhaust fans ×2 (12V) | 1 | 3 |
| CS | PSU losses | 10 | 30 |
| SU | CAN servo stirring motor (24V via J_SU) | 12 | 48 |
| DU | RV1106 + camera + 4" LCD | 1.5 | 3 |
| DU | Unified PCB logic + CAN node | 0.5 | 1 |
| DU | Battery charger (TP5100, 1.0A, while charging) | 8 | 12 |
| DU | Dispenser servos (FID 3 + CID 1, 6V, one at a time) | 0.5 | 20 |
| DU | SLD pumps (x2) + solenoids (x2), 6V | 0 | 16 |
| DU | White LED ring (CAPTURE only) | 0 | 5 |
| | **Total** | **~485** | **~1,440** (peaks not coincident) |

The Dispensing Unit draws from DOCK_24V while docked (the pack only charges) and from its pack when lifted (~3 W: RV1106 + LCD + logic). The 24V PSU is sized for 76.8 W; the DU peaks (one servo at a time, LED ring only during capture) do not coincide with the stir-motor peak.

## 5. Performance Requirements

| Parameter | Target | Notes |
|-----------|--------|-------|
| CV Inference Latency | <500ms | Food stage classification per frame |
| Temperature Setpoint Keep-alive | 2Hz | HEAT_SET_TEMP refresh from the RV1106 `heat` thread; the heating unit regulates internally |
| Motor Control Loop | 50Hz (20ms) | Stir motor velocity commands and feedback on the STM32 (FDCAN2) |
| UI Response Time | <200ms | Touch-to-visual feedback on display |
| System Boot Time | <30s | Power-on to recipe selection screen |
| Temperature Accuracy | +/-5C | Unit surface_temp (centre sensor) to a thermocouple on the pot bottom |
| Dispensing Accuracy | ±10% per ¼ tsp dose (FID), ±5% (SLD) | FID by volumetric measure wheel (open loop), CID whole slot, SLD by dedicated per-reservoir load cells (2× 2 kg) |
| Camera Latency | <100ms | Capture to frame available in memory |
| Recipe Step Transition | <2s | From stage detection to actuator response |
| WiFi Connection | <10s | Auto-reconnect to saved network |
| OTA Update | <5 min | Full recipe DB refresh over WiFi |

## 6. Communication Interfaces

| Interface | Protocol | Speed | Endpoints | Purpose |
|-----------|----------|-------|-----------|---------|
| RV1106 <-> STM32 <-> Heating Unit | CAN 2.0B (isolated port) | 500 kbps | RV1106 SPI0 CS1 → MCP2518FD + ISO1050DUB #2 on the Unified PCB v4.0 (DU; bus side powered from dock 5V_ISO); STM32 FDCAN1 (PB8/PB9) + ISO1050DUB #1 + B0505S on the CSC; J_CAN_HEAT (CSC) <-> heating unit CAN port; the bus crosses the dock on J_DOCK pins 3-6 (stub ≤ 30 cm) | Commands, telemetry, heartbeat, heater setpoints and status (RV1106), heater off-switch (STM32), STM32 firmware update (0x7E0/0x7E8); 5 kV isolation |
| STM32 <-> Stirring Motor | CAN 2.0B (regular port) | 1 Mbps | CSC FDCAN2 (PB12/PB13) + SN65HVD230 → J_CAN_STIR; 24V on J_STIR_PWR (Q_STIR); both bundled in the right-pillar harness to J_SU (Micro-Fit 3.0, 5-way) on the Stirring Unit | Velocity/position commands at 50 Hz, motor feedback (rpm, current, temperature) |
| RV1106 → STM32 (firmware update) | CAN bootloader over the isolated bus | 500 kbps | 0x7E0 FW_UPDATE_REQ / 0x7E8 FW_UPDATE_RSP (OpenBLT-style in-application bootloader on the CSC) | STM32 image streamed by the swupdate handler; no UART between the units. USB-C DFU on the CSC (bench) and SWD (factory) are the fallbacks |
| RV1106 <-> Camera | MIPI CSI-2 | 4-lane | Pico Zero CSI FPC <-> IMX415-98 (DU underside) | 720p frames into the hardware ISP for CV |
| RV1106 <-> Display | SPI | 50 MHz | RV1106 SPI0 <-> 4" ST7796S 480x320 (FT6336U touch module, 14-pin) | UI rendering (fbtft, LVGL) |
| RV1106 <-> Touch | I2C | 400 kHz | RV1106 I2C3 <-> FT6336 (0x38) | Touch input events |
| RV1106 <-> DU peripherals | I2C | 400 kHz | RV1106 I2C3 <-> PCF8574 #2 (0x21), PCA9685 (0x41), INA219 #1 (0x40), INA219 #2 (0x44), TCA9543A (0x71) | Dispenser servos, solenoids, rail enable, charger status, dispenser-rail current (stall detection), battery monitoring |
| RV1106 <-> SLD Load Cells | I2C (via TCA9543A mux) | 10 Hz | RV1106 I2C3 → TCA9543A → 2× NAU7802 (0x2A, one per mux channel) | SLD reservoir weight measurements (`dispense` thread) |
| RV1106 → LED ring / buzzer | PWM | 1 kHz (ring) | RV1106 PWM → Q_LED (J_LED) / 2N7002 buzzer driver on the Unified PCB | Capture illumination (OFF/NIGHT/CAPTURE), audible alerts |
| STM32 <-> Exhaust Fans | PWM | 25 kHz | CSC PA6 (TIM3_CH1) + PB10 (SW PWM) → fan MOSFETs → J_FAN (12V) | Fume extraction speed (SET_EXHAUST / EXHAUST_AUTO over CAN) |
| CS <-> DU (dock) | J_DOCK 8-contact magnetic pogo | — | DOCK_24V, GND, CAN_H, CAN_L, GND_ISO, 5V_ISO, DOCK_SENSE_A (→ RV1106), DOCK_SENSE_B (→ STM32 PB3) | Charge input and the isolated CAN bus across the lift-off joint; dock sense both ways; pads dead when lifted |
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
| 5.6 | 2026-11-04 | Manas Pradhan | Three-unit architecture: STM32 moves to the Cooking Surface Controller (CSC) with both CAN ports, relay, fans and dock switch; Unified PCB v4.0 in the lift-off Dispensing Unit with the 2S pack as primary supply (1.0 A dock charging, INA219 #2 monitoring), 6 V dispenser rail, NAU7802 load cells and white PWM LED ring on the RV1106; isolated CAN crosses the 8-pin pogo dock; UART service link replaced by a CAN bootloader; power, battery, budget-per-unit and interface tables rewritten |
| 5.7 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit of the rice-cooker class (resistive plate, spring-loaded centre sensor, own PID, CAN port; same HEAT_* contract, no controller change): §1.1 rewritten, power 1,800W → 1,300W (assumed), profiles table re-derived (sear 200-230C, boil 80 %), pot detection by the centre sensor, `coil` → `element`, maximum draw, budget (total ~485 W / ~1,440 W peak) and interface rows updated |
| 5.8 | 2026-11-04 | Manas Pradhan | Reference unit Philips OneChef NX5300/00 named in §1.1 (donor body = Cooking Surface, 6 L non-stick pot ~4.8 L usable, 2,280 W nameplate incl. lid heater); temperature range 60-200C, sear 180-200C, plate diameter per the 6 L pot, cut-off surface_temp >230C (CRITICAL >220C) |
