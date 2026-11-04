---
created: 2026-02-15
modified: 2026-11-04
version: 7.4
status: Draft
---

# Ingredient Dispensing System

## 1. Overview

The ingredient dispensing system is divided into three purpose-built subsystems, each optimized for a different ingredient class. All three live in the lift-off **Dispensing Unit (DU)** that sits on top of the Cooking Surface and surrounds the cooking pot from above. They are driven by the RV1106 itself — the `dispense` thread of `epicurad` — over I2C3 and PWM on the Unified PCB v4.0 inside the DU, under commands queued in-process by the recipe engine. No STM32 and no CAN traffic are involved in dispensing.

The FID and CID share one mechanical concept (a servo-indexed carousel) and one electrical control block (the **Dispenser Servo Block, DSB**): four hobby-class servos sized per axis (DS3218, 2× MG996R, MG90S) driven from a single PCA9685 PWM driver on I2C3, powered from one switched 6.0 V dispenser rail (6V_DSP). The SLD keeps its own pump/valve/load-cell hardware on the same board and rail.

| Subsystem | Full Name | Purpose | Actuators | Metering |
|-----------|-----------|---------|-----------|----------|
| **FID** | Fine Ingredients Dispenser | Powdered spices, salt, sugar, dry seasonings (6 canisters) | 3 servos on the DSB: F1 carousel index, F2 dose, F3 steam gate | Volumetric, ¼ tsp per dose stroke (open loop, ±10%) |
| **CID** | Coarse Ingredients Dispenser | Pre-cut vegetables, meat, paneer, dal, rice (5 slots) | 1 servo on the DSB: C1 carousel index | Whole slot per dispense (user pre-measured) |
| **SLD** | Standard Liquid Dispenser | Oil and water | 2 Peristaltic Pumps + 2 Solenoid Valves + 2 Load Cells (one per reservoir) | Closed-loop weight feedback + low-level alerts |

Box and slot numbering matches the recipe contract already used by the cloud schema and recipe schema: FID **Box1–Box6** dosed in multiples of ¼ tsp, CID **Slot1–Slot5** dispensed whole (see [[02-Database-Schema|Database Schema]] §3.6).

## 2. Layout

### 2.1 Top-View Arrangement

```
┌───────────────────────────────────────────────────────┐
│                    REAR OF UNIT                        │
│                                                        │
│            FID carousel (6 canisters, Ø170 mm)         │
│                  ┌───────────────┐                     │
│               ┌──┤ Box 4 │ Box 3 ├──┐                  │
│               │ Box 5 ──┼── Box 2  │   F1 index servo  │
│               └──┤ Box 6 │ Box 1 ├──┘   (5:3 gear-up)  │
│                  └───────┬───────┘                     │
│                 dosing station (F2 dose, F3 gate)      │
│                          ▼ chute                       │
│  ┌─────┐ ┌──────────────────────────────────┐ ┌─────┐ │
│  │ SLD │ │                                  │ │ SLD │ │
│  │Oil  │ │          COOKING POT             │ │Water│ │
│  │Pump │►│          (Center)                │◄│Pump │ │
│  │     │ │                                  │ │     │ │
│  └─────┘ └──────────────────────────────────┘ └─────┘ │
│                          ▲ chute                       │
│                  drop aperture (fixed base plate)      │
│                  ┌───────┴───────┐                     │
│               ┌──┤Slot 3 │Slot 2 ├──┐                  │
│               │Slot 4 ──┼── Slot 1 │   C1 index servo  │
│               └──┤Slot 5 │ COVER ├──┘   (4:3 gear-up)  │
│                  └───────────────┘                     │
│            CID carousel (5 slots + cover, Ø230 mm)     │
│                    FRONT OF UNIT                        │
└───────────────────────────────────────────────────────┘
```

Both carousels sit above pot-rim height; the station/aperture edge of each ring overhangs the pot rim so that material free-falls through a short 45° chute into the pot.

The diagram is the top view of the Dispensing Unit: the FID carousel is at the rear of the DU, the CID carousel at the front, the SLD reservoirs on the two sides. The DU underside carries the two chutes, the two SLD nozzles and the camera window (see [[04-Vision-System|Vision System]]); the reservoirs, canisters and carousel rings lift off with the unit, so the whole dispensing side of the machine can be carried to the counter for loading and cleaning.

### 2.2 Side-View Cross Sections

**FID (servo carousel + per-canister ¼ tsp measure):**

```
              ┌──── Threaded cap + silicone O-ring seal
              │     ┌── Desiccant pocket (1g silica gel)
              ▼     ▼
       ┌───────────────────┐
       │  ╔═══════════════╗│
       │  ║   SPICE       ║│  45 mm dia × 60 mm tall
       │  ║   POWDER      ║│  60 mL capacity
       │  ║               ║│  Food-grade PP, translucent
       │  ╚═══╲       ╱═══╝│  60° internal cone
       │       ╲     ╱     │
       │     ┌──▼───▼──┐   │
       │     │ MEASURE │   │ ◄── Rotary measure wheel, one 1.23 mL (¼ tsp)
       │     │  WHEEL  │   │     pocket; seals outlet in every position
       │     └────┬────┘   │
       └──────────┼────────┘
         blade ───┤◄────── F2 DOSE servo coupling (engages only at station)
         coupling │
           ┌──────▼──────┐
           │ Steam gate  │ ◄── F3 GATE servo flap, spring-closed, opens 70°
           │ flap        │     only while dosing
           └──────┬──────┘
                  │
           ┌──────▼──────┐
           │ Chute       │ ◄── Removable, 45° into pot
           └──────┬──────┘
                  ▼
       ┌────────────────────┐
       │    COOKING POT     │
       └────────────────────┘
```

**CID (servo carousel over fixed base plate):**

