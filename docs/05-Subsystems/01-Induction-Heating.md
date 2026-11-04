---
created: 2026-02-15
modified: 2026-11-04
version: 5.0
status: Draft
---

# Induction Heating System

## 1. Overview

The induction heating system is the primary thermal element of Epicura, delivering up to 1,800W of cooking power through electromagnetic induction. Epicura uses a **commercial microwave induction surface** — a self-contained module with its own power coil, driver electronics, and AC power stage. The module exposes a **CAN bus interface** for external control and runs its **own temperature loop**: the RV1106 application processor sends a temperature setpoint (or, for sear stages, a power level) on the shared isolated CAN bus and reads the module's measured temperature, status and faults back, while the STM32 keeps an independent off-switch. Epicura has no temperature sensor of its own; the IR thermometer of earlier revisions is dropped.

This approach eliminates the need for custom high-voltage power electronics (IGBT half-bridge, gate drivers, resonant tank design, EMI filtering) and leverages a commercially certified, safety-tested heating module.

### 1.1 Advantages of Commercial Microwave Surface

- **No custom high-voltage design:** Eliminates IGBT driver board, resonant tank tuning, and EMI filter design
- **Pre-certified safety:** Commercial module includes pot detection, over-temperature, overcurrent protection
- **CAN bus control:** Digital interface replaces analog PWM gate driving; clean separation between power and logic
- **Built-in temperature control:** The module's own PID on its own surface sensor removes the IR thermometer, the emissivity calibration and the external control loop from Epicura
- **Faster prototyping:** No need to source/test individual IGBT modules, gate drivers, or Litz wire coils
- **Reliability:** Production-tested power electronics vs. prototype IGBT board

### 1.2 Advantages of Induction Over Resistive Heating

- **Speed:** Induction heats the pot directly, not the coil surface, reducing preheat time by 50-70%
- **Efficiency:** 85-90% of electrical energy reaches the food (vs. ~65% for radiant coils)
- **Precision:** Temperature setpoints in 1 °C steps and power from 0 to 1,800W via CAN commands
- **Safety:** No open flame, coil surface stays relatively cool, automatic shutoff without a pot
- **Cleanliness:** No combustion byproducts, easy wipe-down of flat glass-ceramic surface

## 2. Heater Module

### 2.1 Commercial Microwave Surface

The microwave surface is a self-contained induction heating module that includes:

- AC power inlet and internal EMI filter / rectifier
- IGBT or MOSFET driver stage with resonant coil (all internal)
- Built-in safety circuits (pot detection, thermal cutoff, overcurrent)
- Built-in temperature sensor under the glass (pot-bottom temperature) and a closed-loop temperature controller
- Exposed CAN bus port for external control (temperature setpoint, power level, on/off, status)

The module shares one isolated CAN bus with the RV1106 (which sends setpoints and reads status) and the STM32 (which can only force it off). All high-voltage power electronics are handled internally by the module — Epicura's Unified PCB never touches mains voltage.

Module selection requirements:
- Temperature mode: accepts a setpoint in °C and regulates on its own sensor; reports the measured temperature at ≥ 10 Hz
- Power mode: accepts a 0–100 % power level for stages that specify power rather than temperature (sear, boil)
- Command watchdog: drops to zero power if no HEAT_SET_TEMP / HEAT_SET_POWER refresh arrives for 1 s, so a stalled application processor cannot leave the heater on

### 2.2 System Block Diagram

