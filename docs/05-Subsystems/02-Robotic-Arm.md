---
created: 2026-02-15
modified: 2026-11-04
version: 3.0
status: Draft
---

# Robotic Arm System

## 1. Overview

The robotic arm is a single-axis rotary stirring mechanism mounted above the cooking pot on a gantry frame. It provides autonomous stirring, scraping, and folding actions driven by the recipe state machine. The arm is driven by a 24V integrated BLDC servo motor with a **CAN bus interface**, commanded by the STM32 over the Unified PCB's regular (non-isolated) CAN port (FDCAN2, J_CAN_STIR) with velocity and position commands, and powered from a switched 24 V output (J_STIR_PWR). The RV1106 application processor selects patterns and speeds over the isolated host CAN bus; the STM32 translates them into motor commands.

## 2. Arm Assembly Design

### 2.1 Mechanical Configuration

- **Type:** Single-axis rotary arm, gantry-mounted above pot center
- **Motion:** 360-degree continuous rotation around the vertical axis
- **Depth:** Fixed paddle depth in V1 (adjustable via manual set screw during setup)
- **Paddle:** Removable silicone or nylon blade, heat-resistant, food-safe
- **Drive:** 24V BLDC motor at top of gantry, coupled to a vertical drive shaft through a bearing and seal

### 2.2 Assembly Diagram

