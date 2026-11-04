---
tags: [epicura, mcu, stm32, functional-spec, firmware]
created: 2026-02-16
modified: 2026-11-04
version: 1.2
aliases: [STM32 Spec, MCU Spec]
---

# MCU Functional Specification — STM32G0B1RE

> **Document ID:** EPIC-SW-MCU-001
> **Processor:** STM32G0B1RET6, Cortex-M0+ @ 64 MHz
> **Flash / SRAM:** 512 KB (dual-bank) / 144 KB with parity
> **Package:** LQFP-64
> **Board:** Cooking Surface Controller (CSC) v1.0, in the Cooking Surface base beside the LRS-75-24
> **Related:** [[04-MPU-Functional-Specification]], [[02-Controller-Software-Architecture]], [[01-Unified-PCB-Design]]
> **Revision:** 2026-11-04 (v1.2) — Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged: HEAT_STATUS `coil_temp` → `element_temp`, fault 0x02 renamed OVER_TEMP_ELEMENT, power profiles re-based on the assumed 1,300 W unit
> **Previous revision:** 2026-11-04 (v1.1) — Three-unit architecture: the STM32 moves off the Unified PCB onto the Cooking Surface Controller (CSC) in the Cooking Surface base. Dispensing, sensor polling, load cells, LED ring, buzzer, battery monitoring, I2C peripherals and the UART service link leave the MCU (now on the RV1106 in the Dispensing Unit, see [[04-MPU-Functional-Specification]]); four FreeRTOS tasks remain. Added: exhaust-fan control (0x260–0x262, FAN_STALL), dock interface (DOCK_SENSE_B on PB3 → safe hold, Q_DOCK on PB5), Q_STIR on PB4, CAN bootloader (0x7E0/0x7E8), fault 0x17 DU_UNDOCKED
> **Earlier revision:** 2026-11-04 — MCU changed from STM32G474RE to STM32G0B1RE (no control loop on the MCU, so no FPU or 170 MHz needed; two FDCAN controllers kept; same ST HAL, FreeRTOS, system bootloader and X-CUBE-CLASSB); I2C1_SCL PA15 → PB6, VBUS/battery ADC PC0/PC1 → PA0/PA4, buzzer PC7/TIM8 → PA8/TIM1_CH1, FDCAN AF9 → AF3; two CAN ports (FDCAN1 isolated heater/host bus, FDCAN2 regular stir-motor bus); IR thermometer removed (module reports its own temperature); stirring motor is a CAN servo; 2S battery monitoring; host link on the isolated CAN bus, MCU keeps heater off-switch, relay and E-stop authority

---

## 1. Overview

The STM32G0B1RE is the real-time controller and safety guardian for Epicura on the Cooking Surface Controller (CSC), the board in the Cooking Surface (CS) base. It is a node on the isolated CAN bus it shares with the RV1106 (in the lift-off Dispensing Unit, reached through the dock) and the electric heating unit (FDCAN1), and the sole master of the regular CAN bus to the stirring motor in the Stirring Unit (FDCAN2). It runs FreeRTOS with four tasks: motor control over CAN (50 Hz), the safety monitor (10 Hz), host CAN communications (20 Hz) and thermal/fan management (1 Hz). It has no dispensing, no sensors beyond the fan tachometers and the pot reed, no I2C peripherals and no battery: dispensing, load cells, LED ring, buzzer and battery monitoring are local to the RV1106 on the Unified PCB in the Dispensing Unit. There is no temperature loop anywhere in Epicura: the heating unit regulates its own temperature and reports it; the STM32 supervises that status and owns all safety-critical paths including the heater off-switch, the AC relay, the stir-motor 24 V switch, the dock 24 V switch, E-stop handling and watchdog supervision.

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
| Power | 3.3 V via AMS1117-3.3 LDO from the CSC's own 24 → 5 V chain (MP1584EN #2 off the LRS-75-24), ~0.5 W typical; no battery |

---

## 2. Functional Requirements

> [!note] Retired requirement IDs (three-unit architecture, 2026-11-04)
> FR-MCU-013 (DSB servos), FR-MCU-021/022/024/025 (sensor polling), FR-MCU-030–034 (§2.5 dispensing), FR-MCU-056 (POWER_FAIL / battery) and FR-MCU-060–063 (§2.8 LED ring) are **retired (moved to the RV1106, see [[04-MPU-Functional-Specification]])**. IDs are not reused.