```
   C1 servo ──► 4:3 gear-up (F1: 5:3) ──► ring gear on carousel hub
                                        │
       ┌────────────────────────────────▼───────────────────┐
       │   Slot 1   │   Slot 2   │  ...  │   COVER sector   │  lift-off ring,
       │  (open-    │  (open-    │       │  (solid floor,   │  5 bins × 200 mL,
       │   bottom)  │   bottom)  │       │   home position) │  45 mm tall
       ├────────────┴────────────┴───────┴──────────────────┤
       │            FIXED BASE PLATE (thin-section bearing) │
       │                      ┌─────────────┐               │
       │                      │  APERTURE   │ ◄── one 50° sector opening at the
       │                      │  (station)  │     rear edge, over the pot rim
       └──────────────────────┴──────┬──────┴───────────────┘
                                     ▼
                              ┌─────────────┐
                              │   Chute     │ ◄── 45° into pot
                              └──────┬──────┘
                                     ▼
                          ┌────────────────────┐
                          │    COOKING POT     │
                          └────────────────────┘
```

Rotating a bin over the aperture drops its contents; the COVER sector closes the aperture at the home position (loading, idle, steam shielding).

**SLD (Peristaltic Pump + Solenoid):**

```
    ┌──────────────┐
    │  Reservoir   │
    │  (Oil/Water) │
    │  500 mL      │
    └──────┬───────┘
           │ Silicone tube (6mm ID)
           ▼
    ┌──────────────┐
    │  Peristaltic │ ◄── 6 V DC gear motor, PWM speed control
    │  Pump        │     Flow rate: 5-50 mL/min
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Solenoid    │ ◄── 6 V NC solenoid, prevents drip when idle
    │  Valve       │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Nozzle      │ ──► Through the DU underside into the cooking pot
    └──────────────┘

    ┌──────────────┐  ┌──────────────┐
    │  Load Cell   │  │  Load Cell   │ ◄── 2× NAU7802 (one per reservoir, via TCA9543A mux)
    │  (under oil  │  │  (under water│     Closed-loop: pump until target Δweight
    │   reservoir) │  │   reservoir) │     Low-level alert when < threshold
    └──────────────┘  └──────────────┘
```

## 3. Common Carousel Design (FID and CID)

### 3.1 Servos

The four DSB servos are sized per axis. All are standard 50 Hz PWM hobby servos (500–2500 µs) on the same PCA9685 and the same switched 6.0 V dispenser rail (6V_DSP), so one driver serves them; the dispense thread keeps a per-channel angle table (travel and gear ratio differ). All four are rated for 6.0 V, so no per-connector series diode is needed.

| Axis | Servo | Travel | Stall torque | Speed (no load) | Supply | Stall current | Why |
|------|-------|--------|--------------|-----------------|--------|---------------|-----|
| C1 CID index | DS3218 (DSSERVO), metal gear, 270° variant | 270° | 18 kg·cm at 5 V, 21.5 kg·cm at 6.8 V (≈ 20 kg·cm at 6.0 V) | 0.16 s / 60° | 6V_DSP direct (rated 4.8–6.8 V) | 2.2 A at 6.8 V | Drags up to 1 kg of bin contents across the fixed base plate (≈ 3–5 kg·cm at the ring plus breakaway); needs 300° carousel travel |
| F1 FID index | MG996R-class, metal gear | 180° | ≈ 11 kg·cm at 6 V | 0.17 s / 60° | 6V_DSP direct (rated 4.8–7.2 V) | ≈ 2.5 A | Canisters ride on a bearing (< 1 kg·cm); 180° reaches 300° carousel through a 5:3 gear-up |
| F2 FID dose | MG996R-class, metal gear | 180° | ≈ 11 kg·cm at 6 V | 0.17 s / 60° | 6V_DSP direct | ≈ 2.5 A | Turns the measure wheel in compacted powder and shears arches on the jiggle; full 180° swing used |
| F3 FID steam gate | MG90S-class, metal gear micro | 180° | ≈ 2.2 kg·cm at 6 V | 0.10 s / 60° | 6V_DSP direct (rated 4.8–6.0 V; D_DSB4 removed) | ≈ 0.7 A | Spring-assisted flap, 70° swing, negligible load |

Common to all four: no external position feedback (internal potentiometer, absolute), open loop at the RV1106; moving current 0.5–1.5 A, idle a few mA. Datasheet for C1: [[../../research/dsservo-DS3218-datasheet.pdf|DSSERVO DS3218]]. Cost ≈ $10 (DS3218) + 2 × $4 (MG996R) + $2.50 (MG90S) ≈ $20.50 per unit.

### 3.2 Index Drive (C1, F1)

| Parameter | C1 (CID, DS3218 270°) | F1 (FID, MG996R 180°) |
|-----------|------------------------|------------------------|
| Coupling | 4:3 spur gear-up (servo 32T → ring gear 24T), POM or printed | 5:3 spur gear-up (servo 40T → ring gear 24T), POM or printed |
| Travel | Servo 0–225° → carousel 0–300° (six 60° positions) | Servo 0–180° → carousel 0–300° (six 60° positions) |
| Carousel torque | ≈ 13 kg·cm at 6.0 V (ring on a thin-section ball bearing; load is the bin contents sliding on the base plate, ≈ 3–5 kg·cm) | ≈ 6 kg·cm at 6.0 V (canisters ride with the ring on a bearing; load < 1 kg·cm) |
| Resolution | 4.9 µs PWM step ≈ 0.66° servo ≈ 0.9° carousel | 4.9 µs PWM step ≈ 0.44° servo ≈ 0.7° carousel |
| Homing | None required: gear mesh is assembled at marked teeth, servo position is absolute | Same |
| Position table (servo angles) | pos 0 = 0°, 1 = 45°, 2 = 90°, 3 = 135°, 4 = 180°, 5 = 225° | pos 0 = 0°, 1 = 36°, 2 = 72°, 3 = 108°, 4 = 144°, 5 = 180° |

Moves are ramp-limited in the dispense thread (≤ 3° servo per 20 ms tick, ≈ 1.5 s for a 60° carousel step) so that loaded bins do not slosh and the rail current stays under 2 A.