```
AC Mains (220-240V 50Hz)
        │
        ▼
┌──────────────────────────────────────────────────┐
│         Microwave Induction Surface               │
│                                                    │
│  ┌────────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ AC Input   │  │ Power     │  │ Induction    │ │
│  │ EMI Filter │─►│ Driver    │─►│ Coil         │─┼──► Heats Pot
│  │ Rectifier  │  │ (internal)│  │ (internal)   │ │
│  └────────────┘  └─────┬─────┘  └──────────────┘ │
│                        │                           │
│                  ┌─────▼─────┐                     │
│                  │ Onboard   │◄── surface temp     │
│                  │ Controller│    sensor (NTC)     │
│                  │ + PID     │                     │
│                  │ + Safety  │                     │
│                  └─────┬─────┘                     │
│                        │                           │
│                   CAN Bus Port                     │
└────────────────────┬───────────────────────────────┘
                     │
              CAN_H, CAN_L, GND_ISO  (isolated bus, 500 kbps)
                     │
       ┌─────────────┴──────────────┐
       ▼                            ▼
┌──────────────┐             ┌──────────────┐
│  ISO1050DUB  │ ◄── 5 kV ──►│  ISO1050DUB  │   both on the Unified PCB,
│  #1 (STM32)  │  isolation  │  #2 (RV1106) │   one 5 V_ISO domain (B0505S-1WR3)
└──────┬───────┘             └──────┬───────┘
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
                             └──────────────┘  reads HEAT_STATUS (no PID)
```

## 3. CAN Bus Interface

### 3.1 Physical Layer

| Parameter | Value |
|-----------|-------|
| Protocol | CAN 2.0B |
| Bit Rate | 500 kbps |
| Transceiver | Onboard in module; Unified PCB carries two ISO1050DUB isolated transceivers (5 kV RMS) in one isolated 5 V_ISO domain: #1 for the STM32 FDCAN1, #2 for the RV1106's MCP2518FD (SPI0 CS1). This is the board's **isolated CAN port** (J_CAN_HEAT); the stirring motor is on a separate non-isolated port |
| Termination | 120 ohm at each end (module + J_CAN_HEAT on the Unified PCB; the two on-board nodes form a short stub) |
| Connector | Standard CAN connector on module (CAN_H, CAN_L, GND) ↔ J_CAN_HEAT |
| Wiring | Twisted pair, shielded, <1m length; shield connects to GND_ISO at the Unified PCB end only (single-point ground) |
| Nodes | Induction surface MCU (runs its own PID), RV1106 (sends setpoints, reads status), STM32 (HEAT_ON_OFF = 0 only, E_STOP, relay) |

### 3.2 CAN Message Protocol (Heater)

| CAN ID | Name | Direction | Payload | Description |
|--------|------|-----------|---------|-------------|
| 0x100 | HEAT_SET_TEMP | RV1106 → Module | target_dC (int16, 0.1 °C), ramp (uint8, °C/s), max_power_pct (uint8) | Temperature-mode setpoint; the module's own PID regulates. Re-sent at 2 Hz as keep-alive |
| 0x101 | HEAT_ON_OFF | RV1106 or STM32 → Module | 0=off, 1=on | Enable/disable heating; the STM32 only ever sends 0 |
| 0x102 | HEAT_QUERY | RV1106 → Module | - | Request current status |
| 0x103 | HEAT_SET_POWER | RV1106 → Module | power_pct (0-100), ramp (%/s) | Power-mode setpoint for stages defined by power (sear, rolling boil); re-sent at 2 Hz as keep-alive |
| 0x180 | HEAT_STATUS | Module → bus | power_pct, surface_temp_dC (int16), coil_temp (°C), pot_detected, fault_flags | Periodic status (10 Hz); surface_temp drives recipe stage transitions on the RV1106 and the STM32 over-temperature cut-off |
| 0x181 | HEAT_FAULT | Module → bus | Fault code, details | Fault notification |
| 0x182 | HEAT_ACK | Module → RV1106 | Original CAN ID, result | Command acknowledgment |
| 0x001 | E_STOP | Any node → all | Source node, reason | Emergency stop accepted from the RV1106, the STM32 or the module |

> [!note]
> Exact CAN message IDs and payload formats depend on the specific microwave surface module. The above is a reference protocol — adapt to the module's documentation. The full bus ID map (host commands, telemetry, heartbeat) is owned by [[../03-Software/02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]].

## 4. Specifications

