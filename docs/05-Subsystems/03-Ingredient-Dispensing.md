---
created: 2026-02-15
modified: 2026-11-04
version: 7.1
status: Draft
---

# Ingredient Dispensing System

## 1. Overview

The ingredient dispensing system is divided into three purpose-built subsystems, each optimized for a different ingredient class. Together they surround the cooking pot and are orchestrated by the STM32 controller under commands from the RV1106 recipe engine, received over the isolated CAN bus the two processors share with the induction surface.

The FID and CID share one mechanical concept (a servo-indexed carousel) and one electrical control block (the **Dispenser Servo Block, DSB**): four identical hobby-class servos driven from a single PCA9685 PWM driver on I2C1, powered from one switched 6.5 V rail. The SLD keeps its own pump/valve/load-cell hardware.

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
│               └──┤ Box 6 │ Box 1 ├──┘   (4:3 gear-up)  │
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
   F1/C1 servo ──► 4:3 gear-up ──► ring gear on carousel hub
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
    │  Peristaltic │ ◄── 12V DC gear motor, PWM speed control
    │  Pump        │     Flow rate: 5-50 mL/min
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Solenoid    │ ◄── 12V NC solenoid, prevents drip when idle
    │  Valve       │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  Nozzle      │ ──► Into cooking pot
    └──────────────┘

    ┌──────────────┐  ┌──────────────┐
    │  Load Cell   │  │  Load Cell   │ ◄── 2× dedicated HX711 (one per reservoir)
    │  (under oil  │  │  (under water│     Closed-loop: pump until target Δweight
    │   reservoir) │  │   reservoir) │     Low-level alert when < threshold
    └──────────────┘  └──────────────┘
