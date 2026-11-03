---
created: 2026-02-15
modified: 2026-11-04
version: 3.0
status: Draft
---

# Controller & Software Architecture

## 1. Architecture Overview

Epicura uses a dual-processor architecture: a Rockchip RV1106G3 (Luckfox Pico Zero) running Buildroot Linux for AI vision, UI, and cloud connectivity, paired with an STM32G4 microcontroller running FreeRTOS for real-time motor control, dispensing, sensor acquisition and safety monitoring. The two processors and the induction surface's own MCU share one isolated CAN bus; the RV1106 closes the temperature loop and commands the heater directly, the STM32 keeps an independent off-switch.

The RV1106 is a 256 MB, single-core, GPU-less vision SoC. The application side is therefore a single native C application on a minimal Buildroot image, not a container stack. Heavy image work is pushed into the chip's hardware blocks (ISP, NPU, RGA, H.264 encoder) and the CPU is left with UI, recipe logic, storage and comms. See [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]] for the rationale and the CM5 comparison.

| Aspect | RV1106 (Application) | STM32G4 (Real-Time) |
|--------|----------------------|---------------------|
| **Processor** | Rockchip RV1106G3, 1x Cortex-A7 (32-bit, NEON, FPU) | STM32G474RE, Cortex-M4F |
| **Clock** | 1.2 GHz | 170 MHz |
| **Memory** | 256 MB DDR3L (in-package), 8 GB eMMC | 128 KB SRAM, 512 KB Flash |
| **Accelerators** | 1 TOPS NPU, 5 MP ISP, RGA 2D, H.264/H.265 encoder | FPU, CMSIS-DSP |
| **OS** | Buildroot Linux (Luckfox SDK, kernel 5.10) | FreeRTOS 10.x |
| **Role** | AI/Vision, UI, Recipe Engine, Heater setpoints, Storage, Cloud | Stir motor (CAN), Dispensers, Sensors, Safety |
| **Languages** | C11 (single application), LVGL | C (MISRA C subset) |
| **Graphics** | LVGL 9 on 4" 480x320 SPI LCD, software rendering | None |
| **IPC** | Isolated CAN 2.0B 500 kbps via MCP2518FD on SPI0 CS1 (SocketCAN `can0`); UART2 only for STM32 flashing/debug | FDCAN1 on the same bus (host commands, telemetry, heater off-switch); FDCAN2 = regular 1 Mbps bus to the stirring motor; USART2 = service link only |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Luckfox Pico Zero / RV1106G3 (Buildroot Linux)            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              epicurad  (single C process, pthreads)                 │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────┐ ┌──────────────┐    │    │
│  │  │ Recipe Engine │ │ CV Pipeline  │ │   UI   │ │  Cloud Sync  │    │    │
│  │  │ (State Mach.) │ │ (ISP → NPU)  │ │ (LVGL) │ │ (MQTT/HTTPS) │    │    │
│  │  └──────────────┘ └──────────────┘ └────────┘ └──────────────┘    │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                      Library Layer                                  │    │
│  │  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐ │    │
│  │  │  SQLite  │ │ libmosquitto│ │ rockit   │ │ rknn_api│ │SocketCAN│ │    │
│  │  │  (WAL)   │ │ libcurl/TLS │ │ (VI/ISP/ │ │ (NPU)   │ │  can0   │ │    │
│  │  │          │ │            │ │  VENC)   │ │         │ │         │ │    │
│  │  └──────────┘ └────────────┘ └──────────┘ └─────────┘ └────┬────┘ │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │            Buildroot Linux 5.10 (busybox init, fbtft, wpa)          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  Hardware: RV1106G3, Cortex-A7 @ 1.2 GHz, 256 MB, NPU, ISP, VENC    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  On-demand only:  rtsp-stream (child process, H.264 720p → phone)           │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                      CAN 2.0B 500 kbps (isolated bus, shared with the induction surface)
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                       STM32G474RE (FreeRTOS)                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      FreeRTOS Tasks                                  │    │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │    │
│  │  │ CAN Comms   │ │ Motor Control│ │Sensor Polling│ │   Safety   │ │    │
│  │  │  (20 Hz)    │ │  (50 Hz)     │ │  (10 Hz)     │ │  Monitor   │ │    │
│  │  └─────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                      HAL / Driver Layer                              │    │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐  │    │
│  │  │ PWM  │  │ ADC  │  │ SPI  │  │ I2C  │  │ GPIO │  │ CAN/UART │  │    │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────────┘  │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │           Hardware: STM32G474RE, Cortex-M4F @ 170 MHz               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Distribution

| Module | Processor | Rationale |
|--------|-----------|-----------|
| Recipe Engine (State Machine) | RV1106 | Complex logic, YAML parsing, file I/O |
| Computer Vision Pipeline | RV1106 | Hardware ISP + 1 TOPS NPU; no CPU image processing |
| LVGL User Interface | RV1106 | Software-rendered 480x320, SPI LCD, I2C touch |
| Cloud Sync (MQTT/HTTPS) | RV1106 | Full Linux networking stack, Wi-Fi 6 |
| SQLite Database | RV1106 | Embedded, in-process, WAL mode on eMMC |
| On-demand phone video stream | RV1106 | Hardware H.264 encoder, RTSP over Wi-Fi |
| OTA Firmware Updates | RV1106 | Network + A/B eMMC partitions |
| Heater setpoints | RV1106 | `heat` thread (SCHED_FIFO) re-sends HEAT_SET_TEMP / HEAT_SET_POWER at 2 Hz and reads HEAT_STATUS; the induction module runs its own PID on its own sensor — no temperature loop in Epicura |
| Stir Motor Control | STM32 | CAN servo on FDCAN2: velocity/position commands at 50 Hz, encoder feedback |
| Sensor Polling (Temp/Weight) | STM32 | ADC sampling, I2C/SPI peripherals |
| Safety Monitor / Watchdog | STM32 | Independent safety, E-stop authority |
| Ingredient Dispensing | STM32 | Servo actuation, load cell feedback |
| Heater interlock | STM32 | Listens to HEAT_STATUS on the bus; forces HEAT_ON_OFF = 0, broadcasts E_STOP and opens the relay on faults; never sends power levels |
| LED Ring (WS2812B) | STM32 | 5 V logic, 800 kHz bit timing from timer + DMA; RV1106 only requests modes |

---

## 4. Software Stack

### 4.1 RV1106 Native Stack

There is no container runtime, no database server, no message broker and no interpreter on the device. One supervised process, `epicurad`, owns every function. A second process, `rtsp-stream`, is spawned only while a phone is viewing the pot.