### 3.3 Rules shared by both carousels

- Only one DSB servo moves at a time (dispense-thread mutex); the 6V_DSP rail is switched on for the duration of a dispense and off when idle (no holding buzz, no idle heat).
- PCA9685 OE is driven high (all outputs off, servos limp) in the boot-safe state and on E-stop; the rail is also switched off. A 10 k pull-up on OE keeps the servos limp from power-up until `epicurad` claims the GPIO.
- Rings are lift-off, dishwasher-safe parts keyed to the hub so that slot/box 1 always indexes to the same angle.

## 4. FID — Fine Ingredients Dispenser

### 4.1 Canister Specifications

| Parameter | Value |
|-----------|-------|
| Canisters | 6 (Box1 through Box6) |
| Capacity | 60 mL each |
| Dimensions | 45 mm diameter × 60 mm tall (cylindrical, 60° internal cone) |
| Material | Food-grade polypropylene (PP), translucent |
| Removable | Yes (lift out of carousel bay; keyed so the measure wheel faces the station) |
| Lid | Threaded screw-cap with silicone O-ring seal, desiccant pocket |
| Measure | Integral rotary measure wheel in the base, one 1.23 mL (¼ tsp) pocket; outlet is sealed in every wheel position |
| Coupling | Tangential blade on the wheel axle; the station's F2 coupling parks at 0° so a canister can slide in and out of the station without tools |
| Weight (empty) | ~30 g |

### 4.2 Default Canister Assignment

| Box | Default Spice | Bulk Density (g/mL) | Mass per ¼ tsp dose (g) |
|-----|---------------|---------------------|-------------------------|
| Box1 | Turmeric powder | 0.55 | 0.68 |
| Box2 | Chili powder | 0.45 | 0.55 |
| Box3 | Cumin powder | 0.40 | 0.49 |
| Box4 | Salt (fine) | 1.20 | 1.48 |
| Box5 | Garam masala | 0.50 | 0.62 |
| Box6 | Coriander powder | 0.35 | 0.43 |

Mass per dose = 1.23 mL × bulk density. The recipe engine stores quantities in ¼ tsp; grams are derived for logging and the UI only.

### 4.3 Dosing Station

| Element | Servo | Motion | Purpose |
|---------|-------|--------|---------|
| Carousel index | F1 | 0–180° (6 positions via 5:3 gear-up) | Brings the selected canister over the station |
| Dose | F2 | 0° ↔ 180° swing per dose | Rotates the canister's measure wheel: pocket fills under the outlet at 0°, discharges into the chute at 180° |
| Steam gate | F3 | 0° (closed) ↔ 70° (open) | Spring-assisted flap at the chute mouth; open only while dosing so pot steam does not reach the powder path |

Anti-bridging is done in software with no extra hardware: before each dose F2 jiggles the measure wheel ±15° three times (shears any arch at the outlet) and F1 wiggles the carousel ±2° twice.

### 4.4 Dose Sequence

1. The recipe engine queues `DISPENSE_FID(box_id, qty_quarter_tsp)` to the dispense thread
2. The dispense thread switches the 6V_DSP rail on, indexes F1 to `box_id` (ramped)
3. F3 opens the steam gate (70°)
4. For each dose: F2 jiggle (±15° × 3), F2 to 180° (discharge), F2 back to 0° (refill) — ≈ 0.8 s per dose
5. F3 closes the gate, rail off
6. ACK with `doses_done` and the estimated mass (dose count × calibrated mass per dose)

A stall or I2C NACK during any move aborts the sequence (rail off, OE high) and raises `DSB_STALL` to the recipe engine (an RV1106-local fault, see §8).

### 4.5 Metering Strategy

FID uses **volumetric dosing in ¼ tsp increments**: accuracy ±10% of the volume per dose; mass accuracy depends on how well the stored bulk density matches the loaded spice (typically ±15%). Maximum 40 doses (10 tsp) per command.

## 5. CID — Coarse Ingredients Dispenser

### 5.1 Carousel Specifications

| Parameter | Value |
|-----------|-------|
| Slots | 5 (Slot1 through Slot5) + 1 solid COVER sector |
| Capacity | ~200 mL per slot (~1 L total; 60° sector, Ø230 mm ring, Ø80 mm hub, 45 mm tall) |
| Material | Food-grade PP (single lift-off ring, dishwasher-safe) |
| Base plate | Fixed, with one 50° aperture at the rear station over the pot rim; removable for washing together with the chute |
| Ingredient Types | Pre-cut vegetables, meat, paneer, dal, rice |

### 5.2 Dispense Sequence

1. The recipe engine queues `DISPENSE_CID(slot_id)` to the dispense thread
2. The dispense thread rejects (NACK) if `slot_id` is not greater than the current carousel position
3. Rail on; C1 indexes the carousel (ramped) so `slot_id` sits over the aperture — contents free-fall through the chute
4. Dwell 2 s, then wiggle ±5° three times to clear residue
5. Rail off; ACK with the new position

At the end of a recipe (or on `DISPENSER_HOME`) the carousel returns to position 0, placing the COVER sector over the aperture for loading and steam shielding.

### 5.3 Dispense-Order Constraint

Every bin that passes over the aperture empties. Slots are therefore dispensed in **ascending order** (1 → 5) and a recipe may skip a slot only if it was left empty. The ingredient-loading screen enforces this by assigning ingredients to slots in order of use, and the recipe engine validates segment order before `COOKING` starts.

### 5.4 Metering Strategy

CID dispenses a **whole slot** per command; quantities are pre-measured by the user when loading (as before, no closed-loop weight verification).

## 6. SLD — Standard Liquid Dispenser

### 6.1 Channel Specifications

