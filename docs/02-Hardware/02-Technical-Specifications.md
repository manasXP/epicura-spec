---
created: 2026-02-15
modified: 2026-11-05
version: 5.16
status: Draft
---

# Technical Specifications

## 1. Heating System

### 1.1 Electric Heating Unit (Rice-Cooker Class)

The primary cooking element is a commercial electric heating unit of the premium rice-cooker class — a self-contained unit with a resistive heating plate, a spring-loaded centre temperature sensor pressed by the pot, its own relay/triac mains power stage and its own controller. The unit handles all high-voltage power electronics internally and exposes a CAN bus interface for external control. This eliminates the need for any custom mains electronics. It replaced the induction surface on 2026-11-04 as a drop-in CAN node (same HEAT_* message set); see [[../05-Subsystems/01-Electric-Heating|Electric Heating]]. Reference unit: **Philips OneChef NX5300/00** (Electric Heating §2.3) — its body is the Cooking Surface; its round 6 L inner pot is not used — Epicura's pot is a 25 × 25 × 12 cm rounded-square non-stick pot (≈ 7.3 L brim, 6 L max fill; [[04-Mechanical-Design|Mechanical Design]] §2.2); its 2,280 W nameplate includes the air-fryer lid heater, the base plate alone is expected at 1,000–1,300 W.