```
┌─────────────────────────────────────────────┐
│                 GANTRY TOP                  │
│                                             │
│            ┌──────────────┐                 │
│            │ CAN Servo    │ ◄── CAN (FDCAN2) + 24 V
│            │ Motor (24V,  │     from the Unified PCB
│            │ integ. drive)│                 │
│            └──────┬───────┘                 │
│                   │                         │
│            ┌──────┴───────┐                 │
│            │ Shaft Coupler│                 │
│            │ (Aluminum)   │                 │
│            └──────┬───────┘                 │
│                   │                         │
│            ┌──────┴───────┐                 │
│            │ Drive Shaft  │                 │
│            │ (304 SS,     │                 │
│            │  6mm dia.)   │                 │
│            └──────┬───────┘                 │
│                   │                         │
│            ┌──────┴───────┐                 │
│            │ Bearing +    │ ◄── Sealed bearing
│            │ Steam Seal   │     prevents ingress
│            └──────┬───────┘                 │
│                   │                         │
│  ┌────────────────┴────────────────────┐    │
│  │          COOKING POT                │    │
│  │                                     │    │
│  │         ┌───────────┐               │    │
│  │         │  Paddle   │ ◄── Twist-lock
│  │         │  (Silicone│     removable
│  │         │   Blade)  │               │    │
│  │         └───────────┘               │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

## 3. Motor Selection

### 3.1 CAN Servo Motor Specifications

| Parameter | Value |
|-----------|-------|
| Motor Type | 24V integrated BLDC servo (motor + planetary gearbox + encoder + driver in one housing) with CAN bus interface — CyberGear/RobStride-class actuator or an industrial 24 V BLDC gearmotor with a CAN driver (model TBD) |
| Supply Voltage | 24V DC from the Unified PCB switched rail (J_STIR_PWR, 5 A fuse, Q_STIR high-side switch) |
| Continuous / Peak Torque | ≥ 3 N·m (30 kg-cm) continuous, ≥ 5 N·m peak |
| Speed Range | 0-300 RPM at the output shaft |
| Control Interface | CAN 2.0B, 1 Mbps, 29-bit IDs (motor protocol); velocity mode for stirring, position mode for homing/parking; enable/disable, zero-set and parameter frames |
| Feedback | Encoder position (absolute single-turn, ≥ 14-bit), velocity, phase current, driver temperature, fault flags — streamed at the command rate (50 Hz) |
| Command timeout | Configurable; set to ≤ 500 ms so a silent bus stops the motor |
| Gear Type | Planetary gearbox (integrated) |
| IP Rating | IP54 or better recommended (kitchen environment) |
| Weight | ~300-500g (varies by model) |
| Price (approx.) | $35-60 USD |

### 3.2 Selection Rationale

The CAN servo replaces the PWM/EN/DIR BLDC of revision 2.x for the following advantages:

- **Closed-loop speed and position** — the integrated encoder gives true RPM and shaft angle, so stirring speed, scrape offsets and parking are exact; no FG tachometer or PA3 reservation needed
- **Stall and over-torque from the source** — the motor reports phase current and temperature; stall detection no longer relies on the INA219 24 V rail heuristic
- **Two wires for control** — CANH/CANL replace three PWM/GPIO lines; the STM32 frees PA4 and PA5 (PA8/TIM1_CH1 is reused for the buzzer on the G0B1)
- **Shared physical layer** — the Unified PCB already has CAN; a second FDCAN controller and a $1 transceiver add the port
- **Torque headroom** — ≥ 3 N·m continuous for thick Indian gravies, with current limits set in the motor
- **Safe by default** — motor firmware stops on command timeout; the STM32 also removes 24 V with Q_STIR on E-stop and at boot

## 4. Materials

### 4.1 Food-Contact Components

| Component | Material | Properties | Compliance |
|-----------|----------|------------|------------|
| Drive Shaft | 304 Stainless Steel, 6mm diameter | Corrosion resistant, food-safe, autoclavable | FDA 21 CFR 175-178, EU 1935/2004 |
| Paddle Blade | Silicone (platinum cured) | Heat resistant to 250 C, non-stick, flexible | FDA grade, BPA-free |
| Paddle Blade (alt.) | Nylon 66 (food grade) | Heat resistant to 220 C, rigid, dishwasher-safe | FDA grade |
| Shaft Sleeve | PTFE (Teflon) | Low friction, chemical inert, seals shaft entry | FDA grade |
| Shaft Coupler | 6061 Aluminum (anodized) | Lightweight, corrosion resistant | Not food-contact (above seal line) |
| Motor Housing | ABS or 3D-printed PETG | Steam resistant, lightweight | Not food-contact (above seal line) |

## 5. Stirring Patterns

### 5.1 Pattern Definitions

| Pattern | Speed (RPM) | Motion Type | Duration | Use Case |
|---------|-------------|-------------|----------|----------|
| Continuous | 60 | Constant clockwise | Ongoing | General cooking, gravy mixing |
| Intermittent | 30 | 5s on / 10s off cycle | Periodic | Simmering, gentle heat distribution |
| Reverse | 45 | Alternating CW/CCW every 10s | Ongoing | Prevent sticking, unstick food from base |
| Scrape | 20 | Slow rotation with edge-seeking offset | 30s bursts | Deglazing, scraping fond from pot bottom |
| Fold | 15 | Gentle wide sweep, half rotation | 20s cycles | Delicate mixing, incorporating fragile ingredients |
| Vigorous | 90 | Fast constant clockwise | 10-30s bursts | Emulsifying, breaking up lumps |
| Off | 0 | Stationary (parked at home position) | - | Idle, ingredient loading, dispensing |

### 5.2 Pattern Timing Diagram

```
Continuous:  ┌──────────────────────────────────────────────────┐
             │  CW @ 60 RPM (constant)                         │
             └──────────────────────────────────────────────────┘

Intermittent:┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐
             │ ON  │     │ ON  │     │ ON  │     │ ON  │
             └─────┘     └─────┘     └─────┘     └─────┘
              5s    10s   5s    10s   5s    10s   5s

Reverse:     ┌────CW────┐┌───CCW────┐┌────CW────┐┌───CCW────┐
             │  @ 45 RPM ││ @ 45 RPM ││ @ 45 RPM ││ @ 45 RPM │
             └───────────┘└──────────┘└───────────┘└──────────┘
                 10s          10s         10s          10s