```
┌─────────────────────────────────────────────────────────────┐
│          Buildroot Linux (Luckfox SDK, kernel 5.10)         │
│     Hardware: RV1106G3 (1x Cortex-A7 @ 1.2 GHz)             │
│     RAM: 256 MB DDR3L  |  Storage: 8 GB eMMC                │
│     Init: busybox init + /etc/init.d  |  Watchdog: /dev/watchdog │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│   epicurad  (C11, pthreads, one process, ~10 MB RSS)        │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ui thread (LVGL 9)                                    │ │
│  │  • Cooking dashboard • Recipe browser • Settings       │ │
│  │  • Optional pot preview (ISP self-path → RGA → fb)     │ │
│  │  • /dev/fb0 via fbtft (ST7796S, SPI0, 50 MHz, DMA)     │ │
│  │  • Touch: FT6336 on I2C3, evdev                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  engine thread                                         │ │
│  │  • YAML recipe parsing (libyaml) and validation        │ │
│  │  • Cooking state machine, 1 Hz tick                    │ │
│  │  • Writes session state to SQLite every 10 s           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  cv thread                                             │ │
│  │  • rockit VI/ISP: sensor → 1280x720 main path          │ │
│  │  • ISP self-path scaled to 224x224 for inference       │ │
│  │  • rknn_api: MobileNetV2 INT8 on NPU, 2 Hz             │ │
│  │  • 3-frame majority vote → stage + confidence          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  can thread                                            │ │
│  │  • SocketCAN can0 (MCP2518FD on SPI0 CS1), 500 kbps    │ │
│  │  • Heartbeat 2 s, ACK/retry, telemetry ring buffer     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  heat thread                                           │ │
│  │  • 2 Hz HEAT_SET_TEMP / HEAT_SET_POWER keep-alive      │ │
│  │  • HEAT_STATUS surface_temp → engine (module runs PID) │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  sync thread                                           │ │
│  │  • libmosquitto → cloud MQTT broker (TLS, QoS 1)       │ │
│  │  • libcurl + mbedTLS → cloud REST API                  │ │
│  │  • Outbox table in SQLite; retries when offline        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  SQLite 3 (in-process, WAL, JSON1, FTS5)               │ │
│  │  • /data/epicura.db on dedicated eMMC partition        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│   rtsp-stream  (child process, ON DEMAND ONLY)              │
│   • Started by epicurad when a phone requests live view     │
│   • VENC H.264 1280x720 @ 15 fps, 1.5 Mbps, bound to VI     │
│   • RTSP server on :554, single client                      │
│   • Killed after 60 s with no client; frees VENC buffers    │
└─────────────────────────────────────────────────────────────┘
```

**Buildroot package set (beyond the Luckfox base):** `sqlite`, `libyaml`, `cjson`, `libmosquitto`, `libcurl`, `mbedtls`, `lvgl`, `swupdate`, `wpa_supplicant`, `bluez5` (BLE provisioning), `rockit` + `rknn` runtime from the Luckfox SDK, `iproute2` (brings up `can0`); kernel `mcp251xfd` SocketCAN driver. Not included: Python, OpenCV, Docker, PostgreSQL, Node.js, Redis, Mosquitto broker, Kivy, GStreamer.

### 4.2 Memory Budget

256 MB total. Figures are design targets to be verified on hardware; the CMA reservation is set in the device tree.

| Component | Budget | Notes |
|-----------|--------|-------|
| Kernel + Buildroot base (busybox, udev, wpa_supplicant, bluez) | 30 MB | No desktop, no systemd |
| CMA: VI + ISP at 1280x720 | 16 MB | 4x NV12 720p buffers (1.4 MB each) + ISP internal |
| CMA: ISP self-path 224x224 + RGA scratch | 2 MB | Inference and LCD preview |
| CMA: VENC 720p (on demand only) | 8 MB | Allocated only while `rtsp-stream` runs |
| NPU runtime + MobileNetV2 INT8 (~3.5 MB model) | 15 MB | `rknn_api`, weights, intermediate tensors |
| `epicurad` application | 10 MB | LVGL double buffer 480x320 RGB565 (0.6 MB), fonts, SQLite cache (2 MB), TLS, heap |
| Wi-Fi + BT driver and firmware | 8 MB | |
| `rtsp-stream` process (on demand) | 4 MB | |
| **Steady state (no streaming)** | **~80 MB** | ~175 MB free |
| **Peak (streaming + inference + UI)** | **~95 MB** | ~160 MB free |

Design rules that keep this true:
- Sensor runs at 1280x720, not 1080p. Halves VI buffer memory and encoder load; 720p is more than sufficient for a 224x224 classifier and for a phone preview.
- Phone streaming is on demand. The encoder channel and RTSP server exist only while a client is connected.
- No OpenCV. Dehaze, noise reduction, white balance and sharpening run in the ISP; resize runs in the ISP self-path or RGA.
- No local broker, no local REST server. The phone talks to the cloud, or to the device over BLE for provisioning.

### 4.3 Peripheral Bus Allocation (Luckfox Pico Zero header)

The Pico Zero exposes one full SPI controller with two chip selects: CS0 drives the display, CS1 drives the MCP2518FD CAN controller that puts the RV1106 on the isolated CAN bus shared with the STM32 and the induction surface. UART2 stays wired to the STM32 only as a service link (firmware flashing, debug).

| Function | Bus | Header pins | Notes |
|----------|-----|-------------|-------|
| 4" LCD (ST7796S, 480x320) | SPI0 M0: MOSI 19, MISO 21, CLK 23, CS0 24 | + DC GPIO 22, RST GPIO 26, backlight PWM10 pin 12 | fbtft, 50 MHz, DMA. ~50 ms full frame; LVGL partial redraws |
| Touch (FT6336) | I2C3 M0: SDA 16, SCL 18 | INT GPIO 36 | evdev |
| CAN bus (STM32 + induction surface) | SPI0 M0 CS1 (GPIO 58) + INT GPIO | MCP2518FD + ISO1050DUB #2 on the Unified PCB (isolated port J_CAN_HEAT) | SocketCAN `can0`, 500 kbps; shares MOSI/MISO/CLK with the LCD, ≤ 20 MHz. The stirring motor is on the STM32's separate FDCAN2 bus, not reachable from the RV1106 |
| STM32 service UART | UART2 M1: TX 8, RX 10 | | ST system-bootloader flashing + debug only; no runtime traffic |
| STM32 BOOT0 / NRST (OTA) | GPIO 32, GPIO 38 | | Enter system bootloader for firmware load |
| LED ring (WS2812B) | **On STM32**, not on this header | | STM32 timer + DMA, 5 V logic; RV1106 sends SET_LED over CAN |
| Debug console | UART0 M0: TX 35, RX 37 | | Luckfox default |
| Camera | MIPI CSI FPC (4-lane) | | **IMX415-98 IR-CUT 8 MP** (the colour camera Luckfox supports on the Pico Zero; ISP tuning file shipped in SDK; 22-pin FPC). SC3336 is marked incompatible with the Pico Zero; IMX219/IMX477 dropped: no RV1106 tuning file |
| Wi-Fi / BLE | On-board module | | 2.4 GHz Wi-Fi 6, BT 5.2 |
| Spare | UART3, UART4, I2C1, I2C2, PWM | | |

### 4.4 STM32 FreeRTOS Stack

