---
created: 2026-02-15
modified: 2026-11-04
version: 1.1
status: Draft
---

# Vision System

## 1. Overview

The vision system provides real-time food monitoring and cooking stage detection using an overhead camera, LED illumination, and edge AI inference on the RV1106's NPU. A MobileNetV2 model (INT8, RKNN) classifies the current cooking stage (raw, browning, boiling, simmering, done) from frames prepared entirely by the hardware ISP, feeding decisions back to the recipe state machine. The system also supports an on-demand pot preview on the touchscreen and on-demand H.264 live view to the companion mobile app, plus anomaly detection for safety-critical events (burning, boil-over, empty pot).

## 2. Camera Selection

### 2.1 Sensor Specification (SC3336)

| Parameter | SC3336 |
|-----------|--------|
| Resolution | 3 MP (2304 x 1296 native) |
| Operating Mode | 1280 x 720 @ 30 fps (ISP main path) |
| Sensor Size | 1/2.8" |
| Interface | MIPI CSI-2 (2-lane), FPC to Luckfox Pico Zero CSI connector |
| ISP Support | Luckfox SDK ships the RV1106 ISP tuning file (AWB, AE, LSC, dehaze, 3DNR profiles) |
| Low-Light Performance | Good (SmartSens back-illuminated pixel, designed for IP cameras) |
| Lens | Fixed M12 mount on module (wide-angle, ~100 deg FOV typical) |
| Price (approx.) | $12 USD (module, FPC included) |
| Availability | Luckfox / Waveshare store, widely available |

### 2.2 Selection Rationale

The SC3336 is the Luckfox-supported sensor for the RV1106: its ISP tuning file ships in the SDK, so dehaze, noise reduction, lens shading and white balance work out of the box. Raspberry Pi sensors (IMX219, IMX477) have no RV1106 ISP tuning file and are dropped. The sensor is run at 1280 x 720 rather than its native 3 MP: 720p halves the CMA buffer memory and encoder load on a 256 MB system, and is more than sufficient for a 224 x 224 classifier and for a phone preview.

## 3. Mounting and Steam Protection

### 3.1 Camera Position

```
┌──────────────────────────────────────────────────┐
│                  ENCLOSURE LID                    │
│                                                   │
│     ┌───────────┐   ┌──────────────┐              │
│     │ LED Ring  │   │  Camera      │              │
│     │ (WS2812B) │   │  Module      │              │
│     │  ┌─────┐  │   │  ┌───────┐  │              │
│     │  │ O O │  │   │  │ Lens  │  │              │
│     │  │O   O│  │   │  │ (down)│  │              │
│     │  │ O O │  │   │  └───┬───┘  │              │
│     │  └─────┘  │   │      │      │              │
│     └───────────┘   └──────┼──────┘              │
│                            │                      │
│                     20-30cm distance               │
│                            │                      │
│                            ▼                      │
│     ┌──────────────────────────────────────┐      │
│     │           COOKING POT                │      │
│     │         (field of view)              │      │
│     └──────────────────────────────────────┘      │
└──────────────────────────────────────────────────┘
```

### 3.2 Mounting Specifications

| Parameter | Value |
|-----------|-------|
| Position | Overhead, centered above pot |
| Distance to Pot | 20-30 cm (adjustable bracket) |
| Field of View | Covers entire pot opening plus 2 cm margin |
| Mounting | Gantry bracket, stainless steel |
| Angle Adjustment | +/- 10 degrees tilt (set screw) |
| Vibration Isolation | Rubber dampers (2x M3 silicone grommets) |

### 3.3 Steam Protection Measures

