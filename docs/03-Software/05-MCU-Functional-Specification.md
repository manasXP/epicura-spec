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

---

## 1. Overview

The STM32G474RE is the real-time motor/sensor controller and safety guardian for Epicura. It runs FreeRTOS with four primary tasks: PID temperature control (10 Hz), BLDC motor drive (50 Hz task rate), sensor polling (10 Hz), and RV1106 communications (20 Hz). It owns all safety-critical paths including the heater relay, E-stop handling, and watchdog supervision.

### 1.1 Hardware Summary

| Parameter | Value |
|-----------|-------|
| Core | Cortex-M4F @ 170 MHz, single-precision FPU |
| Flash | 512 KB |
| SRAM | 128 KB |
| ADC | 5× 12-bit (up to 4 Msps) |
| Timers | Advanced (TIM1), GP (TIM2/3/4), basic |
| Comm | 3× UART, 3× SPI, 4× I2C, FDCAN |
| Package | LQFP-64 |
| Power | 3.3 V via AMS1117-3.3 LDO (from 5 V), ~0.5 W typical |

---

## 2. Functional Requirements

### 2.1 PID Temperature Control

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-001 | Closed-loop PID at 10 Hz (100 ms period) | Must | Steady-state error ≤ ±5 °C |
| FR-MCU-002 | Default PID gains: Kp=2.0, Ki=0.5, Kd=0.1 | Must | Tunable at runtime via UART command |
| FR-MCU-003 | Overshoot protection: clamp at setpoint + 10 °C | Must | Integral windup reset when exceeded |
| FR-MCU-004 | Temperature ramp control (°C/min configurable) | Should | Linear ramp from current to target |
| FR-MCU-005 | Read IR thermometer (MLX90614) for food surface temp | Must | I2C @ 100 kHz, accuracy ±0.5 °C |
| FR-MCU-006 | Read coil temperature from induction module via CAN | Must | HEAT_STATUS message, coil_temp field |
| FR-MCU-007 | Send power commands to induction module via CAN | Must | FDCAN1 @ 500 kbps, power level 0–1800 W |

### 2.2 Power Level Profiles

| Profile | Power (W) | Temp Range (°C) | Duty Cycle | CAN Command Value |
|---------|-----------|-----------------|------------|-------------------|
| Sear | 1,800 | 200–250 | 100% | 0xFF |
| Boil | 1,500 | 100 | 85% | 0xD9 |
| Simmer | 400–600 | 80–95 | 25–35% | 0x40–0x60 |
| Warm | 200 | 60–70 | 10–15% | 0x1A |
| Off | 0 | Ambient | 0% | 0x00 |

### 2.3 Servo Motor Control

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-010 | Drive BLDC stirring motor at 10 kHz PWM via TIM1_CH1 (PA8) + PA4 (EN) + PA5 (DIR) | Must | 0–100% duty cycle speed, digital enable/direction |
| FR-MCU-011 | Support stir patterns: circular, figure-8, scrape, fold (via duty cycle + DIR toggle) | Must | Pattern selected by RV1106 command (0x02), direction param added |
| FR-MCU-012 | Stall detection via INA219 24V current spike or FG dropout (future) | Should | Alert RV1106 if motor draws >3 A for >500 ms |
| FR-MCU-013 | Drive the Dispenser Servo Block: 4 servos (C1, F1, F2, F3) via PCA9685 (I2C1, addr 0x41, CH0-CH3), OE on PB4, 6.5 V rail enable via PCF8574 #2 P4 | Must | 50 Hz PWM, 500–2500 µs; ramped moves ≤ 3°/tick; one servo moving at a time; rail off when idle |
| FR-MCU-014 | Motor control task at 50 Hz (20 ms period) | Must | Highest priority FreeRTOS task |

### 2.4 Sensor Polling

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-021 | Read 2× SLD reservoir load cells (oil + water) at 10 Hz during dispensing | Must | Accuracy ±5% for closed-loop liquid dispensing; individual level monitoring with low-level alerts |
| FR-MCU-022 | Read IR thermometer at 10 Hz | Must | MLX90614 via I2C1 (PA15/PB7) |
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