```
┌─────────────────────────────────────────────────────────┐
│              FreeRTOS Application Tasks                   │
│  • CAN Comms           • Motor Control                   │
│  • Sensor Polling      • Safety Monitor                  │
│  • Heater Interlock    • Dispensing                      │
├─────────────────────────────────────────────────────────┤
│                      FreeRTOS 10.x                       │
│  • Priority-based preemptive scheduling                  │
│  • Queues, Semaphores, Timers, Event Groups              │
│  • Memory management (heap_4)                            │
├─────────────────────────────────────────────────────────┤
│                   HAL / CMSIS Layer                       │
│  • STM32 HAL drivers (PWM, ADC, FDCAN, I2C, UART)       │
│  • CMSIS-DSP (signal filtering)                          │
│  • CMSIS-RTOS2 abstraction                               │
├─────────────────────────────────────────────────────────┤
│     Hardware: STM32G474RE (Cortex-M4F @ 170 MHz)         │
│     Flash: 512 KB  |  SRAM: 128 KB                       │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Core Modules

### 5.1 Recipe Engine (RV1106)

#### 5.1.1 State Machine Design

Each recipe is modeled as a finite state machine. The Recipe Engine loads a YAML recipe definition, then drives the cooking process by transitioning between stages based on CV analysis, temperature readings, and timer events.

> [!tip] Detailed State Machine
> See [[03-Main-Loop-State-Machine|Main Loop State Machine]] for the full state diagram with Mermaid visualizations, state-layer impact matrix, sequence diagrams, and transition trigger tables.

**Recipe States:**

```
                    ┌──────────────────────────────────────────────┐
                    │                                              │
                    ▼                                              │
┌──────┐    ┌──────────┐    ┌───────────────┐    ┌──────┐        │
│ IDLE │───►│ PREHEAT  │───►│ADD_INGREDIENT │───►│ COOK │        │
└──────┘    └──────────┘    └───────────────┘    └──┬───┘        │
   ▲                                                │             │
   │        ┌──────────┐    ┌──────────┐            ▼             │
   │        │ COMPLETE │◄───│ MONITOR  │◄───────┌──────┐         │
   │        └──────────┘    └────┬─────┘        │ STIR │         │
   │                             │              └──────┘         │
   │                             ▼                                │
   │                        ┌──────────┐                          │
   │                        │  ADJUST  │──────────────────────────┘
   │                        └──────────┘
   │
   │        ┌──────────┐
   └────────│  ERROR   │◄─── (from any state)
            └──────────┘
```

#### 5.1.2 Recipe Format (YAML)

The YAML format is unchanged. It is parsed on-device with libyaml into a fixed-size C struct tree (no dynamic schema), validated, and cached in SQLite as JSON.

```yaml
recipe:
  name: "Dal Tadka"
  servings: 4
  total_time_minutes: 35
  stages:
    - name: "Heat Oil"
      temp_target: 180
      duration_seconds: 120
      stir: false
      ingredients: [{subsystem: "SLD", channel: "OIL", name: "oil", amount_g: 30}]
      cv_check: "oil_shimmer"
    - name: "Add Spices to Oil"
      temp_target: 160
      ingredients:
        - {subsystem: "FID", box: 1, name: "turmeric", qty_quarter_tsp: 4}
        - {subsystem: "FID", box: 2, name: "chili_powder", qty_quarter_tsp: 8}
      cv_check: "spice_bloom"
      stir: true
      stir_pattern: "intermittent"
    - name: "Add Onions & Tomatoes"
      temp_target: 150
      duration_seconds: 300
      ingredients: [{subsystem: "CID", slot: 1, name: "onion_tomato"}]
      cv_check: "golden_brown"
      stir: true
      stir_pattern: "continuous"
    - name: "Season"
      temp_target: 140
      duration_seconds: 60
      ingredients:
        - {subsystem: "FID", box: 4, name: "salt", qty_quarter_tsp: 3}
        - {subsystem: "FID", box: 5, name: "garam_masala", qty_quarter_tsp: 5}
      stir: true
      stir_pattern: "fold"
    - name: "Add Dal & Water"
      temp_target: 95
      ingredients:
        - {subsystem: "CID", slot: 2, name: "toor_dal"}
        - {subsystem: "SLD", channel: "WATER", name: "water", amount_g: 400}
    - name: "Simmer Dal"
      temp_target: 95
      duration_seconds: 900
      cv_check: "thick_consistency"
      stir: true
      stir_pattern: "intermittent"
```

#### 5.1.3 Key Functions

```c
/* recipe_engine.h */
typedef struct recipe   recipe_t;     /* parsed, validated recipe tree  */
typedef struct stage    stage_t;      /* one cooking stage              */

int  recipe_load(const char *yaml_path, recipe_t *out);
/* Parse YAML with libyaml and validate against the schema. */

int  engine_execute_stage(engine_t *e, const stage_t *s);
/* Run a single cooking stage: set temp, dispense, stir, monitor. */

bool engine_check_transition(const stage_t *s, const cv_result_t *cv,
                             const telemetry_t *t);
/* Evaluate whether the current stage is complete and ready to advance. */

error_action_t engine_handle_error(engine_t *e, cooking_error_t err);
/* Determine recovery action: retry, skip, pause, or abort. */
```

---

### 5.2 CV Pipeline (RV1106)

#### 5.2.1 Pipeline Architecture

Every stage before inference is a hardware block. The CPU touches only the 8-class output vector.

```
┌────────────┐   ┌─────────────────────┐   ┌───────────────┐   ┌────────────────┐
│  IMX415-98 │   │  ISP (hardware)     │   │  ISP self-path│   │   NPU (RKNN)   │
│  MIPI CSI  │──►│  3A, 3DNR, dehaze,  │──►│  scale to     │──►│  MobileNetV2   │
│  1280x720  │   │  LSC, sharpen       │   │  224x224 RGB  │   │  INT8, ~8 ms   │
│  @ 30 fps  │   │  main path 720p NV12│   │  @ 2 fps      │   │                │
└────────────┘   └──────────┬──────────┘   └───────────────┘   └───────┬────────┘
                            │                                           │
                 on demand  ▼                                           ▼
                 ┌──────────────────┐                          ┌──────────────┐
                 │ VENC H.264 720p  │                          │ Dequantize,  │
                 │ 15 fps → RTSP    │                          │ argmax, 3-   │
                 │ (phone live view)│                          │ frame vote   │
                 └──────────────────┘                          │ conf < 0.6 → │
                                                               │ timer + temp │
                                                               │ fallback     │
                                                               └──────────────┘
```

#### 5.2.2 Pipeline Implementation

```c
/* cv_pipeline.c  —  rockit MPI + rknn_api, runs in the cv thread */

int cv_init(cv_ctx_t *cv)
{
    /* Sensor → VI → ISP.  Main path 1280x720 NV12 (for preview/stream),
     * self path 224x224 RGB888 (for inference). Both paths are hardware. */
    vi_open(&cv->vi, SENSOR_IMX415, 1280, 720, 30);
    isp_set_output(&cv->vi, ISP_PATH_MAIN, 1280, 720, PIX_NV12);
    isp_set_output(&cv->vi, ISP_PATH_SELF,  224, 224, PIX_RGB888);
    isp_enable(&cv->vi, ISP_DEHAZE | ISP_3DNR | ISP_SHARPEN);

    /* Load INT8 .rknn (converted offline with rknn-toolkit2 from TFLite). */
    rknn_init(&cv->rknn, "/oem/models/stage_mnv2_int8.rknn", 0, 0, NULL);
    cv->confidence_threshold = 0.6f;
    return 0;
}

