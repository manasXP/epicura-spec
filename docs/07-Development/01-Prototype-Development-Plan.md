---
created: 2026-02-15
modified: 2026-11-04
version: 1.1
status: Draft
---

# Prototype Development Plan

## 1. Overview

This document outlines the comprehensive plan for building a functional Epicura prototype capable of cooking 3-5 Indian recipes autonomously. The prototype will validate core subsystems: induction heating, robotic stirring, computer vision, and recipe state machine execution.

**Target Timeline:** 20-24 weeks
**Goal:** Working prototype demonstrating autonomous one-pot cooking with CV-guided stage detection
**Budget:** $1,500-2,500 (including components, tools, and miscellaneous)

## 2. Project Links

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[02-Controller-Software-Architecture|Software Architecture]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]

---

## 3. Development Phases

### 3.1 Phase 1: Hardware Setup & Bring-up (Weeks 1-4)

#### 3.1.1 Objectives
- Set up Luckfox Pico Zero (RV1106G3) with a Buildroot Linux image
- Set up STM32G474RE with FreeRTOS
- Establish RV1106-to-STM32 UART communication link
- Validate basic I/O and power supply

#### 3.1.2 Tasks

**Week 1: RV1106 Bring-up**
- [ ] Acquire Luckfox Pico Zero + SC3336 camera module + 4" ST7796S SPI LCD (FT6336 touch)
- [ ] Build Buildroot image from the Luckfox SDK inside the `luckfoxtech/luckfox_pico:1.0` Docker image (kernel 5.10, busybox init, squashfs rootfs; packages: sqlite, libyaml, cjson, libmosquitto, libcurl, mbedtls, lvgl, swupdate, wpa_supplicant, bluez5, rockit, rknn)
- [ ] Flash image to eMMC over USB-C, verify boot
- [ ] Establish SSH access over Wi-Fi (no Ethernet on the Pico Zero); UART0 debug console as fallback
- [ ] Test GPIO, I2C3, SPI0, UART2 from Linux userspace
- [ ] Bring up the 4" LCD on fbtft (SPI0, 50 MHz, DMA) and FT6336 touch on I2C3 (evdev)
- [ ] Verify SC3336 on MIPI CSI through rockit VI/ISP (1280x720 @ 30 fps)

**Week 2: STM32 Bring-up**
- [ ] Acquire NUCLEO-G474RE development board
- [ ] Install STM32CubeIDE and STM32CubeMX
- [ ] Create FreeRTOS project with basic task structure
- [ ] Test GPIO output (LED blink)
- [ ] Test UART communication (serial terminal echo)
- [ ] Test CAN bus (receive induction module status)
- [ ] Test PWM output (servo signal generation)

**Week 3: Inter-Processor Communication**
- [ ] Wire UART between RV1106 (UART2: header pins 8 TX / 10 RX) and STM32 (USART2: PA2/PA3), 1,000,000 baud 8N1, 3.3 V; on the Nucleo, open the solder bridges so PA2/PA3 reach the CN10 header instead of the ST-Link VCP
- [ ] Define message protocol (SOF 0x7E, byte stuffing, msg ID, type, payload, CRC-16)
- [ ] Implement protocol on STM32 (C, interrupt-driven UART)
- [ ] Implement protocol on RV1106 (C, `epicurad` bridge thread, termios at 1 Mbps)
- [ ] Test bidirectional echo: RV1106 sends command, STM32 responds
- [ ] Measure round-trip latency (target: < 10 ms)

**Week 4: Power Supply & Integration**
- [ ] Use bench PSU initially (5V over USB-C for the Pico Zero (~1 W), 6V for servos, 3.3V for STM32)
- [ ] Design power distribution board (or use prototype PSU module)
- [ ] Wire all subsystems to common power rail
- [ ] Verify power consumption under load
- [ ] Stress test: run RV1106 + STM32 + servo simultaneously for 1 hour

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| RV1106 running Buildroot Linux | Boot < 30s, SSH accessible, ISP camera frames, LVGL test screen on the 4" LCD |
| STM32 running FreeRTOS | 4+ tasks running, UART responsive |
| RV1106-STM32 UART link | Bidirectional messaging, < 10 ms round-trip |
| Power distribution | All subsystems powered, no brownouts under load |

