---
created: 2026-02-15
modified: 2026-11-05
version: 7.6
status: Draft
---

# Ingredient Dispensing System

## 1. Overview

The ingredient dispensing system is divided into three purpose-built subsystems, each optimized for a different ingredient class. All three live in the lift-off **Dispensing Unit (DU)** that sits on top of the Cooking Surface and surrounds the cooking pot from above. They are driven by the **DU STM32** (STM32G0B1RET6, FreeRTOS Dispense task) over I2C1 and timer PWM on the Unified PCB v5.0 inside the DU, under commands the RV1106 `dispense` thread of `epicurad` sends over the host link (UART2 ↔ USART1) as the 0x230–0x239 block. No dispensing frame appears on the CAN bus.

The FID and CID share one mechanical concept (a servo-indexed carousel) and one electrical control block (the **Dispenser Servo Block, DSB**): four hobby-class servos sized per axis (DS3218, 2× MG996R, MG90S) driven from a single PCA9685 PWM driver on the DU STM32's I2C1, powered from one switched 6.0 V dispenser rail (6V_DSP). The SLD (redesigned 2026-11-05 on the robot-mop pattern, §6) is two drawer tanks with pumps in the DU body on the same board and rail, metered open loop by pump tach pulses; it has no solenoid valves and no load cells.

Since 2026-11-05 the DU is a **Ø350 mm disc, ≤ 150 mm tall** (robot-vacuum form factor), and the three dispensers are laid out concentrically (§2.1).

| Subsystem | Full Name | Purpose | Actuators | Metering |
|-----------|-----------|---------|-----------|----------|
| **FID** | Fine Ingredients Dispenser | Powdered spices, salt, sugar, dry seasonings (6 canisters) | 3 servos on the DSB: F1 carousel index, F2 dose, F3 steam gate | Volumetric, ¼ tsp per dose stroke (open loop, ±10%) |
| **CID** | Coarse Ingredients Dispenser | Pre-cut vegetables, meat, paneer, dal, rice (5 slots) | 1 servo on the DSB: C1 carousel index | Whole slot per dispense (user pre-measured) |
| **SLD** | Standard Liquid Dispenser | Oil and water | 2 drawer tanks (200 mL oil, 500 mL water) + 2 pumps in the body (6 V peristaltic for oil, 6 V diaphragm for water) with Hall tachs, nozzle check valves, float low-level + tank-present Hall switches | Open loop, pump tach pulses × calibrated mL/pulse (±5 %); low-level and tank-absent alerts |

Box and slot numbering matches the recipe contract already used by the cloud schema and recipe schema: FID **Box1–Box6** dosed in multiples of ¼ tsp, CID **Slot1–Slot5** dispensed whole (see [[02-Database-Schema|Database Schema]] §3.6).

## 2. Layout

### 2.1 Top-View Arrangement

The DU is a Ø350 mm disc (≤ 150 mm tall) and the dispensers sit in concentric rings around the camera, the way a robot vacuum packs its bin, tank and electronics around its centre. Everything inside the CID aperture radius drops straight into the 25 cm pot below; the outer ring, which overhangs the pot rim and sits over the cooker body, holds only what needs no pot access.

```
                 REAR OF UNIT  (dock pads on the underside, left-rear, over the pillar)
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  SERVICE RING (Ø270–350, 40 mm wide): SLD water drawer tank ≈ 90°,         │
   │  SLD oil drawer tank ≈ 35°, pumps + check valves under the tank bays,      │
   │  2S2P pack (cells tangential) ≈ 50°, Unified PCB (annular sector,          │
   │  ≈ 150°), buzzer, dock pads                                                │
   │      ┌─────────────────────────────────────────────────────┐               │
   │      │  CID RING (Ø190–270): Slot 1 … Slot 5 + COVER sector  │             │
   │      │  ≈ 215 mL per bin, 45 mm tall; C1 index servo;        │             │
   │      │  base-plate aperture + 45° chute inward over the rim  │             │
   │      │      ┌─────────────────────────────────────────┐      │             │
   │      │      │  FID RING (Ø100–170): Box 1 … Box 6      │      │            │
   │      │      │  (Ø45 × 60 mm canisters), F1 index,      │      │            │
   │      │      │  F2 dose + F3 gate at the station;       │      │            │
   │      │      │  doses drop straight into the pot        │      │            │
   │      │      │        ┌─────────────────────┐           │      │            │
   │      │      │        │  CAMERA + LED RING  │           │      │            │
   │      │      │        │  Ø60 sealed window  │           │      │            │
   │      │      │        │  in the hollow hub  │           │      │            │
   │      │      │        └─────────────────────┘           │      │            │
   │      │      └─────────────────────────────────────────┘      │             │
   │      └─────────────────────────────────────────────────────┘               │
   │  4" LCD on the front face (15–30°)      SLD nozzles: underside, pot centre │
   └────────────────────────────────────────────────────────────────────────────┘
                                 FRONT OF UNIT
```

