---
created: 2026-02-15
modified: 2026-11-05
version: 2.5
status: Draft
---

# Prototype Development Plan

## 1. Overview

This document outlines the comprehensive plan for building a functional Epicura prototype capable of cooking 3-5 Indian recipes autonomously. The prototype will validate core subsystems: electric heating, robotic stirring, computer vision, and recipe state machine execution.

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
- Set up STM32G0B1RE with FreeRTOS (two images from one tree: `csc` for the Cooking Surface Controller, `du` for the DU STM32 on the Unified PCB)
- Bring up the host link between the RV1106 and the DU STM32 (UART2 ↔ USART1, 921,600 baud, COBS/CRC) and the isolated CAN bus between the DU STM32 (FDCAN1, gateway for the RV1106), the CSC STM32 and the electric heating unit
- Validate basic I/O and power supply

#### 3.1.2 Tasks

**Week 1: RV1106 Bring-up**
- [ ] Acquire Luckfox Pico Zero + IMX415-98 camera module + 4" ST7796S SPI LCD (FT6336 touch)
- [ ] Build Buildroot image from the Luckfox SDK inside the `luckfoxtech/luckfox_pico:1.0` Docker image (kernel 5.10, busybox init, squashfs rootfs; packages: sqlite, libyaml, cjson, libmosquitto, libcurl, mbedtls, lvgl, swupdate, wpa_supplicant, bluez5, rockit, rknn)
- [ ] Flash image to eMMC over USB-C, verify boot
- [ ] Establish SSH access over Wi-Fi (no Ethernet on the Pico Zero); UART0 debug console as fallback
- [ ] Test GPIO 32/38 (DU STM32 BOOT0/NRST), I2C3 (touch only), PWM10 (backlight), SPI0 (LCD on CS0 — nothing on CS1) and UART2 (`/dev/ttyS2` at 921,600, loopback with TX–RX jumpered) from Linux userspace
- [ ] Bring up the 4" LCD on fbtft (SPI0, 50 MHz, DMA) and FT6336 touch on I2C3 (evdev)
- [ ] Verify IMX415-98 on MIPI CSI through rockit VI/ISP (1280x720 @ 30 fps)