```

## 6. Speed Control

### 6.1 CAN Velocity Command

| Parameter | Value |
|-----------|-------|
| Bus | STM32 FDCAN2 (PB12 RX / PB13 TX) → SN65HVD230 → J_CAN_STIR, 1 Mbps |
| Command rate | 50 Hz (Motor Control task) |
| Velocity command | Signed target in rad/s (motor protocol units); sign = direction (positive = CW) |
| Speed range | 0–300 RPM at the shaft; current limit set in the motor to the stall threshold |
| Enable / disable | Motor enable frame on pattern start; disable frame on ARM_STOP, E-stop and heartbeat loss |
| Power | 24V_STIR switched on by PCF8574 #2 P5 before the enable frame; off when the arm is parked for > 60 s |
| Feedback | Velocity, position, current, temperature parsed every cycle; `motor_rpm` published in TELEMETRY (0x310) |

### 6.2 Speed Ramping

To prevent splashing and mechanical shock, speed changes are ramped:

```
Target Speed
     ▲
     │            ┌──────────── Steady state
     │           /
     │          / ◄── Acceleration limit: 30 RPM/s
     │         /
     │        /
     │───────/
     │  Ramp-up
     └──────────────────────────────────────────► Time
     0     0.5s    1.0s    1.5s    2.0s