Ring order — FID inner, CID outer — is confirmed (2026-11-05); the previous front/rear carousel layout does not fit a Ø350 disc (the Ø230 CID and Ø170 FID rings alone exceed the area over the pot). Height budget: underside layer ≈ 20 mm (window, chutes, nozzles, dock pads), dispenser layer ≈ 70 mm (FID canisters 60 mm + rings), service ring ≈ 85 mm (tanks 50 mm with the PCB and pack above them), lift-off lid over the two rings — ≈ 110–130 mm with 150 mm as the ceiling.

Both carousels sit above pot-rim height; the FID station sits inside the pot outline and drops straight down, the CID aperture at the pot rim feeds a short 45° chute inward.

The DU underside carries the CID chute, the FID drop, the two SLD nozzle cartridges and the camera window (see [[04-Vision-System|Vision System]]); the tanks, canisters and carousel rings lift off with the unit, so the whole dispensing side of the machine can be carried to the counter for loading and cleaning. The SLD tanks also slide out of the service ring individually (drawer style, from the side of the DU) for refilling without lifting the unit.

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

**SLD (drawer tank + pump in the body + check-valve nozzle):**

```
   ┌──────────────────────────────┐
   │  DRAWER TANK (food-grade PP) │ ◄── slides into its bay in the DU service ring;
   │  oil 200 mL / water 500 mL   │     vented filler cap (vent hole keeps the pump primed)
   │   ○ float + magnet ─────────┼──► Hall switch TANK_x_LOW in the bay wall (≈ 20 mL oil / 50 mL water left)
   │   ■ fixed magnet ───────────┼──► Hall switch TANK_x_PRESENT in the bay wall
   └──────────────┬───────────────┘
        self-sealing poppet (silicone seal) — opens only when the tank is seated
                  ▼
   ┌──────────────────────────────┐
   │  PUMP in the DU body         │ ◄── oil: 6 V peristaltic (≈ 0.4 mL/rev, 30–60 mL/min)
   │  (under the bay, TB6612)     │     water: 6 V diaphragm (≈ 0.25 mL/stroke, ≈ 1 L/min)
   │   ◎ rotor magnet(s) ────────┼──► Hall switch PUMP_x_TACH: 1 pulse ≈ 0.2 mL (oil) / 0.25 mL (water)
   └──────────────┬───────────────┘
                  │ short food-grade silicone line (≈ 2 mL oil / 5 mL water)
                  ▼
   ┌──────────────────────────────┐
   │  NOZZLE CARTRIDGE (snap-out) │ ◄── spring check valve (≈ 5 kPa cracking): no drip, no siphon,
   │  through the DU underside    │     no steam back up the line; dishwasher safe
   └──────────────┬───────────────┘
                  ▼  into the pot centre
```

No solenoid valve, no tubing the user handles, no load cell: the tank, the nozzle cartridge and the pump line are the only wetted parts (pump line replaced yearly). Metering is by counting pump tach pulses against a per-channel calibration (§6.4).

## 3. Common Carousel Design (FID and CID)

### 3.1 Servos

The four DSB servos are sized per axis. All are standard 50 Hz PWM hobby servos (500–2500 µs) on the same PCA9685 and the same switched 6.0 V dispenser rail (6V_DSP), so one driver serves them; the DU STM32 Dispense task keeps a per-channel angle table (travel and gear ratio differ). All four are rated for 6.0 V, so no per-connector series diode is needed.

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

Moves are ramp-limited in the DU STM32 Dispense task (≤ 3° servo per 20 ms tick, ≈ 1.5 s for a 60° carousel step) so that loaded bins do not slosh and the rail current stays under 2 A.

### 3.3 Rules shared by both carousels

- Only one DSB servo moves at a time (dispense-thread mutex); the 6V_DSP rail is switched on for the duration of a dispense and off when idle (no holding buzz, no idle heat).
- PCA9685 OE is driven high (all outputs off, servos limp) in the boot-safe state and on E-stop; the rail is also switched off. A 10 k pull-up on OE keeps the servos limp from power-up until the DU STM32 firmware drives PB0.
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

1. The recipe engine queues `DISPENSE_FID(box_id, qty_quarter_tsp)` to the dispense thread, which sends it to the DU STM32 (0x230)
2. The DU STM32 switches the 6V_DSP rail on, indexes F1 to `box_id` (ramped)
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

1. The recipe engine queues `DISPENSE_CID(slot_id)` to the dispense thread, which sends it to the DU STM32 (0x231)
2. The DU STM32 rejects (NAK, 0x3FE) if `slot_id` is not greater than the current carousel position
3. Rail on; C1 indexes the carousel (ramped) so `slot_id` sits over the aperture — contents free-fall through the chute
4. Dwell 2 s, then wiggle ±5° three times to clear residue
5. Rail off; ACK with the new position

At the end of a recipe (or on `DISPENSER_HOME`) the carousel returns to position 0, placing the COVER sector over the aperture for loading and steam shielding.

### 5.3 Dispense-Order Constraint

Every bin that passes over the aperture empties. Slots are therefore dispensed in **ascending order** (1 → 5) and a recipe may skip a slot only if it was left empty. The ingredient-loading screen enforces this by assigning ingredients to slots in order of use, and the recipe engine validates segment order before `COOKING` starts.

### 5.4 Metering Strategy

