---
created: 2026-02-15
modified: 2026-11-04
version: 1.1
status: Draft
---

# Tech Stack

## 1. Architecture Overview

Epicura uses a dual-processor architecture with clearly separated responsibilities. The RV1106 handles high-level application logic and AI, while the STM32G4 manages real-time control and safety-critical operations.

| Layer | RV1106 (Application) | STM32G4 (Real-Time) |
|-------|----------------------|---------------------|
| **Hardware** | Rockchip RV1106G3 (Luckfox Pico Zero), 1x Cortex-A7 @ 1.2 GHz, 256 MB DDR3L, 8 GB eMMC, 1 TOPS NPU, 5 MP ISP | STM32G474RE, Cortex-M4F @ 170 MHz, 512 KB Flash, 128 KB SRAM |
| **OS** | Buildroot Linux (Luckfox SDK, kernel 5.10), busybox init | FreeRTOS 10.x |
| **UI Framework** | LVGL 9 (C, software rendered) on 4" 480x320 SPI LCD | None |
| **AI/ML** | Hardware ISP + NPU via `rockit` / `rknn_api` (RKNN INT8) | None |
| **Application** | C11, single process `epicurad` (Recipe Engine, CV, UI, bridge, sync) | C (MISRA C subset) |
| **Communication** | UART bridge (1 Mbps), MQTT client, HTTPS client | UART/CAN driver |
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
| Camera | MIPI CSI-2 FPC (SC3336 3 MP, 2-lane) |
| Display | 4" 480x320 SPI LCD (ST7796S) + FT6336 I2C touch |
| Connectivity | Wi-Fi 6 (2.4 GHz), Bluetooth 5.2 LE; no Ethernet |
| GPIO | 40-pin RPi-style header: 28x GPIO, UART, SPI, I2C, PWM (3.3 V) |
| Board | 65 x 30 mm, USB-C (power + flashing), no carrier board required |

### 2.2 Operating System & Process Architecture