cv_result_t cv_classify_stage(cv_ctx_t *cv)
{
    /* Zero-copy: self-path frame is already 224x224 RGB in a DMA buffer. */
    frame_t f = isp_get_frame(&cv->vi, ISP_PATH_SELF, /*timeout_ms*/ 100);

    rknn_input in = { .index = 0, .buf = f.vaddr, .size = 224*224*3,
                      .pass_through = 1 };            /* INT8, no CPU normalize */
    rknn_inputs_set(cv->rknn, 1, &in);
    rknn_run(cv->rknn, NULL);                         /* ~5–10 ms on NPU */

    rknn_output out = { .want_float = 1 };
    rknn_outputs_get(cv->rknn, 1, &out, NULL);
    isp_release_frame(&cv->vi, &f);

    int   cls  = argmax_f32(out.buf, N_CLASSES);
    float conf = ((float *)out.buf)[cls];
    rknn_outputs_release(cv->rknn, 1, &out);

    vote_push(&cv->vote, cls, conf);                  /* 3-frame majority */
    if (vote_confidence(&cv->vote) < cv->confidence_threshold)
        return (cv_result_t){ .stage = STAGE_UNKNOWN, .conf = conf, .fallback = true };
    return (cv_result_t){ .stage = vote_class(&cv->vote), .conf = conf, .fallback = false };
}

/* Phone live view, on demand. Called from the sync thread when the cloud
 * relays a "live_view" request; torn down after 60 s without a client. */
int stream_start(cv_ctx_t *cv)
{
    venc_bind(&cv->venc, &cv->vi, ISP_PATH_MAIN, CODEC_H264,
              1280, 720, /*fps*/ 15, /*kbps*/ 1500);
    return spawn("/usr/bin/rtsp-stream", "--venc", "0", "--port", "554");
}
```

**Model Specifications:**

| Parameter | Value |
|-----------|-------|
| Architecture | MobileNetV2 (transfer learning from ImageNet) |
| Input Size | 224 x 224 x 3, INT8 pass-through from ISP |
| Quantization | INT8 (post-training, RKNN-Toolkit2 with calibration set) |
| Inference Time | 5-10 ms on RV1106G3 NPU (target < 20 ms) |
| Inference Rate | 2 Hz |
| Classes | ~15 cooking stages |
| Fallback | Timer + temperature thresholds if confidence < 0.6 |
| Model File | `/oem/models/stage_mnv2_int8.rknn`, ~3.5 MB |

**Camera path configuration:**

| Path | Resolution | Rate | Consumer | Always on? |
|------|-----------|------|----------|-----------|
| ISP main | 1280x720 NV12 | 30 fps | VENC (phone stream), RGA (LCD preview) | Yes (buffers), consumers on demand |
| ISP self | 224x224 RGB888 | sampled at 2 fps | NPU inference | Yes during cooking |
| VENC 0 | 1280x720 H.264 | 15 fps, 1.5 Mbps | `rtsp-stream` to phone | **On demand only** |
| RGA → fb0 | 480x320 RGB565 | ≤ 10 fps | LCD "view pot" screen | On demand only |

---

### 5.3 Motor Control (STM32)

#### 5.3.1 Heater Setpoints (no PID in Epicura)

The temperature loop runs **inside the induction module** on its own under-glass sensor. The `heat` thread of `epicurad` only owns the setpoint: it sends HEAT_SET_TEMP (0x100: target, ramp, max power) or HEAT_SET_POWER (0x103) when the engine changes a stage, re-sends it at 2 Hz as the module's keep-alive, and publishes `surface_temp` from HEAT_STATUS (0x180) to the engine and UI. If no HEAT_STATUS arrives for 500 ms, or the module reports a fault, the thread sends HEAT_ON_OFF 0 and the engine pauses. The STM32 and the module keep their own independent over-temperature cut-offs.

```c
typedef struct {
    heat_mode_t mode;        /* HEAT_MODE_TEMP or HEAT_MODE_POWER */
    int16_t     target_dC;   /* temperature mode: 0.1 °C */
    uint8_t     ramp_C_s;    /* ≤ 5 °C/s */
    uint8_t     max_power;   /* 0–100 %, clamp for simmer stages */
    uint8_t     power_pct;   /* power mode */
} heat_setpoint_t;

/* heat thread, 2 Hz */
void heat_tick(heat_ctx_t *h)
{
    if (h->status_age_ms > 500 || h->status.fault_flags) {
        can_send_heat_on_off(0);
        engine_pause(PAUSE_INDUCTION_ERROR);
        return;
    }
    if (h->sp.mode == HEAT_MODE_TEMP)
        can_send_heat_set_temp(h->sp.target_dC, h->sp.ramp_C_s, h->sp.max_power);
    else
        can_send_heat_set_power(h->sp.power_pct, h->sp.ramp_C_s);
    telemetry_publish_surface_temp(h->status.surface_temp_dC);   /* engine, ui, sync */
}
```

#### 5.3.2 Stirring Patterns

| Pattern | Speed (RPM) | Behavior | Use Case |
|---------|-------------|----------|----------|
| Continuous | 60 | Constant rotation | Gravy, sauce reduction |
| Intermittent | 30 | 5s on / 10s off | Dal simmering, rice |
| Reverse | 45 | Alternating CW/CCW every 8s | Prevent sticking |
| Scrape | 15 | Slow rotation + edge-seeking path | Thick pastes, halwa |
| Fold | 20 | Gentle wide sweep, low torque | Mixing delicate ingredients |

---

### 5.4 Safety Monitor (STM32)

#### 5.4.1 Safety State Machine

```
┌─────────┐   temp > warn_thresh    ┌──────────┐   temp > crit_thresh   ┌───────────┐
│  NORMAL │────────────────────────►│ WARNING  │───────────────────────►│ CRITICAL  │
│         │   OR sensor_degraded    │          │   OR motor_stall       │           │
└─────────┘                         └──────────┘   OR comms_lost > 5s   └─────┬─────┘
     ▲                                   │                                     │
     │       conditions cleared          │                                     │
     └───────────────────────────────────┘                                     │
                                                                               ▼
                                                                         ┌──────────┐
                                                                         │  E_STOP  │
                                                                         │          │
                                                                         │ Cut heat │
                                                                         │ Stop arm │
                                                                         │ Alert UI │
                                                                         └──────────┘