CID dispenses a **whole slot** per command; quantities are pre-measured by the user when loading (as before, no closed-loop weight verification).

## 6. SLD — Standard Liquid Dispenser

Redesigned 2026-11-05 on the pattern robot mops use for their water tanks (Roborock, Dreame, Shark): a flat drawer tank with a bottom self-sealing coupling, the pump inside the body rather than on the removable part, open-loop metering by pump run (here: tach pulses), float + Hall low-level sensing, and a priming routine instead of hand priming. The two solenoid valves, the two 2 kg load cells, the NAU7802 ADCs and the TCA9543A mux of the previous design are gone; a check valve in each nozzle does the solenoid's job, a Hall tach on each pump does the load cell's.

### 6.1 Channel Specifications

| Parameter | Oil Channel (SLD-OIL) | Water Channel (SLD-WATER) |
|-----------|----------------------|--------------------------|
| Tank | 200 mL drawer tank, food-grade PP, vented filler cap, dishwasher safe | 500 mL drawer tank, food-grade PP, vented filler cap, dishwasher safe |
| Bay | ≈ 35° of the DU service ring, slides out sideways | ≈ 90° of the DU service ring, slides out sideways |
| Coupling | Bottom self-sealing poppet (spring + silicone seal) into the bay port; sealed when the tank is out | Same |
| Pump (in the DU body) | 6 V DC peristaltic, ≈ 0.4 mL/rev, 30–60 mL/min, ≈ 0.3 A, TB6612 channel A | 6 V DC diaphragm, ≈ 0.25 mL/stroke, ≈ 1 L/min, ≈ 0.6 A, TB6612 channel B |
| Tach | 2 magnets on the roller head → Hall switch, ≈ 0.2 mL per pulse | 1 magnet on the motor shaft → Hall switch, ≈ 0.25 mL per pulse |
| Line | ≈ 2 mL food-grade silicone, pump to nozzle | ≈ 5 mL food-grade silicone, pump to nozzle |
| Nozzle | Snap-out cartridge with spring check valve (≈ 5 kPa), through the DU underside into the pot centre | Same |
| Level | Float + magnet → Hall switch TANK_OIL_LOW, trips at ≈ 20 mL left | Float + magnet → Hall switch TANK_H2O_LOW, trips at ≈ 50 mL left |
| Presence | Fixed magnet → Hall switch TANK_OIL_PRESENT | Fixed magnet → Hall switch TANK_H2O_PRESENT |
| Dose range / time | 5–30 mL; 30 mL ≈ 45 s | 50–500 mL; 500 mL ≈ 30 s |
| Accuracy | ±5 % (±0.5 mL on 10 mL) after calibration | ±5 % after calibration, ±10 % on the datasheet default |

### 6.2 Actuators and Sensors

**Oil pump — peristaltic (×1):**

| Parameter | Value |
|-----------|-------|
| Type | Peristaltic roller pump, 6 V DC gear motor, 3 rollers; runs from the 6V_DSP rail via TB6612 channel A, PWM from the DU STM32 TIM3_CH1 |
| Displacement | ≈ 0.4 mL per roller-head revolution (calibrated per unit, §6.6) |
| Flow | 30–60 mL/min by PWM |
| Tach | Two 3 mm magnets on the roller head, digital Hall switch (AH3572-class, 3.3 V, open-drain) in the pump bracket → PUMP_OIL_TACH |
| Why peristaltic | Self-priming, oil touches only the tube, reversible, and the occluded tube holds the oil column between doses |
| Cost | ~$10 |

**Water pump — diaphragm (×1):**

| Parameter | Value |
|-----------|-------|
| Type | Mini diaphragm pump, 6 V DC, food-grade EPDM diaphragm; TB6612 channel B, PWM from TIM3_CH2 |
| Displacement | ≈ 0.25 mL per motor revolution (one stroke), calibrated per unit |
| Flow | ≈ 1 L/min at 6 V (500 mL in ≈ 30 s); throttled by PWM for small doses |
| Tach | One magnet on the motor shaft, Hall switch → PUMP_H2O_TACH |
| Why diaphragm | The robot-mop peristaltic pumps are tens of mL/min, far too slow for 500 mL of water; a diaphragm pump is cheap, self-priming to ≈ 1 m and runs from the existing 6 V rail. It does not seal when stopped, which is why every nozzle has a check valve |
| Cost | ~$5 |

**Nozzle check valves (×2):** spring-loaded poppet, ≈ 5 kPa cracking pressure, food-grade PP/silicone, inside a snap-out nozzle cartridge on the DU underside. They stop drip after the pump stops, siphoning from the tank (which sits above the nozzle) and steam entering the line over a 200 °C pot. Cost ~$1.50 each. Passive: nothing electrical remains in the liquid path except the pumps.

**Hall switches (×6):** AH3572-class digital unipolar Hall switches on 3.3 V, open-drain outputs with 10 k pull-ups on the Unified PCB, 100 R series: two pump tachs (EXTI inputs), two tank-present (EXTI, arm the prime routine) and two tank-low (polled at 1 Hz). Magnets: 3 mm neodymium discs in the floats, tank walls and pump rotors (encapsulated, never in contact with food). Cost ~$2 for the set.

