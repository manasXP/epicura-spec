---
created: 2026-02-15
modified: 2026-11-04
version: 6.1
status: Draft
---

# Electric Heating System

## 1. Overview

The electric heating system is the primary thermal element of Epicura. Epicura uses a **commercial electric heating unit of the premium rice-cooker class** — a self-contained module with a resistive heating plate, a spring-loaded centre temperature sensor pressed by the pot, its own power stage (relay or triac on the mains side) and its own controller. The unit exposes a **CAN bus interface** for external control and runs its **own temperature loop**: the RV1106 application processor sends a temperature setpoint (or, for sear stages, a power level) on the shared isolated CAN bus and reads the unit's measured temperature, status and faults back, while the STM32 keeps an independent off-switch. Epicura has no temperature sensor of its own.

This replaced the commercial induction surface on 2026-11-04. Because the heating unit sits on the same CAN bus with the same HEAT_* message set, the change is confined to the heater itself and to the thermal figures in this document: neither the Cooking Surface Controller nor the Unified PCB changes, and neither `epicurad` nor the STM32 firmware gains or loses a function.

> [!note] Reference unit and assumed rated power
> The heating unit is specified against the **Philips OneChef NX5300/00** (§2.3): its body becomes the Cooking Surface, modified to carry the stirring gantry, and its air-fryer lid is replaced by the Dispensing Unit. Its 2,280 W nameplate covers the base plate **and** the air-fryer lid heater together; the base plate alone is expected at 1,000–1,300 W (Philips' lid-less all-in-one cookers are rated ~1,090 W). This document keeps **1,300 W** as the planning figure (upper bound) until the OEM unit is characterised; every wattage derived from it is marked as such.

### 1.1 Advantages of a Commercial Heating Unit

- **No custom mains power electronics:** The heater's relay/triac stage, thermal fuse and mains wiring are inside a pre-certified unit
- **Pre-certified safety:** The unit includes pot detection (centre sensor), over-temperature cut-off and a thermal fuse
- **CAN bus control:** Digital interface; clean separation between power and logic
- **Built-in temperature control:** The unit's own PID on its own plate sensor removes any thermometer and control loop from Epicura
- **Faster prototyping:** No power-stage design or thermal-cutoff qualification
- **Reliability:** Production-tested rice-cooker heating plates run for years in household use

### 1.2 Electric Heating Plate vs. Induction

The induction surface it replaces was faster and more efficient; the trade-offs accepted with the heating plate are:

| Property | Heating plate (chosen) | Induction (dropped) |
|----------|------------------------|---------------------|
| Pot material | Any flat-bottomed pot; the rice-cooker inner pot (aluminium, non-stick) fits directly | Ferromagnetic only |
| Heat path | Plate → pot bottom by contact; plate stores heat, so response is slower and there is thermal lag after a power cut | Direct in the pot base |
| Preheat ramp | ~2–4 °C/s on the plate | ~20 °C/s |
| Efficiency | ~65–75 % (contact losses, plate mass) | 85–90 % |
| Power | 1,300 W (assumed) | 1,800 W |
| Pot detection | Spring-loaded centre sensor | Impedance sensing |
| EMI / EMF | None beyond mains switching | 20–100 kHz field, ICNIRP assessment |
| Precision | Setpoints in 1 °C steps and power 0–100 % via CAN, same as before | Same |

The recipe schema's temperature targets and hold times are re-calibrated against the plate during recipe development (§5.4); the CAN contract and the controller firmware are not affected.

## 2. Heating Unit

### 2.1 Commercial Electric Heating Unit

The heating unit is a self-contained module that includes:

- AC power inlet, internal fuse and EMI filter
- Resistive heating plate (cast aluminium, typ. 180–200 mm) with the mains power stage (relay or zero-cross triac) inside the unit
- Spring-loaded centre temperature sensor (NTC) that touches the pot bottom and doubles as pot-presence detection; a second sensor on the plate or heater body
- Built-in safety circuits (thermal fuse, over-temperature cut-off, pot-absent lockout)
- Closed-loop temperature controller
- Exposed CAN bus port for external control (temperature setpoint, power level, on/off, status)

The unit lives in the Cooking Surface (CS) base and shares one isolated CAN bus with the RV1106 in the Dispensing Unit (which sends setpoints and reads status) and the STM32 on the Cooking Surface Controller (which can only force it off). All mains power electronics are handled internally by the unit — neither of Epicura's control boards (the CSC or the Unified PCB) ever touches mains voltage.

Unit selection requirements:
- Temperature mode: accepts a setpoint in °C and regulates on its own centre sensor; reports the measured temperature at ≥ 10 Hz
- Power mode: accepts a 0–100 % power level (time-proportional on the plate) for stages that specify power rather than temperature (sear, boil)
- Command watchdog: drops to zero power if no HEAT_SET_TEMP / HEAT_SET_POWER refresh arrives for 1 s, so a stalled application processor cannot leave the heater on
- Pot detection: `pot_detected` in HEAT_STATUS from the centre sensor; no heating while the pot is absent
- Plate temperature range: 80–200 °C at the centre sensor, as on the reference unit; sear and tadka stages are written for ≤ 200 °C (the inner pot is non-stick, so no higher target is wanted)
- CAN port: the OEM unit ships with a control board that exposes the HEAT_* set on CAN (confirmed 2026-11-04); the retail OneChef's touch-panel board is not used. No Epicura controller drives the plate

### 2.3 Reference Unit: Philips OneChef NX5300/00

The OneChef is a 6 L multicooker with a detachable air-fryer lid, sold in India since 2026. Epicura takes the cooker body, heating plate, controller, inner pot and glass lid; the air-fryer lid (its heater and fan) is dropped and the Dispensing Unit docks in its place, and the body is modified to carry the Stirring Unit gantry and the dock pillar. Published figures (retail listings disagree on size and weight; the OEM drawing governs):

| Parameter | Reference unit | Used in Epicura |
|-----------|----------------|-----------------|
| Nameplate power | 2,280 W (base plate + air-fryer lid), 230 V | Base plate only: 1,000–1,300 W expected, **1,300 W planning figure** |
| Heating | "AmbiHeat": resistive plate under the pot with temperature sensors under the pot; stage-wise temperature profiles in firmware | Plate + centre sensor; the profile logic moves to the recipe engine, the unit's controller keeps the PID |
| Temperature range | 80–200 °C | 60–200 °C requested (keep-warm at 60–70 °C), sear ≤ 200 °C |
| Inner pot | 6 L, non-stick, min/max marks (fill ≤ 4/5 → ~4.8 L usable), dishwasher safe | Epicura's pot; replaces the 3–4 L stainless pot |
| Lid | Glass lid (plus the air-fryer lid, dropped) | Glass lid kept for the UNIT_LIFTED / manual-cook case; the DU is the lid in normal use |
| Body | Matte plastic, 38.5 × 35.7 × 28 cm / 6.2 kg (Croma, with lid) or 33 × 33 × 33 cm / 4.6 kg (Reliance Digital) | Cooking Surface envelope; stirrer and dock added |
| Sensing / safety | Under-pot temperature sensors, lid detection ("No Lid" in air-fry mode), auto shut-off, cool-touch handles | Centre sensor → `surface_temp`, plate sensor → `element_temp`, `pot_detected`; lid detection not used |
| Interface | Touch panel, 33 presets; HomeID app for recipes only, no device connectivity | OEM control board with CAN port (ships with the unit) |
| Pressure cooking | No (glass lid) | No |
| Price | ₹19,995 MRP (₹18,995 street) | Donor unit for prototypes; OEM pricing for production |

### 2.2 System Block Diagram

```
AC Mains (220-240V 50Hz)
        │
        ▼
┌──────────────────────────────────────────────────┐
│         Electric Heating Unit (rice-cooker class) │
│                                                    │
│  ┌────────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ AC Input   │  │ Power     │  │ Heating      │ │
│  │ Fuse, EMI  │─►│ Stage     │─►│ Plate        │─┼──► Heats Pot (contact)
│  │ Filter     │  │ (relay /  │  │ (resistive)  │ │
│  └────────────┘  │  triac)   │  └──────────────┘ │
│                  └─────┬─────┘                     │
│                  ┌─────▼─────┐                     │
│                  │ Onboard   │◄── centre sensor    │
│                  │ Controller│    (NTC, pressed    │
│                  │ + PID     │     by the pot)     │
│                  │ + Safety  │◄── plate / element  │
│                  └─────┬─────┘    sensor           │
│                        │                           │
│                   CAN Bus Port                     │
└────────────────────┬───────────────────────────────┘
                     │
              CAN_H, CAN_L, GND_ISO, 5V_ISO  (isolated bus, 500 kbps)
                     │  J_CAN_HEAT on the CSC (R_TERM1 120 Ω)
       ┌─────────────┴──────────────┐
       ▼                            ▼  J_DOCK pins 3–6 (pogo dock, stub ≤ 30 cm)
┌──────────────┐             ┌──────────────┐
│  ISO1050DUB  │ ◄── 5 kV ──►│  ISO1050DUB  │   #1 on the CSC (Cooking Surface),
│  #1 (STM32)  │  isolation  │  #2 (RV1106) │   #2 on the Unified PCB (Dispensing Unit);
└──────┬───────┘             └──────┬───────┘   one 5V_ISO domain from the B0505S-1WR3 on the CSC
       │ TXD/RXD (3.3V)             │ TXD/RXD (3.3V)
       ▼                            ▼
┌──────────────┐             ┌──────────────┐
│ STM32G0B1RE  │             │  MCP2518FD   │ ◄── SPI0 CS1 (Luckfox header)
│ FDCAN1       │             │  (SPI CAN)   │
│ (PB8/PB9)    │             └──────┬───────┘
│ off-switch   │                    ▼
│ + status     │             ┌──────────────┐
│   monitor    │             │ RV1106       │
└──────────────┘             │ heat thread  │  HEAT_SET_TEMP keep-alive 2 Hz,
 Cooking Surface             └──────────────┘  reads HEAT_STATUS (no PID)
 Controller (CS base)         Dispensing Unit (lifts off: bus and 24 V open together)
```

## 3. CAN Bus Interface

### 3.1 Physical Layer

| Parameter | Value |
|-----------|-------|
| Protocol | CAN 2.0B |
| Bit Rate | 500 kbps |
| Transceiver | Onboard in the heating unit; two ISO1050DUB isolated transceivers (5 kV RMS), one per Epicura board, in one isolated 5V_ISO domain generated once by the B0505S-1WR3 on the CSC: #1 on the **Cooking Surface Controller** for the STM32 FDCAN1, #2 on the **Unified PCB** (Dispensing Unit) for the RV1106's MCP2518FD (SPI0 CS1), its bus side powered from dock pin 6 (5V_ISO, F_CAN 100 mA). J_CAN_HEAT is the CSC's **isolated CAN port**; the stirring motor is on the CSC's separate non-isolated port (FDCAN2) |
| Termination | 120 ohm at each end (R_TERM1 at J_CAN_HEAT on the CSC + inside the heating unit); the dock → Unified PCB run is a stub ≤ 30 cm |
| Connector | Standard CAN connector on the unit (CAN_H, CAN_L, GND) ↔ J_CAN_HEAT (JST-XH 4-pin: CAN_H, CAN_L, GND_ISO, 5V_ISO) on the CSC; the bus continues to the Dispensing Unit over J_DOCK pogo pins 3–6 (CAN_H, CAN_L, GND_ISO, 5V_ISO) |
| Wiring | Twisted pair, shielded, <1m length; shield connects to GND_ISO at the CSC end only (single-point ground) |
| Nodes | Heating unit MCU (runs its own PID), RV1106 in the Dispensing Unit (sends setpoints, reads status), STM32 on the CSC (HEAT_ON_OFF = 0 only, E_STOP, relay) |

### 3.2 CAN Message Protocol (Heater)

| CAN ID | Name | Direction | Payload | Description |
|--------|------|-----------|---------|-------------|
| 0x100 | HEAT_SET_TEMP | RV1106 → Unit | target_dC (int16, 0.1 °C), ramp (uint8, °C/s), max_power_pct (uint8) | Temperature-mode setpoint; the unit's own PID regulates. Re-sent at 2 Hz as keep-alive |
| 0x101 | HEAT_ON_OFF | RV1106 or STM32 → Unit | 0=off, 1=on | Enable/disable heating; the STM32 only ever sends 0 |
| 0x102 | HEAT_QUERY | RV1106 → Unit | - | Request current status |
| 0x103 | HEAT_SET_POWER | RV1106 → Unit | power_pct (0-100), ramp (%/s) | Power-mode setpoint for stages defined by power (sear, rolling boil); re-sent at 2 Hz as keep-alive |
| 0x180 | HEAT_STATUS | Unit → bus | power_pct, surface_temp_dC (int16), element_temp (°C), pot_detected, fault_flags | Periodic status (10 Hz); surface_temp is the centre-sensor (pot-bottom) temperature and drives recipe stage transitions on the RV1106 and the STM32 over-temperature cut-off; element_temp is the plate / heater-body sensor |
| 0x181 | HEAT_FAULT | Unit → bus | Fault code, details | Fault notification |
| 0x182 | HEAT_ACK | Unit → RV1106 | Original CAN ID, result | Command acknowledgment |
| 0x001 | E_STOP | Any node → all | Source node, reason | Emergency stop accepted from the RV1106, the STM32 or the unit |

> [!note]
> Exact CAN message IDs and payload formats depend on the specific heating unit. The above is a reference protocol — adapt to the unit's documentation. The full bus ID map (host commands, telemetry, heartbeat) is owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]. The message set is identical to the one defined for the induction surface; only the meaning of `element_temp` (formerly `coil_temp`) changed.

## 4. Specifications

| Parameter | Value |
|-----------|-------|
| Maximum Power | 1,300 W (assumed, unit TBD; range 1,000–1,400 W) |
| AC Input Voltage | 220-240V, 50Hz single-phase |
| Plate Diameter | Matched to the 6 L inner pot base: pot is 228.6 mm Ø × 150 mm, plate est. ~220 mm (OEM drawing governs) |
| Efficiency | ~65-75% (electrical to thermal, contact heating) |
| Pot Compatibility | The unit's own 6 L non-stick inner pot (~4.8 L usable); any flat-bottomed pot of the same base diameter fits |
| Minimum Pot Diameter | 120mm |
| Control Interface | CAN bus (500 kbps), temperature mode + power mode |
| Temperature Control | Unit-internal PID on its centre (pot-bottom) sensor; setpoint resolution 1 °C, reported at 0.1 °C |
| Internal Safety | Pot detection (centre sensor), over-temperature cut-off, thermal fuse |
| Temperature Range | 60-200C at the centre sensor (reference unit: 80–200 °C; keep-warm at 60–70 °C to be confirmed with the OEM) |

## 5. Temperature Control

### 5.1 Control Loop Architecture

The temperature loop runs **inside the heating unit**. Epicura does not measure food temperature: the RV1106 recipe engine sends a setpoint (HEAT_SET_TEMP 0x100) or a power level (HEAT_SET_POWER 0x103) and the unit's own controller regulates on its centre sensor. The `heat` thread of `epicurad` re-sends the active setpoint at 2 Hz as a keep-alive, reads HEAT_STATUS (0x180) at 10 Hz and hands `surface_temp` to the engine for stage transitions. The STM32 only supervises HEAT_STATUS for absolute limits and can force the unit off.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────────────┐
│ Recipe Engine│    │  heat thread │    │ Electric Heating Unit                    │
│ (RV1106)     │──► │  (RV1106)    │──► │  CAN 0x100 HEAT_SET_TEMP (target, ramp)  │
│ Setpoint T*  │    │  2 Hz        │    │        │                                 │
│ or power %   │    │  keep-alive  │    │        ▼                                 │
└──────┬───────┘    └──────────────┘    │  ┌───────────┐   ┌───────────┐  ┌──────┐│
       ▲                                │  │ Unit PID  │──►│ relay /   │─►│ Plate││
       │  surface_temp (0.1 °C, 10 Hz)  │  └─────▲─────┘   │ triac     │  └──┬───┘│
       └────────────────────────────────┤        │         └───────────┘     │    │
                 CAN 0x180 HEAT_STATUS  │        └── centre sensor (pot) ────┘    │
                                        └──────────────────────────────────────────┘
```

### 5.2 Setpoint Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Setpoint source | Recipe stage `temp_target` (temperature mode) or `power_level` (power mode) | Engine thread → heat thread |
| Keep-alive rate | 2 Hz | Unit watchdog drops power to 0 after 1 s without a refresh |
| Ramp | 5 °C/s max (HEAT_SET_TEMP `ramp`) | Upper bound only: the plate itself ramps at ~2–4 °C/s |
| Max power clamp | `max_power_pct` in HEAT_SET_TEMP | Lets simmer stages cap power even if the unit wants more |
| Overshoot | Unit-internal; the plate's stored heat gives a few °C of overshoot after a power cut; recipe tolerance ±5 °C on `surface_temp` | Stage transition requires 3 consecutive readings within ±5 °C |
| Tuning | Vendor-tuned inside the unit | No Kp/Ki/Kd in Epicura firmware |

### 5.3 Power Mode Mapping

Power level (0-100%) sent via HEAT_SET_POWER maps to average plate power delivered by the unit (figures for the assumed 1,300 W unit):

```
Power Level (%)    Power (W)     Application
──────────────    ──────────    ───────────────
     0%              0W        Off / Standby
    10-15%        130-195W     Warm / Keep-warm
    25-35%        325-455W     Simmer
    50%             650W       Medium cook
    80-85%      1040-1105W     Boil
    100%           1300W       Sear / Maximum
```

### 5.4 Pot-Bottom vs. Food Temperature

The centre sensor reads the pot-bottom temperature through the pot base, not the food surface. Recipes therefore specify pot-bottom targets, and food-state decisions (browning, boiling, thickening) come from the camera and the CV pipeline rather than from a temperature reading. Water-based stages are self-limiting at ~100 °C in the pot while the sensor reads higher. The plate stores heat, so the pot-bottom temperature lags the power command by tens of seconds in both directions; the recipe schema's `temp_target` values and hold times are calibrated against this behaviour during recipe development.

## 6. Temperature Profiles

### 6.1 Cooking Stage Targets

| Stage | Target Temp (C) | Power Level | Ramp Rate | Hold Time | Typical Use |
|-------|-----------------|-------------|-----------|-----------|-------------|
| Preheat | 180-200 | 100% (1300W) | ~2-4 C/s (plate-limited) | Until target reached (1-2 min) | Initial pot heating |
| Sear / Tadka | 180-200 | 90-100% | - | 30-120s | Browning onions, tempering spices (200 °C is the unit's ceiling) |
| Boil | 100 | 80% (1040W) | Maintain | Until rolling boil | Bringing water/gravy to boil |
| Simmer | 80-95 | 30-40% (390-520W) | Maintain | 10-60 min | Slow cooking dal, curry |
| Warm | 60-70 | 15-20% (195-260W) | Maintain | Until served | Keep-warm after cooking |

### 6.2 Temperature Transition Diagram

```
Temp (C)
  200 ┤             ┌─── Sear ───┐
      │            /              \
  180 ┤     Preheat                \
      │    /                        \
  100 ┤───/                          └── Boil ──┐
      │                                          \
   80 ┤                                           └── Simmer ──────────┐
      │                                                                 \
   60 ┤                                                                  └── Warm
      │
      └──────────────────────────────────────────────────────────────────────────►
        0         2         5        10        20        40        60   Time (min)
```

## 7. Feedback Sources

| Source | Measurement | Interface | Range | Accuracy | Role |
|--------|-------------|-----------|-------|----------|------|
| Unit centre sensor (`surface_temp` in HEAT_STATUS) | Pot-bottom temperature | CAN 0x180, 10 Hz, 0.1 °C | Unit-reported (typ. 0–300 °C) | Unit accuracy (typ. ±3–5 °C) | Unit's own PID input; recipe stage transitions on the RV1106; STM32 over-temperature cut-off |
| Unit element sensor (`element_temp` in HEAT_STATUS) | Plate / heater body | CAN 0x180 | Unit-reported | Unit accuracy | Secondary limit and unit health monitoring |
| Camera + CV pipeline | Food state (colour, bubbles, texture) | ISP → NPU on the RV1106, 2 Hz | — | Classifier confidence | Cooking-stage detection; replaces food-surface temperature for browning and boiling decisions |

### 7.1 Degraded-Mode Logic

```
IF unit.surface_temp.valid:
    stage_temp = surface_temp              # Normal: centre sensor
ELIF unit.element_temp.valid:
    use power mode + timers; flag_degraded_mode()
ELSE:
    HEAT_SET_POWER 0, PAUSED               # No temperature data from the unit
```

## 8. Safety

### 8.1 Dual-Layer Safety Architecture

Safety is handled at two levels:

1. **Unit-internal:** The heating unit has its own safety circuits (pot detection, thermal fuse, over-temperature cut-off, and a 1 s command watchdog that drops power to zero without HEAT_SET_TEMP / HEAT_SET_POWER) that operate independently of both processors. These cannot be overridden by external CAN commands.
2. **System-level:** The RV1106 sends setpoints; the unit regulates. The STM32 independently monitors the unit's HEAT_STATUS (pot-bottom and element temperature, fault flags), and on a fault or heartbeat loss sends HEAT_ON_OFF = 0, broadcasts E_STOP (0x001) and cuts AC power via the safety relay. It never sends setpoints or power levels.
3. **Galvanic isolation:** Two ISO1050DUB isolated CAN transceivers, one per board — #1 on the **Cooking Surface Controller** (STM32 node) and #2 on the **Unified PCB** in the Dispensing Unit (RV1106 node) — share one isolated bus domain (5V_ISO / GND_ISO from the B0505S-1WR3 on the CSC) behind the CSC's isolated CAN port (J_CAN_HEAT) and provide 5 kV RMS galvanic isolation between the control electronics and the CAN bus connected to the heating unit. The isolated bus crosses the dock on pogo pins 3–6; the DU logic ground joins the CS ground only through dock pin 2. The stirring motor sits on a separate, non-isolated CAN port on the CSC. This keeps the mains-referenced heater controller and its relay/triac switching transients out of the logic ground, and satisfies IEC 60335 reinforced insulation requirements.
4. **Dock lift-off:** Lifting the Dispensing Unit opens the bus and the 24 V at the same instant. The unit drops to zero power ≤ 1 s later because its keep-alive stops (the AP is gone from the bus), the STM32 enters its safe hold on DOCK_SENSE_B (HEAT_ON_OFF = 0, stir and dock power off, STATUS DU_UNDOCKED) and the dock pads are de-energised by Q_DOCK. This is a pause, not an E_STOP. The plate keeps radiating stored heat for a few minutes after power-off; the UI shows a hot-surface warning while `surface_temp` is above 60 °C.

> [!warning] Critical Safety Section
> The unit's internal safety interlocks operate independently of the RV1106 and the STM32 and cannot be overridden. The safety relay provides a system-level hard disconnect; the STM32 that drives it does not depend on the application processor.

### 8.2 Safety Summary

| Layer | Mechanism | Trigger | Action | Response Time |
|-------|-----------|---------|--------|---------------|
| Unit | Pot detection (centre sensor) | Pot lifted off the plate | Unit will not heat | <500ms |
| Unit | Over-temperature cut-off (internal) | Element over-temperature | Unit shuts down internally | <100ms |
| Unit | Thermal fuse (internal) | Plate runaway | Unit disconnects permanently | Hardware |
| Unit | Command watchdog | No HEAT_SET_TEMP / HEAT_SET_POWER refresh for 1 s (AP stalled or bus down) | Power to 0 | 1s |
| Unit | Temperature loop | Internal PID holds the setpoint; internal over-temperature limit | Power reduced / cut internally | Unit-internal |
| System | Safety relay | E-stop, STM32 fault, RV1106 heartbeat loss | Relay opens, cuts AC to unit | <100ms |
| System | STM32 CAN off-switch | HEAT_STATUS surface_temp >230C (unit ceiling 200 °C), element over-temp, HEAT_FAULT, or RV1106 heartbeat loss | Send HEAT_ON_OFF=0 and broadcast E_STOP on the bus | <100ms |
| System | RV1106 heat thread | No HEAT_STATUS for 500 ms, HEAT_FAULT, pot absent | HEAT_ON_OFF 0, PAUSED | <500ms |
| System | Dispensing Unit lifted (dock) | DOCK_SENSE_B opens on the CSC; the AP leaves the isolated bus | Unit keep-alive expires → power 0; STM32 safe hold (HEAT_ON_OFF = 0, Q_STIR and Q_DOCK off, STATUS DU_UNDOCKED); RV1106 PAUSED (UNIT_LIFTED), resume only by user tap after re-docking | ≤ 1 s |
| System | STM32 watchdog | Firmware hang | STM32 resets, relay opens (fail-safe) | 1s |

### 8.3 Safe State Definition

When any safety condition triggers, the system enters the following safe state:

```
1. CAN ──► HEAT_ON_OFF = 0 from the STM32 + E_STOP 0x001 broadcast (unit stops heating)
2. Relay ──► OPEN (physical disconnect of AC to the unit)
3. Error flag ──► SET (logged to eMMC, displayed on UI)
4. Buzzer ──► ALERT pattern (3 short beeps, 1s pause, repeat)
5. RV1106 notified ──► Push notification to companion app
```

## 9. Power Management

### 9.1 Power Level Table

Figures for the assumed 1,300 W unit.

| Level | Name | Power (W) | CAN Power % | Application |
|-------|------|-----------|-------------|-------------|
| 0 | Off | 0 | 0% | Idle, no cooking |
| 1 | Warm | 150 | 10-15% | Keep food warm after cooking |
| 2 | Low | 325 | 25% | Gentle simmer, slow cooking |
| 3 | Medium | 650 | 50% | Standard cooking, sauce reduction |
| 4 | High | 1,100 | 85% | Boiling water, rapid cooking |
| 5 | Sear | 1,300 | 100% | Browning, tempering spices |

### 9.2 Soft-Start Sequence

A resistive plate has no inrush worth limiting, but the unit still ramps power over 2-3 seconds on a new setpoint (the `ramp` field of HEAT_SET_TEMP / HEAT_SET_POWER) to limit thermal shock to the pot and flicker on the mains:

```
Power (W)
  1300 ┤                            ┌────────── Target
       │                          /
   900 ┤                        /
       │                      /
   450 ┤                    /
       │                  /
     0 ┤─────────────────/
       └──────────────────────────────────────►
       0s              2s              4s    Time
       │◄── Soft-Start ──►│◄── Steady ──►│
```

### 9.3 Standby Power

- System standby: <5W total draw (RV1106 idle, display off, unit off)
- Deep sleep: <2W (RV1106 suspended, STM32 in STOP mode, relay open)

## 10. Software Safety

### 10.1 Watchdog and Heartbeat

| Mechanism | Timeout | Action on Timeout |
|-----------|---------|-------------------|
| STM32 IWDG (Independent Watchdog) | 1 second | Resets STM32 to safe state (CAN off command + relay open) |
| RV1106 Heartbeat (HB_AP on CAN) | 5 seconds | STM32 sends HEAT_ON_OFF=0, opens relay, enters safe standby |
| Setpoint keep-alive watchdog (unit) | 1 second | Unit drops to zero power on its own if HEAT_SET_TEMP / HEAT_SET_POWER is not refreshed |
| Maximum Cook Duration | Configurable (default 2 hours) | Graceful shutdown, alert user |
| Temperature Rate Limiter | >10 C/s rise detected (implausible for the plate: sensor fault or dry pot) | Reduce power to 50%, flag anomaly |

## 11. Testing and Validation

### 11.1 Test Procedures

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Power Accuracy | Measure input power at each CAN power level with calibrated meter | Within +/- 5% of rated power |
| Temperature Accuracy | Compare unit surface_temp vs. calibrated thermocouple on the pot bottom | Within +/- 5 C at 100 C |
| Setpoint Step Response | HEAT_SET_TEMP from 25 C to 100 C, record surface_temp curve | <180s rise time, <10 C overshoot (unit PID, plate lag) |
| Safety Relay Timing | Trigger E-stop, measure time to relay open | <100ms from trigger to cutoff |
| Pot Detection | Remove pot during operation, verify unit stops heating | Unit stops within 500ms |
| CAN Communication | Verify all message IDs send/receive correctly at 500 kbps | No errors over 10,000 messages |
| Thermal Cycling | 1,000 cycles: heat to 200 C, cool to ambient | No component failure or drift >5% |
| Insulation Resistance | 500V DC megger test, mains to logic | >7 Mohm |

### 11.2 Prototype Validation Checklist

- [ ] Unit powers on and responds to CAN queries
- [ ] CAN power level commands (HEAT_SET_POWER) correctly modulate plate power; HEAT_SET_TEMP engages the unit's temperature mode
- [ ] Unit's internal pot detection prevents heating without pot
- [ ] Unit holds a HEAT_SET_TEMP setpoint within +/- 5 C after settling; RV1106 keep-alive at 2 Hz is never late with the LCD refreshing
- [ ] Sear / tadka stage reaches 200 °C at the centre sensor within 3 min from 25 °C with the 6 L pot empty
- [ ] STM32 watchdog resets to safe state on firmware hang
- [ ] RV1106 heartbeat loss triggers power cutoff within 5s; killing `epicurad` drops unit power within 1s
- [ ] Lifting the Dispensing Unit mid-cook drops unit power within 1 s (keep-alive loss) and the STM32 reports DU_UNDOCKED; heating does not resume on re-dock without a user tap
- [ ] Safety relay disconnects AC on E-stop
- [ ] Soft-start keeps mains flicker within IEC 61000-3-3 limits
- [ ] Continuous 2-hour cook session completes without fault

## 12. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture]]
- [[02-Robotic-Arm|Robotic Arm System]]
- [[03-Ingredient-Dispensing|Ingredient Dispensing System]]
- [[04-Vision-System|Vision System]]
- [[01-Safety-Compliance|Safety & Compliance]]

#epicura #electric-heating #subsystem #canbus

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-20 | Manas Pradhan | Updated CAN transceiver to ISO1050DUB (isolated); added isolation barrier to block diagram; added galvanic isolation safety note; updated wiring for single-point ground on CAN shield |
| 3.0 | 2026-02-20 | Manas Pradhan | Updated ISO1050DUB location from Controller PCB to Driver PCB; CAN cable connects to J_CAN on Driver PCB |
| 3.1 | 2026-11-04 | Manas Pradhan | Application processor renamed from Raspberry Pi CM5 to RV1106 (Luckfox Pico Zero); heating control, CAN protocol and safety logic unchanged |
| 4.0 | 2026-11-04 | Manas Pradhan | Isolated CAN bus now shared by the induction surface MCU, the RV1106 (MCP2518FD + ISO1050DUB #2) and the STM32 (FDCAN1 + ISO1050DUB #1); temperature PID moved from the STM32 to the RV1106 heat thread (IR temperature via CAN telemetry), RV1106 sends HEAT_SET_POWER directly, STM32 limited to HEAT_ON_OFF=0 / E_STOP / relay; module command watchdog (1 s) added as a selection requirement; block diagram, CAN interface, PID, feedback and safety sections updated |
| 5.0 | 2026-11-04 | Manas Pradhan | IR thermometer dropped: the module runs its own temperature loop on its under-glass sensor; RV1106 sends HEAT_SET_TEMP (0x100, 2 Hz keep-alive) or HEAT_SET_POWER (0x103) and reads surface_temp from HEAT_STATUS; §5 rewritten (no PID in Epicura), §7 feedback sources, safety table and tests updated; isolated CAN port named J_CAN_HEAT (stirring motor on a separate non-isolated port) |
| 5.1 | 2026-11-04 | Manas Pradhan | Three-unit architecture: J_CAN_HEAT, ISO1050DUB #1 and the B0505S-1WR3 move to the Cooking Surface Controller in the CS base; ISO1050DUB #2 + MCP2518FD stay on the Unified PCB in the Dispensing Unit with the bus side fed from dock 5V_ISO; the isolated bus crosses the dock on pogo pins 3–6 (stub ≤ 30 cm); lifting the DU stops heating ≤ 1 s by keep-alive loss and the STM32 holds safe on DOCK_SENSE_B (DU_UNDOCKED); block diagram, physical-layer table, isolation paragraph, safety-layer table and checklist updated |
| 6.0 | 2026-11-04 | Manas Pradhan | Induction surface replaced by a commercial electric heating unit of the premium rice-cooker class (resistive plate, spring-loaded centre sensor, own PID and CAN port). Document renamed from Induction Heating. CAN message set, bus topology, CSC, Unified PCB and both firmwares unchanged; `coil_temp` renamed `element_temp`. Rated power assumed 1,300 W (unit TBD): power tables, ramp rates, efficiency, pot compatibility (any flat-bottomed pot, no ferromagnetic requirement), pot detection (centre sensor), EMI/EMF notes, step-response and thermal-cycling criteria updated; §1.2 now records the induction trade-offs |
| 6.1 | 2026-11-04 | Manas Pradhan | Reference unit fixed: Philips OneChef NX5300/00 (§2.3) — its body becomes the Cooking Surface (modified for the stirrer and dock), its air-fryer lid is replaced by the Dispensing Unit, its 6 L non-stick pot is Epicura's pot. 2,280 W nameplate includes the lid heater; base plate 1,000–1,300 W, planning figure stays 1,300 W. Temperature range 60–200 °C (sear/tadka ≤ 200 °C, STM32 cut-off 230 °C), selection requirement for an OEM CAN control board added with the Case B fallback named |
| 6.2 | 2026-11-04 | Manas Pradhan | OEM unit confirmed to ship with a CAN control board: Case B fallback removed from §2.1 and §2.3 |