| Parameter | Value |
|-----------|-------|
| Maximum Power | 1,800W |
| AC Input Voltage | 220-240V, 50Hz single-phase |
| Coil Diameter | 180-220mm (matched to pot base) |
| Efficiency | 85-90% (electrical to thermal) |
| Pot Compatibility | Ferromagnetic (cast iron, stainless w/ magnetic base) |
| Minimum Pot Diameter | 120mm |
| Control Interface | CAN bus (500 kbps), temperature mode + power mode |
| Temperature Control | Module-internal PID on its under-glass surface sensor; setpoint resolution 1 °C, reported at 0.1 °C |
| Internal Safety | Pot detection, thermal cutoff, overcurrent, insulation monitoring |
| Temperature Range | 60-250C surface temperature |

## 5. Temperature Control

### 5.1 Control Loop Architecture

The temperature loop runs **inside the induction module**. Epicura does not measure food temperature: the RV1106 recipe engine sends a setpoint (HEAT_SET_TEMP 0x100) or a power level (HEAT_SET_POWER 0x103) and the module's own controller regulates on its under-glass surface sensor. The `heat` thread of `epicurad` re-sends the active setpoint at 2 Hz as a keep-alive, reads HEAT_STATUS (0x180) at 10 Hz and hands `surface_temp` to the engine for stage transitions. The STM32 only supervises HEAT_STATUS for absolute limits and can force the module off.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────────────────┐
│ Recipe Engine│    │  heat thread │    │ Microwave Surface Module                 │
│ (RV1106)     │──► │  (RV1106)    │──► │  CAN 0x100 HEAT_SET_TEMP (target, ramp)  │
│ Setpoint T*  │    │  2 Hz        │    │        │                                 │
│ or power %   │    │  keep-alive  │    │        ▼                                 │
└──────┬───────┘    └──────────────┘    │  ┌───────────┐   ┌───────────┐  ┌──────┐│
       ▲                                │  │ Module PID│──►│ IGBT drive│─►│ Coil ││
       │  surface_temp (0.1 °C, 10 Hz)  │  └─────▲─────┘   └───────────┘  └──┬───┘│
       └────────────────────────────────┤        │  under-glass sensor        │    │
                 CAN 0x180 HEAT_STATUS  │        └────────────────────────────┘    │
                                        └──────────────────────────────────────────┘
```

### 5.2 Setpoint Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Setpoint source | Recipe stage `temp_target` (temperature mode) or `power_level` (power mode) | Engine thread → heat thread |
| Keep-alive rate | 2 Hz | Module watchdog drops power to 0 after 1 s without a refresh |
| Ramp | 5 °C/s max (HEAT_SET_TEMP `ramp`) | Limits thermal shock; the module enforces it |
| Max power clamp | `max_power_pct` in HEAT_SET_TEMP | Lets simmer stages cap power even if the module wants more |
| Overshoot | Module-internal; recipe tolerance ±5 °C on `surface_temp` | Stage transition requires 3 consecutive readings within ±5 °C |
| Tuning | Vendor-tuned inside the module | No Kp/Ki/Kd in Epicura firmware |

### 5.3 Power Mode Mapping

Power level (0-100%) sent via HEAT_SET_POWER maps to average power delivered by the module:

```
Power Level (%)    Power (W)     Application
──────────────    ──────────    ───────────────
     0%              0W        Off / Standby
    10-15%        180-270W     Warm / Keep-warm
    25-35%        450-630W     Simmer
    50%             900W       Medium cook
    80-85%      1440-1530W     Boil
    100%           1800W       Sear / Maximum