### 6.3 Drawer Tanks

- Food-grade PP, translucent with a fill-level window; 500 mL water (≈ 100 cm² × 50 mm) and 200 mL oil (≈ 40 cm² × 50 mm), shaped as sectors of the DU service ring
- Slide into their bays from the side of the DU on rails; a detent and the presence magnet confirm seating. Refilling never requires lifting the DU
- Bottom outlet at the lowest point of the tank with a self-sealing poppet; the bay port opens it on insertion. Vented filler cap (vent hole) so the pump never pulls a vacuum — a blocked vent and a clogged outlet are the two robot-mop field failures, so both are on the cleaning checklist
- Float with an encapsulated magnet in a guide tube; a fixed magnet in the outer wall for presence
- Dishwasher safe (top rack); the poppet and float are captive

### 6.4 Metering Strategy (Open Loop, Pulse-Counted)

The DU STM32 Dispense task meters volume, not weight: each pump carries a Hall tach and the dispensed volume is `pulses × cal_ul` (µL per pulse, per channel, calibrated per unit and stored on the RV1106). The recipe engine converts grams to millilitres by density (oil 0.92 g/mL) before sending DISPENSE_SLD.

```
┌───────────────┐
│ 1. Check tank │──► TANK_x_PRESENT high else NAK SLD_TANK_ABSENT;
│               │    TANK_x_LOW low else NAK SLD_LOW_LEVEL
└───────┬───────┘
        ▼
┌───────────────┐
│ 2. Prime if   │──► prime_pending[channel] set (boot or tank re-seated)
│ pending       │    → run the prime routine (§6.5) first; primed_ml reported
└───────┬───────┘
        ▼
┌───────────────┐
│ 3. Rail on,   │──► 6V_DSP on; pump[channel].start(speed)
│ start pump    │    target_pulses = target_ml × 1000 / cal_ul
└───────┬───────┘
        ▼
┌───────────────┐
│ 4. Count tach │──► EXTI pulse counter; first pulse within 1 s and rate ≥ 25 %
│ pulses        │    of nominal, else SLD_DISPENSE_ERROR (dry, blocked, stalled)
└───────┬───────┘
        ▼
┌───────────────┐
│ 5. Stop at    │──► pump[channel].stop(); rail off
│ target, report│    actual_ml = pulses × cal_ul / 1000 (+ primed_ml) in the ACK
└───────────────┘
```

Accuracy: ±5 % of target volume after calibration; the limiting factors are tube wear on the peristaltic (a few percent over its life) and viscosity on the diaphragm pump. A no-flow condition is caught by the tach (no pulses) and by the INA219 #1 pump-current window (< 50 mA open / > 1.5 A stalled), not by weight.

### 6.5 Prime Routine

Every robot mop needs priming after a refill or a long idle (air in the pump and line); so does the SLD. The Dispense task owns it:

- `prime_pending[channel]` is set at boot and on a rising edge of TANK_x_PRESENT (tank re-seated, debounced 100 ms)
- It runs automatically at the start of the next DISPENSE_SLD on that channel, or on demand with SLD_PRIME (0x233) — the RV1106 sends SLD_PRIME from the loading screen after the user refills, so the first dose of the recipe is exact
- The routine pumps a fixed `N_PRIME` pulses at 50 % PWM (≈ 1.5 × the line volume: oil 3 mL = 15 pulses, water 8 mL = 32 pulses) into the pot and reports `primed_ml` in the ACK; the recipe engine logs it. Tach pulses must appear within 2 s or SLD_DISPENSE_ERROR is raised
- It never runs while the DU is lifted (DOCK_SENSE_A high → NAK NOT_DOCKED): the nozzle must be over the pot

### 6.6 Calibration

`cal_ul` defaults to the pump datasheet (oil 200 µL/pulse, water 250 µL/pulse). On first use and after a pump-line change the UI runs a calibration: the user places a measuring cup under the nozzle (DU lifted onto the counter, bench mode, dispensing allowed only in this UI flow), the RV1106 commands a fixed 100 pulses (oil) / 400 pulses (water), the user types the measured millilitres, and the RV1106 stores the new `cal_ul` in SQLite and sends it to the DU STM32 with SLD_CAL (0x237) at every boot. No tare, no scale.

## 7. DU STM32 Control Interface

### 7.1 Dispenser Servo Block (DSB)

The FID and CID are one electrical block on the Unified PCB v5.0 inside the Dispensing Unit, driven by the DU STM32 (the RV1106 only sends commands over the host link):

```
  VSYS ──► MP1584EN #2 (6.0 V, 3 A) ──► Q_DSB P-MOSFET high-side switch ──► 6V_DSP dispenser rail
                                               ▲                            │  1000 µF bulk + 3 A PTC
                                   PCF8574 #2 P4 (rail enable)              │  INA219 #1 (0x40) shunt
                                                                            ▼
  STM32 I2C1 (PB6/PB7) ► PCA9685 (addr 0x41) ──┬── CH0 ──► J_DSB1 ──► C1  CID index servo   (DS3218 270°)
                                                ├── CH1 ──► J_DSB2 ──► F1  FID index servo   (MG996R)
  STM32 PB0 ───► PCA9685 OE (active-low,        ├── CH2 ──► J_DSB3 ──► F2  FID dose servo    (MG996R)
                  10 k pull-up)                 └── CH3 ──► J_DSB4 ──► F3  FID steam-gate servo (MG90S, 6V_DSP direct)
                                                     CH4–CH15 spare
```

