---
created: 2026-02-15
modified: 2026-11-04
version: 1.6
status: Draft
---

# Sensors & Data Acquisition

## 1. Sensor Overview

| Sensor | Type | Interface | Range | Accuracy | Sampling Rate | Connected To |
|--------|------|-----------|-------|----------|---------------|--------------|
| Camera (IMX415-98) | CMOS image sensor, 8 MP | MIPI CSI-2 (4-lane FPC) | 1280x720 @ 30fps | N/A (pixel-level) | 2 Hz (CV frames) | Pico Zero CSI connector → RV1106 ISP |
| Cooking surface temperature | Heating-unit-internal spring-loaded centre sensor (NTC, pot-bottom) reported in HEAT_STATUS | Isolated CAN (0x180) | Unit-reported, typ. 0-300C | Unit accuracy (typ. +/-3-5C) | 10 Hz | Heating unit MCU → RV1106 + STM32 |
| Battery pack voltage + current | INA219 #2 (0x44), 10 mΩ shunt in the BAT+ path | I2C3 | 0-26 V, ±3.2 A | +/-1% | 1 Hz | RV1106 I2C3 (Unified PCB v4.0, Dispensing Unit) → state of charge |
| SLD load cells (×2) | Strain-gauge 2 kg, one per reservoir | I2C (NAU7802 24-bit ADC, 0x2A, behind TCA9543A 0x71) | 0-2 kg | +/-5% dispense | 10 Hz | RV1106 I2C3 (`dispense` thread) |
| Pot Detection (backup) | Reed switch / Hall effect | Digital GPIO | On/Off | N/A | Interrupt-driven | STM32 PB1 on the CSC (J_SAFE pin 2); primary pot detection is the heating unit's HEAT_STATUS (`pot_detected`, centre sensor) |
| Dock sense | DOCK_SENSE_A contact (low = docked) | Digital GPIO, 10k pull-up | Docked / lifted | N/A | GPIO edge + 1 Hz | RV1106 GPIO (DU); DOCK_SENSE_B → STM32 PB3 (CSC) |
| Dock power | DOCK_PWR_OK (100k/10k divider on DOCK_24V → 2N7002, active-low) | Digital GPIO | DOCK_24V present / absent | N/A | 1 Hz | RV1106 GPIO (DU) |

---

## 2. Camera System

### 2.1 Module Selection

| Parameter | IMX415-98 (Luckfox module) |
|-----------|-------------------------|
| Resolution | 8.29 MP (3840×2160 native), run at 1280x720 |
| Sensor Size | 1/2.8" |
| Pixel Size | 1.45 um (Sony STARVIS, back-illuminated) |
| Max Video | 2160p @ 15fps on 4 lanes; Epicura uses 720p @ 30fps |
| Interface | MIPI CSI-2, 4-lane, 22-pin FPC (supplied) to the Pico Zero CSI connector |
| Lens | 3.95 mm F2.0 M12, 98 deg diagonal / 84 deg horizontal / 44 deg vertical, distortion < 1%, manual focus, switchable IR-CUT (held in the visible-light position) |
| Low-Light Performance | Very good (STARVIS pixels, ISP 2D/3D noise reduction) |
| ISP Support | RV1106 ISP tuning file shipped in the Luckfox SDK |
| Estimated Cost | $54 (Luckfox IMX415-98 IR-CUT module incl. 22-pin FPC) |
| Recommendation | **Fixed choice** (IMX219/IMX477 dropped: no RV1106 ISP tuning file) |

**Selection Rationale:** The IMX415-98 IR-CUT is the colour camera Luckfox supports on the Pico Zero (its CSI tutorial and factory image target this module), so it is the fixed choice. Luckfox's SC3336 module, used on the other Pico boards, is listed by Luckfox as not compatible with the Pico Zero; IMX219 and IMX477 are dropped because the RV1106 ISP has no tuning file for them. Its 98 deg lens and 8 MP resolution are more than sufficient for food color/texture classification. Running at 1280x720 rather than 1080p halves ISP/VI buffer memory and encoder load, and is more than sufficient for the 224x224 stage classifier and the phone preview. Dehaze, noise reduction, lens shading, sharpening, AWB and AE all run in the ISP; no CPU image processing is needed.

