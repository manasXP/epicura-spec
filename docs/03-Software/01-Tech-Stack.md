---
created: 2026-02-15
modified: 2026-11-05
version: 2.3
status: Draft
---

# Tech Stack

## 1. Architecture Overview

Epicura uses three controllers with clearly separated responsibilities: the RV1106 handles high-level application logic and AI; the **DU STM32** (STM32G0B1RE on the Unified PCB v5.0 beside the RV1106) runs the dispensers, LED ring, buzzer and battery/dock monitoring and is the Dispensing Unit's CAN node, acting as a transparent gateway for the RV1106 over a UART host link; the **CSC STM32** (same part, Cooking Surface Controller in the base) manages real-time stir control and the safety-critical paths. Both STM32 images are built from one `epicura-firmware` tree.

| Layer | RV1106 (Application) | STM32G0 (Real-Time) |
|-------|----------------------|---------------------|
| **Hardware** | Rockchip RV1106G3 (Luckfox Pico Zero), 1x Cortex-A7 @ 1.2 GHz, 256 MB DDR3L, 8 GB eMMC, 1 TOPS NPU, 5 MP ISP — on the Unified PCB v5.0 in the lift-off Dispensing Unit (DU), 2S Li-ion pack as primary supply | STM32G0B1RE, Cortex-M0+ @ 64 MHz, 512 KB Flash, 144 KB SRAM — two instances: the DU STM32 on the Unified PCB v5.0 (dispensing, CAN gateway) and the CSC STM32 on the Cooking Surface Controller in the base (stir, safety) |
| **OS** | Buildroot Linux (Luckfox SDK, kernel 5.10), busybox init | FreeRTOS 10.x |
| **UI Framework** | LVGL 9 (C, software rendered) on 4" 480x320 SPI LCD | None |
| **AI/ML** | Hardware ISP + NPU via `rockit` / `rknn_api` (RKNN INT8) | None |
| **Application** | C11, single process `epicurad` (Recipe Engine, CV, UI, link, heat, dispense, sync) | C (MISRA C subset); `csc` and `du` images from one tree |
| **Communication** | Host link to the DU STM32: UART2 (`/dev/ttyS2`, 921,600 baud, COBS/CRC-16, CAN-shaped frames) carrying both the CAN traffic (gatewayed) and the DU-local dispensing / LED / buzzer / status frames; I2C3 for touch only; MQTT client, HTTPS client | DU STM32: USART1 host link, FDCAN1 on the isolated 500 kbps bus (crossing the dock pogo contacts), I2C1 to the dispenser / power peripherals. CSC STM32: FDCAN1 on the same bus (commands, telemetry, CAN bootloader); FDCAN2 to the CAN servo stirring motor; no UART to the RV1106 (different unit) |
| **Storage** | SQLite 3 (WAL, JSON1, FTS5), read-only squashfs rootfs + `/data` partition | Non-volatile flash (settings, logs) |
| **Development** | Buildroot `br2-external` + CMake, VS Code + Remote SSH, LVGL PC simulator | STM32CubeIDE, STM32CubeMX |

---

## 2. RV1106 Software Stack

### 2.1 Hardware Platform

**Luckfox Pico Zero (Rockchip RV1106G3):**

| Specification | Value |
|--------------|-------|
| SoC | Rockchip RV1106G3 |
| CPU | 1-core Cortex-A7 @ 1.2 GHz (32-bit, NEON, FPU) |
| Accelerators | 1 TOPS INT8 NPU, 5 MP hardware ISP, RGA 2D engine, H.264/H.265 encoder (no decoder, no 3D GPU) |
| RAM | 256 MB DDR3L (in-package) |
| Storage | 8 GB eMMC (onboard), microSD (storage expansion only) |
| Camera | MIPI CSI-2 FPC (IMX415-98 8 MP, 4-lane) |
| Display | 4" 480x320 SPI LCD (ST7796S) + FT6336 I2C touch |
| Connectivity | Wi-Fi 6 (2.4 GHz), Bluetooth 5.2 LE; no Ethernet |
| GPIO | 40-pin RPi-style header: 28x GPIO, UART, SPI, I2C, PWM (3.3 V) |
| Board | 65 x 30 mm, USB-C (power + flashing), no carrier board required |

### 2.2 Operating System & Process Architecture

**Buildroot Linux (Luckfox SDK, kernel 5.10):**
- Custom `br2-external` tree on the Luckfox SDK; no Yocto, no systemd, no container runtime
- Minimal image: kernel + busybox init + `epicurad`; read-only squashfs rootfs
- Device tree for MIPI CSI camera (IMX415-98), fbtft SPI LCD (SPI0 CS0 only), I2C3 touch (FT6336 only), UART2 host link to the DU STM32 (`/dev/ttyS2`), GPIO 32/38 (DU STM32 BOOT0/NRST), PWM10 backlight. No CAN controller and no dispenser / power ICs on the RV1106 side any more — they hang off the DU STM32
- Kernel drivers (all mainline in 5.10): fbtft, `edt-ft5x06`, 8250 UART, `pwm-rockchip` (backlight); `mcp251xfd`, `pwm-pca9685`, `gpio-pcf857x`, `ina2xx`, `i2c-mux-pca954x` and `nau7802` dropped from the config
- `/data` partition (~6 GB) for SQLite, images, logs and OTA staging
- A/B boot + rootfs slots for OTA updates (swupdate)

**Single-Process Architecture:**

All application functions run as threads of one native C process, `epicurad`, on the RV1106:

