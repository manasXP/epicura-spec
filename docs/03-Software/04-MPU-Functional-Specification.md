---
tags: [epicura, mpu, rv1106, luckfox, functional-spec, software]
created: 2026-02-16
aliases: [RV1106 Spec, MPU Spec]
---

# MPU Functional Specification — Luckfox Pico Zero (RV1106G3)

> **Document ID:** EPIC-SW-MPU-001
> **Processor:** Rockchip RV1106G3, 1x Cortex-A7 @ 1.2 GHz (32-bit, NEON, FPU)
> **RAM / Storage:** 256 MB DDR3L (in-package) / 8 GB eMMC
> **Board:** Luckfox Pico Zero (no carrier board required)
> **Related:** [[05-MCU-Functional-Specification]], [[02-Controller-Software-Architecture]], [[01-Tech-Stack]]

---

## 1. Overview

The RV1106 is the main application processor (AP) for Epicura. It runs Buildroot Linux (Luckfox SDK, kernel 5.10) with a single native C11 application, `epicurad`, that owns all high-level functions: recipe engine, computer vision (hardware ISP + NPU), LVGL touchscreen UI, SQLite storage, and cloud sync (REST + MQTT client). It communicates with the STM32 MCU over a 1 Mbps UART for real-time actuator commands and telemetry. There is no container runtime, database server, message broker or interpreter on the device.

### 1.1 Hardware Summary

| Parameter | Value |
|-----------|-------|
| SoC | Rockchip RV1106G3 (1x Cortex-A7 @ 1.2 GHz) |
| Accelerators | 1 TOPS INT8 NPU, 5 MP hardware ISP, RGA 2D engine, H.264/H.265 encoder (no decoder, no 3D GPU) |
| RAM | 256 MB DDR3L (in-package) |
| Storage | 8 GB eMMC (A/B partitioned); microSD for storage expansion only |
| Camera | MIPI CSI-2 2-lane (SC3336 3 MP, run at 1280×720 @ 30 fps) |
| Display | 4" 480×320 IPS LCD, ST7796S over SPI0, FT6336 capacitive touch over I2C3 |
| Networking | Wi-Fi 6 (2.4 GHz), BLE 5.2 (on-board, external antenna connector); no Ethernet |
| Board | 65 × 30 mm, 40-pin RPi-style header (28 GPIO, 3.3 V), USB-C (power + flashing), on-board mic, RTC battery header |
| Power | 5 V via header (from Driver PCB buck) or USB-C; ~1 W class SoC, no heatsink |

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
| FR-MPU-014 | Request LED ring illumination from the STM32 via SET_LED (0x20): mode OFF/CAPTURE/NIGHT, RGB, brightness | Must | CAPTURE mode (5000–6000 K neutral white) requested before every capture window; ring itself is driven by the STM32 (see [[05-MCU-Functional-Specification]] §2.8) |
| FR-MPU-015 | Image enhancement in the ISP (dehaze, 2D/3D noise reduction, LSC, sharpening, AWB, AE) from the SC3336 tuning file in `/oem` | Must | No CPU image processing (no OpenCV / CLAHE); steam haze handled by ISP dehaze |

### 2.3 User Interface

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-020 | Touchscreen UI via LVGL 9 (C, software rendered) on the 4" 480×320 SPI LCD | Must | 20 Hz LVGL tick; partial redraws; full-frame refresh ≤ 50 ms |
| FR-MPU-021 | Touch-to-visual response <200 ms | Must | Measured from FT6336 evdev event to LCD update |
| FR-MPU-022 | Display state-appropriate screens per state machine | Must | Each state maps to a UI view (see §2.3.1) |
| FR-MPU-023 | On-demand "view pot" preview screen (ISP main path → RGA scale to 480×320 → framebuffer) | Should | ≤ 10 fps; active only while the screen is open; dropped under memory pressure |
| FR-MPU-024 | Recipe browser with search and filtering | Must | Full-text search via SQLite FTS5 |

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

