---
created: 2026-02-15
modified: 2026-11-04
version: 2.8
status: Draft
---

# Mechanical Design

## 1. Form Factor

### 1.1 Device Type
**Autonomous Countertop Kitchen Robot** - Stationary appliance designed for compact Indian kitchens

### 1.2 Dimensions
- **Width:** 500 mm
- **Depth:** 400 mm
- **Height:** ≈ 350 mm (to be confirmed; was 300 mm): Cooking Surface ≈ 110 mm + Stirring Unit gantry over the pot + Dispensing Unit ≈ 130 mm on top
- **Weight:** 8-12 kg (assembled, without pot contents); Dispensing Unit ≤ 4 kg fully loaded (two-hand lift)
- **Cooking Surface envelope:** donor Philips OneChef NX5300/00 body + rear pillars + stirrer gantry (§1.5). Retail listings disagree on the donor's size and weight — 38.5 × 35.7 × 28 cm / 6.2 kg (Croma, with the air-fryer lid) vs 33 × 33 × 33 cm / 4.6 kg (Reliance Digital); the OEM drawing governs, and the 500 × 400 mm footprint above is to be confirmed against it
- **Comparable Size:** Large microwave oven or bread maker

### 1.3 Design Philosophy
- Compact footprint for limited countertop space
- All cooking operations contained within enclosure
- Removable components for easy cleaning
- Professional yet approachable kitchen appliance aesthetic
- All user-facing surfaces food-safe and wipe-clean
- Dispensing Unit lifts straight off (no cable) for ingredient loading and cleaning between sessions

### 1.4 Three-Unit Stack

Epicura is physically three units. Only one cable exists between units (Cooking Surface → Stirring Unit, inside the right pillar); the top unit lifts straight off with no cable.

| Unit | Short | Mains? | Contents |
|------|-------|--------|----------|
| **Cooking Surface** | CS | Yes (IEC C14 inlet, fuse, EMI filter) | Modified Philips OneChef NX5300/00 body — the donor cooker's heating plate, controller (own AC stage + CAN), 6 L non-stick inner pot and glass lid; its air-fryer lid is removed and the Dispensing Unit seats in its place (§1.5) — Mean Well LRS-75-24 (24 V), Cooking Surface Controller PCB (CSC, STM32G0B1RE), safety relay, E-stop button (front), 2× exhaust fans + filter cartridge (rear), two rear pillars that carry the Stirring Unit and the dock block |
| **Stirring Unit** | SU | No — fed 24 V by the CS | Gantry bridge between the rear pillars over the pot: 24 V CAN servo stir motor, vertical shaft, paddle, fume hood. One port J_SU (Molex Micro-Fit 3.0, 5-way: 24V_STIR, GND, CAN_H, CAN_L, SHIELD) at the right pillar; harness runs inside the pillar to the CSC |
| **Dispensing Unit** | DU | No — battery is the primary supply | Unified PCB v4.0 (Luckfox Pico Zero RV1106 in J_AP, 2S Li-ion pack, dispenser drivers, RV1106 CAN node), 4" LCD on the front face (tilted 15-30°), IMX415-98 camera + white LED ring on the underside, centred over the pot and looking straight down behind a sealed borosilicate window, FID carousel (rear) + CID carousel (front) with chutes through the underside, SLD oil + water reservoirs (sides) with pumps, solenoids, load cells and nozzles through the underside, buzzer. Dock pads on the underside over the left pillar |

The DU seats on the rear pillars in one orientation only (keyed dock recess on the left pillar). The 8-contact magnetic pogo dock (J_DOCK) carries the 24 V charge input and the isolated CAN bus; lifting the DU opens the bus and the 24 V at the same instant. The user lifts the DU off between sessions to load ingredients and to clean individual coarse slots; on a mains outage the DU (the brain) keeps running on its battery and the session resumes when mains returns. Front-edge support of the DU over the pot well is to be confirmed in the CAD.

### 1.5 Donor Body Modification

The Cooking Surface is not a new enclosure: it is the body of the Philips OneChef NX5300/00 (6 L multicooker with a detachable air-fryer lid; reference unit in [[../05-Subsystems/01-Electric-Heating|Electric Heating]] §2.3), modified as follows.

| | Items |
|---|---|
| **Kept** | Cooker body (matte plastic, cool-touch handles), heating plate with its spring-loaded centre sensor, controller cavity (OEM control board with the CAN port), 6 L non-stick inner pot, glass lid (manual / UNIT_LIFTED use only) |
| **Removed** | Detachable air-fryer lid with its heater and fan, the touch panel (and its lid-detection switch) |
| **Added** | Stirring Unit gantry mount on the rim, two rear pillars (left: dock block + keyed DU recess; right: J_SU port + harness), front E-stop button, 2× exhaust fans + filter cartridge, CSC + LRS-75-24 bay in the rear compartment |

The air-fryer lid's seat on the pot rim is where the Dispensing Unit sits in normal use; the glass lid goes on only when the DU is lifted for a manual cook.

---

## 2. Enclosure Design

### 2.1 Material Selection

| Material | Pros | Cons | Cost | Recommendation |
|----------|------|------|------|----------------|
| **Polypropylene (PP)** | Food-safe, lightweight, cheap, chemical resistant | Lower rigidity, limited finish options | Low | **Prototype default** |
| **Stainless Steel (304 or 430)** | Premium look, durable, excellent heat resistance, easy to clean | Heavy, expensive, harder to fabricate complex shapes | High | Production premium model |
| **PC/ABS Blend** | Balanced strength/cost, good finish, common in appliances | Requires food-safe coating on interior surfaces | Medium | Production standard model |
| **Sheet Metal + PP Interior** | Hybrid: metal exterior, PP food-contact surfaces | More complex assembly | Medium-High | Best compromise |

