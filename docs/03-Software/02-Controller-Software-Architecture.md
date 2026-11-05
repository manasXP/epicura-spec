---
created: 2026-02-15
modified: 2026-11-05
version: 3.9
status: Draft
---

# Controller & Software Architecture

## 1. Architecture Overview

Epicura uses three controllers split across two physical units. In the lift-off Dispensing Unit (DU), a Rockchip RV1106G3 (Luckfox Pico Zero) runs Buildroot Linux from the DU battery for AI vision, UI, the recipe engine and cloud connectivity, and an STM32G0B1 (the **DU STM32**) on the same Unified PCB v5.0 runs FreeRTOS for ingredient dispensing, the LED ring, buzzer, battery/dock monitoring and the DU's CAN node. In the Cooking Surface (CS) base, a second STM32G0B1 on the Cooking Surface Controller (CSC) runs FreeRTOS for stir-motor control, the heater off-switch and safety monitoring. The RV1106 talks to the DU STM32 over a UART host link; the DU STM32, the CSC STM32 and the electric heating unit's own MCU share one isolated CAN bus that crosses the dock between the two units. The DU STM32 is a transparent gateway: on the bus the DU is still the AP node, the RV1106 commands the heater setpoints through it, and the CSC STM32 keeps an independent off-switch.

The RV1106 is a 256 MB, single-core, GPU-less vision SoC. The application side is therefore a single native C application on a minimal Buildroot image, not a container stack. Heavy image work is pushed into the chip's hardware blocks (ISP, NPU, RGA, H.264 encoder) and the CPU is left with UI, recipe logic, storage and comms. See [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]] for the rationale and the CM5 comparison.