### 2.6 RV1106 Communication

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-040 | UART bridge on USART2 (PA2 TX / PA3 RX), 1,000,000 baud, 8N1, 3.3 V, RX via DMA circular buffer | Must | SOF 0x7E framing with 0x7D byte-stuffing; receiver resynchronises on SOF after any corrupt byte |
| FR-MCU-041 | No data-ready / IRQ line: outgoing messages are pushed unsolicited as soon as queued | Must | PB3 freed; RV1106 bridge thread reads continuously (`VMIN=1`) |
| FR-MCU-042 | Validate CRC-16/CCITT on all received messages | Must | NAK on CRC mismatch |
| FR-MCU-043 | Send telemetry at 20 Hz (0x10) | Must | temp, motor_rpm, weight, state |
| FR-MCU-044 | Send status on safety state change (0x12) | Must | safety_state, error_code, flags |
| FR-MCU-045 | Comms task at 20 Hz (50 ms period) | Must | Process incoming commands + queue outgoing |
| FR-MCU-046 | Monitor RV1106 heartbeat (expect every 2 s) | Must | If missed for 5 s → IWDG-triggered safe state |
| FR-MCU-047 | Same USART2 link carries STM32 firmware updates via the ST USART system bootloader | Should | RV1106 drives BOOT0 (header pin 32) and NRST (header pin 38); `.bin` streamed, CRC verified before reset |

### 2.7 Safety

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-MCU-050 | E-stop button (PB2, EXTI interrupt) → immediate shutdown | Must | <1 ms from button press to relay open |
| FR-MCU-051 | Safety relay control (PB0 → MOSFET → relay) | Must | Cuts AC mains to induction module |
| FR-MCU-052 | Thermal cutoff: IR >270 °C or CAN coil over-temp → E_STOP | Must | Checked every 100 ms (sensor poll cycle) |
| FR-MCU-053 | Hardware watchdog (IWDG, 5 s timeout) | Must | Kick in main loop; timeout → full reset |
| FR-MCU-054 | Pot detection via CAN (module-reported) | Must | No heat command if pot absent |
| FR-MCU-055 | Boot-safe state: all actuator outputs OFF until initialized | Must | 100 kΩ pull-downs on MOSFET gates |

### 2.8 LED Ring (WS2812B)