**Risks:**
- Luckfox SDK / Buildroot build issues → Fallback: start from the prebuilt Luckfox Pico Zero image and add packages incrementally
- UART reliability → Fallback: add hardware flow control (RTS/CTS)

---

### 3.2 Phase 2: Induction Integration (Weeks 5-7)

#### 3.2.1 Objectives
- Integrate and control a commercial induction hob
- Implement PID temperature controller on STM32
- Validate temperature accuracy and step response

#### 3.2.2 Tasks

**Week 5: Microwave Surface Module Setup**
- [ ] Acquire commercial microwave induction surface with CAN bus port
- [ ] Review module CAN protocol documentation
- [ ] Wire CAN bus: module CAN port ↔ STM32 FDCAN1 (PB8/PB9) + transceiver + 120Ω termination
- [ ] Verify CAN communication: send HEAT_QUERY, receive HEAT_STATUS
- [ ] Wire safety relay on AC mains to module (STM32 GPIO control)

**Week 6: CAN Power Control Integration**
- [ ] Implement CAN power level commands (0-100%) from STM32
- [ ] Verify all power levels (warm, simmer, medium, boil, sear)
- [ ] Measure power delivery at different CAN power levels (25%, 50%, 75%, 100%)
- [ ] Log temperature ramp rates for water (1L, 2L, 3L)
- [ ] Test safety relay disconnect and CAN off command

**Week 7: PID Controller & Sensors**
- [ ] Wire MLX90614 IR thermometer to STM32 I2C bus
- [ ] Verify CAN bus coil temperature reporting from induction module
- [ ] Calibrate MLX90614 against reference thermometer (0-250°C range)
- [ ] Implement PID controller on STM32 (FreeRTOS task, 10 Hz loop)
- [ ] Tune PID gains: step response test (ambient → 100°C, 100°C → simmer at 85°C)
- [ ] Validate accuracy: ±10°C at target (prototype), ±5°C goal (optimized)

```
┌─────────────────────────────────────────────────────────┐
│              Induction Control Loop                     │
│                                                         │
│  Target Temp ──► PID ──► CAN Power ──► Induction Module │
│       │          ▲           Cmd            │           │
│       │          │                          ▼           │
│       │     Error Calc              Induction Coil      │
│       │          │                         │            │
│       │          │                         ▼            │
│       │     ┌────────────┐            ┌────────┐        │
│       │     │ MLX90614   │◄───────────│  Pot   │        │
│       └────►│ IR Sensor  │  (infrared)│        │        │
│             └────────────┘            └────────┘        │
│                  ▲                         │            │
│             ┌────────────┐                 │            │
│             │ CAN Coil   │◄────────────────┘            │
│             │Temp (CAN)  │  (CAN HEAT_STATUS)           │
│             └────────────┘                              │
└─────────────────────────────────────────────────────────┘
```

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| Induction control | STM32 can set power 0-100% in 10% steps |
| Temperature sensing | MLX90614 reads pot surface ±5°C of reference |
| PID controller | Reach 100°C in < 8 min (1L water), hold ±10°C |
| Safety cutoff | Auto-off at 200°C coil temp or 240°C thermal fuse |

---

### 3.3 Phase 3: Arm & Sensors (Weeks 8-10)

#### 3.3.1 Objectives
- Build and mount the servo stirring arm
- Implement stirring patterns

#### 3.3.2 Tasks

**Week 8: Servo Arm Assembly**
- [ ] Acquire 24V BLDC motor (30-50 kg.cm, integrated ESC)
- [ ] Design mounting bracket (3D print, PETG or aluminum)
- [ ] Fabricate stainless steel shaft (8mm diameter, 250mm length)
- [ ] Attach food-grade silicone paddle to shaft end
- [ ] Mount servo + shaft assembly above pot center
- [ ] Wire servo to STM32 PWM output (TIM1 or TIM2)