### 2.1 Heater Supervision (the temperature loop runs inside the heating unit)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-001 | Mirror the unit's `surface_temp` and `pot_detected` from HEAT_STATUS into TELEMETRY flags for the RV1106 (the RV1106 also reads HEAT_STATUS directly) | Should | Within one TELEMETRY interval (50 ms) |
| FR-MCU-002 | Never send HEAT_SET_TEMP or HEAT_SET_POWER; the only heater command the MCU sends is HEAT_ON_OFF = 0 (0x101) | Must | Verified by bus capture |
| FR-MCU-003 | Absolute thermal limits independent of the AP: HEAT_STATUS surface_temp > 270 °C, element over-temp or HEAT_FAULT → HEAT_ON_OFF = 0, E_STOP (0x001) broadcast, relay open | Must | Checked every 100 ms |
| FR-MCU-004 | Pot-absent in HEAT_STATUS → flag in TELEMETRY; RV1106 pauses | Should | Flag within one status interval |
| FR-MCU-005 | No temperature sensor on the MCU (IR thermometer removed) | — | — |
| FR-MCU-006 | Listen to HEAT_STATUS (0x180) on the shared bus for surface temperature, element temperature and faults | Must | No request needed; the unit broadcasts at 10 Hz |
| FR-MCU-007 | If HB_AP (0x010) is missing for 5 s or TELEMETRY cannot be sent (bus-off): HEAT_ON_OFF = 0, relay open, safe state | Must | Safe state within 5 s |

### 2.2 Power Level Profiles (reference; commanded by the RV1106 heat thread)

| Profile | Power (W) | Temp Range (°C) | Duty Cycle | CAN Command Value |
|---------|-----------|-----------------|------------|-------------------|
| Sear | 1,300 (assumed, unit TBD) | 200–230 | 100% | 0xFF |
| Boil | 1,040 | 100 | 80% | 0xCC |
| Simmer | 390–520 | 80–95 | 30–40% | 0x4D–0x66 |
| Warm | 150 | 60–70 | 10–15% | 0x1A |
| Off | 0 | Ambient | 0% | 0x00 |

### 2.3 Stirring Motor Control (CAN servo on FDCAN2)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-010 | Drive the 24 V CAN servo stirring motor over FDCAN2 (PB12 RX / PB13 TX, SN65HVD230, 1 Mbps, 29-bit IDs): enable/disable, velocity (stirring) and position (home/park) commands at 50 Hz; parse feedback (velocity, position, current, temperature, faults) | Must | Commanded vs. reported speed within ±5 RPM; feedback age ≤ 40 ms |
| FR-MCU-010a | Switch the motor's 24 V (Q_STIR, AO4407A driven from PB4 via 2N7002, F_STIR 5 A → J_STIR_PWR) on before the first enable frame and off after 60 s parked, on E-stop, on heartbeat loss, on DU undock (safe hold) and in the boot-safe state | Must | 0 V on J_STIR_PWR at reset |
| FR-MCU-010b | Configure the motor's command timeout ≤ 500 ms at start-up so a silent bus stops the arm | Must | Verified by stopping FDCAN2 traffic |
| FR-MCU-011 | Support stir patterns: continuous, intermittent, reverse, scrape, fold, vigorous (velocity profiles + signed direction) | Must | Pattern selected by RV1106 command (0x202), direction param |
| FR-MCU-012 | Stall / over-torque detection from motor-reported current and velocity error only (the CAN servo reports its own current; there is no INA219 on the CSC) | Must | STIR_STALL (0x10) within 500 ms of a blocked paddle; 3 retries then error |
| FR-MCU-012a | FDCAN2 bus-off or no motor feedback for 200 ms → disable, Q_STIR off, STIR_CAN_FAULT (0x15) | Must | Reported within 300 ms |
| FR-MCU-013 | Retired — Dispenser Servo Block moved to the RV1106 `dispense` thread (see [[04-MPU-Functional-Specification]] §2.9) | — | — |
| FR-MCU-014 | Motor control task at 50 Hz (20 ms period) | Must | Highest priority FreeRTOS task |

### 2.4 Sensor Polling

Only the unit-reported element temperature remains; FR-MCU-021/022/024/025 (load cells, battery ADC, INA219, sensor-poll task) are retired (moved to the RV1106, see MPU spec). There is no Sensor Poll task; FR-MCU-023 is served by the CAN Comms task.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-023 | Parse element temperature from CAN HEAT_STATUS | Must | Received at 10 Hz from the heating unit |

### 2.5 Ingredient Dispensing

Retired in full (FR-MCU-030–034, §2.5.1, §2.5.2): dispensing is local to the RV1106 in the Dispensing Unit (PCA9685, TB6612, solenoids, NAU7802 load cells over I2C3) — see [[04-MPU-Functional-Specification]] §2.9. No dispensing frame exists on the CAN bus any more.