```

## 3. Common Carousel Design (FID and CID)

### 3.1 Servo

All four DSB servos are the same part, so the firmware uses one angle table and one driver.

| Parameter | Value |
|-----------|-------|
| Type | DS3218-class digital servo, metal gear, 270° travel |
| Torque | 20 kg·cm at 6.8 V (≈ 18 kg·cm at 6.5 V) |
| Speed | ~0.16 s / 60° (no load) |
| Signal | 50 Hz PWM, 500–2500 µs pulse (0–270°) |
| Supply | 6.5 V DSB rail (MP1584EN #2 buck, 3 A) |
| Current | ~0.1 A holding, ~1.5 A moving, ~2.5 A stall |
| Position feedback | None external (internal potentiometer, absolute); open loop at the STM32 |
| Cost | ~$10 each |

### 3.2 Index Drive (C1, F1)

| Parameter | Value |
|-----------|-------|
| Coupling | 4:3 spur gear-up (servo 32T → carousel ring gear 24T), POM or printed |
| Travel | Servo 0–225° → carousel 0–300° (six 60° positions) |
| Carousel torque | ≈ 13 kg·cm at 6.5 V (ample; ring runs on a thin-section ball bearing) |
| Resolution | 4.9 µs PWM step ≈ 0.66° servo ≈ 0.9° carousel |
| Homing | None required: gear mesh is assembled at marked teeth, servo position is absolute |
| Position table | pos 0 = 0°, pos 1 = 45°, pos 2 = 90°, pos 3 = 135°, pos 4 = 180°, pos 5 = 225° (servo angles) |

Moves are ramp-limited in firmware (≤ 3° servo per 20 ms tick, ≈ 1.5 s for a 60° carousel step) so that loaded bins do not slosh and the rail current stays under 2 A.

### 3.3 Rules shared by both carousels

- Only one DSB servo moves at a time (firmware mutex); the 6.5 V rail is switched on for the duration of a dispense and off when idle (no holding buzz, no idle heat).
- PCA9685 OE is driven high (all outputs off, servos limp) in the boot-safe state and on E-stop; the rail is also switched off.
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
| Carousel index | F1 | 0–225° (6 positions via 4:3 gear-up) | Brings the selected canister over the station |
| Dose | F2 | 0° ↔ 180° swing per dose | Rotates the canister's measure wheel: pocket fills under the outlet at 0°, discharges into the chute at 180° |
| Steam gate | F3 | 0° (closed) ↔ 70° (open) | Spring-assisted flap at the chute mouth; open only while dosing so pot steam does not reach the powder path |

Anti-bridging is done in software with no extra hardware: before each dose F2 jiggles the measure wheel ±15° three times (shears any arch at the outlet) and F1 wiggles the carousel ±2° twice.

### 4.4 Dose Sequence

1. RV1106 sends `DISPENSE_FID(box_id, qty_quarter_tsp)`
2. STM32 switches the DSB rail on, indexes F1 to `box_id` (ramped)
3. F3 opens the steam gate (70°)
4. For each dose: F2 jiggle (±15° × 3), F2 to 180° (discharge), F2 back to 0° (refill) — ≈ 0.8 s per dose
5. F3 closes the gate, rail off
6. ACK with `doses_done` and the estimated mass (dose count × calibrated mass per dose)

A stall or I2C NACK during any move aborts the sequence (rail off, OE high) and raises `DSB_STALL` (0x12) to the RV1106.

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

1. RV1106 sends `DISPENSE_CID(slot_id)`
2. STM32 rejects (NACK) if `slot_id` is not greater than the current carousel position
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
| Pump | 12V DC peristaltic, 5–50 mL/min | 12V DC peristaltic, 5–50 mL/min |
| Valve | 12V NC solenoid (drip prevention) | 12V NC solenoid (drip prevention) |
| Nozzle | Directed into pot center | Directed into pot center |

### 6.2 Actuators

**Peristaltic Pump (×2):**

| Parameter | Value |
|-----------|-------|
| Type | Peristaltic roller pump, 12V DC gear motor |
| Tube | Food-grade silicone, 6 mm ID |
| Flow Rate | 5–50 mL/min (adjustable via PWM motor speed) |
| Accuracy | ±2% volumetric (further refined by load cell) |
| Advantage | Self-priming, no contamination (fluid only touches tube), reversible |
| Cost | ~$10 each |

**Solenoid Valve (×2):**

| Parameter | Value |
|-----------|-------|
| Type | 12V DC, normally closed, spring return |
| Response | <50 ms open/close |
| Purpose | Prevent dripping when pump is off |
| Power | ~5W when energized |
| Driver | N-channel MOSFET (IRLZ44N) with flyback diode |
| Cost | ~$4 each |

### 6.3 Dedicated Load Cells (2×)

| Parameter | Value |
|-----------|-------|
| Type | 2× 2 kg strain gauge (one under each SLD reservoir: oil and water) |
| ADC | 2× dedicated HX711 |
| Purpose | Individual liquid level monitoring + closed-loop dispensing by tracking reservoir weight decrease |
| Capacity | 2 kg per load cell (accommodates full reservoir + container weight) |
| Accuracy | ±1 g (24-bit HX711 with averaging) |
| Sampling | 10 Hz |
| Low-Level Alert | Configurable threshold per channel (default: 50 g remaining); alert sent to RV1106 + UI when level drops below threshold |
| Cost | ~$5 (load cell) × 2 + ~$3 (HX711) × 2 = ~$16 total |

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
│               │        send SLD_LOW_LEVEL alert to RV1106
└───────────────┘
```

Accuracy: ±5% of target weight (dedicated load cell and controllable flow rate).

## 7. STM32 Control Interface

### 7.1 Dispenser Servo Block (DSB)

The FID and CID are one electrical block on the Unified PCB:

```
  24V Rail ──► MP1584EN #2 (6.5 V, 3 A) ──► P-MOSFET high-side switch ──► 6.5 V DSB rail
                                               ▲                            │  1000 µF bulk + 3 A PTC
                                   PCF8574 #2 P4 (rail enable)              │
                                                                            ▼
  I2C1 (PA15/PB7) ──► PCA9685 (addr 0x41) ──┬── CH0 ──► J_DSB1 ──► C1  CID index servo
                                            ├── CH1 ──► J_DSB2 ──► F1  FID index servo
  PB4 (GPIO) ──► PCA9685 OE (active-low)    ├── CH2 ──► J_DSB3 ──► F2  FID dose servo
                                            └── CH3 ──► J_DSB4 ──► F3  FID steam-gate servo
                                                 CH4–CH15 spare
```