| Parameter | Oil Channel (SLD-OIL) | Water Channel (SLD-WATER) |
|-----------|----------------------|--------------------------|
| Reservoir | 200 mL food-grade PP bottle | 500 mL food-grade PP bottle |
| Tube | 6 mm ID food-grade silicone | 6 mm ID food-grade silicone |
| Pump | 6 V DC peristaltic, 5–50 mL/min | 6 V DC peristaltic, 5–50 mL/min |
| Valve | 6 V NC solenoid (drip prevention) | 6 V NC solenoid (drip prevention) |
| Nozzle | Through the DU underside, directed into pot center | Through the DU underside, directed into pot center |

### 6.2 Actuators

**Peristaltic Pump (×2):**

| Parameter | Value |
|-----------|-------|
| Type | Peristaltic roller pump, 6 V DC gear motor (re-specified from 12 V; runs from the 6V_DSP rail via TB6612FNG, PWM from the RV1106) |
| Tube | Food-grade silicone, 6 mm ID |
| Flow Rate | 5–50 mL/min (adjustable via PWM motor speed) |
| Accuracy | ±2% volumetric (further refined by load cell) |
| Advantage | Self-priming, no contamination (fluid only touches tube), reversible |
| Cost | ~$10 each |

**Solenoid Valve (×2):**

| Parameter | Value |
|-----------|-------|
| Type | 6 V DC, normally closed, spring return (re-specified from 12 V; fed from the 6V_DSP rail) |
| Response | <50 ms open/close |
| Purpose | Prevent dripping when pump is off |
| Power | ~5W when energized |
| Driver | N-channel MOSFET (IRLML6344) with flyback diode, switched by PCF8574 #2 P0 (oil) / P1 (water) |
| Cost | ~$4 each |

### 6.3 Dedicated Load Cells (2×)

| Parameter | Value |
|-----------|-------|
| Type | 2× 2 kg strain gauge (one under each SLD reservoir: oil and water) |
| ADC | 2× NAU7802 24-bit I2C ADC (addr 0x2A each), one on each channel of a TCA9543A I2C mux (0x71) on I2C3; Linux `nau7802` IIO + `i2c-mux-pca954x` drivers (replaces the HX711 bit-bang pair) |
| Purpose | Individual liquid level monitoring + closed-loop dispensing by tracking reservoir weight decrease |
| Capacity | 2 kg per load cell (accommodates full reservoir + container weight) |
| Accuracy | ±1 g (24-bit NAU7802 with averaging) |
| Sampling | 10 Hz |
| Low-Level Alert | Configurable threshold per channel (default: 50 g remaining); alert raised by the dispense thread to the UI when level drops below threshold |
| Cost | ~$5 (load cell) × 2 + ~$2 (NAU7802) × 2 + ~$1 (TCA9543A) = ~$15 total |

### 6.4 Metering Strategy (Closed-Loop)

SLD uses **two dedicated load cells** (one under each reservoir) for independent closed-loop dispensing and level monitoring:

```
┌───────────────┐
│ 1. Tare       │
│ reservoir     │──► W_initial = sld_load_cell[channel].read()
│ weight        │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 2. Open       │
│ solenoid +    │──► solenoid[channel].open()
│ start pump    │    pump[channel].start(speed)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 3. Monitor    │
│ reservoir     │──► W_dispensed = W_initial - sld_load_cell[channel].read()
│ weight loss   │    (sampled at 10 Hz)
│ in real-time  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 4. Stop pump  │
│ + close       │──► IF W_dispensed >= target_g * 0.95:
│ solenoid when │        pump[channel].stop()
│ target reached│        solenoid[channel].close()
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ 5. Verify     │
│ final weight  │──► W_actual = W_initial - sld_load_cell[channel].read()
│ and log       │    log(channel, target_g, W_actual)
│               │    IF sld_load_cell[channel].read() < LOW_LEVEL_THRESHOLD:
│               │        raise SLD_LOW_LEVEL alert (dispense thread → UI)
└───────────────┘
```

Accuracy: ±5% of target weight (dedicated load cell and controllable flow rate).

## 7. RV1106 Control Interface

### 7.1 Dispenser Servo Block (DSB)

The FID and CID are one electrical block on the Unified PCB v4.0 inside the Dispensing Unit:

```
  VSYS ──► MP1584EN #2 (6.0 V, 3 A) ──► Q_DSB P-MOSFET high-side switch ──► 6V_DSP dispenser rail
                                               ▲                            │  1000 µF bulk + 3 A PTC
                                   PCF8574 #2 P4 (rail enable)              │  INA219 #1 (0x40) shunt
                                                                            ▼
  I2C3 (header 16/18) ──► PCA9685 (addr 0x41) ──┬── CH0 ──► J_DSB1 ──► C1  CID index servo   (DS3218 270°)
                                                ├── CH1 ──► J_DSB2 ──► F1  FID index servo   (MG996R)
  RV1106 GPIO ──► PCA9685 OE (active-low,       ├── CH2 ──► J_DSB3 ──► F2  FID dose servo    (MG996R)
                  10 k pull-up)                 └── CH3 ──► J_DSB4 ──► F3  FID steam-gate servo (MG90S, 6V_DSP direct)
                                                     CH4–CH15 spare
```

VSYS is the Schottky-OR of DOCK_24V (while docked) and the DU's 2S battery (lifted or mains lost), so the dispenser rail is available in both cases; at an empty pack (6.2 V) the buck drops out to ≈ 6.0 V, which is acceptable.

| Element | Part | Notes |
|---------|------|-------|
| PWM driver | PCA9685PW (TSSOP-28), I2C3 addr 0x41 | 16 channels, 12-bit, 50 Hz; CH0–CH3 used; Linux `pwm-pca9685` driver |
| Output enable | RV1106 GPIO (fixed at layout) → OE (active-low), 10 k pull-up | High in boot-safe state and on E-stop; pull-up keeps servos off until `epicurad` starts |
| Rail | MP1584EN #2 set to 6.0 V from VSYS | Switched by PCF8574 #2 P4 via Q_DSB (AO3401-class P-MOSFET); 3 A PTC; 1000 µF bulk; also feeds the SLD pumps (TB6612 VM) and solenoids |
| Connectors | J_DSB1–4, 3-pin JR (signal / V+ / GND), 2.54 mm, keyed | Standard servo leads, 300 mm extensions; all four V+ = 6V_DSP (D_DSB4 removed, all servos rated for 6.0 V) |
| Fault detection | INA219 #1 (0x40) current window on the 6V_DSP rail during moves + move timeout + PCA9685 I2C NACK | Raises `DSB_STALL` in the dispense thread (RV1106-local) |

