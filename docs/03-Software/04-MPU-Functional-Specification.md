---
tags: [epicura, mpu, rv1106, luckfox, functional-spec, software]
created: 2026-02-16
modified: 2026-11-05
version: 1.7
aliases: [RV1106 Spec, MPU Spec]
---

# MPU Functional Specification — Luckfox Pico Zero (RV1106G3)

> **Document ID:** EPIC-SW-MPU-001
> **Processor:** Rockchip RV1106G3, 1x Cortex-A7 @ 1.2 GHz (32-bit, NEON, FPU)
> **RAM / Storage:** 256 MB DDR3L (in-package) / 8 GB eMMC
> **Board:** Luckfox Pico Zero (no carrier board required) in slot J_AP of the Unified PCB v5.0, inside the lift-off Dispensing Unit (DU), beside the DU STM32
> **Revision:** 2026-11-05 (v1.7) — Robot-mop SLD: the DU STM32 meters liquid open loop by pump Hall tach pulses × cal_ul from two drawer tanks (float / presence Hall switches), no solenoids and no load cells; `epicurad` converts recipe grams to mL, keeps the per-channel calibration (SLD_CAL at boot and after the measuring-cup flow), sends SLD_PRIME from the loading screen after a refill and reads QUERY_SLD instead of QUERY_WEIGHT / TARE; faults SLD_TANK_ABSENT and NOT_DOCKED replace SLD_LOAD_CELL_DRIFT; FR-MPU-082/-086/-087/-088, §1.1, pin 16, power bullets, §7.2 and §9.1 updated
> **Previous revision:** 2026-11-04 (v1.4) — MCU back in the Dispensing Unit: a second STM32G0B1RE on the Unified PCB v5.0 owns dispensing, LED ring, buzzer, battery/dock monitoring and the DU's CAN node; the RV1106 talks to it over the host link (UART2 ↔ USART1, 921,600 baud, COBS/CRC, CAN-shaped frames) and reaches the CAN bus through it as a transparent gateway; MCP2518FD / SocketCAN and the I2C3 dispenser peripherals gone; `can` thread → `link` thread, `dispense` thread is a thin client; BOOT0/NRST lines back for flashing the DU STM32
> **Earlier revision:** 2026-11-04 (v1.2) — Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged: HEAT_STATUS field `coil_temp` → `element_temp`, surface_temp is the unit's centre (pot-bottom) sensor; heater wording updated throughout
> **Earlier revision:** 2026-11-04 (v1.1) — Three-unit architecture: the RV1106 lives in the lift-off Dispensing Unit on the Unified PCB v4.0, battery primary (VSYS from dock 24 V or the 2S pack); it reaches the isolated CAN bus through the 8-pin dock. Ingredient dispensing (PCA9685, TB6612, solenoids, NAU7802 load cells over I2C3), the white LED ring (PWM), the buzzer (PWM), battery/dock monitoring (INA219 #2, DOCK_SENSE_A, DOCK_PWR_OK) and the STM32 CAN bootloader client (0x7E0/0x7E8) move onto the RV1106; new `dispense` thread; UART2 service link and BOOT0/NRST lines gone; UNIT_LIFTED pause added
> **Earlier revision (same day):** 2026-11-04 — RV1106 joins the isolated CAN bus (MCP2518FD on SPI0 CS1) and sends heater setpoints (the induction module runs its own PID; no IR thermometer); Pico Zero sits in the Unified PCB slot J_AP, battery-backed; UART2 is a service link only
> **Related:** [[05-MCU-Functional-Specification]], [[02-Controller-Software-Architecture]], [[01-Tech-Stack]]

---

## 1. Overview

The RV1106 is the main application processor (AP) for Epicura. It runs Buildroot Linux (Luckfox SDK, kernel 5.10) with a single native C11 application, `epicurad`, that owns all high-level functions: recipe engine, computer vision (hardware ISP + NPU), LVGL touchscreen UI, SQLite storage, and cloud sync (REST + MQTT client). Epicura has three controllers: the RV1106, the **DU STM32** (STM32G0B1RE on the same Unified PCB v5.0) and the **CSC STM32** (on the Cooking Surface Controller in the base), plus the electric heating unit's own MCU. The RV1106 is the AP node of the isolated CAN bus shared with the CSC STM32 and the heating unit: it sends stir and exhaust commands and heater setpoints (temperature or power), receives telemetry and the unit's measured temperature, and keeps the setpoint alive in its `heat` thread; the temperature loop itself runs inside the heating unit. It has no CAN peripheral of its own: it reaches the bus through the DU STM32, which acts as a transparent gateway over the **host link** (UART2 ↔ USART1, 921,600 baud, COBS-framed CAN-shaped frames with CRC-16). The Pico Zero plugs into the J_AP slot of the Unified PCB v5.0 inside the **Dispensing Unit (DU)**, the top unit that lifts straight off the machine with no cable: the DU reaches the bus and the charge supply only through the 8-contact pogo dock on the Cooking Surface's left pillar. The DU's 2S Li-ion pack is its **primary supply** — VSYS is a Schottky-OR of the dock 24 V and the pack, so the RV1106 keeps running when the unit is lifted or mains fails. The RV1106's own peripherals are the camera (MIPI CSI), the LCD and touch panel (SPI0 + I2C3), Wi-Fi/BLE and the host link; everything else in the DU — ingredient dispensing (servo carousels, pumps, solenoids, load cells), the camera's white LED ring, the buzzer and battery/dock monitoring — is driven by the DU STM32 and commanded by the RV1106 over the host link with DU-local frame IDs (§5.1). The RV1106 flashes the DU STM32 through the ST system bootloader on the same UART (BOOT0 on GPIO 32, NRST on GPIO 38); the CSC STM32 is updated over CAN through the gateway. There is no container runtime, database server, message broker or interpreter on the device.

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
| Host link | UART2 (header pins 8 TX / 10 RX, `/dev/ttyS2`) ↔ DU STM32 USART1 at 921,600 baud 8N1; CAN-shaped frames, COBS-encoded with CRC-16; GPIO 32 → BOOT0, GPIO 38 → NRST for flashing the DU STM32 |
| CAN | No CAN peripheral on the RV1106: the DU STM32 (FDCAN1 + a non-isolated SN65HVD230; the isolation is on the CSC's port) is the DU's node and forwards the RV1106's frames transparently; the bus reaches the DU over dock pins 3–6, so it exists only while docked |
| I2C | I2C3 (header pins 16/18, 400 kHz): FT6336 touch only. Every other I2C device of the DU (PCF8574 #2, PCA9685, INA219 ×2) is on the DU STM32's I2C1; the SLD tank and pump Hall switches are DU STM32 GPIO |
| Dispensing unit I/O | None on the RV1106: dispensers, LED ring, buzzer, DOCK_SENSE_A and DOCK_PWR_OK are DU STM32 I/O, reached over the host link (SET_LED 0x220, SET_BUZZER 0x226, 0x230–0x239 dispensing, DU_STATUS 0x311) |
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
| FR-MPU-014 | Drive the white camera LED ring (12–16 LEDs, 5000 K, CRI ≥ 90, ≤ 1 A on 5V_MAIN) with SET_LED (0x220: seq, duty_pct) over the host link to the DU STM32, whose PWM (1 kHz) drives Q_LED (IRLML6344 low-side) on J_LED; duty modes OFF 0 %, CAPTURE 100 %, NIGHT 30 %; no colour control; SET_LED is DU-local and never reaches the CAN bus | Must | CAPTURE set ≥ 50 ms before every capture window and returned to the previous mode after it; duty 0 at boot, in E_STOP and before halt (the DU STM32 also drops it on host-link loss) |
| FR-MPU-015 | Image enhancement in the ISP (dehaze, 2D/3D noise reduction, LSC, sharpening, AWB, AE) from the IMX415-98 tuning file in `/oem` | Must | No CPU image processing (no OpenCV / CLAHE); steam haze handled by ISP dehaze |

### 2.3 User Interface

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-020 | Touchscreen UI via LVGL 9 (C, software rendered) on the 4" 480×320 SPI LCD | Must | 20 Hz LVGL tick; partial redraws; full-frame refresh ≤ 50 ms |
| FR-MPU-021 | Touch-to-visual response <200 ms | Must | Measured from FT6336 evdev event to LCD update |
| FR-MPU-022 | Display state-appropriate screens per state machine | Must | Each state maps to a UI view (see §2.3.1) |
| FR-MPU-023 | On-demand "view pot" preview screen (ISP main path → RGA scale to 480×320 → framebuffer) | Should | ≤ 10 fps; active only while the screen is open; dropped under memory pressure |
| FR-MPU-024 | Recipe browser with search and filtering | Must | Full-text search via SQLite FTS5 |
| FR-MPU-025 | Buzzer on the DU driven by the DU STM32 (SET_BUZZER 0x226: seq, tone_hz, duration_ms over the host link; STM32 PWM through a 2N7002 on J_BUZZER): continuous tone in E_STOP (sounded on STATUS `safety_state = E_STOP` from the STM32 — the Cooking Surface has no buzzer), short patterns for errors, UNIT_LIFTED / battery warnings, dispense done and touch feedback | Must | E_STOP tone within 100 ms of the STATUS frame or local E_STOP; silent at boot and after halt |

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

### 2.6 Host Link, CAN Gateway and Heater Control

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-050 | `link` thread (C, pthread, `SCHED_FIFO`) owns the host link `/dev/ttyS2` (UART2, 921,600 baud 8N1) to the DU STM32: COBS/CRC-16 codec for CAN-shaped frames (id, dlc, data), routing of DU-local replies (0x311, 0x3FE) to the `dispense` thread and power monitor and of bus frames (0x00x, 0x01x, 0x18x, 0x3xx, 0x7E8) to `heat` / engine exactly as the former raw socket did | Must | Commands 0x2xx with seq byte, ACK/NAK 0x3FF (CSC) or 0x3FE (DU STM32) matched by seq, ACK timeout 500 ms, 3 retries; a frame with a bad CRC or COBS error is dropped and counted |
| FR-MPU-051 | Send HB_AP (0x010) every 2 s | Must | Missed heartbeat → STM32 forces the heater off and opens the relay after 5 s |
| FR-MPU-052 | The RV1106 has no CAN peripheral: the DU STM32 (FDCAN1 + a non-isolated SN65HVD230) is the DU's node on the CSC's isolated bus and forwards the RV1106's frames in both directions without altering them (the node is still AP, src_node 3; the CAN ID map is unchanged). The bus reaches the DU over dock pins 3–5 (CAN_H, CAN_L, GND_ISO tied to DU ground; pin 6 reserved) and therefore exists only while the DU is docked; the host link to the DU STM32 exists always | Must | Decision 2026-11-04: MCP2518FD / SocketCAN removed; bus loss while DU_STATUS reports docked = 0 is expected, not a fault; loss of DU_STATUS itself for 3 s is DU_LINK_LOST (§7.2) |
| FR-MPU-053 | Parse unsolicited TELEMETRY (0x310) at 20 Hz and STATUS (0x312) on change | Must | motor RPM/current, safety state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok), fault code (incl. 0x17 DU_UNDOCKED) available to engine/ui/sync threads via ring buffer; no battery data comes from the CSC STM32 — pack state comes from the DU STM32 in DU_STATUS (§2.10) |
| FR-MPU-054 | `heat` thread (`SCHED_FIFO`): hold the stage setpoint and re-send HEAT_SET_TEMP (0x100: target, ramp ≤ 5 °C/s, max power) or HEAT_SET_POWER (0x103) at 2 Hz as the unit's keep-alive; no PID in Epicura (the heating unit regulates on its own centre sensor) | Must | Keep-alive never later than 150 ms; HEAT_ON_OFF 0 and PAUSED if HEAT_STATUS is older than 500 ms |
| FR-MPU-055 | Consume HEAT_STATUS / HEAT_FAULT (0x180 / 0x181): surface_temp drives stage transitions (±5 °C for 3 readings) and the UI graph; element temperature as secondary limit; pot-absent and unit faults → pause | Must | Reaction within one status interval (100 ms) |
| FR-MPU-057 | Mains loss is detected inside the DU, not reported by the CSC STM32: DU_STATUS `dock_power` clear while `docked` is set (DOCK_PWR_OK / DOCK_SENSE_A on the DU STM32, flag change pushed at once), confirmed by a TELEMETRY timeout (300 ms) → checkpoint the session, PAUSED (AC Power Failure), dim the LCD, show the battery state; the DU keeps running on its pack while the heater and stir motor are already down; auto-resume to RESUMING when TELEMETRY returns within 5 min (the STM32 reboots in < 1 s after mains returns), prompt if < 30 min, ERROR beyond. Pack thresholds per §2.10 | Must | Checkpoint written within 2 s of the confirmed outage |
| FR-MPU-056 | Broadcast E_STOP (0x001, src_node = 3) on critical CV anomaly or user E-stop from the UI | Must | All nodes act without ACK |

### 2.7 OTA Updates

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-060 | A/B boot + rootfs slots on eMMC via swupdate with signed `.swu` | Must | Rollback after 3 failed boots |
| FR-MPU-061 | RSA-2048 signature verification on update images | Must | Reject unsigned or tampered images |
| FR-MPU-062 | CSC STM32 firmware update over the isolated CAN bus: the swupdate handler streams the `.bin` to the CSC's in-application CAN bootloader with FW_UPDATE_REQ (0x7E0: seq, op = ERASE / WRITE / VERIFY / BOOT, 5 data bytes) through the DU STM32 gateway and matches FW_UPDATE_RSP (0x7E8: seq, op, result, 4 data bytes); only while docked, in IDLE, with the heater off (see [[05-MCU-Functional-Specification]] §5.1) | Should | CRC-32 verified by the STM32 before BOOT; lost or NAK'd chunks retried by seq; an abort (undock, E_STOP) leaves the running image |
| FR-MPU-063 | DU STM32 firmware update over the host link: the swupdate handler pulls BOOT0 high (GPIO 32), pulses NRST (GPIO 38), drives the ST system bootloader protocol on USART1 (`/dev/ttyS2`), verifies the image, releases BOOT0 and resets; only in IDLE with the dispenser rail off; the `link` thread is suspended for the duration | Should | Image CRC verified after write; a failed update leaves BOOT0 low and resets so the previous image (if intact) runs; DU_STATUS resumes within 2 s of reset |

### 2.8 Live View (On Demand)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-070 | On `live_view_start`, bind VENC H.264 1280×720 @ 15 fps, 1.5 Mbps and spawn `rtsp-stream` (RTSP on :554, path `/pot`, single client) | Must | First frame available within 2 s of command |
| FR-MPU-071 | Tear down `rtsp-stream` after 60 s with no client or on `live_view_stop`; free VENC CMA buffers | Must | No encoder channel exists outside a live-view session |
| FR-MPU-072 | Streaming is best-effort and never affects cooking | Must | Any encoder or RTSP error tears down the stream only |

### 2.9 Ingredient Dispensing (`dispense` thread)

Dispensing is executed by the DU STM32 (see [[05-MCU-Functional-Specification]], DU instance); the RV1106 `dispense` thread is a thin client that sends the DU-local 0x230–0x239 frames over the host link and waits for DU_ACK (0x3FE). Nothing dispensing-related crosses the CAN bus: the DU STM32 terminates these IDs. Mechanics per [[03-Ingredient-Dispensing]].

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-080 | `dispense` thread (`SCHED_OTHER`) consumes an internal queue from the recipe engine with the same names and semantics as before — DISPENSE_FID 0x230 (box_id 1–6, qty_quarter_tsp 1–40), DISPENSE_CID 0x231 (slot_id 1–5), DISPENSE_SLD 0x232 (channel OIL/WATER, target_ml), SLD_PRIME 0x233, QUERY_SLD 0x235, PREFLIGHT 0x236 (subsystem_mask), SLD_CAL 0x237, DISPENSER_HOME 0x238 (CID / FID / both), DISPENSER_STATUS 0x239 — and for each sends one DU-local frame (seq in byte 0) over the host link via the `link` thread, then waits for DU_ACK / NAK (0x3FE: seq, cmd_type, result_code, ≤ 5 data bytes); the result struct goes back to the engine. The `dispense_submit()` / `dispense_wait()` API is unchanged | Must | Engine and `dispense` thread never touch I2C, PWM or GPIO; one command in flight at a time; NAK on invalid argument or busy; a long move (FID doses, SLD fill) is acknowledged on completion, with the ACK timeout extended to the command's worst-case duration + 1 s |
| FR-MPU-081 | The dispensing sequences themselves (Dispenser Servo Block via PCA9685 on the DU STM32 I2C1, 6V_DSP rail enable, OE, ramped moves ≤ 3°/tick, one servo at a time) run on the DU STM32 — see [[05-MCU-Functional-Specification]], DU instance | — | Rail off and OE high when idle, at boot, on E_STOP, PAUSED, before halt and on host-link loss (DU STM32 rule) |
| FR-MPU-082 | FID dose, CID dispense, DSB stall detection and the SLD open-loop metering (tach pulses × cal_ul, prime routine) are DU STM32 behaviour; the RV1106 only forwards the recipe parameters (grams converted to mL by density, oil 0.92 g/mL) and consumes the result (doses_done + estimated mass, new carousel position, actual_ml + primed_ml) | — | Volumetric accuracy ±10 % per ¼ tsp dose; SLD ±5 % after calibration; CID ascending-order rule enforced by the DU STM32 (NAK) |
| FR-MPU-083 | The RV1106 sends DISPENSER_HOME at recipe end and on abort, and refuses to queue dispensing while PAUSED, in ERROR / E_STOP or while DU_STATUS reports docked = 0 | Must | No dispense frame leaves the RV1106 in those states |
| FR-MPU-086 | QUERY_SLD (tank present / low / prime_pending, cal_ul, last_ml from the DU STM32 ACK data) on request; SLD_CAL sent at boot with the stored µL-per-pulse per channel and after the calibration flow (DU on the counter, measuring cup under the nozzle, fixed 100 / 400 pulses, user enters the measured mL; the only dispensing allowed while undocked); SLD_PRIME from the loading screen after a refill; tank low or absent (reported by the DU STM32) → SLD_LOW_LEVEL / SLD_TANK_ABSENT | Must | QUERY_SLD answered within 100 ms over the link; low-level prompts a refill in the UI; cal_ul persisted in SQLite |
| FR-MPU-087 | PREFLIGHT before a recipe: the DU STM32 answers with a result mask (I2C presence of 0x41, 0x21, 0x40, 0x44, each SLD tank present and not low, 6V_DSP rail voltage after a 100 ms enable pulse); the RV1106 adds the user's fill confirmation vs recipe needs | Must | Missing subsystem blocks the recipe with a user-facing reason |
| FR-MPU-088 | Dispensing faults are detected and reported by the DU STM32 (NAK result code or DU_STATUS error_code): DSB_STALL, SLD_LOW_LEVEL, SLD_DISPENSE_ERROR (pump no-flow: no tach pulse within 1 s of pump start, pulse rate under 25 % of nominal, or pump current out of window), SLD_TANK_ABSENT (tank-present Hall low), NOT_DOCKED (dose or prime attempted while lifted) → engine ERROR with retry / skip / abort (§7.2). No dispensing fault code comes from the CSC STM32 | Must | Fault surfaced to the engine within one link round-trip of the DU STM32 raising it |

### 2.10 Power & Dock

The DU runs on its own 2S pack; the dock only charges it and carries the CAN bus. The DU STM32 measures the pack, charger and dock lines and reports them in DU_STATUS (0x311) at 1 Hz and on any flag change; the RV1106 makes every decision from that record.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-090 | Power/dock monitor: decode DU_STATUS (0x311) from the DU STM32 — `batt_mV`, `batt_mA`, `soc_pct`, flags (`docked` = DOCK_SENSE_A low, `dock_power` = DOCK_PWR_OK active, `charging` / `charge_done` from TP5100 CHRG / STDBY, `dsp_rail_on`, `dsp_busy`, `can_bus_ok`), `error_code` — received at 1 Hz and immediately on any flag change | Must | Values in the ring buffer for engine / ui / sync; battery indicator always visible in the UI; no DU_STATUS for 3 s → DU_LINK_LOST (§7.2) |
| FR-MPU-091 | Battery thresholds: warning banner at 6.4 V; at 6.2 V checkpoint the session, sync, LED ring and dispenser rail off, halt (boot recovery → RECOVERING on next power); the pack PCM cuts off at ≈ 5.6 V as last resort | Must | Checkpoint written before halt; RECOVERING only ever reached because the DU pack ran out |
| FR-MPU-092 | Unit lifted: DU_STATUS `docked` clears (flag-change frame from the DU STM32) → PAUSED (reason UNIT_LIFTED) within 100 ms; the heater stops ≤ 1 s by keep-alive loss and the CSC STM32 enters safe hold on DOCK_SENSE_B; the `link` thread treats the bus disappearing (`can_bus_ok` = 0, TELEMETRY stops) as expected while lifted (no CAN-link-loss error); resume only by user tap after re-docking (no auto-resume), same 30 min food-safety ceiling | Must | No E_STOP broadcast on lift; the DU STM32's FDCAN1 recovers from bus-off automatically on re-dock and `can_bus_ok` returns |
| FR-MPU-093 | Charging: TP5100 at 1.0 A from DOCK_24V (≈ 5.5 h from empty while docked); charge fault (neither `charging` nor `charge_done` with the pack below 8.0 V for 10 min while docked, or pack absent at boot — all from DU_STATUS) → warning, cooking allowed | Should | Fault shown in the UI and logged |
| FR-MPU-094 | Docked, VSYS ≈ 23.5 V and the pack does not discharge; lifted or mains lost, VSYS = 6.0–8.4 V from the pack with no gap (passive Schottky-OR); software never switches the supply | — | Verified by lifting the unit mid-session: no reboot |

---

## 3. Hardware Interfaces

### 3.1 Header Allocation (Luckfox Pico Zero 40-pin)

Unified PCB v5.0 (Dispensing Unit board). The DU STM32 sits beside the Pico Zero; the RV1106's header carries the LCD, touch, host link, BOOT0/NRST and console — nothing else.

| Header Pin | Function | Direction | Notes |
|------------|----------|-----------|-------|
| 8 | UART2_TX (M1) | Output | Host link to the DU STM32 USART1 RX (PA10), 921,600 baud, 33R series; also the ST system-bootloader UART |
| 10 | UART2_RX (M1) | Input | Host link from the DU STM32 USART1 TX (PA9) |
| SPI0_CS1 (GPIO 58) | — | — | Freed (was the MCP2518FD chip select in v4.0) |
| 19 | SPI0_MOSI | Output | LCD data (ST7796S) |
| 21 | SPI0_MISO | Input | LCD (unused by fbtft, reserved) |
| 23 | SPI0_CLK | Output | LCD clock, 50 MHz |
| 24 | SPI0_CS0 | Output | LCD chip select |
| 22 | GPIO | Output | LCD DC (data/command) |
| 26 | GPIO | Output | LCD RST |
| 12 | PWM10 | Output | LCD backlight |
| 16 | I2C3_SDA | Bidir | FT6336 touch 0x38 (via J_LCD) only, 400 kHz, 4.7k pull-ups. The dispenser / power ICs (PCF8574 #2, PCA9685, INA219 ×2) are on the DU STM32 I2C1 |
| 18 | I2C3_SCL | Output | Same bus |
| 36 | GPIO | Input | Touch INT (FT6336) |
| 32 | GPIO | Output | DU STM32 BOOT0 (10k pull-down; high only during a firmware update) |
| 38 | GPIO | Output (open-drain) | DU STM32 NRST (10k pull-up, 100 nF) |
| 35 / 37 | UART0_TX / UART0_RX | — | Debug console (Luckfox default) |
| spare | UART3, UART4, I2C1, I2C2, GPIO 58, PWM ×4 | — | Freed vs v4.0: SPI0 CS1, MCP2518FD nINT, PCA9685 OE, DOCK_SENSE_A, DOCK_PWR_OK and the four PWM lines (pumps, LED ring, buzzer) all moved to the DU STM32 |

### 3.2 Camera (MIPI CSI)

- Connector: MIPI CSI FPC on the Pico Zero (4-lane connector)
- Interface: MIPI CSI-2, 4-lane (IMX415-98)
- Cable length: ≤150 mm (signal integrity)
- Sensor: IMX415-98 8 MP (2304×1296 native, 1/2.8"), run at 1280×720 @ 30 fps; ISP tuning file from the Luckfox SDK in `/oem`
- Paths: ISP main 1280×720 NV12 (preview / stream), ISP self-path 224×224 RGB888 (inference)

### 3.3 Display (SPI LCD)

- 4" 480×320 IPS LCD, ST7796S controller on SPI0 (50 MHz, DMA), fbtft driver, `/dev/fb0`
- Touch: FT6336 capacitive on I2C3 (the only I2C3 device), INT on header pin 36, evdev
- Software rendering (no GPU); full-frame refresh ~50 ms, LVGL partial redraws

### 3.4 Power

- VSYS = SS54 Schottky-OR of DOCK_24V (dock pin 1, switched on by the CSC only while the DU is seated) and BAT+ (2S2P 18650, 7.4 V nominal, 5,200 mAh ≈ 38 Wh, PCM + NTC, J_BAT). Docked: VSYS ≈ 23.5 V and the pack does not discharge. Lifted or mains lost: VSYS = 6.0–8.4 V from the pack. Passive, no gap — the battery is the primary supply
- 5V_MAIN: VSYS → TPS54531 → J_AP pins 2/4 (Pico Zero), LCD, white LED ring (≤ 1 A, DU STM32 PWM), buzzer, AMS1117-3.3 → 3.3 V logic (DU STM32 ≈ 30 mA, PCA9685, PCF8574 #2, INA219 ×2, SLD Hall switches ×6, SN65HVD230, TB6612 VCC)
- 6V_DSP: VSYS → MP1584EN #2 → 6.0 V switched dispenser rail (Q_DSB high-side via PCF8574 #2 P4, 3 A PTC, 1000 µF): servos and the two 6 V SLD pumps (peristaltic oil, diaphragm water); off when idle
- Charging: DOCK_24V → MP1584EN #1 → 12 V → TP5100 at 1.0 A (≈ 5.5 h from empty while docked); CHRG / STDBY on PCF8574 #2 P6 / P7. No isolated supply on this board: the CAN transceiver is a plain SN65HVD230 on 3.3 V, dock pad 5 (GND_ISO) is tied to the DU ground and pad 6 (5V_ISO) is not connected
- Monitoring: by the DU STM32 — INA219 #2 (0x44) pack voltage + current → state of charge, DOCK_PWR_OK and DOCK_SENSE_A — reported to the RV1106 in DU_STATUS (0x311)
- Typical draw: ~1.5 W board (SoC + Wi-Fi), ≤ 3 W with LCD backlight; lifted-unit load ≈ 3 W → > 12 h on the pack
- USB-C used for bench power and flashing only
- No carrier board; all signals on the Pico Zero header

---

## 4. Software Architecture

### 4.1 Operating System

- **Buildroot Linux** from the Luckfox SDK (kernel 5.10), busybox init, no systemd
- Read-only squashfs rootfs; A/B boot + rootfs slots for OTA rollback
- Kernel drivers: fbtft (ST7796S), `edt-ft5x06` (touch), VI/ISP/VENC/RGA (rockit), RKNN NPU, 8250 UART (`/dev/ttyS2` host link), `pwm-rockchip` (LCD backlight only), GPIO (BOOT0/NRST), wpa_supplicant + bluez5. No CAN, no I2C peripheral drivers besides the touch controller
- eMMC layout: `boot_a/b` 2×32 MB, `rootfs_a/b` 2×256 MB, `oem` 64 MB (models, ISP tuning, LVGL assets, default recipes), `data` ~6 GB (`/data/epicura.db`, images, logs, OTA staging), `userdata` 64 MB

### 4.2 Process & Thread Model

| Thread / Process | Role | Scheduling | Notes |
|------------------|------|------------|-------|
| `epicurad` / ui | LVGL 9 rendering, touch input, pot preview | `SCHED_OTHER` | 20 Hz tick, ~0.6 MB double buffer |
| `epicurad` / engine | YAML parsing, cooking state machine, SQLite checkpoint | `SCHED_OTHER` | 1 Hz tick |
| `epicurad` / cv | rockit VI/ISP, `rknn_api` inference, majority vote | `SCHED_OTHER` | 2 Hz |
| `epicurad` / link | Host link `/dev/ttyS2` RX/TX (COBS/CRC codec), frame routing (bus frames ↔ DU-local frames), seq/ACK matching, HB_AP heartbeat, telemetry ring buffer, DU_STATUS decode | `SCHED_FIFO` | Never starved by UI or sync |
| `epicurad` / heat | 2 Hz HEAT_SET_TEMP / HEAT_SET_POWER keep-alive; HEAT_STATUS surface_temp to engine/ui | `SCHED_FIFO` | HEAT_ON_OFF 0 if HEAT_STATUS stale > 500 ms |
| `epicurad` / dispense | Thin client: engine queue → DU-local frames (0x230–0x239) over the link, DU_ACK (0x3FE) → result struct; no I/O of its own (the DU STM32 runs the servo, pump and load-cell sequences) | `SCHED_OTHER` | Blocks on the ACK of the command in flight |
| `epicurad` / sync | libmosquitto, libcurl + mbedTLS, outbox drain, OTA check | `SCHED_OTHER` | 10 s cadence |
| `rtsp-stream` (child) | VENC H.264 720p → RTSP :554 | `SCHED_OTHER` | On demand only, ~4 MB |

Memory budget: ~80 MB steady state, ~95 MB peak (streaming + inference + UI) of 256 MB; `epicurad` ~10 MB RSS.

### 4.3 Boot Sequence

1. **U-Boot** → select active A/B slot
2. **Kernel 5.10** → fbtft, VI/ISP, `/dev/ttyS2` (UART2, 921,600), Wi-Fi/BT drivers
3. **busybox init** → mount `/data`, `/oem`; start wpa_supplicant, kernel watchdog
4. **`epicurad` start** → open SQLite → link thread (open `/dev/ttyS2`, wait for the first DU_STATUS ≤ 2 s: docked? on battery? RECOVERING if an interrupted session is found; first HB_AP, forwarded to the bus if docked) → heat thread → dispense thread (sends DISPENSER_STATUS; the DU STM32 already holds OE high and 6V_DSP off) → ISP + NPU init → sync thread
5. **UI** → display IDLE / recipe browser (target: <15 s from power-on)

### 4.4 Inter-Thread Communication

- All threads share one process; no local MQTT, no sockets
- The link thread publishes CSC STM32 telemetry, heater status and the DU_STATUS record into a lock-free ring buffer read by engine, ui, sync and heat
- Engine pushes commands onto the link command queue; the link thread handles seq/ACK/retry and routes each frame to the bus (through the DU STM32 gateway) or to the DU STM32 itself by ID
- Engine sets the heat thread setpoint; only the heat thread sends HEAT_SET_TEMP / HEAT_SET_POWER
- Engine pushes dispensing commands (DISPENSE_FID / CID / SLD, SLD_PRIME, QUERY_SLD, PREFLIGHT, SLD_CAL, DISPENSER_HOME, DISPENSER_STATUS) onto the dispense queue; the dispense thread turns each into a DU-local frame, waits for DU_ACK and answers with a result struct, publishing dispensed volumes, tank state and carousel state into the same ring buffer
- CV thread writes the latest `cv_result_t` (stage, confidence, fallback flag) for the engine
- Sync thread receives cloud commands (`cmd` topic) and dispatches to engine / live view

---

## 5. Communication Protocols

### 5.1 Host Link and CAN Protocol (RV1106 ↔ DU STM32 ↔ CAN bus)

- **Host link:** UART2 (`/dev/ttyS2`, header pins 8/10) ↔ DU STM32 USART1 (PA9/PA10), 921,600 baud 8N1. Frames are CAN-shaped — `id` (uint16 LE, 11-bit CAN ID), `dlc` (uint8), `data[0..dlc-1]` (≤ 8), `crc16` (CRC-16/CCITT-FALSE over id..data) — COBS-encoded and terminated with 0x00, ≤ 14 bytes on the wire. ≈ 6,500 frames/s of capacity against ≈ 35 frames/s of traffic. Owned by the `link` thread (SCHED_FIFO); the protocol is specified in [[02-Controller-Software-Architecture]] §7.4
- **Gateway:** the DU STM32 forwards AP → bus frames (0x001, 0x010, 0x100–0x103, 0x202, 0x221–0x225, 0x260–0x262, 0x7E0) onto its FDCAN1 unchanged and sends up every bus frame in the AP filter set (0x00x, 0x01x, 0x18x, 0x3xx, 0x7E8). On the bus the node is still AP (src_node 3); the CAN ID map is unchanged
- **DU-local IDs** (terminated on the DU STM32, never on the bus): SET_LED 0x220, SET_BUZZER 0x226, DISPENSE_FID 0x230, DISPENSE_CID 0x231, DISPENSE_SLD 0x232, SLD_PRIME 0x233, QUERY_SLD 0x235, PREFLIGHT 0x236, SLD_CAL 0x237, DISPENSER_HOME 0x238, DISPENSER_STATUS 0x239 (AP → DU), DU_STATUS 0x311 and DU_ACK / NAK 0x3FE (DU → AP). 0x234 reserved
- **CAN bus:** CAN 2.0B at 500 kbps, isolated at the CSC's port (ISO1050DUB #1); the DU STM32's FDCAN1 + a non-isolated SN65HVD230 is the DU's node. The bus crosses the dock on pins 3–5 (stub ≤ 30 cm to the CSC's termination); GND_ISO is tied to the DU ground at pad 5, pad 6 is reserved. Lifting the DU opens the bus; the host link stays up
- **Framing on the bus:** standard 11-bit IDs, DLC ≤ 8, little-endian payloads. Commands (0x2xx) carry `seq` in byte 0; ACK/NAK (0x3FF from the CSC, 0x3FE from the DU STM32) echoes `seq`, `cmd_type` and a result code with up to 5 data bytes. The link's CRC-16 covers the UART hop, CAN hardware CRC + ACK the bus hop
- **Threads:** `link` (SCHED_FIFO) owns the UART and the routing; `heat` (SCHED_FIFO) re-sends the setpoint at 2 Hz; `dispense` (SCHED_OTHER) is a client of the link
- **Timeouts:** ACK 500 ms, 3 retries (longer for dispensing moves, FR-MPU-080); E_STOP needs no ACK. HB_AP every 2 s, forwarded by the gateway (CSC STM32 safe state after 5 s; the DU STM32 drops its dispensers and LED after 5 s without it). TELEMETRY older than 300 ms or HEAT_STATUS older than 500 ms → HEAT_ON_OFF 0, PAUSED (reason AC Power Failure if DU_STATUS says docked without dock_power, UNIT_LIFTED if docked = 0, CAN link loss otherwise). No DU_STATUS for 3 s → DU_LINK_LOST. The heating unit drops to 0 power 1 s after the last setpoint refresh
- **Bus load:** ~6 kbit/s worst case (~1 % of capacity); the dispensing block and DU_STATUS exist only on the host link
- **Firmware update:** 0x7E0 / 0x7E8 carry the CSC STM32 image to its CAN bootloader through the gateway (FR-MPU-062); the DU STM32 is flashed over the same UART with BOOT0/NRST (FR-MPU-063)

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

0x311 is DU_STATUS on the host link (batt_mV, batt_mA, soc_pct, flags, error_code, seq — DU STM32 → RV1106 at 1 Hz and on flag change); it is not a bus message. The DU-local command block above is likewise host-link only.

**DU-local messages on the host link (never on the CAN bus):**

| ID | Message | Dir | DLC | Payload |
|----|---------|-----|-----|---------|
| 0x220 | SET_LED | AP → DU | 2 | seq, duty_pct (0 OFF / 30 NIGHT / 100 CAPTURE) |
| 0x226 | SET_BUZZER | AP → DU | 5 | seq, tone_hz (uint16), duration_ms (uint16) |
| 0x230 | DISPENSE_FID | AP → DU | 3 | seq, box_id, qty (¼ tsp units) |
| 0x231 | DISPENSE_CID | AP → DU | 2 | seq, slot_id (ascending within a session, else NAK) |
| 0x232 | DISPENSE_SLD | AP → DU | 4 | seq, channel (0 oil / 1 water), target_ml (uint16) → ACK data: actual_ml (uint16), primed_ml |
| 0x233 | SLD_PRIME | AP → DU | 2 | seq, channel → ACK data: primed_ml; NAK NOT_DOCKED while lifted |
| 0x235 | QUERY_SLD | AP → DU | 2 | seq, channel → ACK data: flags (bit0 present, bit1 low, bit2 prime_pending), cal_ul (uint16), last_ml (uint16) |
| 0x236 | PREFLIGHT | AP → DU | 1 | seq → ACK data: result bitmap |
| 0x237 | SLD_CAL | AP → DU | 4 | seq, channel, cal_ul (uint16, µL per tach pulse) |
| 0x238 | DISPENSER_HOME | AP → DU | 1 | seq |
| 0x239 | DISPENSER_STATUS | AP → DU | 1 | seq → ACK data: dsp_state, last_error, rail_mA |
| 0x311 | DU_STATUS | DU → AP | 8 | batt_mV (uint16), batt_mA (int16), soc_pct, flags (bit0 docked, bit1 dock_power, bit2 charging, bit3 charge_done, bit4 dsp_rail_on, bit5 dsp_busy, bit6 can_bus_ok, bit7 sld_low), error_code, seq; 1 Hz and on any flag change |
| 0x3FE | DU_ACK / NAK | DU → AP | 3–8 | seq, cmd_type (low byte of the command ID), result_code, data[0..4] |

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
| Lifted | Unit off the dock (loading, cleaning); session PAUSED (UNIT_LIFTED); no bus, no heater | ~3 W → > 12 h on the 38 Wh pack | Pack |
| Mains lost (docked) | PAUSED (AC Power Failure); LCD dimmed, battery indicator shown; auto-resume when the dock returns | ~2 W | Pack |
| Battery low | 6.4 V warning banner; 6.2 V checkpoint + halt | — | Pack |
| Off | Halted after the 6.2 V checkpoint, or pack PCM cut-off (≈ 5.6 V); boots again when docked (charging) or the pack is recharged | 0 W | — |

### 6.2 Power Budget

- Luckfox Pico Zero (SoC + Wi-Fi/BT): ~1–1.5 W
- Display (4" LCD + backlight): ~0.5–1 W
- White LED ring (12–16 LEDs, ≤ 1 A on 5V_MAIN, DU STM32 PWM): up to ~5 W during CAPTURE windows, ~0.3 W averaged at the 2 Hz capture duty — now part of the AP budget on 5V_MAIN
- Buzzer + 3.3 V logic (DU STM32 ≈ 0.1 W, PCA9685, PCF8574 #2, INA219 ×2, SLD Hall switches ×6, SN65HVD230): ~0.3 W
- Total AP subsystem on 5V_MAIN: ≤ 3 W steady state, ≤ 8 W peak with the ring at 100 %
- 6V_DSP dispenser rail (servos and the two 6 V pumps, one at a time, 3 A PTC): budgeted separately from VSYS; off when idle; at an empty pack (6.2 V) the buck drops out to ≈ 6.0 V, acceptable
- Charging (TP5100, 1.0 A into the 2S pack via MP1584EN #1): ~8 W from the dock, docked only

---

## 7. Safety & Fault Handling

### 7.1 RV1106 Safety Responsibilities

The RV1106 is **not** the primary safety controller — the STM32 owns all safety-critical paths. The RV1106's safety role is supervisory:

| Responsibility | Action |
|----------------|--------|
| Heartbeat | Send HB_AP every 2 s over the host link (forwarded to the CAN bus by the DU STM32); if the RV1106 crashes, the DU STM32 drops its dispensers and the CSC STM32 forces the heater off and opens the relay |
| Heater setpoint | Keep HEAT_SET_TEMP / HEAT_SET_POWER alive at 2 Hz; the heating unit regulates and keeps its own cut-offs, the STM32 keeps an independent over-temperature cut-off, and the unit drops to 0 power 1 s after the last refresh |
| Error classification | Analyze STM32 error codes, determine user-facing recovery options |
| Logging | Record all safety events to SQLite with timestamps |
| User notification | Display error/E_STOP screens, guide user through recovery |
| CV anomaly detection | Flag smoke/overflow/dry pot, send E_STOP if critical |

### 7.2 Fault Table (RV1106-Detected)

| Fault | Detection | Severity | Action |
|-------|-----------|----------|--------|
| CAN link loss | No TELEMETRY for 300 ms, 3 consecutive ACK timeouts, or DU_STATUS `can_bus_ok` = 0 — while docked with dock power present | Critical | HEAT_ON_OFF 0, pause cooking, alert user; STM32 holds stir state then safe-shutdown |
| DU_LINK_LOST | No DU_STATUS from the DU STM32 for 3 s, or 3 consecutive 0x3FE timeouts (host link down, DU STM32 crashed or in bootloader) | Critical | Handled like STM32 loss: HEAT_ON_OFF 0 attempted, pause cooking, alert user; the DU STM32 itself drops dispensers and LED on HB_AP loss, the CSC goes safe when HB_AP stops arriving on the bus |
| Heating unit fault | HEAT_FAULT (0x181), fault_flags in HEAT_STATUS, or no HEAT_STATUS for 500 ms | Critical | HEAT_ON_OFF 0, pause, show heater fault |
| Mains power loss | DU_STATUS dock_power clear while docked is set, confirmed by the 300 ms TELEMETRY timeout (detected inside the DU; the CSC STM32 is unpowered and sends nothing) | Warning | Checkpoint, PAUSED (AC Power Failure), battery UI; the DU runs on its pack; auto-resume when TELEMETRY returns within 5 min, prompt < 30 min, ERROR beyond |
| Unit lifted | DU_STATUS docked flag clears (flag-change frame from the DU STM32) | Warning | PAUSED (UNIT_LIFTED); heater stops by keep-alive loss, STM32 safe hold; resume only by user tap after re-docking, 30 min ceiling |
| Battery low / empty | DU_STATUS batt_mV < 6.4 V / < 6.2 V | Warning / Critical | Warning banner / checkpoint + sync + halt, RECOVERING on next boot |
| Charger fault | Neither CHRG nor STDBY with the pack < 8.0 V for 10 min while docked, or pack absent at boot | Warning | Alert, log; cooking allowed |
| DSB_STALL | Reported by the DU STM32 (NAK result / DU_STATUS error_code): INA219 #1 > 2.5 A for 300 ms, 3 s move timeout or PCA9685 NACK, after one retry | Warning | DU STM32 has already set 6V_DSP off, OE high; ERROR with retry / skip / abort |
| SLD_LOW_LEVEL | Tank float Hall low (≈ 20 mL oil / ≈ 50 mL water left; reported by the DU STM32) | Warning | Prompt refill (tank slides out, DU stays docked); dispense step waits; SLD_PRIME after the refill |
| SLD_DISPENSE_ERROR | Pump no-flow (no tach pulse within 1 s, slow tach, or pump current out of window; reported by the DU STM32) | Warning | Pump already off; ERROR with actual vs target (retry / skip / abort) |
| SLD_TANK_ABSENT | Tank-present Hall low at an SLD command (reported by the DU STM32) | Warning | Prompt to seat the tank; dispense step waits |
| NOT_DOCKED (SLD) | DISPENSE_SLD / SLD_PRIME NAK'd while lifted | Info | Never sent by `epicurad` outside the calibration flow (FR-MPU-083); log |
| CV anomaly (smoke/overflow) | Inference confidence ≥ threshold | Critical | Broadcast E_STOP (0x001) on the CAN bus |
| CV failure | Camera disconnect, ISP timeout or `rknn` error | Warning | Fall back to timer + temperature thresholds |
| SQLite write failure | I/O error or `/data` full | Warning | Retry; keep checkpoint in memory; alert user |
| Memory pressure | Free RAM < 32 MB | Warning | Kill `rtsp-stream`, drop LCD preview, log |
| OTA update failure | swupdate exit code / 3 failed boots | Warning | Bootloader falls back to previous slot |
| Wi-Fi disconnect | Network monitor | Info | Continue offline, queue sync in `sync_outbox` |
| `epicurad` hang | Kernel watchdog (10 s) not kicked | Warning | busybox init restarts `epicurad`; heater drops to 0 power within 1 s, CSC STM32 holds stir state meanwhile, DU STM32 drops dispensers after 5 s without HB_AP |

### 7.3 Recovery Sequence (E_STOP)

1. RV1106 broadcasts E_STOP (0x001) on the CAN bus through the DU STM32 gateway (soft stop from the UI, only while docked; the hard E-stop button is on the Cooking Surface and the CSC STM32 initiates independently)
2. STM32 cuts heater relay, disables the stir motor (FDCAN2) and its 24 V, sends STATUS `safety_state = E_STOP`
3. RV1106 sends SET_BUZZER (FR-MPU-025), SET_LED 0 and DISPENSER_HOME / rail-off to the DU STM32 over the host link, displays full-screen red alert
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
| CAN command round-trip (via the gateway) | <10 ms | command sent → ACK (0x3FF) received; adds ≤ 1 ms per UART hop |
| DU-local command round-trip | <5 ms | 0x22x/0x23x sent → DU_ACK (0x3FE) received (excluding the move itself) |
| DU_STATUS flag-change latency | <20 ms | DOCK_SENSE_A edge on the DU STM32 → record in the ring buffer |
| Heat loop period | 100 ms ± 5 ms | `heat` thread wake-up jitter |
| Recipe parse + validate | <2 s | YAML load → state machine ready |
| Live view start | <2 s | `live_view_start` received → first RTSP frame |
| Database query (recipe list) | <100 ms | SQL execute → result set |
| Camera capture interval | 500 ms ± 50 ms | Self-path frame timestamp jitter |
| `epicurad` RSS | ≤10 MB | `/proc/<pid>/status` |

---

## 9. Dependencies & Constraints

### 9.1 Hardware Dependencies

- Unified PCB v5.3 (annular-sector board in the Ø350 mm DU's service ring, 4-layer, Dispensing Unit board): Luckfox Pico Zero in slot J_AP — 5V_MAIN (battery primary), SPI0 (LCD on CS0 via J_LCD, nothing on CS1), I2C3 (touch via J_LCD only), UART2 host link, GPIO 32/38 (DU STM32 BOOT0/NRST), GPIO (LCD DC/RST, touch INT/RST), PWM10 (backlight)
- DU STM32 (STM32G0B1RET6 on the same board): USART1 host link, FDCAN1 → SN65HVD230 (non-isolated DU CAN node), I2C1 to every dispenser / power IC, TIM PWM for pumps, LED ring and buzzer, GPIO for PCA9685 OE, DOCK_SENSE_A, DOCK_PWR_OK; J_SWD for the bench, no USB — see [[05-MCU-Functional-Specification]] (DU instance) and [[01-Unified-PCB-Design]]
- Dock: 8-contact magnetic pogo pads on the DU underside (J_DOCK) over the CS left pillar — DOCK_24V (charge, switched by the CSC), GND, CAN_H / CAN_L / GND_ISO / 5V_ISO, DOCK_SENSE_A (in), DOCK_SENSE_B (out, tied to GND); the DU can only seat one way
- Isolated CAN bus: DU STM32 FDCAN1 + non-isolated SN65HVD230 on the Unified PCB (GND_ISO tied to DU ground at dock pad 5, pad 6 unused), ISO1050DUB #1 + B0505S #1 and termination on the CSC, J_CAN_HEAT to the heating unit (whose CAN port must be SELV); no CAN connector on the Unified PCB besides the dock pads; no CAN controller on the RV1106
- DU STM32 I2C1 peripherals on the Unified PCB: PCA9685 (0x41) with OE, PCF8574 #2 (0x21: P0/P1 spare, P2 spare, P3 TB6612 AIN1, P4 6V_DSP enable, P5 TB6612 BIN1, P6 CHRG in, P7 STDBY in), INA219 #1 (0x40, 6V_DSP rail), INA219 #2 (0x44, BAT+ 10 mΩ); six SLD Hall inputs on PC0–PC5 (J_SLD, 12-pin); TB6612FNG, Q_LED, buzzer 2N7002; TP5100 charger + J_BAT (2S pack), TPS54531, MP1584EN ×2, AMS1117-3.3; J_DSB1–4, J_SLD, J_LED, J_BUZZER
- No J_USB, J_CAN_STIR, J_STIR_PWR, J_SU_IN, J_CAN_HEAT, J_FAN, J_SAFE, HX711, NAU7802, TCA9543A, solenoid drivers, WS2812B or MCP2518FD on this board (moved to the CSC or dropped); J_SWD is back for the DU STM32
- Camera FPC ≤150 mm; IMX415-98 module on the Pico Zero MIPI CSI connector, on the DU underside centred over the pot behind a sealed borosilicate window, with the white LED ring
- Kernel drivers (mainline in 5.10): fbtft, `edt-ft5x06`, 8250 UART, `pwm-rockchip` (backlight), GPIO; `pwm-pca9685`, `gpio-pcf857x`, `ina2xx`, `i2c-mux-pca954x`, `nau7802` and `mcp251xfd` are no longer needed — those devices hang off the DU STM32 or are gone (the NAU7802 load cells were removed with the robot-mop SLD on 2026-11-05)

### 9.2 Software Dependencies

- Luckfox SDK Buildroot (kernel 5.10) with `rockit` (VI/ISP/VENC/RGA), `rknn` runtime, fbtft, `wpa_supplicant`, `bluez5`
- `epicurad`: C11, CMake, pthreads; libraries: SQLite 3 (WAL, JSON1, FTS5), libyaml, cJSON, libmosquitto (client only), libcurl + mbedTLS, LVGL 9, `rknn_api`, swupdate
- RKNN-Toolkit2 on the build host for offline INT8 model conversion (TFLite/ONNX → `.rknn`)
- Not on the device: Python, OpenCV, Docker, PostgreSQL, Node.js, Redis, Mosquitto broker, Kivy, GStreamer, libcamera

### 9.3 Non-Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-MPU-001 | Memory budget: ~80 MB steady state, ~95 MB peak (streaming + inference + UI) of 256 MB | Must | Measured on hardware; CMA reservation set in device tree (VI/ISP 16 MB, self-path + RGA 2 MB, VENC 8 MB on demand) |
| NFR-MPU-002 | Single core: `link` and `heat` threads run at real-time priority (`SCHED_FIFO`); all other threads `SCHED_OTHER` | Must | HB_AP never late by more than 500 ms and the HEAT_SET_TEMP keep-alive never later than 150 ms under UI rendering or sync burst |
| NFR-MPU-003 | Memory-pressure fallback: free RAM < 32 MB → kill `rtsp-stream`, drop LCD preview | Must | Cooking continues uninterrupted |
| NFR-MPU-004 | Sensor runs at 1280×720, not 1080p; phone streaming and LCD preview are on demand only | Must | No VENC channel allocated outside a live-view session |
| NFR-MPU-005 | Read-only rootfs; all mutable state under `/data` and `/userdata` | Must | Power loss at any time leaves a bootable system |
| NFR-MPU-006 | No safety dependency on the AP or the DU STM32: the heating unit drops to 0 power without the setpoint keep-alive and the CSC STM32 forces it off and opens the relay if heartbeats stop; the DU STM32 has no safety authority and only forwards | Must | Verified by killing `epicurad` during a cook, and by holding the DU STM32 in reset |

### 9.4 Cross-References

| Topic | Document |
|-------|----------|
| STM32 MCU spec (CSC and DU instances) | [[05-MCU-Functional-Specification]] |
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
| 1.3 | 2026-11-04 | Manas Pradhan | Dispensing Unit battery doubled to 2S2P 18650, 5,200 mAh (~38 Wh): VSYS note, charge time ≈ 5.5 h, lifted run time > 12 h (§power, power-mode table) |
| 1.4 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: a second STM32G0B1RE on the Unified PCB v5.0 is the DU's CAN node (FDCAN1 + ISO1050DUB #2) and a transparent gateway for the RV1106 over the host link (UART2 ↔ USART1, 921,600 baud, COBS/CRC-16, CAN-shaped frames); MCP2518FD / SocketCAN `can0` and the RV1106-side I2C3 dispenser peripherals, GPIO and PWM removed (I2C3 = touch only); `can` thread → `link` thread; `dispense` thread is a thin client of the DU-local 0x230–0x239 block with DU_ACK 0x3FE; LED ring (SET_LED 0x220) and buzzer (SET_BUZZER 0x226) via the DU STM32; power/dock monitor reads DU_STATUS 0x311; BOOT0/NRST (GPIO 32/38) back for flashing the DU STM32 via the ST system bootloader (FR-MPU-063); DU_LINK_LOST fault; §1, §1.1, §2.2, §2.3, §2.6, §2.7, §2.9, §2.10, §3.1, §3.4, §4, §5.1 (DU-local ID table), §6.2, §7, §8, §9 updated. CAN ID map unchanged |
| 1.5 | 2026-11-04 | Manas Pradhan | Stirring Unit on its own PSU (CSC v1.3): J_SU_IN added to the list of CSC-only connectors in §9.1; nothing on the RV1106 side changes |
| 1.6 | 2026-11-04 | Manas Pradhan | CAN isolation on the CSC only: the DU STM32's node is a non-isolated SN65HVD230 (ISO1050DUB #2 and the dock 5V_ISO feed removed, Unified PCB v5.1); GND_ISO tied to DU ground at dock pin 5, pin 6 reserved; §1.1, FR-MPU-052, §3.4, §5.1, §6.2, §9.1 wording; nothing in `epicurad` changes |
| 1.7 | 2026-11-05 | Manas Pradhan | Robot-mop SLD: open-loop liquid metering on the DU STM32 (tach pulses × cal_ul, drawer tanks with Hall switches, no solenoids or load cells); `epicurad` converts grams to mL, persists cal_ul (SLD_CAL at boot, measuring-cup calibration flow), sends SLD_PRIME after refills, uses QUERY_SLD; faults SLD_TANK_ABSENT / NOT_DOCKED replace SLD_LOAD_CELL_DRIFT; FR-MPU-082/-086/-087/-088, §1.1, pin 16, power bullets, §7.2, §9.1 updated |