### 2.2 Camera Mounting

```
┌────────────────────────────────────────────────────┐
│          Dispensing Unit (DU) underside             │
│                                                     │
│    Camera Module ──► Mounted on the DU underside,   │
│    centred over the pot, looking straight down      │
│    behind a sealed borosilicate window              │
│                                                     │
│         ┌──────────────┐                            │
│         │   Camera      │                           │
│         │   (IMX415-98) │                           │
│         │   ┌──────┐    │                           │
│         │   │ Lens │    │   ◄── White LED Ring      │
│         │   └──┬───┘    │       (surrounding lens,  │
│         └──────┼────────┘        RV1106 PWM)        │
│         ═══════╪════════  sealed borosilicate window│
│                │  20-30 cm (nominal 30 cm)          │
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

The IMX415-98 lens is specified by Luckfox at 98 deg diagonal, 84 deg horizontal and 44 deg vertical (3.95 mm, F2.0, distortion < 1%). In a 16:9 720p frame the vertical axis is the limiting one: at 25 cm above the pot the coverage is about 45 x 20 cm, which does not clear a 22 cm pot rim, while at 30 cm it is about 54 x 24 cm. The nominal mounting height is therefore **30 cm** above the pot rim, giving ~1 cm margin on the short axis and ample width for the LED ring and ladle. The 720p output is produced by the ISP scaling the full sensor frame, so the full FOV is retained; if the Rockchip driver only offers a cropped 720p sensor mode, use the 1080p (2x2 binned) mode and scale in the ISP instead. Confirm the measured coverage on the assembled three-unit stack before fixing the DU seating height.

### 2.4 Lighting System

#### 2.4.1 LED Ring Specifications

| Parameter | Value |
|-----------|-------|
| Type | White LEDs, 5000 K, CRI ≥ 90 (no addressable RGB, no colour control) |
| Count | 12-16 LEDs in ring configuration |
| Ring Diameter | 50-60mm (surrounds the camera lens behind the DU underside window) |
| Color Temperature | 5000 K white |
| Brightness | RV1106 PWM duty: OFF 0 %, NIGHT 30 %, CAPTURE 100 % |
| Interface | RV1106 PWM (1 kHz) → Q_LED (IRLML6344 low-side) on the Unified PCB v4.0 → J_LED 2-pin (5V_MAIN / LED_RET); no STM32 or CAN involvement |
| Power | 5V_MAIN, ≤ 1 A at CAPTURE |

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

## 3. Cooking Temperature (Unit-Reported)

Epicura has no temperature sensor of its own. The IR thermometer of earlier revisions (MLX90614) is dropped because the commercial electric heating unit (rice-cooker class, see [[../05-Subsystems/01-Electric-Heating|Electric Heating]]) runs its own closed-loop temperature control on a spring-loaded centre sensor pressed by the pot and reports the measured temperature on the isolated CAN bus.

| Parameter | Value |
|-----------|-------|
| Source | HEAT_STATUS (CAN 0x180), field `surface_temp_dC` (int16, 0.1 °C), 10 Hz |
| What it measures | Pot-bottom temperature at the centre sensor, not the food surface |
| Setpoint path | RV1106 sends HEAT_SET_TEMP (0x100) or HEAT_SET_POWER (0x103); the unit regulates |
| Consumers | RV1106 engine thread (stage transitions, UI graph), STM32 safety monitor (over-temperature cut-off at 270 °C) |
| Accuracy | Unit-specified; verified against a thermocouple on the pot bottom during bring-up (±5 °C at 100 °C target) |
| Food-state detection | Camera + CV pipeline (browning, boiling, thickening) — see §5 |

> [!note]
> Because the reading is the pot-bottom temperature, recipe `temp_target` values are pot-bottom targets calibrated during recipe development. Boiling water reads above 100 °C at the centre sensor, and the plate's stored heat makes the reading lag the power command by tens of seconds; the CV pipeline, not the temperature, decides "boiling".

---

## 4. Pot Detection

### 5.1 Mechanism

Primary pot detection is inside the heating unit: the pot presses the spring-loaded centre sensor and the unit reports `pot_detected` in HEAT_STATUS. The optional backup below is unchanged: a reed switch (or Hall effect sensor) on the CSC detects a small magnet embedded in the pot base; when the pot is placed on the heating plate, the reed switch closes.

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
        CSC STM32 PB1     GND (with 10k pull-up to 3.3V)
        (J_SAFE pin 2, GPIO input,
         interrupt-capable; optional backup
         to the unit's own pot detection)

Alternative: Hall effect sensor (SS49E or A3144)
  - More robust (no mechanical contacts)
  - Analog output (SS49E) or digital (A3144)
  - Requires small magnet in pot base
```