| Element | Part | Notes |
|---------|------|-------|
| PWM driver | PCA9685PW (TSSOP-28), I2C1 addr 0x41 | 16 channels, 12-bit, 50 Hz; CH0–CH3 used |
| Output enable | PB4 → OE (active-low) | High in boot-safe state and on E-stop |
| Rail | MP1584EN #2 set to 6.5 V (previously retained for future use) | Switched by PCF8574 #2 P4 via AO3401-class P-MOSFET; 3 A PTC; 1000 µF bulk |
| Connectors | J_DSB1–4, 3-pin JR (signal / 6.5 V / GND), 2.54 mm, keyed | Standard servo leads, 300 mm extensions |
| Fault detection | INA219 24 V rail current window during moves + move timeout + PCA9685 I2C NACK | Raises `DSB_STALL` (0x12) |

### 7.2 GPIO and PWM Assignments

| Subsystem | Actuator | STM32 Pin | Interface | Notes |
|-----------|----------|-----------|-----------|-------|
| **FID/CID** | Servos C1, F1, F2, F3 | PCA9685 CH0–CH3 (I2C1, addr 0x41) | 50 Hz PWM, 500–2500 µs | One part number, one angle table |
| **FID/CID** | PCA9685 OE | PB4 (GPIO) | Digital output, active-low | High = all servo outputs off |
| **FID/CID** | DSB 6.5 V rail enable | PCF8574 #2 P4 (I2C1, addr 0x21) | Digital output via P-MOSFET | On only during a dispense |
| **SLD** | Pump Motor SLD-OIL (PWM) | PC3 (GPIO) | PWM (motor speed) | TB6612 PWMA via MOSFET |
| **SLD** | Pump Motor SLD-OIL (DIR) | PC4 (GPIO) | Digital output | TB6612 AIN1 direction |
| **SLD** | Pump Motor SLD-WATER (PWM) | PC5 (GPIO) | PWM (motor speed) | TB6612 PWMB via MOSFET |
| **SLD** | Pump Motor SLD-WATER (DIR) | PC6 (GPIO) | Digital output | TB6612 BIN1 direction |
| **SLD** | Solenoid SLD-OIL | PCF8574 #2 P0 (I2C1, addr 0x21) | Digital output via MOSFET | 12V NC solenoid, flyback diode |
| **SLD** | Solenoid SLD-WATER | PCF8574 #2 P1 (I2C1, addr 0x21) | Digital output via MOSFET | 12V NC solenoid, flyback diode |
| **SLD** | HX711 #1 SCK (oil) | PC11 (GPIO) | Clock out | SLD oil reservoir load cell (2 kg) |
| **SLD** | HX711 #1 DOUT (oil) | PC12 (GPIO) | Data in | SLD oil reservoir load cell (2 kg) |
| **SLD** | HX711 #2 SCK (water) | PC9 (GPIO) | Clock out | SLD water reservoir load cell (2 kg) |
| **SLD** | HX711 #2 DOUT (water) | PC10 (GPIO) | Data in | SLD water reservoir load cell (2 kg) |

> **Note:** Pin assignments match [[01-Unified-PCB-Design|Unified PCB Design]] document. Replacing the P-ASD pneumatics and the stepper/linear-actuator CID with the DSB removes PCF8574 #1 (0x20), the ADS1015 (0x48), DRV8876 #2, the six IRLML6344 solenoid MOSFETs, the pump MOSFET and connector J_CID, and frees PA0, PA10, PB5, PB6, PB11, PC2 and PD2. I2C1 bus devices are now three: PCF8574 #2 (0x21), INA219 (0x40), PCA9685 (0x41) — the MLX90614 IR thermometer is gone (the induction module reports its own temperature). PCF8574 #2 P4 is the DSB rail enable; P5 switches the stir motor's 24 V; P6/P7 read the battery charger status.

### 7.3 Dispensing Command Protocol (RV1106 → STM32, CAN IDs 0x230–0x239)