**Week 9: Stirring Patterns**
- [ ] Implement 5 stirring patterns on STM32 (BLDC motor speed control):
  - Circular (continuous rotation, adjustable speed)
  - Back-and-forth (180° sweep)
  - Scraping (edge-following pattern)
  - Folding (slow, deep strokes for delicate mixing)
  - Pulse (intermittent stir, e.g., 5s on / 30s off)
- [ ] Add speed control: 10-60 RPM range
- [ ] Add torque monitoring: detect obstruction via servo current
- [ ] Test all patterns with water, then with thick dal consistency

```
┌──────────────────────────────────────────┐
│          Arm & Sensor Assembly           │
│                                          │
│         ┌──────┐                         │
│         │BLDC  │ 24V, integrated ESC     │
│         │Motor │ (30-50 kg.cm)           │
│         └──┬───┘                         │
│            │ Shaft (SS, 8mm)             │
│            │                             │
│            ▼                             │
│     ┌──────────────┐                     │
│     │   Paddle     │ (Silicone)          │
│     └──────────────┘                     │
│            │                             │
│     ┌──────────────┐   ┌─────────────┐   │
│     │     Pot      │   │ MLX90614    │   │
│     │  (3-4L SS)   │   │ IR Sensor   │   │
│     └──────┬───────┘   └─────────────┘   │
│            │                             │
│  ┌─────┐┌─────┐┌─────┐┌─────┐            │
│  │LC 1 ││LC 2 ││LC 3 ││LC 4 │            │
│  └──┬──┘└──┬──┘└──┬──┘└──┬──┘            │
│     └───┬──┘      └───┬──┘               │
│         └──────┬──────┘                  │
│                ▼                         │
│          ┌──────────┐                    │
│          │  HX711   │ 24-bit ADC         │
│          └──────────┘                    │
└──────────────────────────────────────────┘
```

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| Servo arm mounted | Stable mounting, paddle reaches pot bottom |
| 5 stirring patterns | All patterns functional, speed adjustable |
| Torque limiting | Servo stalls safely at obstruction |

---

### 3.4 Phase 4: Vision & Computer Vision (Weeks 11-14)

#### 3.4.1 Objectives
- Set up overhead camera with controlled illumination
- Build image preprocessing pipeline
- Train and deploy food stage classification model

#### 3.4.2 Tasks

**Week 11: Camera Setup**
- [ ] Mount SC3336 camera module above pot (overhead view)
- [ ] Install LED ring (WS2812B, 12-LED NeoPixel) around camera; wire data to STM32 PB14 via 74AHCT1G125 and implement SET_LED (0x20) over the bridge
- [ ] Configure rockit VI/ISP on the RV1106 for 1280x720 @ 30fps capture (main path NV12) plus a 224x224 RGB888 self-path
- [ ] ISP tuning check: load the SC3336 tuning file from the Luckfox SDK; verify AWB/AE, dehaze and 3DNR behaviour over a steaming pot
- [ ] Test image quality under LED illumination (consistent lighting)
- [ ] Capture test images at various cooking stages

**Week 12: ISP Pipeline & Preview**
- [ ] Configure the ISP hardware pipeline on the RV1106 (no CPU image processing):
  - Dehaze and 2D/3D noise reduction (steam)
  - Lens shading correction and sharpening
  - AWB/AE locked for consistent colour under the LED ring
  - Self-path crop/scale to the pot ROI at 224x224 RGB888
- [ ] LCD "view pot" preview: ISP main path → RGA scale to 480x320 → framebuffer, ≤ 10 fps, on demand only
- [ ] Benchmark: self-path frame delivered to the NPU with zero CPU copies; CPU load < 10% during capture

**Week 13: Training Data Collection**
- [ ] Cook 20+ dishes manually, capturing images every 10 seconds
- [ ] Label images by cooking stage:
  - Raw ingredients
  - Oil heating / tempering
  - Sauteing (browning)
  - Liquid added (boiling)
  - Simmering
  - Thickening
  - Done / ready to serve
- [ ] Augment dataset: rotation, brightness, contrast variations
- [ ] Target: 2,000+ labeled images across 5-7 stage classes

