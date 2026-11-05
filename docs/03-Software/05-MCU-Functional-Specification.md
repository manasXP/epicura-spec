---
tags: [epicura, mcu, stm32, functional-spec, firmware]
created: 2026-02-16
modified: 2026-11-05
version: 1.9
aliases: [STM32 Spec, MCU Spec]
---

# MCU Functional Specification — STM32G0B1RE

> **Document ID:** EPIC-SW-MCU-001
> **Processor:** STM32G0B1RET6, Cortex-M0+ @ 64 MHz
> **Flash / SRAM:** 512 KB (dual-bank) / 144 KB with parity
> **Package:** LQFP-64
> **Boards:** Cooking Surface Controller (CSC) v1.0 in the Cooking Surface base beside the three Mean Well PSUs (§1–§9), and the Unified PCB v5.0 in the Dispensing Unit (the DU STM32, §10)
> **Related:** [[04-MPU-Functional-Specification]], [[02-Controller-Software-Architecture]], [[01-Unified-PCB-Design]]
> **Revision:** 2026-11-05 (v1.9) — Robot-mop SLD on the DU STM32 (Unified PCB v5.3): the liquid dispenser is two drawer tanks (float + presence magnets on Hall switches) with the pumps in the DU body (6 V peristaltic oil, 6 V diaphragm water, Hall tach each) and passive check-valve nozzles; the solenoids, 2 kg load cells, NAU7802 ×2 and TCA9543A are gone. Metering is open loop — tach pulses × cal_ul — with a prime routine (pending at boot and on a tank re-seat; auto before the next dose or on SLD_PRIME 0x233) and per-unit calibration (SLD_CAL 0x237); QUERY_WEIGHT → QUERY_SLD; six GPIO PC0–PC5; SLD_LOAD_CELL_DRIFT (0x11) → SLD_TANK_ABSENT, NOT_DOCKED (0x23) added; FR-DU-032/-034/-035 rewritten, FR-DU-036/-037 added; §1, §2.5, §11.1–§11.3, §11.5–§11.7 updated
> **Previous revision:** 2026-11-05 (v1.8) — CSC on its own PSU (CSC v1.6, reverses v1.7): the board, both G5V-2 coils and the fans run from 12V_IN, a dedicated Mean Well LRS-35-12 (12 V, 3 A, 36 W) on J_12V_IN (XT30; F1 2 A, SS34, SMBJ12A, 100 µF); the heating-unit tap (J_HU_PWR / 12V_HU), its donor-rail requirements and the IRM-20-12 fallback are withdrawn — nothing is tapped from the OEM unit, which is not opened; K_SAFE returns to the heating unit's AC inlet loom (E-stop / safe hold = whole unit disconnected, the CSC stays up on its own PSU and boots independently of K_SAFE since the LRS-35-12's AC input is unswitched); mains loss takes all three PSUs down together; J_DU_IN unchanged; FR-MCU-051/-055/-056/-080, §1, §1.1, §3.1 PB0, §6.1, §7.1, §7.3, §9.1 updated
> **Earlier revision:** 2026-11-05 (v1.7) — CSC powered from the heating unit (CSC v1.5): the board, both G5V-2 coils and the fans run from 12V_HU, a 12 V SELV tap off the OneChef control-board supply on the new J_HU_PWR (F1 2 A, SS34, SMBJ12A, 470 µF; neither LRS-75-24 powers the CSC); the 24 → 12 V MP1584EN #1 is gone, one MP1584EN makes 5 V from 12 V; J_24V_IN → J_DU_IN (24V_DU, LRS-75-24 #1 to Q_DOCK only, −V bonded to the CSC ground; 12 connectors); K_SAFE now cuts AC to the heating **element** on the plate loom, not the unit's inlet, so the OEM control board, its CAN port and 12V_HU stay live on E-stop / safe hold and the CSC boots as soon as the appliance is on; FR-MCU-051/-055/-056/-080, §1, §1.1, §3.1, §6.1, §7.1, §7.3, §9.1 updated
> **Earlier revision:** 2026-11-04 (v1.5) — Stirring Unit on its own PSU: FDCAN2 is now the second isolated CAN port (ISO1050DUB #3 + B0505S #2, 5V_ISO2 / GND_SU; SN65HVD230 gone); Q_STIR / F_STIR dropped, the SU power cut is the pilot relay K_SU on PB4 (Q_KSU → G5V-2 #2 → J_SAFE pin 5, cuts the AC input of LRS-75-24 #2; heater relay named K_SAFE); PSU start-up rule FR-MCU-010c (≈ 300 ms, wait for the motor boot frame); J_SU pinout 24V_SU / GND_SU, J_SU_IN added (11 connectors); FR-MCU-010/-010a/-012a/-040/-055/-072, §1, §3.1, §3.3, §4.2, §4.3, §4.4, §6.1, §7, §8, §9 updated
> **Earlier revision:** 2026-11-04 (v1.4) — Second instance of the same part: the DU STM32 on the Unified PCB v5.0 takes dispensing, LED ring, buzzer, battery/dock monitoring and the DU's CAN node (gateway for the RV1106 over a UART host link); new §10 with FR-DU requirements, pin map, tasks and codes; CSC sections re-worded where they said these functions were on the RV1106
> **Earlier revision:** 2026-11-04 (v1.3) — Heating unit referenced to the Philips OneChef NX5300/00 (80–200 °C range, 6 L non-stick pot): Sear profile 180–200 °C; absolute limits re-based to surface_temp > 220 °C CRITICAL, > 230 °C E_STOP (were 260/270); element_temp > 250 °C WARNING unchanged
> **Earlier revision:** 2026-11-04 (v1.2) — Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged: HEAT_STATUS `coil_temp` → `element_temp`, fault 0x02 renamed OVER_TEMP_ELEMENT, power profiles re-based on the assumed 1,300 W unit
> **Earlier revision:** 2026-11-04 (v1.1) — Three-unit architecture: the STM32 moves off the Unified PCB onto the Cooking Surface Controller (CSC) in the Cooking Surface base. Dispensing, sensor polling, load cells, LED ring, buzzer, battery monitoring, I2C peripherals and the UART service link leave the MCU (now on the RV1106 in the Dispensing Unit, see [[04-MPU-Functional-Specification]]); four FreeRTOS tasks remain. Added: exhaust-fan control (0x260–0x262, FAN_STALL), dock interface (DOCK_SENSE_B on PB3 → safe hold, Q_DOCK on PB5), Q_STIR on PB4, CAN bootloader (0x7E0/0x7E8), fault 0x17 DU_UNDOCKED
> **Earlier revision:** 2026-11-04 — MCU changed from STM32G474RE to STM32G0B1RE (no control loop on the MCU, so no FPU or 170 MHz needed; two FDCAN controllers kept; same ST HAL, FreeRTOS, system bootloader and X-CUBE-CLASSB); I2C1_SCL PA15 → PB6, VBUS/battery ADC PC0/PC1 → PA0/PA4, buzzer PC7/TIM8 → PA8/TIM1_CH1, FDCAN AF9 → AF3; two CAN ports (FDCAN1 isolated heater/host bus, FDCAN2 regular stir-motor bus); IR thermometer removed (module reports its own temperature); stirring motor is a CAN servo; 2S battery monitoring; host link on the isolated CAN bus, MCU keeps heater off-switch, relay and E-stop authority

---

## 1. Overview

Epicura uses the STM32G0B1RE twice, from one firmware tree. Sections 2–9 of this document specify the **CSC instance**, the real-time controller and safety guardian on the Cooking Surface Controller (CSC) in the Cooking Surface (CS) base. Section 11 specifies the **DU instance** (the DU STM32) on the Unified PCB v5.0 in the Dispensing Unit: it drives the dispensers, LED ring, buzzer and battery/dock monitoring, and is the DU's CAN node — a transparent gateway between the RV1106's UART host link and the bus — with no safety authority.

The CSC STM32 is a node on the isolated CAN bus it shares with the DU STM32 (the AP node, carrying the RV1106's frames; in the lift-off Dispensing Unit, reached through the dock) and the electric heating unit (FDCAN1), and the sole master of the second isolated CAN bus to the stirring motor in the Stirring Unit (FDCAN2). It runs FreeRTOS with four tasks: motor control over CAN (50 Hz), the safety monitor (10 Hz), host CAN communications (20 Hz) and thermal/fan management (1 Hz). It has no dispensing, no sensors beyond the fan tachometers and the pot reed, no I2C peripherals and no battery: dispensing, load cells, LED ring, buzzer and battery monitoring are on the DU STM32 on the Unified PCB v5.0 in the Dispensing Unit (§10). There is no temperature loop anywhere in Epicura: the heating unit regulates its own temperature and reports it; the STM32 supervises that status and owns all safety-critical paths including the heater off-switch, the heating unit's inlet relay (K_SAFE, on its AC inlet loom), the Stirring Unit PSU relay (K_SU), the dock 24 V switch, E-stop handling and watchdog supervision.

### 1.1 Hardware Summary

| Parameter | Value |
|-----------|-------|
| Core | Cortex-M0+ @ 64 MHz, no FPU (nothing on the MCU needs one: there is no control loop, and the fastest task runs at 50 Hz) |
| Flash | 512 KB, dual-bank (STM32G0B1RET6; the 256 KB RCT6 is a drop-in cost-down) |
| SRAM | 144 KB with hardware parity check |
| ADC | 1× 12-bit (2.5 Msps, 16 external channels, hardware oversampling) |
| Timers | Advanced (TIM1), GP (TIM2 32-bit, TIM3/4, TIM14/15/16/17), basic (TIM6/7), LPTIM1/2 |
| Comm | 6× USART + 2× LPUART, 3× SPI, 3× I2C, USB 2.0 FS, 2× FDCAN (FDCAN1 = isolated host + heater bus, FDCAN2 = stir-motor bus); only FDCAN1/2, USB (bench DFU/CDC) and USART2 (J_DBG console) are used on the CSC — I2C1 pads unpopulated |
| Safety | IWDG on its own LSI clock, WWDG, SRAM parity, dual-bank flash with ECC, hardware CRC unit; ST X-CUBE-CLASSB self-test library (IEC 60730-1 Annex H / IEC 60335-1 Annex R Class B) covers the G0 family |
| Package | LQFP-64 (STM32G0B1RET6; the LQFP-48 CET6 would also fit the pin budget but loses PC0–PC15 and PD2) |
| Power | 3.3 V via AMS1117-3.3 LDO from the CSC's 12 → 5 V chain (one MP1584EN off 12V_IN, the CSC's own Mean Well LRS-35-12 on J_12V_IN; neither LRS-75-24 powers the CSC), ~0.5 W typical; no battery |
| DU instance (§10) | Same part on the Unified PCB v5.0: USART1 (PA9/PA10) host link to the RV1106 at 921,600 baud (also the system-bootloader UART), FDCAN1 (PB8/PB9) + a non-isolated SN65HVD230 as the DU's CAN node (isolation is on the CSC's port), I2C1 (PB6/PB7) to PCA9685 / PCF8574 #2 / INA219 ×2, six SLD Hall inputs on PC0–PC5 (pump tachs, tank present, tank low), TIM3 (pumps), TIM1 (LED ring), TIM14 (buzzer); no USB, no FDCAN2, no ADC use; 3.3 V from the DU's AMS1117 (≈ 30 mA), kept alive by the DU pack when lifted |

