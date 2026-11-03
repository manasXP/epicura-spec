---
tags: [epicura, mcu, stm32, functional-spec, firmware]
created: 2026-02-16
aliases: [STM32 Spec, MCU Spec]
---

# MCU Functional Specification — STM32G474RE

> **Document ID:** EPIC-SW-MCU-001
> **Processor:** STM32G474RE, Cortex-M4F @ 170 MHz
> **Flash / SRAM:** 512 KB / 128 KB
> **Package:** LQFP-64
> **Related:** [[04-MPU-Functional-Specification]], [[02-Controller-Software-Architecture]], [[01-Unified-PCB-Design]]
> **Revision:** 2026-11-04 — two CAN ports (FDCAN1 isolated heater/host bus, FDCAN2 regular stir-motor bus); IR thermometer removed (module reports its own temperature); stirring motor is a CAN servo; 2S battery monitoring; host link on the isolated CAN bus, MCU keeps heater off-switch, relay and E-stop authority

---

## 1. Overview

The STM32G474RE is the real-time controller and safety guardian for Epicura on the Unified PCB. It is a node on the isolated CAN bus it shares with the RV1106 and the induction surface (FDCAN1), and the sole master of the regular CAN bus to the stirring motor (FDCAN2). It runs FreeRTOS with five primary tasks: motor control over CAN (50 Hz), dispensing (50 Hz while active), sensor polling (10 Hz), host CAN communications (20 Hz) and the safety monitor (10 Hz). There is no temperature loop anywhere in Epicura: the induction module regulates its own temperature and reports it; the STM32 supervises that status and owns all safety-critical paths including the heater off-switch, the AC relay, the stir-motor 24 V switch, E-stop handling and watchdog supervision.

### 1.1 Hardware Summary

| Parameter | Value |
|-----------|-------|
| Core | Cortex-M4F @ 170 MHz, single-precision FPU |
| Flash | 512 KB |
| SRAM | 128 KB |
| ADC | 5× 12-bit (up to 4 Msps) |
| Timers | Advanced (TIM1), GP (TIM2/3/4), basic |
| Comm | 3× UART, 3× SPI, 4× I2C, 3× FDCAN (FDCAN1 = isolated host + heater bus, FDCAN2 = stir-motor bus) |
| Package | LQFP-64 |
| Power | 3.3 V via AMS1117-3.3 LDO (from 5 V), ~0.5 W typical |

---

## 2. Functional Requirements

### 2.1 Heater Supervision (the temperature loop runs inside the induction module)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-001 | Mirror the module's `surface_temp` and `pot_detected` from HEAT_STATUS into TELEMETRY flags for the RV1106 (the RV1106 also reads HEAT_STATUS directly) | Should | Within one TELEMETRY interval (50 ms) |
| FR-MCU-002 | Never send HEAT_SET_TEMP or HEAT_SET_POWER; the only heater command the MCU sends is HEAT_ON_OFF = 0 (0x101) | Must | Verified by bus capture |
| FR-MCU-003 | Absolute thermal limits independent of the AP: HEAT_STATUS surface_temp > 270 °C, coil over-temp or HEAT_FAULT → HEAT_ON_OFF = 0, E_STOP (0x001) broadcast, relay open | Must | Checked every 100 ms |
| FR-MCU-004 | Pot-absent in HEAT_STATUS → flag in TELEMETRY; RV1106 pauses | Should | Flag within one status interval |
| FR-MCU-005 | No temperature sensor on the MCU (IR thermometer removed) | — | — |
| FR-MCU-006 | Listen to HEAT_STATUS (0x180) on the shared bus for surface temperature, coil temperature and faults | Must | No request needed; module broadcasts at 10 Hz |
| FR-MCU-007 | If HB_AP (0x010) is missing for 5 s or TELEMETRY cannot be sent (bus-off): HEAT_ON_OFF = 0, relay open, safe state | Must | Safe state within 5 s |

### 2.2 Power Level Profiles (reference; commanded by the RV1106 heat thread)

| Profile | Power (W) | Temp Range (°C) | Duty Cycle | CAN Command Value |
|---------|-----------|-----------------|------------|-------------------|
| Sear | 1,800 | 200–250 | 100% | 0xFF |
| Boil | 1,500 | 100 | 85% | 0xD9 |
| Simmer | 400–600 | 80–95 | 25–35% | 0x40–0x60 |
| Warm | 200 | 60–70 | 10–15% | 0x1A |
| Off | 0 | Ambient | 0% | 0x00 |