### 2.2 Pot Specifications

| Parameter | Value |
|-----------|-------|
| Material | Aluminium, non-stick — the 6 L inner pot supplied with the donor OneChef NX5300/00; any flat-bottomed pot of the same base fits, 304 stainless acceptable |
| Interior Coating | Ceramic non-stick or PTFE (Teflon) |
| Capacity | 6 L nominal, ~4.8 L usable (fill ≤ 4/5, min/max marks inside) |
| Diameter | 9 in = 228.6 mm (circular; confirmed 2026-11-04), base matched to the donor heating plate |
| Height | 150 mm (fixed 2026-11-04): 6 L brim-full at 228.6 mm Ø is 146 mm as a straight cylinder, the extra 4 mm covers the rounded base corner; the 4/5 max-fill line (4.8 L) sits at ~120 mm |
| Weight (empty) | 0.8-1.2 kg |
| Handles | As supplied on the OneChef inner pot (OEM drawing); must clear the gantry opening |
| Lid | Donor glass lid, retained for manual / UNIT_LIFTED use; in normal use the Dispensing Unit is the lid |
| Cleaning | Dishwasher-safe, removable |
| Detection | Pot presses the heating unit's spring-loaded centre sensor; the unit reports `pot_detected` (internal pot detection) |

### 2.3 Surface Finish

- **Exterior:** Matte anti-fingerprint texture (fine sand or soft-touch)
- **Interior (food zone):** Smooth, non-porous, food-grade approved
- **Color:** White body with dark gray or stainless accents (appliance standard)
- **Certification:** All food-contact materials comply with FDA 21 CFR / EU 10/2011

---

## 3. Enclosure Layout

### 3.1 Top View

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│ REAR    [Fan 1] [Fan 2] [filter cartridge]  (CS rear panel)  │
│ ┌────────┐                                        ┌────────┐ │
│ │ Left   │════ SU gantry bridge: CAN servo motor ═│ Right  │ │
│ │ pillar │     shaft + paddle + fume hood         │ pillar │ │
│ │ + dock │                                        │ + J_SU │ │
│ └───┬────┘                                        └────┬───┘ │
│     │  ┌───────────────────────────────────────────┐   │     │
│     │  │  Dispensing Unit (DU): lifts off, no cable│   │     │
│     │  │  FID carousel (rear): 6 canisters         │   │     │
│     │  │  [Box1 … Box6] F1 index, F2 dose, F3 gate │   │     │
│     │  │  SLD-OIL  ┌───────────────────┐  SLD-H2O  │   │     │
│     │  │  [pump]   │ Camera + white LED│  [pump]   │   │     │
│     │  │  reservoir│ ring behind sealed│  reservoir│   │     │
│     │  │  (side)   │ window, underside,│  (side)   │   │     │
│     │  │           │ over pot centre   │           │   │     │
│     │  │           └───────────────────┘           │   │     │
│     │  │  CID carousel (front): 5 slots + cover    │   │     │
│     │  │  [Slot1 … Slot5] C1 index (DSB: 4 servos, │   │     │
│     │  │   PCA9685 + 6 V rail, Unified PCB v4.0)   │   │     │
│     │  │  4" LCD on the DU front face (15-30 deg)  │   │     │
│     │  │  dock pads (underside, over left pillar)  │   │     │
│     │  └───────────────────────────────────────────┘   │     │
│     │  (pot well + 23 cm pot on the CS underneath)     │     │
│                                                              │
│  [E-STOP]   FRONT                             [Status LED]   │
└──────────────────────────────────────────────────────────────┘
                        500 mm
```

### 3.2 Front View

```
                         500 mm
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────┐  │ ─┬─
│  │  Dispensing Unit (DU) — lifts straight off, no cable   │  │  │
│  │  ┌────────────────────────────┐                        │  │  │ ≈130 mm
│  │  │  4" Touchscreen Display    │  SLD reservoirs on     │  │  │
│  │  │  (DU front face, 15-30 deg)│  the sides (oil, water)│  │  │
│  │  └────────────────────────────┘                        │  │  │
│  │  underside: camera + LED ring window, FID/CID chutes,  │  │  │
│  │  SLD nozzles, dock pads over the left pillar           │  │  │
│  └────────────────────────────────────────────────────────┘  │ ─┼─
│ ┌──┐                                                   ┌──┐  │  │
│ │  │◄ dock block on this pillar top (J_DOCK pogo)      │  │  │  │ gantry
│ │L │  Stirring Unit (SU): gantry bridge between the    │R │  │  │ over
│ │  │  rear pillars, CAN servo motor + shaft + fume hood│  │  │  │ the pot
│ │  │        Pot Access Opening (insert/remove pot)     │  │  │  │
│ │  │                  [ 23 cm pot ]              J_SU ►│  │  │  │
│ └──┘                                                   └──┘  │ ─┼─
│  ┌────────────────────────────────────────────────────────┐  │  │
│  │  Cooking Surface (CS): heating unit, LRS-75-24 PSU,    │  │  │ ≈110 mm
│  │  CSC (STM32), safety relay; fans + filter at the rear  │  │  │
│  │  [E-STOP]                               [Status LED]   │  │  │
│  └────────────────────────────────────────────────────────┘  │ ─┴─
└──────────────────────────────────────────────────────────────┘
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  Non-slip rubber feet (4x corner)              ≈ 350 mm overall (TBC)
```

### 3.3 Rear View

```
                         500 mm
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Dispensing Unit (DU) rear: FID carousel, no ports     │  │
│  └────────────────────────────────────────────────────────┘  │
│ ┌──────┐                                            ┌──────┐ │
│ │pillar│  SU gantry: stir motor, fume hood ► duct   │pillar│ │
│ │(J_SU)│  (seen from the rear: left/right mirrored) │(dock)│ │
│ └──────┘                                            └──────┘ │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Cooking Surface (CS) rear panel                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────┐    │  │
│  │  │ Fan 1    │  │ Fan 2    │  │ Filter cartridge   │    │  │
│  │  │ (exhaust)│  │ (exhaust)│  │ (slide-out mesh +  │    │  │
│  │  │          │  │          │  │  carbon)           │    │  │
│  │  └──────────┘  └──────────┘  └────────────────────┘    │  │
│  │  ┌──────────┐                                          │  │
│  │  │ IEC C14  │  Rating plate: model, serial,            │  │
│  │  │ inlet +  │  certifications, power specs             │  │
│  │  │ fuse +   │  No service ports on the panel (CSC      │  │
│  │  │ EMI filt.│  USB-C / SWD are inside, bench use only) │  │
│  │  └──────────┘                                          │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.4 Side View (Cross-Section)