```
┌─────────────────────────────────────────────────────────────┐
│          Buildroot Linux (Luckfox SDK, kernel 5.10)         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          epicurad  (C11, pthreads, ~10 MB RSS)         │  │
│  │                                                        │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │  │
│  │  │ ui thread    │ │ engine thread│ │ cv thread    │  │  │
│  │  │ (LVGL 9)     │ │ (Recipe SM)  │ │ (ISP → NPU)  │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘  │  │
│  │                                                        │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │  │
│  │  │ link + heat  │ │ sync thread  │ │ SQLite 3     │  │  │
│  │  │ (UART host   │ │ (MQTT/HTTPS) │ │ (in-process) │  │  │
│  │  │  link, COBS) │ │              │ │              │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘  │  │
│  │                                                        │  │
│  │  ┌──────────────┐ ┌──────────────┐                   │  │
│  │  │dispense thr. │ │ dock monitor │                   │  │
│  │  │(0x23x client)│ │ (DU_STATUS)  │                   │  │
│  │  └──────────────┘ └──────────────┘                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  rtsp-stream  (child process, ON DEMAND ONLY)          │  │
│  │  VENC H.264 720p @ 15 fps → RTSP :554 → phone          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Process Supervision:**
- `epicurad` started by busybox init, restarted on crash; 10 s kernel watchdog
- `rtsp-stream` spawned by `epicurad` on `live_view_start`, killed after 60 s with no client
- Memory budget ~80 MB steady state, ~95 MB peak of 256 MB; free RAM < 32 MB kills `rtsp-stream` and drops the LCD preview

### 2.3 UI Framework

#### 2.3.1 Comparison

| Criteria | LVGL (Chosen) | Kivy | Qt6/QML |
|----------|---------------|------|---------|
| Language | C (pure) | Python (pure) | C++ backend, QML frontend |
| Rendering | Software (no GPU on RV1106) | Requires OpenGL ES GPU | Requires OpenGL ES GPU |
| Widgets | Buttons, sliders, lists, charts, canvas, keyboard | Rich set: buttons, sliders, lists, carousel, video | Rich set: buttons, sliders, lists, charts |
| Camera Integration | Canvas from RGA-scaled framebuffer | Kivy Camera widget + GStreamer | Qt Multimedia + GStreamer |
| Touch Support | evdev touch, gestures | Native multi-touch, gestures | Native multi-touch, gestures |
| Runtime Dependencies | None (static C library) | Python 3 + SDL2 + GStreamer | Qt runtime (~60 MB) |
| Development Speed | Moderate (C, PC simulator) | Fast (Python ecosystem) | Moderate (C++ + QML) |
| Resource Usage | ~2-10 MB RAM | ~40-60 MB RAM + Python | ~60-100 MB RAM |
| Complexity | Medium (C only) | Low (single language) | High (C++ + QML + bindings) |
| **Recommendation** | **Primary choice** | **Not viable: no GPU, no Python on device** | **Overkill, too heavy for 256 MB** |

**Decision Rationale**: The RV1106 has no 3D GPU, 256 MB of RAM and a single Cortex-A7, so a software-rendered C toolkit is the only option that fits. LVGL renders a 480x320 RGB565 frame in well under a frame period with partial redraws, has no runtime dependencies, and ships with a PC simulator so screens can be developed on the desktop. Kivy and Qt6 both assume an OpenGL ES GPU and a far larger memory budget.

#### 2.3.2 LVGL Architecture

```
┌─────────────────────────────────────────────────────────┐
│              ui thread (LVGL 9, C)                       │
│  • HomePage (recipe browser, quick start)               │
│  • CookingPage (temp/time, stage progress, stir)        │
│  • PotPreview (on-demand ISP → RGA → canvas, ≤10 fps)   │
│  • SettingsPage (preferences, pairing, about)           │
│                                                          │
│  LVGL Widgets:                                           │
│  • Screens + lv_obj tree (page navigation)              │
│  • Canvas widget (pot preview from RGA buffer)          │
│  • Chart widget (live temperature graph)                │
│  • Flex/Grid layouts (480x320 layouts)                  │
│  • Button, Slider, Label, Textarea (controls)           │
├─────────────────────────────────────────────────────────┤
│                    LVGL 9 Framework                      │
│  • Core: display driver, 20 Hz tick, timers             │
│  • Graphics: software renderer, RGB565 double buffer    │
│  • Input: evdev touch (FT6336), gestures                │
├─────────────────────────────────────────────────────────┤
│                   In-Process Integration                 │
│  • Direct calls into engine / cv / sync threads         │
│  • Telemetry ring buffer (from link thread)             │
│  • SQLite queries for recipe browser (FTS5)             │
├─────────────────────────────────────────────────────────┤
│   /dev/fb0 via fbtft (ST7796S, SPI0 50 MHz, DMA)         │
│   Buildroot Linux                                        │
└─────────────────────────────────────────────────────────┘
```

### 2.4 AI/ML Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Image Capture | `rockit` VI/ISP (hardware) | IMX415-98 → ISP main path 1280x720 NV12 @ 30 fps |
| Preprocessing | ISP self-path (hardware) | Dehaze, 3DNR, AWB, AE in ISP; scale to 224x224 RGB888 @ 2 fps, zero copy |
| Inference | `rknn_api` on the 1 TOPS NPU | MobileNetV2 INT8 `.rknn` model execution, 5-10 ms |
| Conversion | RKNN-Toolkit2 (off-device, PC) | TFLite/ONNX → `.rknn` with INT8 calibration set |
| Training | Python/Keras (off-device) | Model training on cloud/desktop GPU |
| Labeling | LabelImg / Roboflow | Cooking stage image annotation |

### 2.5 Recipe Engine

- **Language:** C11 (engine thread of `epicurad`)
- **Libraries:** libyaml (recipe parsing into fixed-size struct tree), cJSON (recipe cache + sync payloads), SQLite 3 (recipes, sessions, checkpoint)
- **Interface:** In-process function calls from the LVGL UI thread; no HTTP/RPC boundary
- **Communication:**
  - SQLite for recipe data and the 10 s session checkpoint
  - Telemetry ring buffer from the link thread for real-time state (CSC telemetry, heater status, DU_STATUS)
  - Command queue to the link thread for CSC STM32 commands; heat setpoint to the heat thread; dispense queue to the dispense thread (DISPENSE_FID / CID / SLD, SLD_PRIME, QUERY_SLD, PREFLIGHT, SLD_CAL, DISPENSER_HOME, DISPENSER_STATUS — sent as DU-local frames 0x230–0x239 over the host link to the DU STM32, never on the CAN bus)

### 2.6 Cloud & Networking

| Service | Library / Protocol | Purpose |
|---------|--------------------|---------|
| Telemetry | libmosquitto (MQTT client, TLS, QoS 1) | Direct connection to cloud broker (AWS IoT Core); no local broker |
| Recipe Sync | libcurl + mbedTLS, REST client | `GET /recipes/sync?since=` pull; `sync_outbox` POST push; works offline |
| OTA Updates | swupdate | A/B boot + rootfs slot updates, signed `.swu` |
| Backend API | Fastify (Node.js/TypeScript) — cloud only | REST API for mobile app and device sync; the device is a REST + MQTT client, not a server |
| Live Camera | On-demand H.264 RTSP (`rtsp-stream`, :554 `/pot`) | Stream cooking video to mobile app on request (same LAN direct, else cloud relay) |
| Host link / CAN | link + heat threads of `epicurad` (C, `SCHED_FIFO`) | COBS/CRC-16 frames on `/dev/ttyS2` to the DU STM32 gateway, seq/ACK, HB_AP heartbeat, telemetry buffering, 2 Hz heater setpoint keep-alive (the electric heating unit runs its own PID) |

### 2.7 Storage

**SQLite 3:**
- In-process database at `/data/epicura.db` on a dedicated eMMC partition
- WAL mode, `synchronous=NORMAL` (durable across power loss), JSON1, FTS5
- Mirrors the cloud PostgreSQL schema table-for-table: recipes, cooking logs, user preferences, session checkpoint, sync outbox
- JSON text + JSON1 functions for flexible recipe data
- FTS5 virtual table for recipe discovery
- Sync to cloud through the REST API via the `sync_outbox` table

**Database Architecture:**

| Aspect | Local (RV1106) | Cloud |
|--------|----------------|-------|
| Engine | SQLite 3 (in-process, WAL) | PostgreSQL 16 (RDS/Neon) |
| Schema | Mirror (UUID→TEXT, JSONB→TEXT+JSON1, TEXT[]→JSON array, TIMESTAMPTZ→ISO-8601 TEXT, GIN→FTS5) | Master |
| Purpose | Local cache, offline operation | Centralized data, multi-device sync |
| Sync Direction | REST client: pull recipes, push outbox | REST API endpoint |
| Recipes | Downloaded from cloud + local edits | Master repository |
| Cooking Logs | Created locally, synced to cloud | Aggregated from all devices |
| Images | Cached locally under `/data/images` (100 MB LRU) | Stored in S3/R2 |

### 2.8 Dispensing, Power & Peripheral Drivers

The Dispensing Unit carries the carousels, pumps, SLD drawer tanks with their Hall switches, LED ring, buzzer and battery. Their drivers live in the **DU STM32 firmware** (FreeRTOS, `du` image of `epicura-firmware`), not in Linux: `epicurad` only sends DU-local frames over the host link and reads the replies. Nothing dispensing-related crosses the CAN bus.

| Function | `epicurad` side | DU STM32 side (hardware) |
|----------|-----------------|--------------------------|
| Servo carousels (FID / CID) | `dispense` thread sends DISPENSE_FID 0x230 / DISPENSE_CID 0x231 / DISPENSER_HOME 0x238, waits for DU_ACK 0x3FE | Dispense task: PCA9685 (0x41) on I2C1, 6V_DSP rail enable via PCF8574 #2 P4, PCA9685 OE on PB0; one servo at a time, ramped ≤ 3°/tick |
| Stall detection | NAK result / DU_STATUS error_code → DSB_STALL | INA219 #1 (0x40) on the 6V_DSP rail: > 2.5 A for 300 ms, 3 s timeout or I2C NACK → retry once → DSB_STALL |
| SLD oil / water | DISPENSE_SLD 0x232 (target_ml → actual_ml + primed_ml), SLD_PRIME 0x233, QUERY_SLD 0x235, SLD_CAL 0x237 (cal_ul at boot) | Open loop (2026-11-05): TB6612 pumps on TIM3 PWM (PA6/PA7), direction P3/P5; Hall tachs on PC0/PC1 counted to target_pulses; tank present / low Hall switches on PC2–PC5; prime routine; nozzle check valves (no solenoids, no load cells) |
| LED ring (white, 5000 K) | SET_LED 0x220 (duty_pct) | TIM1 PWM 1 kHz → Q_LED low-side on 5V_MAIN; duty OFF 0 % / CAPTURE 100 % / NIGHT 30 %; no colour control |
| Buzzer | SET_BUZZER 0x226 (tone_hz, duration_ms) | TIM14 PWM → 2N7002 driver on the Unified PCB |
| Battery / dock monitor | Decodes DU_STATUS 0x311 (1 Hz + on flag change): batt_mV, batt_mA, soc_pct, docked, dock_power, charging, charge_done, can_bus_ok. Warning banner at 6.4 V, checkpoint + halt at 6.2 V; battery indicator always visible in the UI; no DU_STATUS for 3 s → DU_LINK_LOST | Monitor task: INA219 #2 (0x44, 10 mΩ in the BAT+ path) → state of charge; TP5100 CHRG / STDBY on PCF8574 #2 P6/P7; DOCK_SENSE_A (PB3, low = docked), DOCK_PWR_OK (PB5, active-low) with EXTI |
| Host-loss rule | — | No HB_AP for 5 s → 6V_DSP off, OE high, pumps off, LED off; DU_STATUS keeps going |

### 2.9 RV1106 Development Tools

| Tool | Purpose |
|------|---------|
| Luckfox SDK (Buildroot) + `br2-external` tree | Build custom Linux image, kernel, device tree |
| CMake + Luckfox cross toolchain | Build `epicurad` and `rtsp-stream` |
| `luckfoxtech/luckfox_pico:1.0` Docker image | Reproducible build environment on the build host and CI (Docker is a build tool only, never on the device) |
| VS Code + Remote SSH / adb over USB-C | Development and deployment on target |
| GDB (gdbserver) | C debugging over SSH |
| perf / top | Performance profiling on target |
| Unity + CMock (or cmocka) via CMake/ctest | Host-side C unit testing |
| LVGL PC simulator (SDL) | UI development without hardware |
| RKNN-Toolkit2 | Model conversion and INT8 calibration on the PC |

---

## 3. Host Link and CAN Bus Node (RV1106 ↔ DU STM32 ↔ CSC STM32 ↔ Heating Unit)

The RV1106 has no CAN peripheral. It talks to the DU STM32 over the **host link** — UART2 (`/dev/ttyS2`) ↔ USART1 at 921,600 baud, CAN-shaped frames (11-bit id, dlc, ≤ 8 data bytes, CRC-16/CCITT-FALSE) COBS-encoded with a 0x00 terminator — and the DU STM32 is the Dispensing Unit's node on the CSC's isolated CAN bus (FDCAN1 + a non-isolated SN65HVD230; the isolation is on the CSC's port). It forwards every bus-bound frame unchanged and sends up every frame in the AP filter set, so on the bus the node is still AP (src_node 3) and the CAN ID map is unchanged; DU-local IDs (0x220, 0x226, 0x230–0x239, 0x311, 0x3FE) terminate on the DU STM32. The isolated domain is generated on the Cooking Surface Controller (CSC) in the base and reaches the Unified PCB over the dock pogo contacts (J_DOCK pins 3–5: CAN_H, CAN_L, GND_ISO tied to the DU ground there; pin 6 5V_ISO reserved); lifting the unit opens the bus but not the host link. Two real-time threads inside `epicurad` own the link: `link` handles every frame and the routing, `heat` keeps the heater setpoint alive and relays the unit's measured temperature (the heating unit runs its own PID; Epicura has no temperature sensor). Protocol detail: [[02-Controller-Software-Architecture#7.4|Controller Software Architecture §7.4]].

### 3.1 CAN Node Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  epicurad (RV1106, single process)          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Recipe Engine│ │  LVGL UI     │ │  Cloud Sync  │        │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│      command queue / setpoint / telemetry ring buffer       │
│                          │                                  │
│   ┌──────────────────────▼──────────┐  ┌─────────────────┐  │
│   │   link thread (SCHED_FIFO)      │  │ heat thread     │  │
│   │  • /dev/ttyS2 921,600, COBS+CRC │◄─┤ (SCHED_FIFO)    │  │
│   │  • route: bus IDs ↔ DU-local IDs│  │ • 2 Hz setpoint │  │
│   │  • seq / ACK / retry (500ms x3) │  │   keep-alive    │  │
│   │  • TELEMETRY + DU_STATUS buffers│  │ • HEAT_SET_TEMP │  │
│   │  • HB_AP heartbeat (2 s)        │  │                 │  │
│   └────────────┬────────────────────┘  └─────────────────┘  │
│                │  UART2 ↔ USART1 (host link)                 │
└────────────────┼────────────────────────────────────────────┘
       ┌─────────▼──────────────────────────────┐
       │ DU STM32 (STM32G0B1RE, Unified PCB v5.0)│
       │ Link/Gateway task: UART ↔ FDCAN1       │
       │ Dispense task: PCA9685, TB6612, tachs  │
       │ Monitor task: INA219 x2, dock sense    │
       └─────────┬──────────────────────────────┘
                 │ FDCAN1 → SN65HVD230 (non-isolated) → J_DOCK pins 3–5 (pogo contacts, stub ≤ 30 cm)
      ═══════════╪════════ isolated CAN bus ════════════════════
                 │                              │
       ┌─────────▼─────────┐          ┌─────────▼─────────┐
       │ STM32G0B1RE (CSC) │          │ Heating unit MCU  │
       │ FDCAN1 + ISO1050  │          │ (onboard CAN,     │
       │ #1 + B0505S 5V_ISO│          │ own PID)          │
       │ stir (FDCAN2),    │          │ HEAT_STATUS,      │
       │ fans, relay, dock │          │ HEAT_SET_TEMP     │
       └───────────────────┘          └───────────────────┘
```