```

### 5.4 Surface vs. Food Temperature

The module's sensor reads the pot-bottom (glass) temperature, not the food surface. Recipes therefore specify pot-bottom targets, and food-state decisions (browning, boiling, thickening) come from the camera and the CV pipeline rather than from a temperature reading. Water-based stages are self-limiting at ~100 °C in the pot while the glass reads higher; the recipe schema's `temp_target` values are calibrated against this behaviour during recipe development.

## 6. Temperature Profiles

### 6.1 Cooking Stage Targets

| Stage | Target Temp (C) | Power Level | Ramp Rate | Hold Time | Typical Use |
|-------|-----------------|-------------|-----------|-----------|-------------|
| Preheat | 200 | 100% (1800W) | Fast (~20 C/s) | Until target reached | Initial pot heating |
| Sear | 200-250 | 90-100% | - | 30-120s | Browning onions, tempering spices |
| Boil | 100 | 80% (1440W) | Maintain | Until rolling boil | Bringing water/gravy to boil |
| Simmer | 80-95 | 30-40% (540-720W) | Maintain | 10-60 min | Slow cooking dal, curry |
| Warm | 60-70 | 15-20% (270-360W) | Maintain | Until served | Keep-warm after cooking |

### 6.2 Temperature Transition Diagram

```
Temp (C)
  250 ┤           ┌─── Sear ───┐
      │          /               \
  200 ┤    Preheat                \
      │   /                        \
  100 ┤──/                          └── Boil ──┐
      │                                         \
   80 ┤                                          └── Simmer ──────────┐
      │                                                                \
   60 ┤                                                                 └── Warm
      │
      └──────────────────────────────────────────────────────────────────────────►
        0         2         5        10        20        40        60   Time (min)
```

## 7. Feedback Sources

| Source | Measurement | Interface | Range | Accuracy | Role |
|--------|-------------|-----------|-------|----------|------|
| Module surface sensor (in HEAT_STATUS) | Pot-bottom / glass temperature | CAN 0x180, 10 Hz, 0.1 °C | Module-reported (typ. 0–300 °C) | Module accuracy (typ. ±3–5 °C) | Module's own PID input; recipe stage transitions on the RV1106; STM32 over-temperature cut-off |
| Module coil temperature (in HEAT_STATUS) | Coil / IGBT heatsink | CAN 0x180 | Module-reported | Module accuracy | Secondary limit and module health monitoring |
| Camera + CV pipeline | Food state (colour, bubbles, texture) | ISP → NPU on the RV1106, 2 Hz | — | Classifier confidence | Cooking-stage detection; replaces food-surface temperature for browning and boiling decisions |

### 7.1 Degraded-Mode Logic

```
IF module.surface_temp.valid:
    stage_temp = surface_temp              # Normal: module sensor
ELIF module.coil_temp.valid:
    use power mode + timers; flag_degraded_mode()
ELSE:
    HEAT_SET_POWER 0, PAUSED               # No temperature data from the module