```
                         400 mm (depth)
    ◄──────────────────────────────────────────────────────►

     FRONT                                            REAR

    ┌──────────────────────────────────────────────────────┐ ─┬─
    │  Dispensing Unit (DU) — lifts straight off, no cable │  │
    │ ┌─────┐ ┌────────┐ ┌───────────────┐ ┌────────┐      │  │
    │ │ 4"  │ │  CID   │ │ Unified PCB   │ │  FID   │      │  │ ≈130 mm
    │ │ LCD │ │carousel│ │ v4.0 + Pico   │ │carousel│      │  │
    │ │tilt │ │(front) │ │ Zero + 2S bat │ │ (rear) │      │  │
    │ └─────┘ └───┬────┘ └───────────────┘ └───┬────┘ dock │  │
    │  SLD res.   │chute ┌──────────┐ chute    │      pads │  │
    │  (sides)    ▼      │ Camera + │          ▼       ▼   │  │
    │  nozzles ▼         │ LED ring │ (sealed window)      │  │
    ├────────────────────┴────┬─────┴──────────────────────┤ ─┼─
    │  Stirring Unit (SU)     │ straight down    ┌───────┐ │  │
    │  gantry between the     │ 20-30 cm to the  │ CAN   │ │  │ gantry
    │  rear pillars           │ pot rim          │ servo │ │  │ over
    │          ┌──────────────┴───────────┐ shaft│ motor │ │  │ the pot
    │          │  Pot + Food Zone (23 cm) │◄─────┴───────┤ │  │
    │          │  (open top; paddle in)   │  rear pillar │ │  │
    │          │                          │  (harness +  │ │  │
    │          │                          │   dock block)│ │  │
    ├──────────┴──────────────────────────┴──────────────┴─┤ ─┼─
    │  Cooking Surface (CS)                                │  │
    │ [E-STOP] ┌──────────────────────┐ ┌───────┐ ┌──────┐ │  │ ≈110 mm
    │ (front)  │ Heating unit         │ │  CSC  │ │ PSU  │ │  │
    │          │ (own AC stage + CAN) │ │(STM32)│ │LRS-75│ │  │
    │          └──────────────────────┘ └───────┘ └──────┘ │  │
    │  ▓▓▓▓ IEC C14 + fuse ▓▓ Fan 1 ▓▓ Fan 2 ▓▓ filter ▓▓▓ │  │
    └──────────────────────────────────────────────────────┘ ─┴─
                                              ≈ 350 mm (TBC)
```

---

## 4. Internal Layout

### 4.1 Cooking Surface (Top Down)

The CS holds everything on mains: the electric heating unit (centre), the LRS-75-24 PSU and the Cooking Surface Controller (CSC) in the rear compartment beside the fans, the safety relay, the E-stop button and the two rear pillars.