| Aspect | RV1106 (Application) | DU STM32 (Dispensing, gateway) | CSC STM32 (Real-Time, safety) |
|--------|----------------------|--------------------------------|-------------------------------|
| **Processor** | Rockchip RV1106G3, 1x Cortex-A7 (32-bit, NEON, FPU) | STM32G0B1RE, Cortex-M0+ | STM32G0B1RE, Cortex-M0+ (same part, same firmware tree) |
| **Board / unit** | Unified PCB v5.0 in the Dispensing Unit (lifts off, no cable; 2S Li-ion pack is the primary supply, dock charging) | Unified PCB v5.0, beside the Pico Zero slot | Cooking Surface Controller (CSC) v1.0 in the Cooking Surface base, beside the 24 V PSU |
| **Clock** | 1.2 GHz | 64 MHz | 64 MHz |
| **Memory** | 256 MB DDR3L (in-package), 8 GB eMMC | 144 KB SRAM (parity), 512 KB Flash (ECC) | 144 KB SRAM (parity), 512 KB Flash (ECC) |
| **Accelerators** | 1 TOPS NPU, 5 MP ISP, RGA 2D, H.264/H.265 encoder | hardware CRC, FDCAN1 | CMSIS-DSP (fixed point), hardware CRC, 2x FDCAN |
| **OS** | Buildroot Linux (Luckfox SDK, kernel 5.10) | FreeRTOS 10.x | FreeRTOS 10.x |
| **Role** | AI/Vision, UI, Recipe Engine, Heater setpoints (through the link), Storage, Cloud | Ingredient dispensing (FID / CID / SLD), LED ring, buzzer, battery/dock monitoring, host link ↔ CAN gateway (no safety authority) | Stir motor (CAN), heater off-switch, safety relay, E-stop, exhaust fans, dock power |
| **Languages** | C11 (single application), LVGL | C (MISRA C subset) | C (MISRA C subset) |
| **Graphics** | LVGL 9 on 4" 480x320 SPI LCD, software rendering | None | None |
| **IPC** | Host link: UART2 (header pins 8/10) ↔ DU STM32 USART1, 921,600 baud, COBS-framed CAN-shaped frames with CRC-16 (§7.4); no CAN peripheral and no SocketCAN on the RV1106; GPIO 32/38 = DU STM32 BOOT0/NRST for flashing it via the ST system bootloader | USART1 host link; FDCAN1 + SN65HVD230 (non-isolated, referenced to DU ground) = the DU's node on the CSC's isolated CAN 2.0B 500 kbps bus (crosses the dock on J_DOCK pins 3–5); forwards AP frames both ways, terminates the DU-local block locally; I2C1 to the dispenser peripherals | FDCAN1 + ISO1050DUB #1 on the same bus (host commands, telemetry, heater off-switch, in-application CAN bootloader 0x7E0/0x7E8 — image streamed by the RV1106 through the DU gateway); FDCAN2 + ISO1050DUB #3 = second isolated 1 Mbps bus to the stirring motor; USART2 = local debug console (J_DBG) only |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│      Luckfox Pico Zero / RV1106G3 (Buildroot Linux) — Dispensing Unit       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              epicurad  (single C process, pthreads)                 │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌──────┐ ┌──────────┐ ┌─────────┐  │    │
│  │  │Recipe Engine│ │ CV Pipeline │ │  UI  │ │Cloud Sync│ │Dispense │  │    │
│  │  │(State Mach.)│ │ (ISP → NPU) │ │(LVGL)│ │(MQTT/TLS)│ │(client) │  │    │
│  │  └─────────────┘ └─────────────┘ └──────┘ └──────────┘ └─────────┘  │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                      Library Layer                                  │    │
│  │  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐ │    │
│  │  │  SQLite  │ │ libmosquitto│ │ rockit   │ │ rknn_api│ │  link   │ │    │
│  │  │  (WAL)   │ │ libcurl/TLS │ │ (VI/ISP/ │ │ (NPU)   │ │ (UART2, │ │    │
│  │  │          │ │            │ │  VENC)   │ │         │ │  COBS)  │ │    │
│  │  └──────────┘ └────────────┘ └──────────┘ └─────────┘ └────┬────┘ │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │            Buildroot Linux 5.10 (busybox init, fbtft, wpa)          │    │
│  │  SPI0: LCD | I2C3: FT6336 touch | UART2: host link | GPIO 32/38     │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  Hardware: RV1106G3, Cortex-A7 @ 1.2 GHz, 256 MB, NPU, ISP, VENC    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │ UART2 ↔ USART1, 921,600 baud            │
│  ┌─────────────────────────────────▼───────────────────────────────────┐    │
│  │        STM32G0B1RE (FreeRTOS) — DU STM32, Unified PCB v5.0          │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │    │
│  │  │ Link/Gateway │ │  Dispense    │ │   Monitor    │                 │    │
│  │  │ (event,≤5 ms)│ │  (50 Hz)     │ │   (1 Hz)     │                 │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │    │
│  │  USART1 | FDCAN1 (AP node) | I2C1: PCA9685, PCF8574 #2, INA219 ×2 | │    │
│  │  SLD Hall ×6 | TIM: pumps, LED ring, buzzer | DOCK_SENSE_A          │    │
│  └─────────────────────────────────┬───────────────────────────────────┘    │
│                                    │                                        │
│  On-demand only:  rtsp-stream (child process, H.264 720p → phone)           │
│  Power: 2S Li-ion pack (primary supply), DOCK_24V charge while docked       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                 CAN 2.0B 500 kbps (isolated bus, over the dock pogo contacts,
                              shared with the heating unit)
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│        STM32G0B1RE (FreeRTOS) — Cooking Surface Controller, CS base         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      FreeRTOS Tasks                                  │    │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │    │
│  │  │ CAN Comms   │ │ Motor Control│ │ Thermal/Fan  │ │   Safety   │ │    │
│  │  │  (20 Hz)    │ │  (50 Hz)     │ │  (1 Hz)      │ │  Monitor   │ │    │
│  │  └─────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                      HAL / Driver Layer                              │    │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐  │    │
│  │  │ PWM  │  │ ADC  │  │FDCAN1│  │FDCAN2│  │ GPIO │  │ IWDG/CRC │  │    │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────────┘  │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │           Hardware: STM32G0B1RE, Cortex-M0+ @ 64 MHz                │    │
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
| Heater setpoints | RV1106 | `heat` thread (SCHED_FIFO) re-sends HEAT_SET_TEMP / HEAT_SET_POWER at 2 Hz through the host link and reads HEAT_STATUS; the heating unit runs its own PID on its own sensor — no temperature loop in Epicura |
| Host link / CAN gateway | STM32 (DU) | Link/Gateway task: USART1 ↔ FDCAN1; forwards AP frames both ways unchanged, terminates the DU-local block (0x220, 0x226, 0x230–0x239) locally, answers with 0x3FE, reports DU_STATUS 0x311; drops dispensers after 5 s without HB_AP (§7.4) |
| Ingredient Dispensing | STM32 (DU) | `Dispense` task on the Unified PCB: PCA9685 servo carousels over I2C1, TB6612 pumps with Hall tach metering (open loop, 2026-11-05), tank present / low Hall switches and the prime routine on PC0–PC5; stall detection from INA219 #1; commanded by the RV1106 `dispense` client over the link (§5.7) |
| LED ring (white, 5000 K) | STM32 (DU) | TIM1 PWM duty through Q_LED (OFF 0 %, CAPTURE 100 %, NIGHT 30 %) on SET_LED 0x220 from the RV1106; no colour control |
| Buzzer | STM32 (DU) | TIM14 PWM via 2N7002 on SET_BUZZER 0x226 |
| Battery / dock monitoring | STM32 (DU) | `Monitor` task: INA219 #2 on the pack (voltage, current → state of charge), CHRG/STDBY, DOCK_SENSE_A and DOCK_PWR_OK on EXTI; reported in DU_STATUS 0x311 at 1 Hz and on change; the RV1106 keeps the battery indicator always visible in the UI |
| Stir Motor Control | STM32 (CSC) | CAN servo on FDCAN2: velocity/position commands at 50 Hz, encoder feedback; K_SU enable (pilot relay on the Stirring Unit PSU's AC input) |
| Safety Monitor / Watchdog | STM32 (CSC) | Independent safety, E-stop authority, safe hold on DOCK_SENSE_B when the DU is lifted |
| Heater interlock | STM32 (CSC) | Listens to HEAT_STATUS on the bus; forces HEAT_ON_OFF = 0, broadcasts E_STOP and opens the relay on faults; never sends power levels |
| Exhaust fans | STM32 (CSC) | Thermal/Fan task (1 Hz): fan MOSFETs on 12 V, SET_EXHAUST / EXHAUST_AUTO from the AP, optional tach and pot reed |
| Dock power | STM32 (CSC) | Q_DOCK switches DOCK_24V to the dock pads only while DOCK_SENSE_B is low; pads are dead when the DU is lifted |

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
│  │  link thread                                           │ │
│  │  • /dev/ttyS2 (UART2) to the DU STM32, 921,600 baud    │ │
│  │  • COBS + CRC-16 CAN-shaped frames; routes bus frames  │ │
│  │    to heat/engine, DU-local replies to dispense        │ │
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
│  │  dispense thread (client)                              │ │
│  │  • Queue from the engine → 0x230–0x239 over the link   │ │
│  │  • Waits for 0x3FE ACK/NAK; LED/buzzer 0x220/0x226     │ │
│  │  • Battery / dock state from DU_STATUS 0x311           │ │
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

**Buildroot package set (beyond the Luckfox base):** `sqlite`, `libyaml`, `cjson`, `libmosquitto`, `libcurl`, `mbedtls`, `lvgl`, `swupdate`, `wpa_supplicant`, `bluez5` (BLE provisioning), `rockit` + `rknn` runtime from the Luckfox SDK; kernel drivers (all mainline in 5.10): `fbtft` (ST7796S), `edt-ft5x06` (touch), the Rockchip 8250 UART (host link on UART2), `pwm-rockchip` (LCD backlight only). No CAN, no SocketCAN and no dispenser peripheral drivers on Linux: every dispenser, load-cell and power-monitor device hangs off the DU STM32's I2C1. Not included: Python, OpenCV, Docker, PostgreSQL, Node.js, Redis, Mosquitto broker, Kivy, GStreamer.

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

The Pico Zero header carries only what the RV1106 itself must drive: the display on SPI0 CS0, the touch controller on I2C3, the camera on its CSI FPC and one UART to the DU STM32. Every dispenser, load-cell and power-monitor device, the LED ring, the buzzer, the dock sense lines and the CAN node hang off the DU STM32 on the Unified PCB v5.0, reached over the UART2 host link (§7.4). The RV1106 has no CAN peripheral and no CAN controller on SPI any more; the DU STM32's FDCAN1 is the DU's node on the isolated bus, which reaches the board through the dock pogo contacts.

| Function | Bus | Header pins | Notes |
|----------|-----|-------------|-------|
| 4" LCD (ST7796S, 480x320) | SPI0 M0: MOSI 19, MISO 21, CLK 23, CS0 24 | + DC GPIO 22, RST GPIO 26, backlight PWM10 pin 12 | fbtft, 50 MHz, DMA. ~50 ms full frame; LVGL partial redraws |
| Touch (FT6336, 0x38) | I2C3 M0: SDA 16, SCL 18 | INT GPIO 36, RST spare GPIO | evdev; the only device on I2C3 |
| Host link to the DU STM32 | UART2 M1: TX pin 8, RX pin 10 | → DU STM32 USART1 (PA10 / PA9) | `/dev/ttyS2`, 921,600 baud 8N1, COBS-framed CAN-shaped frames with CRC-16 (§7.4); carries every CAN frame to and from the bus plus the DU-local dispensing / LED / buzzer / DU_STATUS block; also the ST system-bootloader UART for flashing the DU STM32 |
| DU STM32 BOOT0 / NRST | GPIO 32 (out, 10k pull-down) / GPIO 38 (open-drain, 10k pull-up) | | Driven only by the swupdate handler to flash the DU STM32 through its system bootloader |
| Debug console | UART0 M0: TX 35, RX 37 | | Luckfox default |
| Camera | MIPI CSI FPC (4-lane) | | **IMX415-98 IR-CUT 8 MP** (the colour camera Luckfox supports on the Pico Zero; ISP tuning file shipped in SDK; 22-pin FPC). SC3336 is marked incompatible with the Pico Zero; IMX219/IMX477 dropped: no RV1106 tuning file |
| Wi-Fi / BLE | On-board module | | 2.4 GHz Wi-Fi 6, BT 5.2 |
| Freed vs v4.0 | SPI0 CS1 (GPIO 58), MCP2518FD nINT, PCA9685_OE, DOCK_SENSE_A, DOCK_PWR_OK, 4 PWM, all I2C3 devices except touch | | Moved to the DU STM32 (PCF8574 #2, PCA9685, INA219 ×2 on its I2C1; SLD Hall switches on its GPIO; pumps, ring and buzzer on its timers) |
| Spare | UART3, UART4, I2C1, I2C2, SPI0 CS1 | | |

### 4.4 STM32 FreeRTOS Stack

The `epicura-firmware` tree builds two images for the same STM32G0B1RE: `csc` (Cooking Surface Controller) and `du` (DU STM32 on the Unified PCB v5.0). They share the HAL, FreeRTOS, the MISRA C rule set, the CAN frame codec and the X-CUBE-CLASSB start-up self-tests; only the task set differs.

```
┌─────────────────────────────────────────────────────────┐
│              FreeRTOS Application Tasks                   │
│  csc image:                                              │
│  • CAN Comms (20 Hz)   • Motor Control (50 Hz)           │
│  • Safety Monitor (10 Hz) • Thermal/Fan (1 Hz)           │
│  du image:                                               │
│  • Link/Gateway (event-driven, ≤ 5 ms: USART1 ↔ FDCAN1,  │
│    COBS codec, ID routing, HB_AP watchdog)               │
│  • Dispense (50 Hz while a move is active)               │
│  • Monitor (1 Hz + EXTI: battery, charger, dock sense,   │
│    DU_STATUS; LED ring and buzzer)                       │
│  (no Dispense task on the CSC: it has no I2C or          │
│   SLD Hall sensing; no safety task on the DU)            │
├─────────────────────────────────────────────────────────┤
│                      FreeRTOS 10.x                       │
│  • Priority-based preemptive scheduling                  │
│  • Queues, Semaphores, Timers, Event Groups              │
│  • Memory management (heap_4)                            │
├─────────────────────────────────────────────────────────┤
│                   HAL / CMSIS Layer                       │
│  • STM32 HAL drivers (TIM PWM, ADC, FDCAN, I2C, GPIO,    │
│    UART + DMA)                                           │
│  • CMSIS-DSP (signal filtering)                          │
│  • CMSIS-RTOS2 abstraction                               │
├─────────────────────────────────────────────────────────┤
│     Hardware: STM32G0B1RE (Cortex-M0+ @ 64 MHz)          │
│     Flash: 512 KB  |  SRAM: 144 KB                       │
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

The temperature loop runs **inside the heating unit** on its own centre (pot-bottom) sensor. The `heat` thread of `epicurad` only owns the setpoint: it sends HEAT_SET_TEMP (0x100: target, ramp, max power) or HEAT_SET_POWER (0x103) when the engine changes a stage, re-sends it at 2 Hz as the unit's keep-alive, and publishes `surface_temp` from HEAT_STATUS (0x180) to the engine and UI. If no HEAT_STATUS arrives for 500 ms, or the unit reports a fault, the thread sends HEAT_ON_OFF 0 and the engine pauses. The STM32 and the unit keep their own independent over-temperature cut-offs.

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
        engine_pause(PAUSE_HEATER_ERROR);
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
| WARNING | CRITICAL | Temperature > critical threshold (surface_temp > 220C; E_STOP at 230C) |
| WARNING | CRITICAL | Motor stall detected (overcurrent) |
| WARNING | CRITICAL | RV1106 heartbeat lost for > 5 seconds |
| CRITICAL | E_STOP | Any CRITICAL condition persists > 3 seconds |
| WARNING | NORMAL | All conditions return to safe range |
| NORMAL / WARNING | SAFE_HOLD | DOCK_SENSE_B open (Dispensing Unit lifted): HEAT_ON_OFF = 0, stir disable frame, K_SU off (SU PSU de-energised), Q_DOCK off, STATUS error_code 0x17 DU_UNDOCKED. Not an E_STOP |
| SAFE_HOLD | NORMAL | DOCK_SENSE_B low again (DU re-docked) and HB_AP received |
| E_STOP | NORMAL | Manual user reset only |

**Watchdog Timer:**
- RV1106 sends heartbeat every 2 seconds on the CAN bus (HB_AP, 0x010)
- STM32 independent watchdog (IWDG) timeout: 5 seconds
- If heartbeat missed: enter WARNING state
- If heartbeat missed > 5s: enter CRITICAL state, cut the heater

**Dock safe hold (DOCK_SENSE_B, PB3):** the Dispensing Unit ties dock pin 8 to ground; the CSC pulls it up. When the pad opens (unit lifted) the Safety Monitor enters SAFE_HOLD immediately: HEAT_ON_OFF = 0, stir disable on FDCAN2, K_SU off (SU PSU de-energised) and Q_DOCK off (dock pads de-energised), STATUS with DU_UNDOCKED. The heater also drops to zero by itself ≤ 1 s after the last keep-alive, because the AP has left the bus with the unit. SAFE_HOLD clears to NORMAL on its own when DOCK_SENSE_B reads low again and HB_AP returns; the recipe engine still needs a user tap to resume (state machine §5).

**Emergency Actions (E_STOP):**
1. Immediately send HEAT_ON_OFF = 0 (0x101) to the heating unit, broadcast E_STOP (0x001), open the safety relay
2. Stop servo motor and engage brake; K_SU off (SU PSU de-energised)
3. Send alert message to RV1106 UI (if comms available); the RV1106 sounds the buzzer on the Dispensing Unit
4. Log event to non-volatile memory
5. Require manual user intervention to reset

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
| CSC STM32 (FreeRTOS, CS base) | In-application CAN bootloader (OpenBLT-style) | swupdate handler streams the image through the DU STM32 gateway onto the isolated CAN bus with FW_UPDATE_REQ 0x7E0 / FW_UPDATE_RSP 0x7E8 (ERASE / WRITE / VERIFY / BOOT), verifies CRC, boots; USB-C DFU on the CSC is the bench fallback, SWD for the factory |
| DU STM32 (FreeRTOS, Unified PCB v5.0) | ST system bootloader on USART1 | swupdate handler drives BOOT0 (GPIO 32) high, pulses NRST (GPIO 38), flashes over the host link UART, verifies, releases BOOT0 and resets; `link` thread paused, dispensing refused meanwhile; J_SWD for the bench |

**Update Flow:**
1. RV1106 checks for updates via HTTPS (on `ota_check` command or daily)
2. Downloads `.swu` to `/data/ota`, verifies signature (RSA-2048)
3. RV1106: swupdate writes inactive slot, marks it bootable, reboots, confirms on successful `epicurad` start, else bootloader falls back
4. CSC STM32: only while docked and idle (no cook running); the swupdate handler sends ERASE, streams WRITE frames (5 data bytes each) through the DU gateway, VERIFY (CRC), then BOOT; the CSC STM32 keeps its heater off-switch and E_STOP handling active throughout
5. DU STM32: only while idle; the gateway is down during the flash, so the CSC STM32 loses HB_AP and sits in its safe state until the DU STM32 reboots and the link resumes

---

### 5.7 Ingredient Dispensing (DU STM32 `Dispense` task, RV1106 `dispense` client)

Since the Unified PCB v5.0 the dispenser hardware is driven by the DU STM32: its `Dispense` task (50 Hz while a move is active, idle otherwise) owns every dispenser peripheral on its I2C1 and the pump timers. On the RV1106 the `dispense` thread (`SCHED_OTHER`) is a thin client: the recipe engine feeds it through an internal queue whose commands keep the names and semantics of the original CAN block, and it sends each one over the host link as a DU-local frame (0x230–0x239, §7.4) and waits for the DU STM32's ACK/NAK (0x3FE): `DISPENSE_FID box_id qty`, `DISPENSE_CID slot_id`, `DISPENSE_SLD channel target_ml`, `SLD_PRIME`, `QUERY_SLD`, `PREFLIGHT`, `SLD_CAL`, `DISPENSER_HOME`, `DISPENSER_STATUS`. Payload detail and the mechanical sequences stay in [[../05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]]; the DU STM32 requirements are in [[05-MCU-Functional-Specification|MCU Functional Specification]] §10.

| Function | Mechanism (DU STM32) |
|----------|----------------------|
| Servo moves (FID / CID carousels, DS3218, MG996R ×2, MG90S) | PCA9685 (0x41, I2C1); ramped moves ≤ 3°/tick; one servo at a time; 6V_DSP rail enabled through PCF8574 #2 P4 for the move and switched off when idle; PCA9685 OE (PB0) held high (servos off) until the task starts and whenever the host link is lost |
| Stall detection | INA219 #1 (0x40) on the 6V_DSP rail: current > 2.5 A for 300 ms, or 3 s move timeout, or I2C NACK → retry once with 10° back-off → NAK DSB_STALL |
| SLD oil / water | Open loop (robot-mop pattern, 2026-11-05): tank present / low Hall check, prime if pending (boot or tank re-seat; fixed pulse count), TB6612 pump (TIM3 PWM, direction P3 / P5) run while the Hall tach pulses (EXTI PC0 / PC1) are counted to target_pulses = target_ml × 1000 / cal_ul; no-flow (no pulse in 1 s, rate < 25 %) and INA219 #1 current window → SLD_DISPENSE_ERROR; actual_ml + primed_ml returned in the ACK data; the nozzle check valve closes by itself |
| CID ordering | slot_id must be ascending within a session, otherwise NAK (unchanged rule) |
| Prime / query / preflight / cal / home / status | 0x233, 0x235–0x239, answered with 0x3FE within 50 ms (status) or at completion (moves, prime) |
| Faults (DU STM32-detected) | DSB_STALL, SLD_LOW_LEVEL, SLD_DISPENSE_ERROR, SLD_TANK_ABSENT, NOT_DOCKED (SLD dose or prime while lifted) → NAK result code and DU_STATUS error_code → engine pause, state machine §5. The RV1106 adds DU_LINK_LOST (no DU_STATUS for 3 s) |

```c
/* dispense.h — internal queue from the engine thread; same names as the CAN-era block.
 * The client encodes each command as a 0x23x frame on the host link and matches 0x3FE by seq. */
typedef enum { DSP_FID, DSP_CID, DSP_SLD, DSP_SLD_PRIME, DSP_QUERY_SLD, DSP_PREFLIGHT,
               DSP_SLD_CAL, DSP_HOME, DSP_STATUS } dsp_op_t;

int dispense_submit(const dsp_cmd_t *cmd);                          /* returns seq */
int dispense_wait(uint8_t seq, dsp_result_t *out, int timeout_ms);  /* ACK/NAK + data */
```

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
 3. UI prompts user to lift the Dispensing Unit, load FID/CID/SLD and re-dock, with confirmation (CID slots assigned in order of use; tank present / low from QUERY_SLD; SLD_PRIME after a refill)
                │
                ▼
 4. RV1106 heat thread sends HEAT_SET_TEMP over the host link and CAN; the module ramps itself to the target and reports surface_temp
                │
                ▼
 5. For each stage:
    ┌───────────────────────────────────────────────────┐
    │  a. Dispense ingredients (dispense client → DU)   │
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

The DU STM32 (for the RV1106), the CSC STM32 and the electric heating unit's own MCU share one isolated CAN 2.0B bus at 500 kbps. The isolated domain (5V_ISO / GND_ISO) is generated once, on the Cooking Surface Controller (B0505S-1WR3), runs to the heating unit on J_CAN_HEAT and is extended over the dock contacts (J_DOCK pins 3–6) to the Unified PCB v5.0 in the Dispensing Unit. The RV1106 has no CAN peripheral: the DU's node is the DU STM32's FDCAN1 (classic-CAN mode) with a plain SN65HVD230 on the Unified PCB, and the RV1106 reaches it over the UART host link (§7.4). The DU node is **not isolated**: both galvanic barriers sit on the CSC's two ports, GND_ISO is tied to the DU logic ground at dock pad 5 (the only place the host-bus domain is referenced), and dock pad 6 (5V_ISO) is reserved. The CSC's isolators are signal-reference / ground-loop barriers, not safety barriers — the DU ground already meets the CS ground through dock pad 2 — so the heating unit's CAN port must itself be SELV (isolated inside the unit). The DU STM32 is a transparent gateway, so on the bus the DU is still the AP node and this ID map is unchanged. The CSC STM32 uses FDCAN1 with ISO1050DUB #1 on the CSC; its firmware updates run over this same bus (0x7E0 / 0x7E8), streamed by the RV1106 through the gateway. The stirring motor is on a second isolated CAN bus owned by the STM32 alone (FDCAN2, 1 Mbps, ISO1050DUB #3 + B0505S #2 on the CSC with the bus side in the Stirring Unit's own domain 5V_ISO2 / GND_SU, J_CAN_STIR on the CSC, harness through the right pillar to J_SU); its frames never appear on the host bus and its protocol is private to the STM32 firmware (`stir_motor.c`).

### 7.1 Nodes and Roles

| Node | Controller | Sends | Receives |
|------|-----------|-------|----------|
| AP (Dispensing Unit: RV1106 behind the DU STM32 gateway, Unified PCB v5.0) | DU STM32 FDCAN1 + SN65HVD230 (non-isolated, 3.3 V, referenced to DU ground = GND_ISO at dock pad 5); frames originate on the RV1106 and are forwarded unchanged over the host link (§7.4) | Commands 0x2xx (SET_STIR, arm block, exhaust block), HEAT_SET_TEMP / HEAT_ON_OFF / HEAT_QUERY / HEAT_SET_POWER (0x100–0x103), HB_AP 0x010, E_STOP 0x001, FW_UPDATE_REQ 0x7E0 (update mode) | TELEMETRY / STATUS / ACK (0x3xx), HEAT_STATUS / HEAT_FAULT / HEAT_ACK (0x18x), FW_UPDATE_RSP 0x7E8 |
| STIR (STM32G0B1, Cooking Surface Controller, src_node 2) | FDCAN1 + ISO1050DUB #1 | TELEMETRY 0x310 (20 Hz), STATUS 0x312, ACK 0x3FF, FW_UPDATE_RSP 0x7E8; on faults HEAT_ON_OFF = 0 and E_STOP 0x001. Sends no LOADCELLS — the load cells are on the RV1106 | SET_STIR 0x202, arm block 0x221–0x225, exhaust block 0x260–0x262, HB_AP 0x010, HEAT_STATUS 0x180 (safety monitor), E_STOP 0x001, FW_UPDATE_REQ 0x7E0. Receives no dispensing or LED commands — both are DU-local link messages terminated on the DU STM32 (§7.4) |
| HEAT (heating unit MCU) | Unit-internal, vendor firmware; runs its own temperature PID | HEAT_STATUS 0x180 (10 Hz), HEAT_FAULT 0x181, HEAT_ACK 0x182 | HEAT_SET_TEMP 0x100, HEAT_ON_OFF 0x101, HEAT_QUERY 0x102, HEAT_SET_POWER 0x103, E_STOP 0x001 |

Rules: only the AP sends setpoints (temperature or power); the STM32 may only send HEAT_ON_OFF = 0. The module regulates temperature itself and must drop to zero power if no HEAT_SET_TEMP / HEAT_SET_POWER refresh arrives for 1 s (a selection requirement for the commercial module); the AP refreshes at 2 Hz. E_STOP (0x001) is accepted from any node and acted on by all three: the hard E-stop button is on the Cooking Surface (wired to the CSC), and the DU's UI soft stop broadcasts E_STOP from the AP while docked.

### 7.2 Message Types

This table is the single source of truth for bus identifiers. Standard 11-bit IDs; the lowest ID wins arbitration, so emergency and heartbeat frames always get through. Blocks: `0x00x` emergency, `0x01x` heartbeats, `0x1xx` heating unit (reference IDs, adapted to the chosen unit), `0x2xx` AP → STM32 commands, `0x3xx` STM32 → AP reports, `0x7Ex` firmware update (update mode only, lowest priority). Command frames carry a 1-byte sequence number in byte 0 followed by the payload (≤ 7 bytes); the STM32 answers with ACK/NAK 0x3FF echoing the sequence number and carrying up to 5 bytes of result data. The low byte of each `0x2xx` ID is the former bridge type code, so the arm and exhaust documents keep their code tables (payload detail for 0x221–0x225 is owned by [[../05-Subsystems/02-Robotic-Arm|Robotic Arm]] §8.2, for 0x260–0x262 by [[../05-Subsystems/05-Exhaust-Fume-Management|Exhaust & Fume Management]] §3.4). Dispensing (0x230–0x239), the LED ring (0x220), the buzzer (0x226), DU_STATUS (0x311) and DU_ACK (0x3FE) are not bus messages: they are DU-local frames on the RV1106 ↔ DU STM32 host link, terminated on the DU STM32 and never transmitted on CAN (§7.4); [[../05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]] keeps the same command names. Faults are reported in STATUS `error_code` (codes in [[05-MCU-Functional-Specification|MCU Functional Specification]] §7.2); there is no separate FAULT message. There is no temperature loop in Epicura: the AP sends HEAT_SET_TEMP and the heating unit regulates.

| CAN ID | Message | Direction | DLC | Payload |
|--------|---------|-----------|-----|---------|
| 0x001 | E_STOP | any → all | 2 | src_node (uint8: 1=HEAT, 2=STIR, 3=AP), reason_code (uint8); no ACK, acted on by every node |
| 0x010 | HB_AP | AP → all | 5 | seq (uint8), uptime_ms (uint32 LE); every 2 s |
| 0x100 | HEAT_SET_TEMP | AP → HEAT | 4 | target_dC (int16, 0.1 °C), ramp (uint8, °C/s), max_power_pct (uint8); temperature mode, re-sent at 2 Hz as keep-alive |
| 0x101 | HEAT_ON_OFF | AP or STIR → HEAT | 1 | 0 = off, 1 = on (the STM32 only ever sends 0) |
| 0x102 | HEAT_QUERY | AP → HEAT | 0 | — |
| 0x103 | HEAT_SET_POWER | AP → HEAT | 2 | power_pct (uint8, 0–100), ramp (uint8, %/s); power mode for sear/boil stages, re-sent at 2 Hz as keep-alive |
| 0x180 | HEAT_STATUS | HEAT → all | 8 | power_pct, surface_temp_dC (int16, 0.1 °C, unit's centre sensor), element_temp (int8 °C), pot_detected, fault_flags (uint16), reserved; 10 Hz |
| 0x181 | HEAT_FAULT | HEAT → all | 4 | fault_code (uint16), detail (uint16) |
| 0x182 | HEAT_ACK | HEAT → AP | 3 | cmd_id (uint16), result |
| 0x202 | SET_STIR | AP → STIR | 5 | seq, pattern (uint8), speed_rpm (uint16), direction (uint8: 0=CW, 1=CCW) |
| 0x221 | SET_SPEED | AP → STIR | 4 | seq, speed_rpm (uint16), direction — direct arm override |
| 0x222 | ARM_STOP | AP → STIR | 1 | seq (stop with decel ramp) |
| 0x223 | ARM_HOME | AP → STIR | 1 | seq |
| 0x224 | ARM_STATUS | AP → STIR | 1 | seq → ACK data: status_byte, current_rpm (uint16), position (uint16) |
| 0x225 | SET_RAMP | AP → STIR | 3 | seq, accel_limit (uint16, RPM/s) |
| 0x260 | SET_EXHAUST | AP → STIR | 2 | seq, duty_pct (uint8, 0–100) — manual fan duty |
| 0x261 | GET_EXHAUST | AP → STIR | 1 | seq → ACK data: duty_pct, rpm1 (uint16), rpm2 (uint16) |
| 0x262 | EXHAUST_AUTO | AP → STIR | 2 | seq, stage_id (uint8) — fan profile for the cooking stage |
| 0x310 | TELEMETRY | STIR → AP | 8 | motor_rpm (uint16), motor_current_dA (int16, 0.1 A, from the CAN servo), safety_state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok), error_code, seq; 20 Hz unsolicited |
| 0x312 | STATUS | STIR → AP | 8 | safety_state, error_code, flags (uint16), fault_detail (uint32, fault-specific, e.g. servo current for STIR_STALL; carries no battery data — the pack is on the DU); on change. error_code per MCU Functional Specification §7.2: 0x01–0x05, 0x10 STIR_STALL, 0x15 STIR_CAN_FAULT, 0x17 DU_UNDOCKED (Info: DOCK_SENSE_B open → safe hold), 0x20; 0x11–0x14, 0x16 POWER_FAIL and 0x21 I2C_NACK retired |
| 0x3FF | ACK / NAK | STIR → AP | 3–8 | seq, cmd_type (low byte of the command ID), result_code, data[0..4] |
| 0x7E0 | FW_UPDATE_REQ | AP → STIR | 7 | seq, op (uint8: ERASE / WRITE / VERIFY / BOOT), data[0..4] (address / image bytes / CRC); update mode only, lowest priority |
| 0x7E8 | FW_UPDATE_RSP | STIR → AP | 7 | seq, op, result (uint8), data[0..3]; update mode only, lowest priority |

### 7.3 Protocol Details

- **Physical:** CAN 2.0B, 500 kbps, isolated bus domain (5V_ISO and GND_ISO from the B0505S-1WR3 on the Cooking Surface Controller). One isolated transceiver on this bus, ISO1050DUB #1 on the CSC (CSC STM32 node); the DU STM32 node on the Unified PCB v5.0 is a non-isolated SN65HVD230 referenced to the DU logic ground, to which GND_ISO is tied at dock pad 5 (pad 6, 5V_ISO, is reserved). Terminations: 120 Ω on the CSC at J_CAN_HEAT and 120 Ω inside the heating unit; the bus crosses the dock on J_DOCK pins 3–5 (CAN_H, CAN_L, GND_ISO) and the dock → Unified PCB run is an unterminated stub ≤ 30 cm. Shielded twisted pair ≤ 1 m to the heating unit. Lifting the DU opens the bus and DOCK_24V at the same instant. The stir-motor bus (FDCAN2, ISO1050DUB #3 + B0505S #2 on the CSC, 1 Mbps, J_CAN_STIR → J_SU) is a second isolated domain (5V_ISO2 / GND_SU, the ground of the Stirring Unit's own LRS-75-24 #2, never bonded to the CS ground), electrically separate and STM32-private.
- **AP side (RV1106):** no CAN driver. The `link` thread (SCHED_FIFO) owns `/dev/ttyS2` (UART2, 921,600 baud) and the COBS/CRC-16 codec of §7.4; it hands bus frames to the `heat` thread and the engine exactly as the former raw socket did, and DU-local replies (0x3FE, 0x311) to the `dispense` thread and the dock/battery monitor. The DU STM32's FDCAN1 hardware filters accept `0x00x`, `0x01x`, `0x18x`, `0x3xx` and `0x7E8` for forwarding up the link; its RX FIFO and USART1 DMA keep end-to-end latency ≤ 5 ms. DU_STATUS flags (docked, dock_power, can_bus_ok) let the AP tell a lifted unit or a mains outage from a CSC STM32 fault when TELEMETRY stops.
- **DU STM32 side:** Link/Gateway task; frames from the link with a DU-local ID are executed locally, every other ID is transmitted on FDCAN1 unchanged; bus frames that pass the AP filter set are encoded onto the link. It adds nothing and changes nothing.
- **CSC STM32 side:** FDCAN1 classic frames, RX FIFO interrupt → command parser in the CAN comms task (20 Hz), which also transmits TELEMETRY from the motor-control and safety task data.
- **Timeouts:** ACK 500 ms, 3 retries; E_STOP needs no ACK. HB_AP every 2 s, originated by the RV1106 and forwarded; the CSC STM32 enters its safe state after 5 s without it, and the DU STM32 drops the dispensers after the same 5 s. The AP treats TELEMETRY older than 300 ms as CSC STM32 loss (or, with DOCK_PWR_OK inactive while docked, as a mains outage — state machine §5) and HEAT_STATUS older than 500 ms as module loss: HEAT_ON_OFF 0 and pause. The module drops to zero power 1 s after the last HEAT_SET_TEMP / HEAT_SET_POWER refresh (AP sends at 2 Hz).
- **Dock safe hold:** DOCK_SENSE_B open (DU lifted) puts the CSC STM32 into safe hold at once — HEAT_ON_OFF 0, stir disable, K_SU and Q_DOCK off, STATUS 0x17 DU_UNDOCKED — without an E_STOP; it returns to NORMAL when DOCK_SENSE_B is low again and HB_AP returns.
- **Bus load:** 20 Hz TELEMETRY + 2 Hz HEAT_SET_TEMP + 10 Hz HEAT_STATUS + sporadic commands ≈ 5 kbit/s, about 1 % of 500 kbps.
- **Firmware update, CSC STM32 (CAN bootloader):** there is no UART between the units. The AP streams the CSC image through the DU gateway onto the isolated bus with FW_UPDATE_REQ 0x7E0 / FW_UPDATE_RSP 0x7E8 (ERASE / WRITE / VERIFY / BOOT, 5 data bytes per frame) to an in-application OpenBLT-style bootloader on the CSC; update mode only and lowest priority, so E_STOP, HB_AP and heater frames always win arbitration. USB-C DFU on the CSC is the bench fallback, SWD the factory path. USART2 on the CSC is a local debug console (J_DBG) only; no runtime traffic.
- **Firmware update, DU STM32 (system bootloader):** the swupdate handler on the RV1106 drives BOOT0 high (GPIO 32), pulses NRST (GPIO 38) and talks the ST system-bootloader protocol on the same USART1 host link, verifies the image, releases BOOT0 and resets; the `link` thread is paused meanwhile and dispensing is refused. No in-application bootloader on the DU; J_SWD is the bench path.

### 7.4 Host Link (RV1106 ↔ DU STM32)

The host link is the only connection between the RV1106 and the rest of the machine: UART2 on the Pico Zero header (pins 8 TX / 10 RX, `/dev/ttyS2`) to USART1 on the DU STM32 (PA10 RX / PA9 TX), 921,600 baud 8N1, 33 R series resistors, both on the 3.3 V logic domain of the Unified PCB v5.0. The same UART is the ST system-bootloader port for flashing the DU STM32 (BOOT0 on GPIO 32, NRST on GPIO 38).

- **Framing:** every frame is CAN-shaped — `id` (uint16 LE, 11-bit CAN ID), `dlc` (uint8), `data[0..dlc-1]` (≤ 8 bytes), `crc16` (CRC-16/CCITT-FALSE over id..data) — COBS-encoded and terminated with 0x00; at most 14 bytes on the wire. 921,600 baud carries ≈ 6,500 frames/s; the bus produces ≈ 35 frames/s, so the link is never the bottleneck. A CRC or COBS error drops the frame and re-synchronises on the next 0x00; commands rely on the existing ACK/retry rule.
- **Routing:** frames whose ID is in the DU-local block below are executed on the DU STM32 and never transmitted on CAN. Every other frame from the RV1106 (0x001, 0x010, 0x100–0x103, 0x202, 0x221–0x225, 0x260–0x262, 0x7E0) is transmitted on FDCAN1 unchanged. Bus frames that match the AP filter set (0x00x, 0x01x, 0x18x, 0x3xx, 0x7E8) are forwarded up the link unchanged. The gateway adds nothing and changes nothing; the CAN ID map in §7.2 stays the single source of truth for bus identifiers.
- **Host loss:** HB_AP (0x010) is originated by the RV1106 every 2 s and forwarded. If the DU STM32 sees no HB_AP for 5 s it drops the dispensers (6V_DSP off, PCA9685 OE high, pumps off) and the LED ring, and keeps sending DU_STATUS. The bus loses HB_AP at the same moment, so the CSC STM32 enters its safe state on its existing 5 s rule and the heater stops on its 1 s keep-alive. The DU STM32 has no safety authority: it never originates HEAT_ON_OFF or E_STOP, it only forwards the RV1106's.
- **Lift:** lifting the DU opens the bus; FDCAN1 goes bus-off, DU_STATUS reports can_bus_ok = 0 and docked = 0 within one frame, and the controller recovers from bus-off automatically when re-docked. The RV1106 state machine logic is unchanged but reads docked / dock_power from DU_STATUS instead of its own GPIOs.

DU-local messages (terminated on the DU STM32). They revive the CAN-era codes so the subsystem documents keep their numbers; command frames carry `seq` in byte 0 like every bus command:

| ID | Message | Direction | DLC | Payload |
|----|---------|-----------|-----|---------|
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
| 0x311 | DU_STATUS | DU → AP | 8 | batt_mV (uint16), batt_mA (int16), soc_pct, flags (bit0 docked = DOCK_SENSE_A low, bit1 dock_power = DOCK_PWR_OK, bit2 charging, bit3 charge_done, bit4 dsp_rail_on, bit5 dsp_busy, bit6 can_bus_ok, bit7 sld_low — a tank low or absent), error_code, seq; 1 Hz and on any flag change |
| 0x3FE | DU_ACK / NAK | DU → AP | 3–8 | seq, cmd_type (low byte of the command ID), result_code, data[0..4] |

0x234 is reserved. 0x3FF stays the CSC STM32's ACK; the RV1106 tells the two apart by ID. DU error codes (DSB_STALL, SLD_LOW_LEVEL, SLD_DISPENSE_ERROR, SLD_TANK_ABSENT, NOT_DOCKED, I2C_NACK) are listed in [[05-MCU-Functional-Specification|MCU Functional Specification]] §10.

---

## 8. Real-Time Requirements

| Task | Frequency | Deadline | Processor | Priority |
|------|-----------|----------|-----------|----------|
| Heater setpoint keep-alive (`heat` thread) | 2 Hz | 500 ms | RV1106 | High (SCHED_FIFO) |
| Motor control (CAN servo on FDCAN2) | 50 Hz | 20 ms | STM32 (CSC) | Highest |
| Safety monitor check (incl. DOCK_SENSE_B) | 10 Hz | 100 ms | STM32 (CSC) | Highest |
| CAN comms handler (FDCAN1) | 20 Hz | 50 ms | STM32 (CSC) | Medium |
| Thermal/Fan (fans, optional tach, pot reed) | 1 Hz | 1 s | STM32 (CSC) | Low |
| Link thread (`/dev/ttyS2` RX/TX, heartbeat) | event / 0.5 Hz | 50 ms | RV1106 | High (SCHED_FIFO) |
| Link/Gateway task (USART1 ↔ FDCAN1 routing, HB_AP watchdog) | event | 5 ms | STM32 (DU) | High |
| Dispense task (I2C1 servo / pump / SLD tach loop) | 50 Hz while active | 20 ms | STM32 (DU) | Medium |
| Dispense client (queue → 0x23x frames, 0x3FE wait) | event | — | RV1106 | Medium (SCHED_OTHER) |
| Monitor task (INA219 #2, charger, dock EXTI → DU_STATUS) | 1 Hz + EXTI | 1 s | STM32 (DU) | Low |
| CV inference | 2 Hz | 500 ms | RV1106 | Medium |
| UI update (LVGL tick) | 20 Hz | 50 ms | RV1106 | Medium |
| Recipe engine tick | 1 Hz | 1 s | RV1106 | Low |
| Session checkpoint (SQLite) | 0.1 Hz | 10 s | RV1106 | Low |
| Cloud sync (MQTT) | 0.1 Hz | 10 s | RV1106 | Low |
| Phone stream (VENC) | 15 fps | on demand | RV1106 hardware | Low |

The RV1106 has one core. The `link` and `heat` threads run at real-time priority so heartbeats and the 2 Hz setpoint keep-alive are never starved by UI rendering or a sync burst; everything else is `SCHED_OTHER`, including the `dispense` client. The 50 Hz servo loop itself now runs on the DU STM32, so a busy RV1106 can only delay a dispense command, never a servo tick. Safety does not depend on any of this: the CSC STM32 cuts heat if heartbeats stop, the heating unit drops to zero power when the keep-alive stops arriving, and the DU STM32 drops the dispensers on the same heartbeat loss.

---

## 9. Error Handling

### 9.1 Common Errors

| Error | Detection | Severity | Recovery |
|-------|-----------|----------|----------|
| Sensor failure (temp / SLD) | Module sensor fault flag in HEAT_STATUS; SLD tank absent or pump tach silent (DU STM32 `Dispense` task → NAK / DU_STATUS error_code) | CRITICAL | Fall back to timer-based cooking, alert user |
| DU link lost | No DU_STATUS (0x311) on the host link for 3 s | CRITICAL | Pause (same handling as CSC STM32 loss); the DU STM32 has already dropped the dispensers on its own HB_AP watchdog; `link` thread re-syncs COBS framing and retries |
| Unit lifted | DOCK_SENSE_A high, reported by the DU STM32 in DU_STATUS (DOCK_SENSE_B open on the CSC STM32) | WARNING | Pause (UNIT_LIFTED); heater stops ≤ 1 s by keep-alive loss, STM32 safe hold; resume by user tap after re-docking |
| Communication timeout | No ACK within 500 ms x 3 retries | WARNING → CRITICAL | Retry 3x, then pause cooking, alert user |
| Over-temperature | surface_temp > 220C (CRITICAL), > 230C (E_STOP; unit ceiling 200C) | CRITICAL → E_STOP | Immediately cut heater, stop motor, alarm |
| Motor stall | Overcurrent on motor driver | WARNING → CRITICAL | Stop motor, alert user, suggest pot check |
| CV failure | Camera disconnect, ISP timeout or rknn error | WARNING | Fall back to timer + temp thresholds |
| Memory pressure | Free RAM < 32 MB | WARNING | Kill `rtsp-stream`, drop LCD preview, log |
| Power anomaly | DOCK_PWR_OK inactive while docked (mains outage), or DU pack < 6.4 V — both from DU_STATUS (DU STM32 reads DOCK_PWR_OK and INA219 #2) | WARNING → CRITICAL | Pause on battery (auto-resume when TELEMETRY returns); warning banner at 6.4 V, checkpoint to SQLite and halt at 6.2 V |
| Recipe parse error | Invalid YAML or missing fields | WARNING | Reject recipe, notify user, suggest re-download |

### 9.2 Fallback Strategies

1. **CV fallback:** If camera or model fails, every recipe stage includes `duration_seconds` and `temp_target` as backup transition criteria
2. **Communication fallback:** the heating unit drops to zero power 1 s after the last HEAT_SET_TEMP / HEAT_SET_POWER refresh; the STM32 holds the last stir state for up to 30 seconds, then enters safe shutdown, forces HEAT_ON_OFF = 0 and disables the stir motor
3. **Power loss recovery:** `session_checkpoint` row in SQLite (WAL, `synchronous=NORMAL`) is rewritten every 10 seconds; on restart, offer to resume or discard
4. **Process failure:** `epicurad` is supervised by busybox init with a 10 s kernel watchdog; a crash restarts the process, the heater drops to zero power within 1 s (no setpoint refresh), the CSC STM32 holds the stir state meanwhile and the DU STM32 drops the dispensers 5 s after the last HB_AP
6. **Power loss:** the DU's 2S pack is the RV1106's primary supply, so `epicurad`, the DU STM32, the LCD and the dispensers keep running when mains fails; the heater, stir motor and CSC STM32 are down with the base. The DU STM32 reports DOCK_PWR_OK dropping in DU_STATUS (confirmed by the 300 ms TELEMETRY timeout), the engine checkpoints to SQLite and pauses (state machine §5); when TELEMETRY returns (the STM32 reboots < 1 s after mains comes back) the session auto-resumes if the pause was under 5 min. At 6.2 V pack voltage `epicurad` checkpoints, syncs and halts; RECOVERING on the next boot
5. **Streaming failure:** Live view is best-effort. Any encoder or RTSP error tears the stream down and never affects cooking
7. **Unit lifted:** DOCK_SENSE_A high (DU_STATUS docked = 0, can_bus_ok = 0) → PAUSED (UNIT_LIFTED). The heater drops to zero ≤ 1 s after the last keep-alive, the CSC STM32 holds safe on DOCK_SENSE_B (HEAT_ON_OFF 0, stir and dock power off, STATUS DU_UNDOCKED). Resume only by user tap after re-docking; same 30 min food-safety ceiling

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
| 3.2 | 2026-11-04 | Manas Pradhan | MCU changed to STM32G0B1RE (Cortex-M0+ @ 64 MHz, 144 KB SRAM, 2x FDCAN); no functional change to tasks, bus roles or the CAN ID map |
| 3.1 | 2026-11-04 | Manas Pradhan | Temperature loop removed from Epicura: the induction module regulates on its own sensor; `heat` thread now sends HEAT_SET_TEMP (0x100) / HEAT_SET_POWER (0x103) at 2 Hz and relays surface_temp from HEAT_STATUS; TELEMETRY drops ir_temp (motor current, battery flags added); stirring motor is a CAN servo on the STM32's private FDCAN2 bus; battery-backed power-loss fallback added; §5.3.1, §7 and §8 updated |
| 3.0 | 2026-11-04 | Manas Pradhan | Isolated CAN bus now connects the RV1106 (MCP2518FD on SPI0 CS1, SocketCAN), the STM32 (FDCAN1) and the induction surface MCU; UART2 kept as service link only (flashing/debug); temperature PID moved from the STM32 to the RV1106 `heat` thread, AP commands HEAT_SET_POWER directly, STM32 keeps HEAT_ON_OFF=0 / E_STOP / relay authority; §7 rewritten as the CAN ID map (0x001 E_STOP, 0x010 HB_AP, 0x1xx heater, 0x2xx commands, 0x3xx reports); SET_TEMP retired |
| 3.3 | 2026-11-04 | Manas Pradhan | Three-unit architecture: STM32 moves to the Cooking Surface Controller (CSC) in the base (stir motor, heater off-switch, relay, E-stop, fans, dock power; tasks = CAN Comms, Motor Control, Safety Monitor, Thermal/Fan); RV1106 on the Unified PCB v4.0 in the lift-off Dispensing Unit (battery primary) owns dispensing (new `dispense` thread over I2C3, §5.7), LED ring and buzzer PWM, battery/dock monitoring; isolated CAN crosses the dock (J_DOCK), UART service link removed, STM32 update over CAN (0x7E0/0x7E8); §7.2: 0x220, 0x230–0x239 and 0x311 removed, 0x260–0x262 exhaust and 0x7E0/0x7E8 added, TELEMETRY flags and STATUS codes updated (0x17 DU_UNDOCKED); DOCK_SENSE_B safe hold; power-loss and unit-lifted fallbacks |
| 3.4 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged — §7.2 block `0x1xx` renamed heating unit, HEAT_STATUS field `coil_temp` → `element_temp` (same byte), surface_temp is the unit's centre (pot-bottom) sensor; heater wording in §1, §5.3.1, §7, §8 updated; `PAUSE_INDUCTION_ERROR` → `PAUSE_HEATER_ERROR` |
| 3.6 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: a second STM32G0B1RE (the DU STM32) on the Unified PCB v5.0 owns dispensing, LED ring, buzzer, battery/dock monitoring and the DU's CAN node (FDCAN1 + ISO1050DUB #2); the MCP2518FD / SocketCAN node is removed and the RV1106 reaches the bus through the DU STM32 as a transparent gateway over a UART host link (UART2 ↔ USART1, 921,600 baud, COBS + CRC-16, new §7.4 with the DU-local block 0x220, 0x226, 0x230–0x239, 0x311 DU_STATUS, 0x3FE DU_ACK); CAN ID map §7.2 unchanged, AP node name unchanged; `can` thread → `link` thread, `dispense` thread becomes a client; firmware tree builds `csc` and `du` images; DU STM32 flashed via the ST system bootloader (BOOT0/NRST on GPIO 32/38); DU_LINK_LOST fault; §1–§5.7, §7, §8, §9 updated |
| 3.5 | 2026-11-04 | Manas Pradhan | Heating unit referenced to the Philips OneChef NX5300/00 (80–200 °C centre-sensor range): absolute over-temperature limits in §5 state table and §8 fault table re-based 260 °C → 220 °C CRITICAL, 230 °C E_STOP (see [[05-MCU-Functional-Specification]] v1.3) |
| 3.7 | 2026-11-04 | Manas Pradhan | Stirring Unit on its own PSU (CSC v1.3): the stir-motor bus FDCAN2 is now the CSC's second isolated CAN port (ISO1050DUB #3 + B0505S #2, SU domain 5V_ISO2 / GND_SU, SN65HVD230 removed); Q_STIR replaced by the pilot relay K_SU on the AC input of LRS-75-24 #2 in the responsibility table, SAFE_HOLD row, dock safe hold, E_STOP actions and §7 bus description; CAN ID map unchanged |
| 3.8 | 2026-11-04 | Manas Pradhan | CAN isolation on the CSC only: the DU STM32's node on the Unified PCB v5.1 is a non-isolated SN65HVD230 (ISO1050DUB #2 removed), GND_ISO tied to the DU logic ground at dock pad 5, pad 6 (5V_ISO) reserved; the CSC's two ISO1050 ports are signal-reference barriers, the heating unit's CAN port must be SELV; §1 IPC row, §7 intro, §7.1 AP row, §7.3 physical bullet; CAN ID map and §7.4 unchanged |
| 3.9 | 2026-11-05 | Manas Pradhan | Robot-mop SLD on the DU STM32: open-loop liquid metering by pump Hall tach pulses × cal_ul (drawer tanks with float / presence Hall switches, pumps in the body, check-valve nozzles; solenoids, load cells, NAU7802 and TCA9543A removed); host-link block: DISPENSE_SLD carries target_ml and returns actual_ml + primed_ml, 0x233 SLD_PRIME (new), 0x235 QUERY_WEIGHT → QUERY_SLD, 0x237 TARE → SLD_CAL, DU_STATUS bit7 sld_low; SLD_LOAD_CELL_DRIFT → SLD_TANK_ABSENT, NOT_DOCKED added; §3 diagram, responsibility table, §4.4, §5.7 (dsp_op_t), §6 loading step, §7.4 and §9.1 updated |