VSYS is the Schottky-OR of DOCK_24V (while docked) and the DU's 2S battery (lifted or mains lost), so the dispenser rail is available in both cases; at an empty pack (6.2 V) the buck drops out to ≈ 6.0 V, which is acceptable.

| Element | Part | Notes |
|---------|------|-------|
| PWM driver | PCA9685PW (TSSOP-28), DU STM32 I2C1 addr 0x41 | 16 channels, 12-bit, 50 Hz; CH0–CH3 used; driven by the STM32 HAL I2C (no Linux driver) |
| Output enable | DU STM32 PB0 → OE (active-low), 10 k pull-up | High in boot-safe state, on E-stop and on host-link loss (no HB_AP for 5 s); pull-up keeps servos off until the firmware starts |
| Rail | MP1584EN #2 set to 6.0 V from VSYS | Switched by PCF8574 #2 P4 via Q_DSB (AO3401-class P-MOSFET); 3 A PTC; 1000 µF bulk; also feeds the SLD pumps (TB6612 VM) |
| Connectors | J_DSB1–4, 3-pin JR (signal / V+ / GND), 2.54 mm, keyed | Standard servo leads, 300 mm extensions; all four V+ = 6V_DSP (D_DSB4 removed, all servos rated for 6.0 V) |
| Fault detection | INA219 #1 (0x40) current window on the 6V_DSP rail during moves + move timeout + PCA9685 I2C NACK | Raises `DSB_STALL` on the DU STM32, returned as a NAK result and in DU_STATUS error_code |

### 7.2 GPIO, PWM and I2C Assignments

| Subsystem | Actuator | DU STM32 Pin / Device | Interface | Notes |
|-----------|----------|---------------------|-----------|-------|
| **FID/CID** | Servos C1, F1, F2, F3 | PCA9685 CH0–CH3 (I2C1, addr 0x41) | 50 Hz PWM, 500–2500 µs | DS3218 / MG996R / MG996R / MG90S; per-channel angle table |
| **FID/CID** | PCA9685 OE | PB0 (GPIO) | Digital output, active-low, 10 k pull-up | High = all servo outputs off |
| **FID/CID** | 6V_DSP rail enable | PCF8574 #2 P4 (I2C1, addr 0x21) | Digital output via Q_DSB P-MOSFET | On only during a dispense |
| **SLD** | Pump Motor SLD-OIL (PWM) | PA6 (TIM3_CH1, 20 kHz) | PWM (motor speed) | TB6612 PWMA |
| **SLD** | Pump Motor SLD-OIL (DIR) | PCF8574 #2 P3 (I2C1, addr 0x21) | Digital output | TB6612 AIN1 direction |
| **SLD** | Pump Motor SLD-WATER (PWM) | PA7 (TIM3_CH2, 20 kHz) | PWM (motor speed) | TB6612 PWMB |
| **SLD** | Pump Motor SLD-WATER (DIR) | PCF8574 #2 P5 (I2C1, addr 0x21) | Digital output | TB6612 BIN1 direction |
| **SLD** | Pump tach SLD-OIL | PC0 (EXTI0) | Hall switch, open-drain, 10 k pull-up | 2 pulses per roller-head revolution (≈ 0.2 mL/pulse) |
| **SLD** | Pump tach SLD-WATER | PC1 (EXTI1) | Hall switch, open-drain, 10 k pull-up | 1 pulse per motor revolution (≈ 0.25 mL/pulse) |
| **SLD** | Tank present SLD-OIL / SLD-WATER | PC2 (EXTI2) / PC4 (EXTI4) | Hall switch, fixed magnet in the tank wall | Rising edge arms the prime routine |
| **SLD** | Tank low SLD-OIL / SLD-WATER | PC3 / PC5 (polled 1 Hz) | Hall switch, float magnet | Low at ≈ 20 mL (oil) / ≈ 50 mL (water) left |
| **DSB** | Rail current sense | INA219 #1 (I2C1, addr 0x40) | I2C1, read by the Dispense task | Shunt in the 6V_DSP rail; stall window and self-test |

> **Note:** Pin assignments match [[01-Unified-PCB-Design|Unified PCB Design]] (v5.3) and [[05-MCU-Functional-Specification|MCU Functional Specification]] §10. I2C1 (DU STM32 PB6/PB7, 400 kHz, 4.7 k pull-ups) is the dispenser bus of the DU: PCF8574 #2 (0x21), INA219 #1 (0x40), INA219 #2 (0x44, battery), PCA9685 (0x41). The FT6336 touch controller (0x38) stays on the RV1106's I2C3, which carries touch only. PCF8574 #2 map: P0/P1 spare (were the solenoids), P2 spare (status LED moved to STM32 PC7), P3 TB6612 AIN1, P4 6V_DSP rail enable, P5 TB6612 BIN1, P6 TP5100 CHRG (in), P7 TP5100 STDBY (in). The six SLD Hall switches are direct STM32 GPIO (PC0–PC5) on J_SLD. The HX711 pair, the NAU7802 ×2 + TCA9543A, the solenoid MOSFETs, the 74AHCT1G125 and D_DSB4 are gone from the board. The STM32 on the Cooking Surface Controller in the base has no dispensing role.