### 2.6 RV1106 Communication (CAN bus)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-040 | Host link is FDCAN1 (PB8/PB9) on the isolated 3-node CAN bus (ISO1050DUB #1 on the CSC; J_CAN_HEAT to the heating unit, J_DOCK pins 3–6 to the RV1106 node in the Dispensing Unit), classic CAN 2.0B at 500 kbps, 11-bit IDs; FDCAN2 (PB12/PB13) is a separate regular bus to the stirring motor only (J_CAN_STIR) | Must | FDCAN1 accepts 0x001, 0x010, 0x18x, 0x202, 0x221–0x225, 0x260–0x262 and 0x7E0 via hardware filters; no frame is ever bridged between the two buses |
| FR-MCU-041 | Command frames: byte 0 = seq, bytes 1..7 = payload; answer every command with ACK/NAK (0x3FF: seq, cmd_type, result, ≤ 5 data bytes) | Must | ACK within 50 ms of a valid command; NAK with result code on invalid payload or state |
| FR-MCU-042 | No software framing or CRC; rely on CAN hardware ACK + CRC; reject frames with wrong DLC | Must | Bad-DLC frames counted and dropped |
| FR-MCU-043 | Send TELEMETRY (0x310) at 20 Hz unsolicited (LOADCELLS 0x311 retired — load cells are on the RV1106) | Must | motor_rpm, motor_current_dA, safety_state, flags (pot_detected, stir_enabled, docked, fan1_ok, fan2_ok), error_code, seq |
| FR-MCU-044 | Send STATUS (0x312) on safety state change and on safe-hold entry/exit | Must | safety_state, error_code, flags, fault_detail (no batt_mV: the battery is in the Dispensing Unit) |
| FR-MCU-045 | CAN comms task at 20 Hz (50 ms period) driven by the FDCAN1 RX FIFO interrupt | Must | Process incoming commands + queue outgoing |
| FR-MCU-046 | Monitor HB_AP (0x010, every 2 s) | Must | Missing for 5 s → safe state (HEAT_ON_OFF = 0, relay open) |
| FR-MCU-047 | Firmware update over the isolated CAN bus: an in-application CAN bootloader (OpenBLT-style) accepts FW_UPDATE_REQ (0x7E0: seq, op = ERASE / WRITE / VERIFY / BOOT, 5 data bytes) from the RV1106 and answers FW_UPDATE_RSP (0x7E8: seq, op, result, 4 data bytes); the image is CRC-verified before the application slot is marked valid and booted; USB-C DFU on the CSC is the bench fallback, SWD for factory. No UART host link exists (USART2 is a debug console on J_DBG only) | Should | Update accepted only in the safe state with heater off and stir motor disabled; CRC mismatch → NAK, previous image kept; 0x7E0/0x7E8 are the lowest-priority IDs on the bus |

### 2.7 Safety

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-050 | E-stop button (PB2, EXTI interrupt) → immediate shutdown | Must | <1 ms from button press to relay open |
| FR-MCU-051 | Safety relay control (PB0 → MOSFET → relay) | Must | Cuts AC mains to the heating unit |
| FR-MCU-052 | Thermal cutoff: HEAT_STATUS surface_temp >270 °C, CAN element over-temp or HEAT_FAULT → E_STOP | Must | Checked every 100 ms (safety monitor cycle) |
| FR-MCU-053 | Hardware watchdog (IWDG, 5 s timeout) | Must | Kick in main loop; timeout → full reset |
| FR-MCU-054 | Pot detection via CAN (unit-reported `pot_detected`, spring-loaded centre sensor) | Must | No heat command if pot absent |
| FR-MCU-055 | Boot-safe state: all actuator outputs OFF until initialized — Q_STIR off, Q_DOCK off, relay open, fans off | Must | Pull-downs/pull-ups on MOSFET gates; verified with the MCU held in reset |
| FR-MCU-056 | Retired — POWER_FAIL / battery monitoring moved to the RV1106 dock/power monitor (the CSC has no battery and no 24 V comparator; a mains outage simply resets the STM32, which reboots in < 1 s when mains returns) | — | — |

### 2.8 LED Ring (retired)

Retired in full (FR-MCU-060–063): the camera LED ring is a white PWM-dimmed ring on the Unified PCB in the Dispensing Unit, driven directly by an RV1106 PWM (Q_LED) — see [[04-MPU-Functional-Specification]] FR-MPU-014. SET_LED (0x220) no longer exists on the bus.

### 2.9 Dock Interface (DOCK_SENSE_B, Q_DOCK)

The Dispensing Unit seats on an 8-contact magnetic pogo dock on the CS left pillar; the CSC owns the dock's 24 V switch and senses the unit's presence (see §3.4).

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-070 | Sense DU presence on PB3 (DOCK_SENSE_B, 10k pull-up, low = DU present; dock pin 8 is tied to GND on the DU) with 20 ms debounce; mirror it as the `docked` flag in TELEMETRY | Must | Flag within one TELEMETRY interval of the debounced edge |
| FR-MCU-071 | Enable the dock 24 V (Q_DOCK, AO4407A driven from PB5 via 2N7002, F_DOCK 2 A → J_DOCK pin 1) only while DOCK_SENSE_B is low; off within 1 ms of DOCK_SENSE_B going high, at reset and in E_STOP | Must | Dock pads de-energised when the unit is lifted; 0 V on J_DOCK pin 1 with no DU present |
| FR-MCU-072 | DOCK_SENSE_B open → immediate safe hold: HEAT_ON_OFF = 0 (0x101), stir disable frame on FDCAN2, Q_STIR off, Q_DOCK off, STATUS (0x312) with error_code 0x17 DU_UNDOCKED. Not an E_STOP: the relay stays closed and no E_STOP frame is sent | Must | Outputs off within one safety-monitor cycle (100 ms); the heater also stops by itself ≤ 1 s after the last RV1106 keep-alive |
| FR-MCU-073 | Leave safe hold back to NORMAL only when DOCK_SENSE_B is low again **and** HB_AP (0x010) has returned; Q_DOCK re-enabled as soon as DOCK_SENSE_B is low | Must | STATUS sent on exit; no command accepted while held |

