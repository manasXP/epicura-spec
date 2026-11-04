---
created: 2026-02-15
modified: 2026-11-04
version: 1.6
status: Draft
---

# Epicura - Autonomous Kitchen Robot - Documentation Index

Welcome to the comprehensive documentation for the Epicura autonomous kitchen robot project. This documentation provides detailed specifications, design considerations, and implementation guidance for all subsystems of an AI-powered countertop cooking robot designed for Indian kitchens.

## 1. Quick Navigation

### 1.1 Core Documentation

#### 1.1.1 Overview
1. **[[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]]** - Executive summary, key features, and target use cases

#### 1.1.2 Hardware
2. **[[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]]** - Heating, robotic arm, sensors, and performance requirements
3. **[[01-Epicura-Architecture|Epicura Architecture]]** - Three-unit system (Cooking Surface, Stirring Unit, lift-off Dispensing Unit), block diagrams, dock and hardware wiring
4. **[[03-Sensors-Acquisition|Sensors & Acquisition]]** - Camera + white LED ring on the Dispensing Unit underside, module-reported cooking temperature, NAU7802 load cells, battery/dock monitoring and pot detection
5. **[[04-Mechanical-Design|Mechanical Design]]** - Three-unit stack (CS base, SU gantry, lift-off DU), arm mechanism, dock and industrial design

#### 1.1.3 Software
6. **[[02-Controller-Software-Architecture|Controller & Software Architecture]]** - Dual-processor software modules, recipe state machine, and control flow
7. **[[03-Main-Loop-State-Machine|Main Loop State Machine]]** - Cooking state diagram, state-layer impact matrix, sequence diagrams, and transition triggers
8. **[[01-Tech-Stack|Tech Stack]]** - Hardware platforms, software frameworks, and development tools
9. **[[04-MPU-Functional-Specification|MPU Functional Specification]]** - RV1106G3 (Cortex-A7 + NPU/ISP) functional requirements, interfaces, and software architecture
10. **[[05-MCU-Functional-Specification|MCU Functional Specification]]** - STM32G0B1RE on the Cooking Surface Controller: functional requirements, pin assignments, and FreeRTOS tasks

#### 1.1.4 User Interface
> [!note] Moved to [[__Workspaces/Appliance/Epicura/epi-Design/UX/__init|epi-Design/UX]] workspace

#### 1.1.5 Subsystems
9. **[[01-Electric-Heating|Electric Heating]]** - 1,300W (assumed) electric heating unit of the rice-cooker class on the isolated CAN port, unit-internal temperature control, and power management
10. **[[02-Robotic-Arm|Robotic Arm]]** - Single-axis arm on a 24V CAN servo motor in the Stirring Unit (CSC regular CAN port via the J_SU harness), stirring patterns, and STM32 motor control
11. **[[03-Ingredient-Dispensing|Ingredient Dispensing]]** - Three-subsystem dispensing in the lift-off Dispensing Unit, driven by the RV1106: FID (fine, servo carousel), CID (coarse, servo carousel), SLD (liquids, NAU7802 load cells)
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
19. **[[02-Actuation-Components|Actuation Components]]** - Servo motors, heating unit, solenoids
20. **[[03-Sensor-Components|Sensor Components]]** - IMX415-98 camera, reed switch, LED ring
21. **[[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]]** - Full BOM and cost analysis (≈ $650-760 prototype)