The camera LED ring is driven by the STM32, not the application processor: WS2812B needs 5 V logic and a jitter-free 800 kHz bit stream, which the RV1106 cannot guarantee from a Linux user-space GPIO. The RV1106 only requests a lighting mode over the bridge.

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
| **PA2** | USART2_TX | UART 1 Mbps | Bridge to RV1106 (→ Luckfox Pico Zero header pin 10, UART2 RX); also ST system-bootloader UART |
| **PA3** | USART2_RX | UART 1 Mbps | Bridge from RV1106 (← Luckfox Pico Zero header pin 8, UART2 TX); also ST system-bootloader UART |
| **PA4** | GPIO output | Digital | BLDC motor EN (enable, via J_STACK Pin 39) |
| **PA5** | GPIO output | Digital | BLDC motor DIR (direction, via J_STACK Pin 40) |
| **PA6** | TIM3_CH1 | PWM 25 kHz | Exhaust fan 1 |
| **PA7** | — | Available | Freed (SLD solenoid 1 moved to PCF8574 #2 P0) |
| **PA8** | TIM1_CH1 | PWM 10 kHz | BLDC stirring motor (speed) |
| **PA9** | — | Available | Freed (SLD solenoid 2 moved to PCF8574 #2 P1) |
| **PA10** | — | Available | Freed (CID-1 stepper removed) |
| **PA11** | USB_DM | USB 2.0 FS | USB D- (native USB, DFU+CDC) |
| **PA13** | SWDIO | Debug | SWD programming |
| **PA14** | SWCLK | Debug | SWD programming |
| **PB0** | GPIO output | Digital | Safety relay (via N-MOSFET) |
| **PB1** | GPIO input | Digital | Pot detection (from CAN module status, optional hardwire) |
| **PB2** | EXTI | Interrupt | E-stop button (NC, active-low) |
| **PB3** | — | Available | Freed (was IRQ to application processor; UART bridge needs no data-ready line) |
| **PB4** | GPIO output | Digital | PCA9685 OE (active-low) — DSB servo outputs off when high |
| **PB5** | — | Available | Freed (CID-2 linear actuator removed) |
| **PA15** | I2C1_SCL | I2C @ 100 kHz | MLX90614 + INA219 (shared bus) |
| **PB7** | I2C1_SDA | I2C @ 100 kHz | MLX90614 + INA219 (shared bus) |
| **PB8** | FDCAN1_RX | CAN | Induction module RX (via SN65HVD230) |
| **PB9** | FDCAN1_TX | CAN | Induction module TX (via SN65HVD230) |
| **PB10** | GPIO output | Software PWM 25 kHz | Exhaust fan 2 |
| **PB12** | — | Available | Freed (was SPI2_NSS; bridge moved to USART2) |
| **PB13** | — | Available | Freed (was SPI2_SCK; bridge moved to USART2) |
| **PB14** | TIM15_CH1 | PWM + DMA, 800 kHz | WS2812B LED ring data (via 74AHCT1G125 3.3 → 5 V level shifter to J_LED pin 2) |
| **PB15** | — | Available | Freed (was SPI2_MOSI; bridge moved to USART2) |
| **PC0** | ADC | Analog | USB VBUS detect (100k/100k divider; moved from PA3, which is now USART2_RX) |
| **PC1** | — | Available | Freed (pot load cells removed) |
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
| 0x21 | PCF8574 #2 | SLD solenoid 1 (P0), SLD solenoid 2 (P1), status LED (P2), LED ring enable (P3), DSB 6.5 V rail enable (P4), P5-P7 reserved |
| 0x40 | INA219 | 24 V rail voltage + current (also DSB stall-detection window) |
| 0x41 | PCA9685 | Dispenser Servo Block PWM: CH0 C1 CID index, CH1 F1 FID index, CH2 F2 FID dose, CH3 F3 FID steam gate |
| 0x5A | MLX90614 | Object + ambient temperature |

### 3.3 CAN Bus (FDCAN1)

- Transceiver: SN65HVD230 (3.3 V)
- Bit rate: 500 kbps (CAN 2.0B)
- Bus: 2-wire (CANH/CANL) to induction module
- Termination: 120 Ω at each end
- Messages: power set, power query, status request, fault report

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
- **DSP:** CMSIS-DSP library for PID computation
- **Heap:** heap_4 (coalescing), ~64 KB allocated
- **Tick rate:** 1 kHz (1 ms)

### 4.2 Task Table

| Task | Rate | Period | Priority | Stack | Description |
|------|------|--------|----------|-------|-------------|
| Motor Control | 50 Hz | 20 ms | Highest (4) | 512 B | BLDC PWM duty + EN/DIR GPIO updates, stir patterns |
| Safety Monitor | 10 Hz | 100 ms | Highest (4) | 256 B | Thermal limits, E-stop, watchdog kick |
| PID Control | 10 Hz | 100 ms | High (3) | 512 B | Read IR + CAN coil temp, compute PID, send CAN |
| Sensor Poll | 10 Hz | 100 ms | Medium (2) | 512 B | Load cells, INA219, aggregate telemetry |
| RV1106 Comms | 20 Hz | 50 ms | Medium (2) | 1024 B | USART2 DMA RX + frame codec, command parser, telemetry TX, SET_LED forwarding |

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
| NORMAL | WARNING | CAN coil temp > 250 °C |
| WARNING | CRITICAL | IR > 260 °C, or CAN fault from induction module |
| CRITICAL | E_STOP | IR > 270 °C, CAN coil over-temp, E-stop button, RV1106 heartbeat timeout (5 s) |
| E_STOP | NORMAL | Manual hardware reset (E-stop button released + PB2 debounce) |

### 4.4 Boot Sequence

1. **Reset** → SystemInit (clock to 170 MHz HSE + PLL)
2. **HAL_Init** → SysTick, NVIC priorities
3. **Peripheral init** → GPIO (all outputs LOW/safe), ADC, TIM (incl. TIM15 + DMA for WS2812B), USART2, I2C, FDCAN
4. **Safety check** → Verify E-stop not pressed, relay OFF, self-test sensors
5. **FreeRTOS start** → Create tasks, start scheduler
6. **Wait for RV1106 heartbeat** → First heartbeat received → safety state NORMAL
7. **IDLE mode** → Sensors polling at 1 Hz, heartbeat monitoring, awaiting commands

---

## 5. Communication Protocols

### 5.1 UART Bridge Protocol (STM32 ↔ RV1106)

See [[04-MPU-Functional-Specification#5.1 UART Bridge Protocol]] for full frame definition.

- Link: USART2 (PA2 TX / PA3 RX) ↔ Luckfox Pico Zero UART2 (header pins 10 / 8), 1,000,000 baud, 8N1, 3.3 V. UART is also the production link (no CAN alternative).
- Framing: SOF 0x7E, byte-stuffing with 0x7D escape, then msg_id, msg_type, payload_len, payload (≤ 64 bytes), CRC-16/CCITT. Message body and type codes are unchanged from the earlier SPI design.
- RX: DMA circular buffer + idle-line interrupt; parser discards bytes until SOF and validates CRC before dispatch
- On valid command: parse, execute, queue ACK/response
- On CRC mismatch: NAK (0xFF) response
- No data-ready / IRQ line: TELEMETRY (0x10) is pushed unsolicited at 20 Hz; other responses as soon as queued
- Heartbeat RV1106 → STM32 every 2 s; IWDG 5 s. ACK timeout 500 ms, 3 retries. E_STOP (0x04) needs no ACK
- SET_LED (0x20) is handled by the comms task and forwarded to the LED ring driver (§2.8)
- Firmware update: USART2 is also the ST system-bootloader UART; the RV1106 drives BOOT0 / NRST and streams the `.bin` over the same wires
- NUCLEO-G474RE prototype caveat: PA2/PA3 are tied to the ST-LINK VCP through SB17 and SB23 (ON by default, UM2505 rev 4); remove SB17/SB23 and fit SB18/SB22 to route them to Arduino D1/D0 on CN9, or take them from morpho CN10 pins 35 (PA2) and 37 (PA3); verify against the MB1367-G474RE-C04 schematic before soldering, or use the custom Controller PCB

### 5.2 CAN Bus Protocol (STM32 ↔ Induction Module)

| CAN ID | Direction | DLC | Description |
|--------|-----------|-----|-------------|
| 0x100 | STM32 → Module | 2 | Set power level (0x00–0xFF) |
| 0x101 | STM32 → Module | 1 | Status request |
| 0x200 | Module → STM32 | 4 | Status response (temp, power, fault flags) |
| 0x201 | Module → STM32 | 2 | Fault report (fault code, severity) |

- Timeout: If no module response within 500 ms → CAN_FAULT, reduce to safe power
- Pot detection: Module reports pot-absent in status → STM32 blocks all SET_TEMP commands

### 5.3 I2C Protocol

- Bus speed: 100 kHz (standard mode)
- Pull-ups: 4.7 kΩ to 3.3 V (on Controller PCB)
- MLX90614 (0x5A): Read object temp register 0x07, ambient temp register 0x06
- INA219 (0x40): Read bus voltage register 0x02, current register 0x04

---

## 6. Power Management

### 6.1 Power Supply

- Input: 5 V from Driver PCB 5 V rail (buck from 24 V)
- LDO: AMS1117-3.3 (SOT-223), 5 V → 3.3 V @ 800 mA max
- Decoupling: 10 µF input, 10 µF output, 100 nF per VDD pin
- Typical consumption: ~0.5 W (170 MHz, all peripherals active)

### 6.2 Power States

| State | Description | Current (3.3 V) |
|-------|-------------|-----------------|
| Active | All tasks running, PID + CAN + UART active | ~150 mA |
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
| Thermal cutoff (IR) | MLX90614 > 270 °C → E_STOP | ≤100 ms (poll interval) |
| Thermal cutoff (CAN coil) | CAN coil over-temp → E_STOP | ≤500 ms (CAN status interval) |
| CAN fault | No module response in 500 ms → reduce power | 500 ms |
| RV1106 heartbeat loss | No heartbeat for 5 s → safe state | 5 s |
| Overcurrent | INA219 > threshold → warning/shutdown | ≤100 ms |

### 7.2 Fault Table

| Fault Code | Name | Severity | Action |
|------------|------|----------|--------|
| 0x01 | OVER_TEMP_IR | Critical | E_STOP, cut relay, log |
| 0x02 | OVER_TEMP_COIL | Critical | E_STOP, cut relay, log |
| 0x03 | E_STOP_PRESSED | Critical | E_STOP, cut relay, buzzer |
| 0x04 | CAN_FAULT | Critical | Reduce power to 0, alert RV1106 |
| 0x05 | RV1106_HEARTBEAT_LOSS | Critical | Safe state (hold temp at 0, stop servo) |
| 0x10 | SERVO_STALL | Warning | Stop servo, alert RV1106 |
| 0x11 | SLD_LOAD_CELL_DRIFT | Warning | Alert RV1106, flag SLD dispense unreliable |
| 0x12 | DSB_STALL | Warning | Dispenser servo stall/timeout: retry once (back off, re-approach), then rail off, OE high, alert RV1106 |
| 0x13 | SLD_DISPENSE_ERROR | Warning | Stop pump, alert RV1106 with actual vs target |
| 0x20 | CAN_TX_TIMEOUT | Info | Retry 3×, then CAN_FAULT |
| 0x21 | I2C_NACK | Info | Retry 3×, use last-known value |

### 7.3 E-Stop Sequence

1. **PB2 EXTI fires** (or software E_STOP from RV1106 command 0x04)
2. Safety relay opened (PB0 LOW → relay de-energizes → AC cut)
3. All PWM outputs set to 0% (TIM1, TIM2, TIM3)
4. CAN: send power=0 to module (belt-and-suspenders with relay)
5. Buzzer activated (PC7 PWM)
6. Status packet (0x12) sent to RV1106: `safety_state = E_STOP`
7. **Hold state** — only IWDG kick continues; no commands accepted
8. **Reset** — PB2 debounce clears → re-init → wait for RV1106 heartbeat → NORMAL

---

## 8. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| PID loop period | 100 ms ± 1 ms | TIM interrupt jitter |
| Motor control period | 20 ms ± 0.5 ms | TIM interrupt jitter |
| E-stop latency | <1 ms | PB2 edge → relay GPIO toggle |
| UART command parse | <1 ms | Frame CRC valid → response queued |
| WS2812B frame update (16 LEDs) | <1 ms | DMA start → transfer complete |
| CAN round-trip | <10 ms | TX → RX status |
| Sensor poll cycle | <50 ms (all sensors) | Cycle start → data ready |
| Temperature accuracy | ±5 °C (IR to food surface) | Calibrated against thermocouple |
| Dispensing accuracy (FID) | ±10% per ¼ tsp dose | Volumetric measure wheel, weighed over 10 doses |
| Dispensing accuracy (SLD) | ±5% | Load cell vs target weight |
| FreeRTOS CPU utilization | <70% | Idle task runtime measurement |
| Flash usage | <256 KB | Linker map |
| SRAM usage | <96 KB | Stack + heap analysis |

---

## 9. Dependencies & Constraints

### 9.1 Hardware Dependencies

- Controller PCB (160×90 mm) provides STM32 + LDO + connectors
- Driver PCB (160×90 mm) provides buck converters, H-bridges, MOSFETs
- Stacking connector (J_STACK, 2×20) bridges Controller ↔ Driver
- Luckfox Pico Zero header pins 8/10 (UART2) connect to USART2 PA2/PA3 at 3.3 V (no level shifting)
- 74AHCT1G125 level shifter on the Controller PCB between PB14 and J_LED (WS2812B 5 V data)

### 9.2 Firmware Dependencies

- STM32 HAL drivers (STM32CubeMX generated): GPIO, ADC, TIM, USART, I2C, FDCAN
- FreeRTOS 10.x kernel + CMSIS-RTOS2 wrapper
- CMSIS-DSP library (PID functions)
- Custom HX711 bit-bang driver
- CRC-16/CCITT lookup table
- UART frame codec (SOF / byte-stuffing) and TIM15 + DMA WS2812B driver

### 9.3 Constraints

- MISRA C compliance for safety-critical tasks (PID, safety monitor, E-stop handler)
- No dynamic memory allocation after boot (all FreeRTOS objects static)
- No floating-point in ISRs (FPU context save overhead)
- CAN bus requires 120 Ω termination at both ends
- I2C bus: 4 devices (MLX90614 + INA219 + PCA9685 + PCF8574 #2), total bus capacitance must stay under 400 pF

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