```

**Transition Conditions:**

| From | To | Condition |
|------|----|-----------|
| NORMAL | WARNING | Temperature > warning threshold (e.g., setpoint + 20C) |
| NORMAL | WARNING | Single sensor reading out of range |
| WARNING | CRITICAL | Temperature > critical threshold (e.g., 260C) |
| WARNING | CRITICAL | Motor stall detected (overcurrent) |
| WARNING | CRITICAL | RV1106 heartbeat lost for > 5 seconds |
| CRITICAL | E_STOP | Any CRITICAL condition persists > 3 seconds |
| WARNING | NORMAL | All conditions return to safe range |
| E_STOP | NORMAL | Manual user reset only |

**Watchdog Timer:**
- RV1106 sends heartbeat every 2 seconds on the CAN bus (HB_AP, 0x010)
- STM32 independent watchdog (IWDG) timeout: 5 seconds
- If heartbeat missed: enter WARNING state
- If heartbeat missed > 5s: enter CRITICAL state, cut induction

**Emergency Actions (E_STOP):**
1. Immediately send HEAT_ON_OFF = 0 (0x101) to the induction surface, broadcast E_STOP (0x001), open the safety relay
2. Stop servo motor and engage brake
3. Send alert message to RV1106 UI (if comms available)
4. Activate buzzer alarm
5. Log event to non-volatile memory
6. Require manual user intervention to reset

---

### 5.5 Data Management (RV1106)

#### 5.5.1 SQLite Schema

The device uses SQLite 3 in WAL mode, in-process, on a dedicated `/data` partition of the eMMC. The schema mirrors the cloud PostgreSQL schema in [[../../10-Backend/02-Database-Schema|Database Schema]] table-for-table, with PostgreSQL-only types mapped as below so that sync is a straight row copy.

| PostgreSQL | SQLite | Notes |
|------------|--------|-------|
| `UUID` | `TEXT` (36-char) | Generated on device with a v4 UUID helper |
| `JSONB` | `TEXT` + JSON1 functions | `json_extract()` for queries, validated on insert |
| `TEXT[]` | `TEXT` JSON array | `json_each()` to filter |
| `TIMESTAMPTZ` | `TEXT` ISO-8601 UTC | Lexically sortable |
| `GIN` index | FTS5 virtual table | Recipe name/tag search |

**Key Tables:**

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;          -- durable across power loss with WAL
PRAGMA foreign_keys = ON;

-- Recipes (JSON text for the full recipe definition)
CREATE TABLE recipes (
    id            TEXT PRIMARY KEY,                    -- UUID from cloud
    name          TEXT NOT NULL,
    category      TEXT NOT NULL,
    cuisine       TEXT NOT NULL DEFAULT 'indian',
    recipe_data   TEXT NOT NULL CHECK (json_valid(recipe_data)),
    tags          TEXT NOT NULL DEFAULT '[]',           -- JSON array
    difficulty    TEXT NOT NULL,
    time_minutes  INTEGER NOT NULL,
    image_path    TEXT,                                -- local cache under /data/images
    version       INTEGER NOT NULL DEFAULT 1,
    is_published  INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

-- Cooking logs
CREATE TABLE cooking_sessions (
    id               TEXT PRIMARY KEY,                 -- UUID generated on device
    recipe_id        TEXT NOT NULL REFERENCES recipes(id),
    started_at       TEXT NOT NULL,
    completed_at     TEXT,
    stages_log       TEXT CHECK (stages_log IS NULL OR json_valid(stages_log)),
    status           TEXT NOT NULL DEFAULT 'started',
    peak_temperature REAL,
    total_duration_s INTEGER,
    user_rating      INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    notes            TEXT,
    synced           INTEGER NOT NULL DEFAULT 0
);

-- User preferences (single row)
CREATE TABLE user_preferences (
    id               INTEGER PRIMARY KEY CHECK (id = 1),
    language         TEXT NOT NULL DEFAULT 'en_IN',
    spice_level      INTEGER NOT NULL DEFAULT 3 CHECK (spice_level BETWEEN 1 AND 5),
    default_servings INTEGER NOT NULL DEFAULT 4,
    allergens        TEXT NOT NULL DEFAULT '[]',
    theme            TEXT NOT NULL DEFAULT 'light',
    last_sync_at     TEXT
);

-- Resume-after-power-loss checkpoint (overwritten every 10 s while cooking)
CREATE TABLE session_checkpoint (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    session_id  TEXT NOT NULL,
    stage_index INTEGER NOT NULL,
    stage_elapsed_s INTEGER NOT NULL,
    saved_at    TEXT NOT NULL
);

-- Outbox for cloud sync (survives offline periods)
CREATE TABLE sync_outbox (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,                         -- 'session' | 'preferences' | 'telemetry'
    payload     TEXT NOT NULL CHECK (json_valid(payload)),
    created_at  TEXT NOT NULL,
    attempts    INTEGER NOT NULL DEFAULT 0
);

-- Indexes and search
CREATE INDEX idx_recipes_category ON recipes(category);
CREATE INDEX idx_sessions_started ON cooking_sessions(started_at DESC);
CREATE INDEX idx_sessions_unsynced ON cooking_sessions(synced) WHERE synced = 0;
CREATE VIRTUAL TABLE recipes_fts USING fts5(name, tags, content='recipes', content_rowid='rowid');
```

#### 5.5.2 Storage Layout (8 GB eMMC)

| Partition | Size | Content |
|-----------|------|---------|
| `boot_a`, `boot_b` | 2 x 32 MB | Kernel + DTB |
| `rootfs_a`, `rootfs_b` | 2 x 256 MB | Buildroot root (read-only squashfs) |
| `oem` | 64 MB | Models, ISP tuning, LVGL assets, default recipes |
| `data` | ~6 GB | `/data/epicura.db`, recipe images, cooking logs, OTA staging |
| `userdata` | 64 MB | Wi-Fi credentials, device identity, factory calibration |

---

### 5.6 Cloud Sync (RV1106)

#### 5.6.1 Sync Strategy

The device syncs with the cloud PostgreSQL instance through the cloud REST API only; there is no device-side API server. Every outbound record goes through the `sync_outbox` table, so the device works fully offline and drains the queue when Wi-Fi returns.

| Data Type | Sync Method | Direction | Frequency |
|-----------|-------------|-----------|-----------|
| Recipes | REST GET `/recipes/sync?since=` → SQLite upsert | Cloud → Device | On-demand + daily |
| Cooking Logs | REST POST `/sessions` from outbox | Device → Cloud | After each session |
| User Preferences | REST PUT/GET | Bidirectional | On change |
| Recipe Images | HTTPS download to `/data/images`, 100 MB LRU cap | Cloud → Device | Lazy load |
| Live view request | MQTT command topic | Cloud → Device | On demand |

```c
/* sync.c — runs in the sync thread, libcurl + mbedtls, cJSON */

void sync_recipes(sync_ctx_t *s)
{
    char since[32];
    db_get_last_sync(s->db, since, sizeof since);
    json_t *resp = api_get(s, "/recipes/sync?since=%s", since);
    json_t *r;
    json_array_foreach(resp, "recipes", r)
        db_upsert_recipe(s->db, r);          /* single transaction */
    db_set_last_sync_now(s->db);
    json_free(resp);
}

void sync_drain_outbox(sync_ctx_t *s)
{
    outbox_row_t row;
    while (db_outbox_peek(s->db, &row)) {
        int rc = api_post(s, outbox_endpoint(row.kind), row.payload);
        if (rc != 200) { db_outbox_bump_attempts(s->db, row.seq); break; }
        db_outbox_delete(s->db, row.seq);
    }
}
```

#### 5.6.2 MQTT Telemetry