### 2.6 RV1106–STM32 Bridge

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-050 | Bridge thread (C, pthread, `SCHED_FIFO`) on UART2 at 1,000,000 baud, 8N1 | Must | SOF 0x7E / 0x7D byte-stuffed framing, CRC-16/CCITT validation, ACK timeout 500 ms, 3 retries |
| FR-MPU-051 | Send heartbeat to STM32 every 2 s | Must | Missed heartbeat → STM32 watchdog triggers safe state |
| FR-MPU-052 | CAN bus (500 kbps) as production alternative transport | Could | Same message body and type codes; transport selected at build time |
| FR-MPU-053 | Parse unsolicited TELEMETRY (0x10) at 20 Hz | Must | Temp, motor RPM, weight, safety state available to engine/ui/sync threads via ring buffer; no data-ready line |

### 2.7 OTA Updates

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-060 | A/B boot + rootfs slots on eMMC via swupdate with signed `.swu` | Must | Rollback after 3 failed boots |
| FR-MPU-061 | RSA-2048 signature verification on update images | Must | Reject unsigned or tampered images |
| FR-MPU-062 | STM32 firmware update over the bridge UART (RV1106 drives BOOT0 on header pin 32 and NRST on header pin 38, streams `.bin` via ST USART system-bootloader protocol) | Should | CRC verification before commit |

### 2.8 Live View (On Demand)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MPU-070 | On `live_view_start`, bind VENC H.264 1280×720 @ 15 fps, 1.5 Mbps and spawn `rtsp-stream` (RTSP on :554, path `/pot`, single client) | Must | First frame available within 2 s of command |
| FR-MPU-071 | Tear down `rtsp-stream` after 60 s with no client or on `live_view_stop`; free VENC CMA buffers | Must | No encoder channel exists outside a live-view session |
| FR-MPU-072 | Streaming is best-effort and never affects cooking | Must | Any encoder or RTSP error tears down the stream only |

---

## 3. Hardware Interfaces

### 3.1 Header Allocation (Luckfox Pico Zero 40-pin)

| Header Pin | Function | Direction | Notes |
|------------|----------|-----------|-------|
| 8 | UART2_TX (M1) | Output | RV1106 → STM32 USART2_RX (PA3), 1 Mbps, 3.3 V |
| 10 | UART2_RX (M1) | Input | STM32 USART2_TX (PA2) → RV1106 |
| 19 | SPI0_MOSI | Output | LCD data (ST7796S) |
| 21 | SPI0_MISO | Input | LCD (unused by fbtft, reserved) |
| 23 | SPI0_CLK | Output | LCD clock, 50 MHz |
| 24 | SPI0_CS0 | Output | LCD chip select |
| 22 | GPIO | Output | LCD DC (data/command) |
| 26 | GPIO | Output | LCD RST |
| 12 | PWM10 | Output | LCD backlight |
| 16 | I2C3_SDA | Bidir | Touch panel (FT6336) |
| 18 | I2C3_SCL | Output | Touch panel (FT6336) |
| 36 | GPIO | Input | Touch INT (FT6336) |
| 32 | GPIO | Output | STM32 BOOT0 (firmware update) |
| 38 | GPIO | Output | STM32 NRST (firmware update) |
| 35 / 37 | UART0_TX / UART0_RX | — | Debug console (Luckfox default) |
| — | WS2812B data | — | **Not on this header.** LED ring (12–16 LEDs) is driven by STM32 PB14 (TIM15_CH1 + DMA via 74AHCT1G125) to J_LED pin 2; ring 5 V power switched by PCF8574 #2 P3; RV1106 sends SET_LED (0x20) over the bridge |
| spare | UART3, UART4, I2C1, I2C2, PWM | — | Available |

### 3.2 Camera (MIPI CSI)

