---
tags: [epicura, mpu, rv1106, luckfox, functional-spec, software]
created: 2026-02-16
modified: 2026-11-04
version: 1.2
aliases: [RV1106 Spec, MPU Spec]
---

# MPU Functional Specification — Luckfox Pico Zero (RV1106G3)

> **Document ID:** EPIC-SW-MPU-001
> **Processor:** Rockchip RV1106G3, 1x Cortex-A7 @ 1.2 GHz (32-bit, NEON, FPU)
> **RAM / Storage:** 256 MB DDR3L (in-package) / 8 GB eMMC
> **Board:** Luckfox Pico Zero (no carrier board required) in slot J_AP of the Unified PCB v4.0, inside the lift-off Dispensing Unit (DU)
> **Revision:** 2026-11-04 (v1.2) — Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged: HEAT_STATUS field `coil_temp` → `element_temp`, surface_temp is the unit's centre (pot-bottom) sensor; heater wording updated throughout
> **Previous revision:** 2026-11-04 (v1.1) — Three-unit architecture: the RV1106 lives in the lift-off Dispensing Unit on the Unified PCB v4.0, battery primary (VSYS from dock 24 V or the 2S pack); it reaches the isolated CAN bus through the 8-pin dock. Ingredient dispensing (PCA9685, TB6612, solenoids, NAU7802 load cells over I2C3), the white LED ring (PWM), the buzzer (PWM), battery/dock monitoring (INA219 #2, DOCK_SENSE_A, DOCK_PWR_OK) and the STM32 CAN bootloader client (0x7E0/0x7E8) move onto the RV1106; new `dispense` thread; UART2 service link and BOOT0/NRST lines gone; UNIT_LIFTED pause added
> **Earlier revision:** 2026-11-04 — RV1106 joins the isolated CAN bus (MCP2518FD on SPI0 CS1) and sends heater setpoints (the induction module runs its own PID; no IR thermometer); Pico Zero sits in the Unified PCB slot J_AP, battery-backed; UART2 is a service link only
> **Related:** [[05-MCU-Functional-Specification]], [[02-Controller-Software-Architecture]], [[01-Tech-Stack]]

---

## 1. Overview

The RV1106 is the main application processor (AP) for Epicura. It runs Buildroot Linux (Luckfox SDK, kernel 5.10) with a single native C11 application, `epicurad`, that owns all high-level functions: recipe engine, computer vision (hardware ISP + NPU), LVGL touchscreen UI, SQLite storage, and cloud sync (REST + MQTT client). It sits on the isolated CAN bus shared with the STM32 MCU (on the Cooking Surface Controller in the base) and the electric heating unit: it sends stir and exhaust commands and heater setpoints (temperature or power), receives telemetry and the unit's measured temperature, and keeps the setpoint alive in its `heat` thread; the temperature loop itself runs inside the heating unit. The Pico Zero plugs into the J_AP slot of the Unified PCB v4.0 inside the **Dispensing Unit (DU)**, the top unit that lifts straight off the machine with no cable: the DU reaches the bus and the charge supply only through the 8-contact pogo dock on the Cooking Surface's left pillar. The DU's 2S Li-ion pack is its **primary supply** — VSYS is a Schottky-OR of the dock 24 V and the pack, so the RV1106 keeps running when the unit is lifted or mains fails. Everything inside the DU is local to the RV1106: ingredient dispensing (servo carousels, pumps, solenoids, load cells) in a `dispense` thread over I2C3, the camera's white LED ring and the buzzer on PWM outputs, and battery/dock monitoring. There is no UART to the STM32 any more; its firmware is updated over the CAN bus. There is no container runtime, database server, message broker or interpreter on the device.

### 1.1 Hardware Summary

| Parameter | Value |
|-----------|-------|
| SoC | Rockchip RV1106G3 (1x Cortex-A7 @ 1.2 GHz) |
| Accelerators | 1 TOPS INT8 NPU, 5 MP hardware ISP, RGA 2D engine, H.264/H.265 encoder (no decoder, no 3D GPU) |
| RAM | 256 MB DDR3L (in-package) |
| Storage | 8 GB eMMC (A/B partitioned); microSD for storage expansion only |
| Camera | MIPI CSI-2 4-lane (IMX415-98 8 MP, run at 1280×720 @ 30 fps) |
| Display | 4" 480×320 IPS LCD, ST7796S over SPI0, FT6336 capacitive touch over I2C3 |
| Networking | Wi-Fi 6 (2.4 GHz), BLE 5.2 (on-board, external antenna connector); no Ethernet |
| Board | 65 × 30 mm, 40-pin RPi-style header (28 GPIO, 3.3 V), USB-C (power + flashing), on-board mic, RTC battery header |
| CAN | MCP2518FD on SPI0 CS1 (+ ISO1050DUB #2 on the Unified PCB, bus side powered from dock 5V_ISO), SocketCAN `can0` at 500 kbps; bus reaches the DU over dock pins 3–6, so it exists only while docked |
| I2C | I2C3 (header pins 16/18, 400 kHz) is the single I2C bus of the DU: FT6336 touch, PCF8574 #2, PCA9685, INA219 ×2, TCA9543A mux → NAU7802 ×2 |
| Dispensing unit I/O | PCA9685 OE, DOCK_SENSE_A, DOCK_PWR_OK (GPIO); pump oil, pump water, LED ring, buzzer (4× PWM) |
| Power | 5V_MAIN via the J_AP slot (Unified PCB TPS54531 from VSYS = dock 24 V or the 2S pack, battery primary) or USB-C for bench; ~1 W class SoC, no heatsink |

---

## 2. Functional Requirements

### 2.1 Recipe Engine

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-001 | Parse and validate YAML recipe files (libyaml, fixed-size C struct tree) | Must | Recipe loads in <2 s; schema errors reported to UI |
| FR-MPU-002 | Execute recipe state machine (IDLE → LOADING → AWAITING_LOAD → PREHEATING → DISPENSING → COOKING → MONITORING → TRANSITIONING → COMPLETING) | Must | All state transitions match [[03-Main-Loop-State-Machine]] trigger table |
| FR-MPU-003 | Support PAUSED state with resume/cancel | Must | Timer suspended, STM32 holds temp at 50% power |
| FR-MPU-004 | Support ERROR state with retry/skip/abort | Must | Error classification determines recovery path |
| FR-MPU-005 | Log cooking session to SQLite on completion; checkpoint `session_checkpoint` every 10 s while cooking | Must | Session record includes timestamps, temps, weights, CV results; checkpoint survives power loss (WAL) |
| FR-MPU-006 | Publish session telemetry over MQTT | Should | Topic: `epicura/{device_id}/telemetry`, QoS 1, every 10 s while cooking |

### 2.2 Computer Vision

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-010 | Capture ISP self-path frames (224×224 RGB888) at 2 Hz during COOKING/MONITORING | Must | Sensor runs 1280×720 @ 30 fps; self-path sampled at 2 Hz, interval ±50 ms; zero-copy DMA buffer |
| FR-MPU-011 | Run MobileNetV2 INT8 inference on the NPU via `rknn_api` (`/oem/models/stage_mnv2_int8.rknn`) | Must | Latency 5–10 ms per frame (target <20 ms); INT8 pass-through, no CPU normalisation |
| FR-MPU-012 | Classify food stage (raw, browning, cooked, overcooked, anomaly) | Must | 3-frame majority vote; confidence ≥ 0.6 triggers state transition, else timer + temperature fallback |
| FR-MPU-013 | Detect anomalies (smoke, dry pot, overflow) | Should | Alert within 1 s of anomaly frame |
| FR-MPU-014 | Drive the white camera LED ring (12–16 LEDs, 5000 K, CRI ≥ 90, ≤ 1 A on 5V_MAIN) directly from an RV1106 PWM channel (1 kHz, `pwm-rockchip`) through Q_LED (IRLML6344 low-side) on J_LED; duty modes OFF 0 %, CAPTURE 100 %, NIGHT 30 %; no colour control and no SET_LED on the bus | Must | CAPTURE set ≥ 50 ms before every capture window and returned to the previous mode after it; duty 0 at boot, in E_STOP and before halt |
| FR-MPU-015 | Image enhancement in the ISP (dehaze, 2D/3D noise reduction, LSC, sharpening, AWB, AE) from the IMX415-98 tuning file in `/oem` | Must | No CPU image processing (no OpenCV / CLAHE); steam haze handled by ISP dehaze |

### 2.3 User Interface

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-020 | Touchscreen UI via LVGL 9 (C, software rendered) on the 4" 480×320 SPI LCD | Must | 20 Hz LVGL tick; partial redraws; full-frame refresh ≤ 50 ms |
| FR-MPU-021 | Touch-to-visual response <200 ms | Must | Measured from FT6336 evdev event to LCD update |
| FR-MPU-022 | Display state-appropriate screens per state machine | Must | Each state maps to a UI view (see §2.3.1) |
| FR-MPU-023 | On-demand "view pot" preview screen (ISP main path → RGA scale to 480×320 → framebuffer) | Should | ≤ 10 fps; active only while the screen is open; dropped under memory pressure |
| FR-MPU-024 | Recipe browser with search and filtering | Must | Full-text search via SQLite FTS5 |
| FR-MPU-025 | Buzzer on the DU driven by an RV1106 PWM channel through a 2N7002 on J_BUZZER: continuous tone in E_STOP (sounded on STATUS `safety_state = E_STOP` from the STM32 — the Cooking Surface has no buzzer), short patterns for errors, UNIT_LIFTED / battery warnings, dispense done and touch feedback | Must | E_STOP tone within 100 ms of the STATUS frame or local E_STOP; silent at boot and after halt |

#### 2.3.1 UI State Mapping

| State | UI View |
|-------|---------|
| IDLE | Recipe browser |
| LOADING | "Validating…" spinner |
| AWAITING_LOAD | Ingredient checklist, live weight readout |
| PREHEATING | Progress bar, ETA countdown |
| DISPENSING | Ingredient name + weight bar (e.g. "Dispensing oil — 30 g") |
| COOKING | Timer, temperature graph, stir indicator |
| MONITORING | CV confidence overlay, "Analyzing…" |
| TRANSITIONING | "Stage 3/6 complete — next: Add Dal" |
| COMPLETING | "Cooking Complete!" summary, user rating prompt |
| PAUSED | "Paused" overlay with Resume / Cancel buttons |
| ERROR | Error description, Retry / Skip / Abort options |
| E_STOP | Full-screen red alert |

> [!note] Screen layouts
> Existing UX screen designs target 1280×800 and are pending redesign for 480×320. The state-to-view mapping above is unchanged.

### 2.4 Database & Cloud Sync

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-030 | SQLite 3 in-process database (WAL, JSON1, FTS5) at `/data/epicura.db` | Must | Schema mirrors the cloud PostgreSQL schema table-for-table (UUID→TEXT, JSONB→TEXT+JSON1, TEXT[]→JSON array, TIMESTAMPTZ→ISO-8601 TEXT, GIN→FTS5) |
| FR-MPU-031 | Store recipes, sessions, user preferences locally | Must | Full offline operation |
| FR-MPU-032 | Sync with cloud over REST: pull `GET /recipes/sync?since=`, push sessions/preferences/telemetry from `sync_outbox` via POST | Should | Works offline; outbox drains on reconnect; conflict resolution: last-write-wins with device priority |
| FR-MPU-033 | Cache recipe images locally under `/data/images` for offline use | Should | LRU cache, 100 MB cap |

### 2.5 MQTT Client

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-040 | libmosquitto client with direct TLS connection to the cloud broker (AWS IoT Core) | Must | No local broker; QoS 1 |
| FR-MPU-041 | Automatic reconnect with exponential backoff; spool telemetry to `sync_outbox` while offline | Should | Outbox capped at 1,000 telemetry rows, replayed on reconnect |
| FR-MPU-042 | Publish telemetry, session events, errors; subscribe to `epicura/{device_id}/cmd` | Must | QoS 1; commands handled: `live_view_start`, `live_view_stop`, `recipe_sync_now`, `ota_check` |

### 2.6 CAN Bus Node and Heater Control

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-050 | `can` thread (C, pthread, `SCHED_FIFO`) on SocketCAN `can0` — MCP2518FD on SPI0 CS1 (kernel `mcp251xfd`), 500 kbps, raw socket with ID filters | Must | Commands 0x2xx with seq byte, ACK/NAK 0x3FF matched by seq, ACK timeout 500 ms, 3 retries |
| FR-MPU-051 | Send HB_AP (0x010) every 2 s | Must | Missed heartbeat → STM32 forces the heater off and opens the relay after 5 s |
| FR-MPU-052 | The CAN bus is the only link to the STM32 (on the CSC in the Cooking Surface) and the heating unit; it reaches the DU over dock pins 3–6 (CAN_H, CAN_L, GND_ISO, 5V_ISO) and therefore exists only while the DU is docked. There is no UART between the units (UART2 and the BOOT0/NRST lines are freed) | Must | Decision 2026-11-04: RV1106 joins the bus through the MCP2518FD (SPI0 CS1); bus loss while DOCK_SENSE_A is high is expected, not a fault |
| FR-MPU-053 | Parse unsolicited TELEMETRY (0x310) at 20 Hz and STATUS (0x312) on change | Must | motor RPM/current, safety state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok), fault code (incl. 0x17 DU_UNDOCKED) available to engine/ui/sync threads via ring buffer; no battery data comes from the STM32 — pack state is read locally (§2.10) |
| FR-MPU-054 | `heat` thread (`SCHED_FIFO`): hold the stage setpoint and re-send HEAT_SET_TEMP (0x100: target, ramp ≤ 5 °C/s, max power) or HEAT_SET_POWER (0x103) at 2 Hz as the unit's keep-alive; no PID in Epicura (the heating unit regulates on its own centre sensor) | Must | Keep-alive never later than 150 ms; HEAT_ON_OFF 0 and PAUSED if HEAT_STATUS is older than 500 ms |
| FR-MPU-055 | Consume HEAT_STATUS / HEAT_FAULT (0x180 / 0x181): surface_temp drives stage transitions (±5 °C for 3 readings) and the UI graph; element temperature as secondary limit; pot-absent and unit faults → pause | Must | Reaction within one status interval (100 ms) |
| FR-MPU-057 | Mains loss is detected locally, not reported by the STM32: DOCK_PWR_OK inactive while DOCK_SENSE_A says docked, confirmed by a TELEMETRY timeout (300 ms) → checkpoint the session, PAUSED (AC Power Failure), dim the LCD, show the battery state; the DU keeps running on its pack while the heater and stir motor are already down; auto-resume to RESUMING when TELEMETRY returns within 5 min (the STM32 reboots in < 1 s after mains returns), prompt if < 30 min, ERROR beyond. Pack thresholds per §2.10 | Must | Checkpoint written within 2 s of the confirmed outage |
| FR-MPU-056 | Broadcast E_STOP (0x001, src_node = 3) on critical CV anomaly or user E-stop from the UI | Must | All nodes act without ACK |

### 2.7 OTA Updates

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-060 | A/B boot + rootfs slots on eMMC via swupdate with signed `.swu` | Must | Rollback after 3 failed boots |
| FR-MPU-061 | RSA-2048 signature verification on update images | Must | Reject unsigned or tampered images |
| FR-MPU-062 | STM32 firmware update over the isolated CAN bus: the swupdate handler streams the `.bin` to the STM32's in-application CAN bootloader with FW_UPDATE_REQ (0x7E0: seq, op = ERASE / WRITE / VERIFY / BOOT, 5 data bytes) and matches FW_UPDATE_RSP (0x7E8: seq, op, result, 4 data bytes); only while docked, in IDLE, with the heater off (see [[05-MCU-Functional-Specification]] §5.1) | Should | CRC-32 verified by the STM32 before BOOT; lost or NAK'd chunks retried by seq; an abort (undock, E_STOP) leaves the running image |

### 2.8 Live View (On Demand)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-070 | On `live_view_start`, bind VENC H.264 1280×720 @ 15 fps, 1.5 Mbps and spawn `rtsp-stream` (RTSP on :554, path `/pot`, single client) | Must | First frame available within 2 s of command |
| FR-MPU-071 | Tear down `rtsp-stream` after 60 s with no client or on `live_view_stop`; free VENC CMA buffers | Must | No encoder channel exists outside a live-view session |
| FR-MPU-072 | Streaming is best-effort and never affects cooking | Must | Any encoder or RTSP error tears down the stream only |

### 2.9 Ingredient Dispensing (`dispense` thread)

Dispensing is local to the DU and runs in-process over I2C3; nothing dispensing-related crosses the CAN bus any more (former 0x230–0x239 block and 0x311 LOADCELLS retired from the bus, see [[05-MCU-Functional-Specification]] §2.5). Mechanics per [[03-Ingredient-Dispensing]].

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-080 | `dispense` thread (`SCHED_OTHER`, 50 Hz while a sequence is active, idle otherwise) consumes an internal queue from the recipe engine with the same names and semantics as the former CAN commands: DISPENSE_FID (box_id 1–6, qty_quarter_tsp 1–40), DISPENSE_CID (slot_id 1–5), DISPENSE_SLD (channel OIL/WATER, target_g), QUERY_WEIGHT, PREFLIGHT (subsystem_mask), TARE, DISPENSER_HOME (CID / FID / both), DISPENSER_STATUS; each returns a result struct (ACK/NAK code + data) to the engine | Must | Engine never touches I2C; one command in flight at a time; NAK on invalid argument or busy |
| FR-MPU-081 | Dispenser Servo Block: 4 servos (CH0 C1 CID index, CH1 F1 FID index, CH2 F2 FID dose, CH3 F3 FID steam gate) via PCA9685 (0x41, `pwm-pca9685`), 50 Hz, 500–2,500 µs; ramped moves ≤ 3°/tick; one servo moving at a time; 6V_DSP rail enabled via PCF8574 #2 P4 only during a sequence; PCA9685 OE GPIO (10k pull-up → servos off at boot) low only while moving | Must | Rail off and OE high when idle, at boot, on E_STOP, PAUSED and before halt |
| FR-MPU-082 | FID dose: rail on, OE low; index F1 to box_id (4:3 gear-up → 60° per box); F3 → 70° (open steam gate); per dose F2 jiggle ±15° ×3, F2 → 180° (discharge), F2 → 0° (refill), ≈ 0.8 s/dose; F3 → 0°; rail off; result carries doses_done + estimated mass (doses × calibrated g/dose) | Must | Volumetric accuracy ±10 % per ¼ tsp dose |
| FR-MPU-083 | CID dispense: NAK if slot_id ≤ current position (ascending-order rule — every bin passing the aperture empties); rail on; index C1 to slot_id; dwell 2 s, wiggle ±5° ×3; rail off; result carries the new position; carousel returns to the cover position on DISPENSER_HOME and at recipe end | Must | Slot order enforced; DISPENSER_STATUS reports cid_pos, fid_box, gate_open, rail_on, busy |
| FR-MPU-084 | DSB stall detection: INA219 #1 (0x40, `ina2xx`, shunt on the switched 6V_DSP rail) current > 2.5 A for 300 ms, 3 s move timeout, or PCA9685 I2C NACK → retry once (back off 10°, re-approach) → on second failure DSB_STALL: rail off, OE high, engine ERROR | Must | Stall reported within 1 s; servos limp after fault |
| FR-MPU-085 | SLD closed loop: tare the channel's reservoir load cell (NAU7802 0x2A behind TCA9543A 0x71, ch0 oil / ch1 water, `nau7802` IIO), open the solenoid (PCF8574 #2 P0 oil / P1 water), start the 6 V peristaltic pump (TB6612: RV1106 PWM A/B, direction PCF8574 #2 P3 / P5), monitor weight loss at 10 Hz, stop the pump at 95 % of target, close the solenoid, report the final weight | Must | Accuracy ±5 %; pump never runs with its solenoid closed |
| FR-MPU-086 | TARE (zero offset held in RAM per channel) and QUERY_WEIGHT (oil_g / water_g, int16) on request; reservoir weight below the low-level threshold → SLD_LOW_LEVEL | Must | QUERY_WEIGHT answered within 100 ms; low-level prompts a refill in the UI |
| FR-MPU-087 | PREFLIGHT before a recipe: I2C presence of 0x41, 0x21, 0x40, 0x44, 0x71 and both NAU7802, load-cell data-ready, 6V_DSP rail voltage via INA219 #1 after a 100 ms enable pulse, reservoir levels vs recipe needs | Must | Result mask per subsystem; missing subsystem blocks the recipe with a user-facing reason |
| FR-MPU-088 | Dispensing faults are RV1106-detected: DSB_STALL, SLD_LOW_LEVEL, SLD_DISPENSE_ERROR (pump no-flow: no weight change 5 s after pump start, or target missed), SLD_LOAD_CELL_DRIFT (NAU7802 I2C NACK / no data-ready, or tare drift beyond limit) → engine ERROR with retry / skip / abort (§7.2) | Must | No dispensing fault code is expected from the STM32 any more |

### 2.10 Power & Dock

The DU runs on its own 2S pack; the dock only charges it and carries the CAN bus. The RV1106 self-manages the pack and detects docking, mains loss and lifting locally.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-090 | Power/dock monitor (1 Hz in the sensor path, plus a GPIO edge on DOCK_SENSE_A): `docked` (DOCK_SENSE_A low), `dock_power` (DOCK_PWR_OK active-low from the 100k/10k divider on DOCK_24V), `batt_mV` / `batt_mA` and state of charge from INA219 #2 (0x44, 10 mΩ shunt in the BAT+ path, `ina2xx`), `charging` / `complete` from TP5100 CHRG / STDBY on PCF8574 #2 P6 / P7 | Must | Values in the ring buffer for engine / ui / sync; battery indicator always visible in the UI |
| FR-MPU-091 | Battery thresholds: warning banner at 6.4 V; at 6.2 V checkpoint the session, sync, LED ring and dispenser rail off, halt (boot recovery → RECOVERING on next power); the pack PCM cuts off at ≈ 5.6 V as last resort | Must | Checkpoint written before halt; RECOVERING only ever reached because the DU pack ran out |
| FR-MPU-092 | Unit lifted: DOCK_SENSE_A high → PAUSED (reason UNIT_LIFTED) within 100 ms; the heater stops ≤ 1 s by keep-alive loss and the STM32 enters safe hold on DOCK_SENSE_B; the can thread treats the bus disappearing as expected (no CAN-link-loss error) while lifted; resume only by user tap after re-docking (no auto-resume), same 30 min food-safety ceiling | Must | No E_STOP broadcast on lift; `can0` recovers from bus-off automatically on re-dock |
| FR-MPU-093 | Charging: TP5100 at 1.0 A from DOCK_24V (≈ 3 h from empty while docked); charge fault (neither CHRG nor STDBY with the pack below 8.0 V for 10 min while docked, or pack absent at boot) → warning, cooking allowed | Should | Fault shown in the UI and logged |
| FR-MPU-094 | Docked, VSYS ≈ 23.5 V and the pack does not discharge; lifted or mains lost, VSYS = 6.0–8.4 V from the pack with no gap (passive Schottky-OR); software never switches the supply | — | Verified by lifting the unit mid-session: no reboot |

---

## 3. Hardware Interfaces

### 3.1 Header Allocation (Luckfox Pico Zero 40-pin)

Unified PCB v4.0 (Dispensing Unit board). The STM32 is no longer on this board, so the service UART and its BOOT0/NRST lines are gone.

| Header Pin | Function | Direction | Notes |
|------------|----------|-----------|-------|
| 8 | — | — | Freed (was UART2_TX service link to the STM32, now in another unit) |
| 10 | — | — | Freed (was UART2_RX) |
| SPI0_CS1 (GPIO 58) | SPI0_CS1 | Output | MCP2518FD CAN controller on the Unified PCB (≤ 20 MHz); shares MOSI/MISO/CLK with the LCD |
| spare GPIO | MCP2518FD INT | Input | Active-low; pin fixed at PCB layout |
| 19 | SPI0_MOSI | Output | LCD data (ST7796S) |
| 21 | SPI0_MISO | Input | LCD (unused by fbtft, reserved) |
| 23 | SPI0_CLK | Output | LCD clock, 50 MHz |
| 24 | SPI0_CS0 | Output | LCD chip select |
| 22 | GPIO | Output | LCD DC (data/command) |
| 26 | GPIO | Output | LCD RST |
| 12 | PWM10 | Output | LCD backlight |
| 16 | I2C3_SDA | Bidir | Single I2C bus of the DU, 400 kHz, 4.7k pull-ups: FT6336 touch 0x38 (via J_LCD), PCF8574 #2 0x21, PCA9685 0x41, INA219 #1 0x40 (6V_DSP rail), INA219 #2 0x44 (pack), TCA9543A 0x71 → NAU7802 ×2 0x2A (one per mux channel) |
| 18 | I2C3_SCL | Output | Same bus |
| 36 | GPIO | Input | Touch INT (FT6336) |
| 32 | — | — | Freed (was STM32 BOOT0) |
| 38 | — | — | Freed (was STM32 NRST) |
| 35 / 37 | UART0_TX / UART0_RX | — | Debug console (Luckfox default) |
| GPIO (fixed at layout) | PCA9685 OE | Output | Active-low; 10k pull-up → servos off at boot |
| GPIO (fixed at layout) | DOCK_SENSE_A | Input | 10k pull-up; dock pin 7 tied to GND on the CS → low = docked; edge-triggered |
| GPIO (fixed at layout) | DOCK_PWR_OK | Input | Active-low; 100k/10k divider on DOCK_24V → 2N7002; inactive = dock 24 V absent (mains lost or lifted) |
| PWM (fixed at layout) | Pump oil | Output | TB6612 PWMA |
| PWM (fixed at layout) | Pump water | Output | TB6612 PWMB |
| PWM (fixed at layout) | LED ring | Output | Q_LED (IRLML6344 low-side), 1 kHz, J_LED (5V_MAIN / LED_RET) |
| PWM (fixed at layout) | Buzzer | Output | 2N7002 → J_BUZZER |
| spare | UART3, UART4, I2C1, I2C2 | — | Available (I2C1 stays spare if layout prefers separating the touch panel from the dispensing devices) |

### 3.2 Camera (MIPI CSI)

- Connector: MIPI CSI FPC on the Pico Zero (4-lane connector)
- Interface: MIPI CSI-2, 4-lane (IMX415-98)
- Cable length: ≤150 mm (signal integrity)
- Sensor: IMX415-98 8 MP (2304×1296 native, 1/2.8"), run at 1280×720 @ 30 fps; ISP tuning file from the Luckfox SDK in `/oem`
- Paths: ISP main 1280×720 NV12 (preview / stream), ISP self-path 224×224 RGB888 (inference)

### 3.3 Display (SPI LCD)

- 4" 480×320 IPS LCD, ST7796S controller on SPI0 (50 MHz, DMA), fbtft driver, `/dev/fb0`
- Touch: FT6336 capacitive on I2C3, INT on header pin 36, evdev
- Software rendering (no GPU); full-frame refresh ~50 ms, LVGL partial redraws

### 3.4 Power

- VSYS = SS54 Schottky-OR of DOCK_24V (dock pin 1, switched on by the CSC only while the DU is seated) and BAT+ (2S1P 18650, 7.4 V nominal, 2,600 mAh ≈ 19 Wh, PCM + NTC, J_BAT). Docked: VSYS ≈ 23.5 V and the pack does not discharge. Lifted or mains lost: VSYS = 6.0–8.4 V from the pack. Passive, no gap — the battery is the primary supply
- 5V_MAIN: VSYS → TPS54531 → J_AP pins 2/4 (Pico Zero), LCD, white LED ring (≤ 1 A, PWM), buzzer, AMS1117-3.3 → 3.3 V logic (PCA9685, PCF8574 #2, INA219 ×2, TCA9543A, NAU7802 ×2, MCP2518FD, ISO1050 #2 logic side, TB6612 VCC)
- 6V_DSP: VSYS → MP1584EN #2 → 6.0 V switched dispenser rail (Q_DSB high-side via PCF8574 #2 P4, 3 A PTC, 1000 µF): servos, 6 V pumps and 6 V solenoids; off when idle
- Charging: DOCK_24V → MP1584EN #1 → 12 V → TP5100 at 1.0 A (≈ 3 h from empty while docked); CHRG / STDBY on PCF8574 #2 P6 / P7. 5V_ISO for the CAN transceiver's bus side comes from the dock (no isolated DC-DC on this board)
- Monitoring: INA219 #2 (0x44) pack voltage + current → state of charge; DOCK_PWR_OK and DOCK_SENSE_A GPIOs (§3.1)
- Typical draw: ~1.5 W board (SoC + Wi-Fi), ≤ 3 W with LCD backlight; lifted-unit load ≈ 3 W → > 5 h on the pack
- USB-C used for bench power and flashing only
- No carrier board; all signals on the Pico Zero header

---

## 4. Software Architecture

### 4.1 Operating System

- **Buildroot Linux** from the Luckfox SDK (kernel 5.10), busybox init, no systemd
- Read-only squashfs rootfs; A/B boot + rootfs slots for OTA rollback
- Kernel drivers: fbtft (ST7796S), VI/ISP/VENC/RGA (rockit), RKNN NPU, `mcp251xfd` (SocketCAN `can0`), `pwm-pca9685`, `gpio-pcf857x`, `ina2xx` (hwmon), `i2c-mux-pca954x`, `nau7802` (IIO), `pwm-rockchip` (all mainline in 5.10), wpa_supplicant + bluez5
- eMMC layout: `boot_a/b` 2×32 MB, `rootfs_a/b` 2×256 MB, `oem` 64 MB (models, ISP tuning, LVGL assets, default recipes), `data` ~6 GB (`/data/epicura.db`, images, logs, OTA staging), `userdata` 64 MB

### 4.2 Process & Thread Model

| Thread / Process | Role | Scheduling | Notes |
|------------------|------|------------|-------|
| `epicurad` / ui | LVGL 9 rendering, touch input, pot preview | `SCHED_OTHER` | 20 Hz tick, ~0.6 MB double buffer |
| `epicurad` / engine | YAML parsing, cooking state machine, SQLite checkpoint | `SCHED_OTHER` | 1 Hz tick |
| `epicurad` / cv | rockit VI/ISP, `rknn_api` inference, majority vote | `SCHED_OTHER` | 2 Hz |
| `epicurad` / can | SocketCAN `can0` RX/TX, seq/ACK matching, HB_AP heartbeat, telemetry ring buffer | `SCHED_FIFO` | Never starved by UI or sync |
| `epicurad` / heat | 2 Hz HEAT_SET_TEMP / HEAT_SET_POWER keep-alive; HEAT_STATUS surface_temp to engine/ui | `SCHED_FIFO` | HEAT_ON_OFF 0 if HEAT_STATUS stale > 500 ms |
| `epicurad` / dispense | PCA9685 ramped servo moves, 6V_DSP rail, TB6612 pumps + solenoids, NAU7802 closed loop, stall detection via INA219 #1; power/dock monitor (INA219 #2, DOCK_SENSE_A, DOCK_PWR_OK, charger status) at 1 Hz | `SCHED_OTHER` | 50 Hz while a sequence is active; all over I2C3 |
| `epicurad` / sync | libmosquitto, libcurl + mbedTLS, outbox drain, OTA check | `SCHED_OTHER` | 10 s cadence |
| `rtsp-stream` (child) | VENC H.264 720p → RTSP :554 | `SCHED_OTHER` | On demand only, ~4 MB |

Memory budget: ~80 MB steady state, ~95 MB peak (streaming + inference + UI) of 256 MB; `epicurad` ~10 MB RSS.

### 4.3 Boot Sequence

1. **U-Boot** → select active A/B slot
2. **Kernel 5.10** → fbtft, VI/ISP, mcp251xfd (`can0` up at 500 kbps), Wi-Fi/BT drivers
3. **busybox init** → mount `/data`, `/oem`; start wpa_supplicant, kernel watchdog
4. **`epicurad` start** → open SQLite → power/dock monitor (docked? on battery? RECOVERING if an interrupted session is found) → can thread (first HB_AP, if docked) → heat thread → dispense thread (OE high, 6V_DSP off, I2C3 device probe) → ISP + NPU init → sync thread
5. **UI** → display IDLE / recipe browser (target: <15 s from power-on)

### 4.4 Inter-Thread Communication

- All threads share one process; no local MQTT, no sockets
- The can thread publishes STM32 telemetry and heater status into a lock-free ring buffer read by engine, ui, sync and heat
- Engine pushes commands onto the can command queue; the can thread handles seq/ACK/retry
- Engine sets the heat thread setpoint; only the heat thread sends HEAT_SET_TEMP / HEAT_SET_POWER
- Engine pushes dispensing commands (DISPENSE_FID / CID / SLD, QUERY_WEIGHT, PREFLIGHT, TARE, DISPENSER_HOME, DISPENSER_STATUS) onto the dispense queue; the dispense thread answers with a result struct and publishes weights, carousel state and the power/dock record into the same ring buffer
- CV thread writes the latest `cv_result_t` (stage, confidence, fallback flag) for the engine
- Sync thread receives cloud commands (`cmd` topic) and dispatches to engine / live view

---

## 5. Communication Protocols

### 5.1 CAN Bus Protocol (RV1106 ↔ STM32 ↔ Heating Unit)

- **Link:** isolated CAN 2.0B bus at 500 kbps. The RV1106 joins through an MCP2518FD on SPI0 CS1 (GPIO 58, ≤ 20 MHz, INT on a spare GPIO) with ISO1050DUB #2 on the Unified PCB, whose bus side is powered from dock 5V_ISO; kernel `mcp251xfd` driver, SocketCAN `can0`. The bus crosses the dock on pins 3–6 (stub ≤ 30 cm to the CSC's termination); the isolated domain is generated once on the CSC. Lifting the DU opens the bus
- **Framing:** standard 11-bit IDs, DLC ≤ 8, little-endian payloads. Commands (0x2xx) carry `seq` in byte 0; ACK/NAK (0x3FF) echoes `seq`, `cmd_type` and a result code with up to 5 data bytes. No software CRC (CAN hardware CRC + ACK)
- **Threads:** `can` (SCHED_FIFO) owns the socket, filters `0x00x`, `0x01x`, `0x18x`, `0x3xx` and `0x7E8`; `heat` (SCHED_FIFO) re-sends the setpoint at 2 Hz
- **Timeouts:** ACK 500 ms, 3 retries; E_STOP needs no ACK. HB_AP every 2 s (STM32 safe state after 5 s). TELEMETRY older than 300 ms or HEAT_STATUS older than 500 ms → HEAT_ON_OFF 0, PAUSED (reason AC Power Failure if DOCK_PWR_OK is inactive, UNIT_LIFTED if DOCK_SENSE_A is high, CAN link loss otherwise). The heating unit drops to 0 power 1 s after the last setpoint refresh
- **SPI sharing:** the LCD (CS0) and the MCP2518FD (CS1) share SPI0; an LCD DMA chunk holds the bus ≤ 10 ms, the controller's 32-object RX FIFO buffers frames meanwhile
- **Bus load:** ~6 kbit/s worst case (~1 % of capacity); the dispensing block and LOADCELLS no longer exist on the bus
- **Firmware update:** 0x7E0 / 0x7E8 carry the STM32 image to its CAN bootloader (FR-MPU-062); no service UART

**Messages sent by the RV1106:**

| CAN ID | Name | Payload | Description |
|--------|------|---------|-------------|
| 0x001 | E_STOP | src_node = 3, reason_code | Broadcast emergency stop (no ACK) |
| 0x010 | HB_AP | seq, uptime_ms | Liveness, every 2 s |
| 0x100 | HEAT_SET_TEMP | target_dC, ramp, max_power_pct | Temperature setpoint for the heating unit's own PID, re-sent at 2 Hz |
| 0x101 | HEAT_ON_OFF | 0 / 1 | Enable / disable heating |
| 0x102 | HEAT_QUERY | — | Request HEAT_STATUS |
| 0x103 | HEAT_SET_POWER | power_pct (0–100), ramp | Power-mode setpoint (sear/boil stages), re-sent at 2 Hz |
| 0x202 | SET_STIR | seq, pattern, speed_rpm, direction | Set stir pattern, speed and direction |
| 0x221 | SET_SPEED | seq, speed_rpm, direction | Direct arm speed override |
| 0x222 | ARM_STOP | seq | Stop arm with decel ramp |
| 0x223 | ARM_HOME | seq | Return arm to home |
| 0x224 | ARM_STATUS | seq | Query arm status (ACK data: status_byte, rpm, position) |
| 0x225 | SET_RAMP | seq, accel_limit (RPM/s) | Arm acceleration limit |
| 0x260 | SET_EXHAUST | seq, duty_pct | Exhaust fan duty 0–100 % (fans are on the CSC) |
| 0x261 | GET_EXHAUST | seq | Query fans (ACK data: duty_pct, rpm1, rpm2) |
| 0x262 | EXHAUST_AUTO | seq, stage_id | Fan duty for the cooking stage, sent at each stage transition |
| 0x7E0 | FW_UPDATE_REQ | seq, op (ERASE / WRITE / VERIFY / BOOT), 5 data bytes | STM32 CAN bootloader, update mode only, lowest priority |

Identifiers mirror [[02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]], the single source of truth. Removed from the bus: 0x220 SET_LED and the 0x230–0x239 dispensing block (LED ring and dispensing are local to the RV1106, §2.2 / §2.9).

**Messages received by the RV1106:**

| CAN ID | Name | Payload | Description |
|--------|------|---------|-------------|
| 0x180 | HEAT_STATUS | power_pct, surface_temp_dC, element_temp, pot_detected, fault_flags | Heating unit status (10 Hz) — surface_temp (centre sensor) is the only cooking temperature |
| 0x181 | HEAT_FAULT | fault_code, detail | Heating unit fault → pause |
| 0x182 | HEAT_ACK | cmd_id, result | Heating unit command acknowledge |
| 0x310 | TELEMETRY | motor_rpm, motor_current_dA, safety_state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok), error_code, seq | Periodic status from the STM32 (20 Hz); on_battery / charging flags removed |
| 0x312 | STATUS | safety_state, error_code, flags, fault_detail | Safety/error report (fault codes in error_code, incl. 0x17 DU_UNDOCKED); fault_detail no longer carries batt_mV |
| 0x3FF | ACK / NAK | seq, cmd_type, result_code, data[0..4] | Acknowledge / NAK with result data |
| 0x7E8 | FW_UPDATE_RSP | seq, op, result, 4 data bytes | STM32 CAN bootloader response |

0x311 LOADCELLS is retired: SLD weights are read locally over I2C3.

### 5.2 MQTT Topics (Cloud Broker)

| Topic | Publisher | QoS | Description |
|-------|-----------|-----|-------------|
| `epicura/{device_id}/telemetry` | `epicurad` sync thread | 1 | Telemetry every 10 s while cooking; session lifecycle events and errors (`kind`-tagged) |
| `epicura/{device_id}/cmd` | Cloud | 1 | `live_view_start`, `live_view_stop`, `recipe_sync_now`, `ota_check` |

There are no device-local topics; the broker is AWS IoT Core over TLS.

---

## 6. Power Management

### 6.1 Power States

The battery is the primary supply: VSYS is the passive Schottky-OR of dock 24 V and the pack, so there is no switch-over and no gap. Docked, everything (including charging) draws from the dock; lifted or during a mains outage, the pack carries the whole DU.

| State | Description | Typical Draw | Source |
|-------|-------------|-------------|--------|
| Active Cooking (docked) | `epicurad` running, ISP + NPU active, display on, Wi-Fi connected; dispensing peaks on 6V_DSP | ~3 W (+ servo/pump peaks) | Dock 24 V; pack charging at 1.0 A |
| Idle (docked) | Display on, camera paths idle | ~2 W | Dock 24 V |
| Standby (docked) | Backlight off, reduced polling | ~1 W | Dock 24 V |
| Lifted | Unit off the dock (loading, cleaning); session PAUSED (UNIT_LIFTED); no bus, no heater | ~3 W → > 5 h on the 19 Wh pack | Pack |
| Mains lost (docked) | PAUSED (AC Power Failure); LCD dimmed, battery indicator shown; auto-resume when the dock returns | ~2 W | Pack |
| Battery low | 6.4 V warning banner; 6.2 V checkpoint + halt | — | Pack |
| Off | Halted after the 6.2 V checkpoint, or pack PCM cut-off (≈ 5.6 V); boots again when docked (charging) or the pack is recharged | 0 W | — |

### 6.2 Power Budget

- Luckfox Pico Zero (SoC + Wi-Fi/BT): ~1–1.5 W
- Display (4" LCD + backlight): ~0.5–1 W
- White LED ring (12–16 LEDs, ≤ 1 A on 5V_MAIN, RV1106 PWM): up to ~5 W during CAPTURE windows, ~0.3 W averaged at the 2 Hz capture duty — now part of the AP budget on 5V_MAIN
- Buzzer + 3.3 V logic (PCA9685, PCF8574 #2, INA219 ×2, TCA9543A, NAU7802 ×2, MCP2518FD, ISO1050 #2 logic side): ~0.2 W
- Total AP subsystem on 5V_MAIN: ≤ 3 W steady state, ≤ 8 W peak with the ring at 100 %
- 6V_DSP dispenser rail (servos, 6 V pumps and solenoids, one servo at a time, 3 A PTC): budgeted separately from VSYS; off when idle; at an empty pack (6.2 V) the buck drops out to ≈ 6.0 V, acceptable
- Charging (TP5100, 1.0 A into the 2S pack via MP1584EN #1): ~8 W from the dock, docked only

---

## 7. Safety & Fault Handling

### 7.1 RV1106 Safety Responsibilities

The RV1106 is **not** the primary safety controller — the STM32 owns all safety-critical paths. The RV1106's safety role is supervisory:

| Responsibility | Action |
|----------------|--------|
| Heartbeat | Send HB_AP every 2 s on the CAN bus; if the RV1106 crashes, the STM32 forces the heater off and opens the relay |
| Heater setpoint | Keep HEAT_SET_TEMP / HEAT_SET_POWER alive at 2 Hz; the heating unit regulates and keeps its own cut-offs, the STM32 keeps an independent over-temperature cut-off, and the unit drops to 0 power 1 s after the last refresh |
| Error classification | Analyze STM32 error codes, determine user-facing recovery options |
| Logging | Record all safety events to SQLite with timestamps |
| User notification | Display error/E_STOP screens, guide user through recovery |
| CV anomaly detection | Flag smoke/overflow/dry pot, send E_STOP if critical |

### 7.2 Fault Table (RV1106-Detected)

| Fault | Detection | Severity | Action |
|-------|-----------|----------|--------|
| CAN link loss | No TELEMETRY for 300 ms, 3 consecutive ACK timeouts, or `can0` bus-off — while docked with dock power present | Critical | HEAT_ON_OFF 0, pause cooking, alert user; STM32 holds stir state then safe-shutdown |
| Heating unit fault | HEAT_FAULT (0x181), fault_flags in HEAT_STATUS, or no HEAT_STATUS for 500 ms | Critical | HEAT_ON_OFF 0, pause, show heater fault |
| Mains power loss | DOCK_PWR_OK inactive while DOCK_SENSE_A says docked, confirmed by the 300 ms TELEMETRY timeout (detected locally; the STM32 is unpowered and sends nothing) | Warning | Checkpoint, PAUSED (AC Power Failure), battery UI; the DU runs on its pack; auto-resume when TELEMETRY returns within 5 min, prompt < 30 min, ERROR beyond |
| Unit lifted | DOCK_SENSE_A high (GPIO edge) | Warning | PAUSED (UNIT_LIFTED); heater stops by keep-alive loss, STM32 safe hold; resume only by user tap after re-docking, 30 min ceiling |
| Battery low / empty | INA219 #2 pack voltage < 6.4 V / < 6.2 V | Warning / Critical | Warning banner / checkpoint + sync + halt, RECOVERING on next boot |
| Charger fault | Neither CHRG nor STDBY with the pack < 8.0 V for 10 min while docked, or pack absent at boot | Warning | Alert, log; cooking allowed |
| DSB_STALL | INA219 #1 > 2.5 A for 300 ms, 3 s move timeout or PCA9685 NACK, after one retry (dispense thread) | Warning | 6V_DSP off, OE high; ERROR with retry / skip / abort |
| SLD_LOW_LEVEL | Reservoir load cell below the low-level threshold | Warning | Prompt refill; dispense step waits |
| SLD_DISPENSE_ERROR | Pump no-flow (no weight change 5 s after pump start) or target missed | Warning | Stop pump, close solenoid; ERROR with actual vs target |
| SLD_LOAD_CELL_DRIFT | NAU7802 I2C NACK / no data-ready, or tare drift beyond limit | Warning | Flag SLD dispensing unreliable; alert user |
| CV anomaly (smoke/overflow) | Inference confidence ≥ threshold | Critical | Broadcast E_STOP (0x001) on the CAN bus |
| CV failure | Camera disconnect, ISP timeout or `rknn` error | Warning | Fall back to timer + temperature thresholds |
| SQLite write failure | I/O error or `/data` full | Warning | Retry; keep checkpoint in memory; alert user |
| Memory pressure | Free RAM < 32 MB | Warning | Kill `rtsp-stream`, drop LCD preview, log |
| OTA update failure | swupdate exit code / 3 failed boots | Warning | Bootloader falls back to previous slot |
| Wi-Fi disconnect | Network monitor | Info | Continue offline, queue sync in `sync_outbox` |
| `epicurad` hang | Kernel watchdog (10 s) not kicked | Warning | busybox init restarts `epicurad`; heater drops to 0 power within 1 s, STM32 holds stir state meanwhile |

### 7.3 Recovery Sequence (E_STOP)

1. RV1106 broadcasts E_STOP (0x001) on the CAN bus (soft stop from the UI, only while docked; the hard E-stop button is on the Cooking Surface and the STM32 initiates independently)
2. STM32 cuts heater relay, disables the stir motor (FDCAN2) and its 24 V, sends STATUS `safety_state = E_STOP`
3. RV1106 sounds the buzzer (FR-MPU-025), switches the LED ring and dispenser rail off, displays full-screen red alert
4. RV1106 logs event to SQLite + publishes to MQTT (queued if offline)
5. System remains in E_STOP until manual hardware reset (E-stop button released)
6. After reset: STM32 → NORMAL safety state, RV1106 → IDLE

---

## 8. Performance Requirements

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Boot time (power-on → recipe browser) | <15 s | Stopwatch from 5 V applied |
| CV inference latency (NPU) | <20 ms (5–10 ms typical) | Timestamp delta (self-path frame → result) |
| UI touch-to-visual response | <200 ms | Touch event → LCD update |
| LCD full-frame refresh | ≤50 ms | fbtft transfer time at 50 MHz |
| CAN command round-trip | <10 ms | command sent → ACK (0x3FF) received |
| Heat loop period | 100 ms ± 5 ms | `heat` thread wake-up jitter |
| Recipe parse + validate | <2 s | YAML load → state machine ready |
| Live view start | <2 s | `live_view_start` received → first RTSP frame |
| Database query (recipe list) | <100 ms | SQL execute → result set |
| Camera capture interval | 500 ms ± 50 ms | Self-path frame timestamp jitter |
| `epicurad` RSS | ≤10 MB | `/proc/<pid>/status` |

---

## 9. Dependencies & Constraints

### 9.1 Hardware Dependencies

- Unified PCB v4.0 (160 × 90 mm, 4-layer, Dispensing Unit board): Luckfox Pico Zero in slot J_AP — 5V_MAIN (battery primary), SPI0 (LCD on CS0 via J_LCD, MCP2518FD CAN controller on CS1), I2C3 (touch via J_LCD plus all DU peripherals), GPIO (PCA9685 OE, DOCK_SENSE_A, DOCK_PWR_OK, CAN INT, touch reset), 4× PWM (pumps, LED ring, buzzer)
- Dock: 8-contact magnetic pogo pads on the DU underside (J_DOCK) over the CS left pillar — DOCK_24V (charge, switched by the CSC), GND, CAN_H / CAN_L / GND_ISO / 5V_ISO, DOCK_SENSE_A (in), DOCK_SENSE_B (out, tied to GND); the DU can only seat one way
- Isolated CAN bus: MCP2518FD + ISO1050DUB #2 on the Unified PCB (bus side from dock 5V_ISO), ISO1050DUB #1 + B0505S and termination on the CSC, J_CAN_HEAT to the heating unit; no CAN connector on the Unified PCB besides the dock pads
- I2C3 peripherals on the Unified PCB: PCA9685 (0x41) with OE, PCF8574 #2 (0x21: P0 oil solenoid, P1 water solenoid, P2 status LED, P3 TB6612 AIN1, P4 6V_DSP enable, P5 TB6612 BIN1, P6 CHRG in, P7 STDBY in), INA219 #1 (0x40, 6V_DSP rail), INA219 #2 (0x44, BAT+ 10 mΩ), TCA9543A (0x71) → 2× NAU7802 (0x2A); TB6612FNG, 2× IRLML6344 solenoid MOSFETs, Q_LED, buzzer 2N7002; TP5100 charger + J_BAT (2S pack), TPS54531, MP1584EN ×2, AMS1117-3.3; J_DSB1–4, J_SLD, J_LED, J_BUZZER
- No STM32, J_USB, J_SWD, J_CAN_STIR, J_STIR_PWR, J_CAN_HEAT, J_FAN, J_SAFE, HX711 or WS2812B on this board any more (moved to the CSC or dropped)
- Camera FPC ≤150 mm; IMX415-98 module on the Pico Zero MIPI CSI connector, on the DU underside centred over the pot behind a sealed borosilicate window, with the white LED ring
- Kernel drivers (mainline in 5.10): `pwm-pca9685`, `gpio-pcf857x`, `ina2xx`, `i2c-mux-pca954x`, `nau7802`, `pwm-rockchip`, `mcp251xfd`

### 9.2 Software Dependencies

- Luckfox SDK Buildroot (kernel 5.10) with `rockit` (VI/ISP/VENC/RGA), `rknn` runtime, fbtft, `wpa_supplicant`, `bluez5`
- `epicurad`: C11, CMake, pthreads; libraries: SQLite 3 (WAL, JSON1, FTS5), libyaml, cJSON, libmosquitto (client only), libcurl + mbedTLS, LVGL 9, `rknn_api`, swupdate
- RKNN-Toolkit2 on the build host for offline INT8 model conversion (TFLite/ONNX → `.rknn`)
- Not on the device: Python, OpenCV, Docker, PostgreSQL, Node.js, Redis, Mosquitto broker, Kivy, GStreamer, libcamera

### 9.3 Non-Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-MPU-001 | Memory budget: ~80 MB steady state, ~95 MB peak (streaming + inference + UI) of 256 MB | Must | Measured on hardware; CMA reservation set in device tree (VI/ISP 16 MB, self-path + RGA 2 MB, VENC 8 MB on demand) |
| NFR-MPU-002 | Single core: `can` and `heat` threads run at real-time priority (`SCHED_FIFO`); all other threads `SCHED_OTHER` | Must | HB_AP never late by more than 500 ms and the HEAT_SET_TEMP keep-alive never later than 150 ms under UI rendering or sync burst |
| NFR-MPU-003 | Memory-pressure fallback: free RAM < 32 MB → kill `rtsp-stream`, drop LCD preview | Must | Cooking continues uninterrupted |
| NFR-MPU-004 | Sensor runs at 1280×720, not 1080p; phone streaming and LCD preview are on demand only | Must | No VENC channel allocated outside a live-view session |
| NFR-MPU-005 | Read-only rootfs; all mutable state under `/data` and `/userdata` | Must | Power loss at any time leaves a bootable system |
| NFR-MPU-006 | No safety dependency on the AP: the heating unit drops to 0 power without the setpoint keep-alive and the STM32 forces it off and opens the relay if heartbeats stop | Must | Verified by killing `epicurad` during a cook |

### 9.4 Cross-References

| Topic | Document |
|-------|----------|
| STM32 MCU spec | [[05-MCU-Functional-Specification]] |
| State machine details | [[03-Main-Loop-State-Machine]] |
| Software architecture | [[02-Controller-Software-Architecture]] |
| Tech stack decisions | [[01-Tech-Stack]] |
| RV1106 suitability | [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability]] |
| Hardware architecture | [[01-Epicura-Architecture]] |
| Unified PCB | [[01-Unified-PCB-Design]] |
| Dispensing subsystems | [[03-Ingredient-Dispensing]] |
| Exhaust fans (0x260–0x262) | [[05-Exhaust-Fume-Management]] |

---

## 10. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-16 | Manas Pradhan | Initial document; subsequent single-board revisions recorded in the header (CM5 → RV1106, CAN node + heater setpoints, battery-backed J_AP) |
| 1.1 | 2026-11-04 | Manas Pradhan | Three-unit architecture: RV1106 in the lift-off Dispensing Unit on the Unified PCB v4.0, battery primary (VSYS = dock 24 V or 2S pack, no gap); dock interface (DOCK_SENSE_A, DOCK_PWR_OK); new §2.9 Ingredient Dispensing (`dispense` thread over I2C3: PCA9685, TB6612, solenoids, NAU7802 via TCA9543A, INA219 #1 stall window; DSB_STALL / SLD_* faults now RV1106-detected) and §2.10 Power & Dock (INA219 #2 SoC, 6.4 V warning, 6.2 V checkpoint + halt, UNIT_LIFTED pause, charger status); LED ring (FR-MPU-014) and buzzer (FR-MPU-025) on RV1106 PWM; STM32 OTA over the CAN bootloader (0x7E0/0x7E8); UART2 service link and BOOT0/NRST freed; CAN table drops 0x220, 0x230–0x239, 0x311 and adds 0x260–0x262, 0x7E0/0x7E8; TELEMETRY flags, power states/budget, fault table and dependencies updated |
| 1.2 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged — HEAT_STATUS `coil_temp` → `element_temp` (FR-MPU-055, §5.1 table), surface_temp is the unit's centre (pot-bottom) sensor; heater wording in §1, FR-MPU-052/054, §5.1, §7 fault table, NFR-MPU-006 and dependencies updated |