---

## 2. Functional Requirements

> [!note] Retired requirement IDs (three-unit architecture, 2026-11-04)
> FR-MCU-013 (DSB servos), FR-MCU-021/022/024/025 (sensor polling), FR-MCU-030–034 (§2.5 dispensing), FR-MCU-056 (POWER_FAIL / battery) and FR-MCU-060–063 (§2.8 LED ring) are **retired**. The functions are implemented on the DU STM32 as FR-DU requirements (§10); the RV1106 side is in [[04-MPU-Functional-Specification]]. IDs are not reused.

### 2.1 Heater Supervision (the temperature loop runs inside the heating unit)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-001 | Mirror the unit's `surface_temp` and `pot_detected` from HEAT_STATUS into TELEMETRY flags for the RV1106 (the RV1106 also reads HEAT_STATUS directly) | Should | Within one TELEMETRY interval (50 ms) |
| FR-MCU-002 | Never send HEAT_SET_TEMP or HEAT_SET_POWER; the only heater command the MCU sends is HEAT_ON_OFF = 0 (0x101) | Must | Verified by bus capture |
| FR-MCU-003 | Absolute thermal limits independent of the AP: HEAT_STATUS surface_temp > 230 °C, element over-temp or HEAT_FAULT → HEAT_ON_OFF = 0, E_STOP (0x001) broadcast, relay open | Must | Checked every 100 ms |
| FR-MCU-004 | Pot-absent in HEAT_STATUS → flag in TELEMETRY; RV1106 pauses | Should | Flag within one status interval |
| FR-MCU-005 | No temperature sensor on the MCU (IR thermometer removed) | — | — |
| FR-MCU-006 | Listen to HEAT_STATUS (0x180) on the shared bus for surface temperature, element temperature and faults | Must | No request needed; the unit broadcasts at 10 Hz |
| FR-MCU-007 | If HB_AP (0x010) is missing for 5 s or TELEMETRY cannot be sent (bus-off): HEAT_ON_OFF = 0, relay open, safe state | Must | Safe state within 5 s |

### 2.2 Power Level Profiles (reference; commanded by the RV1106 heat thread)

| Profile | Power (W) | Temp Range (°C) | Duty Cycle | CAN Command Value |
|---------|-----------|-----------------|------------|-------------------|
| Sear | 1,300 (assumed, unit TBD) | 180–200 | 100% | 0xFF |
| Boil | 1,040 | 100 | 80% | 0xCC |
| Simmer | 390–520 | 80–95 | 30–40% | 0x4D–0x66 |
| Warm | 150 | 60–70 | 10–15% | 0x1A |
| Off | 0 | Ambient | 0% | 0x00 |

### 2.3 Stirring Motor Control (CAN servo on FDCAN2)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-010 | Drive the 24 V CAN servo stirring motor over FDCAN2 (PB12 RX / PB13 TX, ISO1050DUB #3, 1 Mbps, 29-bit IDs): enable/disable, velocity (stirring) and position (home/park) commands at 50 Hz; parse feedback (velocity, position, current, temperature, faults) | Must | Commanded vs. reported speed within ±5 RPM; feedback age ≤ 40 ms |
| FR-MCU-010a | Switch the Stirring Unit's PSU (K_SU: Omron G5V-2 pilot relay on the AC input of LRS-75-24 #2, driven from PB4 via 2N7002 Q_KSU → J_SAFE pin 5; NC wiring, de-energised = SU PSU off) on before the first enable frame and off after 60 s parked, on E-stop, on heartbeat loss, on DU undock (safe hold) and in the boot-safe state | Must | 0 V on J_STIR_PWR at reset; motor de-energised within 50 ms of K_SU opening |
| FR-MCU-010b | Configure the motor's command timeout ≤ 500 ms at start-up so a silent bus stops the arm | Must | Verified by stopping FDCAN2 traffic |
| FR-MCU-010c | After K_SU closes, wait for the SU PSU start-up (≈ 300 ms) and for the motor's boot frame on FDCAN2 before sending the first command; a silent bus during that window is not STIR_CAN_FAULT | Must | First command frame only after the boot frame; no 0x15 raised during the start-up window |
| FR-MCU-011 | Support stir patterns: continuous, intermittent, reverse, scrape, fold, vigorous (velocity profiles + signed direction) | Must | Pattern selected by RV1106 command (0x202), direction param |
| FR-MCU-012 | Stall / over-torque detection from motor-reported current and velocity error only (the CAN servo reports its own current; there is no INA219 on the CSC) | Must | STIR_STALL (0x10) within 500 ms of a blocked paddle; 3 retries then error |
| FR-MCU-012a | FDCAN2 bus-off or no motor feedback for 200 ms → disable, K_SU off (SU PSU de-energised), STIR_CAN_FAULT (0x15) | Must | Reported within 300 ms |
| FR-MCU-013 | Retired — Dispenser Servo Block implemented on the DU STM32, see §10 FR-DU-030 | — | — |
| FR-MCU-014 | Motor control task at 50 Hz (20 ms period) | Must | Highest priority FreeRTOS task |

### 2.4 Sensor Polling

Only the unit-reported element temperature remains; FR-MCU-021/022/024/025 (load cells, battery ADC, INA219, sensor-poll task) are retired (implemented on the DU STM32, see §10). There is no Sensor Poll task; FR-MCU-023 is served by the CAN Comms task.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-023 | Parse element temperature from CAN HEAT_STATUS | Must | Received at 10 Hz from the heating unit |

### 2.5 Ingredient Dispensing

Retired in full (FR-MCU-030–034, §2.5.1, §2.5.2): dispensing is implemented on the DU STM32 in the Dispensing Unit (PCA9685 over I2C1, TB6612 pumps with Hall tach metering, tank Hall switches on PC0–PC5) — see §10 FR-DU-030–037; the RV1106 `dispense` client is in [[04-MPU-Functional-Specification]] §2.9. No dispensing frame exists on the CAN bus: the 0x230–0x239 block lives on the RV1106 ↔ DU STM32 host link only.

### 2.6 RV1106 Communication (CAN bus)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-040 | Host link is FDCAN1 (PB8/PB9) on the isolated 3-node CAN bus (ISO1050DUB #1 on the CSC; J_CAN_HEAT to the heating unit, J_DOCK pins 3–6 to the DU node — the DU STM32 gateway for the RV1106 — in the Dispensing Unit), classic CAN 2.0B at 500 kbps, 11-bit IDs; FDCAN2 (PB12/PB13) is a separate isolated bus to the stirring motor only (ISO1050DUB #3, J_CAN_STIR) | Must | FDCAN1 accepts 0x001, 0x010, 0x18x, 0x202, 0x221–0x225, 0x260–0x262 and 0x7E0 via hardware filters; no frame is ever bridged between the two buses |
| FR-MCU-041 | Command frames: byte 0 = seq, bytes 1..7 = payload; answer every command with ACK/NAK (0x3FF: seq, cmd_type, result, ≤ 5 data bytes) | Must | ACK within 50 ms of a valid command; NAK with result code on invalid payload or state |
| FR-MCU-042 | No software framing or CRC; rely on CAN hardware ACK + CRC; reject frames with wrong DLC | Must | Bad-DLC frames counted and dropped |
| FR-MCU-043 | Send TELEMETRY (0x310) at 20 Hz unsolicited (LOADCELLS 0x311 retired on the bus — there are no load cells since 2026-11-05, SLD metering is by pump tach on the DU STM32; 0x311 is reused as DU_STATUS on the host link only) | Must | motor_rpm, motor_current_dA, safety_state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok), error_code, seq |
| FR-MCU-044 | Send STATUS (0x312) on safety state change and on safe-hold entry/exit | Must | safety_state, error_code, flags, fault_detail (no batt_mV: the battery is in the Dispensing Unit) |
| FR-MCU-045 | CAN comms task at 20 Hz (50 ms period) driven by the FDCAN1 RX FIFO interrupt | Must | Process incoming commands + queue outgoing |
| FR-MCU-046 | Monitor HB_AP (0x010, every 2 s) | Must | Missing for 5 s → safe state (HEAT_ON_OFF = 0, relay open) |
| FR-MCU-047 | Firmware update over the isolated CAN bus: an in-application CAN bootloader (OpenBLT-style) accepts FW_UPDATE_REQ (0x7E0: seq, op = ERASE / WRITE / VERIFY / BOOT, 5 data bytes) streamed by the RV1106 through the DU STM32 gateway and answers FW_UPDATE_RSP (0x7E8: seq, op, result, 4 data bytes); the image is CRC-verified before the application slot is marked valid and booted; USB-C DFU on the CSC is the bench fallback, SWD for factory. No UART host link exists (USART2 is a debug console on J_DBG only) | Should | Update accepted only in the safe state with heater off and stir motor disabled; CRC mismatch → NAK, previous image kept; 0x7E0/0x7E8 are the lowest-priority IDs on the bus |