```
┌──────────────────────────────────────────────────────────────┐
│                  REAR — Cooking Surface (CS)                 │
│                                                              │
│  ┌────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ Left   │ │ LRS-75-24  │ │ CSC PCB    │ │ 2x exhaust │     │
│  │ pillar │ │ 24 V PSU   │ │ STM32G0B1  │ │ fans +     │     │
│  │ + dock │ │ IEC C14 +  │ │ relay,     │ │ filter     │     │
│  │ block  │ │ fuse + EMI │ │ J_DOCK,    │ │ cartridge  │     │
│  │ (pogo) │ │ filter     │ │ J_CAN_HEAT │ │ (fume duct)│     │
│  └────────┘ └────────────┘ └────────────┘ └────────────┘     │
│   Right pillar (not shown): J_SU port + harness to the CSC   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  Thermal Barrier                       │  │
│  │   (aluminum sheet or silicone thermal pad)             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │     Commercial Electric Heating Unit (rice-cooker)     │  │
│  │     (self-contained: own AC stage via the safety       │  │
│  │      relay, own PID, CAN to J_CAN_HEAT on the CSC)     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  [E-STOP button, front, NC → CSC J_SAFE]                     │
│                        FRONT                                 │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Dispensing Unit (Top Down)

The DU holds the brain and everything that touches ingredients: the Unified PCB v4.0 with the Luckfox Pico Zero and the 2S Li-ion pack, the 4" LCD on its front face, the camera + white LED ring on its underside, and all three dispensers.

```
┌──────────────────────────────────────────────────────────────┐
│               REAR — Dispensing Unit (DU, top-down)          │
│                                                              │
│  ┌──────────────────┐ ┌────────────────────────────────────┐ │
│  │ Unified PCB v4.0 │ │ FID carousel: 6 canisters, F1/F2/F3│ │
│  │ 160 x 90 mm:     │ │ servos, dosing station → chute     │ │
│  │ Pico Zero (J_AP) │ └────────────────────────────────────┘ │
│  │ MCP2518FD CAN,   │ ┌──────────┐ ┌──────────────┐ ┌──────┐ │
│  │ PCA9685 DSB,     │ │ SLD-OIL  │ │ Camera +     │ │ SLD- │ │
│  │ TB6612 pumps,    │ │ reservoir│ │ white LED    │ │ H2O  │ │
│  │ NAU7802 x2,      │ │ + pump + │ │ ring, sealed │ │ res. │ │
│  │ INA219 x2, TP5100│ │ solenoid │ │ window (under│ │ pump │ │
│  │ J_DOCK pads below│ │ + NAU7802│ │  side, centre│ │ sol. │ │
│  ├──────────────────┤ │ load cell│ │  over pot)   │ │ cell │ │
│  │ 2S Li-ion pack   │ └──────────┘ └──────────────┘ └──────┘ │
│  │ (J_BAT, PCM+NTC) │ ┌────────────────────────────────────┐ │
│  └──────────────────┘ │ CID carousel: 5 slots + cover, C1  │ │
│   dock pads: left-rear│ servo, base-plate aperture → chute │ │
│   underside (pillar)  └────────────────────────────────────┘ │
│  [buzzer]  ┌────────────────────────────────────────┐        │
│            │ 4" LCD + FT6336 touch on the front face│        │
│            └────────────────────────────────────────┘        │
│                        FRONT                                 │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 Stirring Unit

The SU is the gantry bridge between the rear pillars: the 24 V CAN servo stir motor, the vertical shaft with its silicone gasket, the twist-lock paddle and the fume hood that feeds the CS exhaust duct. It has no PCB; its only connection is J_SU at the right pillar (24 V + CAN + shield), wired inside the pillar to J_CAN_STIR + J_STIR_PWR on the CSC.

---

## 5. Pot Design

### 5.1 Specifications

| Parameter | Value |
|-----------|-------|
| Body Material | Aluminium, non-stick (the OneChef NX5300/00 6 L inner pot; alloy per OEM) |
| Base | Flat aluminium base in contact with the heating plate (presses the spring-loaded centre sensor) |
| Interior Coating | Ceramic non-stick (PFOA-free) or PTFE |
| Capacity | 6 L nominal; ~4.8 L usable (fill ≤ 4/5) |
| Outer Diameter | 228.6 mm (9 in, confirmed 2026-11-04) |
| Inner Diameter | ~225 mm (wall ~1.5–2 mm; OEM drawing governs) |
| Height | 150 mm (fixed 2026-11-04; 6 L brim-full, max-fill line at ~120 mm) |
| Wall Thickness | 3 mm (aluminum body) |
| Base Thickness | 3-5 mm aluminium (flat for plate contact) |
| Weight (empty) | 0.8-1.2 kg |
| Max Operating Temp | 200C (heating unit ceiling; non-stick coating) |

### 5.2 Detection Mechanism

- Pot detection is handled internally by the electric heating unit
- The pot presses the unit's spring-loaded centre sensor; the unit reports `pot_detected` in HEAT_STATUS
- No external reed switch or magnet required (the CSC reed switch remains an optional backup)
- Interlock: the unit will not heat without pot detected (internal safety)

### 5.3 Handle Design

- Handles as supplied on the OneChef inner pot (OEM drawing); if folding side handles: stow flat against pot body, flip out for lifting
- Material: Bakelite or silicone-wrapped stainless steel
- Heat rating: handles remain <60C even when pot contents at 200C
- Clearance: handles fit through gantry opening when folded

---

## 6. Robotic Arm Assembly

### 6.1 Gantry-Mounted Stirring System