### 2.10 Exhaust Fans

Both 12 V exhaust fans sit in the CS rear with the CSC and are driven by it (fans and their MOSFETs left the Unified PCB). Command codes follow [[05-Exhaust-Fume-Management]] §3.4.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-080 | Drive fan 1 from PA6 (TIM3_CH1, 25 kHz hardware PWM) and fan 2 from PB10 (25 kHz software PWM) through IRLML6344 low-side MOSFETs (SS14 flyback) → J_FAN (12 V from MP1584EN #1) | Must | Duty 0–100 % in 1 % steps; fans off in the boot-safe state and on E_STOP |
| FR-MCU-081 | Handle SET_EXHAUST (0x260: seq, duty_pct) and EXHAUST_AUTO (0x262: seq, stage_id → stage duty table held in firmware); ACK within one comms cycle | Must | Duty applied ≤ 50 ms after the frame; NAK on duty > 100 or unknown stage_id |
| FR-MCU-082 | Answer GET_EXHAUST (0x261: seq) with ACK data: duty_pct, rpm1, rpm2 (uint16, from the optional tachometer inputs, 0 if not fitted) | Must | Response within 100 ms |
| FR-MCU-083 | Fan stall detection in the Thermal/Fan task (1 Hz): tachometer < 300 rpm for 2 s with duty > 0 → clear fan1_ok / fan2_ok in the TELEMETRY flags (FAN_STALL) and send STATUS; the RV1106 heat thread reduces heater power, the STM32 never sends power levels | Must | Flag within 3 s of a stalled fan; cleared when rpm recovers |

---

## 3. Hardware Interfaces

### 3.1 Pin Assignment (LQFP-64)

All signals are on the Cooking Surface Controller (CSC) v1.0; the STM32 no longer shares a board with the RV1106.

| Pin | Function | Peripheral | Target |
|-----|----------|------------|--------|
| **PA0** | ADC_IN0 | Analog | USB VBUS detect (100k/100k divider; bench USB-C only) |
| **PA1** | — | Available | Freed (24 V power-fail comparator dropped — no battery on the CSC, outage handling is on the RV1106) |
| **PA2** | USART2_TX (AF1) | UART | Debug console → J_DBG 3-pin header; no host link (the RV1106 is in another unit) |
| **PA3** | USART2_RX (AF1) | UART | Debug console ← J_DBG |
| **PA4** | — | Available | Freed (battery ADC dropped — the 2S pack is in the Dispensing Unit) |
| **PA5** | — | Available | Freed (stir motor DIR; motor is now on FDCAN2) |
| **PA6** | TIM3_CH1 (AF1) | PWM 25 kHz | Exhaust fan 1 (IRLML6344 + SS14 → J_FAN, 12 V) |
| **PA7** | — | Available | Freed |
| **PA8** | — | Available | Freed (piezo buzzer moved to the Dispensing Unit, RV1106 PWM) |
| **PA9** | — | Available | Freed |
| **PA10** | — | Available | Freed |
| **PA11** | USB_DM | USB 2.0 FS | USB D- (native USB, DFU+CDC, J_USB bench only) |
| **PA13** | SWDIO | Debug | SWD programming (J_SWD 2×5 1.27 mm) |
| **PA14** | SWCLK / BOOT0 | Debug + boot | SWD clock; on the G0 this pin is also BOOT0 (sampled at reset) → SW_BOOT push-button on the CSC for bench DFU entry (option bit nBOOT_SEL must be cleared once at factory programming, see §5.1); no RV1106 line |
| **PB0** | GPIO output | Digital | Safety relay Q_RLY (2N7002 → Omron G5V-2 12 V coil → J_SAFE pin 1) |
| **PB1** | GPIO input | Digital | Pot reed switch (J_SAFE pin 2, optional backup to the heating unit's pot detection) |
| **PB2** | EXTI | Interrupt | E-stop button on the CS front (NC, active-low, J_SAFE pin 3, 10k pull-up + 100 nF) |
| **PB3** | GPIO input | Digital | DOCK_SENSE_B (10k pull-up; low = DU present; J_DOCK pin 8) |
| **PB4** | GPIO output | Digital | Q_STIR enable (2N7002 → AO4407A P-MOSFET → F_STIR 5 A → J_STIR_PWR) |
| **PB5** | GPIO output | Digital | Q_DOCK enable (2N7002 → AO4407A P-MOSFET → F_DOCK 2 A → J_DOCK pin 1 DOCK_24V) |
| **PB6** | I2C1_SCL (AF6) | Unpopulated pads | No I2C device on the CSC; pads kept for a future expander |
| **PB7** | I2C1_SDA (AF6) | Unpopulated pads | No I2C device on the CSC |
| **PA15** | — | Available | Freed (was I2C1_SCL on the G474) |
| **PB8** | FDCAN1_RX (AF3) | CAN 500 kbps | Isolated 3-node bus (RV1106 via the dock + heating unit) via ISO1050DUB #1 |
| **PB9** | FDCAN1_TX (AF3) | CAN 500 kbps | Isolated 3-node bus (RV1106 via the dock + heating unit) via ISO1050DUB #1 |
| **PB10** | GPIO output | Software PWM 25 kHz | Exhaust fan 2 (IRLML6344 + SS14 → J_FAN, 12 V) |
| **PB11** | — | Available | Freed |
| **PB12** | FDCAN2_RX (AF3) | CAN 1 Mbps | Regular (non-isolated) stir-motor bus via SN65HVD230 → J_CAN_STIR |
| **PB13** | FDCAN2_TX (AF3) | CAN 1 Mbps | Regular (non-isolated) stir-motor bus via SN65HVD230 → J_CAN_STIR |
| **PB14** | — | Available | Freed (WS2812B ring removed; the white LED ring is on the Dispensing Unit, RV1106 PWM) |
| **PB15** | — | Available | Freed |
| **PC0–PC6** | — | Available | Freed (pump PWM/DIR, VBUS and battery sense all left the CSC) |
| **PC7** | GPIO output | Digital | Status LED |
| **PC8–PC12** | — | Available | Freed (HX711 load cells moved to NAU7802 on the RV1106's I2C3) |
| **PD2** | — | Available | Freed |

### 3.2 I2C1 Bus (PB6/PB7)

Unpopulated pads. The CSC carries no I2C device: the PCF8574 (all CSC outputs are now direct GPIO), INA219 (the CAN servo reports its own current) and PCA9685 (dispensing, now on the RV1106) are gone from this board.

### 3.3 CAN Buses

**FDCAN1 — isolated host + heater bus (J_CAN_HEAT + J_DOCK pins 3–6)**
- Transceiver: ISO1050DUB #1 (isolated, 5 kV RMS) on the CSC, fed by the CSC's B0505S-1WR3 (5V_ISO/GND_ISO). This is the single isolated domain of the machine: it is extended over dock pins 3–6 (CAN_H, CAN_L, GND_ISO, 5V_ISO through F_CAN 100 mA) to the RV1106 node's ISO1050DUB #2 + MCP2518FD (SPI0 CS1) on the Unified PCB in the Dispensing Unit
- Bit rate: 500 kbps (CAN 2.0B, classic frames, 11-bit IDs)
- Nodes: STM32 (this MCU, src_node 2), RV1106 application processor (via the dock), heating unit MCU (J_CAN_HEAT, JST-XH 4-pin: CAN_H, CAN_L, GND_ISO, 5V_ISO)
- Termination: R_TERM1 120 Ω on the CSC at J_CAN_HEAT and 120 Ω inside the heating unit; the dock → Unified PCB run is a stub ≤ 30 cm; PESD1CAN on the isolated side
- Lifting the DU opens the bus and the dock 24 V at the same instant: the STM32 sees DOCK_SENSE_B go high (safe hold, §2.9) and HB_AP stop; the heating unit stops ≤ 1 s after the last keep-alive
- Traffic: host commands 0x2xx and reports 0x3xx (RV1106 ↔ STM32), heater control 0x1xx (RV1106 → unit; STM32 sends HEAT_ON_OFF = 0 only), E_STOP 0x001, HB_AP 0x010, firmware update 0x7E0/0x7E8 — see §5.2

**FDCAN2 — regular stir-motor bus (J_CAN_STIR)**
- Transceiver: SN65HVD230 (3.3 V, non-isolated) on the CSC; PB12 RX / PB13 TX (AF3)
- Bit rate: 1 Mbps (CAN 2.0B, 29-bit IDs per the motor protocol)
- Nodes: STM32 (master) and the stirring motor's integrated controller in the Stirring Unit; 120 Ω at J_CAN_STIR and at the motor
- Traffic: enable/disable, velocity and position commands at 50 Hz; motor feedback (velocity, position, current, temperature, faults); wrapped in `stir_motor.c`
- Power: 24 V to the motor on J_STIR_PWR (XT30) through Q_STIR (PB4 via 2N7002 → AO4407A, F_STIR 5 A). J_CAN_STIR and J_STIR_PWR are bundled into the stirring-unit harness inside the right pillar, ending at J_SU (Molex Micro-Fit 3.0, 5-way: 24V_STIR, GND, CAN_H, CAN_L, SHIELD) — the only cable between units
- Never bridged to FDCAN1

### 3.4 Dock Interface (J_DOCK, CSC view)

J_DOCK is an 8-pin JST-XH header on the CSC wired to the pogo block in the CS left pillar (8 spring pins, 2 A each, 2.54 mm pitch, magnetic, keyed recess; flat gold pads on the DU underside). The load cells, HX711 and all other DU sensing that used to be in this section are now on the Unified PCB (see MPU spec).

| Pin | Signal | Direction | CSC side |
|-----|--------|-----------|----------|
| 1 | DOCK_24V | CS → DU | Q_DOCK (AO4407A, PB5 via 2N7002) → F_DOCK 2 A polyfuse; on only while DOCK_SENSE_B is low; pads dead when the unit is lifted |
| 2 | GND | — | 24 V return; ties the DU logic ground to the CS ground while docked |
| 3 | CAN_H | bus | Isolated bus from ISO1050DUB #1 (same bus as J_CAN_HEAT) |
| 4 | CAN_L | bus | |
| 5 | GND_ISO | — | Isolated bus ground (B0505S output) |
| 6 | 5V_ISO | CS → DU | B0505S-1WR3 output through F_CAN 100 mA; powers the bus side of the DU's ISO1050DUB #2 |
| 7 | DOCK_SENSE_A | CS → DU | Tied to GND on the CSC; the DU's 10k pull-up → RV1106 GPIO reads low when docked |
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
| Safety Monitor | 10 Hz | 100 ms | Highest (4) | 256 B | HEAT_STATUS thermal limits, E-stop, heartbeat, DOCK_SENSE_B safe hold, Q_STIR/Q_DOCK/relay authority, watchdog kick |
| CAN Comms | 20 Hz | 50 ms | High (3) | 1024 B | FDCAN1 RX FIFO → command parser, ACK/NAK, TELEMETRY/STATUS TX, HEAT_STATUS capture for the safety monitor, exhaust commands, CAN bootloader hand-off (0x7E0) |
| Thermal/Fan | 1 Hz | 1 s | Medium (2) | 256 B | Fan PWM (PA6/PB10), optional tachometer read and FAN_STALL, EXHAUST_AUTO stage table, pot reed (PB1) debounce |

The former Dispense and Sensor Poll tasks are removed (moved to the RV1106 `dispense` thread and its power/dock monitor).

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
| WARNING | CRITICAL | HEAT_STATUS surface_temp > 260 °C, or CAN fault from the heating unit |
| CRITICAL | E_STOP | surface_temp > 270 °C, CAN element over-temp, HEAT_FAULT, E-stop button, RV1106 heartbeat timeout (5 s) |
| E_STOP | NORMAL | Manual hardware reset (E-stop button released + PB2 debounce) |

**Safe hold (DU undocked):** DOCK_SENSE_B going high is not a safety-state transition and not an E_STOP. The safety monitor applies the safe-hold outputs (HEAT_ON_OFF = 0, stir disable + Q_STIR off, Q_DOCK off, relay stays closed), reports error_code 0x17 DU_UNDOCKED in STATUS and refuses commands until DOCK_SENSE_B is low again and HB_AP has returned, then resumes NORMAL and clears the code. Battery-low is no longer a WARNING trigger: the pack and its monitoring are in the Dispensing Unit.

### 4.4 Boot Sequence

1. **Reset** → SystemInit (8 MHz HSE + PLL → 64 MHz SYSCLK; FDCAN kernel clock from PLLQ); Class B start-up self-tests
2. **HAL_Init** → SysTick, NVIC priorities
3. **Peripheral init** → GPIO (all outputs LOW/safe: Q_STIR, Q_DOCK, relay and fans off), ADC (VBUS), TIM3 (fan 1 PWM), FDCAN1 (filters for 0x001, 0x010, 0x18x, 0x202, 0x221–0x225, 0x260–0x262, 0x7E0), FDCAN2 (motor feedback filter, 1 Mbps), USART2 (J_DBG console)
4. **Safety check** → Verify E-stop not pressed, relay OFF; read DOCK_SENSE_B (PB3): Q_DOCK stays off until a DU is sensed (low), then Q_DOCK on. No I2C self-test and no battery check (neither exists on the CSC)
5. **FreeRTOS start** → Create the four tasks, start scheduler
6. **Wait for RV1106 heartbeat** → First HB_AP (0x010) on the bus (the RV1106 only reaches the bus while docked) → safety state NORMAL
7. **IDLE mode** → Thermal/Fan task at 1 Hz, heartbeat and dock monitoring, awaiting commands; stir motor enumerated on FDCAN2 (command timeout configured) and left disabled with 24 V off

---

## 5. Communication Protocols

### 5.1 Firmware Update over CAN (and debug console)

There is no UART between the RV1106 and the STM32 any more — they are in different units, joined only by the dock. Firmware reaches the STM32 over the isolated CAN bus.

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

### 5.2 CAN Bus Protocol (shared bus: RV1106, STM32, heating unit)

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

Removed from the bus: 0x220 SET_LED, 0x230–0x239 dispensing block and 0x311 LOADCELLS (dispensing and the LED ring are local to the RV1106).

- Reference heater IDs follow [[../05-Subsystems/01-Electric-Heating|Electric Heating]] §3.2 and are adapted to the chosen heating unit
- Timeouts: HB_AP missing 5 s → safe state; no HEAT_STATUS for 500 ms or FDCAN bus-off → CAN_FAULT (relay open, since the heater cannot be commanded)
- Pot detection: pot-absent in HEAT_STATUS is flagged in TELEMETRY; the RV1106 pauses heating
- Dock: DOCK_SENSE_B open → safe hold with STATUS error_code 0x17 (§2.9); the RV1106 leaves the bus physically at the same moment, so HB_AP loss follows within 5 s

### 5.3 I2C Protocol

Removed — the CSC has no I2C devices (I2C1 pads unpopulated, §3.2).

---

## 6. Power Management

### 6.1 Power Supply

- Input: J_24V_IN (XT30) from the LRS-75-24 in the CS base; F1 5 A polyfuse, SS54 reverse protection, SMBJ24A TVS
- Rails on the CSC: MP1584EN #1 24 → 12 V (fans, relay coil); MP1584EN #2 24 → 5 V → AMS1117-3.3 (SOT-223, 800 mA max) for the STM32, SN65HVD230, ISO1050DUB #1 logic side and the B0505S-1WR3 input; 5V_USB from J_USB OR'd into the 3.3 V LDO input for bench programming
- No battery: the 2S pack is in the Dispensing Unit and keeps the RV1106 alive through an outage; the STM32 simply resets on mains loss and reboots in < 1 s when mains returns (the heater and relay are already de-energised)
- Switched outputs from the 24 V input: Q_STIR → J_STIR_PWR (5 A) and Q_DOCK → J_DOCK pin 1 (2 A), both off at reset
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
| Safety relay | PB0 → N-MOSFET → relay coil (NC relay, fail-safe open) | <5 ms |
| Hardware watchdog (IWDG) | 5 s timeout, kicked in safety monitor task | 5 s (worst case) |
| Class B self-tests | X-CUBE-CLASSB: CPU/RAM/flash/clock/program-flow checks at boot; RAM and flash CRC re-checked periodically | Fault → safe state at next safety tick |
| Thermal cutoff (surface) | HEAT_STATUS surface_temp > 270 °C → E_STOP | ≤200 ms (status interval + poll) |
| Thermal cutoff (CAN element) | CAN element over-temp → E_STOP | ≤500 ms (CAN status interval) |
| Stir motor | Motor disable on FDCAN2 + Q_STIR 24 V switch off on E-stop / heartbeat loss / FDCAN2 fault / DU undock | ≤10 ms |
| Dock sense | DOCK_SENSE_B (PB3) high → safe hold: HEAT_ON_OFF = 0, stir disable, Q_STIR off, Q_DOCK off (dock pads de-energised), STATUS DU_UNDOCKED | ≤100 ms (safety-monitor cycle); Q_DOCK ≤ 1 ms |
| CAN fault | No HEAT_STATUS for 500 ms or bus-off → relay open (heater cannot be commanded), alert | 500 ms |
| RV1106 heartbeat loss | No HB_AP (0x010) for 5 s → HEAT_ON_OFF = 0, relay open, safe state | 5 s |
| Fan stall | Tachometer < 300 rpm for 2 s with duty > 0 → fan1_ok / fan2_ok cleared (FAN_STALL), STATUS; RV1106 reduces heater power | ≤3 s |

### 7.2 Fault Table

| Fault Code | Name | Severity | Action |
|------------|------|----------|--------|
| 0x01 | OVER_TEMP_SURFACE | Critical | E_STOP, cut relay, log (HEAT_STATUS surface_temp > 270 °C) |
| 0x02 | OVER_TEMP_ELEMENT | Critical | E_STOP, cut relay, log |
| 0x03 | E_STOP_PRESSED | Critical | E_STOP, cut relay; the RV1106 sounds the buzzer (on the DU) from STATUS |
| 0x04 | CAN_FAULT | Critical | Open relay (heater unreachable on the bus), alert RV1106 when the bus returns |
| 0x05 | RV1106_HEARTBEAT_LOSS | Critical | HEAT_ON_OFF = 0, relay open, stir motor disabled + Q_STIR off (safe state) |
| 0x10 | STIR_STALL | Warning | Disable motor, retry 3×, alert RV1106 (motor-reported current / velocity error) |
| 0x15 | STIR_CAN_FAULT | Warning | FDCAN2 bus-off or no motor feedback 200 ms: disable, Q_STIR off, alert RV1106 |
| 0x17 | DU_UNDOCKED | Info | DOCK_SENSE_B open → safe hold (HEAT_ON_OFF = 0, stir disable, Q_STIR off, Q_DOCK off); cleared when docked and HB_AP returns |
| 0x20 | CAN_TX_TIMEOUT | Info | Retry 3×, then CAN_FAULT |

Removed codes (now RV1106-detected, see [[04-MPU-Functional-Specification]] §7.2): 0x11 SLD_LOAD_CELL_DRIFT, 0x12 DSB_STALL, 0x13 SLD_DISPENSE_ERROR, 0x14 BATTERY_FAULT, 0x16 POWER_FAIL; 0x21 I2C_NACK dropped (no I2C device on the CSC). Codes are not reused.

### 7.3 E-Stop Sequence

1. **PB2 EXTI fires** (or E_STOP 0x001 received on the CAN bus)
2. Safety relay opened (PB0 LOW → relay de-energizes → AC cut)
3. Stir motor: disable frame on FDCAN2, Q_STIR (PB4) off; fan PWM to 0 %; Q_DOCK off
4. CAN: send HEAT_ON_OFF = 0 (0x101) and broadcast E_STOP (0x001, src_node = 2) on FDCAN1 — belt-and-suspenders with the relay
5. STATUS (0x312) sent on the bus: `safety_state = E_STOP`; the RV1106 sounds the buzzer (on the Dispensing Unit) and shows the alert — the CSC has no buzzer
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
| Safe hold on undock | <100 ms (Q_DOCK < 1 ms) | DOCK_SENSE_B edge → HEAT_ON_OFF 0 / Q_STIR off / Q_DOCK off |
| Fan duty latency | <50 ms | SET_EXHAUST received → PWM duty applied |
| CAN firmware update (512 KB image) | <3 min | ERASE → BOOT over 0x7E0/0x7E8 at 500 kbps |
| FreeRTOS CPU utilization | <70% at 64 MHz | Idle task runtime measurement |
| Flash usage | <256 KB | Linker map |
| SRAM usage | <96 KB (of 144 KB) | Stack + heap analysis |

---

## 9. Dependencies & Constraints

### 9.1 Hardware Dependencies

- Cooking Surface Controller (CSC) v1.0 (~100 × 70 mm, 4-layer with isolation slot, in the CS base beside the LRS-75-24) provides the STM32, 8 MHz HSE, LDO, both MP1584EN bucks, both CAN transceivers, the B0505S-1WR3 isolated supply, Q_STIR / Q_DOCK / Q_RLY, the G5V-2 safety relay, fan MOSFETs and ten connectors: J_24V_IN, J_CAN_HEAT, J_CAN_STIR, J_STIR_PWR, J_DOCK, J_FAN, J_SAFE, J_DBG, J_SWD, J_USB
- Isolated CAN port on the CSC (ISO1050DUB #1 for FDCAN1, J_CAN_HEAT to the heating unit, J_DOCK pins 3–6 to the RV1106 node's ISO1050DUB #2 + MCP2518FD on the Unified PCB in the Dispensing Unit)
- Regular CAN port on the CSC (SN65HVD230 on FDCAN2, J_CAN_STIR) and switched 24 V (Q_STIR, J_STIR_PWR), bundled into the stirring-unit harness to J_SU
- Dock block in the CS left pillar (8-contact magnetic pogo, J_DOCK) for DOCK_24V, the isolated bus and the two sense lines
- No HX711, WS2812B, 74AHCT1G125, PCA9685, PCF8574, INA219 or battery on this board (all on the Unified PCB in the Dispensing Unit, or dropped)

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
- Both CAN buses require 120 Ω termination at both ends; FDCAN1 (isolated) and FDCAN2 (regular) share nothing; the dock → Unified PCB stub on FDCAN1 must stay ≤ 30 cm
- Q_DOCK must never be on with DOCK_SENSE_B high (exposed pogo pins)

### 9.4 Cross-References

| Topic | Document |
|-------|----------|
| RV1106 MPU spec | [[04-MPU-Functional-Specification]] |
| State machine details | [[03-Main-Loop-State-Machine]] |
| Software architecture | [[02-Controller-Software-Architecture]] |
| Unified PCB design | [[01-Unified-PCB-Design]] |
| Dispensing subsystems (now RV1106-driven) | [[03-Ingredient-Dispensing]] |
| Exhaust fans | [[05-Exhaust-Fume-Management]] |
| Hardware architecture | [[01-Epicura-Architecture]] |
| Technical specifications | [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications]] |

---

## 10. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-16 | Manas Pradhan | Initial document; subsequent single-board revisions recorded in the header (STM32G474RE → STM32G0B1RE, CAN host link, CAN servo stir motor, 2S battery monitoring) |
| 1.1 | 2026-11-04 | Manas Pradhan | Three-unit architecture: STM32 moved to the Cooking Surface Controller (CSC) in the CS base; four FreeRTOS tasks (Motor Control, Safety Monitor, CAN Comms, Thermal/Fan); dispensing (§2.5), sensor polling, load cells, LED ring (§2.8), buzzer, battery/POWER_FAIL, I2C peripherals and the UART service link retired (moved to the RV1106); added dock interface (DOCK_SENSE_B PB3 safe hold, Q_DOCK PB5, §2.9/§3.4), exhaust-fan FRs (0x260–0x262, FAN_STALL, §2.10), Q_STIR on PB4, CAN bootloader 0x7E0/0x7E8 (§5.1), fault 0x17 DU_UNDOCKED; CAN filters, TELEMETRY flags, pin table, power and dependencies updated |
| 1.2 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit (rice-cooker class, own PID, CAN port); CAN contract unchanged — HEAT_STATUS `coil_temp` → `element_temp` (FR-MCU-006/-023, §5.2 table), fault 0x02 OVER_TEMP_COIL → OVER_TEMP_ELEMENT (same code), safety-state table coil temp → element temp; §2.2 power profiles re-based on the assumed 1,300 W unit (Sear 200–230 °C, Boil 80 %, Simmer 30–40 %); FR-MCU-054 pot detection via the unit's centre sensor; heater wording in §1, §2.1, §3, §4, §5.2, §7 updated |