**Week 14: Model Training & Deployment**
- [ ] Transfer learning: MobileNetV2 pretrained on ImageNet
- [ ] Fine-tune on cooking stage dataset (TensorFlow/Keras, on PC)
- [ ] RKNN model conversion: export TFLite/ONNX, convert to INT8 `.rknn` with RKNN-Toolkit2 using a calibration image set
- [ ] Deploy on the RV1106 NPU (`/oem/models/stage_mnv2_int8.rknn`): inference time target < 20 ms per frame at 2 Hz
- [ ] Validate accuracy: target > 85% on held-out test set (INT8 `.rknn` vs float model)
- [ ] Implement rule-based fallback (timer + temperature thresholds when confidence < 0.6)

```
┌─────────────────────────────────────────────────────┐
│              Vision Pipeline                        │
│                                                     │
│  SC3336 ──► ISP (hw) ──► NPU (RKNN) ──► Stage Label │
│  (720p)     dehaze/3DNR  (MobileNetV2   (7 classes) │
│                │         INT8, 2 Hz)      │         │
│                ▼                          ▼         │
│         Self-path 224x224        Recipe State       │
│         RGB888 (zero copy)       Machine Input      │
│         Main path → VENC / RGA                      │
│                │                                    │
│                ▼                                    │
│         Rule-Based Fallback                         │
│         (if model confidence < 60%)                 │
└─────────────────────────────────────────────────────┘
```

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| Camera + LED ring | Consistent overhead imaging, no shadows |
| ISP pipeline | Hardware dehaze/3DNR verified, 224x224 self-path to NPU with no CPU copies |
| Training dataset | 2,000+ labeled images, 5-7 stage classes |
| Deployed RKNN model | > 85% accuracy, < 20 ms inference on the RV1106 NPU |
| Rule-based fallback | Works when model confidence is low |

---

### 3.5 Phase 5: Recipe Engine & Dispensing (Weeks 15-17)

#### 3.5.1 Objectives
- Define recipe YAML format and implement state machine
- Build ingredient dispensing subsystems (ASD, CID, SLD)
- Validate end-to-end cooking of 3-5 Indian recipes

#### 3.5.2 Tasks

**Week 15: Recipe Format & State Machine**
- [ ] Define recipe YAML schema:
  ```yaml
  name: "Dal Tadka"
  servings: 2
  total_time_min: 25
  stages:
    - name: "Heat Oil"
      actions: [heat: {target: 180, mode: sear}]
      detect: {method: cv, class: oil_shimmer}
      timeout_sec: 180
    - name: "Add Tempering"
      actions: [dispense: {subsystem: "ASD", id: 1, weight_g: 5}]
      ...
  ```
- [ ] Implement state machine on the RV1106 (C, `epicurad` engine thread, libyaml):
  - Load recipe YAML
  - Execute stages sequentially
  - Transition on CV detection OR timeout OR weight confirmation
  - Send commands to STM32 via UART protocol
- [ ] Create recipe files for 5 target dishes

**Week 16: Dispensing Mechanism**
- [ ] Build ASD: 3 seasoning hoppers (3D printed PETG, 80 mL each) with SG90 servo gates
- [ ] Build CID: 2 slide-out trays (400 mL each) with 12V linear actuators and limit switches
- [ ] Build SLD: 2 liquid channels (peristaltic pumps + solenoid valves + silicone tubing)
- [ ] Install 2× SLD dedicated load cells (2 kg each) + HX711 under oil and water reservoirs
- [ ] Wire all dispensing actuators to STM32 (PWM + GPIO)
- [ ] Calibrate P-ASD dispensing: pulse duration per spice, verify pressure drop via ADS1015
- [ ] Calibrate SLD dispensing per channel: start pump, monitor individual reservoir weight loss, stop at target
- [ ] Test SLD low-level alert: verify alert fires when reservoir drops below threshold