- **Client:** libmosquitto, direct TLS connection to the cloud broker (AWS IoT Core). No local broker.
- **Topic structure:** `epicura/{device_id}/telemetry` (publish), `epicura/{device_id}/cmd` (subscribe)
- **QoS:** Level 1 (at least once delivery)
- **Publish interval:** Every 10 seconds during cooking
- **Offline:** telemetry is spooled to `sync_outbox` (capped at 1,000 rows) and replayed on reconnect
- **Commands received:** `live_view_start`, `live_view_stop`, `recipe_sync_now`, `ota_check`

```json
{
    "device_id": "EPIC-001",
    "timestamp": "2026-02-14T12:30:00Z",
    "state": "COOKING",
    "recipe_id": "uuid-here",
    "stage": "Simmer Dal",
    "temperature": 96.2,
    "stir_active": true,
    "progress_pct": 72
}
```

#### 5.6.3 On-Demand Phone Live View

```
Phone app ──(REST)──► Cloud ──(MQTT cmd: live_view_start)──► epicurad
                                                                │
                                           bind VENC 720p/15fps, spawn rtsp-stream
                                                                │
Phone app ◄──(RTSP/RTP over Wi-Fi LAN, or cloud relay)──────────┘
                                                                │
                     no client for 60 s, or live_view_stop ──► kill rtsp-stream,
                                                               unbind VENC, free CMA
```

- Single viewer at a time. Stream is 1280x720 H.264, 15 fps, 1.5 Mbps.
- Only the main ISP path is always live; the encoder and its ~8 MB of buffers exist only during a session.
- On the same LAN the phone connects directly to `rtsp://<device>:554/pot`; otherwise the cloud relays. The relay design belongs to the cloud API spec.

#### 5.6.4 OTA Firmware Updates

| Target | Method | Mechanism |
|--------|--------|-----------|
| RV1106 (Linux) | A/B root + boot partitions | swupdate with signed `.swu`, bootloader slot switch, rollback on 3 failed boots |
| STM32 (FreeRTOS) | System bootloader | RV1106 pulls BOOT0 high + resets STM32, streams `.bin` over UART2 (ST USART bootloader protocol), verifies CRC, resets |

**Update Flow:**
1. RV1106 checks for updates via HTTPS (on `ota_check` command or daily)
2. Downloads `.swu` to `/data/ota`, verifies signature (RSA-2048)
3. RV1106: swupdate writes inactive slot, marks it bootable, reboots, confirms on successful `epicurad` start, else bootloader falls back
4. STM32: RV1106 holds STM32 in bootloader mode, streams firmware, verifies CRC, resets

---

## 6. Control Flow

### 6.1 Cooking Workflow (10-Step Sequence)

```
 1. User selects recipe on the 4" touchscreen
                │
                ▼
 2. Recipe Engine loads YAML, validates ingredients
                │
                ▼
 3. UI prompts user to load dispensing subsystems (FID/CID/SLD) with confirmation (CID slots assigned in order of use)
                │
                ▼
 4. RV1106 heat thread sends HEAT_SET_TEMP over CAN; the module ramps itself to the target and reports surface_temp
                │
                ▼
 5. For each stage:
    ┌───────────────────────────────────────────────────┐
    │  a. Dispense ingredients (DISPENSE_FID/CID/SLD)   │
    │  b. Set temperature (heat thread setpoint → module)│
    │  c. Set stir pattern (RV1106 → STM32 SET_STIR)    │
    │  d. Monitor via CV pipeline (ISP → NPU, 2 Hz)     │
    │  e. Check transition conditions                   │
    │  f. If stage complete → advance to next stage     │
    │  g. Checkpoint session to SQLite every 10 s       │
    └───────────────────────────────────────────────────┘
                │
                ▼
 6. CV pipeline confirms final stage complete
                │
                ▼
 7. RV1106 stops heating (HEAT_ON_OFF 0) and stirring (ARM_STOP)
                │
                ▼
 8. UI displays "Cooking Complete" with summary
                │
                ▼
 9. Log results to SQLite (temps, times, stages, rating); queue to sync_outbox
                │
                ▼
10. Publish summary to cloud via MQTT; drain outbox over REST
```

---

## 7. CAN Bus Communication Protocol

The RV1106, the STM32 and the induction surface's own MCU share one isolated CAN 2.0B bus at 500 kbps — the Unified PCB's isolated CAN port (J_CAN_HEAT). The RV1106 has no CAN peripheral, so it joins the bus through an MCP2518FD SPI CAN controller on SPI0 CS1 (kernel `mcp251xfd` driver, SocketCAN `can0`) and its own ISO1050DUB on the Unified PCB; the STM32 uses FDCAN1 in classic-CAN mode with ISO1050DUB #1. UART2/USART2 stays wired only as a service link for STM32 firmware flashing (ST system bootloader via BOOT0/NRST) and debug. The stirring motor is on a second, regular (non-isolated) CAN bus owned by the STM32 alone (FDCAN2, 1 Mbps, J_CAN_STIR); its frames never appear on the host bus and its protocol is private to the STM32 firmware (`stir_motor.c`).

### 7.1 Nodes and Roles

| Node | Controller | Sends | Receives |
|------|-----------|-------|----------|
| AP (RV1106) | MCP2518FD on SPI0 CS1 + ISO1050DUB #2 | Commands 0x2xx, HEAT_SET_TEMP / HEAT_ON_OFF / HEAT_QUERY / HEAT_SET_POWER (0x100–0x103), HB_AP 0x010, E_STOP 0x001 | TELEMETRY / LOADCELLS / STATUS / ACK (0x3xx), HEAT_STATUS / HEAT_FAULT / HEAT_ACK (0x18x) |
| STIR (STM32G474, Unified PCB) | FDCAN1 + ISO1050DUB #1 | TELEMETRY 0x310 (20 Hz), LOADCELLS 0x311, STATUS 0x312, ACK 0x3FF; on faults HEAT_ON_OFF = 0 and E_STOP 0x001 | Commands 0x2xx, HB_AP 0x010, HEAT_STATUS 0x180 (safety monitor), E_STOP 0x001 |
| HEAT (induction surface MCU) | Module-internal, vendor firmware; runs its own temperature PID | HEAT_STATUS 0x180 (10 Hz), HEAT_FAULT 0x181, HEAT_ACK 0x182 | HEAT_SET_TEMP 0x100, HEAT_ON_OFF 0x101, HEAT_QUERY 0x102, HEAT_SET_POWER 0x103, E_STOP 0x001 |

Rules: only the AP sends setpoints (temperature or power); the STM32 may only send HEAT_ON_OFF = 0. The module regulates temperature itself and must drop to zero power if no HEAT_SET_TEMP / HEAT_SET_POWER refresh arrives for 1 s (a selection requirement for the commercial module); the AP refreshes at 2 Hz. E_STOP (0x001) is accepted from any node and acted on by all three.

### 7.2 Message Types