```
┌─────────────────────────────────────────────────────────┐
│                    Gantry Top View                       │
│                                                         │
│    ┌──────────────────────────────────────────────┐     │
│    │              Gantry Bridge                    │     │
│    │                                               │     │
│    │   ┌─────────┐                 ┌────────────┐  │     │
│    │   │ J_SU    │   Gantry Arm    │ CAN servo  │  │     │
│    │   │ port at │────────────────►│ motor      │  │     │
│    │   │ pillar  │ (24 V + CAN)    │ (24 V)     │  │     │
│    │   └─────────┘                 └─────┬──────┘  │     │
│    │                                     │         │     │
│    └─────────────────────────────────────┼─────────┘     │
│                                          │               │
│                                     Shaft (vertical)     │
│                                          │               │
│                                     ┌────▼─────┐         │
│                                     │ Silicone │         │
│                                     │ Gasket   │         │
│                                     │ (IPX5    │         │
│                                     │  seal)   │         │
│                                     └────┬─────┘         │
│                                          │               │
│                                     ┌────▼─────┐         │
│                                     │ Paddle   │         │
│                                     │ Attach-  │         │
│                                     │ ment     │         │
│                                     │ (remov-  │         │
│                                     │  able)   │         │
│                                     └──────────┘         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

The camera and LED ring are no longer on the gantry: they sit on the underside of the Dispensing Unit, centred over the pot (§3.4). The gantry carries only the stir motor, shaft, paddle and fume hood, and is fed by the single J_SU harness from the Cooking Surface.

### 6.2 Arm Specifications

| Parameter | Value |
|-----------|-------|
| Actuator | 24V BLDC motor with integrated ESC (30-50 kg-cm torque) |
| Rotation | 360 degrees continuous (modified servo or stepper alternative) |
| Speed Range | 10-60 RPM (adjustable via recipe) |
| Shaft Material | 304 stainless steel, 8mm diameter |
| Shaft Length | 150 mm (extends from gantry into pot) |
| Depth Adjustment | Fixed depth (set during assembly for target pot) |
| Paddle | Food-grade silicone or nylon, PTFE-tipped edge — non-stick-safe, no metal touches the coated pot; removable twist-lock |
| Seal | Silicone gasket around shaft penetration (IPX5 rated) |
| Cleaning | Shaft and paddle removable, dishwasher-safe |

### 6.3 Stirring Patterns

The recipe engine commands different stirring patterns:

| Pattern ID | Name | Description | RPM | Use Case |
|------------|------|-------------|-----|----------|
| 0 | Stop | Arm stationary | 0 | Idle, dispensing, settling |
| 1 | Slow Continuous | Steady rotation | 10-15 | Gentle simmer, prevent sticking |
| 2 | Medium Continuous | Moderate rotation | 20-30 | Active cooking, mixing ingredients |
| 3 | Fast Continuous | Vigorous rotation | 40-60 | Rapid mixing, emulsification |
| 4 | Intermittent | 5s on / 10s off | 20 | Light stirring during slow cook |
| 5 | Reverse Alternating | CW 10s / CCW 10s | 25 | Better mixing, prevent vortex |

---

## 7. Ingredient Dispensing Subsystems

See [[03-Ingredient-Dispensing|Ingredient Dispensing System]] for full details.

### 7.1 Layout and Design

```
                    ┌───────────────────────────────────────┐
                    │     Dispensing Layout (Top View)      │
                    │                                       │
                    │  FID (Rear, behind pot):              │
                    │       ┌───────────────┐               │
                    │     ┌─┤ Box4  │ Box3  ├─┐             │
                    │     │ Box5 ──┼── Box2   │  F1 index   │
                    │     └─┤ Box6  │ Box1  ├─┘  (4:3 gear) │
                    │       └───────┬───────┘               │
                    │      station: F2 dose, F3 gate        │
                    │            ▼ Chute (¼ tsp doses)      │
                    │                                       │
                    │  SLD (Left/Right sides):              │
                    │  SLD-OIL ═══► Pot ◄═══ SLD-WATER      │
                    │  [pump+sol]         [pump+sol]        │
                    │                                       │
                    │  CID (Front, above pot rim):          │
                    │            ▲ Chute (whole slot)       │
                    │       ┌───────┴───────┐               │
                    │     ┌─┤Slot3  │Slot2  ├─┐             │
                    │     │Slot4 ──┼── Slot1  │  C1 index   │
                    │     └─┤Slot5  │COVER  ├─┘  (4:3 gear) │
                    │       └───────────────┘               │
                    └───────────────────────────────────────┘
