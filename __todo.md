# Epicura - Task Tracking

## Documentation

- [x] Create documentation folder structure
- [x] [[__Workspaces/Appliance/Epicura/epi-Spec/docs/README|Documentation Index]] (README.md)
- [x] [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]
- [x] [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]
- [x] [[docs/02-Hardware/Epicura-Architecture|Epicura Architecture]]
- [x] [[docs/02-Hardware/05-Sensors-Acquisition|Sensors & Acquisition]]
- [x] [[07-Mechanical-Design|Mechanical Design]]
- [x] [[04-Controller-Software-Architecture|Controller & Software Architecture]]
- [x] [[08-Tech-Stack|Tech Stack]]
- [x] [[03-UI-UX-Design|UI/UX Design]]
- [x] [[docs/05-Subsystems/09-Induction-Heating|Induction Heating]]
- [x] [[docs/05-Subsystems/10-Robotic-Arm|Robotic Arm]]
- [x] [[docs/05-Subsystems/11-Ingredient-Dispensing|Ingredient Dispensing]]
- [x] [[docs/05-Subsystems/12-Vision-System|Vision System]]
- [x] [[docs/05-Subsystems/13-Exhaust-Fume-Management|Exhaust & Fume Management]]
- [x] [[06-Safety-Compliance|Safety & Compliance]]
- [x] [[__Workspaces/Healthcare/ECG/docs/07-Development/Prototype-Development-Plan|Prototype Development Plan]]
- [x] [[01-Compute-Module-Components|Compute Module Components]]
- [x] [[02-Actuation-Components|Actuation Components]]
- [x] [[03-Sensor-Components|Sensor Components]]
- [x] [[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]
- [x] Update `__init.md` with documentation links
- [x] Expand `CLAUDE.md` with technical context

## Prototype Hardware

- [ ] Order Luckfox Pico Zero (RV1106G3)
- [ ] Order NUCLEO-G0B1RE dev board
- [ ] Source a ommercial induction hob for teardown
- [ ] Order 24V integrated CAN servo motor (≥ 3 N·m, CyberGear/RobStride-class)
- [ ] Order 2S1P 18650 Li-ion pack with PCM + NTC
- [ ] Order IMX415-98 camera module
- [ ] Order HX711 + load cells
- [ ] Order a 4" ST7796S SPI touchscreen display
- [ ] 3D print enclosure prototype

## Firmware Development

- [ ] RV1106 Buildroot image bring-up
- [ ] STM32 FreeRTOS project setup
- [ ] Isolated CAN bus: RV1106 (MCP2518FD) ↔ STM32 ↔ induction surface
- [ ] Induction setpoint keep-alive (RV1106 heat thread; module runs its own PID)
- [ ] Stir motor CAN driver on STM32 FDCAN2
- [ ] Servo arm stirring patterns
- [ ] Load cell calibration
- [ ] Battery backup: POWER_FAIL handling, pack voltage monitoring, shutdown at 6.2 V
- [ ] Camera capture pipeline
- [ ] RKNN model inference on the NPU
- [ ] Recipe state machine engine
- [ ] LVGL touchscreen UI
- [ ] Ingredient dispensing control
- [ ] Safety watchdog and interlocks

## Software Development

- [ ] Recipe YAML format definition
- [ ] SQLite database schema
- [ ] ISP preprocessing pipeline (dehaze/3DNR, 224x224 self-path)
- [ ] MobileNetV2 training data collection
- [ ] Model training and INT8 quantization (RKNN-Toolkit2)
- [ ] Cloud MQTT telemetry
- [ ] OTA update mechanism
- [ ] Native companion mobile apps (iOS + Android)

## Testing & Validation

- [ ] Power budget measurement
- [ ] Temperature accuracy validation (±5°C)
- [ ] CV inference latency (<500ms)
- [ ] End-to-end dal tadka cook test
- [ ] Safety interlock verification
- [ ] EMC pre-compliance scan

---

#epicura #tasks #project-tracking