### 2.3 Stirring Motor Control (CAN servo on FDCAN2)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-010 | Drive the 24 V CAN servo stirring motor over FDCAN2 (PB12 RX / PB13 TX, SN65HVD230, 1 Mbps, 29-bit IDs): enable/disable, velocity (stirring) and position (home/park) commands at 50 Hz; parse feedback (velocity, position, current, temperature, faults) | Must | Commanded vs. reported speed within ±5 RPM; feedback age ≤ 40 ms |
| FR-MCU-010a | Switch the motor's 24 V (Q_STIR, PCF8574 #2 P5) on before the first enable frame and off after 60 s parked, on E-stop, on heartbeat loss and in the boot-safe state | Must | 0 V on J_STIR_PWR at reset |
| FR-MCU-010b | Configure the motor's command timeout ≤ 500 ms at start-up so a silent bus stops the arm | Must | Verified by stopping FDCAN2 traffic |
| FR-MCU-011 | Support stir patterns: continuous, intermittent, reverse, scrape, fold, vigorous (velocity profiles + signed direction) | Must | Pattern selected by RV1106 command (0x202), direction param |
| FR-MCU-012 | Stall / over-torque detection from motor-reported current and velocity error; INA219 as plausibility check | Must | STIR_STALL (0x10) within 500 ms of a blocked paddle; 3 retries then error |
| FR-MCU-012a | FDCAN2 bus-off or no motor feedback for 200 ms → disable, Q_STIR off, STIR_CAN_FAULT (0x15) | Must | Reported within 300 ms |
| FR-MCU-013 | Drive the Dispenser Servo Block: 4 servos (C1, F1, F2, F3) via PCA9685 (I2C1, addr 0x41, CH0-CH3), OE on PB4, 6.5 V rail enable via PCF8574 #2 P4 | Must | 50 Hz PWM, 500–2500 µs; ramped moves ≤ 3°/tick; one servo moving at a time; rail off when idle |
| FR-MCU-014 | Motor control task at 50 Hz (20 ms period) | Must | Highest priority FreeRTOS task |

### 2.4 Sensor Polling

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-021 | Read 2× SLD reservoir load cells (oil + water) at 10 Hz during dispensing | Must | Accuracy ±5% for closed-loop liquid dispensing; individual level monitoring with low-level alerts |
| FR-MCU-022 | Read battery pack voltage on PC1 (ADC1_IN7, 100k/22k divider) at 1 Hz and TP5100 CHRG/STDBY on PCF8574 #2 P6/P7; report `batt_mV`, charging/complete and `on_battery` in STATUS | Must | ±2 % of pack voltage; warning at 6.4 V, shutdown request at 6.2 V; BATTERY_FAULT (0x14) when neither CHRG nor STDBY is active with the pack below 8.0 V for 10 min or the pack is absent at boot |
| FR-MCU-023 | Parse coil temperature from CAN HEAT_STATUS | Must | Received at 10 Hz from induction module |
| FR-MCU-024 | Read INA219 bus current monitor | Should | I2C1 @ address 0x40, 24 V rail monitoring |
| FR-MCU-025 | Sensor polling task at 10 Hz (100 ms period) | Must | All sensor data available within each cycle |

### 2.5 Ingredient Dispensing

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-030 | FID: Index canister (F1), open steam gate (F3), N dose strokes of the measure wheel (F2, ¼ tsp each) with pre-dose jiggle, close gate | Must | Volumetric accuracy ±10% per dose; 1–40 doses per command; ACK carries doses_done + estimated mass |
| FR-MCU-031 | CID: Index slot over the base-plate aperture (C1), dwell 2 s, wiggle ±5° ×3; enforce ascending slot order | Must | NACK when slot_id ≤ current position; carousel returns to cover position on DISPENSER_HOME (0x38) and at recipe end |
| FR-MCU-031a | DSB fault handling: INA219 current window, move timeout (3 s), PCA9685 NACK → retry once (back off 10°) then DSB_STALL (0x12), rail off, OE high | Must | Stall reported within 1 s; servos limp after fault |
| FR-MCU-031b | Report carousel state on DISPENSER_STATUS (0x39): cid_pos, fid_box, gate_open, rail_on, busy | Must | Response within 100 ms |
| FR-MCU-032 | SLD: Drive peristaltic pumps + solenoids, closed-loop weight | Must | Accuracy ±5%, stop at target×0.95 |
| FR-MCU-033 | Tare load cells on command (0x37) | Must | Zero offset stored in SRAM |
| FR-MCU-034 | Report weight on query (0x35) | Must | Response within 100 ms |

#### 2.5.1 DSB Dispense Sequences