**Buildroot Linux (Luckfox SDK, kernel 5.10):**
- Custom `br2-external` tree on the Luckfox SDK; no Yocto, no systemd, no container runtime
- Minimal image: kernel + busybox init + `epicurad`; read-only squashfs rootfs
- Device tree for MIPI CSI camera (SC3336), fbtft SPI LCD, I2C touch, UART2 bridge
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
│  │  │ bridge thread│ │ sync thread  │ │ SQLite 3     │  │  │
│  │  │ (UART2 1Mbps)│ │ (MQTT/HTTPS) │ │ (in-process) │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘  │  │
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
│  • Telemetry ring buffer (from bridge thread)           │
│  • SQLite queries for recipe browser (FTS5)             │
├─────────────────────────────────────────────────────────┤
│   /dev/fb0 via fbtft (ST7796S, SPI0 50 MHz, DMA)         │
│   Buildroot Linux                                        │
└─────────────────────────────────────────────────────────┘
```

### 2.4 AI/ML Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Image Capture | `rockit` VI/ISP (hardware) | SC3336 → ISP main path 1280x720 NV12 @ 30 fps |
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
  - Telemetry ring buffer from the bridge thread for real-time state
  - Command queue to the bridge thread for STM32 commands

### 2.6 Cloud & Networking

| Service | Library / Protocol | Purpose |
|---------|--------------------|---------|
| Telemetry | libmosquitto (MQTT client, TLS, QoS 1) | Direct connection to cloud broker (AWS IoT Core); no local broker |
| Recipe Sync | libcurl + mbedTLS, REST client | `GET /recipes/sync?since=` pull; `sync_outbox` POST push; works offline |
| OTA Updates | swupdate | A/B boot + rootfs slot updates, signed `.swu` |
| Backend API | Fastify (Node.js/TypeScript) — cloud only | REST API for mobile app and device sync; the device is a REST + MQTT client, not a server |
| Live Camera | On-demand H.264 RTSP (`rtsp-stream`, :554 `/pot`) | Stream cooking video to mobile app on request (same LAN direct, else cloud relay) |
| RV1106-STM32 Bridge | bridge thread of `epicurad` (C, `SCHED_FIFO`) | UART framing, CRC, heartbeat, telemetry buffering |

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

### 2.8 RV1106 Development Tools

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

## 3. RV1106-STM32 Bridge

The bridge is a real-time thread inside `epicurad` and handles all communication between the RV1106 application threads and the STM32 real-time controller.

### 3.1 Bridge Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  epicurad (RV1106, single process)          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Recipe Engine│ │  LVGL UI     │ │  Cloud Sync  │        │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│         command queue / telemetry ring buffer               │
│                          │                                  │
│         ┌────────────────▼────────────────┐                 │
│         │   bridge thread (SCHED_FIFO)    │                 │
│         │                                 │                 │
│         │  • UART frame codec (SOF/stuff) │                 │
│         │  • CRC-16/CCITT                 │                 │
│         │  • ACK / retry (500 ms x 3)     │                 │
│         │  • Telemetry buffering (20 Hz)  │                 │
│         │  • Watchdog heartbeat (2 s)     │                 │
│         └────────────┬────────────────────┘                 │
│                      │                                      │
│            UART2 1 Mbps (pins 8/10)                         │
│                      │                                      │
└──────────────────────┼──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   STM32G474RE                               │
│          (FreeRTOS Controller, USART2 PA2/PA3)              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Bridge Features

| Feature | Implementation |
|---------|----------------|
| **Protocol** | SOF 0x7E, byte-stuffing (0x7D escape), then MSG_ID, TYPE, LENGTH, PAYLOAD (≤64), CRC-16/CCITT |
| **Transport** | UART2 ↔ USART2, 1,000,000 baud, 8N1, 3.3 V (CAN 500 kbps as production alternative) |
| **Message Queue** | In-process command queue (pthread mutex + condvar) |
| **Telemetry Buffer** | Lock-free ring buffer; 20 Hz unsolicited TELEMETRY; SQLite checkpoint every 10 s |
| **Health Monitoring** | Heartbeat every 2 s, STM32 IWDG 5 s; alerts if STM32 unresponsive |
| **API** | C API: `bridge_send()`, `bridge_poll_telemetry()`, `bridge_status()` |
| **Logging** | syslog (busybox) / stderr |

### 3.3 Bridge Stack

```c
/* epicurad bridge thread — no external dependencies */
├── termios (raw mode, 1 Mbps, VMIN=1)      /* UART2 /dev/ttyS2 */
├── frame_codec.c (SOF / byte-stuffing)
├── crc16_ccitt.c (lookup table)
├── pthread (SCHED_FIFO bridge thread)
├── ring buffer (telemetry → engine / ui / sync)
└── stm32_bootloader.c (BOOT0/NRST GPIO + ST USART bootloader protocol for firmware updates)
```

---

## 4. STM32 Software Stack

### 4.1 Hardware Platform

#### 4.1.1 Primary Choice: STM32G474RE

| Specification | Value |
|--------------|-------|
| Core | ARM Cortex-M4F @ 170 MHz |
| Flash | 512 KB |
| SRAM | 128 KB |
| FPU | Single-precision hardware FPU |
| ADC | 5x 12-bit ADC (up to 4 Msps) |
| Timers | Advanced PWM timers (HRTIM for induction) |
| Comm | 3x UART, 3x SPI, 4x I2C, FDCAN |
| Package | LQFP-64 or LQFP-100 |

#### 4.1.2 Alternative: STM32F446RE

| Specification | Value |
|--------------|-------|
| Core | ARM Cortex-M4F @ 180 MHz |
| Flash | 512 KB |
| SRAM | 128 KB |
| FPU | Single-precision hardware FPU |
| ADC | 3x 12-bit ADC |
| Timers | Standard PWM timers |
| Comm | 4x UART, 4x SPI, 3x I2C, 2x CAN |
| Package | LQFP-64 |

**Recommendation:** STM32G474RE preferred for its FDCAN peripheral (required for CAN bus communication with the microwave induction surface module) and HRTIM for precise servo PWM control.

### 4.2 RTOS

**FreeRTOS 10.x:**
- 4-5 concurrent tasks (PID, Motor, Sensor, Safety, Communication)
- Priority-based preemptive scheduling
- Memory: heap_4 allocator (128 KB SRAM budget)
- Tick rate: 1 kHz (1 ms resolution)
- Stack monitoring enabled for overflow detection

### 4.3 Language & Standards

- **Language:** C11 (MISRA C:2012 subset for safety-critical paths)
- **Math:** CMSIS-DSP library for PID computation and signal filtering
- **Coding standard:** MISRA C mandatory for safety monitor and motor control tasks

### 4.4 HAL & Drivers

| Peripheral | Driver | Usage |
|------------|--------|-------|
| PWM (TIM/HRTIM) | STM32 HAL TIM | Motor control (BLDC, SG90 servos) |
| ADC | STM32 HAL ADC + DMA | Temperature sensors, current sensing |
| SPI | STM32 HAL SPI | Thermocouple interface (MAX31855) |
| I2C | STM32 HAL I2C | Load cells (HX711), IR thermometer |
| USART | STM32 HAL UART + DMA | Bridge to RV1106 (USART2 PA2/PA3, 1 Mbps, SOF-framed) |
| TIM15 + DMA | STM32 HAL TIM PWM DMA | WS2812B LED ring (PB14, 800 kHz, via 74AHCT1G125) |
| FDCAN | STM32 HAL FDCAN | CAN bus to microwave induction surface (primary heater control) |
| GPIO | STM32 HAL GPIO | Limit switches, ASD servos, CID actuators, SLD solenoids, buzzer |
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
| HIL on Luckfox Pico Zero | C | ISP/NPU pipeline, UART bridge, LCD, Wi-Fi |

### 6.2 STM32 Testing

| Framework | Language | Scope |
|-----------|---------|-------|
| Unity test framework | C | PID controller, protocol parser, safety logic |
| CMock | C | Mock HAL functions for unit testing |
| Ceedling | C | Build system for Unity + CMock |

### 6.3 Integration & System Testing

| Method | Purpose |
|--------|---------|
| Hardware-in-Loop (HIL) | STM32 + real sensors, RV1106 + camera, end-to-end |
| UART loopback | Protocol testing without full hardware |
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

- **Mechanism:** System bootloader (STM32 built-in USART bootloader on USART2)
- **Trigger:** RV1106 drives STM32 BOOT0 (header pin 32) high and pulses NRST (header pin 38)
- **Delivery:** RV1106 downloads .bin, streams to STM32 over the bridge UART (ST USART bootloader protocol)
- **Verification:** CRC check after flashing
- **Rollback:** Dual-bank flash (if available) or re-flash previous version

---

## 8. Development Timeline

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| **Environment Setup** | 2 weeks | Luckfox SDK Buildroot `br2-external` for RV1106, STM32CubeIDE project, toolchain validation |
| **Hardware Bring-up** | 4 weeks | RV1106 boot + SPI LCD + touch, STM32 peripherals (PWM, ADC, UART), SC3336 camera test |
| **Core Firmware** | 6 weeks | FreeRTOS tasks, PID controller, motor control, safety monitor, protocol |
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
| STM32 RTOS | FreeRTOS | Bare metal | FreeRTOS provides task isolation, priority scheduling, and watchdog integration needed for concurrent PID + safety + comms |
| Inter-Processor Comm | UART 1 Mbps (primary) | SPI, CAN bus | Pico Zero's single SPI controller goes to the LCD; UART needs no data-ready line, doubles as the STM32 bootloader link; CAN kept as production alternative, also used for microwave surface control |
| STM32 Variant | STM32G474RE | STM32F446RE | G474 has FDCAN for microwave surface CAN bus and HRTIM; F446 viable but lacks FDCAN |
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