```
┌──────────────────────────────────────────────────┐
│           Dispensing Subsystem Layout             │
│                                                  │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│   │  ASD-1  │  │  ASD-2  │  │  ASD-3  │         │
│   │(turmeric│  │ (chili  │  │ (salt/  │         │
│   │ powder) │  │ powder) │  │ masala) │         │
│   └────┬────┘  └────┬────┘  └────┬────┘         │
│        │SG90        │SG90        │SG90           │
│        ▼            ▼            ▼               │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─          │
│                                                  │
│   SLD-OIL ═══╗           ╔═══ SLD-WATER          │
│   [Pump]─[Sol]╚══►Pot◄══╝[Sol]─[Pump]           │
│                                                  │
│   ┌──────────────┐  ┌──────────────┐             │
│   │    CID-1     │  │    CID-2     │             │
│   │ (vegetables) │  │  (dal/rice)  │             │
│   │ [LinActuator]│  │ [LinActuator]│             │
│   └──────┬───────┘  └──────┬───────┘             │
│          ▼                 ▼                     │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─          │
│                  Pot Below                       │
└──────────────────────────────────────────────────┘
```

**Week 17: End-to-End Recipe Testing**
- [ ] Test Recipe 1: **Dal Tadka** (lentil curry with tempering)
- [ ] Test Recipe 2: **Jeera Rice** (cumin rice)
- [ ] Test Recipe 3: **Tomato Soup** (simple, CV-friendly color transitions)
- [ ] Test Recipe 4: **Khichdi** (rice + lentil, one-pot)
- [ ] Test Recipe 5: **Vegetable Curry** (mixed vegetables in gravy)
- [ ] Log results: timing, temperature accuracy, CV detections, taste evaluation
- [ ] Iterate on PID gains, stirring patterns, and dispensing calibration

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| Recipe YAML format | 5 recipes defined, schema validated |
| State machine | Executes recipes end-to-end, handles timeouts |
| ASD/CID/SLD subsystems | All actuators functional, no jamming |
| Pressure-verified dispensing (P-ASD) | ~±20% accuracy, pressure drop confirmed |
| 3-5 cooked recipes | Edible output, correct stage transitions |

---

### 3.6 Phase 6: UI & Companion App (Weeks 18-20)

#### 3.6.1 Objectives
- Build touchscreen UI on the RV1106 4" LCD with 5 core screens (LVGL)
- Build basic native companion mobile apps (iOS + Android)
- Connect app to the device through the cloud REST API and MQTT (no device-hosted API)

#### 3.6.2 Tasks

**Week 18: Touchscreen UI**
- [ ] Set up LVGL 9 on the RV1106 (fbtft framebuffer, evdev touch, 20 Hz tick, software rendering)
- [ ] Implement 5 core screens at 480x320:
  1. **Home:** Recipe selection grid with images
  2. **Recipe Detail:** Ingredients, servings, estimated time, start button
  3. **Cooking:** Current stage, progress bar, temperature; optional "view pot" preview
  4. **Settings:** WiFi, language, spice level, allergen preferences
  5. **History:** Past cook logs with timestamps and results
- [ ] Wire UI events to recipe state machine
- [ ] Display real-time sensor data (temperature, weight, arm status)

**Week 19: Live View & Cloud Sync**
- [ ] Implement the on-demand LCD "view pot" preview (ISP main path → RGA 480x320 → framebuffer, ≤ 10 fps)
- [ ] Overlay CV annotations (stage label, confidence, temperature) on the Cooking screen
- [ ] Implement on-demand phone live view: `live_view_start` over MQTT → bind VENC H.264 720p @ 15 fps → spawn `rtsp-stream` (`rtsp://<device>:554/pot`); teardown after 60 s with no client or on `live_view_stop`
- [ ] Implement cloud sync in `epicurad`: `GET /recipes/sync?since=` pull, `sync_outbox` push over REST, MQTT telemetry every 10 s while cooking
- [ ] Test against the cloud API (`epicura-api`) with curl, and the stream with an RTSP client (VLC)

**Week 20: Native Companion Mobile Apps**
- [ ] Create native app projects (Swift/SwiftUI for iOS, Kotlin/Compose for Android)
- [ ] Implement 4 screens:
  1. **Discovery:** BLE scan and pairing with the device
  2. **Recipe Browse:** List and detail view from the cloud API
  3. **Live Cook:** RTSP live view (same LAN, or cloud relay) + status from the cloud
  4. **Controls:** Start/stop, spice level adjustment