**FID dose (DISPENSE_FID box_id, qty):**
1. Rail on (PCF8574 #2 P4), OE low; index F1 to box_id (ramped, 4:3 gear-up → 60° per box)
2. Open steam gate: F3 → 70°
3. Per dose: F2 jiggle ±15° ×3, F2 → 180° (discharge), F2 → 0° (refill); ≈ 0.8 s per dose
4. Close gate: F3 → 0°; rail off; ACK with doses_done and estimated mass (doses × calibrated g/dose)

**CID dispense (DISPENSE_CID slot_id):**
1. NACK if slot_id ≤ current position (every bin passing the aperture empties)
2. Rail on; index C1 to slot_id (ramped) — contents free-fall through the chute
3. Dwell 2 s, wiggle ±5° ×3; rail off; ACK with new position

**Fault (any move):** INA219 24 V current above window for 300 ms, move timeout 3 s, or PCA9685 NACK → retry once (back off 10°, re-approach) → on second failure send DSB_STALL (0x12), rail off, OE high.

#### 2.5.2 SLD Closed-Loop Dispensing

1. Tare the channel's dedicated reservoir load cell (oil or water)
2. Open solenoid + start pump
3. Monitor weight loss on that channel's load cell @ 10 Hz
4. Stop pump when `weight_dispensed ≥ target × 0.95`
5. Close solenoid, report final weight to RV1106
6. If reservoir weight < low-level threshold, send STATUS (0x12) with error_code SLD_LOW_LEVEL to RV1106

### 2.6 RV1106 Communication (CAN bus)

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-040 | Host link is FDCAN1 (PB8/PB9) on the isolated 3-node CAN bus (J_CAN_HEAT), classic CAN 2.0B at 500 kbps, 11-bit IDs; FDCAN2 (PB12/PB13) is a separate regular bus to the stirring motor only (J_CAN_STIR) | Must | FDCAN1 accepts 0x001, 0x010, 0x180–0x182 and 0x200–0x23F via hardware filters; no frame is ever bridged between the two buses |
| FR-MCU-041 | Command frames: byte 0 = seq, bytes 1..7 = payload; answer every command with ACK/NAK (0x3FF: seq, cmd_type, result, ≤ 5 data bytes) | Must | ACK within 50 ms of a valid command; NAK with result code on invalid payload or state |
| FR-MCU-042 | No software framing or CRC; rely on CAN hardware ACK + CRC; reject frames with wrong DLC | Must | Bad-DLC frames counted and dropped |
| FR-MCU-043 | Send TELEMETRY (0x310) at 20 Hz unsolicited; LOADCELLS (0x311) at 10 Hz while dispensing | Must | motor_rpm, motor_current_dA, safety_state, flags (pot, on_battery, stir_enabled, …), error_code, seq |
| FR-MCU-044 | Send STATUS (0x312) on safety state change | Must | safety_state, error_code, flags, fault_detail |
| FR-MCU-045 | CAN comms task at 20 Hz (50 ms period) driven by the FDCAN1 RX FIFO interrupt | Must | Process incoming commands + queue outgoing |
| FR-MCU-046 | Monitor HB_AP (0x010, every 2 s) | Must | Missing for 5 s → safe state (HEAT_ON_OFF = 0, relay open) |
| FR-MCU-047 | USART2 (PA2/PA3) is a service link only: ST USART system bootloader for firmware updates (RV1106 drives BOOT0 on header pin 32 and NRST on header pin 38) and optional debug console | Should | `.bin` streamed, CRC verified before reset; no runtime protocol on USART2 |

### 2.7 Safety

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-050 | E-stop button (PB2, EXTI interrupt) → immediate shutdown | Must | <1 ms from button press to relay open |
| FR-MCU-051 | Safety relay control (PB0 → MOSFET → relay) | Must | Cuts AC mains to induction module |
| FR-MCU-052 | Thermal cutoff: HEAT_STATUS surface_temp >270 °C, CAN coil over-temp or HEAT_FAULT → E_STOP | Must | Checked every 100 ms (safety monitor cycle) |
| FR-MCU-053 | Hardware watchdog (IWDG, 5 s timeout) | Must | Kick in main loop; timeout → full reset |
| FR-MCU-054 | Pot detection via CAN (module-reported) | Must | No heat command if pot absent |
| FR-MCU-055 | Boot-safe state: all actuator outputs OFF until initialized — PCA9685 OE high, DSB rail off, Q_STIR off, LED ring off, relay open | Must | Pull-downs/pull-ups on MOSFET gates; verified with the MCU held in reset |
| FR-MCU-056 | On POWER_FAIL (COMP1): report within 50 ms with `batt_mV`; at 6.2 V request RV1106 shutdown and enter STOP mode | Must | Verified by pulling the 24 V input |

### 2.8 LED Ring (WS2812B)

The camera LED ring is driven by the STM32, not the application processor: WS2812B needs 5 V logic and a jitter-free 800 kHz bit stream, which the RV1106 cannot guarantee from a Linux user-space GPIO. The RV1106 only requests a lighting mode over the CAN bus.

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-060 | Drive 12–16 WS2812B LEDs from PB14 (TIM15_CH1 PWM + DMA, 800 kHz bit timing, 1.25 µs/bit) through a 74AHCT1G125 3.3 → 5 V level shifter | Must | No CPU bit-banging; 16-LED frame update ≤ 1 ms; ≥ 50 µs reset latch after each frame |
| FR-MCU-061 | Handle SET_LED (0x20): mode (uint8: OFF / CAPTURE / NIGHT), r, g, b (uint8), brightness_pct (uint8) | Must | Applied within one comms cycle (≤ 50 ms); ACK returned |
| FR-MCU-062 | Mode semantics: OFF = all LEDs off and ring 5 V switch (PCF8574 #2 P3) off; CAPTURE = supplied RGB at brightness_pct (default daylight white 255,255,255 @ 100 %); NIGHT = supplied RGB at brightness_pct (default 128,110,90 @ 30 %) | Must | Colour and brightness held until next SET_LED |
| FR-MCU-063 | Ring OFF in boot-safe state and on E_STOP | Must | PB14 idle low, PCF8574 #2 P3 low until first SET_LED after NORMAL |

---

## 3. Hardware Interfaces

### 3.1 Pin Assignment (LQFP-64)

| Pin | Function | Peripheral | Target |
|-----|----------|------------|--------|
| **PA0** | — | Available | Freed (P-ASD pump removed; dispensers now on PCA9685) |
| **PA1** | — | Available | Freed (was P-ASD solenoid V1, now via PCF8574) |
| **PA2** | USART2_TX | UART 1 Mbps | Service link to RV1106 (→ Luckfox Pico Zero header pin 10, UART2 RX): ST system-bootloader + debug only; runtime traffic is on FDCAN1 |
| **PA3** | USART2_RX | UART 1 Mbps | Service link from RV1106 (← Luckfox Pico Zero header pin 8, UART2 TX): ST system-bootloader + debug only |
| **PA4** | — | Available | Freed (stir motor EN; motor is now on FDCAN2) |
| **PA5** | — | Available | Freed (stir motor DIR; motor is now on FDCAN2) |
| **PA6** | TIM3_CH1 | PWM 25 kHz | Exhaust fan 1 |
| **PA7** | — | Available | Freed (SLD solenoid 1 moved to PCF8574 #2 P0) |
| **PA8** | — | Available | Freed (stir motor PWM; motor is now on FDCAN2) |
| **PA9** | — | Available | Freed (SLD solenoid 2 moved to PCF8574 #2 P1) |
| **PA10** | — | Available | Freed (CID-1 stepper removed) |
| **PA11** | USB_DM | USB 2.0 FS | USB D- (native USB, DFU+CDC) |
| **PA13** | SWDIO | Debug | SWD programming |
| **PA14** | SWCLK | Debug | SWD programming |
| **PB0** | GPIO output | Digital | Safety relay (via N-MOSFET) |
| **PB1** | GPIO input | Digital | Pot detection (from CAN module status, optional hardwire) |
| **PB2** | EXTI | Interrupt | E-stop button (NC, active-low) |
| **PB3** | — | Available | Freed (was IRQ to application processor; CAN needs no data-ready line) |
| **PB4** | GPIO output | Digital | PCA9685 OE (active-low) — DSB servo outputs off when high |
| **PB5** | — | Available | Freed (CID-2 linear actuator removed) |
| **PA15** | I2C1_SCL | I2C @ 100 kHz | PCA9685 + PCF8574 #2 + INA219 (shared bus) |
| **PB7** | I2C1_SDA | I2C @ 100 kHz | PCA9685 + PCF8574 #2 + INA219 (shared bus) |
| **PB8** | FDCAN1_RX | CAN 500 kbps | Isolated 3-node bus (RV1106 + induction surface) via ISO1050DUB #1 |
| **PB9** | FDCAN1_TX | CAN 500 kbps | Isolated 3-node bus (RV1106 + induction surface) via ISO1050DUB #1 |
| **PB10** | GPIO output | Software PWM 25 kHz | Exhaust fan 2 |
| **PB12** | FDCAN2_RX (AF9) | CAN 1 Mbps | Regular (non-isolated) stir-motor bus via SN65HVD230 → J_CAN_STIR |
| **PB13** | FDCAN2_TX (AF9) | CAN 1 Mbps | Regular (non-isolated) stir-motor bus via SN65HVD230 → J_CAN_STIR |
| **PB14** | TIM15_CH1 | PWM + DMA, 800 kHz | WS2812B LED ring data (via 74AHCT1G125 3.3 → 5 V level shifter to J_LED pin 2) |
| **PB15** | — | Available | Freed (was SPI2_MOSI; host link now on FDCAN1, USART2 is the service link) |
| **PC0** | ADC | Analog | USB VBUS detect (100k/100k divider; moved from PA3, which is now USART2_RX) |
| **PC1** | ADC1_IN7 | Analog | 2S battery pack voltage (100k/22k divider from BAT+) |
| **PC2** | — | Available | Freed (CID-2 linear actuator removed) |
| **PC3** | GPIO output | PWM (software) | SLD pump 1 PWM (TB6612) |
| **PC4** | GPIO output | Digital | SLD pump 1 DIR (TB6612) |
| **PC5** | GPIO output | PWM (software) | SLD pump 2 PWM (TB6612) |
| **PC6** | GPIO output | Digital | SLD pump 2 DIR (TB6612) |
| **PC7** | — | Available | Freed (was P-ASD solenoid V3, now via PCF8574) |
| **PD2** | — | Available | Freed (was P-ASD solenoid V4, now via PCF8574) |
| **PB11** | — | Available | Freed (was CID-1 full-extend limit) |
| **PC7** | TIM8_CH2 | PWM | Piezo buzzer (via MOSFET) |
| **PC8** | — | Available | Freed (status LED moved to PCF8574 #2 P2) |

### 3.2 I2C1 Bus (PA15/PB7)

| Address | Device | Data |
|---------|--------|------|
| 0x21 | PCF8574 #2 | SLD solenoid 1 (P0), SLD solenoid 2 (P1), status LED (P2), LED ring enable (P3), DSB 6.5 V rail enable (P4), stir-motor 24 V enable Q_STIR (P5), TP5100 CHRG in (P6), TP5100 STDBY in (P7) |
| 0x40 | INA219 | 24 V rail voltage + current (DSB stall-detection window, stir-motor plausibility) |
| 0x41 | PCA9685 | Dispenser Servo Block PWM: CH0 C1 CID index, CH1 F1 FID index, CH2 F2 FID dose, CH3 F3 FID steam gate |

### 3.3 CAN Buses

**FDCAN1 — isolated host + heater bus (J_CAN_HEAT)**
- Transceiver: ISO1050DUB #1 (isolated, 5 kV RMS) on the Unified PCB; shares the isolated 5 V_ISO/GND_ISO domain (B0505S-1WR3) with ISO1050DUB #2 of the RV1106 node (MCP2518FD on SPI0 CS1)
- Bit rate: 500 kbps (CAN 2.0B, classic frames, 11-bit IDs)
- Nodes: STM32 (this MCU), RV1106 application processor, induction surface MCU — one bus, J_CAN_HEAT to the module
- Termination: 120 Ω at J_CAN_HEAT (both on-board nodes form a short stub) and inside the module
- Traffic: host commands 0x2xx and reports 0x3xx (RV1106 ↔ STM32), heater control 0x1xx (RV1106 → module; STM32 sends HEAT_ON_OFF = 0 only), E_STOP 0x001 and HB_AP 0x010 — see §5.2

**FDCAN2 — regular stir-motor bus (J_CAN_STIR)**
- Transceiver: SN65HVD230 (3.3 V, non-isolated); PB12 RX / PB13 TX (AF9)
- Bit rate: 1 Mbps (CAN 2.0B, 29-bit IDs per the motor protocol)
- Nodes: STM32 (master) and the stirring motor's integrated controller; 120 Ω at J_CAN_STIR and at the motor
- Traffic: enable/disable, velocity and position commands at 50 Hz; motor feedback (velocity, position, current, temperature, faults); wrapped in `stir_motor.c`
- Power: 24 V to the motor on J_STIR_PWR through Q_STIR (PCF8574 #2 P5)
- Never bridged to FDCAN1

### 3.4 SLD Reservoir Load Cells (HX711)

- SLD oil reservoir: HX711 #1 on PC11 (SCK) / PC12 (DOUT), 2 kg strain gauge
- SLD water reservoir: HX711 #2 on PC9 (SCK) / PC10 (DOUT), 2 kg strain gauge
- Interface: Bit-banged GPIO
- Sample rate: 10 Hz (RATE pin low)
- Resolution: 24-bit ADC → ~1 g at 2 kg full scale

---

## 4. Software Architecture

### 4.1 RTOS Configuration

- **RTOS:** FreeRTOS 10.x
- **Language:** C (MISRA C subset for safety-critical paths)
- **DSP:** CMSIS-DSP library for signal filtering (no PID on the MCU; the temperature loop runs on the RV1106)
- **Heap:** heap_4 (coalescing), ~64 KB allocated
- **Tick rate:** 1 kHz (1 ms)

### 4.2 Task Table

| Task | Rate | Period | Priority | Stack | Description |
|------|------|--------|----------|-------|-------------|
| Motor Control | 50 Hz | 20 ms | Highest (4) | 512 B | FDCAN2 velocity/position commands to the stir motor, feedback parsing, ramps, stir patterns, stall detection |
| Safety Monitor | 10 Hz | 100 ms | Highest (4) | 256 B | HEAT_STATUS thermal limits, E-stop, heartbeat, Q_STIR/DSB rail/relay authority, watchdog kick |
| Dispense | 50 Hz (while active) | 20 ms | High (3) | 512 B | PCA9685 ramped moves, DSB rail, TB6612 pumps, solenoids, HX711 closed loop |
| Sensor Poll | 10 Hz | 100 ms | Medium (2) | 512 B | Load cells, INA219, battery ADC (PC1) and charger status (1 Hz); aggregate TELEMETRY |
| CAN Comms | 20 Hz | 50 ms | High (3) | 1024 B | FDCAN1 RX FIFO → command parser, ACK/NAK, TELEMETRY/STATUS TX, HEAT_STATUS capture for the safety monitor, SET_LED forwarding |

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
| NORMAL | WARNING | HEAT_STATUS coil temp > 250 °C, battery low (< 6.4 V on battery), stir-motor temperature > 80 °C |
| WARNING | CRITICAL | HEAT_STATUS surface_temp > 260 °C, or CAN fault from induction module |
| CRITICAL | E_STOP | surface_temp > 270 °C, CAN coil over-temp, HEAT_FAULT, E-stop button, RV1106 heartbeat timeout (5 s) |
| E_STOP | NORMAL | Manual hardware reset (E-stop button released + PB2 debounce) |

### 4.4 Boot Sequence

1. **Reset** → SystemInit (clock to 170 MHz HSE + PLL)
2. **HAL_Init** → SysTick, NVIC priorities
3. **Peripheral init** → GPIO (all outputs LOW/safe, Q_STIR and DSB rail off), ADC (VBUS, battery), TIM (incl. TIM15 + DMA for WS2812B), FDCAN1 (filters for 0x001, 0x010, 0x18x, 0x2xx), FDCAN2 (motor feedback filter, 1 Mbps), I2C, USART2 (service link)
4. **Safety check** → Verify E-stop not pressed, relay OFF, battery pack voltage 5.5–8.5 V, self-test I2C devices (0x21, 0x40, 0x41)
5. **FreeRTOS start** → Create tasks, start scheduler
6. **Wait for RV1106 heartbeat** → First HB_AP (0x010) on the bus → safety state NORMAL
7. **IDLE mode** → Sensors polling at 1 Hz, heartbeat monitoring, awaiting commands; stir motor enumerated on FDCAN2 (command timeout configured) and left disabled with 24 V off

---

## 5. Communication Protocols

### 5.1 UART Service Link (STM32 ↔ RV1106, flashing and debug only)

- Link: USART2 (PA2 TX / PA3 RX) ↔ Luckfox Pico Zero UART2 (header pins 10 / 8), 3.3 V. It carries **no runtime protocol**: host commands and telemetry are on the CAN bus (§5.2).
- Firmware update: USART2 is the ST system-bootloader UART; the RV1106 drives BOOT0 (header GPIO 32) / NRST (GPIO 38) and streams the `.bin` over these wires, verifying the CRC before reset
- Debug: optional console at 1,000,000 baud, 8N1
- NUCLEO-G474RE prototype caveat: PA2/PA3 are tied to the ST-LINK VCP through SB17 and SB23 (ON by default, UM2505 rev 4); remove SB17/SB23 and fit SB18/SB22 to route them to Arduino D1/D0 on CN9, or take them from morpho CN10 pins 35 (PA2) and 37 (PA3); verify against the MB1367-G474RE-C04 schematic before soldering, or use the custom Controller PCB

### 5.2 CAN Bus Protocol (shared bus: RV1106, STM32, induction module)

Identifiers are owned by [[02-Controller-Software-Architecture#7.2 Message Types|Controller Software Architecture §7.2]]; this is the MCU view.

| CAN ID | Direction | DLC | MCU behaviour |
|--------|-----------|-----|---------------|
| 0x001 E_STOP | any ↔ all | 2 | Received: run the E-stop sequence (§7.3). Sent (src_node = 2) on any CRITICAL → E_STOP transition |
| 0x010 HB_AP | RV1106 → all | 5 | Resets the 5 s heartbeat timer |
| 0x100 HEAT_SET_TEMP | RV1106 → module | 4 | Never sent by the MCU; observed only for logging |
| 0x101 HEAT_ON_OFF | RV1106 or MCU → module | 1 | MCU sends 0 on thermal fault, heartbeat loss, E-stop |
| 0x103 HEAT_SET_POWER | RV1106 → module | 2 | Never sent by the MCU; observed only for logging |
| 0x180 HEAT_STATUS | module → all | 8 | surface_temp, coil_temp and fault_flags feed the safety monitor; pot_detected and surface_temp feed TELEMETRY flags |
| 0x181 HEAT_FAULT | module → all | 4 | Mapped to CAN_FAULT handling (§7.2) |
| 0x202, 0x220–0x225 | RV1106 → MCU | 1–6 | SET_STIR, SET_LED, SET_SPEED, ARM_STOP, ARM_HOME, ARM_STATUS, SET_RAMP (byte 0 = seq) |
| 0x230–0x239 | RV1106 → MCU | 1–4 | DISPENSE_FID/CID/SLD, QUERY_WEIGHT, PREFLIGHT, TARE, DISPENSER_HOME, DISPENSER_STATUS (byte 0 = seq) |
| 0x310 TELEMETRY | MCU → RV1106 | 8 | motor_rpm (uint16), motor_current_dA (int16), safety_state, flags, error_code, seq — 20 Hz |
| 0x311 LOADCELLS | MCU → RV1106 | 5 | oil_g, water_g (int16), flags — 10 Hz while dispensing |
| 0x312 STATUS | MCU → RV1106 | 8 | safety_state, error_code, flags, fault_detail — on change; fault_detail carries batt_mV for POWER_FAIL / BATTERY_FAULT |
| 0x3FF ACK/NAK | MCU → RV1106 | 3–8 | seq, cmd_type, result_code, data[0..4] |

- Reference heater IDs follow [[../05-Subsystems/01-Induction-Heating|Induction Heating]] §3.2 and are adapted to the chosen module
- Timeouts: HB_AP missing 5 s → safe state; no HEAT_STATUS for 500 ms or FDCAN bus-off → CAN_FAULT (relay open, since the heater cannot be commanded)
- Pot detection: pot-absent in HEAT_STATUS is flagged in TELEMETRY; the RV1106 pauses heating

### 5.3 I2C Protocol

- Bus speed: 100 kHz (standard mode)
- Pull-ups: 4.7 kΩ to 3.3 V (on the Unified PCB)
- PCA9685 (0x41): 50 Hz prescale, CH0–CH3 on/off counts for 500–2,500 µs pulses
- PCF8574 #2 (0x21): one byte write for outputs P0–P5; P6/P7 written high and read back as charger status
- INA219 (0x40): Read bus voltage register 0x02, current register 0x04

---

## 6. Power Management

### 6.1 Power Supply

- Input: 5V_MAIN from the Unified PCB TPS54531 (VSYS = 24 V rail or 2S battery via diode-OR), OR'd with USB-C 5 V for bench programming
- LDO: AMS1117-3.3 (SOT-223), 5 V → 3.3 V @ 800 mA max
- Battery backup: the 2S pack keeps the MCU, the RV1106 and the LCD running through an outage; the MCU monitors pack voltage (PC1) and charger status (PCF8574 #2 P6/P7)
- Decoupling: 10 µF input, 10 µF output, 100 nF per VDD pin
- Typical consumption: ~0.5 W (170 MHz, all peripherals active)

### 6.2 Power States

| State | Description | Current (3.3 V) |
|-------|-------------|-----------------|
| Active | All tasks running, CAN + motor + sensors active | ~150 mA |
| Idle | Sensors at 1 Hz, awaiting commands | ~80 mA |
| E_STOP | Relay open, buzzer on, minimal processing | ~100 mA |
| Reset | After IWDG timeout, re-initializing | ~50 mA |

---

## 7. Safety & Fault Handling

### 7.1 Safety Mechanisms

| Mechanism | Implementation | Response Time |
|-----------|---------------|---------------|
| E-stop button | PB2 EXTI interrupt (highest NVIC priority) | <1 ms |
| Safety relay | PB0 → N-MOSFET → relay coil (NC relay, fail-safe open) | <5 ms |
| Hardware watchdog (IWDG) | 5 s timeout, kicked in safety monitor task | 5 s (worst case) |
| Thermal cutoff (surface) | HEAT_STATUS surface_temp > 270 °C → E_STOP | ≤200 ms (status interval + poll) |
| Thermal cutoff (CAN coil) | CAN coil over-temp → E_STOP | ≤500 ms (CAN status interval) |
| Stir motor | Motor disable on FDCAN2 + Q_STIR 24 V switch off on E-stop / heartbeat loss / FDCAN2 fault | ≤10 ms |
| Battery | Pack voltage 6.2 V → shutdown request; charger fault → BATTERY_FAULT | 1 s |
| CAN fault | No HEAT_STATUS for 500 ms or bus-off → relay open (heater cannot be commanded), alert | 500 ms |
| RV1106 heartbeat loss | No HB_AP (0x010) for 5 s → HEAT_ON_OFF = 0, relay open, safe state | 5 s |
| Overcurrent | INA219 > threshold → warning/shutdown | ≤100 ms |

### 7.2 Fault Table

| Fault Code | Name | Severity | Action |
|------------|------|----------|--------|
| 0x01 | OVER_TEMP_SURFACE | Critical | E_STOP, cut relay, log (HEAT_STATUS surface_temp > 270 °C) |
| 0x02 | OVER_TEMP_COIL | Critical | E_STOP, cut relay, log |
| 0x03 | E_STOP_PRESSED | Critical | E_STOP, cut relay, buzzer |
| 0x04 | CAN_FAULT | Critical | Open relay (heater unreachable on the bus), alert RV1106 when the bus returns |
| 0x05 | RV1106_HEARTBEAT_LOSS | Critical | HEAT_ON_OFF = 0, relay open, stir motor disabled + Q_STIR off (safe state) |
| 0x10 | STIR_STALL | Warning | Disable motor, retry 3×, alert RV1106 (motor-reported current / velocity error) |
| 0x11 | SLD_LOAD_CELL_DRIFT | Warning | Alert RV1106, flag SLD dispense unreliable |
| 0x12 | DSB_STALL | Warning | Dispenser servo stall/timeout: retry once (back off, re-approach), then rail off, OE high, alert RV1106 |
| 0x13 | SLD_DISPENSE_ERROR | Warning | Stop pump, alert RV1106 with actual vs target |
| 0x14 | BATTERY_FAULT | Warning | Pack absent, charger fault or NTC out of range; cooking allowed, backup unavailable; alert RV1106 |
| 0x15 | STIR_CAN_FAULT | Warning | FDCAN2 bus-off or no motor feedback 200 ms: disable, Q_STIR off, alert RV1106 |
| 0x16 | POWER_FAIL | Info | 24 V lost, running on battery; batt_mV in fault_detail |
| 0x20 | CAN_TX_TIMEOUT | Info | Retry 3×, then CAN_FAULT |
| 0x21 | I2C_NACK | Info | Retry 3×, use last-known value |

### 7.3 E-Stop Sequence

1. **PB2 EXTI fires** (or E_STOP 0x001 received on the CAN bus)
2. Safety relay opened (PB0 LOW → relay de-energizes → AC cut)
3. Stir motor: disable frame on FDCAN2, Q_STIR (PCF8574 #2 P5) off; PCA9685 OE high, DSB rail off; fan/pump PWM to 0 %
4. CAN: send HEAT_ON_OFF = 0 (0x101) and broadcast E_STOP (0x001, src_node = 2) on FDCAN1 — belt-and-suspenders with the relay
5. Buzzer activated (PC7 PWM)
6. STATUS (0x312) sent on the bus: `safety_state = E_STOP`
7. **Hold state** — only IWDG kick continues; no commands accepted
8. **Reset** — PB2 debounce clears → re-init → wait for HB_AP → NORMAL

---

## 8. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Motor control period | 20 ms ± 0.5 ms | TIM interrupt jitter |
| E-stop latency | <1 ms | PB2 edge → relay GPIO toggle |
| CAN command dispatch | <1 ms | RX FIFO interrupt → ACK queued |
| WS2812B frame update (16 LEDs) | <1 ms | DMA start → transfer complete |
| CAN command round-trip | <10 ms | RV1106 command → ACK on the bus |
| Sensor poll cycle | <50 ms (all sensors) | Cycle start → data ready |
| Stir motor command latency | < 20 ms | SET_STIR received → first FDCAN2 velocity frame |
| Stir speed accuracy | ±5 RPM | Motor-reported vs. external tachometer |
| Dispensing accuracy (FID) | ±10% per ¼ tsp dose | Volumetric measure wheel, weighed over 10 doses |
| Dispensing accuracy (SLD) | ±5% | Load cell vs target weight |
| FreeRTOS CPU utilization | <70% | Idle task runtime measurement |
| Flash usage | <256 KB | Linker map |
| SRAM usage | <96 KB | Stack + heap analysis |

---

## 9. Dependencies & Constraints

### 9.1 Hardware Dependencies

- Unified PCB (160×90 mm) provides the STM32, LDO, buck converters, PCA9685, TB6612, MOSFETs, both CAN transceivers, the battery charger and all connectors
- Isolated CAN port on the Unified PCB (ISO1050DUB #1 for FDCAN1, ISO1050DUB #2 + MCP2518FD for the RV1106 node, B0505S-1WR3 isolated supply, J_CAN_HEAT to the induction surface)
- Regular CAN port on the Unified PCB (SN65HVD230 on FDCAN2, J_CAN_STIR) and switched 24 V (Q_STIR, J_STIR_PWR) to the stirring motor
- Luckfox Pico Zero in the J_AP slot: header pins 8/10 (UART2) connect to USART2 PA2/PA3 at 3.3 V as the service link (bootloader/debug only)
- 74AHCT1G125 level shifter on the Unified PCB between PB14 and J_LED (WS2812B 5 V data)
- 2S Li-ion pack on J_BAT with TP5100 charger; pack voltage divider to PC1

### 9.2 Firmware Dependencies

- STM32 HAL drivers (STM32CubeMX generated): GPIO, ADC, TIM, USART, I2C, FDCAN
- FreeRTOS 10.x kernel + CMSIS-RTOS2 wrapper
- CMSIS-DSP library (filtering)
- Custom HX711 bit-bang driver
- CRC-16/CCITT lookup table
- CAN message codec (ID map, payload packing, seq/ACK) and TIM15 + DMA WS2812B driver
- `stir_motor.c`: wrapper for the stirring motor's CAN protocol on FDCAN2 (enable, velocity, position, feedback, timeout configuration)

### 9.3 Constraints

- MISRA C compliance for safety-critical tasks (safety monitor, E-stop handler, CAN command dispatcher, heater off-switch)
- No dynamic memory allocation after boot (all FreeRTOS objects static)
- No floating-point in ISRs (FPU context save overhead)
- Both CAN buses require 120 Ω termination at both ends; FDCAN1 (isolated) and FDCAN2 (regular) share nothing
- I2C bus: 3 devices (INA219 + PCA9685 + PCF8574 #2), total bus capacitance must stay under 400 pF

### 9.4 Cross-References

| Topic | Document |
|-------|----------|
| RV1106 MPU spec | [[04-MPU-Functional-Specification]] |
| State machine details | [[03-Main-Loop-State-Machine]] |
| Software architecture | [[02-Controller-Software-Architecture]] |
| Unified PCB design | [[01-Unified-PCB-Design]] |
| Dispensing subsystems | [[03-Ingredient-Dispensing]] |
| Hardware architecture | [[01-Epicura-Architecture]] |
| Technical specifications | [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications]] |
