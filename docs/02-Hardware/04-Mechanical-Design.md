---
created: 2026-02-15
modified: 2026-11-05
version: 3.5
status: Draft
---

# Mechanical Design

## 1. Form Factor

### 1.1 Device Type
**Autonomous Countertop Kitchen Robot** - Stationary appliance designed for compact Indian kitchens

### 1.2 Dimensions
- **Width:** 500 mm
- **Depth:** 400 mm
- **Height:** ≈ 370 mm (to be confirmed; was 350 mm): Cooking Surface ≈ 110 mm + Stirring Unit gantry over the pot + Dispensing Unit ≤ 150 mm on top
- **Dispensing Unit envelope (2026-11-05):** Ø350 mm disc, ≤ 150 mm tall (≈ 110–130 mm expected) — the robot-vacuum form factor; concentric layout (camera hub, FID ring, CID ring, outer service ring with the SLD drawer tanks, pack and the arc-shaped Unified PCB). The disc overhangs the 25 cm pot by 5 cm per side and sits on the donor body's lid seat, which is Ø350 mm (confirmed 2026-11-05) — the DU disc matches the seat exactly, so the seat's locating lip, not the disc, provides the lateral key; keep the dock recess on the left pillar as the orientation key
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
| **Cooking Surface** | CS | Yes (IEC C14 inlet, fuse, EMI filter) | Modified Philips OneChef NX5300/00 body — the donor cooker's heating plate and controller (own AC stage + CAN); its air-fryer lid is removed and the Dispensing Unit seats in its place, its round inner pot and glass lid are set aside (§1.5) — 25 × 25 × 12 cm rounded-square non-stick pot (6 L max fill, §2.2) in an opened-out well — three Mean Well PSUs (LRS-75-24 #1 DU via the dock; LRS-75-24 #2 SU with a floating output; LRS-35-12 for the controller), Cooking Surface Controller PCB (CSC, STM32G0B1RE; powered by its own LRS-35-12), safety relays K_SAFE (heating unit AC inlet) and K_SU (SU PSU), E-stop button (front), 2× exhaust fans + filter cartridge (rear), two rear pillars that carry the Stirring Unit and the dock block |
| **Stirring Unit** | SU | No — fed 24 V by its own PSU (LRS-75-24 #2 in the CS rear, output floating) | Gantry bridge between the rear pillars over the pot: 24 V CAN servo stir motor, vertical shaft, paddle, fume hood. One port J_SU (Molex Micro-Fit 3.0, 5-way: 24V_SU, GND_SU, CAN_H, CAN_L, SHIELD; nothing on it references the CS ground) at the right pillar; harness runs inside the pillar to the CSC |
| **Dispensing Unit** | DU | No — battery is the primary supply | Ø350 mm disc, ≤ 150 mm tall. Unified PCB v5.3 (annular-sector board in the outer service ring: Luckfox Pico Zero RV1106 in J_AP, DU STM32G0B1RE, dispenser drivers, DU CAN node) and the 2S2P Li-ion pack, 4" LCD on the front face (tilted 15-30°), IMX415-98 camera + white LED ring in the hollow hub on the underside, centred over the pot and looking straight down behind a sealed borosilicate window, FID ring (inner) + CID ring (outer) dropping through the underside, SLD oil (200 mL) + water (500 mL) drawer tanks in the service ring with pumps in the body and check-valve nozzle cartridges through the underside, buzzer. Dock pads on the underside over the left pillar |

The DU seats on the rear pillars in one orientation only (keyed dock recess on the left pillar). The 8-contact magnetic pogo dock (J_DOCK) carries the 24 V charge input and the isolated CAN bus; lifting the DU opens the bus and the 24 V at the same instant. The user lifts the DU off between sessions to load ingredients and to clean individual coarse slots; on a mains outage the DU (the brain) keeps running on its battery and the session resumes when mains returns. The Ø350 disc sits on the donor's Ø350 mm lid seat (confirmed 2026-11-05); front-edge support of the DU over the pot well is to be confirmed in the CAD.

### 1.5 Donor Body Modification

The Cooking Surface is not a new enclosure: it is the body of the Philips OneChef NX5300/00 (6 L multicooker with a detachable air-fryer lid; reference unit in [[../05-Subsystems/01-Electric-Heating|Electric Heating]] §2.3), modified as follows.

| | Items |
|---|---|
| **Kept** | Cooker body (matte plastic, cool-touch handles), heating plate with its spring-loaded centre sensor, controller cavity (OEM control board with the CAN port) |
| **Removed** | Detachable air-fryer lid with its heater and fan, the touch panel (and its lid-detection switch); the donor's round 6 L inner pot and glass lid are set aside — neither fits the 25 cm rounded-square pot (§2.2) |
| **Added** | 25 × 25 cm rounded-square pot well (the donor's round well opened out, heating plate centred under it) with the 25 × 25 × 12 cm rounded-square non-stick pot and its matching glass lid (§2.2), Stirring Unit gantry mount on the rim, two rear pillars (left: dock block + keyed DU recess; right: J_SU port + harness), front E-stop button, 2× exhaust fans + filter cartridge, CSC + three-PSU bay in the rear compartment (two LRS-75-24 at 129 × 97 × 30 mm and one LRS-35-12 at 99 × 82 × 30 mm, stacked or side by side — placement TBC; the LRS-35-12 footprint replaces the IRM-20-12 reservation) |

The air-fryer lid's seat on the pot rim is where the Dispensing Unit sits in normal use; the pot's square glass lid goes on only when the DU is lifted for a manual cook.

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
| Material | Aluminium (pressed or cast), non-stick — a 25 cm rounded-square pot sourced as a commercial square casserole pot or custom pressed (fixed 2026-11-04; the donor OneChef's round 6 L inner pot is not used); any flat-bottomed pot that covers the heating plate and fits the well is acceptable, 304 stainless included |
| Interior Coating | Ceramic non-stick or PTFE (Teflon) |
| Capacity | ≈ 7.3 L brim-full (nominal, outer dimensions); 6 L usable at the max-fill line (fill ≤ 5/6, min/max marks inside) |
| Plan shape | Rounded square, 250 × 250 mm outer (fixed 2026-11-04), corner radius ≈ 40 mm (to be confirmed with the pot drawing); same area as a 28 cm round pot (~610 cm²). Flat base covers the ~220 mm heating plate with ~15 mm margin on all sides |
| Height | 120 mm (fixed 2026-11-04): ≈ 7.3 L brim-full as a straight rounded-square prism (610 cm² × 12 cm; walls and the base radius take it to ~7 L); the 6 L max-fill line sits at ~100 mm, leaving 20 mm of freeboard for stirring and splash |
| Weight (empty) | 1.0-1.5 kg |
| Handles | Two side handles on opposite flats (riveted, cool-touch) or integral rim lips, per the sourced pot; must clear the gantry opening |
| Lid | Square glass lid matching the pot (sourced with it; the donor's round lid does not fit), for manual / UNIT_LIFTED use; in normal use the Dispensing Unit is the lid |
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
│     │  │  DU: Ø350 mm disc, lifts off, no cable    │   │     │
│     │  │  service ring (Ø270-350): SLD drawer tanks│   │     │
│     │  │  (oil, water), pumps, 2S2P pack, arc PCB  │   │     │
│     │  │  CID ring (Ø190-270): 5 slots + cover, C1 │   │     │
│     │  │  FID ring (Ø100-170): 6 canisters, F1-F3  │   │     │
│     │  │           ┌───────────────────┐           │   │     │
│     │  │           │ Camera + white LED│           │   │     │
│     │  │           │ ring behind sealed│           │   │     │
│     │  │           │ window, underside,│           │   │     │
│     │  │           │ over pot centre   │           │   │     │
│     │  │           └───────────────────┘           │   │     │
│     │  │  DSB: PCA9685 + 6 V rail (Unified PCB v5.3│   │     │
│     │  │  arc board); 4" LCD on the front (15-30°) │   │     │
│     │  │  dock pads (underside, over left pillar)  │   │     │
│     │  └───────────────────────────────────────────┘   │     │
│     │  (pot well + 25 cm pot on the CS underneath)     │     │
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
│  │  DU (Ø350 mm disc) — lifts straight off, no cable      │  │  │
│  │  ┌────────────────────────────┐                        │  │  │ ≤150 mm
│  │  │  4" Touchscreen Display    │  SLD drawer tanks in   │  │  │
│  │  │  (DU front face, 15-30 deg)│  the service ring      │  │  │
│  │  └────────────────────────────┘                        │  │  │
│  │  underside: camera + LED ring window, FID/CID chutes,  │  │  │
│  │  SLD nozzles, dock pads over the left pillar           │  │  │
│  └────────────────────────────────────────────────────────┘  │ ─┼─
│ ┌──┐                                                   ┌──┐  │  │
│ │  │◄ dock block on this pillar top (J_DOCK pogo)      │  │  │  │ gantry
│ │L │  Stirring Unit (SU): gantry bridge between the    │R │  │  │ over
│ │  │  rear pillars, CAN servo motor + shaft + fume hood│  │  │  │ the pot
│ │  │        Pot Access Opening (insert/remove pot)     │  │  │  │
│ │  │                  [ 25 cm pot ]              J_SU ►│  │  │  │
│ └──┘                                                   └──┘  │ ─┼─
│  ┌────────────────────────────────────────────────────────┐  │  │
│  │  Cooking Surface (CS): heating unit, 3× Mean Well PSU, │  │  │ ≈110 mm
│  │  CSC (STM32), safety relays; fans + filter at the rear │  │  │
│  │  [E-STOP]                               [Status LED]   │  │  │
│  └────────────────────────────────────────────────────────┘  │ ─┴─
└──────────────────────────────────────────────────────────────┘
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
  Non-slip rubber feet (4x corner)              ≈ 370 mm overall (TBC)
```

### 3.3 Rear View

```
                         500 mm
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────┐  │
│  │  DU rear (Ø350 disc): service ring, no ports           │  │
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
    │  DU (Ø350 mm disc) — lifts straight off, no cable    │  │
    │ ┌─────┐ ┌────────┐ ┌───────────────┐ ┌────────┐      │  │
    │ │ 4"  │ │  CID   │ │ Unified PCB   │ │  FID   │      │  │ ≤150 mm
    │ │ LCD │ │  ring  │ │ v5.3 arc +    │ │  ring  │      │  │
    │ │tilt │ │(outer) │ │ Pico + 2S bat │ │(inner) │      │  │
    │ └─────┘ └───┬────┘ └───────────────┘ └───┬────┘ dock │  │
    │  SLD tanks  │chute ┌──────────┐ drop     │      pads │  │
    │  (ring)     ▼      │ Camera + │          ▼       ▼   │  │
    │  nozzles ▼         │ LED ring │ (sealed window)      │  │
    ├────────────────────┴────┬─────┴──────────────────────┤ ─┼─
    │  Stirring Unit (SU)     │ straight down    ┌───────┐ │  │
    │  gantry between the     │ 20-30 cm to the  │ CAN   │ │  │ gantry
    │  rear pillars           │ pot rim          │ servo │ │  │ over
    │          ┌──────────────┴───────────┐ shaft│ motor │ │  │ the pot
    │          │  Pot + Food Zone (25 cm) │◄─────┴───────┤ │  │
    │          │  (open top; paddle in)   │  rear pillar │ │  │
    │          │                          │  (harness +  │ │  │
    │          │                          │   dock block)│ │  │
    ├──────────┴──────────────────────────┴──────────────┴─┤ ─┼─
    │  Cooking Surface (CS)                                │  │
    │ [E-STOP] ┌──────────────────────┐ ┌───────┐ ┌──────┐ │  │ ≈110 mm
    │ (front)  │ Heating unit         │ │  CSC  │ │PSU ×3│ │  │
    │          │ (own AC stage + CAN) │ │(STM32)│ │24+12V│ │  │
    │          └──────────────────────┘ └───────┘ └──────┘ │  │
    │  ▓▓▓▓ IEC C14 + fuse ▓▓ Fan 1 ▓▓ Fan 2 ▓▓ filter ▓▓▓ │  │
    └──────────────────────────────────────────────────────┘ ─┴─
                                              ≈ 370 mm (TBC)
```

---

## 4. Internal Layout

### 4.1 Cooking Surface (Top Down)

The CS holds everything on mains: the electric heating unit (centre), the three Mean Well PSUs (LRS-75-24 #1 DU, LRS-75-24 #2 SU, LRS-35-12 CSC) and the Cooking Surface Controller (CSC) in the rear compartment beside the fans, the safety relays K_SAFE and K_SU, the E-stop button and the two rear pillars. The rear bay holds two 129 × 97 × 30 mm footprints (LRS-75-24 #1 and #2, stacked on standoffs or side by side) and one 99 × 82 × 30 mm footprint (LRS-35-12) — placement TBC against the donor's rear cavity; the LRS-35-12 footprint replaces the IRM-20-12 reservation of v3.3. PSU #2's 24 V output floats (24V_SU / GND_SU, −V left unbonded) and its AC input runs through K_SU on the inlet loom. The CSC takes no power from either 24 V PSU and nothing from the heating unit, which is not opened: its supply lead is a 2-wire 12 V XT30 lead (J_12V_IN) from the LRS-35-12, whose AC input is unswitched; LRS-75-24 #1 goes to the CSC only as the dock feed (J_DU_IN). K_SAFE's power relay sits on the heating unit's AC inlet loom; the CSC stays up on its own PSU when it opens.

```
┌──────────────────────────────────────────────────────────────┐
│                  REAR — Cooking Surface (CS)                 │
│                                                              │
│  ┌────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ Left   │ │ 3× PSU:    │ │ CSC PCB    │ │ 2x exhaust │     │
│  │ pillar │ │ 24V ×2,12V │ │ STM32G0B1  │ │ fans +     │     │
│  │ + dock │ │ IEC C14 +  │ │ 2 relays,  │ │ filter     │     │
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

The DU is a Ø350 mm disc, ≤ 150 mm tall (2026-11-05), packed like a robot vacuum: the camera in the hub, the two dispenser rings around it, and everything that needs no pot access in the outer service ring over the cooker body. It holds the brain and everything that touches ingredients: the Unified PCB v5.3 (annular-sector board) with the Luckfox Pico Zero and the DU STM32, the 2S2P Li-ion pack, the 4" LCD on its front face, the camera + white LED ring on its underside, and all three dispensers.

```
                      REAR — Dispensing Unit (DU, top-down, Ø350 mm)
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  SERVICE RING Ø270–350 (40 mm wide, over the cooker body, no pot access)   │
   │   • SLD water drawer tank 500 mL (≈ 90°) + SLD oil drawer tank 200 mL      │
   │     (≈ 35°), slide out sideways; pumps + check-valve nozzle cartridges     │
   │     under the bays; 6 Hall switches (tach ×2, present ×2, low ×2)          │
   │   • 2S2P 18650 pack, cells tangential (≈ 50°, J_BAT, PCM + NTC)            │
   │   • Unified PCB v5.3, annular sector ≈ 150° (Pico Zero J_AP, DU STM32,     │
   │     PCA9685 DSB, TB6612 pumps, INA219 ×2, TP5100, J_DOCK pads below)       │
   │   • buzzer; dock pads: left-rear underside over the pillar                 │
   │      ┌──────────────────────────────────────────────────────────┐          │
   │      │  CID RING Ø190–270: 5 slots + COVER (≈ 215 mL, 45 mm tall)  │       │
   │      │  C1 index servo, base-plate aperture at the pot rim → chute │       │
   │      │      ┌──────────────────────────────────────────────┐    │          │
   │      │      │  FID RING Ø100–170: 6 canisters Ø45 × 60 mm    │    │        │
   │      │      │  F1 index, F2 dose, F3 steam gate at the station│    │       │
   │      │      │         ┌──────────────────────┐              │    │         │
   │      │      │         │  HUB Ø60–80: camera + │              │    │        │
   │      │      │         │  white LED ring behind│              │    │        │
   │      │      │         │  the sealed window    │              │    │        │
   │      │      │         └──────────────────────┘              │    │         │
   │      │      └──────────────────────────────────────────────┘    │          │
   │      └──────────────────────────────────────────────────────────┘          │
   │   4" LCD + FT6336 touch on the front face                                  │
   └────────────────────────────────────────────────────────────────────────────┘
                                   FRONT
```

Height stack: underside layer ≈ 20 mm (window, chutes, nozzle cartridges, dock pads) → dispenser layer ≈ 70 mm (FID canisters 60 mm, CID bins 45 mm, rings and bearings) under a lift-off lid → service ring ≈ 85 mm (tanks 50 mm with the PCB and pack in a 35 mm layer above them). Ring order (FID inner, CID outer) is confirmed (2026-11-05); the PCB outline is to be confirmed in the CAD; the Ø350 disc replaces the 500 × 400 mm DU of earlier revisions because the Ø230 CID and Ø170 FID rings side by side do not fit inside it.

### 4.3 Stirring Unit

The SU is the gantry bridge between the rear pillars: the 24 V CAN servo stir motor, the vertical shaft with its silicone gasket, the twist-lock paddle and the fume hood that feeds the CS exhaust duct. It has no PCB; its only connection is J_SU at the right pillar (24V_SU + GND_SU + isolated CAN + shield, all referenced to the SU's own floating supply), wired inside the pillar to J_CAN_STIR + J_STIR_PWR on the CSC's SU island. The SU's 24 V comes from its own LRS-75-24 #2 in the CS rear, not from the CS rail, and GND_SU is never bonded to the CS ground.

---

## 5. Pot Design

### 5.1 Specifications

| Parameter | Value |
|-----------|-------|
| Body Material | Aluminium, non-stick (25 cm rounded-square pot, commercial square casserole or custom pressed; alloy per the pot drawing) |
| Base | Flat aluminium base in contact with the heating plate (presses the spring-loaded centre sensor) |
| Interior Coating | Ceramic non-stick (PFOA-free) or PTFE |
| Capacity | ≈ 7.3 L brim-full (nominal); 6 L usable at the max-fill line (fill ≤ 5/6) |
| Outer Plan | 250 × 250 mm rounded square, corner radius ≈ 40 mm (fixed 2026-11-04; radius to be confirmed) |
| Inner Plan | ~244 × 244 mm flat-to-flat (3 mm walls; pot drawing governs) |
| Height | 120 mm (fixed 2026-11-04; ≈ 7.3 L brim-full, 6 L max-fill line at ~100 mm) |
| Wall Thickness | 3 mm (aluminum body) |
| Base Thickness | 3-5 mm aluminium (flat for plate contact) |
| Weight (empty) | 1.0-1.5 kg |
| Max Operating Temp | 200C (heating unit ceiling; non-stick coating) |

### 5.2 Detection Mechanism

- Pot detection is handled internally by the electric heating unit
- The pot presses the unit's spring-loaded centre sensor; the unit reports `pot_detected` in HEAT_STATUS
- No external reed switch or magnet required (the CSC reed switch remains an optional backup)
- Interlock: the unit will not heat without pot detected (internal safety)

### 5.3 Handle Design

- Handles per the sourced pot (two side handles on opposite flats or integral rim lips); if folding side handles: stow flat against pot body, flip out for lifting
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

The camera and LED ring are no longer on the gantry: they sit on the underside of the Dispensing Unit, centred over the pot (§3.4). The gantry carries only the stir motor, shaft, paddle and fume hood, and is fed by the single J_SU harness from the Cooking Surface (its own LRS-75-24 #2 behind the CSC's SU island).

### 6.2 Arm Specifications

| Parameter | Value |
|-----------|-------|
| Actuator | 24V BLDC motor with integrated ESC (30-50 kg-cm torque) |
| Rotation | 360 degrees continuous (modified servo or stepper alternative) |
| Speed Range | 10-60 RPM (adjustable via recipe) |
| Shaft Material | 304 stainless steel, 8mm diameter |
| Shaft Length | 145 mm overall: 30 mm above the gantry seal plane (bearing + coupler) + 115 mm below it (40 mm rim gap + 75 mm into the pot); derived from the stack below |
| Depth Adjustment | Fixed depth (set during assembly for the 120 mm pot; set-screw range ±10 mm) |
| Paddle | Food-grade silicone or nylon, PTFE-tipped edge — non-stick-safe, no metal touches the coated pot; removable twist-lock |
| Seal | Silicone gasket around shaft penetration (IPX5 rated) |
| Cleaning | Shaft and paddle removable, dishwasher-safe |

#### 6.2.1 Shaft and Paddle Vertical Stack

Derived from the 250 × 250 × 120 mm rounded-square pot (§5.1). Heights are measured from the pot bottom (inside); adjust the gantry gap if the donor-body rim height moves.

| Level | Height above pot bottom | Note |
|-------|------------------------|------|
| Gantry seal plane (bearing + silicone gasket) | 160 mm | 40 mm above the rim: clears the folded pot handles and the fume-hood lip, keeps the gasket 60 mm above the max-fill line |
| Pot rim | 120 mm | Pot height |
| Max-fill line (6 L) | ~100 mm | Shaft is wetted below this level |
| Paddle hub (twist-lock) centre | 45 mm | End of the drive shaft; hub body 45 mm → 25 mm |
| Paddle blade lower edge | 3 mm | PTFE-tipped edge sweeps the non-stick bottom without touching it |
| Paddle blade outer edge | 3 mm from the flat walls | Blade radius ~119 mm on the ~244 mm inner flat-to-flat; the four rounded corners (R ≈ 40 mm) lie outside the swept circle and are reached only by the blade's wake |

Shaft: 304 stainless, 8 mm, **145 mm** overall = 30 mm above the seal plane (bearing seat + coupler engagement) + 115 mm below it (160 − 45). The 25 mm from the rim to the hood underside is the fume-collection gap. The DU camera window sits a further 200–300 mm above the rim (§3.4) and is unaffected.

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
                    │  Dispensing Layout (Top View, Ø350)   │
                    │                                       │
                    │  Service ring (Ø270–350):             │
                    │   SLD-WATER tank ══► pump ══► nozzle  │
                    │   SLD-OIL tank   ══► pump ══► nozzle  │
                    │   (drawer tanks, pumps in the body,   │
                    │    check valves at the nozzles)       │
                    │                                       │
                    │  CID ring (Ø190–270, over the rim):   │
                    │       ┌───────────────┐               │
                    │     ┌─┤Slot3  │Slot2  ├─┐  C1 index   │
                    │     │Slot4 ──┼── Slot1  │  (4:3 gear) │
                    │     └─┤Slot5  │COVER  ├─┘             │
                    │       └───────┬───────┘               │
                    │        aperture ▼ 45° chute inward    │
                    │                                       │
                    │  FID ring (Ø100–170, inside the pot): │
                    │       ┌───────────────┐               │
                    │     ┌─┤ Box4  │ Box3  ├─┐             │
                    │     │ Box5 ──┼── Box2   │  F1 index   │
                    │     └─┤ Box6  │ Box1  ├─┘  (5:3 gear) │
                    │       └───────┬───────┘               │
                    │      station: F2 dose, F3 gate        │
                    │            ▼ straight drop (¼ tsp)    │
                    │       hub: camera + LED ring          │
                    └───────────────────────────────────────┘
```

All three dispensers travel with the Dispensing Unit. The FID ring (inner) drops its doses straight into the pot, the CID ring (outer) through a short chute at the rim; the SLD oil and water drawer tanks sit in the service ring with their pumps in the body and lift off with the DU (or slide out individually for refilling). Nothing dispensing-related stays on the Cooking Surface: the servos and pumps are driven from the Unified PCB v5.3 (switched 6 V rail) by the DU STM32 Dispense task under commands from the RV1106 `dispense` thread.

### 7.2 Subsystem Specifications

| Parameter | FID (Fine / Seasonings) | CID (Coarse) | SLD (Liquids) |
|-----------|------------------------|-------------|--------------|
| Count | 6 canisters on one carousel | 5 slots + cover sector on one carousel | 2 channels (oil + water) |
| Capacity | 60 mL each | ~215 mL each (~1.1 L total) | 200 mL (oil), 500 mL (water) drawer tanks |
| Material | Food-grade PP, integral ¼ tsp measure wheel | Food-grade PP lift-off ring on fixed base plate | PP drawer tanks with self-sealing poppet, float + magnet; short silicone pump line; PP/silicone check-valve nozzle cartridge |
| Actuator | 3 servos (F1 index, F2 dose, F3 steam gate) on the DSB | 1 servo (C1 index) on the DSB | 6 V peristaltic pump (oil) + 6 V diaphragm pump (water), Hall tach each; spring check valve per nozzle (no solenoid) |
| Carousel | Ø100–170 mm ring (inner), 60° bays, 5:3 gear-up from servo | Ø190–270 mm ring (outer), 60° sectors, 4:3 gear-up from servo | — (tanks in the Ø270–350 service ring) |
| Metering | Volumetric, ¼ tsp per dose stroke (±10%) | Whole slot, user pre-measured; ascending slot order | Open loop, pump tach pulses × calibrated mL/pulse (±5 %); float low-level + tank-present Hall switches |
| Cleaning | Canisters lift out, dishwasher-safe | Ring + base plate lift off, dishwasher-safe | Drawer tanks and nozzle cartridges dishwasher-safe; pump line is a service part |

### 7.3 Dispensing Sequence

**FID:** Recipe engine queues `DISPENSE_FID(box_id, qty_quarter_tsp)` → the RV1106 `dispense` thread sends it over the host link and the DU STM32 Dispense task indexes the carousel (F1) → opens steam gate (F3) → N dose strokes of the canister measure wheel (F2, ¼ tsp each) → closes gate

**CID:** Recipe engine queues `DISPENSE_CID(slot_id)` → the DU STM32 Dispense task indexes the carousel (C1) so the slot sits over the base-plate aperture → contents free-fall through chute into pot → dwell + wiggle

**SLD:** Recipe engine queues `DISPENSE_SLD(channel, target_ml)` → the DU STM32 Dispense task checks the tank (present, not low), primes if the tank was re-seated, starts the pump and counts tach pulses → stops at target_pulses; the nozzle check valve closes by itself
8. Recipe engine logs dispensed amount and proceeds

---

## 8. Thermal Management

### 8.1 Heat Sources

| Source | Typical Heat Dissipation | Unit / Location |
|--------|--------------------------|-----------------|
| Electric heating unit | 100-400W (plate losses at ~65-75% efficiency, 1,300 W assumed); plate ceiling 200 °C at the centre sensor | CS, center-bottom |
| PSU LRS-75-24 ×2 (switch-mode; #1 DU, #2 SU) | 15-30W total (at full load, ~85% efficient; #2 is loaded only while stirring) | CS, rear compartment beside the CSC |
| PSU LRS-35-12 (switch-mode; CSC, fans, relay coils) | ~3-5W (≈ 17 W load, ~86% efficient) | CS, rear compartment beside the CSC |
| CSC (STM32G0B1RE, 5 V buck, LDO, two relay coils, transceivers, fan MOSFETs; fed from the LRS-35-12) | ~3.5W | CS, rear compartment |
| CAN servo stirring motor | 12-48W (intermittent) | SU gantry |
| RV1106 (Luckfox Pico Zero) + Unified PCB v5.0 logic (incl. DU STM32) | ~1-2W | DU (passively cooled, above the fume hood) |
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
| SLD drawer tanks (×2) | Dishwasher (top rack) or hand wash; keep the vent hole and bottom outlet clear | Yes (slide out of the service ring, no lifting) |
| SLD nozzle cartridges (×2, with check valve) | Dishwasher or hand wash | Yes (snap out of the underside) |
| SLD pump lines (×2) | Rinse cycle (§9.3 of Ingredient Dispensing); replace yearly | No (service part) |
| Dispensing unit (whole) | Lift off; wipe underside, camera window and dock pads with a damp cloth | Yes (lift-off, no cable; seats one way) |
| Pot platform | Wipe with damp cloth | No (fixed, sealed surface) |
| Exterior surfaces | Wipe with damp cloth | No |
| Display | Wipe with soft cloth | No |
| Gantry area | Wipe with damp cloth | No (sealed against steam) |

### 9.3 Auto-Rinse Cycle (Future Feature)

Optional automated cleaning: fill pot with water, heat to 60C, stir for 5 minutes, drain. Requires drain valve (not included in prototype).

### 9.4 Cable Management

- One mains cord (IEC C14 with detachable cord) into the Cooking Surface; cable exit from rear-bottom
- One internal harness (J_SU: 24V_SU + GND_SU + isolated CAN + shield, 5-way Micro-Fit 3.0, floating with respect to the CS ground) from the CSC to the Stirring Unit, routed inside the right pillar; no external cable between units
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
| Enclosure (pot well) | Donor cooker pot well opened out to the 25 × 25 cm rounded-square footprint (3D printed collar / sheet insert) | The donor's round well does not take the square pot; the heating plate stays centred under the flat base |
| Pot | 25 × 25 × 12 cm rounded-square non-stick aluminium pot + matching glass lid, sourced (commercial square casserole) or custom pressed | Embedded magnet only for the optional reed backup |
| Gantry | Aluminum extrusion + 3D printed brackets | Standard 2020 or 2040 V-slot |
| FID canisters, FID/CID carousel rings, base plate, chutes, index gears | 3D printed (food-safe PETG; POM for gears) | Or silicone mold for flexibility |
| PCBs | 4-layer custom PCB (JLCPCB or similar) | 2 boards: Unified PCB v5.0 in the DU (Pico Zero slot, DU STM32G0B1RE, dispenser drivers, 2S battery, DU CAN node, dock pads) and the Cooking Surface Controller in the CS (STM32G0B1RE, two safety relays, fans, dock switch, both CAN ports isolated, floating SU supply pass-through, powered from its own LRS-35-12); Luckfox Pico Zero is an off-the-shelf module |
| Wiring | Hand-soldered, JST/Dupont connectors | Label all connectors |

### 10.2 Production Phase

| Component | Fabrication Method | Notes |
|-----------|-------------------|-------|
| Enclosure (body) | Injection mold (PC/ABS blend) | Tooling cost ~$5,000-15,000, <$5/unit |
| Enclosure (pot well) | Stamped stainless steel, 25 cm rounded square | Press-formed, integrated with base |
| Pot | Custom pressed 25 × 25 × 12 cm rounded-square non-stick aluminium pot + glass lid | Magnet only for the optional reed backup |
| Gantry | Zinc die-cast or stamped steel | Integrated motor mount and fume hood (camera is on the DU) |
| FID/CID carousels, canisters, housings | Injection mold (food-grade PP) | Tooling ~$2,000 per shape |
| PCBs | SMT assembly (pick-and-place) | Panelized, automated testing |
| Assembly | Semi-automated line | Target 30 min per unit |

### 10.3 Assembly Sequence (Prototype)

**Cooking Surface (CS) first**

1. Strip the donor OneChef: remove the air-fryer lid, its heater and fan and the touch panel; keep the body, heating plate and controller cavity (§1.5); set the round inner pot and glass lid aside and open the pot well out to the 25 cm rounded-square footprint. Feed the heating unit's AC from the inlet through K_SAFE's power relay on its inlet loom (NC: de-energised = unit disconnected); do not open the unit or tap anything from it — bring only its CAN cable to J_CAN_HEAT on the CSC (isolated bus shared by the RV1106, the STM32 and the unit)
2. Mount the three PSUs (two LRS-75-24, one LRS-35-12) and the Cooking Surface Controller in the rear compartment beside the fans; wire IEC C14 inlet → fuse / EMI filter → K_SAFE relay → heating unit (step 1), LRS-75-24 #1, LRS-75-24 #2 (via K_SU) and the LRS-35-12 (unswitched); LRS-35-12 12 V → J_12V_IN (XT30) on the CSC (its −V is the CSC ground); PSU #1 24 V → J_DU_IN (XT30) on the CSC (DU dock feed only, −V bonded to the CSC ground there); PSU #2 24 V → J_SU_IN (XT30) with its −V left unbonded (floating GND_SU)
3. Fit the two exhaust fans and the filter cartridge slot (J_FAN), the front E-stop button and the optional pot reed (J_SAFE)
4. Fit the rear pillars: dock pogo block in the keyed recess on top of the left pillar, 8-way harness down the pillar to J_DOCK on the CSC; J_SU port in the right pillar, harness (J_CAN_STIR + J_STIR_PWR bundled: 24V_SU, GND_SU, CAN_H, CAN_L, SHIELD) down the pillar to the CSC's SU island
5. Bench-flash the CSC (USB-C DFU or SWD, with J_12V_IN disconnected); power-on test: E-stop, both relays (K_SAFE cuts the heating unit's AC inlet while the CSC stays up on its own PSU, K_SU), fans; dock pads must stay dead until DOCK_SENSE_B is pulled low

**Stirring Unit (SU)**

6. Assemble the gantry bridge: CAN servo motor, vertical shaft with silicone gasket, paddle twist-lock, fume hood
7. Seat the bridge between the pillars and plug the motor into J_SU; check there is no continuity between GND_SU and the CS ground, then verify that K_SU brings the SU PSU up, stir commands over FDCAN2 and the fume hood alignment with the exhaust duct

**Dispensing Unit (DU)**

8. Install the Unified PCB v5.3 (annular sector) and the 2S2P pack (J_BAT, cells tangential) in the DU service ring; fit the Luckfox Pico Zero in J_AP (no carrier board; four 3.0 mm mounting holes)
9. Mount the IMX415-98 camera and the white LED ring on the underside behind the sealed borosilicate window, centred over the pot position, looking straight down; connect the CSI FPC to the Pico Zero and the ring to J_LED
10. Mount the 4" display in the front-face pocket; connect SPI (LCD) and I2C3 (touch)
11. Install the dispensers: FID ring + 3 servos + dosing station (inner), CID ring + index servo + base plate (outer), chute through the underside; SLD tank bays with their Hall switches, pumps with tach magnets, pump lines and check-valve nozzle cartridges through the underside; plug servo leads into J_DSB1-4 and the pumps + six Hall switches into J_SLD (12-pin); fit the buzzer; slide the two drawer tanks in
12. Fit the gold dock pads on the underside (left-rear, over the pillar) and close the DU shell

**Stack and dock alignment check**

13. Seat the DU on the pillars: confirm it seats one way only, the magnetic pogo block engages, DOCK_SENSE_A and DOCK_SENSE_B both read low, DOCK_24V appears at VSYS (≈ 23.5 V), CAN traffic (HB_AP, TELEMETRY) crosses the dock and the pack charges (CHRG)
14. Lift the DU: confirm the pads go dead (Q_DOCK off), the STM32 reports DU_UNDOCKED and holds safe, the UI shows UNIT_LIFTED on battery; re-dock and resume
15. Connect the power cord; full power-on test and calibration (camera coverage, SLD pump calibration and prime, dispenser home)

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
| 2.9 | 2026-11-04 | Manas Pradhan | Stirrer shaft re-sized for the 150 mm pot: §6.2 shaft length 150 → 175 mm overall (145 mm below the gantry seal plane), new §6.2.1 vertical stack (seal plane 40 mm above the rim, paddle hub at 45 mm, blade edge 3 mm off the bottom and wall) |
| 3.0 | 2026-11-04 | Manas Pradhan | Pot changed from the donor's round 6 L inner pot to a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot (corner radius ≈ 40 mm TBC; ≈ 7.3 L brim, 6 L max-fill line at ~100 mm; same area as a 28 cm round pot): §1.5 donor pot and lid set aside, pot well opened out to the square footprint, matching square glass lid; §2.2 / §5.1 rows, layout views (25 cm pot), §6.2 shaft 175 → 145 mm overall (115 mm below the seal plane at 160 mm), §6.2.1 stack (rim 120 mm, max-fill 90 mm, blade radius ~119 mm, corners outside the swept circle), DFM pot-well / pot rows and assembly step 1 updated |
| 3.1 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: Unified PCB v5.0 carries a DU STM32G0B1RE (dispensing, LED ring, buzzer, battery/dock monitor, DU CAN node) beside the Pico Zero; MCP2518FD gone; unit table, DU layout, dispensing sequences, thermal and DFM rows, assembly step 8 updated |
| 3.2 | 2026-11-04 | Manas Pradhan | Stirring Unit on its own PSU and both CSC CAN ports isolated (CSC v1.3): second Mean Well LRS-75-24 (#2, floating 24V_SU / GND_SU, AC input through K_SU) in the CS rear bay (one extra 129 × 97 × 30 mm footprint, placement TBC); J_SU pinout 24V_SU, GND_SU, CAN_H, CAN_L, SHIELD with nothing referenced to the CS ground; unit table, §1.5 added list, CS views and layout, §4.3, thermal rows, cable management, DFM row and assembly steps 2, 4, 5, 7 updated |
| 3.3 | 2026-11-05 | Manas Pradhan | CSC, fans and relay coils powered from the heating unit's control-board 12 V SELV rail (CSC v1.5, J_HU_PWR): rear-bay text (supply lead from the donor's control board, IRM-20-12 fallback footprint reserved), K_SAFE on the heating element loom instead of the unit's inlet, PSU #1 → J_DU_IN as the dock feed only; unit table, §1.5 added list, thermal rows (CSC ~3.5 W), DFM PCB row and assembly steps 1, 2, 5 updated |
| 3.5 | 2026-11-05 | Manas Pradhan | Dispensing Unit re-packaged as a Ø350 mm disc, ≤ 150 mm tall (robot-vacuum form factor) with a concentric layout — camera hub, FID ring Ø100–170 (inner), CID ring Ø190–270 (outer, ≈ 215 mL bins), service ring Ø270–350 with the SLD drawer tanks, pumps, 2S2P pack (cells tangential) and an annular-sector Unified PCB v5.3; overall height ≈ 350 → ≈ 370 mm (TBC), donor lid seat Ø350 mm confirmed the same day. SLD on the robot-mop pattern: drawer tanks (200 mL oil / 500 mL water, self-sealing poppet, float + presence magnets), pumps in the body (peristaltic oil, diaphragm water, Hall tachs), check-valve nozzle cartridges; solenoids and load cells gone. §1.2, §1.4, §3.1–3.4, §4.2, §7, §9.2 and assembly steps 8, 11, 15 updated |
| 3.4 | 2026-11-05 | Manas Pradhan | CSC on a dedicated Mean Well LRS-35-12 (CSC v1.6, reversing 3.3): the rear bay holds three PSUs (two LRS-75-24 at 129 × 97 × 30 mm, one LRS-35-12 at 99 × 82 × 30 mm, placement TBC) and the IRM-20-12 reservation is dropped; the CSC's supply lead is J_12V_IN from the LRS-35-12, nothing is tapped from the heating unit (not opened) and K_SAFE returns to the unit's AC inlet loom; unit table, §1.5 added list, CS views and rear layout, §4.3, thermal rows (+ LRS-35-12 ~3-5 W), DFM PCB row and assembly steps 1, 2, 5 updated |