### 7.2 GPIO, PWM and I2C Assignments

| Subsystem | Actuator | RV1106 Pin / Device | Interface | Notes |
|-----------|----------|---------------------|-----------|-------|
| **FID/CID** | Servos C1, F1, F2, F3 | PCA9685 CH0–CH3 (I2C3, addr 0x41) | 50 Hz PWM, 500–2500 µs | DS3218 / MG996R / MG996R / MG90S; per-channel angle table |
| **FID/CID** | PCA9685 OE | RV1106 GPIO (fixed at layout) | Digital output, active-low, 10 k pull-up | High = all servo outputs off |
| **FID/CID** | 6V_DSP rail enable | PCF8574 #2 P4 (I2C3, addr 0x21) | Digital output via Q_DSB P-MOSFET | On only during a dispense |
| **SLD** | Pump Motor SLD-OIL (PWM) | RV1106 PWM (fixed at layout) | PWM (motor speed) | TB6612 PWMA |
| **SLD** | Pump Motor SLD-OIL (DIR) | PCF8574 #2 P3 (I2C3, addr 0x21) | Digital output | TB6612 AIN1 direction |
| **SLD** | Pump Motor SLD-WATER (PWM) | RV1106 PWM (fixed at layout) | PWM (motor speed) | TB6612 PWMB |
| **SLD** | Pump Motor SLD-WATER (DIR) | PCF8574 #2 P5 (I2C3, addr 0x21) | Digital output | TB6612 BIN1 direction |
| **SLD** | Solenoid SLD-OIL | PCF8574 #2 P0 (I2C3, addr 0x21) | Digital output via IRLML6344 | 6 V NC solenoid, flyback diode |
| **SLD** | Solenoid SLD-WATER | PCF8574 #2 P1 (I2C3, addr 0x21) | Digital output via IRLML6344 | 6 V NC solenoid, flyback diode |
| **SLD** | Load cell SLD-OIL | NAU7802 #1 (addr 0x2A) on TCA9543A (0x71) channel 0 | I2C3, 24-bit, 10 Hz | SLD oil reservoir load cell (2 kg) |
| **SLD** | Load cell SLD-WATER | NAU7802 #2 (addr 0x2A) on TCA9543A (0x71) channel 1 | I2C3, 24-bit, 10 Hz | SLD water reservoir load cell (2 kg) |
| **DSB** | Rail current sense | INA219 #1 (I2C3, addr 0x40) | I2C3, `ina2xx` hwmon | Shunt in the 6V_DSP rail; stall window and self-test |

> **Note:** Pin assignments match [[01-Unified-PCB-Design|Unified PCB Design]] (v4.0). I2C3 (Luckfox header pins 16/18, 400 kHz, 4.7 k pull-ups) is the single I2C bus of the DU: FT6336 touch (0x38, via J_LCD), PCF8574 #2 (0x21), NAU7802 ×2 (0x2A, behind the TCA9543A mux at 0x71), INA219 #1 (0x40), INA219 #2 (0x44, battery), PCA9685 (0x41). PCF8574 #2 map: P0 oil solenoid, P1 water solenoid, P2 status LED, P3 TB6612 AIN1, P4 6V_DSP rail enable, P5 TB6612 BIN1, P6 TP5100 CHRG (in), P7 TP5100 STDBY (in). The HX711 pair, the 74AHCT1G125 and D_DSB4 are gone from the board, and the former STM32 pins (PB4, PC3–PC6, PC9–PC12) no longer apply: the STM32 now sits on the Cooking Surface Controller in the base and has no dispensing role.

### 7.3 Dispensing Command Queue (recipe engine → dispense thread)