- Connector: MIPI CSI FPC on the Pico Zero (4-lane connector)
- Interface: MIPI CSI-2, 2-lane (SC3336)
- Cable length: ≤150 mm (signal integrity)
- Sensor: SC3336 3 MP (2304×1296 native, 1/2.8"), run at 1280×720 @ 30 fps; ISP tuning file from the Luckfox SDK in `/oem`
- Paths: ISP main 1280×720 NV12 (preview / stream), ISP self-path 224×224 RGB888 (inference)

### 3.3 Display (SPI LCD)

- 4" 480×320 IPS LCD, ST7796S controller on SPI0 (50 MHz, DMA), fbtft driver, `/dev/fb0`
- Touch: FT6336 capacitive on I2C3, INT on header pin 36, evdev
- Software rendering (no GPU); full-frame refresh ~50 ms, LVGL partial redraws

### 3.4 Power

- Input: 5 V on the 40-pin header (sourced from 24 V → 5 V buck on Driver PCB); USB-C used for bench power and flashing only
- Typical draw: ~1.5 W board (SoC + Wi-Fi), ≤ 3 W with LCD backlight
- No carrier board; all signals on the Pico Zero header

---

## 4. Software Architecture

### 4.1 Operating System

- **Buildroot Linux** from the Luckfox SDK (kernel 5.10), busybox init, no systemd
- Read-only squashfs rootfs; A/B boot + rootfs slots for OTA rollback
- Kernel drivers: fbtft (ST7796S), VI/ISP/VENC/RGA (rockit), RKNN NPU, UART2, wpa_supplicant + bluez5
- eMMC layout: `boot_a/b` 2×32 MB, `rootfs_a/b` 2×256 MB, `oem` 64 MB (models, ISP tuning, LVGL assets, default recipes), `data` ~6 GB (`/data/epicura.db`, images, logs, OTA staging), `userdata` 64 MB

### 4.2 Process & Thread Model

| Thread / Process | Role | Scheduling | Notes |
|------------------|------|------------|-------|
| `epicurad` / ui | LVGL 9 rendering, touch input, pot preview | `SCHED_OTHER` | 20 Hz tick, ~0.6 MB double buffer |
| `epicurad` / engine | YAML parsing, cooking state machine, SQLite checkpoint | `SCHED_OTHER` | 1 Hz tick |
| `epicurad` / cv | rockit VI/ISP, `rknn_api` inference, majority vote | `SCHED_OTHER` | 2 Hz |
| `epicurad` / bridge | UART2 framing, CRC, heartbeat, telemetry ring buffer | `SCHED_FIFO` | Never starved by UI or sync |
| `epicurad` / sync | libmosquitto, libcurl + mbedTLS, outbox drain, OTA check | `SCHED_OTHER` | 10 s cadence |
| `rtsp-stream` (child) | VENC H.264 720p → RTSP :554 | `SCHED_OTHER` | On demand only, ~4 MB |

Memory budget: ~80 MB steady state, ~95 MB peak (streaming + inference + UI) of 256 MB; `epicurad` ~10 MB RSS.

### 4.3 Boot Sequence

1. **U-Boot** → select active A/B slot
2. **Kernel 5.10** → fbtft, VI/ISP, UART2, Wi-Fi/BT drivers
3. **busybox init** → mount `/data`, `/oem`; start wpa_supplicant, kernel watchdog
4. **`epicurad` start** → open SQLite → bridge thread (first heartbeat) → ISP + NPU init → sync thread
5. **UI** → display IDLE / recipe browser (target: <15 s from power-on)

### 4.4 Inter-Thread Communication

- All threads share one process; no local MQTT, no sockets
- Bridge publishes STM32 telemetry into a lock-free ring buffer read by engine, ui and sync
- Engine pushes commands onto the bridge command queue; bridge handles ACK/retry
- CV thread writes the latest `cv_result_t` (stage, confidence, fallback flag) for the engine
- Sync thread receives cloud commands (`cmd` topic) and dispatches to engine / live view

---

## 5. Communication Protocols

### 5.1 UART Bridge Protocol (RV1106 ↔ STM32)

- **Link:** UART2 (header pins 8 TX / 10 RX) ↔ STM32 USART2 (PA3 RX / PA2 TX), 1,000,000 baud, 8N1, 3.3 V
- **Framing:** SOF 0x7E, byte-stuffing with 0x7D escape, then msg_id, msg_type, payload_len, payload (≤ 64 bytes), CRC-16/CCITT. Receiver discards until SOF and validates CRC before dispatch
- **Data-ready:** none. STM32 pushes TELEMETRY at 20 Hz unsolicited; RV1106 reads continuously (`VMIN=1`)
- **Timeouts:** ACK 500 ms, 3 retries; E_STOP needs no ACK. Heartbeat RV1106 → STM32 every 2 s; STM32 IWDG 5 s
- **Bandwidth:** ~28 kbit/s worst case (<3% of link)

**Message Frame:**

```c
#define SOF 0x7E               // start of frame; 0x7D escapes 0x7E/0x7D in body

typedef struct {
    uint8_t  msg_id;       // Sequence number 0–255
    uint8_t  msg_type;     // Command/response type
    uint16_t payload_len;  // 0–64 bytes
    uint8_t  payload[64];  // Variable-length data
    uint16_t crc;          // CRC-16/CCITT over msg_id..payload
} cmd_msg_t;               // Max 70 bytes before stuffing

// Wire format:  SOF | stuffed(msg_id, msg_type, len, payload, crc)
```

**Key Command Types (RV1106 → STM32):**

| Type | Name | Payload | Description |
|------|------|---------|-------------|
| 0x01 | SET_TEMP | target_temp (°C), ramp_rate | Set induction target temperature |
| 0x02 | SET_STIR | pattern, speed_rpm | Set servo stir pattern and speed |
| 0x03 | DISPENSE_ASD | asd_id, target_g | Dispense seasoning from ASD hopper |
| 0x04 | E_STOP | — | Emergency stop all actuators (no ACK) |
| 0x05 | HEARTBEAT | uptime_ms | Liveness, every 2 s |
| 0x20 | SET_LED | mode (OFF/CAPTURE/NIGHT), r, g, b, brightness_pct | LED ring mode request (ring driven by STM32) |
| 0x30 | DISPENSE_ASD | id, target_g | Seasoning dispense |
| 0x31 | DISPENSE_CID | id, mode, position | Coarse ingredient dispense |
| 0x32 | DISPENSE_SLD | channel, target_g | Liquid dispense |
| 0x35 | QUERY_WEIGHT | source (SLD_OIL=1, SLD_WATER=2) | Read SLD load cell |
| 0x37 | TARE | source (SLD_OIL=1, SLD_WATER=2) | Zero SLD load cell |

**Key Response Types (STM32 → RV1106):**

| Type | Name | Payload | Description |
|------|------|---------|-------------|
| 0x10 | TELEMETRY | temp, motor_rpm, weight, state | Periodic status (20 Hz, unsolicited) |
| 0x12 | STATUS | safety_state, error_code, flags | Safety/error report |
| 0xFF | ACK | ack_msg_id, result_code | Acknowledge / NAK |

### 5.2 MQTT Topics (Cloud Broker)

| Topic | Publisher | QoS | Description |
|-------|-----------|-----|-------------|
| `epicura/{device_id}/telemetry` | `epicurad` sync thread | 1 | Telemetry every 10 s while cooking; session lifecycle events and errors (`kind`-tagged) |
| `epicura/{device_id}/cmd` | Cloud | 1 | `live_view_start`, `live_view_stop`, `recipe_sync_now`, `ota_check` |

There are no device-local topics; the broker is AWS IoT Core over TLS.

---

## 6. Power Management

### 6.1 Power States

| State | Description | Typical Draw |
|-------|-------------|-------------|
| Active Cooking | `epicurad` running, ISP + NPU active, display on, Wi-Fi connected | ~3 W |
| Idle | Display on, camera paths idle | ~2 W |
| Standby | Backlight off, reduced polling | ~1 W |
| Off | Powered down (relay-switched) | 0 W |

### 6.2 Power Budget

- Luckfox Pico Zero (SoC + Wi-Fi/BT): ~1–1.5 W
- Display (4" LCD + backlight): ~0.5–1 W
- LED ring (16× WS2812B, ~1 W): on the 5 V rail, switched and driven by the STM32 side — not part of the AP budget
- Total AP subsystem: ≤ 3 W from 5 V rail

---

## 7. Safety & Fault Handling

### 7.1 RV1106 Safety Responsibilities

The RV1106 is **not** the primary safety controller — the STM32 owns all safety-critical paths. The RV1106's safety role is supervisory:

| Responsibility | Action |
|----------------|--------|
| Heartbeat | Send 2 s heartbeat over UART; if the RV1106 crashes, STM32 watchdog triggers safe state |
| Error classification | Analyze STM32 error codes, determine user-facing recovery options |
| Logging | Record all safety events to SQLite with timestamps |
| User notification | Display error/E_STOP screens, guide user through recovery |
| CV anomaly detection | Flag smoke/overflow/dry pot, send E_STOP if critical |

### 7.2 Fault Table (RV1106-Detected)

| Fault | Detection | Severity | Action |
|-------|-----------|----------|--------|
| UART link loss | No TELEMETRY for 500 ms, or 3 consecutive ACK timeouts | Critical | Pause cooking, alert user; STM32 holds last setpoints then safe-shutdown |
| CV anomaly (smoke/overflow) | Inference confidence ≥ threshold | Critical | Send E_STOP (0x04) to STM32 |
| CV failure | Camera disconnect, ISP timeout or `rknn` error | Warning | Fall back to timer + temperature thresholds |
| SQLite write failure | I/O error or `/data` full | Warning | Retry; keep checkpoint in memory; alert user |
| Memory pressure | Free RAM < 32 MB | Warning | Kill `rtsp-stream`, drop LCD preview, log |
| OTA update failure | swupdate exit code / 3 failed boots | Warning | Bootloader falls back to previous slot |
| Wi-Fi disconnect | Network monitor | Info | Continue offline, queue sync in `sync_outbox` |
| `epicurad` hang | Kernel watchdog (10 s) not kicked | Warning | busybox init restarts `epicurad`; STM32 holds last setpoints meanwhile |

### 7.3 Recovery Sequence (E_STOP)

1. RV1106 sends E_STOP (0x04) to STM32 (or STM32 initiates independently)
2. STM32 cuts heater relay, brakes servo, activates buzzer
3. RV1106 displays full-screen red alert
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
| UART command round-trip | <10 ms | msg_id sent → ACK received |
| Recipe parse + validate | <2 s | YAML load → state machine ready |
| Live view start | <2 s | `live_view_start` received → first RTSP frame |
| Database query (recipe list) | <100 ms | SQL execute → result set |
| Camera capture interval | 500 ms ± 50 ms | Self-path frame timestamp jitter |
| `epicurad` RSS | ≤10 MB | `/proc/<pid>/status` |

---

## 9. Dependencies & Constraints

### 9.1 Hardware Dependencies

- Luckfox Pico Zero 40-pin header provides 5 V power, SPI0 (LCD), I2C3 (touch), UART2 (bridge), GPIO (BOOT0/NRST)
- Controller PCB (STM32) connects via USART2 (PA2/PA3) at 3.3 V; on a Nucleo-G474RE prototype PA2/PA3 must be freed from the ST-Link VCP solder bridges
- Driver PCB provides the 5 V buck converter feeding the Pico Zero header
- Camera FPC ≤150 mm; SC3336 module on the Pico Zero MIPI CSI connector
- 74AHCT1G125 level shifter for the LED ring sits on the STM32 side (PB14), not on the AP

### 9.2 Software Dependencies

- Luckfox SDK Buildroot (kernel 5.10) with `rockit` (VI/ISP/VENC/RGA), `rknn` runtime, fbtft, `wpa_supplicant`, `bluez5`
- `epicurad`: C11, CMake, pthreads; libraries: SQLite 3 (WAL, JSON1, FTS5), libyaml, cJSON, libmosquitto (client only), libcurl + mbedTLS, LVGL 9, `rknn_api`, swupdate
- RKNN-Toolkit2 on the build host for offline INT8 model conversion (TFLite/ONNX → `.rknn`)
- Not on the device: Python, OpenCV, Docker, PostgreSQL, Node.js, Redis, Mosquitto broker, Kivy, GStreamer, libcamera

### 9.3 Non-Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| NFR-MPU-001 | Memory budget: ~80 MB steady state, ~95 MB peak (streaming + inference + UI) of 256 MB | Must | Measured on hardware; CMA reservation set in device tree (VI/ISP 16 MB, self-path + RGA 2 MB, VENC 8 MB on demand) |
| NFR-MPU-002 | Single core: bridge thread runs at real-time priority (`SCHED_FIFO`); all other threads `SCHED_OTHER` | Must | STM32 heartbeat never late by more than 500 ms under UI rendering or sync burst |
| NFR-MPU-003 | Memory-pressure fallback: free RAM < 32 MB → kill `rtsp-stream`, drop LCD preview | Must | Cooking continues uninterrupted |
| NFR-MPU-004 | Sensor runs at 1280×720, not 1080p; phone streaming and LCD preview are on demand only | Must | No VENC channel allocated outside a live-view session |
| NFR-MPU-005 | Read-only rootfs; all mutable state under `/data` and `/userdata` | Must | Power loss at any time leaves a bootable system |
| NFR-MPU-006 | No safety dependency on the AP: STM32 cuts heat autonomously if heartbeats stop | Must | Verified by killing `epicurad` during a cook |

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