- **Rated Power:** 1,300W maximum (assumed, unit TBD; premium rice-cooker units are 1,000-1,400W)
- **AC Input:** 220-240V, 50Hz single-phase (standard Indian household outlet) — connected directly to the unit
- **Plate Diameter:** Est. ~220 mm (internal to the unit), centred under the flat base of the 250 × 250 × 120 mm rounded-square pot, which overhangs it by ~15 mm on all sides
- **Temperature Range:** 60-200C at the centre sensor (reference unit 80-200C; keep-warm at 60-70C to be confirmed with the OEM)
- **Preheat Ramp:** ~2-4 C/s (plate-limited); preheat 1-2 min
- **Control:** Temperature loop inside the unit on its own centre (pot-bottom) sensor; the RV1106 sends a setpoint (HEAT_SET_TEMP) or power level (HEAT_SET_POWER) over the shared isolated CAN bus and reads the measured temperature back; the STM32 can only force the unit off. No IR thermometer in Epicura
- **Control Interface:** CAN 2.0B at 500 kbps, 3-node bus on the CSC's isolated CAN port #1 (ISO1050DUB #1, J_CAN_HEAT): DU STM32 FDCAN1 + non-isolated SN65HVD230 on the Unified PCB v5.0 in the Dispensing Unit (a transparent gateway for the RV1106 over its UART host link), STM32 FDCAN1 on the Cooking Surface Controller, heating unit MCU; the bus reaches the DU over the dock (J_DOCK pins 3-5; pad 5 GND_ISO tied to the DU ground). The unit's CAN port must be SELV (isolated inside the unit from its mains side)
- **Pot Detection:** Internal to the unit — the pot presses the spring-loaded centre sensor and the unit reports `pot_detected` (won't heat without a pot); the 25 cm rounded-square non-stick pot (6 L max fill); any flat-bottomed pot that covers the plate and fits the well is accepted
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
| Illumination | White LED ring (12-16 LEDs, 5000 K, CRI ≥ 90) with diffuser, PWM-dimmed by the DU STM32 TIM1 on SET_LED from the RV1106 (Q_LED on the Unified PCB, 1 kHz; OFF 0 % / NIGHT 30 % / CAPTURE 100 %, ≤ 1 A on 5V_MAIN) |
| Mounting | Dispensing Unit underside, centred over the pot and looking straight down behind a sealed borosilicate window, 20-30 cm above the pot rim (nominal 30 cm; 44 deg vertical FOV covers ~24cm at 30cm) |
| Purpose | Food color/texture analysis, stage detection via CV |

### 2.2 Cooking Temperature

No IR thermometer. The heating unit's centre (pot-bottom) sensor is the only cooking-temperature source; it is reported in HEAT_STATUS at 10 Hz with 0.1C resolution (see §1.3 and [[03-Sensors-Acquisition|Sensors & Acquisition]] §3). Food-state decisions come from the camera.

### 2.3 Battery Pack Monitoring

| Parameter | Value |
|-----------|-------|
| Pack voltage + current | INA219 #2 (0x44, 10 mΩ shunt in the BAT+ path) on the Unified PCB v5.0, read by the DU STM32 over I2C1 at 1 Hz and reported to the RV1106 in DU_STATUS (0x311) → state of charge; warning at 6.4 V, checkpoint + halt at 6.2 V |
| Charger status | TP5100 CHRG / STDBY → PCF8574 #2 P6 / P7 (DU STM32 I2C1), flags in DU_STATUS |
| Dock | DOCK_SENSE_A (low = docked) and DOCK_PWR_OK (DOCK_24V present, active-low) → DU STM32 PB3 / PB5 (EXTI + 1 Hz), reported to the RV1106 in DU_STATUS flags |
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
| **Maximum Draw** | <2,000W (1,300W heater, assumed + ~190W system: the PSU ratings of the two 76.8W LRS-75-24 and the 36W LRS-35-12, not their load) |
| **Fuse Rating** | 10A (IEC C14 inlet with integrated fuse) |
| **PSU** | Three Mean Well PSUs in the CS rear, one customer each: 2× LRS-75-24 (24V / 3.2A / 76.8W each) — #1 for the Dispensing Unit only (dock charge feed; −V bonded to the CSC ground at J_DU_IN), #2 for the Stirring Unit (output floating, AC input through the pilot relay K_SU) — and 1× LRS-35-12 (12V / 3A / 36W, 99 × 82 × 30 mm, AC input unswitched) for the CSC, the fans and the relay coils (12V Rail below). Neither 24V PSU powers the CSC and nothing is tapped from the heating unit |
| **24V Rail (DU PSU)** | 24V / 3.2A from LRS-75-24 #1 in the Cooking Surface — enters the CSC on J_DU_IN (F_DU 3A, SS54, SMBJ24A → 24V_DU) and feeds only the switched DOCK_24V (Q_DOCK, F_DOCK 2A) to the Dispensing Unit over the dock; nothing on the CSC runs from it; ~0.6A typical, ~1.6A peak (an LRS-50-24 would do; LRS-75-24 kept for a single part number) |
| **12V Rail (CSC PSU)** | 12V / 3A from the Mean Well LRS-35-12 in the Cooking Surface, to the CSC on J_12V_IN (XT30; F1 2A polyfuse, SS34, SMBJ12A, 100µF → 12V_IN) — powers the CSC, the two 12V exhaust fans and the K_SAFE / K_SU relay coils; ~1.3A typical, ~1.4A peak (≈ 17 W of 36 W, > 50 % headroom). The PSU's −V is the CSC ground; its AC input is unswitched (live whenever the appliance is on), so the CSC boots independently of K_SAFE and K_SU. Nothing is tapped from the heating unit, which is not opened; K_SAFE cuts the unit's AC inlet |
| **24V Rail (SU)** | 24V_SU / GND_SU from LRS-75-24 #2, output floating (never bonded to the CS ground) — crosses the CSC's SU island (J_SU_IN → F_SU 5A → J_STIR_PWR) into the J_SU harness to the stirring motor; 1.0A typical, 3.0A peak; AC input cut by K_SU (STM32 PB4 → Q_KSU → J_SAFE 5), default off at reset, opened on E-stop, fault and DU_UNDOCKED |
| **CS Rails (CSC)** | 12V_IN straight to the fans and the K_SAFE + K_SU relay coils (no 24→12V buck); MP1584EN 12→5V → AMS1117-3.3 (STM32, ISO1050DUB #1 and #3 logic side); B0505S-1WR3 #1 → 5V_ISO/GND_ISO, the bus side of ISO1050DUB #1 (port #1), referenced to the DU ground at dock pin 5; pin 6 (5V_ISO) reserved; B0505S-1WR3 #2 → 5V_ISO2/GND_SU, the stir port's bus side in the floating SU domain |
| **Dock (J_DOCK)** | 8-contact magnetic pogo connector (2A/pin): DOCK_24V, GND, CAN_H, CAN_L, GND_ISO (tied to the DU ground on the Unified PCB), 5V_ISO (reserved, not connected on the DU), DOCK_SENSE_A, DOCK_SENSE_B — pads are dead when the DU is lifted (Q_DOCK enabled only while DOCK_SENSE_B is low) |
| **VSYS (DU)** | Schottky-OR (SS54) of DOCK_24V and BAT+ on the Unified PCB v5.0 — input of the TPS54531 5V buck and the 6V dispenser buck; docked ≈ 23.5V and the pack does not discharge; lifted or mains lost 6.0-8.4V from the pack; passive, no gap |
| **5V Rail (DU)** | 5V_MAIN from TPS54531 (VSYS→5V, 5A) — Luckfox Pico Zero (J_AP), 4" LCD, white LED ring (≤ 1A, PWM), buzzer, AMS1117-3.3 → 3.3V logic (DU STM32G0B1RE, PCA9685, PCF8574 #2, INA219 ×2, SLD Hall switches ×6, SN65HVD230, TB6612 VCC) |
| **6V Dispenser Rail (DU)** | 6V_DSP from MP1584EN #2 (VSYS→6.0V), switched by Q_DSB (PCF8574 #2 P4), 3A PTC, 1000µF — DSB servos (J_DSB1-4), 6V SLD pumps (TB6612 VM: peristaltic oil, diaphragm water); one servo or pump at a time, rail off when idle |
| **USB-C Power** | 5V from the CSC's USB-C (J_USB, bench only) OR'd into its 3.3V — standalone STM32 DFU/CDC with J_12V_IN disconnected; no USB-C on the Dispensing Unit |
| **Li-Ion Battery** | 2S2P 18650 Li-ion pack (7.4V nominal, 5,200 mAh, ~38 Wh) with protection module and NTC, on J_BAT (JST-XH 3-pin) — the Dispensing Unit's primary supply; TP5100 switching charger on the Unified PCB (8.4V, 1.0A from DOCK_24V via MP1584EN #1 12V) charges only while docked |
| **3.3V Rail** | AMS1117-3.3 on each board: Unified PCB (DU STM32, I2C devices, SN65HVD230) and CSC (STM32, ISO1050DUB #1 and #3 logic, B0505S #1 / #2 input) |
| **Standby Power** | <5W (RV1106 idle, display off, heater off) |
| **PSU Type** | Mean Well enclosed AC-DC: 2× LRS-75-24 (single 24V output, one part number; #2 floating) + 1× LRS-35-12 (single 12V output) |
| **Efficiency** | >87% at full load (Mean Well LRS-75 series) |

### 4.1 Battery Specifications (Dispensing Unit Primary Supply)

A 2-cell Li-ion pack on the Unified PCB v5.0 is the Dispensing Unit's primary supply: the DU has no cable, so the pack runs the RV1106, LCD, logic and dispensers whenever the unit is lifted off, and keeps the brain alive through a mains outage so the session can be checkpointed and resumed when mains returns. While docked, VSYS is fed from DOCK_24V and the pack only charges.

| Parameter | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| Configuration | 2S Li-ion | 2S2P 18650, 5,200 mAh (~38 Wh) | 6.0-8.4V into the TPS54531 (VIN 3.5-28V) via the VSYS diode-OR |
| Protection | Pack PCM: per-cell OV/UV, OC, SC | PCM with balancing | IEC 62133-2 / IS 16046 certified cells and pack (BIS) |
| Charger | TP5100 on the Unified PCB, 2S mode (8.4V) | — | 1.0A CC/CV (R_CS = 0.1 Ω) from DOCK_24V via MP1584EN #1 (12V), NTC-gated (0-45C), CHRG/STDBY to the DU STM32 via PCF8574 #2, relayed in DU_STATUS |
| Charge time | — | ≈ 5.5 h from empty | 1.0 A into 5,200 mAh (0.2 C); charges only while docked |
| Runtime (lifted) | 2 h | > 12 h | ~3W load (RV1106 + 4" LCD + logic); a full session docked draws from the dock, not the pack |
| Switch-over | Passive diode-OR | — | No gap: VSYS falls from ~23.5V to the pack voltage; the buck keeps regulating |
| Monitoring | INA219 #2 (voltage + current → state of charge) on DU STM32 I2C1, 1 Hz, in DU_STATUS | — | RV1106 self-manages: warning banner at 6.4V, checkpoint + halt at 6.2V, PCM cut-off ~5.6V last resort; battery indicator always visible on the DU UI |
| Connector | J_BAT, JST-XH 2.5 mm 3-pin (B+, B−, NTC) | — | Pack in the Dispensing Unit — cool zone by definition (< 45C), away from the heating unit and PSU |

> [!tip]
> **AC power failure (docked):** DOCK_PWR_OK goes inactive while DOCK_SENSE_A still reads docked, confirmed by a TELEMETRY timeout (300 ms). The DU keeps running on its pack; the heater and stir motor are already down with the 24V rail. The RV1106 checkpoints the session and auto-resumes when TELEMETRY returns within 5 minutes (the STM32 reboots in < 1 s after mains returns), prompts the user if < 30 minutes, ERROR beyond. **Unit lifted:** DOCK_SENSE_A goes high → PAUSED (UNIT_LIFTED); the heater stops ≤ 1 s by keep-alive loss and the STM32 holds safe on DOCK_SENSE_B; resume only by user tap after re-docking. At 6.2V the RV1106 checkpoints and halts; the next boot enters RECOVERING.

### 4.2 Power Budget Breakdown

| Unit | Subsystem | Typical (W) | Peak (W) |
|------|-----------|-------------|----------|
| CS | Electric heating unit (1,300W assumed) | 450 | 1,300 |
| CS | CSC (STM32, transceivers, two relay coils; from the LRS-35-12) | 1 | 2 |
| CS | Exhaust fans ×2 (12V, from the LRS-35-12) | 1 | 3 |
| CS | PSU losses | 10 | 30 |
| SU | CAN servo stirring motor (24V_SU from LRS-75-24 #2 via J_SU; 1.0A typical, 3.0A peak) | 24 | 72 |
| DU | RV1106 + camera + 4" LCD | 1.5 | 3 |
| DU | Unified PCB logic (DU STM32, I2C devices) + CAN node | 0.5 | 1 |
| DU | Battery charger (TP5100, 1.0A, while charging) | 8 | 12 |
| DU | Dispenser servos (FID 3 + CID 1, 6V, one at a time) | 0.5 | 20 |
| DU | SLD pumps (x2, 6V, one at a time; no solenoids) | 0 | 4 |
| DU | White LED ring (CAPTURE only) | 0 | 5 |
| | **Total** | **~495** | **~1,453** (peaks not coincident) |

The Dispensing Unit draws from DOCK_24V while docked (the pack only charges) and from its pack when lifted (~3 W: RV1106 + LCD + logic). Each 24V PSU is sized for 76.8 W: LRS-75-24 #1 carries only the DU (dock) load, LRS-75-24 #2 only the stir motor (3.0 A peak = 72 W), so the DU peaks (one servo at a time, LED ring only during capture) and the stir-motor peak no longer share a supply; the CSC, the fans and the relay coils (≈ 17 W peak) run from their own 36 W LRS-35-12, one supply per customer.

## 5. Performance Requirements

| Parameter | Target | Notes |
|-----------|--------|-------|
| CV Inference Latency | <500ms | Food stage classification per frame |
| Temperature Setpoint Keep-alive | 2Hz | HEAT_SET_TEMP refresh from the RV1106 `heat` thread; the heating unit regulates internally |
| Motor Control Loop | 50Hz (20ms) | Stir motor velocity commands and feedback on the STM32 (FDCAN2) |
| UI Response Time | <200ms | Touch-to-visual feedback on display |
| System Boot Time | <30s | Power-on to recipe selection screen |
| Temperature Accuracy | +/-5C | Unit surface_temp (centre sensor) to a thermocouple on the pot bottom |
| Dispensing Accuracy | ±10% per ¼ tsp dose (FID), ±5% (SLD) | FID by volumetric measure wheel (open loop), CID whole slot, SLD open loop by pump Hall tach pulses × calibrated mL/pulse (drawer tanks, no load cells) |
| Camera Latency | <100ms | Capture to frame available in memory |
| Recipe Step Transition | <2s | From stage detection to actuator response |
| WiFi Connection | <10s | Auto-reconnect to saved network |
| OTA Update | <5 min | Full recipe DB refresh over WiFi |

## 6. Communication Interfaces

| Interface | Protocol | Speed | Endpoints | Purpose |
|-----------|----------|-------|-----------|---------|
| RV1106 <-> DU STM32 | UART host link | 921,600 baud 8N1 | RV1106 UART2 (J_AP pins 8/10) <-> DU STM32 USART1 (PA9/PA10) on the Unified PCB v5.0; GPIO 32 → BOOT0, GPIO 38 → NRST | COBS/CRC-framed CAN-shaped frames: bus traffic forwarded transparently both ways, DU-local block (0x220 SET_LED, 0x226 SET_BUZZER, 0x230–0x239 dispensing, 0x311 DU_STATUS, 0x3FE DU_ACK) terminated on the DU STM32; DU STM32 flashing via the ST system bootloader |
| DU STM32 <-> CSC STM32 <-> Heating Unit | CAN 2.0B (isolated port) | 500 kbps | DU STM32 FDCAN1 (PB8/PB9) + SN65HVD230 (non-isolated, DU ground) on the Unified PCB v5.0 (DU; node AP, gateway for the RV1106); STM32 FDCAN1 (PB8/PB9) + ISO1050DUB #1 + B0505S #1 on the CSC (the only barrier on this bus); J_CAN_HEAT (CSC) <-> heating unit CAN port; the bus crosses the dock on J_DOCK pins 3-5 (stub ≤ 30 cm; pin 5 GND_ISO tied to the DU ground) | Commands, telemetry, heartbeat, heater setpoints and status (RV1106 through the gateway), heater off-switch (CSC STM32), CSC firmware update (0x7E0/0x7E8); isolated at the CSC port (ground-loop barrier; the unit's CAN port must be SELV); ID map unchanged by the gateway |
| STM32 <-> Stirring Motor | CAN 2.0B (isolated port #2) | 1 Mbps | CSC FDCAN2 (PB12/PB13) + ISO1050DUB #3 + B0505S #2 (5V_ISO2/GND_SU) → J_CAN_STIR; 24V_SU from LRS-75-24 #2 on J_STIR_PWR (J_SU_IN → F_SU); both bundled in the right-pillar harness to J_SU (Micro-Fit 3.0, 5-way: 24V_SU, GND_SU, CAN_H, CAN_L, SHIELD) on the Stirring Unit; 5 kV isolation, GND_SU never bonded to the CS ground; K_SU cuts the SU PSU's AC | Velocity/position commands at 50 Hz, motor feedback (rpm, current, temperature) |
| RV1106 → CSC STM32 (firmware update) | CAN bootloader over the isolated bus, through the DU STM32 gateway | 500 kbps | 0x7E0 FW_UPDATE_REQ / 0x7E8 FW_UPDATE_RSP (OpenBLT-style in-application bootloader on the CSC) | CSC image streamed by the swupdate handler; no UART between the units. USB-C DFU on the CSC (bench) and SWD (factory) are the fallbacks |
| RV1106 → DU STM32 (firmware update) | ST system bootloader on USART1 | 921,600 → autobaud | GPIO 32 BOOT0 high, GPIO 38 NRST pulse, bootloader protocol on UART2 | DU STM32 image by the swupdate handler; dispensers held off; J_SWD on the Unified PCB for the bench |
| RV1106 <-> Camera | MIPI CSI-2 | 4-lane | Pico Zero CSI FPC <-> IMX415-98 (DU underside) | 720p frames into the hardware ISP for CV |
| RV1106 <-> Display | SPI | 50 MHz | RV1106 SPI0 <-> 4" ST7796S 480x320 (FT6336U touch module, 14-pin) | UI rendering (fbtft, LVGL) |
| RV1106 <-> Touch | I2C | 400 kHz | RV1106 I2C3 <-> FT6336 (0x38) | Touch input events |
| DU STM32 <-> DU peripherals | I2C | 400 kHz | DU STM32 I2C1 <-> PCF8574 #2 (0x21), PCA9685 (0x41), INA219 #1 (0x40), INA219 #2 (0x44) | Dispenser servos, pump direction, rail enable, charger status, dispenser-rail current (stall detection), battery monitoring |
| DU STM32 <-> SLD Hall switches | Digital GPIO (PC0–PC5) | Tach EXTI, level 1 Hz | 6× open-drain Hall on J_SLD: pump tachs, tank present, tank low | SLD open-loop metering, prime arming and level alerts (DU STM32 Dispense task; QUERY_SLD to the RV1106) |
| DU STM32 → LED ring / buzzer | PWM | 1 kHz (ring) | DU STM32 TIM1 → Q_LED (J_LED) / TIM14 → 2N7002 buzzer driver on the Unified PCB; SET_LED / SET_BUZZER from the RV1106 over the host link | Capture illumination (OFF/NIGHT/CAPTURE), audible alerts |
| STM32 <-> Exhaust Fans | PWM | 25 kHz | CSC PA6 (TIM3_CH1) + PB10 (SW PWM) → fan MOSFETs → J_FAN (12V) | Fume extraction speed (SET_EXHAUST / EXHAUST_AUTO over CAN) |
| CS <-> DU (dock) | J_DOCK 8-contact magnetic pogo | — | DOCK_24V, GND, CAN_H, CAN_L, GND_ISO (→ DU GND), 5V_ISO (reserved), DOCK_SENSE_A (→ DU STM32 PB3), DOCK_SENSE_B (→ CSC STM32 PB3) | Charge input and the isolated CAN bus across the lift-off joint; dock sense both ways; pads dead when lifted |
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
| 5.9 | 2026-11-04 | Manas Pradhan | Pot changed to a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot (≈ 7.3 L brim, 6 L max fill; Mechanical Design §2.2): §1.1 reference-unit note, plate diameter (plate centred under the overhanging flat base) and pot detection rows |
| 5.10 | 2026-11-04 | Manas Pradhan | Dispensing Unit battery doubled to 2S2P 18650, 5,200 mAh (~38 Wh; was 2S1P 2,600 mAh): lifted run time > 12 h, charge ≈ 5.5 h at 1.0 A; §1 power table and battery table updated |
| 5.13 | 2026-11-04 | Manas Pradhan | DU CAN node non-isolated (Unified PCB v5.1): SN65HVD230 replaces ISO1050DUB #2; dock pin 5 GND_ISO tied to the DU ground, pin 6 5V_ISO reserved; isolation only on the CSC's two ports; heating-unit CAN port must be SELV (selection requirement); heater control-interface bullet, rail rows, interface and dock rows updated |
| 5.12 | 2026-11-04 | Manas Pradhan | Both CSC CAN ports isolated and the Stirring Unit on its own PSU (CSC v1.3): second Mean Well LRS-75-24 (#2, floating 24V_SU / GND_SU, AC input through the pilot relay K_SU) feeds the stir motor via the CSC's SU island (J_SU_IN → F_SU → J_STIR_PWR); stir port is ISO1050DUB #3 + B0505S #2 instead of the SN65HVD230; Q_STIR dropped; PSU, 24V rail (split CS / SU), CS rails, 3.3V, maximum draw, budget (SU 24 / 72 W, total ~495 / ~1,465 W) and stir-motor interface rows updated |
| 5.11 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: DU STM32G0B1RET6 on the Unified PCB v5.0 owns dispensing, LED ring, buzzer, battery/dock monitoring and the DU CAN node (FDCAN1 + ISO1050 #2); MCP2518FD removed; RV1106 ↔ DU STM32 UART host link (921,600 baud, CAN-shaped frames, DU-local block) and BOOT0/NRST flashing added; interface, power, battery and illumination rows updated |
| 5.14 | 2026-11-05 | Manas Pradhan | CSC, fans and relay coils powered from the heating unit (CSC v1.5): new 12V_HU row (12V SELV tap off the OEM control-board supply to J_HU_PWR; SELV / 10.8–13.2V / ≥ 1.5A spare / live whenever on; not yet characterised, IRM-20-12 fallback); LRS-75-24 #1 is the DU's supply only (J_DU_IN → Q_DOCK, ~0.6 / 1.6A, −V bonded to the CSC ground); MP1584EN #1 dropped from the CS rails; PSU, maximum draw, USB-C, budget rows and the PSU paragraph updated |
| 5.15 | 2026-11-05 | Manas Pradhan | CSC, fans and relay coils on a dedicated Mean Well LRS-35-12 (CSC v1.6, reversing 5.14): the 12V_HU row becomes 12V Rail (CSC PSU) from the LRS-35-12 via J_12V_IN (F1 2A, SS34, SMBJ12A, 100µF; ~1.3 / 1.4A of 36 W; AC input unswitched); the heating-unit tap, its SELV / spare-current requirements, the characterisation task and the IRM-20-12 fallback are withdrawn, K_SAFE cuts the unit's AC inlet again; PSU (three units), maximum draw (+36 W rating), CS rails, PSU type, USB-C bench note, budget rows and the PSU paragraph updated |
| 5.16 | 2026-11-05 | Manas Pradhan | Robot-mop SLD and Ø350 mm DU disc: 5 V / 6 V rail rows (Hall switches, no solenoids), DU power row 16 W → 4 W (total peak ~1,465 → ~1,453 W), dispensing-accuracy row (open-loop tach metering), DU STM32 interface rows (I2C1 without TCA9543A; Hall GPIO instead of NAU7802) |