```

- **Acceleration limit:** 30 RPM/s (prevents sudden splashing)
- **Deceleration limit:** 60 RPM/s (faster stop for safety)
- **Emergency stop:** Immediate halt (motor disable frame + Q_STIR off, no ramp; safety conditions only)

## 7. Home Position Sensor

### 7.1 Calibration Reference

- **Primary:** The motor's absolute single-turn encoder. The home angle is stored in the motor (zero-set) at assembly and re-read at boot; no homing move is needed
- **Backup:** Optional Hall effect sensor (SS49E or equivalent) with a magnet on the shaft, read by a spare STM32 GPIO, to re-zero the encoder after a paddle/shaft service
- **Parking:** Arm returns to the home angle (position-mode command) after cooking to allow pot removal and ingredient loading

## 8. STM32 Control Interface

### 8.1 Motor Bus (FDCAN2)

```c
/* FDCAN2 on PB12 (RX) / PB13 (TX), AF3 — regular (non-isolated) motor bus */
/* Classic CAN, 1 Mbps nominal bit timing from the 64 MHz FDCAN kernel clk */
/* Extended (29-bit) IDs as required by the motor protocol                 */
/* RX FIFO0 filter: motor feedback IDs only; TX: enable, velocity, position */
/* Motor Control task (50 Hz): send velocity target, parse feedback,        */
/* ramp-limit, detect stall from reported current                           */
/* Boot-safe: PCF8574 #2 P5 (24V_STIR) low until the first SET_STIR         */
```

The motor's own protocol (frame layout, units, parameter IDs) is wrapped in `stir_motor.c`; the rest of the firmware sees `stir_set_velocity()`, `stir_set_position()`, `stir_enable()` and a `stir_feedback_t` struct.

### 8.2 Command Protocol (RV1106 to STM32, CAN IDs 0x202 and 0x221–0x225)

| Command | Code | Parameters | Response | Description |
|---------|------|------------|----------|-------------|
| SET_STIR | 0x02 | pattern_id (1 byte), speed (2 bytes, RPM), direction (1 byte: 0=CW, 1=CCW) | ACK/NAK | Set stirring pattern, speed, and direction (was SET_PATTERN 0x20; 0x20 is now SET_LED) |
| SET_SPEED | 0x21 | speed (2 bytes, RPM), direction (1 byte: 0=CW, 1=CCW) | ACK/NAK | Direct speed and direction override |
| ARM_STOP | 0x22 | none | ACK | Immediately stop arm (with decel ramp) |
| ARM_HOME | 0x23 | none | ACK | Return to home position |
| ARM_STATUS | 0x24 | none | status_byte, current_rpm, position | Query arm status (distinct from STATUS 0x12) |
| SET_RAMP | 0x25 | accel_limit (2 bytes, RPM/s) | ACK/NAK | Configure acceleration limit |

Codes mirror [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]], the single source of truth for the CAN bus protocol: each code is the low byte of a 0x2xx CAN ID, frames carry a sequence byte first, and responses arrive in ACK/NAK 0x3FF.

### 8.3 FreeRTOS Task Configuration

| Task | Priority | Stack Size | Update Rate | Description |
|------|----------|------------|-------------|-------------|
| Motor Control | 3 (high) | 256 words | 50 Hz (20ms) | FDCAN2 velocity/position commands, feedback parsing, speed ramping, pattern execution |
| Home / Park | 2 (medium) | 128 words | On-demand | Position-mode move to the stored home angle (ARM_HOME, end of cook) |
| Stall Monitor | 3 (high) | 128 words | 50 Hz | Motor-reported current and temperature window; INA219 as plausibility check |

## 9. Safety

### 9.1 Torque and Stall Protection

| Safety Feature | Detection Method | Threshold | Action |
|----------------|------------------|-----------|--------|
| Stall Detection | Motor-reported phase current with velocity error (commanded vs. measured) | Current above the configured limit with < 20 % of commanded speed for 500 ms | Disable motor, retry up to 3 times, then error |
| Over-Torque | Motor current limit (set in the motor) + STM32 check of reported current | > configured peak (≈ 5 N·m equivalent) | Motor limits current itself; STM32 disables and logs |
| Thermal Protection | Motor-reported driver/winding temperature | > 80 °C | Reduce speed 50%, alert; disable at 95 °C |
| Power Isolation | Q_STIR high-side switch on 24V_STIR (PCF8574 #2 P5) | E-stop, heartbeat loss, boot | 24 V removed from the motor independently of CAN |
| Mechanical Guard | Physical shroud above pot rim | - | Prevents finger access to paddle zone |

### 9.2 Stall Recovery Sequence

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Stall   │    │ Stop     │    │ Wait     │    │ Retry    │
│ Detected│──► │ Motor    │──► │ 2s       │──► │ Reverse  │
│(current)│    │          │    │          │    │ 180 deg  │
└─────────┘    └──────────┘    └──────────┘    └─────┬────┘
                                                      │
                                              ┌───────▼───────┐
                                              │ Resume Pattern │
                                              │ (if clear)     │
                                              │                │
                                              │ OR             │
                                              │                │
                                              │ Error State    │
                                              │ (after 3       │
                                              │  retries)      │
                                              └────────────────┘
```

### 9.3 Lid Interlock (Future Enhancement)

- Magnetic reed switch on lid detects open/closed state
- Arm will not operate if lid is open (user safety)
- Opening lid during operation triggers arm stop and cook pause

## 10. Cleaning Design

### 10.1 Tool-Less Disassembly

| Component | Removal Method | Dishwasher Safe | Notes |
|-----------|----------------|-----------------|-------|
| Paddle Blade | Twist-lock (quarter turn) | Yes | Silicone or nylon, hand-wash or dishwasher |
| Shaft Sleeve | Pull-off after paddle removed | Yes | PTFE sleeve slides off shaft |
| Cooking Pot | Lift out | Yes | Standard removable pot |
| Motor Housing | Wipe-down only | No | Above splash zone, sealed |
| Drive Shaft | Not user-removable | N/A | Cleaned in-place with damp cloth |

### 10.2 Cleaning Sequence

1. Remove pot from unit
2. Twist-lock paddle counterclockwise (quarter turn) and pull down to release
3. Slide shaft sleeve off the drive shaft
4. Place paddle and sleeve in dishwasher or hand-wash with warm soapy water
5. Wipe exposed shaft with damp cloth
6. Reassemble in reverse order (sleeve on shaft, paddle twist-lock clockwise)