### 7.3 Dispensing Command Queue (recipe engine → dispense thread → DU STM32)

Commands are an in-process queue inside `epicurad`: the recipe engine enqueues a command and the `dispense` thread (a thin client, SCHED_OTHER) sends it to the DU STM32 over the host link (UART2 ↔ USART1, 921,600 baud, COBS-framed CAN-shaped frames) and waits for the reply. The DU STM32 Dispense task (50 Hz while a move is active) executes it and answers with DU_ACK / NAK (0x3FE: seq, cmd_type, result_code, ≤ 5 data bytes). Names, parameters and responses are unchanged from the former CAN protocol. The IDs 0x230–0x239 are **DU-local**: they exist only on the host link and are never put on the CAN bus (see [[02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]] and the host-link table in §7.4 there).

| Link ID | Command | Parameters | Response | Description |
|---------|---------|------------|----------|-------------|
| 0x230 | DISPENSE_FID | box_id (1–6), qty_quarter_tsp (1–40) | ACK + doses_done + est_mass_dg (0.1 g) | Index canister, open gate, N dose strokes, close gate |
| 0x231 | DISPENSE_CID | slot_id (1–5) | ACK + cid_pos; NAK if slot_id ≤ current position | Rotate slot over the aperture, dwell, wiggle |
| 0x232 | DISPENSE_SLD | channel (OIL=0, WATER=1), target_ml (uint16) | ACK + actual_ml (uint16), primed_ml (uint8) | Prime if pending, then pump until target_pulses tach pulses; NAK SLD_TANK_ABSENT / SLD_LOW_LEVEL / NOT_DOCKED |
| 0x233 | SLD_PRIME | channel | ACK + primed_ml | Run the prime routine now (§6.5); NAK NOT_DOCKED while lifted |
| 0x235 | QUERY_SLD | channel | flags (bit0 present, bit1 low, bit2 prime_pending), cal_ul (uint16), last_ml (uint16) | Tank state for the loading / preflight screens |
| 0x236 | PREFLIGHT | subsystem_mask | status per subsystem | Check if required subsystems are loaded/ready (servos reachable, rail OK, each tank present and not low) |
| 0x237 | SLD_CAL | channel, cal_ul (uint16, µL per tach pulse) | ACK | Set the channel's metering constant (sent at boot and after calibration, §6.6) |
| 0x238 | DISPENSER_HOME | target (CID=1, FID=2, 0xFF=both) | ACK | CID → COVER over aperture (pos 0); FID → gate closed, measure at fill, carousel to Box1 |
| 0x239 | DISPENSER_STATUS | — | cid_pos, fid_box, gate_open, rail_on, busy | Carousel positions for the loading screen |

0x234 is reserved. Every command frame carries a 1-byte sequence number first; the DU STM32 echoes it in 0x3FE. If the host link falls silent (no HB_AP for 5 s) the DU STM32 switches the 6V_DSP rail off, drives OE high and stops the pumps on its own.

## 8. Fault Handling (DSB)

Faults are detected by the Dispense task on the DU STM32 and reported to the RV1106 as the NAK result code of the failed command and in DU_STATUS (0x311) `error_code`: `DSB_STALL`, `SLD_LOW_LEVEL`, `SLD_DISPENSE_ERROR` and `SLD_TANK_ABSENT`. They never appear in the CSC's STATUS/TELEMETRY frames. The recipe engine reacts exactly as before (pause, prompt, resume). An SLD dispense error is a missing or slow pump tach (no pulse within 1 s of pump start, or a rate under 25 % of nominal for 2 s) or a pump current outside the INA219 #1 window.

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
| In-flight material | Powder in chute after last dose | Pieces still falling during wiggle | Fluid between the check valve and the nozzle tip after the pump stops | FID: gate closes 300 ms after last dose. CID: 2 s dwell. SLD: check valve closes at once, the line stays full so the next dose starts at zero |
| Pocket fill variance | ±10% per dose (packing) | N/A | ±1 pulse (≈ 0.2–0.25 mL) | FID: jiggle before each dose levels the pocket |
| Bulk density drift | Mass per dose off by stored density error | N/A | N/A | Per-spice density table, user-editable |
| Sticky ingredients | Arches at canister outlet | Pieces stick to bin floor/base plate | Oil residue in the pump line, viscosity drift with temperature | FID: jiggle + 60° cone. CID: wiggle, smooth PP. SLD: per-unit calibration, yearly line replacement |
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