Commands travel on the CAN bus as frames with ID 0x200 + code, a sequence byte first and the parameters after it; responses come back in ACK/NAK 0x3FF with up to 5 data bytes (see [[02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]). The codes below are the low byte of the CAN ID.

| Command | Code | Parameters | Response | Description |
|---------|------|------------|----------|-------------|
| DISPENSE_FID | 0x30 | box_id (1 byte: 1–6), qty_quarter_tsp (1 byte: 1–40) | ACK + doses_done (1 byte) + est_mass_dg (2 bytes, 0.1 g) | Index canister, open gate, N dose strokes, close gate |
| DISPENSE_CID | 0x31 | slot_id (1 byte: 1–5) | ACK + cid_pos (1 byte); NACK if slot_id ≤ current position | Rotate slot over the aperture, dwell, wiggle |
| DISPENSE_SLD | 0x32 | channel (1 byte: OIL=1, WATER=2), target_weight_g (2 bytes) | ACK + actual_weight_g | Pump liquid, closed-loop via dedicated load cell |
| QUERY_WEIGHT | 0x35 | source (1 byte: SLD_OIL=1, SLD_WATER=2) | weight_g (4 bytes) | Read weight from individual SLD load cell |
| PREFLIGHT | 0x36 | subsystem_mask (1 byte) | status per subsystem | Check if required subsystems are loaded/ready |
| TARE | 0x37 | source (1 byte: SLD_OIL=1, SLD_WATER=2) | ACK | Zero the specified SLD load cell readings |
| DISPENSER_HOME | 0x38 | target (1 byte: CID=1, FID=2, 0xFF=both) | ACK | CID → COVER over aperture (pos 0); FID → gate closed, measure at fill, carousel to Box1 |
| DISPENSER_STATUS | 0x39 | — | cid_pos, fid_box, gate_open, rail_on, busy (1 byte each) | Carousel positions for the loading screen |

## 8. Fault Handling (DSB)

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Rail on,     │────►│ Ramped move   │────►│ Move done    │
│ OE low       │     │ (≤3°/tick)    │     │ within       │
└──────────────┘     └───────────────┘     │ timeout?     │
                                           └──────┬───────┘
                                                   │
                                          Yes ◄────┴────► No (INA219 > 2.5 A for 300 ms,
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
                                           │ Continue │   │ DSB_STALL    │
                                           │ sequence │   │ 0x12: rail   │
                                           └──────────┘   │ off, OE high,│
                                                          │ alert user   │
                                                          └──────────────┘
```

Because the servos are open loop, a jammed carousel is detected by current and time, not position. The user is prompted to clear the jam and tap Resume; the sequence then restarts from `DISPENSER_HOME`.

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

1. **DSB self-test (boot and pre-flight):** rail on, each servo moved to its home angle and back 5°, INA219 current profile within window, PCA9685 ACKs; `DISPENSER_STATUS` reports CID at position 0 and FID gate closed
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

| Component | Removal Method | Dishwasher Safe | Cleaning Frequency |
|-----------|----------------|-----------------|-------------------|
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
- [ ] CID firmware NACKs out-of-order slot commands
- [ ] DSB: only one servo moves at a time, rail switches off after each dispense
- [ ] DSB: OE high on E-stop leaves all four servos limp within 50 ms
- [ ] DSB: stall detection fires when a carousel is blocked by hand
- [ ] SLD peristaltic pumps deliver consistent flow at calibrated speed
- [ ] SLD solenoid valves seal completely when de-energized (no drips)
- [ ] SLD oil reservoir load cell reads within ±1g of calibration weight
- [ ] SLD water reservoir load cell reads within ±1g of calibration weight
- [ ] SLD closed-loop dispensing achieves ±5% accuracy (both channels independently)
- [ ] SLD low-level alert triggers when reservoir weight drops below configured threshold
- [ ] Pre-flight check correctly identifies empty/insufficient subsystems
- [ ] All chutes/nozzles direct ingredients into pot center (no spillage)
- [ ] Auto-rinse cycle clears visible residue from SLD tubing

## 14. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture]]
- [[01-Induction-Heating|Induction Heating System]]
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