### 4.2 Interlock Logic

1. On boot, the RV1106 queries the heating unit (HEAT_QUERY) on the shared CAN bus; both processors read pot detection from HEAT_STATUS
2. If pot not detected, display "Place pot" on UI
3. The unit will not heat without pot detected (internal interlock)
4. If pot removed during cooking, the unit stops heating internally; both processors receive the status via CAN and the RV1106 sends HEAT_SET_POWER 0
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
│  Surface Temp (CAN, 10Hz)      ├──► Stage Classifier    │
│  ├── Unit-reported temp ───────┤    (RV1106 NPU,        │
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

| Cooking Stage | Camera Signal | Surface Temp (C, unit-reported) | Confidence |
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
| Surface Temperature | 10 Hz HEAT_STATUS from the heating unit on CAN | 1 Hz engine tick (stage logic), 10 Hz STM32 safety monitor | <200ms |
| Pot Detection | Interrupt-driven | Immediate (<1ms) | <1ms |
| SLD Load Cells | 10 Hz NAU7802 (I2C3 via TCA9543A) | 10 Hz `dispense` thread closed loop | <100ms |
| Battery / Dock | 1 Hz INA219 #2; DOCK_SENSE_A edge; DOCK_PWR_OK | 1 Hz power/dock monitor; UNIT_LIFTED on edge | <300ms (TELEMETRY timeout confirms mains loss) |

---

## 6. Sensor Quality Monitoring

### 6.1 Health Check Table

| Sensor | Health Check | Pass Criteria | Failure Mode |
|--------|-------------|---------------|--------------|
| Camera | Frame received, not black/white | Valid histogram, >10% variance | Lens blocked, cable loose, module fault |
| Surface Temperature | HEAT_STATUS received, reading in range | Frame every ≤ 500 ms, -20C < T < 350C | CAN bus fault, unit sensor fault (fault_flags) |
| Pot Detection | State change matches expectations | Toggles when pot placed/removed | Switch stuck, magnet missing |
| SLD Load Cells | NAU7802 ACK + data-ready, stable tare | DRDY ≤ 100 ms, drift < 2 g/min | NAU7802 I2C NACK / no data-ready → SLD_LOAD_CELL_DRIFT (RV1106-detected) |
| Battery / Dock | INA219 #2 reading in range; DOCK_SENSE_A and DOCK_PWR_OK consistent | 5.5 V < V < 8.5 V; PWR_OK only while docked | I2C NACK, pack PCM fault, fouled dock contacts |

### 6.2 Degradation Fallback Strategy

| Primary Sensor Failed | Fallback Strategy | Limitations |
|-----------------------|-------------------|-------------|
| Camera fails | Timer-based cooking (no CV stage detection) | Cannot detect browning, must rely on time/temp |
| Unit centre sensor fails (fault flag or no HEAT_STATUS) | Pause; if element temperature is still reported, allow power-mode stages with timers + camera | No temperature-mode stages; user prompted |

---

## 7. Testing & Validation

### 7.1 Camera Test Procedures

- [ ] Seat the DU; verify the camera window is 30cm above the pot rim and the full pot is in frame
- [ ] Verify IMX415-98 coverage at 30cm in the 720p ISP output (expected ~54 x 24 cm from the 84/44 deg H/V spec); confirm the ISP scales the full frame rather than cropping; confirm pot rim margin and fix the DU seating height
- [ ] Verify 1280x720 @ 30fps on the ISP main path and 224x224 self-path frames reaching the NPU at 2 Hz
- [ ] Capture image of white card, verify white balance (R/G/B within +/-10%)
- [ ] Capture image of X-Rite ColorChecker, verify color accuracy (deltaE < 5)
- [ ] LED ring on (RV1106 PWM CAPTURE 100 %): verify even illumination (no hot spots >20% variance); NIGHT 30 % usable for the on-demand preview
- [ ] LED ring off: verify camera captures adequate image under typical kitchen lighting
- [ ] Steam test: boil water for 10 minutes, verify the sealed borosilicate window does not fog
- [ ] FPS test: verify 30fps capture sustained over 30 minutes

### 7.2 Surface Temperature Test Procedures

- [ ] HEAT_STATUS arrives at 10 Hz on the isolated CAN bus; `surface_temp_dC` is parsed by both the RV1106 and the STM32
- [ ] Compare unit surface_temp against a thermocouple clamped to the pot bottom at 60C, 100C, 180C (+/-5C)
- [ ] HEAT_SET_TEMP 100C with 1L water: unit settles within +/-5C in < 180 s (plate-limited ramp), overshoot < 10C
- [ ] Remove HEAT_SET_TEMP keep-alive: unit drops to zero power within 1 s
- [ ] STM32 cut-off: inject surface_temp > 270C on a bench CAN node, verify HEAT_ON_OFF=0, E_STOP and relay open within 100 ms

### 7.3 Pot Detection Test Procedures

- [ ] Place pot: verify detection within 100ms
- [ ] Remove pot: verify detection within 100ms
- [ ] Verify interlock: attempt to enable heating without pot, confirm rejection (centre sensor not pressed)
- [ ] Verify interlock: remove pot during heating, confirm shutdown within 100ms
- [ ] Test with non-magnetic pot: verify no false detection

### 7.4 Battery, Dock & Load Cell Test Procedures

- [ ] INA219 #2 pack voltage and current agree with a bench meter (±1 %) at idle (~3 W lifted) and while charging (1.0 A docked)
- [ ] Dock: seat the DU, verify DOCK_SENSE_A (RV1106) and DOCK_SENSE_B (STM32 PB3) both read low within 100 ms and DOCK_PWR_OK follows DOCK_24V
- [ ] Lift the DU: verify DOCK_SENSE_A high → PAUSED (UNIT_LIFTED) and dock pads de-energised (Q_DOCK off) within 100 ms
- [ ] Pull mains while docked: DOCK_PWR_OK inactive + TELEMETRY timeout (300 ms) → AC-failure pause; the DU keeps running on its pack
- [ ] Load cells: tare each NAU7802 channel through the TCA9543A, verify ±2 g at 100 g and 500 g reference masses, drift < 2 g over 10 min

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
| 1.2 | 2026-11-04 | Manas Pradhan | Camera changed to Luckfox IMX415-98 IR-CUT (8 MP, 98/84/44 deg FOV): SC3336 is not compatible with the Pico Zero; FOV section rewritten with datasheet figures, nominal height 30 cm |
| 1.3 | 2026-11-04 | Manas Pradhan | Pot-detection interlock and IR data flow updated for the shared CAN bus (PID on the RV1106) |
| 1.4 | 2026-11-04 | Manas Pradhan | IR thermometer (MLX90614) dropped: cooking temperature is the induction module's own under-glass sensor reported in HEAT_STATUS; §3 rewritten, fusion/health/fallback tables and tests updated; battery pack voltage added to the sensor table |
| 1.5 | 2026-11-04 | Manas Pradhan | Three-unit architecture: battery voltage/current via INA219 #2 and SLD load cells via NAU7802 (TCA9543A mux) on RV1106 I2C3; pot reed on the CSC (STM32 PB1); dock sense / dock power rows added; white PWM LED ring driven by the RV1106 (WS2812B, SET_LED and STM32 removed); camera on the Dispensing Unit underside looking straight down; sampling, health and test checklists updated |
| 1.6 | 2026-11-04 | Manas Pradhan | Heater is now a commercial electric heating unit (rice-cooker class) instead of the induction surface: cooking temperature comes from its spring-loaded centre (pot-bottom) sensor, pot detection is the pot pressing that sensor (`pot_detected`; no ferromagnetic pot, reed backup unchanged), `coil` → `element` temperature; §3, §4, fusion/health/fallback tables and tests updated (settle < 180 s) |