| Measure | Implementation | Effectiveness |
|---------|---------------|---------------|
| Glass Lens Cover | Borosilicate glass disc, anti-fog hydrophilic coating | Primary barrier, prevents condensation buildup |
| Air Curtain | Small 5V fan (25mm) blowing across lens surface | Diverts rising steam, keeps lens clear |
| Hydrophobic Coating | RainX or nano-coating on glass cover (reapply monthly) | Beads water, reduces fogging |
| ISP Dehazing | Hardware dehaze + 3D noise reduction in the RV1106 ISP (SC3336 tuning profile), zero CPU cost | Compensates for mild haze when physical measures insufficient |
| Periodic Wipe Reminder | UI notification after N cook cycles | Prompts user to clean lens cover |

## 4. LED Illumination

### 4.1 Ring Light Design

```
         ┌───────────────────────┐
         │     LED Ring          │
         │   (12-16 WS2812B)    │
         │                       │
         │    O  O  O  O         │
         │  O            O       │
         │  O  ┌──────┐  O      │
         │  O  │Camera│  O      │
         │  O  │ Lens │  O      │
         │  O  └──────┘  O      │
         │  O            O       │
         │    O  O  O  O         │
         │                       │
         └───────────────────────┘
```

### 4.2 LED Specifications

| Parameter | Value |
|-----------|-------|
| LED Type | WS2812B (addressable RGB) |
| LED Count | 12-16 on ring PCB |
| Color Temperature | 5000K daylight white (for accurate food color) |
| Brightness | 60 mA per LED at max, ~960 mA total ring |
| Control Interface | Single-wire 800 kHz protocol driven by the STM32 (PB14, TIM15_CH1 + DMA) through a 74AHCT1G125 3.3 V to 5 V level shifter; the RV1106 only requests modes via SET_LED (0x20) over the bridge |
| Diffuser | Frosted polycarbonate ring (reduces specular glare on liquids) |
| Power | 5V, max 1A (from 5V rail, switched by PCF8574 #2 P3) |
| Mounting | Co-axial with camera, 5mm offset below lens plane |

### 4.3 Illumination Modes

| Mode | RGB Value | Brightness | SET_LED Request (RV1106 to STM32) | Use Case |
|------|-----------|------------|-----------------------------------|----------|
| Cooking (default) | Warm white (255, 220, 180) | 80% | mode=CAPTURE, rgb=(255,220,180), brightness=80 | Standard cooking illumination |
| Capture (inference) | Daylight white (255, 255, 255) | 100% | mode=CAPTURE, rgb=(255,255,255), brightness=100 | Brief flash during frame capture for CV |
| Night Mode | Dim warm (128, 110, 90) | 30% | mode=NIGHT, rgb=(128,110,90), brightness=30 | Low ambient light, reduced eye strain |
| Off | (0, 0, 0) | 0% | mode=OFF | Standby, lid open, cleaning |
| Alert | Red pulse (255, 0, 0) | 100% pulsing | mode=CAPTURE, rgb=(255,0,0), toggled by the RV1106 at 2 Hz | Anomaly detected (burning, boil-over) |

The SET_LED message carries `mode (OFF/CAPTURE/NIGHT), r, g, b, brightness_pct`; the STM32 holds the last requested colour until the next message. See [[../03-Software/05-MCU-Functional-Specification|MCU Functional Specification]] section 2.8 for the driver requirements.

## 5. Image Processing Pipeline

### 5.1 End-to-End Flow

Every stage before inference is a hardware block. The CPU touches only the 8-class output vector.

```
┌──────────────┐    ┌───────────────┐    ┌────────────────┐
│ Camera       │    │ ISP (hardware)│    │ ISP self-path  │
│ (SC3336)     │──► │ 3A, 3DNR,     │──► │ (hardware)     │
│ MIPI CSI-2   │    │ dehaze, LSC,  │    │ scale to       │
│ 1280x720     │    │ sharpen; main │    │ 224x224 RGB888 │
│ @ 30 fps     │    │ path 720p NV12│    │ @ 2 fps        │
└──────────────┘    └───────┬───────┘    └───────┬────────┘
                            │                    │
              on demand     ▼                    ▼
                    ┌───────────────┐    ┌────────────────┐
                    │ VENC H.264    │    │ NPU (rknn_api) │
                    │ 720p @ 15 fps │    │ MobileNetV2    │
                    │ → rtsp-stream │    │ INT8, 5-10 ms  │
                    │ RGA → LCD     │    │ (zero copy)    │
                    └───────────────┘    └───────┬────────┘
                                                 │
                                                 ▼
                                        ┌────────────────┐
                                        │ Post-Process   │
                                        │ Dequantize,    │
                                        │ argmax, 3-frame│
                                        │ majority vote  │
                                        └───────┬────────┘
                                                │
                                                ▼
                                        ┌────────────────┐
                                        │ Recipe Engine  │
                                        │ Decision       │
                                        │ (Stage ID +   │
                                        │  Confidence)  │
                                        └────────────────┘
```

### 5.2 Pipeline Stage Details

| Stage | Input | Output | Library | Notes |
|-------|-------|--------|---------|-------|
| Capture | CSI-2 raw Bayer (SC3336) | 1280x720 NV12 frame (ISP main path) | rockit VI/ISP (hardware) | 30 fps sensor rate; dehaze, 2D/3D NR, LSC, sharpening, AWB, AE all in the ISP |
| Scale | ISP main path | 224x224 RGB888 tensor (ISP self-path) | ISP self-path (hardware) | Sampled at 2 fps straight into a DMA buffer; no CPU resize or normalisation |
| Inference | 224x224 RGB888 (INT8 pass-through) | 8-class probability vector | rknn_api on the 1 TOPS NPU | INT8 .rknn model, 5-10 ms |
| Post-Process | Probability vector | Stage ID + confidence | C (cv thread of epicurad) | Confidence threshold >0.6, 3-frame majority vote |

There is no histogram equalisation / CLAHE stage: steam haze and contrast are handled by the ISP dehaze block, tuned per the SC3336 profile.

### 5.3 Inference Timing Budget

```
Operation                      Time (ms)    Cumulative
────────────────────────────   ──────────   ──────────
ISP self-path frame ready      0 (hardware) 0
Dequeue frame (zero copy)      <1           1
NPU inference (rknn_run)       5-10         11
Dequantize + argmax + vote     <1           12
Total per frame                ~7-12 ms

Target: < 20 ms per inference (< 50 ms end-to-end including
        scheduling on the single Cortex-A7 core)
Actual inference rate: 2 fps (every 500 ms); NPU idle > 97% of the time
```

## 6. Classification Stages

### 6.1 Cooking Stage Definitions

| Stage ID | Stage Name | Visual Cues | Example Dish State |
|----------|-----------|-------------|---------------------|
| 0 | Raw | Uncooked ingredients visible, distinct colors and shapes | Raw onions and tomatoes in oil |
| 1 | Heating | Oil shimmer, steam wisps beginning, surface rippling | Oil surface showing movement |
| 2 | Browning | Color change from white/pale to golden/brown, Maillard reaction | Onions turning translucent then golden |
| 3 | Liquid Added | Visible water/broth/sauce covering ingredients | Water or tomato puree poured in |
| 4 | Boiling | Vigorous bubbling, large bubbles breaking surface | Rolling boil with active surface motion |
| 5 | Simmering | Gentle bubbles, slow surface movement, steady steam | Gentle bubbling dal or curry |
| 6 | Thickening | Reduced liquid level, glossy/viscous surface, less bubbling | Gravy coating spoon, reduced sauce |
| 7 | Done | Final color/texture matching recipe target, minimal activity | Thick dal, well-coated curry |

### 6.2 Stage Transition Diagram

```
    ┌───────┐    Heat    ┌──────────┐   Browning   ┌──────────┐
    │  RAW  │──────────►│ HEATING  │────────────►│ BROWNING │
    │  (0)  │           │   (1)    │             │   (2)    │
    └───────┘           └──────────┘             └────┬─────┘
                                                      │
                                                      │ Add liquid
                                                      ▼
    ┌───────┐  Reduce   ┌──────────┐    Heat     ┌──────────┐
    │ DONE  │◄─────────│THICKENING│◄────────────│ LIQUID   │
    │  (7)  │          │   (6)    │             │ ADDED(3) │
    └───────┘          └──────────┘             └────┬─────┘
         ▲                  ▲                        │
         │                  │                        │ Heat
         │             Time + Evaporation            ▼
         │                  │               ┌──────────┐
         │                  └───────────────│ BOILING  │
         │                                  │   (4)    │
         │                                  └────┬─────┘
         │                                       │
         │                                       │ Reduce heat
         │                                       ▼
         │                              ┌──────────────┐
         └──────────────────────────────│  SIMMERING   │
                  (Direct finish)       │    (5)       │
                                        └──────────────┘
```

## 7. AI Model Development

### 7.1 Model Architecture

| Parameter | Value |
|-----------|-------|
| Backbone | MobileNetV2 (transfer learning from ImageNet) |
| Custom Head | Global Average Pooling -> Dense(128, ReLU) -> Dropout(0.3) -> Dense(8, Softmax) |
| Input Shape | 224 x 224 x 3 (RGB, INT8 pass-through from ISP) |
| Output | 8-class probability vector (stages 0-7) |
| Total Parameters | ~2.3M (MobileNetV2) + ~130K (custom head) |
| Quantization | INT8 post-training quantization (RKNN-Toolkit2, calibration set of ~500 images spanning all stages and LED modes) |
| Model Size | ~3.5 MB (INT8 .rknn at `/oem/models/stage_mnv2_int8.rknn`) |
| Framework | TensorFlow / Keras (training), RKNN-Toolkit2 (conversion from TFLite/ONNX), rknn_api on the RV1106 NPU (inference) |

### 7.2 Training Pipeline

```
┌────────────────┐    ┌───────────────┐    ┌────────────────┐
│ Data Collection│    │ Augmentation  │    │ Training       │
│ (1000+ images  │──► │ (rotation,    │──► │ (MobileNetV2   │
│  per stage,    │    │  brightness,  │    │  fine-tune,    │
│  real cooking) │    │  crop, color  │    │  50 epochs)    │
└────────────────┘    │  jitter)      │    └───────┬────────┘
                      └───────────────┘            │
                                                   ▼
┌────────────────┐    ┌───────────────┐    ┌────────────────┐
│ Deploy to      │    │ RKNN Convert  │    │ Evaluate       │
│ RV1106 (.rknn  │◄── │ + INT8 Quant. │◄── │ (Validation    │
│ in /oem/models)│    │ (RKNN-Toolkit2│    │  accuracy,     │
└────────────────┘    │  calib. set)  │    │  confusion     │
                      └───────────────┘    │  matrix)       │
                                           └────────────────┘
```

The training pipeline itself is unchanged; only the export step differs. The Keras model is exported to TFLite/ONNX, then converted offline with RKNN-Toolkit2 on the build host using a calibration image set for INT8 quantization. The resulting `.rknn` is validated against the float model on the PC before deployment to `/oem/models`.

### 7.3 Training Data Requirements

| Stage | Min Images | Collection Method | Augmented Total |
|-------|-----------|-------------------|-----------------|
| Raw (0) | 1,000 | Photograph raw ingredients in pot | 5,000 |
| Heating (1) | 1,000 | Video frames of oil heating | 5,000 |
| Browning (2) | 1,500 | Multiple browning levels, various ingredients | 7,500 |
| Liquid Added (3) | 1,000 | Various liquid types (water, broth, puree) | 5,000 |
| Boiling (4) | 1,000 | Video frames of active boiling | 5,000 |
| Simmering (5) | 1,000 | Extended captures during simmering | 5,000 |
| Thickening (6) | 1,500 | Gradual reduction sequences | 7,500 |
| Done (7) | 1,500 | Final states across many recipes | 7,500 |
| **Total** | **9,500** | | **47,500** (after augmentation) |

### 7.4 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Overall Accuracy | >85% | Across all 8 stages |
| Per-Stage Recall | >80% | No stage below 80% recall |
| Inference Latency | <20ms | On RV1106 NPU with INT8 quantization (5-10 ms typical) |
| Model Size | <5 MB | Fits comfortably in the 64 MB `oem` partition |
| False Positive Rate (anomaly) | <5% | Burning/boil-over false alarms |

## 8. Rule-Based Fallback

When CV confidence drops below 0.6 or the camera is unavailable, the system falls back to sensor-based cooking stage estimation:

### 8.1 Fallback Decision Table

| Stage | Temperature Indicator | Time Indicator | Weight Indicator |
|-------|----------------------|----------------|------------------|
| Raw (0) | T < 50 C | t = 0 | Initial weight stable |
| Heating (1) | 50 C < T < 120 C | 0 < t < 3 min | No change |
| Browning (2) | T > 150 C | 2 < t < 8 min | Slight decrease (moisture loss) |
| Liquid Added (3) | T drops sharply | After dispensing | Weight increase (liquid added) |
| Boiling (4) | T = 100 C (+/- 3 C) | After liquid stage | Weight slowly decreasing |
| Simmering (5) | 80 C < T < 95 C | After boil | Weight slowly decreasing |
| Thickening (6) | T rising above 95 C | >70% cook time elapsed | Significant weight loss (>15%) |
| Done (7) | Stable T, recipe timer expired | Cook time complete | Target weight reached |

### 8.2 Fallback Activation

```
IF camera.status == OFFLINE OR last_inference.confidence < 0.6:
    mode = FALLBACK
    stage = estimate_from_sensors(temperature, weight, elapsed_time)
    notify_user("Vision degraded, using sensor-based cooking")
    log_event(VISION_FALLBACK, reason)
ELSE:
    mode = VISION
    stage = last_inference.stage_id
```

## 9. Anomaly Detection

### 9.1 Critical Anomalies

| Anomaly | Detection Method | Trigger Condition | Action |
|---------|-----------------|-------------------|--------|
| Burning | Sudden darkening in frame + temperature spike | Dark pixel ratio > 40% AND T > 220 C | Reduce heat to 0%, alert user, pause cooking |
| Boil-Over | Liquid detected at pot rim (region of interest) | Brightness/motion at rim ROI > threshold | Reduce power to 30%, pause stirring, alert |
| Empty Pot | No contents detected in pot area | Frame variance < threshold (flat surface) | Stop heating immediately, alert user |
| Foreign Object | Unexpected shape/color in pot | Classification confidence < 0.3 for all stages | Pause cooking, alert user to inspect |

### 9.2 Anomaly Detection Pipeline

```
┌──────────────┐
│ Camera Frame │
│ (224x224     │
│  self-path)  │
└──────┬───────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌──────────────┐                     ┌──────────────────┐
│ Stage        │                     │ Anomaly Checks   │
│ Classification│                    │ (parallel)       │
│ (NPU, RKNN)  │                     │                  │
└──────┬───────┘                     │ 1. Dark pixel %  │
       │                             │ 2. Rim ROI motion│
       │                             │ 3. Frame variance│
       │                             │ 4. Confidence    │
       │                             │    analysis      │
       │                             └────────┬─────────┘
       │                                      │
       ▼                                      ▼
┌──────────────┐                     ┌──────────────────┐
│ Recipe       │                     │ Safety Action    │
│ Engine       │                     │ (if anomaly)     │
│ (normal flow)│                     │ - Reduce heat    │
└──────────────┘                     │ - Alert user     │
                                     │ - Log event      │
                                     └──────────────────┘
```

The pixel statistics (dark pixel ratio, rim ROI motion, frame variance) are computed in C on the 224 x 224 self-path frame at 2 Hz, which costs well under 1 ms per frame on the Cortex-A7.

## 10. Live Feed Streaming

### 10.1 Streaming Architecture

| Destination | Protocol | Resolution | Frame Rate | Latency Target |
|-------------|----------|------------|------------|----------------|
| Touchscreen (LVGL "view pot" screen) | ISP main path → RGA scale → framebuffer (local, on demand) | 480x320 | ≤10 fps | <100ms |
| Mobile App | On-demand H.264 RTSP (`rtsp://<device>:554/pot`, direct on same LAN, else cloud relay) | 720p, 1.5 Mbps | 15 fps | <500ms (LAN), <2s (relay) |
| CV Inference | ISP self-path DMA buffer | 224x224 | 2 fps | <50ms |

### 10.2 Touchscreen Pot Preview (LVGL)

- Optional "view pot" screen only; the normal cooking screens show state, temperature and timers without video.
- Path: ISP main path (1280x720 NV12) → RGA scale + colour convert to 480x320 RGB565 → LVGL canvas on `/dev/fb0`, ≤10 fps.
- Enabled only while the screen is open; dropped automatically under memory pressure (free RAM < 32 MB).
- CV confidence overlay is drawn by LVGL on top of the preview.

### 10.3 On-Demand RTSP Live View (Mobile App)

> [!note] No always-on streamer
> The H.264 encoder channel and the `rtsp-stream` child process exist only while a phone is viewing the pot. The device never runs an MJPEG or WebSocket video server; the phone talks to the cloud, or connects directly to the RTSP URL when on the same LAN.

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

- Single viewer at a time. Stream is 1280x720 H.264, 15 fps, 1.5 Mbps (~8 MB of CMA while active).
- `live_view_start` / `live_view_stop` arrive on `epicura/{device_id}/cmd`; the stream is torn down after 60 s with no client.
- Streaming is best-effort: any encoder or RTSP error tears the stream down and never affects cooking or inference.

## 11. Steam Management Solutions

### 11.1 Multi-Layer Approach

| Layer | Solution | Maintenance | Effectiveness |
|-------|----------|-------------|---------------|
| 1. Physical Barrier | Borosilicate glass lens cover | Replace if cracked | Blocks direct steam contact |
| 2. Anti-Fog Coating | Hydrophilic coating on glass (Cat Crap or similar) | Reapply monthly | Prevents condensation droplets |
| 3. Air Curtain | 25mm 5V fan blowing across lens | Clean fan quarterly | Diverts rising steam column |
| 4. ISP Dehaze | Hardware dehaze block in the RV1106 ISP, always on (strength from SC3336 tuning) | None | Recovers detail in slightly foggy frames at zero CPU cost |
| 5. Capture Timing | Brief air puff (compressed air nozzle) before capture | Refill air canister | Clears lens immediately before frame |

## 12. Calibration

### 12.1 Factory Calibration

| Calibration | Method | Frequency |
|-------------|--------|-----------|
| Color Reference | X-Rite ColorChecker Mini placed in pot, capture reference image | Per-unit (factory) |
| White Balance | Capture under LED ring CAPTURE mode, store ISP AWB gains as a fixed illuminant preset in `/userdata` | Per-unit (factory) |
| Focus Distance | Set focus to pot depth (20-30cm), lock focus ring | Per-unit (factory) |
| LED Uniformity | Capture white reference surface, measure brightness variance | Per-unit (factory) |

### 12.2 Runtime Calibration

| Calibration | Method | Frequency |
|-------------|--------|-----------|
| Auto White Balance | ISP AWB with the LED ring (CAPTURE mode, 5000K) as the known illuminant | Every capture session |
| Exposure Compensation | ISP AE with metering ROI set to pot center | Continuous |
| Steam Compensation | ISP dehaze strength raised when the ISP's contrast statistic drops below threshold | Per-frame |

## 13. Testing and Validation

### 13.1 Test Procedures

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Classification Accuracy | 100 test images per stage, measure per-stage accuracy | >85% overall, >80% per-stage recall |
| Confusion Matrix | Full 8x8 confusion matrix on test set | No off-diagonal >10% |
| INT8 Conversion Fidelity | Compare `.rknn` output to float Keras model on 500 validation images | Top-1 agreement >98% |
| Inference Latency | 1000 inference runs on the NPU, measure mean and P99 latency | Mean <20ms, P99 <30ms |
| Steam Resistance | 30-minute continuous steam exposure, capture frames | Frame clarity metric >70% throughout |
| LED Uniformity | Capture flat white surface, measure brightness std dev | Std dev <10% of mean brightness |
| Low-Light Performance | Capture at 50% LED brightness, run inference | Accuracy drop <5% vs. full brightness |
| Streaming Quality | RTSP live view to app for 1 hour, measure frame drops and latency | Frame drop <2%, latency <500ms (LAN); cooking and inference unaffected |
| Memory Pressure | Stream + inference + preview for 1 hour, monitor free RAM | Peak system usage ≤95 MB; no OOM |
| Anomaly Detection | 50 simulated anomaly events (burning, boil-over) | Detection rate >90%, false positive <5% |
| Fallback Mode | Disable camera, verify sensor-based cooking completes | Recipe completes within +/- 20% of normal cook time |
| Lens Cleaning | Run 10 cook cycles without cleaning, measure clarity degradation | Clarity remains >60% after 10 cycles |

### 13.2 Prototype Validation Checklist

- [ ] SC3336 enumerates on the Pico Zero MIPI CSI port and the SDK ISP tuning file loads
- [ ] ISP main path delivers clear 1280x720 NV12 frames at 30 fps from the mounted position
- [ ] ISP self-path delivers 224x224 RGB888 frames at 2 fps into a DMA buffer (zero copy)
- [ ] LED ring responds to SET_LED (OFF/CAPTURE/NIGHT) from the RV1106 and provides uniform illumination (no hot spots on liquid surface)
- [ ] `.rknn` model loads and runs inference on the RV1106 NPU within 20ms
- [ ] Classification correctly identifies at least 6 of 8 stages on real cooking data
- [ ] Steam protection (physical + ISP dehaze) keeps frames usable for 30-minute continuous cooking
- [ ] RTSP live view starts within 2 s of `live_view_start` and is reachable from the mobile app on the same WiFi network; tears down 60 s after the client leaves
- [ ] LCD pot preview runs at ≤10 fps without stalling the LVGL UI
- [ ] Burning anomaly detection triggers within 5 seconds of simulated burn
- [ ] Boil-over detection triggers before liquid exits pot
- [ ] Fallback mode activates automatically when camera is covered/disabled
- [ ] Color calibration produces consistent readings across 10 capture sessions

## 14. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture]]
- [[02-Controller-Software-Architecture|Controller & Software Architecture]]
- [[../03-Software/05-MCU-Functional-Specification|MCU Functional Specification]]
- [[../../research/04-RV1106-Luckfox-Pico-Zero-Suitability|RV1106 Suitability Assessment]]
- [[01-Induction-Heating|Induction Heating System]]
- [[02-Robotic-Arm|Robotic Arm System]]
- [[03-Ingredient-Dispensing|Ingredient Dispensing System]]
- [[01-Safety-Compliance|Safety & Compliance]]

#epicura #vision-system #computer-vision #ai-ml #subsystem #rv1106 #rknn

---

## 15. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Application processor changed to RV1106 (Luckfox Pico Zero): camera is SC3336 at 1280x720 @ 30 fps (IMX219/IMX477 dropped, no ISP tuning); pipeline is hardware ISP (dehaze/3DNR/AWB) → ISP self-path 224x224 → NPU via RKNN (5-10 ms, INT8 from RKNN-Toolkit2); OpenCV/CLAHE/libcamera removed; MJPEG server replaced by on-demand H.264 RTSP; LED ring driven by STM32 via SET_LED; calibration uses ISP AWB/AE; validation checklist updated. Stage classes, transitions and training pipeline unchanged |