**Week 2: STM32 Bring-up (both images)**
- [ ] Acquire two NUCLEO-G0B1RE development boards (one stands in for the CSC, one for the DU STM32)
- [ ] Install STM32CubeIDE and STM32CubeMX
- [ ] Create the FreeRTOS project with one tree and two targets (`csc`: CAN Comms / Motor Control / Safety / Thermal; `du`: Link-Gateway / Dispense / Monitor)
- [ ] Test GPIO output (LED blink) on both
- [ ] CSC: test USB-C DFU and the J_DBG console on the NUCLEO; later verify the CAN bootloader (0x7E0/0x7E8) once FDCAN1 is up
- [ ] DU: flash through the ST system bootloader on USART1 (PA9/PA10) with BOOT0/NRST driven from the Pico Zero GPIO 32/38; SWD as bench fallback
- [ ] DU: host-link loopback — COBS/CRC-16 frames from `epicurad` echoed by the DU STM32 at 921,600 baud, zero CRC errors over 1 M frames
- [ ] Test FDCAN1 on the shared bus from both images (receive heating unit HEAT_STATUS; DU forwards the RV1106's HB_AP, CSC receives it)
- [ ] DU: test I2C1 (PCA9685, PCF8574 #2, INA219 ×2), the six SLD Hall inputs (PC0–PC5) and TIM PWM (pumps, LED ring, buzzer, servo signal generation)

**Week 3: Inter-Processor Communication (host link + CAN)**
- [ ] Wire the isolated CAN bus: DU STM32 FDCAN1 (PB8/PB9) + non-isolated SN65HVD230 on the Unified PCB (GND_ISO tied to DU ground at dock pad 5, pad 6 unused), CSC STM32 FDCAN1 (PB8/PB9) + ISO1050DUB #1 with the B0505S-1WR3 #1 isolated supply, 120 Ω at J_CAN_HEAT and in the module; 500 kbps; confirm the heating unit's CAN port is SELV
- [ ] Define the CAN ID map (E_STOP 0x001, HB_AP 0x010, heater 0x1xx, commands 0x2xx with a seq byte, reports 0x3xx, ACK/NAK 0x3FF) and the host-link DU-local block (0x220, 0x226, 0x230–0x239, 0x311 DU_STATUS, 0x3FE DU_ACK)
- [ ] Implement the protocol on the CSC STM32 (FDCAN1 RX FIFO interrupt, ID filters, ACK/NAK, 20 Hz TELEMETRY)
- [ ] Implement the gateway on the DU STM32 (USART1 DMA ↔ FDCAN1: forward bus IDs unchanged, terminate DU-local IDs, 5 s HB_AP watchdog → dispensers off)
- [ ] Implement the protocol on the RV1106 (C, `epicurad` link thread: termios on `/dev/ttyS2`, COBS/CRC codec, ID routing)
- [ ] Test bidirectional exchange: RV1106 sends a command, CSC ACKs through the gateway; 20 Hz TELEMETRY and 1 Hz DU_STATUS keep flowing while the LCD refreshes
- [ ] Measure round-trip latency (target: < 10 ms through the gateway, < 5 ms for a DU-local command)

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
| STM32 running FreeRTOS | 4+ tasks running, CAN responsive |
| Isolated CAN bus (3 nodes) | Bidirectional messaging, < 10 ms round-trip, no frame loss during LCD refresh |
| Power distribution | All subsystems powered, no brownouts under load |

**Risks:**
- Luckfox SDK / Buildroot build issues → Fallback: start from the prebuilt Luckfox Pico Zero image and add packages incrementally
- Host-link framing errors at 921,600 baud (long header traces, EMI from the 6V_DSP switcher) → Fallback: drop to 460,800 baud (still > 10x the traffic), keep the link thread at SCHED_FIFO; CAN frames are hardware-protected once on the bus

---

### 3.2 Phase 2: Heater Integration (Weeks 5-7)

#### 3.2.1 Objectives
- Integrate and control a commercial electric heating unit (rice-cooker class, CAN port)
- Drive the unit's own temperature controller from the RV1106 (`heat` thread: HEAT_SET_TEMP keep-alive, HEAT_STATUS surface_temp); no IR thermometer
- Validate the unit's temperature accuracy and step response

#### 3.2.2 Tasks

**Week 5: Heating Unit Setup**
- [ ] Buy a Philips OneChef NX5300/00 donor cooker (or equivalent, ₹19,995 ≈ $230) and strip the air-fryer lid; keep the body, heating plate (~1,300 W assumed) and controller; set the round inner pot and glass lid aside
- [ ] Source the 25 × 25 × 12 cm rounded-square rounded-square non-stick pot and its matching glass lid (commercial square casserole or custom pressed; 6 L max fill) and open the donor pot well out to the square footprint (Mechanical Design §2.2)
- [ ] Obtain the OEM unit with its CAN control board (ships with the unit, confirmed 2026-11-04) and review its CAN protocol documentation; the retail OneChef board has no external interface and is not used
- [ ] Connect the unit's CAN port to J_CAN_HEAT on the Cooking Surface Controller (the DU STM32 node reaches the same bus over the dock contacts; both Epicura nodes already up)
- [ ] Verify CAN communication from the RV1106 through the DU STM32 gateway: send HEAT_QUERY, receive HEAT_STATUS on the host link; confirm the CSC STM32 sees the same frames
- [ ] Wire the safety relay K_SAFE on the heating unit's AC inlet loom (STM32 PB0 → J_SAFE pin 1 → power relay; NC wiring, de-energised = unit disconnected); the OEM unit is not opened — Epicura uses only its CAN port

**Week 6: CAN Power Control Integration**
- [ ] Implement HEAT_SET_POWER (0-100%, power mode) and HEAT_SET_TEMP (temperature mode) from the RV1106 heat thread with 2 Hz keep-alive; STM32 sends HEAT_ON_OFF=0 only
- [ ] Verify all power levels (warm, simmer, medium, boil, sear)
- [ ] Measure power delivery at different CAN power levels (25%, 50%, 75%, 100%)
- [ ] Log temperature ramp rates for water (1L, 2L, 3L)
- [ ] Test the E-stop cut (K_SAFE opens the heating unit's AC inlet; the CSC stays up on its own LRS-35-12 and keeps reporting), STM32 HEAT_ON_OFF=0 / E_STOP broadcast, and the unit's 1 s command watchdog (kill `epicurad`)

**Week 7: Temperature Control & Sensors**
- [ ] Verify surface_temp and element temperature reporting in HEAT_STATUS from the heating unit (10 Hz)
- [ ] Calibrate the unit's surface_temp against a thermocouple on the pot bottom (ambient to the unit's 200°C ceiling)
- [ ] Implement the `heat` thread on the RV1106 (SCHED_FIFO): HEAT_SET_TEMP / HEAT_SET_POWER keep-alive at 2 Hz, HEAT_STATUS parsing, 500 ms watchdog
- [ ] Characterise the unit's own loop: step response (ambient → 100°C, 100°C → simmer at 85°C); derive pot-bottom `temp_target` values for the recipe schema
- [ ] Validate accuracy: ±10°C at target (prototype), ±5°C goal

```
┌─────────────────────────────────────────────────────────┐
│          Heater Control (loop inside the heating unit)   │
│                                                         │
│  Recipe Target ──► heat thread ──► CAN 0x100 HEAT_SET_TEMP │
│  (RV1106)          2 Hz keep-alive        │             │
│                                           ▼             │
│                              ┌───────────────────────┐  │
│                              │ Heating Unit          │  │
│                              │  PID ──► Plate ──► Pot│  │
│                              │   ▲                   │  │
│                              │   └── centre NTC      │  │
│                              └──────────┬────────────┘  │
│                                         │ CAN 0x180     │
│  Stage transitions ◄── surface_temp ◄───┘ HEAT_STATUS   │
│  STM32 cut-off      ◄── surface/element temp, faults    │
└─────────────────────────────────────────────────────────┘
```

**Deliverables:**

| Deliverable | Success Criteria |
|-------------|-----------------|
| Heater control | RV1106 can set power 0-100% in 10% steps over CAN; STM32 off-switch verified |
| Temperature sensing | Unit surface_temp (HEAT_STATUS) within ±5°C of a pot-bottom thermocouple |
| Temperature mode (unit PID, RV1106 setpoint) | Reach 100°C in < 10 min (1L water, 1,300 W plate), hold ±10°C |
| Safety cutoff | Unit's own element over-temp cut-off and thermal fuse verified; STM32 CRITICAL at surface_temp > 220°C, E_STOP at > 230°C (element temp > 250°C → WARNING) |

---

### 3.3 Phase 3: Arm & Sensors (Weeks 8-10)

#### 3.3.1 Objectives
- Build and mount the servo stirring arm
- Implement stirring patterns

#### 3.3.2 Tasks

**Week 8: Servo Arm Assembly**
- [ ] Acquire 24V integrated CAN servo motor (≥ 3 N·m, CyberGear/RobStride-class) and bring it up on the STM32 FDCAN2 bus (J_CAN_STIR, isolated port #2, 1 Mbps) with 24 V from J_STIR_PWR — the SU's own LRS-75-24 #2 fed in on J_SU_IN and switched by the K_SU pilot relay on its AC input (after K_SU closes, wait ≈ 300 ms and for the motor boot frame before commanding)
- [ ] Design mounting bracket (3D print, PETG or aluminum)
- [ ] Fabricate stainless steel shaft (8mm diameter, 250mm length)
- [ ] Attach food-grade silicone paddle to shaft end
- [ ] Mount servo + shaft assembly above pot center
- [ ] Wire motor CAN + 24 V harness to J_CAN_STIR / J_STIR_PWR (J_SU 5-way: 24V_SU, GND_SU, CAN_H, CAN_L, SHIELD; GND_SU stays floating from the CS ground — verify no continuity); configure the motor's command timeout (≤ 500 ms) and zero the encoder at the home angle

**Week 9: Stirring Patterns**
- [ ] Implement 5 stirring patterns on STM32 (CAN velocity commands at 50 Hz):
  - Circular (continuous rotation, adjustable speed)
  - Back-and-forth (180° sweep)
  - Scraping (edge-following pattern)
  - Folding (slow, deep strokes for delicate mixing)
  - Pulse (intermittent stir, e.g., 5s on / 30s off)
- [ ] Add speed control: 10-60 RPM range
- [ ] Add torque monitoring: detect obstruction via motor-reported current and velocity error
- [ ] Test all patterns with water, then with thick dal consistency

```
┌──────────────────────────────────────────┐
│          Arm & Sensor Assembly           │
│                                          │
│         ┌──────┐                         │
│         │CAN   │ 24V integrated servo    │
│         │Servo │ (≥ 3 N·m, CAN 1 Mbps)   │
│         └──┬───┘                         │
│            │ Shaft (SS, 8mm)             │
│            │                             │
│            ▼                             │
│     ┌──────────────┐                     │
│     │   Paddle     │ (Silicone)          │
│     └──────────────┘                     │
│            │                             │
│     ┌──────────────┐   ┌─────────────┐   │
│     │     Pot      │   │ Heating unit│   │
│     │(25 cm square)│   │ centre temp │   │
│     └──────┬───────┘   └─────────────┘   │
│            │                             │
│  ┌─────────┐┌─────────┐  SLD drawer tanks│
│  │Oil tank ││H2O tank │  (float+presence │
│  └──┬───┬──┘└──┬───┬──┘   magnets)       │
│  pump│   │Hall │   │Hall                 │
│     ▼   ▼     ▼   ▼                      │
│  ┌──────────────────┐                    │
│  │ DU STM32 PC0–PC5 │ tachs + level in,  │
│  │ (Dispense task)  │ open-loop metering │
│  └──────────────────┘                    │
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
- [ ] Mount IMX415-98 camera module on the Dispensing Unit underside, centred over the pot behind the sealed window (overhead view)
- [ ] Install the white LED ring (12–16 LEDs, 5000 K) around the camera window; drive it from the DU STM32 PWM via Q_LED (SET_LED 0x220 over the host link) and implement the OFF / CAPTURE / NIGHT duty modes in `epicurad`
- [ ] Configure rockit VI/ISP on the RV1106 for 1280x720 @ 30fps capture (main path NV12) plus a 224x224 RGB888 self-path
- [ ] ISP tuning check: load the IMX415-98 tuning file from the Luckfox SDK; verify AWB/AE, dehaze and 3DNR behaviour over a steaming pot
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
│  IMX415 ──► ISP (hw) ──► NPU (RKNN) ──► Stage Label │
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
- Build ingredient dispensing subsystems (FID, CID, SLD)
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
      actions: [dispense: {subsystem: "FID", box: 1, qty_quarter_tsp: 4}]
      ...
  ```
- [ ] Implement state machine on the RV1106 (C, `epicurad` engine thread, libyaml):
  - Load recipe YAML
  - Execute stages sequentially
  - Transition on CV detection OR timeout OR weight confirmation
  - Send commands to the CSC STM32 and heater over the CAN bus (link thread → DU STM32 gateway) and dispensing commands to the DU STM32 (dispense thread, DU-local IDs)
- [ ] Create recipe files for 5 target dishes

**Week 16: Dispensing Mechanism**
- [ ] Build FID: 6-canister carousel (Ø170 mm ring, 4:3 index gear) with per-canister ¼ tsp measure wheels, dosing station (F2 blade coupling) and steam-gate flap (F3)
- [ ] Build CID: 5-slot + cover carousel (Ø230 mm lift-off ring, thin-section bearing) on fixed base plate with rear aperture and chute, index servo (C1) via 4:3 gear
- [ ] Build SLD (robot-mop pattern): two drawer tanks (200 mL oil, 500 mL water; bottom self-sealing poppet, vented cap, float + presence magnets) in the DU service ring, 6 V peristaltic (oil) and 6 V diaphragm (water) pumps in the body with rotor magnets, short pump lines, snap-out nozzle cartridges with spring check valves
- [ ] Fit the six Hall switches (two tachs, two present, two low) on the 12-pin J_SLD → DU STM32 PC0–PC5; implement open-loop metering (pulses × cal_ul), the prime routine and SLD_CAL; calibrate both channels into a measuring cup
- [ ] Assemble the Dispenser Servo Block: PCA9685 @ 0x41 on the DU STM32 I2C1, OE on PB0, MP1584EN #2 set to 6.0 V with P-MOSFET rail switch on PCF8574 #2 P4, servo leads to J_DSB1-4; implement the DU STM32 Dispense task (FID/CID/SLD sequences, INA219 stall window) and the `epicurad` dispense thread as its host-link client (0x230–0x239 → DU_ACK 0x3FE)
- [ ] Calibrate FID dosing: weigh 10 doses per spice, store g per ¼ tsp; verify jiggle clears packed powder; verify CID ascending-order NACK and stall detection
- [ ] Calibrate SLD dispensing per channel: fixed pulse count into a measuring cup, store cal_ul (SLD_CAL); verify ±5 % on 10 mL oil and 300 mL water
- [ ] Test SLD tank sensing: low-level Hall at ≈ 20 / 50 mL left, tank-absent NAK with a tank out, prime runs once after a tank re-seat; check valves hold with a full tank

```
┌──────────────────────────────────────────────────┐
│           Dispensing Subsystem Layout            │
│                                                  │
│   FID carousel (rear): 6 canisters, ¼ tsp wheels │
│        ┌──────────────────────┐                  │
│        │ Box4  Box3  Box2     │ F1 index servo   │
│        │ Box5  Box6  Box1 ──► │ F2 dose servo    │
│        └──────────┬───────────┘ F3 steam gate    │
│                   ▼ chute                        │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─            │
│                                                  │
│   SLD-OIL ═══╗           ╔═══ SLD-WATER          │
│   [Pump]─[Sol]╚══►Pot◄══╝[Sol]─[Pump]            │
│                                                  │
│                   ▲ chute                        │
│        ┌──────────┴───────────┐                  │
│        │ Slot3  Slot2  Slot1  │ C1 index servo   │
│        │ Slot4  Slot5  COVER  │ (whole slot)     │
│        └──────────────────────┘                  │
│   CID carousel (front): 5 slots + cover sector   │
│                                                  │
│   DSB: 4 servos ── PCA9685 (0x41) ── 6.0 V rail  │
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
| FID/CID/SLD subsystems | All four DSB servos + SLD pumps functional, no jamming, stall detection verified |
| Volumetric dosing (FID) | ±10% per ¼ tsp dose across all 6 spices |
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
- [ ] Verify wiring per unit: CS (LRS-35-12 → J_12V_IN for the CSC, fans and relay coils, LRS-75-24 #1 → J_DU_IN only, LRS-75-24 #2 → J_SU_IN, K_SAFE on the heating unit's AC inlet, K_SU on the SU PSU's AC input, fans, J_CAN_HEAT, stir harness to J_SU with GND_SU floating), DU (battery pack, DU STM32 host link + BOOT0/NRST, I2C1 peripherals, SPI LCD, servos, pumps, LED ring), dock contacts (DOCK_24V, CAN, sense pins) with the DU seated and lifted
- [ ] Run system self-test sequence (each subsystem checks in)
- [ ] End-to-end test: select recipe on UI → cook → complete notification

**Week 22: Cooking Validation**
- [ ] Cook each recipe 5+ times, log all parameters
- [ ] Evaluate results: taste, texture, consistency, timing
- [ ] Identify failure modes and edge cases
- [ ] Tune PID, CV thresholds, and dispensing calibration
- [ ] Test with different fill levels in the 25 cm rounded-square pot (1 L, 2 L, 4 L, 6 L max-fill)

**Week 23: Safety Validation**
- [ ] Test all interlocks:
  - Pot removed during cooking → heater off
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
| Actuation | 24V CAN servo motor + 4 dispenser servos (FID/CID carousels, PCA9685) + SLD drawer tanks, pumps and check-valve nozzles + OneChef NX5300/00 donor cooker (heating unit, controller, body) + 25 cm rounded-square pot with lid | $415-515 |
| Sensors | IMX415-98 camera + reed switch + white LED ring + SLD Hall switches ×6 + INA219 ×2 (no thermometer) | $60-75 |
| Mechanical | 3D printing (PETG filament) + stainless steel shaft + fasteners + brackets | $100-200 |
| Display | 4" ST7796S SPI IPS touchscreen (FT6336 I2C touch) | $15-20 |
| Power | Bench PSU + 2× Mean Well LRS-75-24 (DU #1, SU #2) + 1× Mean Well LRS-35-12 (CSC) + prototype PSU board + cables + connectors | $77-112 |
| Tools | Soldering station + multimeter + oscilloscope + 3D printer access | $100-200 |
| Consumables | Ingredients (20+ cook sessions) + thermal paper + misc | $50-100 |
| Miscellaneous | PCBs (JLCPCB) + shipping + contingency | $200-400 |
| **Total** | | **$1,072-1,707** |

---

## 5. Risk Management

### 5.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Heater control difficulty (CAN protocol of the chosen unit) | Medium | High | Start with relay on/off (HEAT_ON_OFF), then the unit's temperature and power modes; worst case: use a unit with manual power setting plus relay on/off. The OEM unit ships with a CAN control board (confirmed 2026-11-04); the retail OneChef board is not used |
| CV accuracy insufficient | Medium | Medium | Rule-based fallback (color + temperature thresholds); collect more training data; use ensemble of simple classifiers |
| Mechanical assembly issues | Low | Medium | Iterate 3D prints rapidly; consult maker community; use off-the-shelf brackets where possible |
| RV1106 resource limits (256 MB RAM, single Cortex-A7) | Medium | Medium | Keep all image work in the ISP/NPU/RGA/VENC hardware blocks; verify the ~95 MB peak memory budget on hardware; phone streaming on demand only; memory-pressure fallback kills `rtsp-stream` |
| Integration complexity | High | High | Test each subsystem independently before integrating; define clear interfaces (CAN ID map, API); CI/CD for RV1106 software |
| Servo arm reliability | Medium | Medium | Use an integrated CAN servo with encoder feedback; add mechanical end-stops; monitor motor-reported current and temperature for early failure detection |
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
- [ ] Dispensing works for all 3 subsystems (FID, CID, SLD)

### 6.2 Should-Have
- [ ] 5 recipes validated with consistent results
- [ ] CV-guided cooking stage detection (> 80% accuracy)
- [ ] Mobile app with basic functionality (browse, live view, start/stop)
- [ ] Temperature accuracy ±5°C
- [ ] Volumetric FID dosing (±10% per ¼ tsp dose)

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
| Electronic Components (BOM) | $618 |
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
- Design a custom heater power stage (replace the commercial heating unit)
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
| 1.2 | 2026-11-04 | Manas Pradhan | Phase 5 dispensing tasks rewritten for servo carousels (FID 6 canisters / 3 servos, CID 5 slots / 1 servo, Dispenser Servo Block) |
| 1.3 | 2026-11-04 | Manas Pradhan | Camera IMX415-98 ($54): sensors line $75-95, total $835-1,465, BOM $473; Nucleo SB numbers |
| 1.5 | 2026-11-04 | Manas Pradhan | Week 7 rewritten: no IR thermometer or PID in Epicura (module-internal temperature control, HEAT_SET_TEMP keep-alive); arm weeks and diagrams updated for the CAN servo motor on FDCAN2; integration wiring and budget rows updated |
| 1.4 | 2026-11-04 | Manas Pradhan | Phases 1–2 rewritten for the isolated 3-node CAN bus (RV1106 MCP2518FD node, STM32 FDCAN1, induction surface) and the RV1106 heat thread PID; UART2 is a service link only |
| 1.6 | 2026-11-04 | Manas Pradhan | Three-unit architecture: STM32 on the Cooking Surface Controller (no UART service link, CAN bootloader), dispensers driven by the RV1106 dispense thread on I2C3 (NAU7802 load cells, 6.0 V rail), white PWM LED ring on the Dispensing Unit underside, per-unit wiring check with the dock |
| 1.7 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, ~1,300 W assumed, own PID, CAN port; same CAN contract): Phase 2 renamed Heater Integration, week 5/7 tasks, control diagram (plate, centre NTC, element temp), deliverables (boil < 10 min, element over-temp cut-off), budget row ($205-305), risk and production rows reworded |
| 1.8 | 2026-11-04 | Manas Pradhan | Heating unit referenced to the Philips OneChef NX5300/00: Phase 2 starts by buying the donor cooker and stripping the air-fryer lid, OEM CAN control board (Case A / Case B) task and risk note; pot is the donor's 6 L non-stick inner pot (diagram, fill-level tests); calibration range and cut-offs re-based (surface_temp 220 °C CRITICAL / 230 °C E_STOP, unit ceiling 200 °C); budget: Actuation $205-305 → $390-490 (donor $230 replaces heating unit $45), total $835-1,465 → $1,020-1,650, BOM $433 → $618 |
| 1.9 | 2026-11-04 | Manas Pradhan | Pot changed to a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot (6 L max fill; Mechanical Design §2.2): Week 5 sourcing / pot-well task added, donor's round pot and lid set aside, control diagram and fill-level tests updated; budget Actuation $390-490 → $415-515 (pot + lid $25), total $1,020-1,650 → $1,045-1,675 |
| 2.0 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit (second STM32G0B1RE on the Unified PCB v5.0 as CAN node + gateway for the RV1106 over a UART host link): Phase 1 weeks 1–3 rewritten (two NUCLEO boards, `csc` + `du` images, host-link loopback, BOOT0/NRST flashing, gateway bring-up, DU-local ID block), MCP2518FD / `can0` tasks and the SPI0-contention risk removed (host-link framing risk added), week 5 heater verification through the gateway, LED ring and DSB tasks moved to the DU STM32 with `epicurad` as client, integration wiring check updated; budget unchanged (second NUCLEO ≈ $11 inside the development line) |
| 2.1 | 2026-11-04 | Manas Pradhan | Stirring Unit on its own PSU (CSC v1.3): week 8 motor bring-up on the isolated FDCAN2 port with 24 V from LRS-75-24 #2 via J_SU_IN and the K_SU pilot relay (≈ 300 ms start-up, motor boot frame), harness wiring to J_SU (24V_SU / GND_SU floating), week 21 CS wiring check (two PSUs, K_SAFE / K_SU); budget: second LRS-75-24 added to the Power line $50-80 → $65-100, total $1,045-1,675 → $1,060-1,695 |
| 2.2 | 2026-11-04 | Manas Pradhan | CAN isolation on the CSC only: week 3 bus wiring uses a non-isolated SN65HVD230 on the DU STM32 (ISO1050DUB #2 dropped, Unified PCB v5.1), GND_ISO tied to DU ground at the dock, SELV check on the heating unit's CAN port added; budget unchanged |
| 2.3 | 2026-11-05 | Manas Pradhan | CSC powered from the heating unit (CSC v1.5): week 5 gains the donor-supply characterisation task (SELV, 12 V, ≥ 1.5 A spare with the element cycling, IRM-20-12 fallback on the same J_HU_PWR) and wires K_SAFE on the element loom instead of the AC inlet; week 6 element-disconnect test; week 21 CS wiring check (CSC on J_HU_PWR, LRS-75-24 #1 → J_DU_IN only, K_SAFE on the element loom); budget: IRM-20-12 fallback (~$8, if needed) listed without changing the totals |
| 2.4 | 2026-11-05 | Manas Pradhan | CSC on its own PSU (CSC v1.6, reverses 2.3): week 5 donor-supply characterisation task removed and K_SAFE wired back on the heating unit's AC inlet loom (the OEM unit is not opened); week 6 element-disconnect test → E-stop test (unit's AC cut, CSC stays up); week 21 CS wiring check (LRS-35-12 → J_12V_IN, LRS-75-24 #1 → J_DU_IN, #2 → J_SU_IN, K_SAFE on the inlet); budget: IRM-20-12 "if needed" line dropped, 1× Mean Well LRS-35-12 ($12) added to the Power line $65-100 → $77-112, total $1,060-1,695 → $1,072-1,707 |
| 2.5 | 2026-11-05 | Manas Pradhan | Robot-mop SLD: week 2 DU bring-up (Hall inputs instead of NAU7802), sensing diagram, week 16 SLD build tasks (drawer tanks, pumps with tachs, check-valve nozzles, open-loop metering, prime, calibration) and budget rows updated |