1. **DSB self-test (boot and pre-flight):** run by the DU STM32 on PREFLIGHT (0x236): rail on, each servo moved to its home angle and back 5°, INA219 #1 current profile within window, PCA9685 ACKs; `DISPENSER_STATUS` reports CID at position 0 and FID gate closed
2. **FID / CID:** User confirms canisters and slots loaded via touchscreen (no automatic fill detection — visual confirmation)
3. **SLD:** QUERY_SLD per channel — tank present and not low; the user confirms the fill against the recipe's oil and water totals (the tanks have fill windows); SLD_PRIME from the loading screen if a tank was re-seated
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

The whole Dispensing Unit lifts straight off the Cooking Surface: there is no cable between them, the dock pads are de-energised the moment the unit leaves the pillar, and the unit keeps running on its battery. Lifting it (two-hand lift, ≤ 4 kg fully loaded) brings every tank, canister and carousel to the counter or sink in one move and exposes the chutes, nozzles and camera window on the underside for wiping. The parts below are then removed from the lifted unit.

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
| SLD Drawer Tanks (×2) | Slide out of the service ring (no lifting needed) | Yes (top rack; float and poppet captive) | After every use (oil: weekly); check the vent hole and the bottom outlet |
| SLD Nozzle Cartridges (×2, with check valve) | Snap out of the underside | Yes | After every use |
| SLD Pump Line (×2) | Not user-removable (service part) | No | Rinse cycle weekly; replace yearly |
| DSB Servos, Gear Pairs, Dose Coupling | Not user-removable | No | Wipe-down weekly |
| SLD Pumps, Tank Bays, Hall Switches | Not user-removable | No | Wipe the bay ports weekly |

### 12.2 Auto-Rinse Cycle

For quick cleaning of SLD channels between recipes:

1. User fills the SLD-WATER tank with warm water (and, for the oil line, seats a water-filled oil tank)
2. Select "Rinse" mode on touchscreen (DU docked, pot in place)
3. System runs each pump for a fixed pulse count (water 200 pulses, oil 100 pulses)
4. Water flushes through the pump line, check valve and nozzle into the pot
5. User discards pot contents; repeat if needed; the next dose on each channel re-primes automatically

## 13. Testing and Validation

### 13.1 Test Procedures

| Test | Subsystem | Method | Pass Criteria |
|------|-----------|--------|---------------|
| Dose Volume Accuracy | FID | 10 doses per canister into a tared cup, weigh, divide by density | Within ±10% of 1.23 mL per dose |
| Dose Repeatability | FID | 20 × 4-dose commands per spice | Std. dev. ≤ 5% of mean mass |
| Steam Gate Seal | FID | Boil water 30 min with gate closed, inspect canister outlet | No visible caking or condensation above the gate |
| Index Accuracy | FID, CID | Command every position 50 times, measure aperture/station alignment | Within ±2° carousel, no overshoot past adjacent position |
| Coarse Dispense | CID | 10 trials per slot with 200 mL chopped vegetables | ≥ 95% of contents reach pot, no spillage outside chute |
| Order Enforcement | CID | Command Slot3 while at Slot3, then Slot2 (host-link 0x231 from a bench script on the RV1106, or injected over SWD) | NAK (0x3FE) returned, carousel does not move |
| Liquid Accuracy | SLD | 10 trials per channel after calibration (10 mL oil, 300 mL water) into a tared cup | Within ±5 % of target volume |
| Drip Prevention (SLD) | SLD | After pump stop, observe the nozzle for 10 min with the tank full (max head) and the pot at 200 °C | No drip (check valve holds); no siphoning |
| Prime (SLD) | SLD | Remove and re-seat a tank, then DISPENSE_SLD 10 mL | prime_pending set on the present edge; primed_ml reported; dose correct within ±5 % after the prime |
| Low-Level / Absent (SLD) | SLD | Run a tank down; remove a tank | SLD_LOW_LEVEL at ≈ 20 mL (oil) / ≈ 50 mL (water) remaining; SLD_TANK_ABSENT NAK with the tank out |
| Stall Detection | DSB | Block carousel by hand during index | DSB_STALL within 1 s (NAK result + DU_STATUS error_code), rail off, servo limp |
| Cross-Contamination | All | Dispense colored liquid (SLD), colored powder (FID), inspect adjacent paths | No visible contamination |
| Food Safety Hold Time | All | Load perishable ingredient, monitor temperature over 2 hours | Temperature remains within safe zone (ambient <25°C) |
| Cleaning Verification | All | ATP swab test after cleaning on all removable parts | ATP reading <100 RLU |
| Servo Endurance | DSB | 10,000 index cycles (C1, F1), 50,000 dose strokes (F2), 20,000 gate cycles (F3) | Position within ±2°, no gear wear audible, no rail overcurrent |
| SLD Pump Endurance | SLD | 10,000 pump cycles (30 s runs) per channel | mL per pulse within ±5 % of the initial calibration; no tube failure on the peristaltic |
| SLD Check Valve Endurance | SLD | 10,000 open/close cycles plus 100 dishwasher cycles | No leak at full tank head, cracking pressure within ±30 % |
| Tank Coupling | SLD | 1,000 tank insert/remove cycles, wet | No leak from the poppet with the tank out; presence Hall reads correctly on every insertion |

### 13.2 Prototype Validation Checklist

