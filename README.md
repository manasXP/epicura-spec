# Epicura

An autonomous countertop kitchen robot that cooks one-pot meals using AI vision, robotic stirring, and precise induction heat control. Designed for compact Indian kitchens, under 2kW power draw.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Epicura System Overview                          │
│                                                                     │
│  ┌──────────────────────┐        ┌──────────────────────┐           │
│  │  RV1106 (Luckfox)    │        │  STM32 MCU           │           │
│  │  (Buildroot Linux)   │◄──────►│  (FreeRTOS)          │           │
│  │  - Recipe Engine     │  UART  │  - PID Control       │           │
│  │  - CV Pipeline       │  /CAN  │  - Servo Driver      │           │
│  │  - LVGL UI           │        │  - Sensor Polling    │           │
│  │  - Cloud Sync        │        │  - Safety Watchdog   │           │
│  └──────────┬───────────┘        └──────────┬───────────┘           │
│             │                               │                       │
│  ┌──────────▼───────────┐        ┌──────────▼───────────┐           │
│  │  4" Touchscreen      │        │  Induction Heater    │           │
│  │  IMX415-98 Camera    │        │  Servo Arm           │           │
│  │  WiFi/BT             │        │  Load Cells          │           │
│  │                      │        │  NTC + IR Sensors    │           │
│  └──────────────────────┘        └──────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Autonomous Cooking** — Hands-off operation after ingredient loading with state machine recipe execution
- **AI Vision** — Overhead camera with hardware ISP and MobileNetV2 INT8 on the RV1106 NPU (RKNN) for food color/texture analysis and cooking stage detection
- **Induction PID Control** — 1,800W microwave induction surface (CAN bus) with closed-loop PID, ±5°C accuracy
- **Robotic Stirring Arm** — Single-axis servo arm with multiple stir patterns and auto-scraping
- **Three-Subsystem Dispensing** — Fine ingredients (6-canister servo carousel, ¼ tsp dosing), coarse ingredients (5-slot servo carousel), liquids (peristaltic pumps)
- **Touchscreen + Mobile Apps** — 4" LVGL touchscreen UI, native iOS (Swift) and Android (Kotlin) companion apps
- **100+ Indian Recipes** — Curries, dal, rice, biryani with regional variations and dietary customization
- **Cloud + Offline** — Cloud-updatable recipe library with full local fallback

## Hardware Architecture

| Component | Part | Purpose |
|-----------|------|---------|
| Compute (AI) | Luckfox Pico Zero — RV1106G3 (Cortex-A7 @ 1.2 GHz, 1 TOPS NPU, ISP, 256MB, 8GB eMMC) | Vision, recipe engine, UI, cloud sync |
| Compute (Control) | STM32G474 (Cortex-M4F, 170 MHz) | PID, servo driver, sensor polling, safety |
| Camera | IMX415-98 (8 MP, MIPI CSI) | Food stage detection via ISP + NPU |
| IR Thermometer | MLX90614 | Non-contact food surface temp |
| Load Cells | 4× strain gauge + HX711 | Weight-based dispensing verification |
| Induction Surface | 1,800W commercial module | CAN bus controlled cooking heat |
| Servo Arm | 24V BLDC motor (integrated ESC) | Stirring and scraping |
| Display | 4" 480×320 capacitive SPI (ST7796S + FT6336) | LVGL touchscreen UI |

## Software Stack

### RV1106 (Buildroot Linux, single C application `epicurad`)

- **Database**: SQLite 3 (WAL, JSON1, FTS5) — mirrors the cloud PostgreSQL schema table-for-table
- **Cloud**: libmosquitto MQTT client (TLS) + libcurl REST client — no device-hosted API or broker
- **Recipe Engine**: C — libyaml parsing, state machine
- **CV Pipeline**: hardware ISP → NPU, MobileNetV2 INT8 (`.rknn`, RKNN-Toolkit2)
- **UI**: LVGL 9 — 4" SPI touchscreen interface
- **Live view**: on-demand H.264 RTSP stream to the phone
- **OTA Updates**: swupdate with A/B partitions

### STM32 (FreeRTOS)

- 4 tasks: PID (100 Hz), servo (50 Hz), sensor (10 Hz), comms (20 Hz)
- C (MISRA subset for safety-critical paths)
- Hardware watchdog, thermal cutoffs, e-stop relay

## Project Status

**Phase:** Design & Documentation

Comprehensive documentation exists across 30+ documents covering hardware, software, subsystems, compliance, PCB design, backend, APIs, mobile apps, and project management.

See [`docs/README.md`](__Workspaces/Appliance/Epicura/epi-Spec/docs/README.md) for the full documentation index.

## Repositories

| Repository                                                          | Stack                          | Purpose                                                               |
| ------------------------------------------------------------------- | ------------------------------ | --------------------------------------------------------------------- |
| **[epicura-spec](https://github.com/manasXP/epicura-spec)**         | Markdown + KiCAD 9             | Documentation, specifications, PCB design (this repo)                 |
| **[epicura-pcb](https://github.com/manasXP/epicura-pcb)**           | KiCAD 9                        | PCB schematics, layouts, Gerbers, DRC/fabrication outputs             |
| **[epicura-pm](https://github.com/manasXP/epicura-pm)**             | Markdown                       | Project management — epics, sprints, resource allocation              |
| **[epicura-tcc](https://github.com/manasXP/epicura-tcc)**           | Markdown                       | Testing strategies, compliance/safety, recipe schema & seed data      |
| **[epicura-ux](https://github.com/manasXP/epicura-ux)**             | Markdown + Vite/React          | UI/UX design documentation and interactive mobile mockups             |
| **[epicura-firmware](https://github.com/manasXP/epicura-firmware)** | C (FreeRTOS, STM32 HAL)        | STM32G474RE real-time control — PID, servo, sensors, CAN, safety      |
| **[epicura-rv1106](https://github.com/manasXP/epicura-rv1106)**     | C11 (CMake) + Buildroot        | RV1106 `epicurad` — recipe engine, ISP/NPU CV, LVGL UI, UART bridge, Buildroot image |
| **[epicura-api](https://github.com/manasXP/epicura-api)**           | TypeScript (Fastify + Next.js) | Cloud API server and admin portal monorepo                            |
| **[epicura-ios](https://github.com/manasXP/epicura-ios)**           | Swift (SwiftUI)                | iOS companion app — BLE pairing, recipes, live cooking                |
| **[epicura-android](https://github.com/manasXP/epicura-android)**   | Kotlin (Jetpack Compose)       | Android companion app                                                 |

See [Repository Plan](02-Repository-Plan.md) for directory structures, CI/CD, and cross-repo dependencies.

## Estimated BOM

~$433 for prototype. See [Total Component Cost](__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost.md) for breakdown.

## Development Roadmap

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Prototype | 3–6 months | Hardware prototype, basic recipe execution, vision PoC |
| Alpha | 3–6 months | Core features, 20+ recipes, app integration, safety testing |
| Beta | 3–6 months | 100+ recipes, field testing, regulatory pre-compliance |
| Production | 3–6 months | Manufacturing, certifications, market launch |

## License

[Apache License 2.0](LICENSE)
