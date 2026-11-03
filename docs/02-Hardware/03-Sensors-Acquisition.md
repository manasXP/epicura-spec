---
created: 2026-02-15
modified: 2026-11-04
version: 1.1
status: Draft
---

# Sensors & Data Acquisition

## 1. Sensor Overview

| Sensor | Type | Interface | Range | Accuracy | Sampling Rate | Connected To |
|--------|------|-----------|-------|----------|---------------|--------------|
| Camera (SC3336) | CMOS image sensor, 3 MP | MIPI CSI-2 (4-lane FPC) | 1280x720 @ 30fps | N/A (pixel-level) | 2 Hz (CV frames) | Pico Zero CSI connector → RV1106 ISP |
| IR Thermometer (MLX90614) | Non-contact thermopile | I2C (0x5A) | -70 to +380C | +/-0.5C | 10 Hz | STM32 I2C1 |
| Pot Detection | Reed switch / Hall effect | Digital GPIO | On/Off | N/A | Interrupt-driven | STM32 GPIO |

---

## 2. Camera System

### 2.1 Module Selection

| Parameter | SC3336 (Luckfox module) |
|-----------|-------------------------|
| Resolution | 3 MP (2304x1296 native), run at 1280x720 |
| Sensor Size | 1/2.8" |
| Pixel Size | 2.0 um |
| Max Video | 1296p @ 30fps; Epicura uses 720p @ 30fps |
| Interface | MIPI CSI-2 (4-lane FPC to the Pico Zero CSI connector) |
| Lens | Fixed-focus M12, approx. 80 deg diagonal with the stock lens (to be confirmed) |
| Low-Light Performance | Good (2.0 um pixels, ISP 2D/3D noise reduction) |
| ISP Support | RV1106 ISP tuning file shipped in the Luckfox SDK |
| Estimated Cost | $12 (module incl. FPC) |
| Recommendation | **Fixed choice** (IMX219/IMX477 dropped: no RV1106 ISP tuning file) |

**Selection Rationale:** The SC3336 is the Luckfox-supported sensor with an RV1106 ISP tuning file in the SDK, so it is the fixed choice; IMX219 and IMX477 are dropped because the RV1106 ISP has no tuning file for them. Its fixed-focus lens and 3 MP resolution are sufficient for food color/texture classification. Running at 1280x720 rather than 1080p halves ISP/VI buffer memory and encoder load, and is more than sufficient for the 224x224 stage classifier and the phone preview. Dehaze, noise reduction, lens shading, sharpening, AWB and AE all run in the ISP; no CPU image processing is needed.

### 2.2 Camera Mounting

```
┌────────────────────────────────────────────────────┐
│                    Gantry (Top)                     │
│                                                     │
│    Camera Module ──► Mounted on gantry arm          │
│    (facing downward into pot)                       │
│                                                     │
│         ┌──────────────┐                            │
│         │   Camera      │                           │
│         │   (SC3336)    │                           │
│         │   ┌──────┐    │                           │
│         │   │ Lens │    │   ◄── LED Ring            │
│         │   └──┬───┘    │       (surrounding lens)  │
│         └──────┼────────┘                           │
│                │                                    │
│                │  20-30 cm                           │
│                │                                    │
│         ┌──────▼──────────────────────┐             │
│         │                             │             │
│         │         Pot                 │             │
│         │    (diameter ~22cm)         │             │
│         │                             │             │
│         └─────────────────────────────┘             │
│                                                     │
└────────────────────────────────────────────────────┘
```

### 2.3 Field of View

The SC3336 is a 1/2.8" sensor with a fixed-focus M12 lens on the Luckfox module, giving approximately 80 degrees diagonal with the stock lens (to be confirmed on the physical module). At 25 cm above a 22 cm pot, an 80 degree diagonal in a 16:9 720p frame corresponds to roughly 36 cm of horizontal and 20 cm of vertical coverage, so the vertical axis is the limiting one: mount toward the top of the 20-30 cm range, or fit a wider M12 lens, if the measured FOV does not cover the full pot rim with margin. The 720p mode may also crop the native 2304x1296 frame, which narrows the effective FOV further. Measure on hardware before fixing the gantry height.

### 2.4 Lighting System

#### 2.4.1 LED Ring Specifications