```

## 8. Safety

### 8.1 Dual-Layer Safety Architecture

Safety is handled at two levels:

1. **Module-internal:** The microwave surface has its own safety circuits (pot detection, thermal fuse, overcurrent, and a 1 s command watchdog that drops power to zero without HEAT_SET_POWER) that operate independently of both processors. These cannot be overridden by external CAN commands.
2. **System-level:** The RV1106 sends setpoints; the module regulates. The STM32 independently monitors the module's HEAT_STATUS (surface and coil temperature, fault flags), and on a fault or heartbeat loss sends HEAT_ON_OFF = 0, broadcasts E_STOP (0x001) and cuts AC power via the safety relay. It never sends setpoints or power levels.
3. **Galvanic isolation:** Two ISO1050DUB isolated CAN transceivers on the **Unified PCB** (STM32 node and RV1106 node) share one isolated bus domain (B0505S-1WR3) behind the board's isolated CAN port (J_CAN_HEAT) and provide 5 kV RMS galvanic isolation between the control electronics and the CAN bus connected to the induction module. The stirring motor sits on a separate, non-isolated CAN port. This prevents ground bounce and EMI transients from the module's high-power IGBT switching from coupling into the logic ground, and satisfies IEC 60335 reinforced insulation requirements.

> [!warning] Critical Safety Section
> The module's internal safety interlocks operate independently of the RV1106 and the STM32 and cannot be overridden. The safety relay provides a system-level hard disconnect; the STM32 that drives it does not depend on the application processor.

### 8.2 Safety Summary

| Layer | Mechanism | Trigger | Action | Response Time |
|-------|-----------|---------|--------|---------------|
| Module | Pot detection (internal) | No ferromagnetic pot | Module will not heat | Immediate |
| Module | Thermal cutoff (internal) | Coil over-temperature | Module shuts down internally | <100ms |
| Module | Overcurrent (internal) | Excessive coil current | Module shuts down internally | <10us |
| Module | Command watchdog | No HEAT_SET_TEMP / HEAT_SET_POWER refresh for 1 s (AP stalled or bus down) | Power to 0 | 1s |
| Module | Temperature loop | Internal PID holds the setpoint; internal over-temperature limit | Power reduced / cut internally | Module-internal |
| System | Safety relay | E-stop, STM32 fault, RV1106 heartbeat loss | Relay opens, cuts AC to module | <100ms |
| System | STM32 CAN off-switch | HEAT_STATUS surface_temp >270C, module coil over-temp, HEAT_FAULT, or RV1106 heartbeat loss | Send HEAT_ON_OFF=0 and broadcast E_STOP on the bus | <100ms |
| System | RV1106 heat thread | No HEAT_STATUS for 500 ms, HEAT_FAULT, pot absent | HEAT_ON_OFF 0, PAUSED | <500ms |
| System | STM32 watchdog | Firmware hang | STM32 resets, relay opens (fail-safe) | 1s |

### 8.3 Safe State Definition

When any safety condition triggers, the system enters the following safe state:

```
1. CAN ──► HEAT_ON_OFF = 0 from the STM32 + E_STOP 0x001 broadcast (module stops heating)
2. Relay ──► OPEN (physical disconnect of AC to module)
3. Error flag ──► SET (logged to eMMC, displayed on UI)
4. Buzzer ──► ALERT pattern (3 short beeps, 1s pause, repeat)
5. RV1106 notified ──► Push notification to companion app
```

## 9. Power Management

### 9.1 Power Level Table

| Level | Name | Power (W) | CAN Power % | Application |
|-------|------|-----------|-------------|-------------|
| 0 | Off | 0 | 0% | Idle, no cooking |
| 1 | Warm | 200 | 10-15% | Keep food warm after cooking |
| 2 | Low | 450 | 25% | Gentle simmer, slow cooking |
| 3 | Medium | 900 | 50% | Standard cooking, sauce reduction |
| 4 | High | 1,500 | 85% | Boiling water, rapid cooking |
| 5 | Sear | 1,800 | 100% | Browning, tempering spices |

### 9.2 Soft-Start Sequence

To reduce inrush current and thermal shock, the module ramps power over 2-3 seconds on a new setpoint (the `ramp` field of HEAT_SET_TEMP / HEAT_SET_POWER):

```
Power (W)
  1800 ┤                            ┌────────── Target
       │                          /
  1200 ┤                        /
       │                      /
   600 ┤                    /
       │                  /
     0 ┤─────────────────/
       └──────────────────────────────────────►
       0s              2s              4s    Time
       │◄── Soft-Start ──►│◄── Steady ──►│