### 3.2 Host Link and CAN Node Features

| Feature | Implementation |
|---------|----------------|
| **Protocol** | CAN 2.0B, 11-bit IDs: 0x001 E_STOP, 0x010 HB_AP, 0x1xx heater, 0x2xx commands (seq byte first), 0x3xx reports, 0x3FF ACK/NAK, 0x7E0/0x7E8 firmware update — map in [[02-Controller-Software-Architecture#7.2 Message Types\|Controller Software Architecture §7.2]] |
| **Transport** | Host link UART2 ↔ DU STM32 USART1, 921,600 baud 8N1, COBS-encoded frames `id(u16 LE) dlc data[≤8] crc16`; the DU STM32's FDCAN1 + a non-isolated SN65HVD230 puts the frames on the bus, which reaches the CSC's isolated port (ISO1050DUB #1) through J_DOCK pins 3–5 at 500 kbps. DU-local IDs 0x220, 0x226, 0x230–0x239 (AP → DU) and 0x311, 0x3FE (DU → AP) never leave the link |
| **Message Queue** | In-process command queue (pthread mutex + condvar); seq-matched ACK/NAK |
| **Telemetry Buffer** | Lock-free ring buffer; 20 Hz TELEMETRY + 10 Hz HEAT_STATUS; SQLite checkpoint every 10 s |
| **Heater setpoint** | `heat` thread: HEAT_SET_TEMP (target, ramp ≤ 5 °C/s, max power) or HEAT_SET_POWER re-sent at 2 Hz; `surface_temp` from HEAT_STATUS to engine/ui; HEAT_ON_OFF 0 if HEAT_STATUS > 500 ms old |
| **Health Monitoring** | HB_AP every 2 s, forwarded by the gateway (CSC safe state after 5 s; DU STM32 drops dispensers after 5 s); TELEMETRY watchdog 300 ms, HEAT_STATUS watchdog 500 ms; DU_STATUS watchdog 3 s (DU_LINK_LOST); `can_bus_ok`, `docked` and `dock_power` flags in DU_STATUS tell bus-off, a lifted unit or a mains outage from an STM32 fault |
| **STM32 firmware update** | CSC: CAN bootloader client — FW_UPDATE_REQ 0x7E0 / FW_UPDATE_RSP 0x7E8 (ERASE / WRITE / VERIFY / BOOT) streamed by the swupdate handler through the gateway to the in-application bootloader on the CSC. DU STM32: ST system bootloader over the same UART with BOOT0 (GPIO 32) / NRST (GPIO 38), driven by the swupdate handler |
| **API** | C API: `link_send()`, `link_poll_telemetry()`, `link_du_status()`, `heat_set_setpoint()` |
| **Logging** | syslog (busybox) / stderr; `epicurad --link-dump` prints decoded host-link frames (bus capture with a CAN analyser on J_CAN_HEAT) |

### 3.3 Host Link Stack

```c
/* epicurad link + heat threads — no external dependencies beyond the kernel */
├── termios on /dev/ttyS2 (921,600 8N1, raw)                                      /* host link */
├── link_codec.c (COBS encode/decode, CRC-16/CCITT-FALSE, frame = id/dlc/data)
├── can_codec.c (ID map, little-endian payload packing, seq/ACK matching; DU-local vs bus routing)
├── heat_setpoint.c (2 Hz HEAT_SET_TEMP / HEAT_SET_POWER keep-alive, HEAT_STATUS parsing)
├── pthread (SCHED_FIFO link + heat threads)
├── ring buffer (telemetry + heater status + DU_STATUS → engine / ui / sync / heat / dispense)
├── stm32_can_bootloader.c (0x7E0/0x7E8 OpenBLT-style client for the CSC, through the gateway)
└── stm32_uart_flash.c (BOOT0/NRST + ST system-bootloader protocol for the DU STM32)
```

---

## 4. STM32 Software Stack

### 4.1 Hardware Platform

#### 4.1.1 Primary Choice: STM32G0B1RE

| Specification | Value |
|--------------|-------|
| Core | ARM Cortex-M0+ @ 64 MHz |
| Flash | 512 KB, dual-bank, ECC (STM32G0B1RET6; 256 KB RCT6 as cost-down) |
| SRAM | 144 KB with parity |
| FPU | None (not needed: no control loop on the MCU, fastest task 50 Hz) |
| ADC | 1x 12-bit ADC (2.5 Msps, 16 channels, hardware oversampling) |
| Timers | TIM1 advanced, TIM2/3/4, TIM14–17, LPTIM1/2 |
| Comm | 6x USART + 2x LPUART, 3x SPI, 3x I2C, USB FS, 2x FDCAN |
| Safety | IWDG, WWDG, SRAM parity, flash ECC, CRC; X-CUBE-CLASSB (IEC 60730-1 Class B) |
| Package | LQFP-64 (LQFP-48 also fits the pin budget) |
| Boards | Two instances: Cooking Surface Controller (CSC) v1.0, ~100 × 70 mm, 4-layer, in the Cooking Surface base beside the three Mean Well PSUs (its own LRS-35-12 on J_12V_IN; LRS-75-24 #1 for the DU, #2 for the SU) (J_SWD, USB-C J_USB DFU + CDC bench only, J_DBG); and the Unified PCB v5.0 in the Dispensing Unit (DU STM32: J_SWD only, flashed by the RV1106 over USART1 with BOOT0/NRST) |
| Dev board | NUCLEO-G0B1RE (MB1360), ~$11 |

#### 4.1.2 Previous Choice: STM32G474RE

| Specification | Value |
|--------------|-------|
| Core | ARM Cortex-M4F @ 170 MHz |
| Flash | 512 KB |
| SRAM | 128 KB |
| FPU | Single-precision hardware FPU |
| ADC | 5x 12-bit ADC (up to 4 Msps) |
| Timers | Advanced PWM timers, HRTIM |
| Comm | 3x UART, 3x SPI, 4x I2C, 3x FDCAN |
| Package | LQFP-64 or LQFP-100 |

**Recommendation:** STM32G0B1RE. It is the cheapest ST part with two FDCAN controllers (FDCAN1 on the isolated host/heater bus, FDCAN2 on the second isolated stir-motor bus) and keeps the same HAL, FreeRTOS, system bootloader (USB DFU on the bench) and Class B library as the G474. The G474's FPU, 170 MHz and HRTIM were only needed while the MCU ran the temperature PID and a PWM motor; both have left the MCU. An RP2040 was rejected: no CAN peripheral (two external controllers or a PIO soft-CAN on the heater kill path), no internal flash, no UART ROM bootloader and no certified Class B library erase the price gap.

### 4.2 RTOS

**FreeRTOS 10.x:**
- CSC image, 4 tasks: Motor Control 50 Hz (FDCAN2 stir servo), Safety Monitor 10 Hz, CAN Comms 20 Hz (FDCAN1), Thermal/Fan 1 Hz (fans, optional tach, pot reed)
- DU image, 3 tasks: Link/Gateway (event-driven: USART1 DMA ↔ FDCAN1 RX FIFO, COBS codec, ID routing, HB_AP watchdog), Dispense (50 Hz while a move is active: PCA9685, TB6612 pumps with Hall tach metering, tank Hall switches, prime routine, INA219 #1 stall window), Monitor (1 Hz + EXTI: INA219 #2, charger, dock sense → DU_STATUS; LED and buzzer PWM). No safety authority on the DU STM32
- One tree, two targets (`csc`, `du`): shared HAL, FreeRTOS, CAN frame codec, Class B start-up self-tests
- Priority-based preemptive scheduling
- Memory: heap_4 allocator (128 KB SRAM budget)
- Tick rate: 1 kHz (1 ms resolution)
- Stack monitoring enabled for overflow detection

### 4.3 Language & Standards

- **Language:** C11 (MISRA C:2012 subset for safety-critical paths)
- **Math:** CMSIS-DSP library for signal filtering (no temperature PID anywhere in Epicura; the heating unit regulates itself)
- **Coding standard:** MISRA C mandatory for safety monitor and motor control tasks

### 4.4 HAL & Drivers

| Peripheral | Driver | Usage |
|------------|--------|-------|
| PWM (TIM) | STM32 HAL TIM | Exhaust fans: PA6 (TIM3_CH1) and PB10 (software PWM) → fan MOSFETs, 25 kHz |
| ADC | STM32 HAL ADC | USB VBUS detect (PA0) only — no battery on this board |
| USART | STM32 HAL UART | USART2 (PA2/PA3) → J_DBG local debug console only; no host link |
| USB FS | STM32 HAL PCD / system bootloader | USB-C J_USB: DFU + CDC, bench only (SW_BOOT, SW_RST) |
| FDCAN1 | STM32 HAL FDCAN | Isolated 3-node bus: host commands/telemetry with the RV1106, HEAT_STATUS monitoring, HEAT_ON_OFF=0 off-switch, in-application CAN bootloader (0x7E0/0x7E8) |
| FDCAN2 | STM32 HAL FDCAN | Second isolated 1 Mbps bus (ISO1050DUB #3, SU domain) to the CAN servo stirring motor (velocity/position commands, feedback) |
| GPIO | STM32 HAL GPIO | E-stop (PB2, EXTI), safety relay Q_RLY (PB0), pot reed (PB1), DOCK_SENSE_B in (PB3, 10k pull-up, low = DU present), K_SU enable (PB4, pilot relay on the Stirring Unit PSU's AC input), Q_DOCK enable (PB5), status LED (PC7) |
| IWDG | STM32 HAL IWDG | Independent watchdog (safety) |

### 4.5 STM32 Development Tools

| Tool | Purpose |
|------|---------|
| STM32CubeIDE | Integrated C development, debugging |
| STM32CubeMX | Peripheral configuration, code generation |
| ST-Link V3 | On-chip debugging and programming |
| openocd | Alternative debug interface |
| STM32CubeProgrammer | Flash programming and option bytes |
| Logic Analyzer | UART/SPI/I2C protocol debugging |

---

## 5. Companion Mobile Apps

### 5.1 Framework Comparison

| Criteria | Native (Swift + Kotlin) (Chosen) | Flutter (Previously Considered) |
|----------|----------------------------------|--------------------------------|
| Language | Swift 5.9+ (iOS), Kotlin 1.9+ (Android) | Dart |
| UI Framework | SwiftUI / Jetpack Compose | Custom Skia engine |
| BLE Support | Core Bluetooth / CompanionDeviceManager (direct platform APIs) | flutter_blue_plus (plugin-based, limited control) |
| Camera Streaming | Hardware H.264 decode (VideoToolbox / MediaCodec) with an RTSP client library | Plugin-based, frame decoding overhead |
| Platform Feel | 100% native UI, gestures, animations | Approximates native via Skia |
| Background Processing | Full OS-level support (BGTasks / WorkManager) | Limited plugin support |
| App Size | ~15-25 MB per platform | ~25-40 MB (Dart runtime + Skia) |
| Push Notifications | Native APNs / FCM integration | Plugin-based |
| **Recommendation** | **Primary choice** | **Not selected** |

**Decision:** Native development provides superior BLE integration, camera streaming performance, and platform-native UX — all critical for Epicura's pairing and live cooking flows. See [[../12-MobileApps/01-Mobile-Architecture|Mobile Architecture]] for full rationale.

### 5.2 Communication

| Channel | Protocol | Purpose |
|---------|----------|---------|
| WiFi (Same LAN) | RTSP / H.264 (`rtsp://<device>:554/pot`) | On-demand live camera feed during cooking; cloud relay when not on the same LAN |
| Cloud | HTTPS REST API | Recipe browsing, settings, history, remote monitoring, recipe store |
| Cloud | WebSocket (cloud relay) | Real-time cooking progress via backend |
| Cloud | Push notifications (FCM/APNs) | Cooking complete, error alerts |
| BLE | GATT services | Device pairing, WiFi provisioning |

### 5.3 Key Screens

1. **Recipe Browse** - Grid of recipes with filters (category, time, difficulty)
2. **Recipe Detail** - Ingredients, steps, customization (spice level, allergens)
3. **Cooking Progress** - Live camera feed, temperature gauge, stage progress
4. **History** - Past cooks with ratings, time logs, notes
5. **Settings** - Device pairing, spice preferences, allergen profiles, language
6. **Remote Start** - Select recipe and start cooking remotely
7. **Device Pairing** - BLE scan, WiFi provisioning, cloud account linking

---

## 6. Testing & Validation

### 6.1 RV1106 Testing

| Framework | Language | Scope |
|-----------|---------|-------|
| Unity + CMock (or cmocka) via CMake/ctest | C | Recipe engine, frame codec, sync logic, SQLite layer (host-side, mocked rockit/rknn) |
| gcov / lcov | C | Code coverage reporting |
| LVGL PC simulator | C | UI screens and navigation on the desktop |
| HIL on Luckfox Pico Zero | C | ISP/NPU pipeline, host link to the DU STM32 (and through it the CAN bus), heat loop, LCD, Wi-Fi |

### 6.2 STM32 Testing

| Framework | Language | Scope |
|-----------|---------|-------|
| Unity test framework | C | CAN command parser, safety logic, motor control (CSC); COBS/CRC codec, gateway routing, dispensing state machine, HB_AP watchdog (DU) |
| CMock | C | Mock HAL functions for unit testing |
| Ceedling | C | Build system for Unity + CMock |

### 6.3 Integration & System Testing

| Method | Purpose |
|--------|---------|
| Hardware-in-Loop (HIL) | STM32 + real sensors, RV1106 + camera, end-to-end |
| pty / CAN loopback | Protocol testing without full hardware (host-link loopback on a `pty` pair with a simulated DU STM32 for `epicurad`; FDCAN internal loopback on the STM32) |
| Static analysis (cppcheck) | C code quality on both platforms |
| PC-lint (MISRA) | MISRA C compliance on STM32 safety code |
| Valgrind / AddressSanitizer | Memory error detection on host-side `epicurad` unit tests |
| LVGL performance monitor | UI rendering performance (FPS / CPU overlay) on RV1106 |

---

## 7. Firmware Update Strategy

### 7.1 RV1106 (Buildroot Linux)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        eMMC Partition Layout (8 GB)                      │
├─────────┬─────────┬───────────┬───────────┬────────┬──────────┬──────────┤
│ boot_a  │ boot_b  │ rootfs_a  │ rootfs_b  │ oem    │ data     │ userdata │
│ 32 MB   │ 32 MB   │ squashfs  │ squashfs  │ 64 MB  │ ~6 GB    │ 64 MB    │
│         │         │ 256 MB    │ 256 MB    │        │          │          │
└─────────┴─────────┴───────────┴───────────┴────────┴──────────┴──────────┘
```

- **Mechanism:** swupdate with A/B boot + rootfs slots
- **Delivery:** HTTPS download of signed `.swu` to `/data/ota` (on `ota_check` command or daily)
- **Verification:** RSA-2048 signature on update image
- **Rollback:** If boot fails 3 times, bootloader reverts to previous slot
- **Data partition:** Preserved across updates (recipes, logs, preferences); `oem` holds models, ISP tuning, LVGL assets

### 7.2 STM32 (FreeRTOS)

- **Mechanism (CSC):** In-application CAN bootloader (OpenBLT-style) on the CSC, reached through the DU STM32 gateway; no UART or BOOT0/NRST lines exist between the units
- **Mechanism (DU STM32):** ST system bootloader on USART1 — the swupdate handler raises BOOT0 (GPIO 32), pulses NRST (GPIO 38), writes and verifies the image over `/dev/ttyS2`, lowers BOOT0 and resets; the `link` thread is suspended meanwhile and DU_STATUS resumes within 2 s
- **Trigger:** the RV1106 swupdate handler sends FW_UPDATE_REQ 0x7E0 `op = ERASE` while the appliance is docked and idle; the STM32 answers on FW_UPDATE_RSP 0x7E8 and enters update mode (stir disabled, heater off-switch and E_STOP handling stay active)
- **Delivery:** the image is streamed in 0x7E0 `WRITE` frames (5 data bytes each) over the isolated CAN bus, through the dock; `VERIFY` then `BOOT`. Update frames carry the lowest priority on the bus
- **Verification:** CRC over the written bank before `BOOT`
- **Rollback:** Dual-bank flash — the previous bank stays bootable until `VERIFY` passes
- **Bench fallback:** USB-C DFU on the CSC (SW_BOOT + SW_RST); SWD (J_SWD) for factory programming

---

## 8. Development Timeline

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| **Environment Setup** | 2 weeks | Luckfox SDK Buildroot `br2-external` for RV1106, STM32CubeIDE project, toolchain validation |
| **Hardware Bring-up** | 4 weeks | RV1106 boot + SPI LCD + touch, STM32 peripherals (PWM, ADC, FDCAN), CAN bus bring-up, IMX415-98 camera test |
| **Core Firmware** | 6 weeks | FreeRTOS tasks, CAN servo motor control (FDCAN2), safety monitor, CAN protocol; RV1106 heat thread setpoint keep-alive |
| **CV Integration** | 4 weeks | ISP/NPU pipeline, model training (collect cooking images), RKNN conversion on RV1106 |
| **UI Development** | 4 weeks | LVGL screens (home, cooking, settings) at 480x320, pot preview, recipe browser |
| **App Development** | 3 weeks | Native iOS + Android apps (recipe browse, live view, settings), WiFi communication |
| **System Integration** | 4 weeks | End-to-end cooking tests, timing tuning, error handling, OTA updates |

**Total estimated:** ~27 weeks (approximately 7 months) from environment setup to integration complete.

---

## 9. Design Decisions

| Decision | Chosen | Alternative | Rationale |
|----------|--------|-------------|-----------|
| Application Processor | RV1106G3 (Luckfox Pico Zero) | Raspberry Pi CM5 | ~1 W, $47, no carrier board, hardware ISP + 1 TOPS NPU + H.264 encoder cover the whole vision path; see [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]] |
| RV1106 OS | Buildroot Linux (Luckfox SDK) | Yocto, Raspberry Pi OS | Vendor SDK with rockit/rknn drivers, tiny image for 256 MB RAM, A/B OTA via swupdate, no container runtime needed |
| UI Framework | LVGL 9 | Kivy, Qt6/QML | Software-rendered C toolkit fits a GPU-less single-core SoC with 256 MB; Kivy and Qt6 require OpenGL ES and far more RAM |
| Recipe Engine Language | C11 | Python 3.11+ | No interpreter on the device; libyaml + SQLite in one process; deterministic memory use on 256 MB |
| Mobile App Framework | Native (Swift + Kotlin) | Flutter | Native platform APIs for BLE (Core Bluetooth, CompanionDeviceManager) and camera streaming; better UX, smaller app size |
| Backend Framework | Fastify (TypeScript) | Express, NestJS | Fastest Node.js framework, built-in schema validation, TypeScript-first, plugin system (cloud only; device is a client) |
| STM32 RTOS | FreeRTOS | Bare metal | FreeRTOS provides task isolation, priority scheduling, and watchdog integration needed for concurrent motor + safety + CAN comms |
| Inter-Processor Comm | Isolated CAN 2.0B 500 kbps between the units (DU STM32 FDCAN1, CSC STM32 FDCAN1, heating unit MCU); UART host link (921,600, COBS/CRC) between the RV1106 and the DU STM32 inside the DU, with the DU STM32 as a transparent CAN gateway | MCP2518FD on the RV1106 SPI0, DU STM32 as a second CAN node, UART-only peripheral MCU | One bus for all three units with hardware CRC/ACK and priority arbitration for E_STOP, isolated once at the CSC's port (the DU node is a plain SN65HVD230, GND_ISO tied to DU ground at the dock); the RV1106 needs no CAN controller or SocketCAN, SPI0 is the LCD's alone, and the CAN ID map is untouched because the gateway forwards AP frames unchanged; the same UART flashes the DU STM32 via the ST system bootloader |
| DU MCU (dispensing) | STM32G0B1RE on the Unified PCB v5.0 running the dispensers, LED ring, buzzer and battery/dock monitor | RV1106 driving them directly over I2C3 / PWM / GPIO (v4.0) | The Pico Zero header runs out of I/O once the camera, LCD and touch are placed; a second G0B1 shares the CSC toolchain, bootloader and Class B library, gives deterministic 50 Hz servo ramps off the single Linux core, and leaves the RV1106 with camera, display and one UART |
| Stirring Motor Interface | CAN servo on STM32 FDCAN2 (second isolated port, ISO1050DUB #3 + B0505S #2); the Stirring Unit runs from its own LRS-75-24 #2 with GND_SU never bonded to the CS ground, cut by the K_SU pilot relay on the PSU's AC input | PWM + EN/DIR BLDC; non-isolated SN65HVD230 port with a Q_STIR 24 V switch on the CS supply | Encoder feedback (rpm, angle, current, temperature) over two wires; stall detection from the motor itself; separate bus keeps the 1 Mbps motor protocol off the isolated heater bus; with the SU on its own supply its ground must not tie to the CS ground, so isolating FDCAN2 too leaves the ISO1050 barrier and the B0505S transformer as the only galvanic links between CS and SU, and a relay on the PSU's AC input gives the command-independent stop without a switch in the floating rail |
| Temperature Control | Unit-internal PID (electric heating unit's own centre sensor), RV1106 sends setpoints | IR thermometer + PID on the RV1106 / STM32 | No sensor, emissivity calibration or tuning in Epicura; the pre-certified heating unit already regulates; camera covers food-state decisions |
| Dispensing-unit battery (primary supply, dock charging) | 2S Li-ion pack + TP5100 (1.0 A) on the Unified PCB v5.0 as the DU's primary supply, DOCK_24V charging through the dock, VSYS diode-OR | External 12 V UPS, mains-only DU with a tethered cable | The DU lifts off with no cable; the brain keeps running through a mains outage (> 12 h at ≈ 3 W on the 5,200 mAh pack) and the session auto-resumes when TELEMETRY returns; the pack lives in the cool zone away from the heat |
| STM32 Variant | STM32G0B1RE | STM32G474RE, RP2040 | Two FDCAN controllers at about half the G474's price; nothing on the MCU needs the G474's FPU or 170 MHz any more; RP2040 has no CAN, no internal flash and no Class B library, so its saving disappears once those are added |
| CV Model | MobileNetV2 INT8 (RKNN) | Custom CNN | MobileNetV2 converts cleanly with RKNN-Toolkit2, runs in 5-10 ms on the RV1106 NPU, proven on ARM |
| Database | SQLite 3 (in-process) | PostgreSQL (Docker), MongoDB | Zero-server embedded DB fits 256 MB; JSON1 + FTS5 mirror the cloud PostgreSQL schema table-for-table so sync is a row copy |
| Firmware Update | swupdate (A/B) | Manual SD card | A/B partitions enable safe OTA with automatic rollback; SD card update requires physical access |

---

## 10. Related Documentation

- [[../01-Overview/01-Project-Overview|Project Overview]]
- [[02-Controller-Software-Architecture|Controller & Software Architecture]]
- [[../04-UserInterface/01-UI-UX-Design|UI/UX Design]]
- [[../10-Backend/01-Backend-Architecture|Backend Architecture]]
- [[../11-API/01-REST-API-Reference|REST API Reference]]
- [[../12-MobileApps/01-Mobile-Architecture|Mobile Architecture]]
- [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]]

#epicura #tech-stack #development #rv1106 #luckfox #stm32 #buildroot #lvgl #freertos #swift #kotlin #native-mobile #rknn

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Application processor changed from Raspberry Pi CM5 to RV1106G3 (Luckfox Pico Zero): device stack is Buildroot + single C11 process (`epicurad`) with LVGL, SQLite, libmosquitto/libcurl clients, rockit/rknn vision and swupdate; Docker/PostgreSQL/Kivy/Python removed from the device; bridge moved from SPI to UART 1 Mbps; on-demand RTSP live view replaces MJPEG. Cloud stack unchanged |
| 1.2 | 2026-11-04 | Manas Pradhan | GPIO row updated for the Dispenser Servo Block (PCA9685 OE; stepper/linear-actuator and limit-switch lines removed) |
| 1.3 | 2026-11-04 | Manas Pradhan | Camera IMX415-98; CAN alternative for the STM32 link removed |
| 1.4 | 2026-11-04 | Manas Pradhan | RV1106 joins the isolated CAN bus (MCP2518FD on SPI0 CS1, SocketCAN); bridge thread replaced by can + heat threads (heater PID on the RV1106); UART2 demoted to STM32 flashing/debug; §3 rewritten, STM32 stack and decision table updated |
| 1.6 | 2026-11-04 | Manas Pradhan | STM32G474RE replaced by STM32G0B1RE (Cortex-M0+ @ 64 MHz, 2x FDCAN): §4.1 and the decision table updated with the RP2040 comparison |
| 1.5 | 2026-11-04 | Manas Pradhan | Heater PID removed from Epicura (module-internal control, heat thread = 2 Hz setpoint keep-alive); FDCAN2 added for the CAN servo stirring motor; HAL table corrected (no IR thermometer / thermocouple); decisions for motor interface, temperature control and 2S battery backup added |
| 1.7 | 2026-11-04 | Manas Pradhan | Three-unit architecture: RV1106 on the Unified PCB v4.0 in the Dispensing Unit (battery primary) gains the `dispense` thread, I2C3 peripheral drivers (`pwm-pca9685`, `gpio-pcf857x`, `ina2xx`, `i2c-mux-pca954x`, `nau7802`), LED ring / buzzer PWM and dock monitoring (new §2.8); STM32 moves to the Cooking Surface Controller with 4 tasks and a trimmed peripheral table (DOCK_SENSE_B, Q_DOCK, Q_STIR GPIO; no HX711 / I2C / WS2812B / battery ADC); CAN bus crosses the dock, service UART replaced by the CAN bootloader (0x7E0/0x7E8, USB DFU bench fallback); decision table row for the dispensing-unit battery |
| 1.8 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); same CAN contract, no controller change — §1 table, §3 heading/diagram and the temperature-control decision reworded |
| 1.9 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: second STM32G0B1RE on the Unified PCB v5.0 as the DU's CAN node and transparent gateway for the RV1106 over a UART host link (UART2 ↔ USART1, 921,600 baud, COBS/CRC-16, CAN-shaped frames); MCP2518FD / SocketCAN and the RV1106-side I2C3 / PWM / GPIO peripheral drivers removed; `can` thread → `link` thread; §2.2, §2.5, §2.6, §2.8 (drivers now in the DU STM32 firmware), §3 (host link + gateway), §4.1/4.2 (two images from one tree, DU task set), §6, §7.2 (DU STM32 flashed via the ST system bootloader) and the decision table updated |
| 2.0 | 2026-11-04 | Manas Pradhan | Stirring Unit on its own PSU (CSC v1.3): FDCAN2 row and GPIO row of the STM32 peripheral table (second isolated port on ISO1050DUB #3, K_SU on PB4 instead of Q_STIR), boards row (two LRS-75-24 in the CS base) and the Stirring Motor Interface decision (isolated port, floating GND_SU, AC pilot relay) updated |
| 2.1 | 2026-11-04 | Manas Pradhan | CAN isolation on the CSC only: DU STM32 node is a non-isolated SN65HVD230 (ISO1050DUB #2 and dock 5V_ISO feed removed, Unified PCB v5.1); §3 diagram and transport row, §4.1 recommendation wording, Inter-Processor Comm decision rationale ("5 kV isolation" → isolated at the CSC port) |
| 2.2 | 2026-11-05 | Manas Pradhan | CSC on its own PSU (CSC v1.6): boards row — the CSC sits beside three Mean Well PSUs (a dedicated LRS-35-12 on J_12V_IN for the board, relay coils and fans; LRS-75-24 #1 for the DU, #2 for the SU) instead of "the two LRS-75-24"; nothing is tapped from the heating unit |
| 2.3 | 2026-11-05 | Manas Pradhan | Robot-mop SLD: §2.8 SLD row (open-loop tach metering, SLD_PRIME / QUERY_SLD / SLD_CAL, no solenoids or NAU7802), host-loss row, DU STM32 diagram and FreeRTOS task bullet updated |