#### 1.1.10 PCB Design
22. **[[01-Unified-PCB-Design|Unified PCB Design]]** - Dispensing Unit board v4.0 (160x90mm, 4-layer): Luckfox Pico Zero slot, 2S Li-ion primary supply + 1 A dock charger, CID/FID/SLD drivers on a 6 V rail, NAU7802 load cells, RV1106 isolated CAN node, dock pads (document lives in epi-Design/PCB)
23. **[[02-Cooking-Surface-Controller|Cooking Surface Controller]]** - Cooking Surface board v1.0 (~100x70mm, 4-layer): STM32G0B1RE, isolated CAN to the heating unit (J_CAN_HEAT) and the dock, stir-motor CAN + 24V (J_SU harness), safety relay, E-stop, fans, dock power switch (document lives in epi-Design/PCB alongside 01-Unified-PCB-Design)
24. **[epicura-design / PCB](https://github.com/manasXP/Epicura-Design/tree/main/PCB)** - Dedicated repo for KiCad project files, schematics, layouts, Gerbers, and DRC/fabrication outputs

#### 1.1.11 Backend
25. **[[01-Backend-Architecture|Backend Architecture]]** - Cloud backend (Fastify, PostgreSQL, Redis, MQTT bridge)
26. **[[02-Database-Schema|Database Schema]]** - PostgreSQL tables, indexes, sync strategy
27. **[[03-Admin-Portal|Admin Portal]]** - Next.js admin dashboard for recipe and appliance management

#### 1.1.12 API
28. **[[01-REST-API-Reference|REST API Reference]]** - Complete endpoint documentation with examples
29. **[[02-WebSocket-Events|WebSocket Events]]** - Real-time cooking event protocol
30. **[[03-MQTT-Topics|MQTT Topics]]** - Device telemetry topic hierarchy
31. **[[04-BLE-Services|BLE Services]]** - BLE GATT services for pairing and WiFi provisioning

#### 1.1.13 Mobile Apps
32. **[[01-Mobile-Architecture|Mobile Architecture]]** - MVVM architecture, networking, design system
33. **[[02-iOS-App|iOS App]]** - Swift/SwiftUI implementation (Core Bluetooth, APNs)
34. **[[03-Android-App|Android App]]** - Kotlin/Compose implementation (CompanionDeviceManager, FCM)

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
├── (04-UserInterface → moved to epi-Design/UX workspace)
├── 05-Subsystems/
│   ├── 01-Electric-Heating.md                  Electric heating subsystem
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
│   └── 04-Total-Component-Cost.md               Full cost analysis (≈ $650-760)
├── 09-PCB/  (documents live in epi-Design/PCB)
│   ├── 01-Unified-PCB-Design.md              Dispensing Unit board (Unified PCB v4.0)
│   └── 02-Cooking-Surface-Controller.md      Cooking Surface board (CSC, STM32G0B1RE)
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
3. UI/UX Design - See [[__Workspaces/Appliance/Epicura/epi-Design/UX/__init|epi-Design/UX]] workspace

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
2. UI/UX Design - See [[__Workspaces/Appliance/Epicura/epi-Design/UX/__init|epi-Design/UX]] workspace
3. [[__Workspaces/Appliance/Epicura/epi-Spec/docs/01-Overview/01-Project-Overview|Project Overview]] - Product vision and target user profile

## 4. Key Features Summary

- **Autonomous Cooking** - Hands-off operation after ingredient loading; state machine recipe execution
- **AI Vision Monitoring** - Overhead camera with hardware ISP + NPU edge AI (RKNN) for food color/texture analysis and cooking stage detection
- **Electric Heating Control** - 1,300W (assumed) rice-cooker-class heating unit regulating on its own centre sensor; setpoints and status over an isolated CAN port
- **Robotic Stirring Arm** - Single-axis arm on a 24V CAN servo motor in the Stirring Unit (CSC FDCAN2 via the J_SU harness) with multiple stir patterns and auto-scraping
- **Three-Subsystem Dispensing** - FID (6-canister servo carousel, ¼ tsp dosing, 3 servos), CID (5-slot servo carousel, 1 servo), SLD (2 peristaltic pump liquid channels with dedicated per-reservoir load cells + low-level alerts); FID + CID share one Dispenser Servo Block; all three travel with the lift-off Dispensing Unit and are driven by the RV1106
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
- **Compute Platform** - Luckfox Pico Zero (RV1106G3; AI/vision/UI/dispensing) on the Unified PCB v4.0 in the Dispensing Unit + STM32G0B1RE on the Cooking Surface Controller (CSC: stir motor, heater off-switch, fans, dock)
- **Electric Heating Unit** - 1,300W (assumed) rice-cooker-class heating unit with internal temperature control in the Cooking Surface base, isolated CAN port on the CSC
- **Display** - 4" 480x320 capacitive touchscreen (LVGL interface, SPI) on the Dispensing Unit front face
- **Robotic Arm** - Stirring Unit gantry between the rear pillars: single-axis arm on a 24V CAN servo motor, fed by one harness (J_SU) from the CSC's regular CAN port
- **Sensors** - IMX415-98 camera + white LED ring on the DU underside, NAU7802 SLD load cells, INA219 battery monitor, module-reported cooking temperature over CAN; the 2S Li-ion pack on the Unified PCB v4.0 is the DU's primary supply
- **Ingredient Dispensing** - FID + CID servo carousels (PCA9685 Dispenser Servo Block, 6 V rail) + SLD (6 V peristaltic pumps + solenoids), all in the lift-off Dispensing Unit, driven by the RV1106
- **Dock** - 8-contact magnetic pogo block on the left rear pillar: 24V charge + isolated CAN + dock sense; the Dispensing Unit lifts straight off with no cable

### 6.2 Software Subsystems
- **RV1106 (Buildroot Linux)** - Single C application `epicurad`: recipe engine, ISP + NPU vision pipeline, LVGL UI, `dispense` thread (FID/CID/SLD over I2C), battery/dock monitor, heater setpoints over the shared CAN bus (the module runs its own PID), cloud sync (REST/MQTT client), SQLite, STM32 OTA over CAN
- **STM32 (FreeRTOS)** - CAN node on the Cooking Surface Controller: stir motor over a second CAN bus, heater off-switch, safety relay / E-stop, exhaust fans, dock power switch, safe hold when the DU is lifted, safety watchdog

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Epicura System Overview                          │
│                                                                     │
│  DISPENSING UNIT (lifts off, battery-powered)                       │
│  ┌──────────────────────┐        ┌──────────────────────┐           │
│  │  RV1106 (Luckfox)    │        │  4" Touchscreen      │           │
│  │  Unified PCB v4.0    │        │  IMX415-98 Camera +  │           │
│  │  - Recipe Engine     │        │   white LED ring     │           │
│  │  - CV Pipeline       │        │  FID/CID/SLD, load   │           │
│  │  - Dispense thread   │        │   cells, 2S battery  │           │
│  │  - LVGL UI, Cloud    │        │  WiFi/BT             │           │
│  └──────────┬───────────┘        └──────────────────────┘           │
│             │ J_DOCK (8 pogo pins: 24 V charge + isolated CAN)      │
│  COOKING SURFACE (mains)                                            │
│  ┌──────────▼───────────┐        ┌──────────────────────┐           │
│  │  STM32 on the CSC    │        │  Heating Unit        │           │
│  │  (FreeRTOS)          │◄──────►│  PSU, E-stop, relay  │           │
│  │  - Heater Interlock  │  CAN   │  2x fans + filter    │           │
│  │  - Stir Motor (CAN)  │ (iso)  │  Dock block (pillar) │           │
│  │  - Safety Watchdog   │        │                      │           │
│  └──────────┬───────────┘        └──────────────────────┘           │
│             │ J_SU (24 V + CAN harness in the right pillar)         │
│  STIRRING UNIT                                                      │
│  ┌──────────▼───────────┐                                           │
│  │  CAN Servo Arm       │                                           │
│  │  (stirring, hood)    │                                           │
│  └──────────────────────┘                                           │
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
| 1.5 | 2026-11-04 | Manas Pradhan | Three-unit architecture (Cooking Surface with the CSC, Stirring Unit, lift-off Dispensing Unit with the Unified PCB v4.0, magnetic pogo dock): index descriptions, subsystem overview and system diagram updated; new PCB doc 02-Cooking-Surface-Controller; BOM ≈ $650-760 |
| 1.6 | 2026-11-04 | Manas Pradhan | Induction surface replaced by a rice-cooker-class electric heating unit (1,300 W assumed, same CAN contract): index entries, file tree, subsystem overview and system diagram updated |