## 11. Testing and Validation

### 11.1 Test Procedures

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Torque Under Load | Stir 2L thick curry (butter chicken consistency) | Continuous operation at 60 RPM without stall |
| Continuous Operation | Run at 45 RPM for 4 hours with medium-viscosity load | No overheating, no stall, no bearing failure |
| Stall Recovery | Manually block paddle, verify detection and retry | Stall detected within 500ms, 3 retries, error state |
| Splash Containment | Run at 90 RPM with 1.5L water, measure splatter | No liquid escapes pot rim (with guard installed) |
| Cleaning Cycle | Disassemble, wash, reassemble 100 times | No wear on twist-lock, secure fit maintained |
| Noise Level | Measure at 30cm during operation at 60 RPM | <50 dB(A) |
| Speed Accuracy | Motor-reported velocity vs. external tachometer at each speed setting | Within +/- 5 RPM of commanded speed |
| CAN Link | 1 Mbps bus, 50 Hz commands for 4 hours | No bus-off, no missed feedback frame > 100 ms |
| Ramp Profile | Record speed vs. time during acceleration | Within +/- 10% of configured ramp rate |
| Home Position | 50 consecutive home-seek operations | Repeatable within +/- 2 degrees |

### 11.2 Prototype Validation Checklist

- [ ] CAN servo motor drives paddle through 360-degree rotation smoothly; feedback RPM matches commanded within ±5 RPM
- [ ] Motor stops within 500 ms when CAN commands cease (command timeout) and when Q_STIR removes 24 V
- [ ] Twist-lock paddle attachment holds securely during vigorous stirring
- [ ] Stall detection triggers within 500ms of blockage
- [ ] Speed ramping prevents visible splashing at all pattern transitions
- [ ] Steam seal prevents moisture ingress to motor housing over 2-hour cook
- [ ] Home angle from the encoder is repeatable within ±2 degrees across power cycles
- [ ] All food-contact surfaces pass dishwasher cycle without degradation
- [ ] Noise level below 50 dB(A) at maximum operational speed

## 12. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture]]
- [[01-Induction-Heating|Induction Heating System]]
- [[03-Ingredient-Dispensing|Ingredient Dispensing System]]
- [[04-Vision-System|Vision System]]
- [[01-Safety-Compliance|Safety & Compliance]]

#epicura #robotic-arm #subsystem #bldc-motor #canbus

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-20 | Manas Pradhan | Replaced DS3225 servo with 24V BLDC motor (integrated ESC); updated motor selection, PWM config (10 kHz), control interface (PWM+EN+DIR), command protocol (added direction param), stall detection (INA219-based), and testing procedures |
| 2.1 | 2026-11-04 | Manas Pradhan | Application processor renamed from Raspberry Pi CM5 to RV1106 (Luckfox Pico Zero); motor control and command protocol unchanged |
| 2.2 | 2026-11-04 | Manas Pradhan | Bridge codes aligned to the software doc: SET_PATTERN 0x20 → SET_STIR 0x02; STOP/HOME/STATUS renamed ARM_STOP/ARM_HOME/ARM_STATUS |
| 2.3 | 2026-11-04 | Manas Pradhan | Command protocol mapped onto the shared CAN bus (IDs 0x202, 0x221–0x225) |
| 3.0 | 2026-11-04 | Manas Pradhan | Stirring motor changed to a 24 V integrated CAN servo on the Unified PCB's regular (non-isolated) CAN port (STM32 FDCAN2, PB12/PB13, SN65HVD230, 1 Mbps, J_CAN_STIR) with switched 24 V (J_STIR_PWR, Q_STIR); PWM/EN/DIR on PA8/PA4/PA5 retired; encoder feedback replaces FG tachometer and Hall homing (Hall kept as optional backup); stall/over-torque from motor-reported current; motor specs, control interface, tasks, safety and tests updated |