```

### 9.3 Standby Power

- System standby: <5W total draw (RV1106 idle, display off, module off)
- Deep sleep: <2W (RV1106 suspended, STM32 in STOP mode, relay open)

## 10. Software Safety

### 10.1 Watchdog and Heartbeat

| Mechanism | Timeout | Action on Timeout |
|-----------|---------|-------------------|
| STM32 IWDG (Independent Watchdog) | 1 second | Resets STM32 to safe state (CAN off command + relay open) |
| RV1106 Heartbeat (HB_AP on CAN) | 5 seconds | STM32 sends HEAT_ON_OFF=0, opens relay, enters safe standby |
| Setpoint keep-alive watchdog (module) | 1 second | Module drops to zero power on its own if HEAT_SET_TEMP / HEAT_SET_POWER is not refreshed |
| Maximum Cook Duration | Configurable (default 2 hours) | Graceful shutdown, alert user |
| Temperature Rate Limiter | >30 C/s rise detected | Reduce power to 50%, flag anomaly |

## 11. Testing and Validation

### 11.1 Test Procedures

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Power Accuracy | Measure input power at each CAN power level with calibrated meter | Within +/- 5% of rated power |
| Temperature Accuracy | Compare module surface_temp vs. calibrated thermocouple on the pot bottom | Within +/- 5 C at 100 C |
| Setpoint Step Response | HEAT_SET_TEMP from 25 C to 100 C, record surface_temp curve | <90s rise time, <10 C overshoot (module PID) |
| Safety Relay Timing | Trigger E-stop, measure time to relay open | <100ms from trigger to cutoff |
| Pot Detection | Remove pot during operation, verify module stops heating | Module stops within 500ms |
| CAN Communication | Verify all message IDs send/receive correctly at 500 kbps | No errors over 10,000 messages |
| Thermal Cycling | 1,000 cycles: heat to 250 C, cool to ambient | No component failure or drift >5% |
| Insulation Resistance | 500V DC megger test, mains to logic | >7 Mohm |

### 11.2 Prototype Validation Checklist

- [ ] Module powers on and responds to CAN queries
- [ ] CAN power level commands (HEAT_SET_POWER) correctly modulate heating power; HEAT_SET_TEMP engages the module's temperature mode
- [ ] Module's internal pot detection prevents heating without pot
- [ ] Module holds a HEAT_SET_TEMP setpoint within +/- 5 C after settling; RV1106 keep-alive at 2 Hz is never late with the LCD refreshing
- [ ] STM32 watchdog resets to safe state on firmware hang
- [ ] RV1106 heartbeat loss triggers power cutoff within 5s; killing `epicurad` drops module power within 1s
- [ ] Safety relay disconnects AC on E-stop
- [ ] Soft-start limits inrush current to acceptable levels
- [ ] Continuous 2-hour cook session completes without fault

## 12. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [[01-Epicura-Architecture|Hardware Architecture]]
- [[02-Robotic-Arm|Robotic Arm System]]
- [[03-Ingredient-Dispensing|Ingredient Dispensing System]]
- [[04-Vision-System|Vision System]]
- [[01-Safety-Compliance|Safety & Compliance]]

#epicura #induction-heating #subsystem #canbus

---

## 13. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 2.0 | 2026-02-20 | Manas Pradhan | Updated CAN transceiver to ISO1050DUB (isolated); added isolation barrier to block diagram; added galvanic isolation safety note; updated wiring for single-point ground on CAN shield |
| 3.0 | 2026-02-20 | Manas Pradhan | Updated ISO1050DUB location from Controller PCB to Driver PCB; CAN cable connects to J_CAN on Driver PCB |
| 3.1 | 2026-11-04 | Manas Pradhan | Application processor renamed from Raspberry Pi CM5 to RV1106 (Luckfox Pico Zero); heating control, CAN protocol and safety logic unchanged |
| 5.0 | 2026-11-04 | Manas Pradhan | IR thermometer dropped: the module runs its own temperature loop on its under-glass sensor; RV1106 sends HEAT_SET_TEMP (0x100, 2 Hz keep-alive) or HEAT_SET_POWER (0x103) and reads surface_temp from HEAT_STATUS; §5 rewritten (no PID in Epicura), §7 feedback sources, safety table and tests updated; isolated CAN port named J_CAN_HEAT (stirring motor on a separate non-isolated port) |
| 4.0 | 2026-11-04 | Manas Pradhan | Isolated CAN bus now shared by the induction surface MCU, the RV1106 (MCP2518FD + ISO1050DUB #2) and the STM32 (FDCAN1 + ISO1050DUB #1); temperature PID moved from the STM32 to the RV1106 heat thread (IR temperature via CAN telemetry), RV1106 sends HEAT_SET_POWER directly, STM32 limited to HEAT_ON_OFF=0 / E_STOP / relay; module command watchdog (1 s) added as a selection requirement; block diagram, CAN interface, PID, feedback and safety sections updated |