- [ ] BLE provisioning flow: app connects over BLE (BT 5.2), sends home WiFi credentials, device joins via wpa_supplicant
- [ ] Test on Android device (physical)

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| Touchscreen UI | 5 LVGL screens on the 4" LCD, responsive touch, pot preview |
| Cloud sync | Recipe pull, outbox push and MQTT telemetry working against the cloud API |
| Native mobile apps | Recipe browse, live view (RTSP), start/stop cooking |
| BLE provisioning | BLE pairing → home WiFi configuration works |

---

### 3.7 Phase 7: Integration & Testing (Weeks 21-24)

#### 3.7.1 Objectives
- Full system integration of all subsystems
- End-to-end cooking validation
- Safety testing and reliability assessment

#### 3.7.2 Tasks

**Week 21: Full System Integration**
- [ ] Connect all subsystems into single enclosure/frame
- [ ] Verify wiring: power, UART, I2C, SPI, PWM, servo, relay
- [ ] Run system self-test sequence (each subsystem checks in)
- [ ] End-to-end test: select recipe on UI → cook → complete notification

**Week 22: Cooking Validation**
- [ ] Cook each recipe 5+ times, log all parameters
- [ ] Evaluate results: taste, texture, consistency, timing
- [ ] Identify failure modes and edge cases
- [ ] Tune PID, CV thresholds, and dispensing calibration
- [ ] Test with different pot sizes (2L, 3L, 4L)

**Week 23: Safety Validation**
- [ ] Test all interlocks:
  - Pot removed during cooking → induction off
  - Lid opened → arm stops
  - Overtemperature → auto shutoff
  - Emergency stop button → all off
  - Communication loss → safe stop after 30s
- [ ] Measure external surface temperatures during cooking
- [ ] Test thermal fuse activation (controlled over-temp)
- [ ] Verify watchdog timer recovery on STM32

**Week 24: Reliability & Documentation**
- [ ] 24-hour continuous operation test (cycle through recipes)
- [ ] 50+ cook cycle endurance test
- [ ] Memory profiling on the RV1106 (`epicurad` RSS and CMA usage; stay within the ~95 MB peak budget)
- [ ] Power consumption profiling (average and peak)
- [ ] Bug fixing and optimization
- [ ] Prepare demo: 3 recipes cooked live, camera + UI + app shown
- [ ] Write prototype report and lessons learned

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| Integrated system | All subsystems in single assembly, working |
| Cooking validation | 5 recipes, 5+ cooks each, consistent results |
| Safety validation | All interlocks verified, no unsafe states |
| Reliability test | 50+ cook cycles without failure |
| Demo & documentation | Live demo ready, prototype report written |

---

## 4. Resource Requirements

| Category | Items | Estimated Cost |
|----------|-------|----------------|
| Compute | Luckfox Pico Zero (RV1106G3) + STM32 Nucleo dev board | $65-80 |
| Actuation | 24V BLDC motor + ASD servos + CID actuators + SLD pumps/solenoids + induction hob | $200-300 |
| Sensors | SC3336 camera + MLX90614 + reed switch + LED ring + level shifter | $30-50 |
| Mechanical | 3D printing (PETG filament) + stainless steel shaft + fasteners + brackets | $100-200 |
| Display | 4" ST7796S SPI IPS touchscreen (FT6336 I2C touch) | $15-20 |
| Power | Bench PSU + prototype PSU board + cables + connectors | $50-80 |
| Tools | Soldering station + multimeter + oscilloscope + 3D printer access | $100-200 |
| Consumables | Ingredients (20+ cook sessions) + thermal paper + misc | $50-100 |
| Miscellaneous | PCBs (JLCPCB) + shipping + contingency | $200-400 |
| **Total** | | **$790-1,420** |

---

## 5. Risk Management