### 2.7 Safety

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-050 | E-stop button (PB2, EXTI interrupt) → immediate shutdown | Must | <1 ms from button press to relay open |
| FR-MCU-051 | Safety relay control (PB0 → MOSFET → K_SAFE, piloting the power relay on the heating unit's AC inlet loom; the OEM unit itself is not opened) | Must | Cuts AC to the whole heating unit; the CSC, on its own LRS-35-12, stays up with K_SAFE open |
| FR-MCU-052 | Thermal cutoff: HEAT_STATUS surface_temp >230 °C, CAN element over-temp or HEAT_FAULT → E_STOP | Must | Checked every 100 ms (safety monitor cycle) |
| FR-MCU-053 | Hardware watchdog (IWDG, 5 s timeout) | Must | Kick in main loop; timeout → full reset |
| FR-MCU-054 | Pot detection via CAN (unit-reported `pot_detected`, spring-loaded centre sensor) | Must | No heat command if pot absent |
| FR-MCU-055 | Boot-safe state: all actuator outputs OFF until initialized — K_SU open (SU PSU off), Q_DOCK off, K_SAFE open (heating unit disconnected at its inlet), fans off. The CSC powers up from 12V_IN (its own LRS-35-12, AC input unswitched) as soon as the appliance is on, independent of K_SAFE and K_SU | Must | Pull-downs/pull-ups on MOSFET gates; verified with the MCU held in reset; the STM32 boots and reports STATUS with K_SAFE open |
| FR-MCU-056 | Retired — POWER_FAIL / battery monitoring is on the DU STM32 Monitor task (§10 FR-DU-050), reported to the RV1106 in DU_STATUS (the CSC has no battery and no 24 V comparator; a mains outage takes all three PSUs, the CSC, fans, relays and the dock 24 V down together, and the STM32 reboots in < 1 s when 12V_IN returns with mains) | — | — |

### 2.8 LED Ring (retired)

Retired in full (FR-MCU-060–063) on the CSC: the camera LED ring is a white PWM-dimmed ring on the Unified PCB v5.0 in the Dispensing Unit, driven by the DU STM32 (TIM1 → Q_LED) on SET_LED (0x220) from the RV1106 — see §10 FR-DU-040. SET_LED exists on the host link only, never on the bus.

### 2.9 Dock Interface (DOCK_SENSE_B, Q_DOCK)

The Dispensing Unit seats on an 8-contact magnetic pogo dock on the CS left pillar; the CSC owns the dock's 24 V switch and senses the unit's presence (see §3.4).

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-070 | Sense DU presence on PB3 (DOCK_SENSE_B, 10k pull-up, low = DU present; dock pin 8 is tied to GND on the DU) with 20 ms debounce; mirror it as the `docked` flag in TELEMETRY | Must | Flag within one TELEMETRY interval of the debounced edge |
| FR-MCU-071 | Enable the dock 24 V (Q_DOCK, AO4407A driven from PB5 via 2N7002, F_DOCK 2 A → J_DOCK pin 1) only while DOCK_SENSE_B is low; off within 1 ms of DOCK_SENSE_B going high, at reset and in E_STOP | Must | Dock pads de-energised when the unit is lifted; 0 V on J_DOCK pin 1 with no DU present |
| FR-MCU-072 | DOCK_SENSE_B open → immediate safe hold: HEAT_ON_OFF = 0 (0x101), stir disable frame on FDCAN2, K_SU off (SU PSU de-energised), Q_DOCK off, STATUS (0x312) with error_code 0x17 DU_UNDOCKED. Not an E_STOP: the relay stays closed and no E_STOP frame is sent | Must | Outputs off within one safety-monitor cycle (100 ms); the heater also stops by itself ≤ 1 s after the last RV1106 keep-alive |
| FR-MCU-073 | Leave safe hold back to NORMAL only when DOCK_SENSE_B is low again **and** HB_AP (0x010) has returned; Q_DOCK re-enabled as soon as DOCK_SENSE_B is low | Must | STATUS sent on exit; no command accepted while held |

### 2.10 Exhaust Fans

Both 12 V exhaust fans sit in the CS rear with the CSC and are driven by it (fans and their MOSFETs left the Unified PCB). Command codes follow [[05-Exhaust-Fume-Management]] §3.4.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-080 | Drive fan 1 from PA6 (TIM3_CH1, 25 kHz hardware PWM) and fan 2 from PB10 (25 kHz software PWM) through IRLML6344 low-side MOSFETs (SS14 flyback) → J_FAN (12V_IN, the CSC's LRS-35-12) | Must | Duty 0–100 % in 1 % steps; fans off in the boot-safe state and on E_STOP |
| FR-MCU-081 | Handle SET_EXHAUST (0x260: seq, duty_pct) and EXHAUST_AUTO (0x262: seq, stage_id → stage duty table held in firmware); ACK within one comms cycle | Must | Duty applied ≤ 50 ms after the frame; NAK on duty > 100 or unknown stage_id |
| FR-MCU-082 | Answer GET_EXHAUST (0x261: seq) with ACK data: duty_pct, rpm1, rpm2 (uint16, from the optional tachometer inputs, 0 if not fitted) | Must | Response within 100 ms |
| FR-MCU-083 | Fan stall detection in the Thermal/Fan task (1 Hz): tachometer < 300 rpm for 2 s with duty > 0 → clear fan1_ok / fan2_ok in the TELEMETRY flags (FAN_STALL) and send STATUS; the RV1106 heat thread reduces heater power, the STM32 never sends power levels | Must | Flag within 3 s of a stalled fan; cleared when rpm recovers |

---

## 3. Hardware Interfaces

### 3.1 Pin Assignment (LQFP-64)

All signals are on the Cooking Surface Controller (CSC) v1.0; this instance does not share a board with the RV1106 (the DU instance's pin map is in §10.2).

| Pin | Function | Peripheral | Target |
|-----|----------|------------|--------|
| **PA0** | ADC_IN0 | Analog | USB VBUS detect (100k/100k divider; bench USB-C only) |
| **PA1** | — | Available | Freed (24 V power-fail comparator dropped — no battery on the CSC, outage handling is on the DU STM32 / RV1106) |
| **PA2** | USART2_TX (AF1) | UART | Debug console → J_DBG 3-pin header; no host link (the RV1106 is in another unit, behind the DU STM32 gateway) |
| **PA3** | USART2_RX (AF1) | UART | Debug console ← J_DBG |
| **PA4** | — | Available | Freed (battery ADC dropped — the 2S pack is in the Dispensing Unit) |
| **PA5** | — | Available | Freed (stir motor DIR; motor is now on FDCAN2) |
| **PA6** | TIM3_CH1 (AF1) | PWM 25 kHz | Exhaust fan 1 (IRLML6344 + SS14 → J_FAN, 12 V) |
| **PA7** | — | Available | Freed |
| **PA8** | — | Available | Freed (piezo buzzer moved to the Dispensing Unit, DU STM32 TIM14) |
| **PA9** | — | Available | Freed |
| **PA10** | — | Available | Freed |
| **PA11** | USB_DM | USB 2.0 FS | USB D- (native USB, DFU+CDC, J_USB bench only) |
| **PA13** | SWDIO | Debug | SWD programming (J_SWD 2×5 1.27 mm) |
| **PA14** | SWCLK / BOOT0 | Debug + boot | SWD clock; on the G0 this pin is also BOOT0 (sampled at reset) → SW_BOOT push-button on the CSC for bench DFU entry (option bit nBOOT_SEL must be cleared once at factory programming, see §5.1); no RV1106 line |
| **PB0** | GPIO output | Digital | Heater safety relay K_SAFE (Q_RLY 2N7002 → Omron G5V-2 12 V coil → J_SAFE pin 1; pilots the power relay on the heating unit's AC inlet loom) |
| **PB1** | GPIO input | Digital | Pot reed switch (J_SAFE pin 2, optional backup to the heating unit's pot detection) |
| **PB2** | EXTI | Interrupt | E-stop button on the CS front (NC, active-low, J_SAFE pin 3, 10k pull-up + 100 nF) |
| **PB3** | GPIO input | Digital | DOCK_SENSE_B (10k pull-up; low = DU present; J_DOCK pin 8) |
| **PB4** | GPIO output | Digital | K_SU enable (Q_KSU 2N7002 → Omron G5V-2 #2 12 V coil → J_SAFE pin 5; pilot relay on the AC input of the SU PSU LRS-75-24 #2) |
| **PB5** | GPIO output | Digital | Q_DOCK enable (2N7002 → AO4407A P-MOSFET → F_DOCK 2 A → J_DOCK pin 1 DOCK_24V) |
| **PB6** | I2C1_SCL (AF6) | Unpopulated pads | No I2C device on the CSC; pads kept for a future expander |
| **PB7** | I2C1_SDA (AF6) | Unpopulated pads | No I2C device on the CSC |
| **PA15** | — | Available | Freed (was I2C1_SCL on the G474) |
| **PB8** | FDCAN1_RX (AF3) | CAN 500 kbps | Isolated 3-node bus (RV1106 via the dock + heating unit) via ISO1050DUB #1 |
| **PB9** | FDCAN1_TX (AF3) | CAN 500 kbps | Isolated 3-node bus (RV1106 via the dock + heating unit) via ISO1050DUB #1 |
| **PB10** | GPIO output | Software PWM 25 kHz | Exhaust fan 2 (IRLML6344 + SS14 → J_FAN, 12 V) |
| **PB11** | — | Available | Freed |
| **PB12** | FDCAN2_RX (AF3) | CAN 1 Mbps | Isolated stir-motor bus via ISO1050DUB #3 (5V_ISO2 / GND_SU) → J_CAN_STIR |
| **PB13** | FDCAN2_TX (AF3) | CAN 1 Mbps | Isolated stir-motor bus via ISO1050DUB #3 (5V_ISO2 / GND_SU) → J_CAN_STIR |
| **PB14** | — | Available | Freed (WS2812B ring removed; the white LED ring is on the Dispensing Unit, DU STM32 TIM1) |
| **PB15** | — | Available | Freed |
| **PC0–PC6** | — | Available | Freed (pump PWM/DIR, VBUS and battery sense all left the CSC) |
| **PC7** | GPIO output | Digital | Status LED |
| **PC8–PC12** | — | Available | Freed (the HX711 load cells of the single-board design are gone; SLD sensing is Hall switches on the DU STM32) |
| **PD2** | — | Available | Freed |

### 3.2 I2C1 Bus (PB6/PB7)

Unpopulated pads. The CSC carries no I2C device: the PCF8574 (all CSC outputs are now direct GPIO), INA219 (the CAN servo reports its own current) and PCA9685 (dispensing, now on the DU STM32) are gone from this board.

### 3.3 CAN Buses

**FDCAN1 — isolated host + heater bus (J_CAN_HEAT + J_DOCK pins 3–6)**
- Transceiver: ISO1050DUB #1 (isolated, 5 kV RMS) on the CSC, fed by the CSC's B0505S-1WR3 #1 (5V_ISO/GND_ISO). This is the host bus's isolated domain (the stir bus has its own, GND_SU, below): it is extended over dock pins 3–5 (CAN_H, CAN_L, GND_ISO) to the DU STM32's non-isolated SN65HVD230 (FDCAN1, the AP node carrying the RV1106's frames) on the Unified PCB v5.0 in the Dispensing Unit. GND_ISO is tied to the DU logic ground on the Unified PCB (dock pad 5) and nowhere on the CSC — the host-bus domain is referenced once, at the DU, so ISO1050DUB #1 is a ground-loop barrier rather than a safety barrier (the DU ground already meets the CS ground on dock pad 2); dock pin 6 (5V_ISO through F_CAN 100 mA) is exported but reserved, the DU draws nothing from it. The heating unit's CAN port must therefore be SELV (isolated inside the unit)
- Bit rate: 500 kbps (CAN 2.0B, classic frames, 11-bit IDs)
- Nodes: STM32 (this MCU, src_node 2), AP = the DU STM32 gateway carrying the RV1106's frames (via the dock), heating unit MCU (J_CAN_HEAT, JST-XH 4-pin: CAN_H, CAN_L, GND_ISO, 5V_ISO)
- Termination: R_TERM1 120 Ω on the CSC at J_CAN_HEAT and 120 Ω inside the heating unit; the dock → Unified PCB run is a stub ≤ 30 cm; PESD1CAN on the isolated side
- Lifting the DU opens the bus and the dock 24 V at the same instant: the STM32 sees DOCK_SENSE_B go high (safe hold, §2.9) and HB_AP stop; the heating unit stops ≤ 1 s after the last keep-alive
- Traffic: host commands 0x2xx and reports 0x3xx (RV1106 ↔ STM32), heater control 0x1xx (RV1106 → unit; STM32 sends HEAT_ON_OFF = 0 only), E_STOP 0x001, HB_AP 0x010, firmware update 0x7E0/0x7E8 — see §5.2

**FDCAN2 — isolated stir-motor bus (J_CAN_STIR)**
- Transceiver: ISO1050DUB #3 (isolated, 5 kV RMS) on the CSC, bus side fed by B0505S #2 (5V_ISO2, referenced to GND_SU); PB12 RX / PB13 TX (AF3). The only galvanic links between the CS and the SU are the ISO1050 barrier and the B0505S transformer
- Bit rate: 1 Mbps (CAN 2.0B, 29-bit IDs per the motor protocol)
- Nodes: STM32 (master) and the stirring motor's integrated controller in the Stirring Unit; 120 Ω at J_CAN_STIR and at the motor
- Traffic: enable/disable, velocity and position commands at 50 Hz; motor feedback (velocity, position, current, temperature, faults); wrapped in `stir_motor.c`
- Power: the Stirring Unit runs from its own PSU, LRS-75-24 #2, whose floating output (24V_SU / GND_SU, never bonded to the CS ground) enters the CSC on J_SU_IN (XT30), crosses the SU island (F_SU 5 A polyfuse, SMBJ24A) and leaves on J_STIR_PWR (XT30). The SU power cut is K_SU (PB4 via 2N7002 Q_KSU → G5V-2 #2 → J_SAFE pin 5), a pilot relay on the PSU's AC input: the motor is de-energised within ~50 ms of K_SU opening, and the PSU needs ≈ 300 ms after K_SU closes (FR-MCU-010c). J_CAN_STIR and J_STIR_PWR are bundled into the stirring-unit harness inside the right pillar, ending at J_SU (Molex Micro-Fit 3.0, 5-way: 24V_SU, GND_SU, CAN_H, CAN_L, SHIELD — GND_SU at the CSC end) — the only cable between units; nothing on it references the CS ground
- Never bridged to FDCAN1

### 3.4 Dock Interface (J_DOCK, CSC view)

J_DOCK is an 8-pin JST-XH header on the CSC wired to the pogo block in the CS left pillar (8 spring pins, 2 A each, 2.54 mm pitch, magnetic, keyed recess; flat gold pads on the DU underside). The load cells, HX711 and all other DU sensing that used to be in this section are now on the Unified PCB (see MPU spec).

| Pin | Signal | Direction | CSC side |
|-----|--------|-----------|----------|
| 1 | DOCK_24V | CS → DU | Q_DOCK (AO4407A, PB5 via 2N7002) → F_DOCK 2 A polyfuse; on only while DOCK_SENSE_B is low; pads dead when the unit is lifted |
| 2 | GND | — | 24 V return; ties the DU logic ground to the CS ground while docked |
| 3 | CAN_H | bus | Isolated bus from ISO1050DUB #1 (same bus as J_CAN_HEAT) |
| 4 | CAN_L | bus | |
| 5 | GND_ISO | — | Isolated bus ground (B0505S #1 output); tied to the DU logic ground on the Unified PCB — the only reference point of the host-bus domain |
| 6 | 5V_ISO | CS → DU | B0505S-1WR3 #1 output through F_CAN 100 mA; reserved — not connected on the Unified PCB v5.0 (the DU node is a non-isolated SN65HVD230) |
| 7 | DOCK_SENSE_A | CS → DU | Tied to GND on the CSC; the DU's 10k pull-up → DU STM32 PB3 reads low when docked (reported to the RV1106 in DU_STATUS) |
| 8 | DOCK_SENSE_B | DU → CS | Tied to GND on the DU; 10k pull-up on the CSC → PB3; low = DU present (enables Q_DOCK) |

---

## 4. Software Architecture

### 4.1 RTOS Configuration

- **RTOS:** FreeRTOS 10.x
- **Language:** C (MISRA C subset for safety-critical paths)
- **DSP:** CMSIS-DSP (fixed-point q15/q31 kernels) for signal filtering; no control loop on the MCU — the heating unit regulates its own temperature
- **Class B:** X-CUBE-CLASSB self-tests (CPU registers, RAM march, flash CRC, clock and program-flow monitors) at boot and in the safety monitor's background slot
- **Heap:** heap_4 (coalescing), ~64 KB allocated
- **Tick rate:** 1 kHz (1 ms)

### 4.2 Task Table

| Task | Rate | Period | Priority | Stack | Description |
|------|------|--------|----------|-------|-------------|
| Motor Control | 50 Hz | 20 ms | Highest (4) | 512 B | FDCAN2 velocity/position commands to the stir motor, feedback parsing, ramps, stir patterns, stall detection |
| Safety Monitor | 10 Hz | 100 ms | Highest (4) | 256 B | HEAT_STATUS thermal limits, E-stop, heartbeat, DOCK_SENSE_B safe hold, K_SAFE/K_SU/Q_DOCK authority, watchdog kick |
| CAN Comms | 20 Hz | 50 ms | High (3) | 1024 B | FDCAN1 RX FIFO → command parser, ACK/NAK, TELEMETRY/STATUS TX, HEAT_STATUS capture for the safety monitor, exhaust commands, CAN bootloader hand-off (0x7E0) |
| Thermal/Fan | 1 Hz | 1 s | Medium (2) | 256 B | Fan PWM (PA6/PB10), optional tachometer read and FAN_STALL, EXHAUST_AUTO stage table, pot reed (PB1) debounce |

The former Dispense and Sensor Poll tasks are removed from the CSC image (they live in the DU image as the Dispense and Monitor tasks, §10.3).

### 4.3 Safety State Machine

```
NORMAL ──[warning condition]──→ WARNING
WARNING ──[critical condition]──→ CRITICAL
CRITICAL ──[any safety violation]──→ E_STOP
E_STOP ──[manual reset]──→ NORMAL
WARNING ──[condition cleared]──→ NORMAL
CRITICAL ──[condition cleared within timeout]──→ WARNING
```

**State Transitions:**

| From | To | Trigger |
|------|----|---------|
| NORMAL | WARNING | HEAT_STATUS element temp > 250 °C, stir-motor temperature > 80 °C, fan stall (FAN_STALL) |
| WARNING | CRITICAL | HEAT_STATUS surface_temp > 220 °C, or CAN fault from the heating unit |
| CRITICAL | E_STOP | surface_temp > 230 °C, CAN element over-temp, HEAT_FAULT, E-stop button, RV1106 heartbeat timeout (5 s) |
| E_STOP | NORMAL | Manual hardware reset (E-stop button released + PB2 debounce) |

**Safe hold (DU undocked):** DOCK_SENSE_B going high is not a safety-state transition and not an E_STOP. The safety monitor applies the safe-hold outputs (HEAT_ON_OFF = 0, stir disable + K_SU off (SU PSU de-energised), Q_DOCK off, relay stays closed), reports error_code 0x17 DU_UNDOCKED in STATUS and refuses commands until DOCK_SENSE_B is low again and HB_AP has returned, then resumes NORMAL and clears the code. Battery-low is no longer a WARNING trigger: the pack and its monitoring are in the Dispensing Unit.

### 4.4 Boot Sequence

1. **Reset** → SystemInit (8 MHz HSE + PLL → 64 MHz SYSCLK; FDCAN kernel clock from PLLQ); Class B start-up self-tests
2. **HAL_Init** → SysTick, NVIC priorities
3. **Peripheral init** → GPIO (all outputs LOW/safe: K_SU, Q_DOCK, relay and fans off), ADC (VBUS), TIM3 (fan 1 PWM), FDCAN1 (filters for 0x001, 0x010, 0x18x, 0x202, 0x221–0x225, 0x260–0x262, 0x7E0), FDCAN2 (motor feedback filter, 1 Mbps), USART2 (J_DBG console)
4. **Safety check** → Verify E-stop not pressed, relay OFF; read DOCK_SENSE_B (PB3): Q_DOCK stays off until a DU is sensed (low), then Q_DOCK on. No I2C self-test and no battery check (neither exists on the CSC)
5. **FreeRTOS start** → Create the four tasks, start scheduler
6. **Wait for RV1106 heartbeat** → First HB_AP (0x010) on the bus (forwarded by the DU STM32; the RV1106 only reaches the bus while docked) → safety state NORMAL
7. **IDLE mode** → Thermal/Fan task at 1 Hz, heartbeat and dock monitoring, awaiting commands; stir motor enumerated on FDCAN2 once the Safety Monitor closes K_SU (≈ 300 ms PSU start-up, motor boot frame, command timeout configured) and left disabled; K_SU opens again after 60 s parked (FR-MCU-010a)

---

## 5. Communication Protocols

### 5.1 Firmware Update over CAN (and debug console)

There is no UART between the RV1106 and the CSC STM32 — they are in different units, joined only by the dock. Firmware reaches the CSC STM32 over the isolated CAN bus, streamed by the RV1106 through the DU STM32 gateway. (The DU STM32 itself is flashed over its USART1 host link by the ST system bootloader, §10.6.)

**CAN bootloader (in-application, OpenBLT-style):**
- IDs: 0x7E0 FW_UPDATE_REQ (AP → STIR: seq, op, 5 data bytes) and 0x7E8 FW_UPDATE_RSP (STIR → AP: seq, op, result, 4 data bytes); lowest priority on the bus, used in update mode only
- Ops: `ERASE` (bank/sector range, allowed only in the safe state with heater off, stir motor disabled, no cook running), `WRITE` (address-sequenced 5-byte chunks into the inactive flash bank, 0x7E8 acks each chunk by seq), `VERIFY` (RV1106 sends the image CRC-32; bootloader recomputes over the written bank with the hardware CRC unit), `BOOT` (swap banks via the dual-bank option bits and reset only after a successful VERIFY; previous image kept otherwise)
- The RV1106 swupdate handler streams the `.bin` (see [[04-MPU-Functional-Specification]] FR-MPU-062); a lost or NAK'd chunk is retried by seq; an aborted update leaves the running bank untouched
- HB_AP, E_STOP and HEAT_STATUS handling stay active during an update; an E_STOP or heartbeat loss aborts it

**Bench and factory paths:**
- USB-C J_USB on the CSC: ST USB DFU (and a CDC console) — hold SW_BOOT and pulse SW_RST. BOOT0 on the G0 is multiplexed on PA14 (PA14-BOOT0, shared with SWCLK) and is ignored unless option bit `nBOOT_SEL` = 0; program `nBOOT_SEL` = 0 (keep `nBOOT1` = 1) over SWD once at factory programming. A blank part boots the system bootloader anyway (empty-flash check), so first-time programming works over USB DFU without this step
- J_SWD (2×5 1.27 mm): factory programming and debug
- Debug console: USART2 (PA2 TX / PA3 RX) on the J_DBG 3-pin header, 1,000,000 baud, 8N1, 3.3 V; no runtime protocol
- NUCLEO-G0B1RE prototype caveat: PA2/PA3 are routed to the ST-LINK VCP by default on the MB1360 board, which serves as J_DBG there

### 5.2 CAN Bus Protocol (shared bus: DU STM32 for the RV1106, CSC STM32, heating unit)

Identifiers are owned by [[02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]; this is the MCU view.

| CAN ID | Direction | DLC | MCU behaviour |
|--------|-----------|-----|---------------|
| 0x001 E_STOP | any ↔ all | 2 | Received: run the E-stop sequence (§7.3). Sent (src_node = 2) on any CRITICAL → E_STOP transition |
| 0x010 HB_AP | RV1106 → all | 5 | Resets the 5 s heartbeat timer |
| 0x100 HEAT_SET_TEMP | RV1106 → unit | 4 | Never sent by the MCU; observed only for logging |
| 0x101 HEAT_ON_OFF | RV1106 or MCU → unit | 1 | MCU sends 0 on thermal fault, heartbeat loss, E-stop |
| 0x103 HEAT_SET_POWER | RV1106 → unit | 2 | Never sent by the MCU; observed only for logging |
| 0x180 HEAT_STATUS | unit → all | 8 | surface_temp, element_temp and fault_flags feed the safety monitor; pot_detected and surface_temp feed TELEMETRY flags |
| 0x181 HEAT_FAULT | unit → all | 4 | Mapped to CAN_FAULT handling (§7.2) |
| 0x202, 0x221–0x225 | RV1106 → MCU | 1–6 | SET_STIR, SET_SPEED, ARM_STOP, ARM_HOME, ARM_STATUS, SET_RAMP (byte 0 = seq) |
| 0x260 SET_EXHAUST | RV1106 → MCU | 2 | seq, duty_pct — fan duty 0–100 % |
| 0x261 GET_EXHAUST | RV1106 → MCU | 1 | seq → ACK data: duty_pct, rpm1, rpm2 |
| 0x262 EXHAUST_AUTO | RV1106 → MCU | 2 | seq, stage_id — duty from the firmware stage table |
| 0x310 TELEMETRY | MCU → RV1106 | 8 | motor_rpm (uint16), motor_current_dA (int16), safety_state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok), error_code, seq — 20 Hz |
| 0x312 STATUS | MCU → RV1106 | 8 | safety_state, error_code, flags, fault_detail — on change and on safe-hold entry/exit (no batt_mV) |
| 0x3FF ACK/NAK | MCU → RV1106 | 3–8 | seq, cmd_type, result_code, data[0..4] |
| 0x7E0 FW_UPDATE_REQ | RV1106 → MCU | 7 | seq, op (ERASE / WRITE / VERIFY / BOOT), 5 data bytes — update mode only (§5.1) |
| 0x7E8 FW_UPDATE_RSP | MCU → RV1106 | 7 | seq, op, result, 4 data bytes |

Not on the bus: 0x220 SET_LED, 0x226 SET_BUZZER, the 0x230–0x239 dispensing block, 0x311 DU_STATUS and 0x3FE DU_ACK are DU-local frames on the RV1106 ↔ DU STM32 host link, terminated on the DU STM32 (§10.5); the CSC never sees them.

- Reference heater IDs follow [[../05-Subsystems/01-Electric-Heating|Electric Heating]] §3.2 and are adapted to the chosen heating unit
- Timeouts: HB_AP missing 5 s → safe state; no HEAT_STATUS for 500 ms or FDCAN bus-off → CAN_FAULT (relay open, since the heater cannot be commanded)
- Pot detection: pot-absent in HEAT_STATUS is flagged in TELEMETRY; the RV1106 pauses heating
- Dock: DOCK_SENSE_B open → safe hold with STATUS error_code 0x17 (§2.9); the DU node leaves the bus physically at the same moment, so HB_AP loss follows within 5 s

### 5.3 I2C Protocol

Removed — the CSC has no I2C devices (I2C1 pads unpopulated, §3.2).

---

## 6. Power Management

### 6.1 Power Supply

- Input: J_12V_IN (XT30 2-pin) — 12V_IN from a dedicated Mean Well LRS-35-12 (12 V, 3 A, 36 W) in the CS base, AC input unswitched (live whenever the appliance is on); F1 2 A polyfuse, SS34 reverse protection, SMBJ12A TVS, 100 µF bulk for fan start-up and relay pull-in. Neither Mean Well LRS-75-24 powers the CSC, and nothing is tapped from the heating unit: the OEM unit is not opened, Epicura uses only its CAN port and the K_SAFE relay on its AC inlet loom
- Rails on the CSC: 12V_IN feeds the fans and the two relay coils K_SAFE / K_SU directly (no 24 → 12 V buck); one MP1584EN 12 → 5 V → AMS1117-3.3 (SOT-223, 800 mA max) for the STM32 and the ISO1050DUB #1 / #3 logic sides, and the B0505S-1WR3 #1 / #2 inputs; 5V_USB from J_USB OR'd into the 3.3 V LDO input for bench programming (DFU with J_12V_IN disconnected)
- No battery: the 2S pack is in the Dispensing Unit and keeps the RV1106 alive through an outage; on mains loss all three PSUs, the CSC, the fans, the relays and the dock 24 V go down together, and the STM32 reboots in < 1 s when 12V_IN returns with mains (K_SAFE is already de-energised). Because the LRS-35-12's AC input is unswitched, the CSC boots as soon as the appliance is on, independent of K_SAFE and K_SU
- 24 V for the Dispensing Unit: J_DU_IN (XT30) from the LRS-75-24 #1 in the CS base — F_DU 3 A polyfuse, SS54 reverse protection, SMBJ24A TVS → 24V_DU, which goes to Q_DOCK → F_DOCK → J_DOCK pin 1 (2 A) only, off at reset; nothing on the CSC runs from it. The LRS #1 −V is bonded to the CSC ground at J_DU_IN (the dock's sense lines and charge return need the DU and CS grounds common while docked). The Stirring Unit's 24 V is not on this input: LRS-75-24 #2 (floating 24V_SU / GND_SU) passes through J_SU_IN → F_SU 5 A → J_STIR_PWR and is cut by K_SU on its AC input (off at reset)
- Budgets: 12V_IN ~1.3 A typical / 1.4 A peak (two fans 1.0 A, two coils 0.08 A, 5 V buck ≈ 0.25 A in; ≈ 17 W of the LRS-35-12's 36 W); 24V_DU ~0.6 / 1.6 A; 24V_SU 1.0 / 3.0 A
- Decoupling: 10 µF input, 10 µF output, 100 nF per VDD pin
- Typical consumption: ~0.15 W (64 MHz, all peripherals active)

### 6.2 Power States

| State | Description | Current (3.3 V) |
|-------|-------------|-----------------|
| Active | All tasks running, CAN + motor + fans active | ~150 mA |
| Idle | Thermal/Fan task at 1 Hz, awaiting commands | ~80 mA |
| E_STOP | Relay open, outputs off, minimal processing (the buzzer is on the DU) | ~100 mA |
| Reset | After IWDG timeout, re-initializing | ~50 mA |

---

## 7. Safety & Fault Handling

### 7.1 Safety Mechanisms

| Mechanism | Implementation | Response Time |
|-----------|---------------|---------------|
| E-stop button | PB2 EXTI interrupt (highest NVIC priority) | <1 ms |
| Safety relay | PB0 → N-MOSFET → K_SAFE coil (NC relay, fail-safe open); pilots the power relay on the heating unit's AC inlet loom — the CSC, on its own PSU, stays powered | <5 ms |
| Hardware watchdog (IWDG) | 5 s timeout, kicked in safety monitor task | 5 s (worst case) |
| Class B self-tests | X-CUBE-CLASSB: CPU/RAM/flash/clock/program-flow checks at boot; RAM and flash CRC re-checked periodically | Fault → safe state at next safety tick |
| Thermal cutoff (surface) | HEAT_STATUS surface_temp > 230 °C → E_STOP | ≤200 ms (status interval + poll) |
| Thermal cutoff (CAN element) | CAN element over-temp → E_STOP | ≤500 ms (CAN status interval) |
| Stir motor | Motor disable on FDCAN2 + K_SU off (SU PSU de-energised) on E-stop / heartbeat loss / FDCAN2 fault / DU undock | ≤10 ms (disable frame); motor de-energised ≤ 50 ms after K_SU opens |
| Dock sense | DOCK_SENSE_B (PB3) high → safe hold: HEAT_ON_OFF = 0, stir disable, K_SU off, Q_DOCK off (dock pads de-energised), STATUS DU_UNDOCKED | ≤100 ms (safety-monitor cycle); Q_DOCK ≤ 1 ms |
| CAN fault | No HEAT_STATUS for 500 ms or bus-off → relay open (heater cannot be commanded), alert | 500 ms |
| RV1106 heartbeat loss | No HB_AP (0x010) for 5 s → HEAT_ON_OFF = 0, relay open, safe state | 5 s |
| Fan stall | Tachometer < 300 rpm for 2 s with duty > 0 → fan1_ok / fan2_ok cleared (FAN_STALL), STATUS; RV1106 reduces heater power | ≤3 s |

### 7.2 Fault Table

| Fault Code | Name | Severity | Action |
|------------|------|----------|--------|
| 0x01 | OVER_TEMP_SURFACE | Critical | E_STOP, cut relay, log (HEAT_STATUS surface_temp > 230 °C) |
| 0x02 | OVER_TEMP_ELEMENT | Critical | E_STOP, cut relay, log |
| 0x03 | E_STOP_PRESSED | Critical | E_STOP, cut relay; the RV1106 sounds the buzzer (on the DU) from STATUS |
| 0x04 | CAN_FAULT | Critical | Open relay (heater unreachable on the bus), alert RV1106 when the bus returns |
| 0x05 | RV1106_HEARTBEAT_LOSS | Critical | HEAT_ON_OFF = 0, relay open, stir motor disabled + K_SU off (safe state) |
| 0x10 | STIR_STALL | Warning | Disable motor, retry 3×, alert RV1106 (motor-reported current / velocity error) |
| 0x15 | STIR_CAN_FAULT | Warning | FDCAN2 bus-off or no motor feedback 200 ms: disable, K_SU off, alert RV1106 |
| 0x17 | DU_UNDOCKED | Info | DOCK_SENSE_B open → safe hold (HEAT_ON_OFF = 0, stir disable, K_SU off, Q_DOCK off); cleared when docked and HB_AP returns |
| 0x20 | CAN_TX_TIMEOUT | Info | Retry 3×, then CAN_FAULT |

Removed from the CSC image (now DU STM32 codes, §11.7, same numbers): 0x11 SLD_TANK_ABSENT (was SLD_LOAD_CELL_DRIFT), 0x12 DSB_STALL, 0x13 SLD_DISPENSE_ERROR, 0x14 BATTERY_FAULT, 0x16 POWER_FAIL, 0x21 I2C_NACK. Codes are not reused across images.

### 7.3 E-Stop Sequence

1. **PB2 EXTI fires** (or E_STOP 0x001 received on the CAN bus)
2. Safety relay opened (PB0 LOW → K_SAFE de-energizes → AC cut to the whole heating unit at its inlet; the CSC stays up on its own LRS-35-12)
3. Stir motor: disable frame on FDCAN2, K_SU (PB4) off — SU PSU de-energised; fan PWM to 0 %; Q_DOCK off
4. CAN: send HEAT_ON_OFF = 0 (0x101) and broadcast E_STOP (0x001, src_node = 2) on FDCAN1 — belt-and-suspenders with the relay
5. STATUS (0x312) sent on the bus: `safety_state = E_STOP`; the RV1106 sounds the buzzer (SET_BUZZER to the DU STM32) and shows the alert — the CSC has no buzzer
6. **Hold state** — only IWDG kick continues; no commands accepted
7. **Reset** — PB2 debounce clears → re-init → wait for HB_AP → NORMAL

---

## 8. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Motor control period | 20 ms ± 0.5 ms | TIM interrupt jitter |
| E-stop latency | <1 ms | PB2 edge → relay GPIO toggle |
| CAN command dispatch | <1 ms | RX FIFO interrupt → ACK queued |
| CAN command round-trip | <10 ms | RV1106 command → ACK on the bus |
| Stir motor command latency | < 20 ms | SET_STIR received → first FDCAN2 velocity frame |
| Stir speed accuracy | ±5 RPM | Motor-reported vs. external tachometer |
| Safe hold on undock | <100 ms (Q_DOCK < 1 ms) | DOCK_SENSE_B edge → HEAT_ON_OFF 0 / K_SU off / Q_DOCK off |
| Fan duty latency | <50 ms | SET_EXHAUST received → PWM duty applied |
| CAN firmware update (512 KB image) | <3 min | ERASE → BOOT over 0x7E0/0x7E8 at 500 kbps |
| FreeRTOS CPU utilization | <70% at 64 MHz | Idle task runtime measurement |
| Flash usage | <256 KB | Linker map |
| SRAM usage | <96 KB (of 144 KB) | Stack + heap analysis |

---

## 9. Dependencies & Constraints

### 9.1 Hardware Dependencies

- Cooking Surface Controller (CSC) v1.0 (~100 × 70 mm, 4-layer with two isolation slots, in the CS base beside the three Mean Well PSUs, powered from its own LRS-35-12 on J_12V_IN) provides the STM32, 8 MHz HSE, LDO, one MP1584EN (12 → 5 V), both isolated CAN transceivers (ISO1050DUB #1, #3) with their B0505S-1WR3 #1 / #2 supplies, Q_DOCK / Q_RLY / Q_KSU, the two G5V-2 pilot relays (K_SAFE, K_SU), the 24V_DU chain (J_DU_IN → Q_DOCK), the SU island (J_SU_IN → F_SU → J_STIR_PWR), fan MOSFETs and twelve connectors: J_12V_IN, J_DU_IN, J_SU_IN, J_CAN_HEAT, J_CAN_STIR, J_STIR_PWR, J_DOCK, J_FAN, J_SAFE, J_DBG, J_SWD, J_USB
- Isolated CAN port on the CSC (ISO1050DUB #1 for FDCAN1, J_CAN_HEAT to the heating unit, J_DOCK pins 3–5 to the DU STM32's non-isolated SN65HVD230 on the Unified PCB v5.0 in the Dispensing Unit; GND_ISO tied to DU ground there, pin 6 reserved)
- Second isolated CAN port on the CSC (ISO1050DUB #3 + B0505S #2 on FDCAN2, J_CAN_STIR, SU domain 5V_ISO2 / GND_SU) and the SU's own 24 V (LRS-75-24 #2 via J_SU_IN → F_SU → J_STIR_PWR, cut by K_SU on the PSU's AC input), bundled into the stirring-unit harness to J_SU; GND_SU is never bonded to the CS ground
- Dock block in the CS left pillar (8-contact magnetic pogo, J_DOCK) for DOCK_24V, the isolated bus and the two sense lines
- No HX711, WS2812B, 74AHCT1G125, PCA9685, PCF8574, INA219 or battery on this board (all on the Unified PCB v5.0 under the DU STM32, or dropped)

### 9.2 Firmware Dependencies

- STM32G0xx HAL drivers (STM32CubeMX generated): GPIO, ADC, TIM, USART, FDCAN, CRC, FLASH (dual-bank swap)
- FreeRTOS 10.x kernel (Cortex-M0 port) + CMSIS-RTOS2 wrapper
- X-CUBE-CLASSB self-test library
- CMSIS-DSP library (fixed-point filtering)
- CRC-32 (hardware CRC unit) for image verification; CRC-16/CCITT lookup table
- CAN message codec (ID map, payload packing, seq/ACK)
- CAN bootloader (OpenBLT-style in-application loader on 0x7E0/0x7E8: ERASE / WRITE / VERIFY / BOOT into the inactive flash bank)
- `stir_motor.c`: wrapper for the stirring motor's CAN protocol on FDCAN2 (enable, velocity, position, feedback, timeout configuration)
- `exhaust.c`: fan PWM, tachometer capture, EXHAUST_AUTO stage table
- No HX711 or WS2812B driver

### 9.3 Constraints

- MISRA C compliance for safety-critical tasks (safety monitor, E-stop handler, CAN command dispatcher, heater off-switch)
- No dynamic memory allocation after boot (all FreeRTOS objects static)
- No floating-point in control or safety paths (the Cortex-M0+ has no FPU; float is software-emulated), use q15/q31 fixed point
- Both CAN buses require 120 Ω termination at both ends; FDCAN1 (isolated port 1) and FDCAN2 (isolated port 2, SU domain) share nothing; the dock → Unified PCB stub on FDCAN1 must stay ≤ 30 cm
- Q_DOCK must never be on with DOCK_SENSE_B high (exposed pogo pins)

### 9.4 Cross-References

| Topic | Document |
|-------|----------|
| RV1106 MPU spec | [[04-MPU-Functional-Specification]] |
| State machine details | [[03-Main-Loop-State-Machine]] |
| Software architecture | [[02-Controller-Software-Architecture]] |
| Unified PCB design | [[01-Unified-PCB-Design]] |
| Dispensing subsystems (DU STM32-driven, §10) | [[03-Ingredient-Dispensing]] |
| Exhaust fans | [[05-Exhaust-Fume-Management]] |
| Hardware architecture | [[01-Epicura-Architecture]] |
| Technical specifications | [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications]] |

---

## 10. Dispensing Unit Instance (DU STM32)

### 11.1 Purpose and Scope

The second STM32G0B1RET6 sits on the Unified PCB v5.0 in the lift-off Dispensing Unit, beside the Luckfox Pico Zero slot, and is built from the same `epicura-firmware` tree as the `du` image (shared HAL, FreeRTOS, MISRA C rules, CAN codec, X-CUBE-CLASSB start-up self-tests). It exists because the Pico Zero header cannot drive the camera, LCD, SLD, CID and FID at once. It owns:

- the **host link** to the RV1106 (USART1, 921,600 baud, COBS-framed CAN-shaped frames with CRC-16) and the **DU's CAN node** (FDCAN1 + a non-isolated SN65HVD230 over the dock; the isolation is on the CSC's port), acting as a transparent gateway — on the bus the DU is still the AP node (src_node 3) and the ID map of [[02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]] is unchanged;
- **ingredient dispensing** (FID / CID servo carousels over I2C1; the SLD pumps on TIM3 with Hall tach metering, the tank present / low Hall switches and the prime routine on PC0–PC5);
- the **white LED ring** and the **piezo buzzer**;
- **battery and dock monitoring** (INA219 #2, TP5100 CHRG/STDBY, DOCK_SENSE_A, DOCK_PWR_OK), reported as DU_STATUS.

It has **no safety authority**: it never originates HEAT_ON_OFF or E_STOP (it forwards the RV1106's), it does not open any relay and nothing on the CS depends on it beyond the HB_AP frames it relays. Its only autonomous action is to drop its own dispensers when the RV1106 stops talking. Class B is limited to the start-up self-tests; the runtime safety monitor of §2.7 does not run in the `du` image.

### 11.2 Pin Assignment (LQFP-64, DU instance)

| Pin | Function | Signal | Circuit |
|-----|----------|--------|---------|
| PA9 / PA10 | USART1 TX / RX | HOST_TX / HOST_RX | ↔ J_AP pin 10 (UART2 RX) / pin 8 (UART2 TX); 33 R series; also the ST system-bootloader UART |
| PA14 (SWCLK / BOOT0) | BOOT0 | BOOT0 | ← J_AP GPIO 32, 10k pull-down; `nBOOT_SEL` = 0 programmed over SWD at factory |
| NRST | reset | NRST | ← J_AP GPIO 38 (open-drain), 10k pull-up, 100 nF |
| PA13 / PA14 | SWDIO / SWCLK | SWD | J_SWD 2×5 1.27 mm (bench and factory) |
| PB8 / PB9 | FDCAN1 RX / TX (AF3) | CAN 500 kbps | SN65HVD230 R / D (3.3 V, non-isolated, Rs 10k to GND); CAN_H / CAN_L on dock pads 3–4, GND_ISO (pad 5) tied to DU ground, pad 6 not connected |
| PB6 / PB7 | I2C1 SCL / SDA | I2C1 400 kHz | PCA9685 0x41, PCF8574 #2 0x21, INA219 #1 0x40, INA219 #2 0x44; 4.7k pull-ups |
| PA6 / PA7 | TIM3_CH1 / CH2 | PWM_PUMP_OIL / PWM_PUMP_WATER | TB6612 PWMA / PWMB via 100 R, 20 kHz |
| PA8 | TIM1_CH1 | PWM_LED | Q_LED gate (IRLML6344) via 100 R, 1 kHz |
| PA4 | TIM14_CH1 | PWM_BUZZER | Q_BUZZ gate (2N7002) via 100 R, 2–4 kHz |
| PB0 | GPIO out | PCA9685_OE | 10k pull-up: servos off at boot, in reset and on host loss |
| PB3 | GPIO EXTI | DOCK_SENSE_A | J_DOCK pad 7, 10k pull-up, low = docked |
| PB5 | GPIO EXTI | DOCK_PWR_OK | Q_PWR drain, 10k pull-up, low = DOCK_24V present |
| PC0 / PC1 | GPIO EXTI0 / EXTI1 | SLD_OIL_TACH / SLD_H2O_TACH | Pump Hall tachs (J_SLD 7 / 8), open-drain, 10k pull-up + 100 R; 2 pulses/rev ≈ 0.2 mL (oil), 1 pulse/rev ≈ 0.25 mL (water) |
| PC2 / PC4 | GPIO EXTI2 / EXTI4 | TANK_OIL_PRESENT / TANK_H2O_PRESENT | Fixed-magnet Hall in the tank bays (J_SLD 9 / 11); rising edge (debounced 100 ms) arms the prime routine |
| PC3 / PC5 | GPIO in, polled 1 Hz | TANK_OIL_LOW / TANK_H2O_LOW | Float-magnet Hall (J_SLD 10 / 12); low at ≈ 20 mL (oil) / ≈ 50 mL (water) left |
| PC7 | GPIO out | Status LED | green, 330 R (PCF8574 #2 P2 freed) |
| PF0 / PF1 | HSE | 8 MHz | Y1 + 2× 15 pF |
| PC14 / PC15 | LSE pads | — | unpopulated |
| PB12 / PB13 | FDCAN2 | — | unused (no second CAN port on the DU) |
| PA11 / PA12 | USB | — | not used (no USB-C on the DU STM32) |
| all others | — | Available | |

All PWM lines keep 10k pull-downs. PCF8574 #2 keeps its v4.0 map less the solenoids (P0/P1 spare since 2026-11-05, P3/P5 pump direction, P4 6V_DSP enable, P6/P7 CHRG/STDBY). Power: 3.3 V from the DU's AMS1117-3.3, ≈ 30 mA; the 2S pack keeps the DU STM32 alive when the unit is lifted or mains fails.

### 11.3 Task Table (`du` image)

| Task | Rate | Priority | Stack | Description |
|------|------|----------|-------|-------------|
| Link/Gateway | event-driven (USART1 DMA idle-line, FDCAN1 RX FIFO) | High (3) | 1024 B | COBS/CRC codec, ID routing between the host link and FDCAN1, DU-local command dispatch, 0x3FE replies, HB_AP watchdog (5 s), bus-off recovery; end-to-end latency ≤ 5 ms |
| Dispense | 50 Hz while a move is active | Medium (2) | 768 B | PCA9685 ramped moves, 6V_DSP enable, INA219 #1 stall window, SLD open-loop metering (tank Hall gating, prime routine, tach pulse count to target, no-flow rules), prime / query / preflight / cal / home / status |
| Monitor | 1 Hz + EXTI | Low (1) | 256 B | INA219 #2 → state of charge, CHRG/STDBY, DOCK_SENSE_A, DOCK_PWR_OK → DU_STATUS (0x311); LED ring duty and buzzer tones; IWDG kick |

### 11.4 Host Link and Gateway Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-DU-010 | Host link on USART1 (PA9/PA10) to RV1106 UART2 at 921,600 baud 8N1; every frame is CAN-shaped (`id` uint16 LE, `dlc`, `data[0..7]`, CRC-16/CCITT-FALSE over id..data), COBS-encoded, 0x00-terminated, ≤ 14 bytes on the wire | Must | Loopback test at 6,000 frames/s with zero CRC errors; a corrupted frame is dropped and the decoder re-synchronises on the next 0x00 |
| FR-DU-011 | Gateway routing: frames from the link whose ID is DU-local (0x220, 0x226, 0x230–0x239) are executed locally and never transmitted on CAN; every other ID (0x001, 0x010, 0x100–0x103, 0x202, 0x221–0x225, 0x260–0x262, 0x7E0) is transmitted on FDCAN1 unchanged | Must | No DU-local ID ever appears on the bus (bus-analyser check); forwarded frames are byte-identical |
| FR-DU-012 | Bus frames matching the AP filter set (0x00x, 0x01x, 0x18x, 0x3xx, 0x7E8) are forwarded up the link unchanged via FDCAN1 hardware filters | Must | TELEMETRY at 20 Hz and HEAT_STATUS at 10 Hz reach the RV1106 with ≤ 5 ms added latency |
| FR-DU-013 | FDCAN1 classic CAN 2.0B, 500 kbps, 11-bit IDs, no termination on the DU board (stub ≤ 30 cm from the dock) | Must | Bit timing from the 64 MHz kernel clock; error counters stay at zero on the bench bus |
| FR-DU-014 | HB_AP watchdog: no HB_AP (0x010) from the link for 5 s → 6V_DSP off, PCA9685 OE high, pumps off, LED ring off; DU_STATUS continues; recovers on the next HB_AP | Must | Measured 5.0 ± 0.1 s; no dispenser moves while the link is silent |
| FR-DU-015 | Bus-off (DU lifted) → DU_STATUS can_bus_ok = 0 within one frame; automatic bus-off recovery when re-docked; frames queued for the bus while off are discarded, not replayed | Must | Lift / re-dock 100× without a stuck controller |
| FR-DU-016 | The DU STM32 never originates E_STOP, HEAT_ON_OFF, heater setpoints or any 0x2xx command; it only forwards the RV1106's | Must | Code review + bus log: every AP-sourced frame has a matching link frame |

### 11.5 DU-Local Message Handling

| ID | Message | Dir | DLC | DU STM32 behaviour |
|----|---------|-----|-----|--------------------|
| 0x220 | SET_LED | AP → DU | 2 | seq, duty_pct (0 OFF / 30 NIGHT / 100 CAPTURE) → TIM1 duty; ACK |
| 0x226 | SET_BUZZER | AP → DU | 5 | seq, tone_hz (uint16), duration_ms (uint16) → TIM14; ACK on start |
| 0x230 | DISPENSE_FID | AP → DU | 3 | seq, box_id, qty (¼ tsp units) → Dispense task; ACK at completion with actual qty |
| 0x231 | DISPENSE_CID | AP → DU | 2 | seq, slot_id; NAK if slot_id is not ascending within the session |
| 0x232 | DISPENSE_SLD | AP → DU | 4 | seq, channel (0 oil / 1 water), target_ml (uint16); prime first if pending; ACK at completion with actual_ml (uint16) + primed_ml; NAK SLD_TANK_ABSENT / SLD_LOW_LEVEL / NOT_DOCKED |
| 0x233 | SLD_PRIME | AP → DU | 2 | seq, channel → run the prime routine (FR-DU-036); ACK with primed_ml; NAK NOT_DOCKED while lifted |
| 0x235 | QUERY_SLD | AP → DU | 2 | seq, channel → ACK data: flags (bit0 present, bit1 low, bit2 prime_pending), cal_ul (uint16), last_ml (uint16) |
| 0x236 | PREFLIGHT | AP → DU | 1 | seq → ACK data: result bitmap (servos reachable, rail OK, each SLD tank present and not low) |
| 0x237 | SLD_CAL | AP → DU | 4 | seq, channel, cal_ul (uint16, µL per tach pulse); held in RAM, re-sent by the RV1106 at every boot |
| 0x238 | DISPENSER_HOME | AP → DU | 1 | seq → home every carousel, one servo at a time |
| 0x239 | DISPENSER_STATUS | AP → DU | 1 | seq → ACK data: dsp_state, last_error, rail_mA |
| 0x311 | DU_STATUS | DU → AP | 8 | batt_mV (uint16), batt_mA (int16), soc_pct, flags (bit0 docked, bit1 dock_power, bit2 charging, bit3 charge_done, bit4 dsp_rail_on, bit5 dsp_busy, bit6 can_bus_ok, bit7 sld_low — a tank low or absent), error_code, seq — 1 Hz and on any flag change |
| 0x3FE | DU_ACK / NAK | DU → AP | 3–8 | seq, cmd_type (low byte of the command ID), result_code, data[0..4]; status queries answered within 50 ms, moves at completion or on fault |

0x234 is reserved. 0x3FF remains the CSC's ACK; the RV1106 tells the two apart by ID. Command frames carry `seq` in byte 0 like every bus command; one dispenser command is in flight at a time (a second one is NAK'd BUSY).

### 11.6 Dispensing, Peripheral and Update Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-DU-030 | Servo moves (FID / CID: DS3218, MG996R ×2, MG90S) through the PCA9685: ramped ≤ 3°/tick at 50 Hz, one servo at a time; 6V_DSP enabled (PCF8574 #2 P4) for the move only; PCA9685 OE high until the Dispense task starts | Must | Rail current per [[03-Ingredient-Dispensing]] §7; no two servos move together |
| FR-DU-031 | Stall detection: INA219 #1 current > 2.5 A for 300 ms, or 3 s move timeout, or I2C NACK → retry once with 10° back-off → NAK DSB_STALL (0x12) | Must | Blocked carousel yields DSB_STALL within 3.5 s |
| FR-DU-032 | SLD open-loop metering: refuse unless the tank is present and not low and the DU is docked; prime first if pending; run the pump (TIM3 PWM, oil ≈ 100 %, water PWM reduced below 50 mL) and count Hall tach pulses on EXTI until target_pulses = target_ml × 1000 / cal_ul; stop, rail off, actual_ml = pulses × cal_ul / 1000 and primed_ml in the ACK | Must | ±5 % on 10 mL oil and 300 mL water after calibration; 500 mL water in ≤ 40 s; no pulse ever missed or doubled at any PWM |
| FR-DU-033 | CID slot_id must be ascending within a session; otherwise NAK | Must | Out-of-order request rejected without a move |
| FR-DU-034 | SLD_CAL, QUERY_SLD, PREFLIGHT, DISPENSER_HOME and DISPENSER_STATUS as in §11.5; cal_ul defaults to 200 µL (oil) / 250 µL (water) until SLD_CAL arrives | Must | Preflight completes in < 3 s; QUERY_SLD answered within 50 ms |
| FR-DU-035 | SLD faults: tank-present Hall low at command start → SLD_TANK_ABSENT (0x11, NAK); float Hall low at command start → SLD_LOW_LEVEL (0x1A, NAK), during a dose → finish the dose, set DU_STATUS bit7; no tach pulse within 1 s of pump start, pulse rate < 25 % of nominal for 2 s, or INA219 #1 pump current outside 50 mA–1.5 A → pump off, SLD_DISPENSE_ERROR (0x13); DISPENSE_SLD or SLD_PRIME while DOCK_SENSE_A is high → NOT_DOCKED (0x23) | Must | Each fault reported in the NAK result and DU_STATUS error_code; a dry pump stops within 1.5 s |
| FR-DU-036 | Prime routine: `prime_pending[channel]` set at boot and on a TANK_x_PRESENT rising edge (debounced 100 ms); executed before the next DISPENSE_SLD on that channel or on SLD_PRIME: pump at 50 % PWM for N_PRIME pulses (oil 15 ≈ 3 mL, water 32 ≈ 8 mL), tach pulses must appear within 2 s, primed_ml reported in the ACK, flag cleared; never while lifted | Must | A re-seated tank primes exactly once; the following dose is within ±5 % |
| FR-DU-037 | Tach handling: EXTI0 / EXTI1 edge counters with a 2 ms glitch filter, nominal rate learned from the calibrated pump (oil ≈ 2–5 Hz, water ≈ 50–70 Hz); counters readable by QUERY_SLD (last_ml) | Must | Verified against a bench optical counter at every PWM setting |
| FR-DU-040 | LED ring duty on SET_LED (TIM1 → Q_LED, 1 kHz); off at boot, on host loss and when lifted | Must | OFF / NIGHT / CAPTURE within 20 ms of the command |
| FR-DU-041 | Buzzer tones on SET_BUZZER (TIM14 → Q_BUZZ, 2–4 kHz); a new command pre-empts the current tone | Should | Tone within 20 ms |
| FR-DU-050 | Battery monitor: INA219 #2 (bus voltage on BAT+, signed current) at 1 Hz; state of charge from voltage + coulomb count; batt_mV < 6.4 V → DU_STATUS error_code BATTERY_LOW warning, < 6.2 V → halt-request flag so the RV1106 checkpoints and halts; self-test at boot (5.5–8.5 V) else BATTERY_FAULT (0x14) | Must | Reported within 1 s of the threshold |
| FR-DU-051 | Charger status: CHRG / STDBY (PCF8574 #2 P6/P7) → charging / charge_done flags; both inactive with the pack < 8.0 V for > 10 min while dock_power = 1 → BATTERY_FAULT | Should | Flags match the TP5100 LEDs |
| FR-DU-052 | Dock sense: DOCK_SENSE_A (PB3) and DOCK_PWR_OK (PB5) on EXTI → docked / dock_power flags, DU_STATUS sent on every change (debounce 20 ms); dock_power lost while docked → POWER_FAIL (0x16) info code | Must | Flag change reaches the RV1106 ≤ 30 ms after the edge |
| FR-DU-060 | Firmware update by the RV1106 through the ST system bootloader: BOOT0 (GPIO 32) high, NRST (GPIO 38) pulse, bootloader protocol on USART1, verify, BOOT0 low, reset; no in-application bootloader; J_SWD for bench and factory; `nBOOT_SEL` = 0 programmed once at factory (a blank part enters the system bootloader regardless) | Should | Full image (≤ 256 KB) flashed and verified in < 60 s; a failed update leaves a part that the RV1106 can re-flash |
| FR-DU-061 | While in the bootloader or in reset the dispensers are safe by hardware: PCA9685 OE pull-up, PWM pull-downs, 6V_DSP switch off by the PCF8574 reset state | Must | Measured: no servo twitch, rail off during a flash |
| FR-DU-070 | IWDG (LSI) armed at boot, kicked by the Monitor task only when Link/Gateway and Dispense have both run in the last 500 ms; Class B start-up self-tests (CPU, flash CRC, SRAM march) from X-CUBE-CLASSB; no runtime Class B | Must | A stuck task resets the MCU within 1 s; boot-time self-test < 100 ms |

### 11.7 DU Fault and Result Codes

Reported in 0x3FE `result_code` and in DU_STATUS `error_code`; numbers are the CSC-era codes, kept so the RV1106 fault table does not change.

| Code | Name | Severity (RV1106 action) | DU STM32 action |
|------|------|--------------------------|-----------------|
| 0x11 | SLD_TANK_ABSENT | Warning → prompt (seat the tank) | Refuse the SLD command, report |
| 0x12 | DSB_STALL | Warning → pause | Retry once, then rail off, report |
| 0x13 | SLD_DISPENSE_ERROR | Warning → pause | Pump off, report (no tach / slow tach / pump current out of window) |
| 0x14 | BATTERY_FAULT | Warning (banner, cooking allowed) | Report |
| 0x16 | POWER_FAIL | Info (dock power lost while docked) | Report; nothing to switch |
| 0x18 | BATTERY_LOW | Warning at 6.4 V; halt request at 6.2 V | Report |
| 0x19 | HOST_LINK_LOST | — (self-detected) | Dispensers and LED off after 5 s without HB_AP |
| 0x1A | SLD_LOW_LEVEL | Warning → prompt refill | Refuse the SLD command |
| 0x21 | I2C_NACK | Warning | Retry 3×, then the owning fault above |
| 0x22 | BUSY | NAK only | Second dispenser command while one is in flight |
| 0x23 | NOT_DOCKED | NAK only | DISPENSE_SLD or SLD_PRIME while the DU is lifted (nozzle not over the pot); the bench calibration flow is the exception and is gated on the RV1106 side |

The RV1106 side adds DU_LINK_LOST (no DU_STATUS for 3 s, see [[04-MPU-Functional-Specification]] §7.2).

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-16 | Manas Pradhan | Initial document; subsequent single-board revisions recorded in the header (STM32G474RE → STM32G0B1RE, CAN host link, CAN servo stir motor, 2S battery monitoring) |
| 1.1 | 2026-11-04 | Manas Pradhan | Three-unit architecture: STM32 moved to the Cooking Surface Controller (CSC) in the CS base; four FreeRTOS tasks (Motor Control, Safety Monitor, CAN Comms, Thermal/Fan); dispensing (§2.5), sensor polling, load cells, LED ring (§2.8), buzzer, battery/POWER_FAIL, I2C peripherals and the UART service link retired (moved to the RV1106); added dock interface (DOCK_SENSE_B PB3 safe hold, Q_DOCK PB5, §2.9/§3.4), exhaust-fan FRs (0x260–0x262, FAN_STALL, §2.10), Q_STIR on PB4, CAN bootloader 0x7E0/0x7E8 (§5.1), fault 0x17 DU_UNDOCKED; CAN filters, TELEMETRY flags, pin table, power and dependencies updated |
| 1.2 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged — HEAT_STATUS `coil_temp` → `element_temp` (FR-MCU-006/-023, §5.2 table), fault 0x02 OVER_TEMP_COIL → OVER_TEMP_ELEMENT (same code), safety-state table coil temp → element temp; §2.2 power profiles re-based on the assumed 1,300 W unit (Sear 200–230 °C, Boil 80 %, Simmer 30–40 %); FR-MCU-054 pot detection via the unit's centre sensor; heater wording in §1, §2.1, §3, §4, §5.2, §7 updated |
| 1.3 | 2026-11-04 | Manas Pradhan | Heating unit referenced to the Philips OneChef NX5300/00 (centre-sensor range 80–200 °C, 6 L non-stick inner pot, see [[01-Electric-Heating]] §2.3): §2.2 Sear profile 200–230 → 180–200 °C; absolute limits re-based — FR-MCU-003/-052, §3 safety-state table, §5 fault 0x01: surface_temp > 260 °C CRITICAL → > 220 °C, > 270 °C E_STOP → > 230 °C (the unit's ceiling is 200 °C); element_temp > 250 °C WARNING unchanged |
| 1.4 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: a second STM32G0B1RE (the DU STM32) on the Unified PCB v5.0 — new §10 (purpose without safety authority, pin map, `du` task table, FR-DU-010–070: USART1 host link 921,600 baud COBS + CRC-16, gateway routing with the DU-local block 0x220 / 0x226 / 0x230–0x239 / 0x311 DU_STATUS / 0x3FE DU_ACK, HB_AP 5 s watchdog, dispensing, LED ring, buzzer, battery/dock monitoring, system-bootloader update via BOOT0/NRST, codes 0x11–0x16 reused plus 0x18–0x1A, 0x21, 0x22). CSC sections: "on the RV1106" → "on the DU STM32" (§1, §1.1, §2 note, §2.3/2.4/2.5/2.6/2.7/2.8, §3.1 notes, §3.3, §3.4, §4.2, §4.4, §5.1, §5.2, §7.2, §7.3, §9); CAN ID map, CSC pins and tasks unchanged |
| 1.5 | 2026-11-04 | Manas Pradhan | Stirring Unit on its own PSU (CSC v1.3): FDCAN2 becomes the second isolated CAN port (ISO1050DUB #3 + B0505S #2, 5V_ISO2 / GND_SU; SN65HVD230 removed); Q_STIR / F_STIR dropped — the SU power cut is the pilot relay K_SU on PB4 (Q_KSU → G5V-2 #2 → J_SAFE pin 5) on the AC input of LRS-75-24 #2, heater relay named K_SAFE; new FR-MCU-010c (≈ 300 ms PSU start-up, wait for the motor boot frame); J_SU pinout 24V_SU / GND_SU (floating, never bonded to CS GND), J_SU_IN added (eleven connectors); FR-MCU-010/-010a/-012a/-040/-055/-072, §1, §3.1 pin table, §3.3, §4.2, §4.3 safe hold, §4.4 boot, §6.1, §7.1–7.3, §8, §9.1 updated; CAN ID map, TELEMETRY / STATUS unchanged |
| 1.6 | 2026-11-04 | Manas Pradhan | CAN isolation on the CSC only: the DU STM32's node is a non-isolated SN65HVD230 (ISO1050DUB #2 removed from the Unified PCB, now v5.1); GND_ISO tied to the DU logic ground at dock pin 5, pin 6 (5V_ISO) reserved; ISO1050DUB #1 is a ground-loop barrier, the heating unit's CAN port must be SELV; §1.1 DU row, §3.3, §3.4 dock table, §9.1, §9.3, §10 pin map updated; CAN ID map unchanged |
| 1.7 | 2026-11-05 | Manas Pradhan | CSC powered from the heating unit (CSC v1.5): the board, both G5V-2 coils and the fans run from 12V_HU, a 12 V SELV tap off the OneChef control-board supply on the new J_HU_PWR (F1 2 A, SS34, SMBJ12A, 470 µF; requirements 10.8–13.2 V, ≥ 1.5 A spare, IRM-20-12 fallback); the 24 → 12 V MP1584EN #1 is dropped and one MP1584EN makes 5 V from 12 V; J_24V_IN → J_DU_IN (F_DU 3 A, SS54, SMBJ24A → 24V_DU, LRS-75-24 #1 to Q_DOCK only, −V bonded to the CSC ground; twelve connectors); K_SAFE re-specified onto the element loom — E-stop / safe hold = element disconnected while the OEM control board, its CAN port and 12V_HU stay live, the CSC boots as soon as the appliance is on, and mains return brings the heating unit's supply and the CSC back together; §1, §1.1 Power row, FR-MCU-051/-055/-056/-080, §3.1 PB0, §6.1, §7.1, §7.3, §9.1 updated; CAN ID map, tasks and pin map unchanged |
| 1.8 | 2026-11-05 | Manas Pradhan | CSC on its own PSU (CSC v1.6, reverses 1.7): the board, both G5V-2 coils and the fans run from 12V_IN, a dedicated Mean Well LRS-35-12 (12 V, 3 A, 36 W, AC input unswitched) on J_12V_IN (XT30; F1 2 A, SS34, SMBJ12A, 100 µF); the heating-unit tap J_HU_PWR / 12V_HU, its donor-rail requirements (SELV, 10.8–13.2 V, ≥ 1.5 A spare) and the IRM-20-12 fallback are withdrawn — nothing is tapped from the OEM unit, which is not opened; K_SAFE back on the heating unit's AC inlet loom (E-stop / safe hold = whole unit disconnected; the CSC stays up and boots independently of K_SAFE and K_SU); mains loss takes all three PSUs, the CSC, fans, relays and dock 24 V down together; J_DU_IN / 24V_DU, the single MP1584EN (12 → 5 V) and the twelve-connector count unchanged; §1, §1.1 Power row, FR-MCU-051/-055/-056/-080, §3.1 PB0, §6.1, §7.1, §7.3, §9.1 updated |
| 1.9 | 2026-11-05 | Manas Pradhan | Robot-mop SLD on the DU STM32 (Unified PCB v5.3): drawer tanks with float / presence Hall switches, pumps in the body with Hall tachs (6 V peristaltic oil, 6 V diaphragm water), passive check-valve nozzles; solenoids, 2 kg load cells, NAU7802 ×2 and TCA9543A removed. Open-loop metering (tach pulses × cal_ul), prime routine, per-unit calibration; new PC0–PC5 inputs; host-link block: DISPENSE_SLD target_ml / actual_ml + primed_ml, 0x233 SLD_PRIME, 0x235 QUERY_SLD, 0x237 SLD_CAL, DU_STATUS bit7 sld_low; codes 0x11 SLD_TANK_ABSENT, 0x23 NOT_DOCKED; FR-DU-032/-034/-035 rewritten, FR-DU-036/-037 added; §1, §2.5, FR-MCU-043, §11.1–§11.3, §11.5–§11.7 updated |