This table is the single source of truth for bus identifiers. Standard 11-bit IDs; the lowest ID wins arbitration, so emergency and heartbeat frames always get through. Blocks: `0x00x` emergency, `0x01x` heartbeats, `0x1xx` induction surface (reference IDs, adapted to the chosen module), `0x2xx` AP → STM32 commands, `0x3xx` STM32 → AP reports. Command frames carry a 1-byte sequence number in byte 0 followed by the payload (≤ 7 bytes); the STM32 answers with ACK/NAK 0x3FF echoing the sequence number and carrying up to 5 bytes of result data. The low byte of each `0x2xx` ID is the former bridge type code, so the arm and dispensing documents keep their code tables (payload detail for 0x230–0x239 is owned by [[../05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]] §7.3, for 0x221–0x225 by [[../05-Subsystems/02-Robotic-Arm|Robotic Arm]] §8.2). Faults are reported in STATUS `error_code` (codes in [[05-MCU-Functional-Specification|MCU Functional Specification]] §7.2); there is no separate FAULT message. There is no temperature loop in Epicura: the AP sends HEAT_SET_TEMP and the module regulates.

| CAN ID | Message | Direction | DLC | Payload |
|--------|---------|-----------|-----|---------|
| 0x001 | E_STOP | any → all | 2 | src_node (uint8: 1=HEAT, 2=STIR, 3=AP), reason_code (uint8); no ACK, acted on by every node |
| 0x010 | HB_AP | AP → all | 5 | seq (uint8), uptime_ms (uint32 LE); every 2 s |
| 0x100 | HEAT_SET_TEMP | AP → HEAT | 4 | target_dC (int16, 0.1 °C), ramp (uint8, °C/s), max_power_pct (uint8); temperature mode, re-sent at 2 Hz as keep-alive |
| 0x101 | HEAT_ON_OFF | AP or STIR → HEAT | 1 | 0 = off, 1 = on (the STM32 only ever sends 0) |
| 0x102 | HEAT_QUERY | AP → HEAT | 0 | — |
| 0x103 | HEAT_SET_POWER | AP → HEAT | 2 | power_pct (uint8, 0–100), ramp (uint8, %/s); power mode for sear/boil stages, re-sent at 2 Hz as keep-alive |
| 0x180 | HEAT_STATUS | HEAT → all | 8 | power_pct, surface_temp_dC (int16, 0.1 °C, module's under-glass sensor), coil_temp (int8 °C), pot_detected, fault_flags (uint16), reserved; 10 Hz |
| 0x181 | HEAT_FAULT | HEAT → all | 4 | fault_code (uint16), detail (uint16) |
| 0x182 | HEAT_ACK | HEAT → AP | 3 | cmd_id (uint16), result |
| 0x202 | SET_STIR | AP → STIR | 5 | seq, pattern (uint8), speed_rpm (uint16), direction (uint8: 0=CW, 1=CCW) |
| 0x220 | SET_LED | AP → STIR | 6 | seq, mode (OFF/CAPTURE/NIGHT), r, g, b, brightness_pct |
| 0x221 | SET_SPEED | AP → STIR | 4 | seq, speed_rpm (uint16), direction — direct arm override |
| 0x222 | ARM_STOP | AP → STIR | 1 | seq (stop with decel ramp) |
| 0x223 | ARM_HOME | AP → STIR | 1 | seq |
| 0x224 | ARM_STATUS | AP → STIR | 1 | seq → ACK data: status_byte, current_rpm (uint16), position (uint16) |
| 0x225 | SET_RAMP | AP → STIR | 3 | seq, accel_limit (uint16, RPM/s) |
| 0x230 | DISPENSE_FID | AP → STIR | 3 | seq, box_id (1–6), qty_quarter_tsp (1–40) → ACK data: doses_done, est_mass_dg (uint16) |
| 0x231 | DISPENSE_CID | AP → STIR | 2 | seq, slot_id (1–5) → ACK data: cid_pos; NAK if slot_id ≤ current position |
| 0x232 | DISPENSE_SLD | AP → STIR | 4 | seq, channel (OIL=1, WATER=2), target_g (uint16) → ACK data: actual_g (uint16) |
| 0x235 | QUERY_WEIGHT | AP → STIR | 2 | seq, source (SLD_OIL=1, SLD_WATER=2) → ACK data: weight_g (int32) |
| 0x236 | PREFLIGHT | AP → STIR | 2 | seq, subsystem_mask → ACK data: status per subsystem |
| 0x237 | TARE | AP → STIR | 2 | seq, source |
| 0x238 | DISPENSER_HOME | AP → STIR | 2 | seq, target (CID=1, FID=2, 0xFF=both) |
| 0x239 | DISPENSER_STATUS | AP → STIR | 1 | seq → ACK data: cid_pos, fid_box, gate_open, rail_on, busy |
| 0x310 | TELEMETRY | STIR → AP | 8 | motor_rpm (uint16), motor_current_dA (int16, 0.1 A, from the CAN servo), safety_state, flags (pot_detected, on_battery, stir_enabled, charging), error_code, seq; 20 Hz unsolicited |
| 0x311 | LOADCELLS | STIR → AP | 5 | oil_g (int16), water_g (int16), flags; 10 Hz while dispensing |
| 0x312 | STATUS | STIR → AP | 8 | safety_state, error_code, flags (uint16), fault_detail (uint32: batt_mV for POWER_FAIL / BATTERY_FAULT); on change |
| 0x3FF | ACK / NAK | STIR → AP | 3–8 | seq, cmd_type (low byte of the command ID), result_code, data[0..4] |

### 7.3 Protocol Details

- **Physical:** CAN 2.0B, 500 kbps, isolated bus domain (5 V_ISO and GND_ISO from the B0505S-1WR3 on the Unified PCB), two ISO1050DUB transceivers on the Unified PCB (STM32 node and RV1106 node) sharing one 120 Ω termination at J_CAN_HEAT; the second termination is inside the induction surface. Shielded twisted pair ≤ 1 m to the module. The stir-motor bus (FDCAN2, SN65HVD230, 1 Mbps, J_CAN_STIR) is electrically separate and STM32-private.
- **AP side:** `mcp251xfd` kernel driver; `ip link set can0 up type can bitrate 500000` at boot; the `can` thread (SCHED_FIFO) owns a raw socket with ID filters for `0x00x`, `0x01x`, `0x18x` and `0x3xx`. The MCP2518FD shares SPI0 with the LCD (CS0) at ≤ 20 MHz; its 32-object RX FIFO absorbs frames while an LCD DMA chunk (≤ 10 ms) holds the bus.
- **STM32 side:** FDCAN1 classic frames, RX FIFO interrupt → command parser in the CAN comms task (20 Hz), telemetry TX from the sensor task.
- **Timeouts:** ACK 500 ms, 3 retries; E_STOP needs no ACK. HB_AP every 2 s; the STM32 enters its safe state after 5 s without it. The AP treats TELEMETRY older than 300 ms as STM32 loss and HEAT_STATUS older than 500 ms as module loss: HEAT_ON_OFF 0 and pause. The module drops to zero power 1 s after the last HEAT_SET_TEMP / HEAT_SET_POWER refresh (AP sends at 2 Hz).
- **Bus load:** 20 Hz TELEMETRY + 2 Hz HEAT_SET_TEMP + 10 Hz HEAT_STATUS + sporadic commands ≈ 5 kbit/s, about 1 % of 500 kbps.
- **Service UART:** USART2 ↔ UART2 (1 Mbps) carries only the ST system-bootloader protocol for STM32 firmware updates (BOOT0 on header GPIO 32, NRST on GPIO 38) and an optional debug console; no runtime traffic.

---

## 8. Real-Time Requirements

| Task | Frequency | Deadline | Processor | Priority |
|------|-----------|----------|-----------|----------|
| Heater setpoint keep-alive (`heat` thread) | 2 Hz | 500 ms | RV1106 | High (SCHED_FIFO) |
| Motor control (CAN servo on FDCAN2) | 50 Hz | 20 ms | STM32 | Highest |
| Sensor polling (ADC/I2C) | 10 Hz | 100 ms | STM32 | High |
| Safety monitor check | 10 Hz | 100 ms | STM32 | Highest |
| CAN comms handler (FDCAN1) | 20 Hz | 50 ms | STM32 | Medium |
| CAN thread (`can0` RX, heartbeat) | 20 Hz / 0.5 Hz | 50 ms | RV1106 | High (SCHED_FIFO) |
| CV inference | 2 Hz | 500 ms | RV1106 | Medium |
| UI update (LVGL tick) | 20 Hz | 50 ms | RV1106 | Medium |
| Recipe engine tick | 1 Hz | 1 s | RV1106 | Low |
| Session checkpoint (SQLite) | 0.1 Hz | 10 s | RV1106 | Low |
| Cloud sync (MQTT) | 0.1 Hz | 10 s | RV1106 | Low |
| Phone stream (VENC) | 15 fps | on demand | RV1106 hardware | Low |

The RV1106 has one core. The `can` and `heat` threads run at real-time priority so heartbeats and the 2 Hz setpoint keep-alive are never starved by UI rendering or a sync burst; everything else is `SCHED_OTHER`. Safety does not depend on this: the STM32 cuts heat if heartbeats stop, and the induction surface drops to zero power when the keep-alive stops arriving.

---

## 9. Error Handling

### 9.1 Common Errors

| Error | Detection | Severity | Recovery |
|-------|-----------|----------|----------|
| Sensor failure (temp/weight) | ADC out-of-range or NaN | CRITICAL | Fall back to timer-based cooking, alert user |
| Communication timeout | No ACK within 500 ms x 3 retries | WARNING → CRITICAL | Retry 3x, then pause cooking, alert user |
| Over-temperature | Temp > 260C (absolute max) | CRITICAL → E_STOP | Immediately cut heater, stop motor, alarm |
| Motor stall | Overcurrent on motor driver | WARNING → CRITICAL | Stop motor, alert user, suggest pot check |
| CV failure | Camera disconnect, ISP timeout or rknn error | WARNING | Fall back to timer + temp thresholds |
| Memory pressure | Free RAM < 32 MB | WARNING | Kill `rtsp-stream`, drop LCD preview, log |
| Power anomaly | Voltage/current out of range | CRITICAL | Graceful shutdown, checkpoint to SQLite |
| Recipe parse error | Invalid YAML or missing fields | WARNING | Reject recipe, notify user, suggest re-download |

### 9.2 Fallback Strategies

1. **CV fallback:** If camera or model fails, every recipe stage includes `duration_seconds` and `temp_target` as backup transition criteria
2. **Communication fallback:** the induction surface drops to zero power 1 s after the last HEAT_SET_TEMP / HEAT_SET_POWER refresh; the STM32 holds the last stir/dispense state for up to 30 seconds, then enters safe shutdown, forces HEAT_ON_OFF = 0 and disables the stir motor
3. **Power loss recovery:** `session_checkpoint` row in SQLite (WAL, `synchronous=NORMAL`) is rewritten every 10 seconds; on restart, offer to resume or discard
4. **Process failure:** `epicurad` is supervised by busybox init with a 10 s kernel watchdog; a crash restarts the process, the heater drops to zero power within 1 s (no setpoint refresh) and the STM32 holds the stir state meanwhile
6. **Power loss:** the 2S battery on the Unified PCB keeps the RV1106, LCD and STM32 running; on POWER_FAIL the engine checkpoints to SQLite and pauses (state machine §5); at 6.2 V pack voltage the STM32 requests shutdown and `epicurad` syncs and halts
5. **Streaming failure:** Live view is best-effort. Any encoder or RTSP error tears the stream down and never affects cooking

---

## 10. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[03-Main-Loop-State-Machine|Main Loop State Machine]]
- [[01-Tech-Stack|Tech Stack]]
- [[01-UI-UX-Design|UI/UX Design]]
- [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]]