- [ ] All 6 FID canisters seat in their bays and slide into/out of the station with the F2 coupling parked
- [ ] FID measure wheels seal in every position (no powder leak with gate open and F2 idle)
- [ ] FID dosing achieves ±10% volume accuracy for all 6 spices
- [ ] FID jiggle clears a hand-packed canister without a stall
- [ ] FID steam gate closes fully by spring with the servo unpowered
- [ ] CID ring lifts off and re-seats keyed to Slot1
- [ ] CID COVER sector fully closes the aperture at position 0
- [ ] CID each slot empties into the pot on index (200 mL chopped onion, 200 g dal)
- [ ] DU STM32 NAKs out-of-order slot commands (0x3FE result code) and the dispense thread surfaces it
- [ ] DSB: only one servo moves at a time, rail switches off after each dispense
- [ ] DSB: OE high on E-stop and on host-link loss (no HB_AP for 5 s) leaves all four servos limp within 50 ms; the OE pull-up keeps them limp from power-up until the DU STM32 firmware starts
- [ ] DSB: stall detection fires when a carousel is blocked by hand (INA219 #1 > 2.5 A for 300 ms on the 6V_DSP rail)
- [ ] All four servos and both pumps run from the 6.0 V dispenser rail; the 6V_DSP rail is also available from the pack with the DU lifted (bench test and calibration only — recipe dispensing and priming are refused while undocked)
- [ ] DU STM32 I2C1 enumerates PCA9685 (0x41), PCF8574 #2 (0x21), INA219 #1 (0x40) and INA219 #2 (0x44) — checked by the firmware self-test over SWD / PREFLIGHT, not by Linux I2C tools
- [ ] SLD pump tachs count cleanly (no missed or double pulses) at every PWM setting on both pumps
- [ ] SLD nozzle check valves hold with a full tank and a 200 °C pot (no drip in 10 min)
- [ ] SLD drawer tanks seal with the poppet when out, open when seated; vent hole clear
- [ ] SLD open-loop dispensing achieves ±5 % accuracy after calibration (both channels independently)
- [ ] SLD low-level Hall trips at ≈ 20 mL (oil) / ≈ 50 mL (water); tank-present Hall arms the prime routine on re-seating
- [ ] Prime routine runs on the first dose after a tank re-seat and reports primed_ml; refused while lifted
- [ ] Pre-flight check correctly identifies empty/insufficient subsystems
- [ ] All chutes/nozzles through the DU underside direct ingredients into pot center when docked (no spillage)
- [ ] Whole DU (Ø350 × ≤ 150 mm) lifts off and re-docks one way only with tanks, canisters and rings in place (≤ 4 kg loaded)
- [ ] Auto-rinse cycle clears visible residue from the SLD pump lines and nozzle cartridges

## 14. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture]]
- [[01-Electric-Heating|Electric Heating System]]
- [[02-Robotic-Arm|Robotic Arm System]]
- [[05-MCU-Functional-Specification|MCU Functional Specification]] §10 — DU STM32 instance (Dispense task, host link, pin map)
- [[02-Controller-Software-Architecture|Controller & Software Architecture]] §7.4 — host-link protocol and DU-local IDs
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
| 7.6 | 2026-11-05 | Manas Pradhan | Ring order FID inner / CID outer confirmed the same day. SLD redesigned on the robot-mop pattern and the DU re-packaged as a Ø350 × ≤ 150 mm disc: drawer tanks (200 mL oil / 500 mL water, bottom self-sealing poppet, vented cap, float + magnet low level and fixed-magnet presence on Hall switches) in the DU service ring, pumps in the body (6 V peristaltic for oil, 6 V diaphragm for water, each with a Hall tach), spring check valves in snap-out nozzle cartridges; the two solenoid valves, two 2 kg load cells, NAU7802 ×2 and TCA9543A are removed. Metering is open loop by tach pulses × cal_ul (±5 %), with a prime routine (pending at boot and on tank re-seat, auto before the next dose or on SLD_PRIME 0x233) and a per-unit calibration (SLD_CAL 0x237); QUERY_WEIGHT → QUERY_SLD (0x235), TARE → SLD_CAL, SLD_LOAD_CELL_DRIFT → SLD_TANK_ABSENT; six DU STM32 GPIO (PC0–PC5) on a 12-pin J_SLD. §2.1 concentric layout (camera hub, FID ring Ø100–170, CID ring Ø190–270, service ring Ø270–350), §2.2, §6, §7, §8, §9, §10.3, §12, §13 rewritten |
| 7.5 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: all three dispensers are driven by the DU STM32 (STM32G0B1RET6 on the Unified PCB v5.0, FreeRTOS Dispense task) over its I2C1 (PCA9685, PCF8574 #2, INA219 ×2, TCA9543A/NAU7802) and TIM3 pump PWM (PA6/PA7), OE on PB0; the RV1106 `dispense` thread is a thin client sending the 0x230–0x239 block over the host link (UART2 ↔ USART1), answered by DU_ACK 0x3FE; the IDs are DU-local and never reach the CAN bus; faults reported as NAK result / DU_STATUS error_code; host-link loss (5 s) drops the rail and OE; §7 retitled DU STM32 Control Interface, §7.2 pin table, §8, §13 and related docs updated |
