---
created: 2026-02-15
modified: 2026-11-04
version: 1.4
status: Draft
---

# Epicura - Autonomous Kitchen Robot - Documentation Index

Welcome to the comprehensive documentation for the Epicura autonomous kitchen robot project. This documentation provides detailed specifications, design considerations, and implementation guidance for all subsystems of an AI-powered countertop cooking robot designed for Indian kitchens.

## 1. Quick Navigation

### 1.1 Core Documentation

#### 1.1.1 Overview
1. **[[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]** - Executive summary, key features, and target use cases

#### 1.1.2 Hardware
2. **[[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]** - Induction, robotic arm, sensors, and performance requirements
3. **[[01-Epicura-Architecture|Epicura Architecture]]** - System block diagrams and hardware wiring
4. **[[03-Sensors-Acquisition|Sensors & Acquisition]]** - Camera, module-reported cooking temperature, load cells and pot detection
5. **[[04-Mechanical-Design|Mechanical Design]]** - Enclosure, arm mechanism, and industrial design

#### 1.1.3 Software
6. **[[02-Controller-Software-Architecture|Controller & Software Architecture]]** - Dual-processor software modules, recipe state machine, and control flow
7. **[[03-Main-Loop-State-Machine|Main Loop State Machine]]** - Cooking state diagram, state-layer impact matrix, sequence diagrams, and transition triggers
8. **[[01-Tech-Stack|Tech Stack]]** - Hardware platforms, software frameworks, and development tools
9. **[[04-MPU-Functional-Specification|MPU Functional Specification]]** - RV1106G3 (Cortex-A7 + NPU/ISP) functional requirements, interfaces, and software architecture
10. **[[05-MCU-Functional-Specification|MCU Functional Specification]]** - STM32G474RE functional requirements, pin assignments, and FreeRTOS tasks

#### 1.1.4 User Interface
> [!note] Moved to [[__Workspaces/Appliance/Epicura/epi-UX/__init|epi-UX]] workspace

#### 1.1.5 Subsystems
9. **[[01-Induction-Heating|Induction Heating]]** - 1,800W microwave induction surface on the isolated CAN port, module-internal temperature control, and power management
10. **[[02-Robotic-Arm|Robotic Arm]]** - Single-axis arm on a 24V CAN servo motor (regular CAN port), stirring patterns, and STM32 motor control
11. **[[03-Ingredient-Dispensing|Ingredient Dispensing]]** - Three-subsystem dispensing: FID (fine, servo carousel), CID (coarse, servo carousel), SLD (liquids)
12. **[[04-Vision-System|Vision System]]** - HD camera, edge AI inference, and cooking stage detection
13. **[[05-Exhaust-Fume-Management|Exhaust & Fume Management]]** - Exhaust fan, grease/carbon filtration, and fume extraction

#### 1.1.6 Compliance
> [!note] Moved to [[__Workspaces/Appliance/Epicura/epi-TCC/__init|epi-TCC]] workspace

#### 1.1.7 Development
14. **[[01-Prototype-Development-Plan|Prototype Development Plan]]** - Phased plan from prototype to production (20-24 weeks)
15. **[[02-Repository-Plan|Repository Plan]]** - 6 GitHub repositories, directory structures, CI/CD, and cross-repo dependencies
16. **[[03-Submodule-Setup|Docs Submodule Setup]]** - Linking the docs repo as a submodule in all other repositories

#### 1.1.8 Project Management
> [!note] Moved to [[__Workspaces/Appliance/Epicura/epi-PM/__init|epi-PM]] workspace

15. **[[__Workspaces/Appliance/Epicura/epi-PM/Epics/__init|Epics]]** - 13 subsystem-based epics (~89 stories, ~385 points) covering PCB, embedded, thermal, actuation, vision, recipe, UI, backend, iOS, Android, admin, integration, and UX
16. **[[__Workspaces/Appliance/Epicura/epi-PM/Sprints/__init|Sprint Calendar]]** - 6-week pre-sprint PCB phase + 12 two-week sprints (30 weeks total)

#### 1.1.9 Components (BOM)
18. **[[01-Compute-Module-Components|Compute Module Components]]** - Luckfox Pico Zero (RV1106G3), STM32, 4" SPI LCD
19. **[[02-Actuation-Components|Actuation Components]]** - Servo motors, induction driver, solenoids
20. **[[03-Sensor-Components|Sensor Components]]** - IMX415-98 camera, reed switch, LED ring
21. **[[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]** - Full BOM and cost analysis (~$433 prototype)

#### 1.1.10 PCB Design
22. **[[01-Unified-PCB-Design|Unified PCB Design]]** - Single 4-layer board (160x90mm): STM32, Luckfox Pico Zero slot, CID/FID/SLD drivers, isolated + regular CAN ports, 2S Li-ion backup (document lives in the epicura-pcb repo)
23. **[epicura-pcb](https://github.com/manasXP/epicura-pcb)** - Dedicated repo for KiCad project files, schematics, layouts, Gerbers, and DRC/fabrication outputs

#### 1.1.11 Backend
24. **[[01-Backend-Architecture|Backend Architecture]]** - Cloud backend (Fastify, PostgreSQL, Redis, MQTT bridge)
25. **[[02-Database-Schema|Database Schema]]** - PostgreSQL tables, indexes, sync strategy
26. **[[03-Admin-Portal|Admin Portal]]** - Next.js admin dashboard for recipe and appliance management

#### 1.1.12 API
27. **[[01-REST-API-Reference|REST API Reference]]** - Complete endpoint documentation with examples
28. **[[02-WebSocket-Events|WebSocket Events]]** - Real-time cooking event protocol
29. **[[03-MQTT-Topics|MQTT Topics]]** - Device telemetry topic hierarchy
30. **[[04-BLE-Services|BLE Services]]** - BLE GATT services for pairing and WiFi provisioning

#### 1.1.13 Mobile Apps
31. **[[01-Mobile-Architecture|Mobile Architecture]]** - MVVM architecture, networking, design system
32. **[[02-iOS-App|iOS App]]** - Swift/SwiftUI implementation (Core Bluetooth, APNs)
33. **[[03-Android-App|Android App]]** - Kotlin/Compose implementation (CompanionDeviceManager, FCM)

#### 1.1.14 Testing & Recipes
> [!note] Moved to [[__Workspaces/Appliance/Epicura/epi-TCC/__init|epi-TCC]] workspace

## 2. Documentation Structure

```
docs/
├── README.md                                    (this file)
├── 01-Overview/
│   └── 01-Project-Overview.md                   Core project description
├── 02-Hardware/
│   ├── 01-Epicura-Architecture.md               System architecture & wiring
│   ├── 02-Technical-Specifications.md           Hardware specifications
│   ├── 03-Sensors-Acquisition.md                Sensor system design
│   └── 04-Mechanical-Design.md                  Physical/industrial design
├── 03-Software/
│   ├── 01-Tech-Stack.md                         Technology choices
│   ├── 02-Controller-Software-Architecture.md   Software architecture
│   ├── 03-Main-Loop-State-Machine.md            Cooking state machine & layer impacts
│   ├── 04-MPU-Functional-Specification.md       RV1106 functional spec
│   └── 05-MCU-Functional-Specification.md       STM32 functional spec
├── (04-UserInterface → moved to epi-UX workspace)
├── 05-Subsystems/
│   ├── 01-Induction-Heating.md                  Induction heater subsystem
│   ├── 02-Robotic-Arm.md                        Stirring arm subsystem
│   ├── 03-Ingredient-Dispensing.md              Dispensing subsystem
│   ├── 04-Vision-System.md                      Computer vision subsystem
│   └── 05-Exhaust-Fume-Management.md            Exhaust fan and filtration
├── (06-Compliance → moved to epi-TCC workspace)
├── 07-Development/
│   ├── 01-Prototype-Development-Plan.md         Development roadmap (20-24 weeks)
│   └── 02-Repository-Plan.md                    6-repo structure & GitHub setup
├── 08-Components/
│   ├── 01-Compute-Module-Components.md          Compute & control BOM
│   ├── 02-Actuation-Components.md               Motors & actuators BOM
│   ├── 03-Sensor-Components.md                  Sensors & cameras BOM
│   └── 04-Total-Component-Cost.md               Full cost analysis (~$433)
├── 09-PCB/
│   ├── 01-Unified-PCB-Design.md              STM32 + power + drivers unified board
├── 10-Backend/
│   ├── 01-Backend-Architecture.md               Cloud backend architecture
│   ├── 02-Database-Schema.md                    PostgreSQL schema & sync
│   └── 03-Admin-Portal.md                       Next.js admin dashboard
├── 11-API/
│   ├── 01-REST-API-Reference.md                 REST endpoints & examples
│   ├── 02-WebSocket-Events.md                   Real-time event protocol
│   ├── 03-MQTT-Topics.md                        Device telemetry topics
│   └── 04-BLE-Services.md                       BLE pairing & WiFi setup
├── 12-MobileApps/
│   ├── 01-Mobile-Architecture.md                MVVM, networking, design
│   ├── 02-iOS-App.md                            Swift/SwiftUI implementation
│   └── 03-Android-App.md                        Kotlin/Compose implementation
├── (14-Testing → moved to epi-TCC workspace)
├── (15-Recipes → moved to epi-TCC workspace)
└── (13-ProjectManagement → moved to epi-PM workspace)
```

## 3. Getting Started

### 3.1 For Project Managers
Start with:
1. [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]] - Understand the project scope and target market
2. [[__Workspaces/Appliance/Epicura/epi-PM/Epics/__init|Epics]] - 13 subsystem-based epics (~89 stories, ~385 points)
3. [[__Workspaces/Appliance/Epicura/epi-PM/Sprints/__init|Sprint Calendar]] - 6-week pre-sprint PCB phase + 12 two-week sprints
5. [[01-Prototype-Development-Plan|Prototype Development Plan]] - Phased development roadmap (20-24 weeks)
6. [[01-Tech-Stack|Tech Stack]] - Review technology choices
7. Safety & Compliance - See [[__Workspaces/Appliance/Epicura/epi-TCC/__init|epi-TCC]] workspace

### 3.2 For Hardware Engineers
Start with:
1. [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]] - System requirements and power budget
2. [[01-Epicura-Architecture|Epicura Architecture]] - Block diagrams and wiring
3. [[03-Sensors-Acquisition|Sensors & Acquisition]] - Camera, module-reported temperature, and load cell design
4. [[04-Mechanical-Design|Mechanical Design]] - Enclosure, arm mechanism, and thermal management

### 3.3 For Software Engineers
Start with:
1. [[02-Controller-Software-Architecture|Controller & Software Architecture]] - Dual-processor design and recipe state machine
2. [[01-Tech-Stack|Tech Stack]] - Development environment and tools
3. UI/UX Design - See [[__Workspaces/Appliance/Epicura/epi-UX/__init|epi-UX]] workspace

### 3.4 For Backend Engineers
Start with:
1. [[01-Backend-Architecture|Backend Architecture]] - Fastify, PostgreSQL, Redis, MQTT bridge
2. [[02-Database-Schema|Database Schema]] - Tables, indexes, device sync strategy
3. [[01-REST-API-Reference|REST API Reference]] - Endpoint specifications with examples
4. [[03-MQTT-Topics|MQTT Topics]] - Device telemetry protocol

### 3.5 For Mobile Developers
Start with:
1. [[01-Mobile-Architecture|Mobile Architecture]] - MVVM architecture, networking, BLE
2. [[02-iOS-App|iOS App]] or [[03-Android-App|Android App]] - Platform-specific guide
3. [[04-BLE-Services|BLE Services]] - Device pairing and WiFi provisioning
4. [[01-REST-API-Reference|REST API Reference]] - Backend API endpoints

### 3.6 For Industrial Designers
Start with:
1. [[04-Mechanical-Design|Mechanical Design]] - Enclosure form factor and material selection
2. UI/UX Design - See [[__Workspaces/Appliance/Epicura/epi-UX/__init|epi-UX]] workspace
3. [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]] - Product vision and target user profile

## 4. Key Features Summary

- **Autonomous Cooking** - Hands-off operation after ingredient loading; state machine recipe execution
- **AI Vision Monitoring** - Overhead camera with hardware ISP + NPU edge AI (RKNN) for food color/texture analysis and cooking stage detection
- **Induction Temperature Control** - 1,800W induction surface regulating on its own sensor; setpoints and status over an isolated CAN port
- **Robotic Stirring Arm** - Single-axis arm on a 24V CAN servo motor (STM32 FDCAN2) with multiple stir patterns and auto-scraping
- **Three-Subsystem Dispensing** - FID (6-canister servo carousel, ¼ tsp dosing, 3 servos), CID (5-slot servo carousel, 1 servo), SLD (2 peristaltic pump liquid channels with dedicated per-reservoir load cells + low-level alerts); FID + CID share one Dispenser Servo Block
- **Touchscreen + Companion Apps** - 4" LVGL touchscreen on device, native mobile apps (iOS + Android) for remote control and live camera feed
- **100+ Indian Recipes** - Curated recipe database covering curries, dal, rice, biryani, and more with regional variations
- **Cloud + Offline Operation** - Cloud-updatable recipe library with full local SQLite for offline cooking
- **Under 2kW Power Draw** - Designed for standard Indian household 15A outlets with dynamic power management

## 5. Development Phases

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Prototype** | 3-6 months | Hardware prototype, basic recipe execution, vision proof-of-concept |
| **Alpha** | 3-6 months | Core features, 20+ recipes, app integration, safety testing |
| **Beta** | 3-6 months | 100+ recipes, field testing, regulatory pre-compliance |
| **Production** | 3-6 months | Manufacturing, final certifications, market launch |
| **Total** | 12-24 months | Market-ready product |

## 6. Subsystem Overview

### 6.1 Hardware Subsystems
- **Compute Platform** - Luckfox Pico Zero (RV1106G3; AI/vision/UI) + STM32 (motor/arm control)
- **Induction Heater** - 1,800W induction surface with internal temperature control, isolated CAN port
- **Display** - 4" 480x320 capacitive touchscreen (LVGL interface, SPI)
- **Robotic Arm** - Single-axis arm on a 24V CAN servo motor (regular CAN port) for stirring
- **Sensors** - Overhead IMX415-98 camera + SLD load cells + module-reported cooking temperature over CAN; 2S Li-ion backup on the Unified PCB
- **Ingredient Dispensing** - FID + CID servo carousels (PCA9685 Dispenser Servo Block) + SLD (peristaltic pumps + solenoids)

### 6.2 Software Subsystems
- **RV1106 (Buildroot Linux)** - Single C application `epicurad`: recipe engine, ISP + NPU vision pipeline, LVGL UI, heater setpoints over the shared CAN bus (the module runs its own PID), cloud sync (REST/MQTT client), SQLite
- **STM32 (FreeRTOS)** - CAN node: stir motor over a second CAN bus, dispensers, sensor polling, battery monitoring, heater off-switch, safety watchdog

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Epicura System Overview                          │
│                                                                     │
│  ┌──────────────────────┐        ┌──────────────────────┐           │
│  │  RV1106 (Luckfox)    │        │  STM32 MCU           │           │
│  │  (Buildroot Linux)   │◄──────►│  (FreeRTOS)          │           │
│  │  - Recipe Engine     │  CAN   │  - Heater Interlock  │           │
│  │  - CV Pipeline       │ (iso)  │  - Stir Motor (CAN)  │           │
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

## 7. Tags

#epicura #kitchen-robot #documentation #index

---

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Index descriptions and overview updated for the Luckfox Pico Zero (RV1106G3) application processor, LVGL 4" LCD, SC3336 camera and SQLite; BOM figure ~$433 |
| 1.2 | 2026-11-04 | Manas Pradhan | Dispensing descriptions updated for servo carousels (FID/CID) |
| 1.3 | 2026-11-04 | Manas Pradhan | Software subsystem summary and system diagram updated for the shared isolated CAN bus (heater PID on the RV1106, STM32 as CAN node with heater off-switch) |
| 1.4 | 2026-11-04 | Manas Pradhan | Single Unified PCB with Pico Zero slot, two CAN ports and 2S battery; IR thermometer removed (module-internal temperature control); CAN servo stirring motor; BOM ~$710 |