#epicura #software-architecture #controller #firmware #recipe-engine #computer-vision #canbus #safety #stm32 #rv1106 #luckfox

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-11-03 | Manas Pradhan | Application processor changed from Raspberry Pi CM5 to RV1106G3 (Luckfox Pico Zero). Replaced Docker/PostgreSQL/Fastify/Kivy/Python stack with a single C application: SQLite, LVGL on 4" SPI LCD, ISP+NPU vision at 720p, on-demand H.264 phone streaming, STM32 link moved from SPI to UART. Added memory budget and bus allocation. |
| 2.1 | 2026-11-04 | Manas Pradhan | Confirmed: camera sensor is SC3336 (IMX219/IMX477 dropped, no RV1106 ISP tuning); WS2812B LED ring driven by STM32, SET_LED (0x20) added to bridge protocol. |
| 2.2 | 2026-11-04 | Manas Pradhan | Recipe YAML example and cooking flow updated for servo carousels: ASD → FID (box, qty in ¼ tsp), CID slot whole-slot (mode removed); message table carries the 0x30–0x39 dispensing block |
| 2.3 | 2026-11-04 | Manas Pradhan | Camera changed to IMX415-98 IR-CUT (SC3336 not compatible with the Pico Zero); §7.2 is now the single source of truth for bridge type codes (arm 0x21–0x25 and dispensing 0x30–0x39 blocks added, SET_STIR gains direction); CAN alternative for the bridge dropped |
| 3.1 | 2026-11-04 | Manas Pradhan | Temperature loop removed from Epicura: the induction module regulates on its own sensor; `heat` thread now sends HEAT_SET_TEMP (0x100) / HEAT_SET_POWER (0x103) at 2 Hz and relays surface_temp from HEAT_STATUS; TELEMETRY drops ir_temp (motor current, battery flags added); stirring motor is a CAN servo on the STM32's private FDCAN2 bus; battery-backed power-loss fallback added; §5.3.1, §7 and §8 updated |
| 3.0 | 2026-11-04 | Manas Pradhan | Isolated CAN bus now connects the RV1106 (MCP2518FD on SPI0 CS1, SocketCAN), the STM32 (FDCAN1) and the induction surface MCU; UART2 kept as service link only (flashing/debug); temperature PID moved from the STM32 to the RV1106 `heat` thread, AP commands HEAT_SET_POWER directly, STM32 keeps HEAT_ON_OFF=0 / E_STOP / relay authority; §7 rewritten as the CAN ID map (0x001 E_STOP, 0x010 HB_AP, 0x1xx heater, 0x2xx commands, 0x3xx reports); SET_TEMP retired |
