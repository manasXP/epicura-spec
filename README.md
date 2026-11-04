# Epicura

An autonomous countertop kitchen robot that cooks one-pot meals using AI vision, robotic stirring, and precise induction heat control. Designed for compact Indian kitchens, under 2kW power draw.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Epicura System Overview                          │
│                                                                     │
│  ┌──────────────────────┐        ┌──────────────────────┐           │
│  │  RV1106 (Luckfox)    │        │  STM32 MCU           │           │
│  │  (Buildroot Linux)   │◄──────►│  (FreeRTOS)          │           │
│  │  - Recipe Engine     │  CAN   │  - Heater Interlock  │           │
│  │  - CV Pipeline       │ (iso)  │  - Servo Driver      │           │
│  │  - LVGL UI           │        │  - Sensor Polling    │           │
│  │  - Cloud Sync        │        │  - Safety Watchdog   │           │
│  └──────────┬───────────┘        └──────────┬───────────┘           │
│             │                               │                       │
│  ┌──────────▼───────────┐        ┌──────────▼───────────┐           │
│  │  4" Touchscreen      │        │  Induction Heater    │           │
│  │  IMX415-98 Camera    │        │  Servo Arm           │           │
│  │  WiFi/BT             │        │  Load Cells          │           │
│  │                      │        │  CAN x2, 2S battery  │           │
│  └──────────────────────┘        └──────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Autonomous Cooking** — Hands-off operation after ingredient loading with state machine recipe execution
- **AI Vision** — Overhead camera with hardware ISP and MobileNetV2 INT8 on the RV1106 NPU (RKNN) for food color/texture analysis and cooking stage detection
- **Induction Temperature Control** — 1,800W microwave induction surface regulating on its own sensor; setpoints and status on an isolated CAN bus shared by the RV1106, the STM32 and the heater MCU
- **Robotic Stirring Arm** — Single-axis arm on a 24V CAN servo motor with multiple stir patterns and auto-scraping
- **Three-Subsystem Dispensing** — Fine ingredients (6-canister servo carousel, ¼ tsp dosing), coarse ingredients (5-slot servo carousel), liquids (peristaltic pumps)
- **Touchscreen + Mobile Apps** — 4" LVGL touchscreen UI, native iOS (Swift) and Android (Kotlin) companion apps
- **100+ Indian Recipes** — Curries, dal, rice, biryani with regional variations and dietary customization
- **Cloud + Offline** — Cloud-updatable recipe library with full local fallback

## Hardware Architecture

| Component | Part | Purpose |
|-----------|------|---------|
| Compute (AI) | Luckfox Pico Zero — RV1106G3 (Cortex-A7 @ 1.2 GHz, 1 TOPS NPU, ISP, 256MB, 8GB eMMC) | Vision, recipe engine, UI, cloud sync |
| Compute (Control) | STM32G0B1 (Cortex-M0+, 64 MHz) on the Unified PCB (Pico Zero slot, CID/FID/SLD drivers, 2 CAN ports, 2S battery backup) | Stir motor (CAN), dispensers, sensor polling, heater off-switch, safety |
| Camera | IMX415-98 (8 MP, MIPI CSI) | Food stage detection via ISP + NPU |
| Cooking Temperature | Induction module's own sensor, reported over CAN | No thermometer in Epicura |
| Load Cells | 2× strain gauge + HX711 (SLD reservoirs) | Weight-based liquid dispensing |
| Induction Surface | 1,800W commercial module with internal temperature control | Isolated CAN port; setpoints from the RV1106 |
| Servo Arm | 24V integrated CAN servo motor | Stirring and scraping (regular CAN port, STM32 FDCAN2) |
| Backup Power | 2S Li-ion pack + on-board TP5100 charger | Keeps RV1106/LCD/STM32 alive through outages |
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

- 4 tasks: servo (50 Hz), sensor (10 Hz), CAN comms (20 Hz), safety (10 Hz); the heater PID runs on the RV1106
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
| **[epicura-firmware](https://github.com/manasXP/epicura-firmware)** | C (FreeRTOS, STM32 HAL)        | STM32G0B1RE real-time control — servo, sensors, CAN node, dispensers, safety |
| **[epicura-rv1106](https://github.com/manasXP/epicura-rv1106)**     | C11 (CMake) + Buildroot        | RV1106 `epicurad` — recipe engine, ISP/NPU CV, LVGL UI, CAN node + heater PID, Buildroot image |
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