| Parameter | Value |
|-----------|-------|
| Type | WS2812B addressable RGB LEDs |
| Count | 12-16 LEDs in ring configuration |
| Ring Diameter | 50-60mm (surrounds camera lens) |
| Color Temperature | Neutral white (5000-6500K, RGB mixed) |
| Brightness | Software-adjustable, 0-100% |
| Interface | Single-wire data (800 kHz) from STM32 PB14 (TIM15_CH1 PWM + DMA) via 74AHCT1G125 3.3→5V level shifter; modes requested by the RV1106 via SET_LED |
| Power | 5V (switched by PCF8574 #2 P3), ~60mA per LED at full white (total ~1A max) |

#### 2.4.2 Lighting Design

- **Consistent Illumination:** Ring around camera lens provides even, shadow-free lighting on food surface
- **Anti-Glare:** Diffuser film over LEDs reduces specular reflections from liquid surfaces (oil, water)
- **Color Accuracy:** Neutral white enables reliable food color detection (e.g., golden-brown vs. burnt)
- **Adjustable:** Software dims LEDs during non-imaging periods to reduce heat/power

### 2.5 Calibration

- **White Balance:** Calibrate on boot using a white reference card placed on pot. Store AWB gains per unit.
- **Color Reference:** Optional X-Rite ColorChecker patch card for factory calibration of color reproduction
- **Per-Unit Calibration:** Each unit stores calibration data in `/data/calibration/camera.json` on eMMC
- **Recalibration:** User-triggered recalibration via Settings menu (place white card, press button)

---

## 3. IR Thermometer (MLX90614)

### 3.1 Specifications

| Parameter | Value |
|-----------|-------|
| Part Number | MLX90614ESF-BAA |
| Type | Non-contact infrared thermopile |
| Object Temperature Range | -70C to +380C |
| Ambient Temperature Range | -40C to +125C |
| Accuracy (0-50C ambient) | +/-0.5C |
| Accuracy (full range) | +/-1.0C |
| Resolution | 0.02C |
| Field of View | 90 degrees (wide FOV variant) |
| Interface | I2C / SMBus (address 0x5A) |
| Supply Voltage | 3.3V (2.6V to 3.6V) |
| Current Consumption | 1.5 mA (typical) |
| Response Time | 100ms (to 90% of final value) |

### 3.2 Mounting Configuration

```
                     ┌──── Gantry Arm ────┐
                     │                    │
                     │   ┌────────────┐   │
                     │   │  MLX90614  │   │
                     │   │  (angled   │   │
                     │   │   ~30 deg) │   │
                     │   └─────┬──────┘   │
                     │         │          │
                     │         │ IR beam  │
                     │         │ (90 deg  │
                     │         │  FOV)    │
                     │         ▼          │
              ┌──────┴─────────────────────┴──────┐
              │                                    │
              │         Pot (center area)           │
              │     Food surface measurement        │
              │                                    │
              └────────────────────────────────────┘

Mounting distance: 5-10 cm from food surface
Aim: Center of pot
FOV at 7cm distance: covers ~14cm diameter circle
(adequate for pot center measurement)
```

### 3.3 Emissivity Calibration

Different food surfaces have different IR emissivity values, affecting temperature accuracy:

| Surface | Emissivity | Notes |
|---------|-----------|-------|
| Water | 0.95-0.98 | Highly consistent |
| Cooking Oil | 0.90-0.95 | Depends on oil type |
| Food (general) | 0.90-0.97 | Curries, stews, sauces |
| Metal (pot rim) | 0.10-0.30 | Avoid measuring bare metal |
| Non-stick coating | 0.85-0.95 | Ceramic or PTFE |

- **Default Emissivity:** 0.95 (suitable for most food/water surfaces)
- **Configurable:** Recipe engine can set emissivity per recipe stage (e.g., dry spices vs. liquid gravy)
- **Calibration:** Compare IR reading against reference thermometer in water bath at 50C, 70C, 90C

### 3.4 I2C Wiring Diagram

```
STM32G474RE                        MLX90614ESF-BAA
┌──────────────────┐              ┌──────────────────┐
│                  │              │                  │
│  PA15 (SCL) ────┼──────┬──────┼──── Pin 3 (SCL) │
│                  │      │      │                  │
│  PB7 (SDA) ─────┼──────┼──┬───┼──── Pin 1 (SDA) │
│                  │      │  │   │                  │
│  3.3V ───────────┼──┬───┘  │   │  Pin 2 (VDD) ───┼── 3.3V
│                  │  │      │   │                  │
│                  │  R1     R2  │  Pin 4 (VSS) ───┼── GND
│                  │  4.7k   4.7k│                  │
│                  │  │      │   │                  │
│  GND ────────────┼──┴──────┴───┼──── GND          │
│                  │              │                  │
└──────────────────┘              └──────────────────┘

R1, R2: 4.7k ohm pull-up resistors to 3.3V
C1: 100nF ceramic decoupling cap on VDD (close to MLX90614)
Cable: Shielded 4-wire, <30cm length
Shield: Connected to GND at STM32 end only
```

### 3.5 STM32 Software Interface

```c
// MLX90614 I2C read sequence (simplified)
#define MLX90614_ADDR   0x5A
#define MLX90614_TOBJ1  0x07  // Object temperature register

float mlx90614_read_object_temp(I2C_HandleTypeDef *hi2c) {
    uint8_t buf[3];
    HAL_I2C_Mem_Read(hi2c, MLX90614_ADDR << 1,
                     MLX90614_TOBJ1, I2C_MEMADD_SIZE_8BIT,
                     buf, 3, 100);
    uint16_t raw = buf[0] | (buf[1] << 8);
    // Temperature in Kelvin * 50, convert to Celsius
    float temp_c = (raw * 0.02f) - 273.15f;
    return temp_c;
}
```

---

---

## 4. Pot Detection

### 5.1 Mechanism

A reed switch (or Hall effect sensor) detects the presence of a ferromagnetic pot on the induction platform. A small magnet is embedded in the pot base; when the pot is placed on the platform, the reed switch closes.

```
        ┌── Pot Base (with embedded magnet) ──┐
        │                                      │
        │          [N ▓▓ S]  Magnet            │
        │                                      │
        └──────────────────────────────────────┘
                         │
                    ~2-5mm gap
                         │
        ┌──────────────────────────────────────┐
        │      Platform Surface                │
        │                                      │
        │     ┌──────────────────┐             │
        │     │   Reed Switch    │             │
        │     │   (NC or NO)     │             │
        │     └───┬──────────┬───┘             │
        │         │          │                 │
        └─────────┼──────────┼─────────────────┘
                  │          │
              STM32 PB1   GND (with 10k pull-up to 3.3V)
              (GPIO input,
               interrupt-capable)

Alternative: Hall effect sensor (SS49E or A3144)
  - More robust (no mechanical contacts)
  - Analog output (SS49E) or digital (A3144)
  - Requires small magnet in pot base
```

### 4.2 Interlock Logic

1. On boot, STM32 queries microwave surface module via CAN for pot detection status
2. If pot not detected, display "Place pot" on UI
3. Module will not heat without pot detected (internal interlock)
4. If pot removed during cooking, module stops heating internally; STM32 receives status via CAN
5. Recipe pauses and UI shows "Pot removed" warning
6. When pot replaced, resume after 3-second confirmation delay

---

## 5. Sensor Fusion

### 5.1 Multi-Sensor Cooking Stage Detection

The recipe engine on the RV1106 combines data from multiple sensors to determine the current cooking stage and trigger transitions:

```
┌─────────────────────────────────────────────────────────┐
│                  Sensor Fusion Pipeline                  │
│                                                         │
│  Camera (2Hz)                                           │
│  ├── Color histogram ──────────┐                        │
│  ├── Texture features ─────────┤                        │
│  └── Bubble detection ─────────┤                        │
│                                │                        │
│  IR Temp (10Hz)                ├──► Stage Classifier    │
│  ├── Surface temperature ──────┤    (RV1106 NPU,        │
│  └── Rate of change ───────────┘     RKNN INT8)         │
│                                         │              │
│                                         ▼              │
│                                    Cooking Stage ID    │
│                                    (e.g., "browning",  │
│                                      "boiling",         │
│                                      "simmering",       │
│                                      "done")            │
│                                         │               │
│                                         ▼               │
│                                   Recipe State Machine   │
│                                   (next action:          │
│                                    adjust temp,          │
│                                    add ingredient,       │
│                                    change stir speed)    │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Decision Matrix

| Cooking Stage | Camera Signal | IR Temp (C) | Confidence |
|---------------|---------------|-------------|------------|
| Raw/Cold | Raw ingredient colors, no bubbles | <50 | High |
| Heating | Slight color shift, steam wisps | 50-90 | Medium |
| Boiling | Active bubbles, steam, rolling motion | 95-102 | High |
| Browning | Golden-brown color shift, darkening edges | 120-180 | High |
| Simmering | Gentle bubbles, consistent color | 80-95 | High |
| Thickening | Darker color, less liquid visible | 85-100 | Medium |
| Done | Target color/texture reached | Recipe-specific | Recipe-dependent |
| Burning (ALERT) | Dark/black spots, smoke detection | >200 | High |

### 5.3 Sampling Rate Summary

| Sensor | Acquisition Rate | Processing Rate | Latency Budget |
|--------|-----------------|-----------------|----------------|
| Camera | 30 fps capture | 2 Hz CV inference | <500ms per frame |
| IR Thermometer | 10 Hz read | 10 Hz to PID | <100ms |
| Pot Detection | Interrupt-driven | Immediate (<1ms) | <1ms |

---

## 6. Sensor Quality Monitoring

### 6.1 Health Check Table

| Sensor | Health Check | Pass Criteria | Failure Mode |
|--------|-------------|---------------|--------------|
| Camera | Frame received, not black/white | Valid histogram, >10% variance | Lens blocked, cable loose, module fault |
| IR Thermometer | I2C ACK, reading in range | ACK on address, -20C < T < 350C | I2C bus fault, sensor damaged |
| Pot Detection | State change matches expectations | Toggles when pot placed/removed | Switch stuck, magnet missing |

### 6.2 Degradation Fallback Strategy

| Primary Sensor Failed | Fallback Strategy | Limitations |
|-----------------------|-------------------|-------------|
| Camera fails | Timer-based cooking (no CV stage detection) | Cannot detect browning, must rely on time/temp |
| IR thermometer fails | CAN coil temp + camera (color-based temp estimation) | Less accurate food temp, wider PID margins |

---

## 7. Testing & Validation

### 7.1 Camera Test Procedures

- [ ] Mount camera at 25cm height, verify full pot is in frame
- [ ] Measure the actual FOV of the SC3336 stock lens at 25cm (horizontal and vertical, 720p mode); confirm pot rim margin and fix gantry height
- [ ] Verify 1280x720 @ 30fps on the ISP main path and 224x224 self-path frames reaching the NPU at 2 Hz
- [ ] Capture image of white card, verify white balance (R/G/B within +/-10%)
- [ ] Capture image of X-Rite ColorChecker, verify color accuracy (deltaE < 5)
- [ ] LED ring on (SET_LED CAPTURE mode via STM32): verify even illumination (no hot spots >20% variance)
- [ ] LED ring off: verify camera captures adequate image under typical kitchen lighting
- [ ] Steam test: boil water for 10 minutes, verify lens does not fog (shroud effective)
- [ ] FPS test: verify 30fps capture sustained over 30 minutes

### 7.2 IR Thermometer Test Procedures

- [ ] Read room temperature, compare to reference thermometer (+/-1C)
- [ ] Read boiling water surface, verify 97-102C (altitude-dependent)
- [ ] Read 70C water bath, compare to reference (+/-1C)
- [ ] Read cooking oil at 180C, compare to reference (+/-3C)
- [ ] Emissivity test: compare readings for water (0.95) vs. oil (0.92)
- [ ] Steam interference: verify stable reading during active boiling
- [ ] Response time: apply sudden temp change, verify 90% response in <200ms

### 7.3 Pot Detection Test Procedures

- [ ] Place pot: verify detection within 100ms
- [ ] Remove pot: verify detection within 100ms
- [ ] Verify interlock: attempt to enable induction without pot, confirm rejection
- [ ] Verify interlock: remove pot during heating, confirm shutdown within 100ms
- [ ] Test with non-magnetic pot: verify no false detection

---

## 8. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture & Wiring Diagrams]]
- [[04-Mechanical-Design|Mechanical Design]]
- [[02-Controller-Software-Architecture|Controller & Software]]

#epicura #sensors #data-acquisition

---

## 9. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Camera changed to SC3336 3 MP at 1280x720 on the Luckfox Pico Zero (RV1106G3) 4-lane CSI with hardware ISP; IMX219/IMX477 dropped; FOV section rewritten (stock-lens FOV to be confirmed); LED ring now STM32-driven via level shifter; sensor fusion runs on the RV1106 NPU; camera test checklist updated |