```

All three dispensers travel with the Dispensing Unit. The FID carousel (rear) and CID carousel (front) drop their doses through chutes in the DU underside; the SLD oil and water reservoirs (sides, each on its own NAU7802 load cell) with their pumps, solenoids and nozzles lift off with the DU. Nothing dispensing-related stays on the Cooking Surface: the servos, pumps and solenoids are driven from the Unified PCB v4.0 (switched 6 V rail) by the RV1106 `dispense` thread.

### 7.2 Subsystem Specifications

| Parameter | FID (Fine / Seasonings) | CID (Coarse) | SLD (Liquids) |
|-----------|------------------------|-------------|--------------|
| Count | 6 canisters on one carousel | 5 slots + cover sector on one carousel | 2 channels (oil + water) |
| Capacity | 60 mL each | ~200 mL each (~1 L total) | 200 mL (oil), 500 mL (water) |
| Material | Food-grade PP, integral ¼ tsp measure wheel | Food-grade PP lift-off ring on fixed base plate | PP reservoirs + silicone tubing |
| Actuator | 3 servos (F1 index, F2 dose, F3 steam gate) on the DSB | 1 servo (C1 index) on the DSB | Peristaltic pump + solenoid valve |
| Carousel | Ø170 mm, 60° bays, 4:3 gear-up from servo | Ø230 mm, 60° sectors, 4:3 gear-up from servo | — |
| Metering | Volumetric, ¼ tsp per dose stroke (±10%) | Whole slot, user pre-measured; ascending slot order | Dedicated load cell (±5%) |
| Cleaning | Canisters lift out, dishwasher-safe | Ring + base plate lift off, dishwasher-safe | Removable reservoir; tubing replaceable |

### 7.3 Dispensing Sequence

**FID:** Recipe engine queues `DISPENSE_FID(box_id, qty_quarter_tsp)` → the RV1106 `dispense` thread indexes the carousel (F1) → opens steam gate (F3) → N dose strokes of the canister measure wheel (F2, ¼ tsp each) → closes gate

**CID:** Recipe engine queues `DISPENSE_CID(slot_id)` → the `dispense` thread indexes the carousel (C1) so the slot sits over the base-plate aperture → contents free-fall through chute into pot → dwell + wiggle

**SLD:** Recipe engine queues `DISPENSE_SLD(channel, target_g)` → the `dispense` thread opens solenoid + starts pump → monitors reservoir weight loss on the NAU7802 at 10 Hz → stops pump + closes solenoid at target
8. Recipe engine logs dispensed amount and proceeds

---

## 8. Thermal Management

### 8.1 Heat Sources

| Source | Typical Heat Dissipation | Unit / Location |
|--------|--------------------------|-----------------|
| Electric heating unit | 100-400W (plate losses at ~65-75% efficiency, 1,300 W assumed); plate ceiling 200 °C at the centre sensor | CS, center-bottom |
| PSU LRS-75-24 (switch-mode) | 15-30W (at full load, ~85% efficient) | CS, rear compartment beside the CSC |
| CSC (STM32G0B1RE, relay coil, transceivers) | <1W | CS, rear compartment |
| CAN servo stirring motor | 12-48W (intermittent) | SU gantry |
| RV1106 (Luckfox Pico Zero) + Unified PCB v4.0 logic | ~1-2W | DU (passively cooled, above the fume hood) |
| Dispenser drivers (servos, pumps, 6 V buck) | 1-3W (intermittent) | DU |
| White LED ring | ≤ 5W (CAPTURE only) | DU underside |
| 2S Li-ion battery pack | <1W (charging); ~3W discharge when lifted | DU — cool zone by definition (< 45C), away from the heating unit and PSU |

### 8.2 Cooling Strategy

```
┌────────────────────────────────────────────────────────────┐
│                    Airflow Path (Side View)                 │
│                                                            │
│    Exhaust ◄──── Fan 2 (40mm, 12V)                        │
│    Grille        (rear-top, pulls hot air out)             │
│    (rear)                  ▲                               │
│                            │                               │
│                   ┌────────┴──────────┐                    │
│                   │  CSC + PSU (rear) │                    │
│                   │  (< 2 W + 15-30 W)│                    │
│                   └───────────────────┘                    │
│                            ▲                               │
│                   ┌────────┴──────────┐                    │
│                   │  Thermal barrier  │                    │
│                   │  (isolates plate  │                    │
│                   │   heat from PCBs) │                    │
│                   └───────────────────┘                    │
│                            ▲                               │
│                   ┌────────┴──────────┐                    │
│                   │  Heating plate    │                    │
│                   │  (stores heat,    │                    │
│                   │   unit-internal)  │                    │
│                   └───────────────────┘                    │
│                            ▲                               │
│    Intake ────► Fan 1 (40mm, 12V)                         │
│    Grille       (rear-bottom, pushes cool air in)          │
│    (rear)                                                  │
└────────────────────────────────────────────────────────────┘

Dual-fan push-pull configuration:
  Fan 1 (bottom): intake fresh air, cools PSU and electronics
  Fan 2 (top): exhaust hot air past the CSC and PSU
  Airflow path avoids pot/food zone (no contamination risk)
  The Dispensing Unit (Pico Zero ~1 W, battery) has no fan: it is
  passively cooled and sits above the fume hood, outside the CS airflow