Commands are an in-process queue inside `epicurad`: the recipe engine enqueues a command, the `dispense` thread (SCHED_OTHER, 50 Hz while active) executes it and answers with the same ACK/NAK semantics the former CAN protocol used. Names, parameters and responses are unchanged; only the transport is gone. CAN IDs 0x230–0x239 are **retired** from the bus map (see [[02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]).

| Command | Parameters | Response | Description |
|---------|------------|----------|-------------|
| DISPENSE_FID | box_id (1–6), qty_quarter_tsp (1–40) | ACK + doses_done + est_mass_dg (0.1 g) | Index canister, open gate, N dose strokes, close gate |
| DISPENSE_CID | slot_id (1–5) | ACK + cid_pos; NACK if slot_id ≤ current position | Rotate slot over the aperture, dwell, wiggle |
| DISPENSE_SLD | channel (OIL=1, WATER=2), target_weight_g | ACK + actual_weight_g | Pump liquid, closed-loop via dedicated load cell |
| QUERY_WEIGHT | source (SLD_OIL=1, SLD_WATER=2) | weight_g | Read weight from individual SLD load cell |
| PREFLIGHT | subsystem_mask | status per subsystem | Check if required subsystems are loaded/ready |
| TARE | source (SLD_OIL=1, SLD_WATER=2) | ACK | Zero the specified SLD load cell readings |
| DISPENSER_HOME | target (CID=1, FID=2, 0xFF=both) | ACK | CID → COVER over aperture (pos 0); FID → gate closed, measure at fill, carousel to Box1 |
| DISPENSER_STATUS | — | cid_pos, fid_box, gate_open, rail_on, busy | Carousel positions for the loading screen |

## 8. Fault Handling (DSB)

Faults are detected by the dispense thread on the RV1106 and are local to it: `DSB_STALL`, `SLD_LOW_LEVEL`, `SLD_DISPENSE_ERROR` and `SLD_LOAD_CELL_DRIFT` no longer appear in STM32 STATUS/TELEMETRY frames. A load-cell fault is a NAU7802 I2C NACK or missing data-ready.

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Rail on,     │────►│ Ramped move   │────►│ Move done    │
│ OE low       │     │ (≤3°/tick)    │     │ within       │
└──────────────┘     └───────────────┘     │ timeout?     │
                                           └──────┬───────┘
                                                   │
                                          Yes ◄────┴────► No (INA219 #1 > 2.5 A for 300 ms,
                                           │                  I2C NACK, or > 3 s)
                                           ▼              ▼
                                    ┌──────────┐   ┌──────────────┐
                                    │ Continue │   │ Retry once:  │
                                    │ sequence │   │ back off 10°,│
                                    └──────────┘   │ re-approach  │
                                                   └──────┬───────┘
                                                          │
                                                 Yes ◄────┴────► No
                                                  │              │
                                                  ▼              ▼
                                           ┌──────────┐   ┌──────────────┐
                                           │ Continue │   │ DSB_STALL:   │
                                           │ sequence │   │ rail off,    │
                                           └──────────┘   │ OE high,     │
                                                          │ alert user   │
                                                          └──────────────┘
```

Because the servos are open loop, a jammed carousel is detected by current (INA219 #1 on the 6V_DSP rail) and time, not position. The user is prompted to clear the jam and tap Resume; the sequence then restarts from `DISPENSER_HOME`.

## 9. Metering Accuracy Summary

| Factor | FID Impact | CID Impact | SLD Impact | Mitigation |
|--------|-----------|-----------|-----------|------------|
| In-flight material | Powder in chute after last dose | Pieces still falling during wiggle | Fluid in tube after pump stops | FID: gate closes 300 ms after last dose. CID: 2 s dwell. SLD: close at 95% target |
| Pocket fill variance | ±10% per dose (packing) | N/A | ±1 g (dedicated cell) | FID: jiggle before each dose levels the pocket |
| Bulk density drift | Mass per dose off by stored density error | N/A | N/A | Per-spice density table, user-editable |
| Sticky ingredients | Arches at canister outlet | Pieces stick to bin floor/base plate | Oil residue in tube | FID: jiggle + 60° cone. CID: wiggle, smooth PP. SLD: tube replacement |
| Steam ingress | Caking at outlet | Minor | N/A | FID: steam gate closed except while dosing. CID: COVER sector at home |

## 10. Recipe Integration

### 10.1 Dispensing Sequence Example (Dal Tadka)

```
Step 1:  DISPENSE_SLD(OIL, 30g)                ──► Oil into hot pot
Step 2:  Wait for sear temp (200°C)             ──► Module surface_temp (HEAT_STATUS) confirms
Step 3:  DISPENSE_FID(Box1, 4)                 ──► Turmeric, 1 tsp (~2.7 g)
Step 4:  DISPENSE_FID(Box2, 8)                 ──► Chili powder, 2 tsp (~4.4 g)
Step 5:  Stir briefly                           ──► Arm mixes spices into oil
Step 6:  DISPENSE_CID(Slot1)                   ──► Chopped onions, tomatoes
Step 7:  Wait for browning (CV detection)       ──► Camera detects golden color
Step 8:  DISPENSE_FID(Box4, 3)                 ──► Salt, ¾ tsp (~4.4 g)
Step 8b: DISPENSE_FID(Box5, 5)                 ──► Garam masala, 1¼ tsp (~3.1 g)
Step 9:  DISPENSE_CID(Slot2)                   ──► Toor dal (200g, pre-measured)
Step 10: DISPENSE_SLD(WATER, 400g)              ──► Water
Step 11: Simmer until done (CV + timer)         ──► Camera detects thickening
```

### 10.2 Ingredient Loading Configuration

Users configure subsystem contents when loading ingredients before cooking:

| Field | Example Value | Source |
|-------|---------------|--------|
| Subsystem | FID Box2 / CID Slot1 / SLD-OIL | Fixed by hardware position |
| Ingredient Name | "Chili Powder" | From recipe ingredient list |
| Quantity | 8 × ¼ tsp (FID), whole slot pre-measured 150 g (CID), 30 mL (SLD) | From recipe (adjusted for servings) |
| Pre-loaded | Yes/No | User confirms via touchscreen or app |

CID slots are assigned in order of use (Slot1 first) because of the dispense-order constraint in §5.3.

### 10.3 Pre-Flight Check

Before starting a recipe, the system verifies all required subsystems:

1. **DSB self-test (boot and pre-flight):** rail on, each servo moved to its home angle and back 5°, INA219 #1 current profile within window, PCA9685 ACKs; `DISPENSER_STATUS` reports CID at position 0 and FID gate closed
2. **FID / CID:** User confirms canisters and slots loaded via touchscreen (no automatic fill detection — visual confirmation)
3. **SLD:** Read each reservoir's dedicated load cell — compare oil and water levels individually to minimum required for recipe; alert if either is below threshold
4. Display subsystem status on UI: loaded / insufficient / empty
5. Block recipe start if any required subsystem is insufficient

## 11. Food Safety

### 11.1 Temperature and Hold Time

| Consideration | Guideline | Implementation |
|--------------|-----------|----------------|
| Compartment Temperature | Ambient (no active heating or cooling) | Passive, ingredients at room temperature |
| Maximum Hold Time | 2 hours recommended for perishables | Timer starts when user loads, alert at 90 min |
| Allergen Cross-Contamination | Dedicated subsystems per ingredient type | FID: dry powders only, measure wheel is part of each canister. CID: separate bins on one ring. SLD: separate tubes per liquid |
| Raw Meat Handling | A CID slot designated for raw protein in the loading screen | Slot flagged in UI, cleaning reminder after use |

### 11.2 Contamination Prevention

- FID: powder touches only its own canister and measure wheel; the shared chute and steam gate see free-falling powder only and are removable for washing
- CID: bins share the base plate and aperture; the ring and base plate are washed after every use
- SLD: fluid only contacts silicone tubing (per-channel, no shared path)
- All removable parts are smooth, non-porous food-grade PP
- Silicone pump tubing is replaceable (recommended every 3 months or 200 cycles)

## 12. Cleaning Design

### 12.1 Removable Components

The whole Dispensing Unit lifts straight off the Cooking Surface: there is no cable between them, the dock pads are de-energised the moment the unit leaves the pillar, and the unit keeps running on its battery. Lifting it (two-hand lift, ≤ 4 kg fully loaded) brings every reservoir, canister and carousel to the counter or sink in one move and exposes the chutes, nozzles and camera window on the underside for wiping. The parts below are then removed from the lifted unit.

| Component | Removal Method | Dishwasher Safe | Cleaning Frequency |
|-----------|----------------|-----------------|-------------------|
| Dispensing Unit (whole) | Lift straight off the dock; re-seats one way only | No (wipe underside: chutes, nozzles, camera window) | After every use |
| FID Canisters (×6) | Lift out of carousel bay | Yes | After every use |
| FID Canister Caps (×6) | Unscrew threaded cap | Yes | After every use |
| FID Measure Wheels (×6) | Pull out of canister base (bayonet) | Yes | Weekly deep clean |
| FID Carousel Ring | Lift off hub (keyed) | Yes | Weekly |
| FID Chute + Steam Gate Flap | Pull out from below the station | Yes | After every use |
| CID Carousel Ring (5 bins) | Lift off hub (keyed), carousel at home | Yes | After every use |
| CID Base Plate + Chute | Lift out after ring removal | Yes | After every use |
| SLD Reservoirs (×2) | Lift out | Yes | After every use |
| SLD Silicone Tubing (×2) | Disconnect at quick-fit couplings | Hand wash (boil sterilize) | Weekly; replace every 3 months |
| SLD Nozzles (×2) | Unscrew | Yes | After every use |
| DSB Servos, Gear Pairs, Dose Coupling | Not user-removable | No | Wipe-down weekly |
| Solenoid Valve Assembly (SLD) | Not user-removable | No | Wipe-down weekly |

### 12.2 Auto-Rinse Cycle

For quick cleaning of SLD channels between recipes:

1. User fills SLD-WATER reservoir with warm water
2. Select "Rinse" mode on touchscreen
3. System runs pump through each SLD channel sequentially (water + oil lines)
4. Water flushes through tubing and nozzle into pot
5. User discards pot contents; repeat if needed

## 13. Testing and Validation

### 13.1 Test Procedures

| Test | Subsystem | Method | Pass Criteria |
|------|-----------|--------|---------------|
| Dose Volume Accuracy | FID | 10 doses per canister into a tared cup, weigh, divide by density | Within ±10% of 1.23 mL per dose |
| Dose Repeatability | FID | 20 × 4-dose commands per spice | Std. dev. ≤ 5% of mean mass |
| Steam Gate Seal | FID | Boil water 30 min with gate closed, inspect canister outlet | No visible caking or condensation above the gate |
| Index Accuracy | FID, CID | Command every position 50 times, measure aperture/station alignment | Within ±2° carousel, no overshoot past adjacent position |
| Coarse Dispense | CID | 10 trials per slot with 200 mL chopped vegetables | ≥ 95% of contents reach pot, no spillage outside chute |
| Order Enforcement | CID | Command Slot3 while at Slot3, then Slot2 | NACK returned, carousel does not move |
| Liquid Accuracy | SLD | 10 trials per channel, compare load cell reading to scale | Within ±5% of target weight |
| Drip Prevention (SLD) | SLD | After pump stop, observe nozzle for 60s | No drip (solenoid sealed) |
| Stall Detection | DSB | Block carousel by hand during index | DSB_STALL within 1 s, rail off, servo limp |
| Cross-Contamination | All | Dispense colored liquid (SLD), colored powder (FID), inspect adjacent paths | No visible contamination |
| Food Safety Hold Time | All | Load perishable ingredient, monitor temperature over 2 hours | Temperature remains within safe zone (ambient <25°C) |
| Cleaning Verification | All | ATP swab test after cleaning on all removable parts | ATP reading <100 RLU |
| Servo Endurance | DSB | 10,000 index cycles (C1, F1), 50,000 dose strokes (F2), 20,000 gate cycles (F3) | Position within ±2°, no gear wear audible, no rail overcurrent |
| SLD Pump Endurance | SLD | 10,000 pump cycles (1-minute runs) | Consistent flow rate, no tube degradation |
| SLD Solenoid Endurance | SLD | 10,000 open/close cycles | No leaking when closed, consistent response |
| Tubing Replacement | SLD | Replace tubing, verify flow rate matches spec | Flow rate within ±10% of calibrated value |

### 13.2 Prototype Validation Checklist

- [ ] All 6 FID canisters seat in their bays and slide into/out of the station with the F2 coupling parked
- [ ] FID measure wheels seal in every position (no powder leak with gate open and F2 idle)
- [ ] FID dosing achieves ±10% volume accuracy for all 6 spices
- [ ] FID jiggle clears a hand-packed canister without a stall
- [ ] FID steam gate closes fully by spring with the servo unpowered
- [ ] CID ring lifts off and re-seats keyed to Slot1
- [ ] CID COVER sector fully closes the aperture at position 0
- [ ] CID each slot empties into the pot on index (200 mL chopped onion, 200 g dal)
- [ ] Dispense thread NACKs out-of-order slot commands
- [ ] DSB: only one servo moves at a time, rail switches off after each dispense
- [ ] DSB: OE high on E-stop leaves all four servos limp within 50 ms; the OE pull-up keeps them limp from power-up until `epicurad` starts
- [ ] DSB: stall detection fires when a carousel is blocked by hand (INA219 #1 > 2.5 A for 300 ms on the 6V_DSP rail)
- [ ] All four servos, both pumps and both solenoids run from the 6.0 V dispenser rail with no STM32 or CAN involvement; the 6V_DSP rail is also available from the pack with the DU lifted (bench test only — recipe dispensing is paused while undocked)
- [ ] I2C3 enumerates PCA9685 (0x41), PCF8574 #2 (0x21), INA219 #1 (0x40), INA219 #2 (0x44), TCA9543A (0x71) and both NAU7802 (0x2A, one per mux channel) with the mainline drivers
- [ ] SLD peristaltic pumps deliver consistent flow at calibrated speed
- [ ] SLD solenoid valves seal completely when de-energized (no drips)
- [ ] SLD oil reservoir load cell reads within ±1g of calibration weight
- [ ] SLD water reservoir load cell reads within ±1g of calibration weight
- [ ] SLD closed-loop dispensing achieves ±5% accuracy (both channels independently)
- [ ] SLD low-level alert triggers when reservoir weight drops below configured threshold
- [ ] Pre-flight check correctly identifies empty/insufficient subsystems
- [ ] All chutes/nozzles through the DU underside direct ingredients into pot center when docked (no spillage)
- [ ] Whole DU lifts off and re-docks one way only with reservoirs, canisters and rings in place (≤ 4 kg loaded)
- [ ] Auto-rinse cycle clears visible residue from SLD tubing

## 14. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture]]
- [[01-Electric-Heating|Electric Heating System]]
- [[02-Robotic-Arm|Robotic Arm System]]
- [[04-Vision-System|Vision System]]
- [[02-Database-Schema|Database Schema]]
- [[01-Safety-Compliance|Safety & Compliance]]

#epicura #ingredient-dispensing #subsystem #fid #cid #sld #servo #carousel

---

## 15. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-15 | Manas Pradhan | Rewrite: replaced 6-compartment C1-C6 system with 3 subsystems (ASD, CID, SLD) |
| 3.0 | 2026-02-16 | Manas Pradhan | Replaced ASD (servo-gated gravity-fed, 3 hoppers) with P-ASD (pneumatic puff-dosing, 6 cartridges) |
| 4.0 | 2026-02-16 | Manas Pradhan | P-ASD solenoids now controlled via PCF8574 I2C GPIO expander (addr 0x20) on Driver PCB instead of 6× direct STM32 GPIO |
| 5.0 | 2026-03-11 | Manas Pradhan | CID-1: replaced DC linear actuator + DRV8876 #1 with NEMA 23 stepper motor + external driver (PUL/DIR/ENA via PA10, PB4, PCF8574 P7); CID-2 unchanged; updated GPIO table, dispensing mechanism, actuator specs |
| 6.0 | 2026-03-11 | Manas Pradhan | SLD solenoids moved from PA7/PA9 to PCF8574 #2 (0x21) P0/P1 for GPIO headroom; I2C1 bus now 5 devices |
| 6.1 | 2026-11-04 | Manas Pradhan | Application processor renamed from Raspberry Pi CM5 to RV1106 (Luckfox Pico Zero); dispensing hardware, pin map and command protocol unchanged (LED ring 5 V switch stays on PCF8574 #2 P3) |
| 7.0 | 2026-11-04 | Manas Pradhan | P-ASD (pneumatic) replaced by FID: 6-canister servo carousel with per-canister ¼ tsp measure wheels, 3 servos (index, dose, steam gate); CID replaced by a 5-slot + cover servo carousel, 1 servo; FID and CID merged into one Dispenser Servo Block (4× DS3218-class servos on PCA9685 @ 0x41, switched 6.5 V rail from MP1584EN #2, OE on PB4); removed pump, accumulator, 6 solenoids, ADS1015, PCF8574 #1, NEMA 23 + driver, linear actuator, DRV8876 #2, J_CID; new commands DISPENSE_FID/CID, DISPENSER_HOME, DISPENSER_STATUS; box/slot numbering aligned with recipe schema |
| 7.1 | 2026-11-04 | Manas Pradhan | Command protocol mapped onto the shared CAN bus (IDs 0x230–0x239, seq byte, ACK 0x3FF) |
| 7.2 | 2026-11-04 | Manas Pradhan | I2C1 device list and PCF8574 #2 allocation updated (IR thermometer removed; stir-motor 24 V enable and charger status pins); recipe example uses module surface temperature |
| 7.3 | 2026-11-04 | Manas Pradhan | DSB servos sized per axis instead of 4× DS3218: C1 keeps the DS3218 270° (bin contents slide on the base plate, ≈ 3–5 kg·cm), F1 and F2 become MG996R, F3 becomes MG90S fed through D_DSB4 (1N4007, ≈ 5.8 V) on the 6.5 V rail; F1 gear-up changed 4:3 → 5:3 so the 180° servo still reaches 300° carousel travel; per-channel angle tables; DS3218 figures from the DSSERVO datasheet (21.5 kg·cm / 2.2 A at 6.8 V); servo BOM ≈ $20.50 |
| 7.4 | 2026-11-04 | Manas Pradhan | Three-unit architecture: all three dispensers live in the lift-off Dispensing Unit and are driven by the RV1106 `dispense` thread over I2C3/PWM on the Unified PCB v4.0 (no STM32, no CAN); DSB rail re-specified to 6.0 V (6V_DSP, MP1584EN #2 from VSYS, D_DSB4 removed), pumps and solenoids re-specified to 6 V, INA219 #1 shunt moved to the 6V_DSP rail; HX711 ×2 replaced by NAU7802 ×2 behind a TCA9543A mux; PCF8574 #2 map and PCA9685 OE on an RV1106 GPIO; §7 rewritten as the RV1106 control interface with an in-process command queue (CAN IDs 0x230–0x239 retired); faults RV1106-local; whole-unit lift-off added to layout, cleaning and validation |