### 5.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Induction control difficulty | Medium | High | Start with relay on/off, upgrade to PWM injection; worst case: use commercial hob with manual power setting |
| CV accuracy insufficient | Medium | Medium | Rule-based fallback (color + temperature thresholds); collect more training data; use ensemble of simple classifiers |
| Mechanical assembly issues | Low | Medium | Iterate 3D prints rapidly; consult maker community; use off-the-shelf brackets where possible |
| RV1106 resource limits (256 MB RAM, single Cortex-A7) | Medium | Medium | Keep all image work in the ISP/NPU/RGA/VENC hardware blocks; verify the ~95 MB peak memory budget on hardware; phone streaming on demand only; memory-pressure fallback kills `rtsp-stream` |
| Integration complexity | High | High | Test each subsystem independently before integrating; define clear interfaces (UART protocol, API); CI/CD for RV1106 software |
| Servo arm reliability | Medium | Medium | Use BLDC motor with integrated ESC; add mechanical end-stops; monitor motor current for early failure detection |
| Recipe state machine bugs | Medium | Medium | Extensive unit testing; timeout fallbacks on every state; manual override via UI |

### 5.2 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Component delivery delays | Medium | High | Order early (Week 0); identify backup suppliers; use dev boards initially |
| Luckfox SDK / Buildroot build issues | Medium | Medium | Build inside the `luckfoxtech/luckfox_pico:1.0` Docker image; start from the prebuilt Luckfox Pico Zero image and add packages incrementally |
| Scope creep | Medium | Medium | Strict MVP definition; defer nice-to-haves to post-prototype |
| Testing takes longer than planned | High | Medium | Start testing during development (not only at end); automate where possible |

---

## 6. Success Criteria

### 6.1 Minimum Viable Prototype (MVP)
- [ ] Cook 3 recipes end-to-end autonomously
- [ ] Temperature control within ±10°C of target
- [ ] Basic touchscreen UI: recipe select, cooking screen, pot preview
- [ ] Safety interlocks functional (pot detect, overtemp shutoff)
- [ ] Dispensing works for all 3 subsystems (ASD, CID, SLD)

### 6.2 Should-Have
- [ ] 5 recipes validated with consistent results
- [ ] CV-guided cooking stage detection (> 80% accuracy)
- [ ] Mobile app with basic functionality (browse, live view, start/stop)
- [ ] Temperature accuracy ±5°C
- [ ] Pressure-verified P-ASD dispensing (~±20% accuracy)

### 6.3 Nice-to-Have
- [ ] 10+ recipes in library
- [ ] Cloud sync for recipe updates
- [ ] Multi-language UI (English + Hindi)
- [ ] Auto-rinse cycle between recipes
- [ ] Voice notifications during cooking

---

## 7. Budget Summary

| Category | Estimated Cost |
|----------|---------------|
| Electronic Components (BOM) | $431 |
| Tools & Equipment | $100-200 |
| 3D Printing & Mechanical | $100-200 |
| Consumables (ingredients, filament) | $50-100 |
| PCB Fabrication | $40-80 |
| Shipping & Miscellaneous | $100-200 |
| Contingency (+20%) | $200-400 |
| **Total Project Budget** | **$1,500-2,500** |

---

## 8. Next Steps After Prototype

### 8.1 Alpha Phase Preparation
- Identify improvements from prototype testing
- Design custom carrier PCB (combine bare RV1106G3 or Core1106 SoM + STM32 + power on single board)
- Plan injection-molded enclosure design
- Begin BIS certification process (India)

### 8.2 Production Planning
- Finalize component selection for long-term availability
- Design custom induction driver board (replace teardown hob)
- Establish supplier relationships (volume pricing)
- Target production unit cost: $200-250

---

## 9. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[02-Controller-Software-Architecture|Software Architecture]]
- [[01-Safety-Compliance|Safety & Compliance]]
- [[01-Compute-Module-Components|Compute Module Components]]
- [[02-Actuation-Components|Actuation Components]]
- [[03-Sensor-Components|Sensor Components]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]

---

#epicura #development #prototype #roadmap

---

## 10. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Application processor changed to Luckfox Pico Zero (RV1106G3): Buildroot bring-up, UART bridge, SC3336 + ISP tuning, RKNN NPU model, LVGL on 4" LCD, cloud-only API and RTSP live view; budgets recomputed |