```

### 8.3 Thermal Barriers

- **Silicone thermal pad** or **aluminum shield** between the heating unit and PSU compartment
- **Air gap** (minimum 10mm) between the heating unit and PSU
- **Operating ambient range:** 0-40C (indoor kitchen environment)
- **Maximum internal temp:** 70C at any PCB location (exhaust fan manages airflow)

### 8.4 Cooking Fume Exhaust

A separate exhaust system handles cooking fumes (steam, oil smoke, spice volatiles) from the pot zone. This is independent of the electronics cooling airflow to prevent food contamination of electronic components.

- **Exhaust fan:** 60mm PWM fan, mounted rear-top, draws fumes upward from pot zone
- **Filtration:** Dual-stage slide-out cartridge (stainless steel grease mesh + activated carbon)
- **Collection hood:** Integrated into gantry above pot, directs fumes toward exhaust duct
- **Intake:** Passive side/bottom vents provide makeup air via negative pressure

See [[05-Exhaust-Fume-Management|Exhaust & Fume Management]] for full specifications, filter design, and safety interlocks.

---

## 9. Ergonomics

### 9.1 Touchscreen

- **Angle:** Tilted 15-30 degrees from vertical (optimal viewing while standing at kitchen counter)
- **Height:** Screen center at ~200mm from countertop (within natural downward gaze)
- **Size:** 4.0" diagonal, 480x320. Panel: 4.0" ST7796S + FT6336U SPI module, glass 94.57 x 60.88 mm, active area 83.52 x 55.68 mm (landscape), module 108.0 x 60.88 x 14.8 mm including the 14-pin header. Bezel aperture 84 x 56 mm (+0.5 mm clearance), pocket 95 x 61 mm for the glass, 15 mm depth behind the bezel for the module and header. Recipe steps and controls fit; the pot camera view is an optional on-demand screen
- **Touch:** Capacitive (works with dry fingers, not with wet/gloved hands -- design assumes user dries hands)

### 9.2 Cleaning Design

| Component | Cleaning Method | Removable |
|-----------|----------------|-----------|
| Pot | Dishwasher or hand wash | Yes |
| Stirring paddle | Dishwasher or hand wash | Yes (twist-lock) |
| Stirring shaft | Wipe with damp cloth | Yes (pull-out) |
| FID canisters (×6) + carousel ring | Dishwasher or hand wash | Yes (lift out) |
| CID carousel ring (5 bins) + base plate + chute | Dishwasher or hand wash | Yes (lift off at home position) |
| SLD reservoirs (×2) | Dishwasher or hand wash | Yes (lift out) |
| SLD tubing (×2) | Hand wash / boil sterilize | Yes (disconnect) |
| Dispensing unit (whole) | Lift off; wipe underside, camera window and dock pads with a damp cloth | Yes (lift-off, no cable; seats one way) |
| Pot platform | Wipe with damp cloth | No (fixed, sealed surface) |
| Exterior surfaces | Wipe with damp cloth | No |
| Display | Wipe with soft cloth | No |
| Gantry area | Wipe with damp cloth | No (sealed against steam) |

### 9.3 Auto-Rinse Cycle (Future Feature)

Optional automated cleaning: fill pot with water, heat to 60C, stir for 5 minutes, drain. Requires drain valve (not included in prototype).

### 9.4 Cable Management

- One mains cord (IEC C14 with detachable cord) into the Cooking Surface; cable exit from rear-bottom
- One internal harness (J_SU: 24 V + CAN + shield, 5-way Micro-Fit 3.0) from the CSC to the Stirring Unit, routed inside the right pillar; no external cable between units
- No cable to the Dispensing Unit: charge and the isolated CAN bus cross the 8-contact magnetic pogo dock (J_DOCK) on the left pillar; the DU lifts straight off
- No user-facing cables during operation; dock contacts (gold pads on the DU underside, spring pins in the keyed recess) are wipe-clean and de-energised when the DU is lifted
- No external service port: the CSC's USB-C (DFU/CDC) and SWD are internal, bench use only

### 9.5 Non-Slip Feet

- 4x rubber feet at corners of base
- Diameter: 20mm each
- Height: 5mm (provides ventilation clearance under base)
- Material: Silicone or TPE (thermoplastic elastomer)

---

## 10. DFM Considerations

### 10.1 Prototype Phase

| Component | Fabrication Method | Notes |
|-----------|-------------------|-------|
| Enclosure (body) | Donor OneChef NX5300/00 body (CS) + 3D printed (FDM, PETG or ABS) pillars, SU gantry and DU shell | Air-fryer lid, its heater/fan and the touch panel removed from the donor (§1.5); iterative design, <$100 per print |
| Dock block + DU recess | Off-the-shelf 8-pin magnetic pogo pair in a 3D printed keyed recess | Spring pins on the left pillar top, gold pads on the DU underside |
| Enclosure (pot well) | Donor cooker pot well, as is | Already matched to the plate and the 6 L pot |
| Pot | OneChef 6 L non-stick inner pot, supplied with the donor cooker | Embedded magnet only for the optional reed backup |
| Gantry | Aluminum extrusion + 3D printed brackets | Standard 2020 or 2040 V-slot |
| FID canisters, FID/CID carousel rings, base plate, chutes, index gears | 3D printed (food-safe PETG; POM for gears) | Or silicone mold for flexibility |
| PCBs | 4-layer custom PCB (JLCPCB or similar) | 2 boards: Unified PCB v4.0 in the DU (Pico Zero slot, dispenser drivers, 2S battery, RV1106 CAN node, dock pads) and the Cooking Surface Controller in the CS (STM32G0B1RE, safety relay, fans, dock switch, both CAN ports); Luckfox Pico Zero is an off-the-shelf module |
| Wiring | Hand-soldered, JST/Dupont connectors | Label all connectors |

### 10.2 Production Phase

| Component | Fabrication Method | Notes |
|-----------|-------------------|-------|
| Enclosure (body) | Injection mold (PC/ABS blend) | Tooling cost ~$5,000-15,000, <$5/unit |
| Enclosure (pot well) | Stamped stainless steel | Press-formed, integrated with base |
| Pot | OEM-supplied 6 L non-stick aluminium inner pot (with the heating unit) | Magnet only for the optional reed backup |
| Gantry | Zinc die-cast or stamped steel | Integrated motor mount and fume hood (camera is on the DU) |
| FID/CID carousels, canisters, housings | Injection mold (food-grade PP) | Tooling ~$2,000 per shape |
| PCBs | SMT assembly (pick-and-place) | Panelized, automated testing |
| Assembly | Semi-automated line | Target 30 min per unit |

### 10.3 Assembly Sequence (Prototype)

**Cooking Surface (CS) first**

1. Strip the donor OneChef: remove the air-fryer lid, its heater and fan and the touch panel; keep the body, heating plate, controller cavity, 6 L pot and glass lid (§1.5). Route the heating unit's AC feed through the safety relay and its CAN cable to J_CAN_HEAT on the CSC (isolated bus shared by the RV1106, the STM32 and the unit)
2. Mount the LRS-75-24 PSU and the Cooking Surface Controller in the rear compartment beside the fans; wire IEC C14 inlet → fuse / EMI filter → heating unit AC (via the relay) and PSU; PSU 24 V → J_24V_IN (XT30) on the CSC
3. Fit the two exhaust fans and the filter cartridge slot (J_FAN), the front E-stop button and the optional pot reed (J_SAFE)
4. Fit the rear pillars: dock pogo block in the keyed recess on top of the left pillar, 8-way harness down the pillar to J_DOCK on the CSC; J_SU port in the right pillar, harness (J_CAN_STIR + J_STIR_PWR bundled) down the pillar to the CSC
5. Bench-flash the CSC (USB-C DFU or SWD); power-on test: E-stop, relay, fans; dock pads must stay dead until DOCK_SENSE_B is pulled low

**Stirring Unit (SU)**

6. Assemble the gantry bridge: CAN servo motor, vertical shaft with silicone gasket, paddle twist-lock, fume hood
7. Seat the bridge between the pillars and plug the motor into J_SU; verify stir commands over FDCAN2 and the fume hood alignment with the exhaust duct

**Dispensing Unit (DU)**

8. Install the Unified PCB v4.0 and the 2S pack (J_BAT) in the DU shell; fit the Luckfox Pico Zero in J_AP (no carrier board; four 3.0 mm mounting holes)
9. Mount the IMX415-98 camera and the white LED ring on the underside behind the sealed borosilicate window, centred over the pot position, looking straight down; connect the CSI FPC to the Pico Zero and the ring to J_LED
10. Mount the 4" display in the front-face pocket; connect SPI (LCD) and I2C3 (touch)
11. Install the dispensers: FID carousel + 3 servos + dosing station (rear), CID carousel + index servo + base plate (front), chutes through the underside; SLD reservoirs + pumps + solenoids + NAU7802 load cells + tubing to the underside nozzles; plug servo leads into J_DSB1-4 and pumps / solenoids into J_SLD; fit the buzzer
12. Fit the gold dock pads on the underside (left-rear, over the pillar) and close the DU shell

**Stack and dock alignment check**

13. Seat the DU on the pillars: confirm it seats one way only, the magnetic pogo block engages, DOCK_SENSE_A and DOCK_SENSE_B both read low, DOCK_24V appears at VSYS (≈ 23.5 V), CAN traffic (HB_AP, TELEMETRY) crosses the dock and the pack charges (CHRG)
14. Lift the DU: confirm the pads go dead (Q_DOCK off), the STM32 reports DU_UNDOCKED and holds safe, the UI shows UNIT_LIFTED on battery; re-dock and resume
15. Connect the power cord; full power-on test and calibration (camera coverage, load-cell tare, dispenser home)

---

## 11. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture & Wiring Diagrams]]
- [[03-Sensors-Acquisition|Sensors & Data Acquisition]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[05-Exhaust-Fume-Management|Exhaust & Fume Management]]
- [[01-Safety-Compliance|Safety & Compliance]]

#epicura #mechanical-design #enclosure #industrial-design

---

## 12. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-20 | Manas Pradhan | Replaced DS3225 servo references with 24V BLDC motor |
| 2.1 | 2026-11-04 | Manas Pradhan | Compute module changed to Luckfox Pico Zero (RV1106G3, no carrier, no heatsink); 10.1" display replaced by 4" 480x320 SPI LCD (cut-out to be confirmed); camera is SC3336 on the Pico Zero CSI FPC; assembly steps updated |
| 2.2 | 2026-11-04 | Manas Pradhan | Dispensers redesigned as servo carousels: FID (6 canisters, 3 servos) replaces P-ASD/ASD hoppers, CID (5 slots + cover, 1 servo) replaces two push-plate trays; layout, specs, sequence, cleaning, fabrication and assembly updated |
| 2.3 | 2026-11-04 | Manas Pradhan | Display cut-out fixed from the 4.0" ST7796S/FT6336U module drawing (active 83.52 x 55.68 mm); camera IMX415-98 |
| 2.4 | 2026-11-04 | Manas Pradhan | Assembly steps updated for the shared isolated CAN bus (RV1106 CAN node on the Unified PCB; UART2 service link) |
| 2.5 | 2026-11-04 | Manas Pradhan | Three-unit architecture: Cooking Surface (induction module, PSU, CSC, E-stop, fans, rear pillars), Stirring Unit (gantry, J_SU harness) and lift-off Dispensing Unit (Unified PCB v4.0, battery, LCD, camera + white LED ring on the underside, all three dispensers); magnetic pogo dock on the left pillar; height ≈ 350 mm (TBC), DU ≤ 4 kg; enclosure views, internal layout, thermal, cleaning, cable management, DFM and assembly sequence rewritten per unit |
| 2.6 | 2026-11-04 | Manas Pradhan | Induction surface replaced by a commercial electric heating unit of the rice-cooker class: pot is any flat-bottomed (aluminium, non-stick) pot with no ferromagnetic base, pot detection by the unit's spring-loaded centre sensor, CS layout/labels, thermal budget (plate losses at ~65-75 %), cooling diagram, thermal barriers, DFM pot rows and assembly steps updated |
| 2.7 | 2026-11-04 | Manas Pradhan | Reference unit fixed: Philips OneChef NX5300/00. The Cooking Surface is the modified donor body (§1.5: kept / removed / added), the air-fryer lid position is the Dispensing Unit seat, the pot is the donor's 6 L non-stick inner pot (~4.8 L usable; 3-4 L stainless/aluminium pot rows replaced), glass lid retained for manual use; CS envelope quoted from the conflicting retail figures; paddle non-stick-safe; pot and plate temperature ceiling 200 °C; DFM and assembly step 1 updated |
| 2.8 | 2026-11-04 | Manas Pradhan | Pot dimensions fixed: 9 in (228.6 mm) diameter, 150 mm height (6 L brim-full; 4.8 L max-fill line at ~120 mm); §2.2 and §5.1 pot rows updated, layout views say 23 cm pot |
