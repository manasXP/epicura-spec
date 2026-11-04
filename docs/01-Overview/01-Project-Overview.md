---
created: 2026-02-14
modified: 2026-11-04
version: 1.4
status: Draft
tags: [epicura, project-overview, kitchen-robot]
---

# Epicura - Project Overview

## 1. Project Description

Development of an autonomous countertop kitchen robot that cooks complete one-pot meals using AI-powered computer vision, robotic stirring, and precise induction heat control. Epicura is designed for the Indian home market, inspired by the commercial Posha robot chef, and engineered to operate within compact Indian kitchens on standard household outlets (under 2kW). The system combines embedded Linux compute, real-time motor control, and edge AI inference to deliver fully autonomous cooking from ingredient loading to finished meal.

## 2. Key Components

This project encompasses the following major subsystems:

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]] - Induction, robotic arm, sensors, and power budget
- [[01-Epicura-Architecture|Epicura Architecture]] - System block diagrams and hardware wiring
- [[03-Sensors-Acquisition|Sensors & Acquisition]] - Camera, module-reported cooking temperature, and pot detection
- [[04-Mechanical-Design|Mechanical Design]] - Enclosure, arm mechanism, and industrial design
- [[02-Controller-Software-Architecture|Controller & Software Architecture]] - Dual-processor software modules and recipe state machine
- [[01-Tech-Stack|Tech Stack]] - Hardware platforms, software frameworks, and tools
- [[01-UI-UX-Design|UI/UX Design]] - Touchscreen interface and companion mobile app
- [[01-Induction-Heating|Induction Heating]] - 1,800W microwave induction surface with CAN bus control and PID
- [[02-Robotic-Arm|Robotic Arm]] - Single-axis servo arm and stir patterns
- [[03-Ingredient-Dispensing|Ingredient Dispensing]] - Three-subsystem dispensing (FID/CID/SLD)
- [[04-Vision-System|Vision System]] - HD camera, edge AI, and cooking stage detection
- [[05-Exhaust-Fume-Management|Exhaust & Fume Management]] - Exhaust fan, grease/carbon filtration
- [[01-Safety-Compliance|Safety & Compliance]] - Electrical safety and food contact regulations

## 3. Core Features

### 3.1 Autonomous Cooking
- Fully hands-off operation after ingredient loading and recipe selection
- State machine recipe execution: detect cooking stage via CV, adjust heat/stir, dispense ingredients
- Automatic ingredient dispensing via three subsystems: FID (fine ingredients, 6-canister servo carousel with ¼ tsp dosing), CID (coarse items, 5-slot servo carousel), SLD (liquids, peristaltic pump)
- Supports one-pot recipes: curries, dal, rice, biryani, stir-fries, pasta, soups

### 3.2 Recipe Intelligence
- 100+ curated Indian recipes at launch with regional variations (North, South, East, West)
- App-driven customization for spice levels, allergen substitutions, and dietary preferences
- Cloud-updatable recipe library with new recipes pushed via OTA
- Full offline fallback with local SQLite recipe database for uninterrupted cooking

### 3.3 Precision Control
- PID-controlled induction heating (loop on the RV1106 over the shared isolated CAN bus) with dynamic temperature range (60-250°C)
- IR non-contact thermometer + CAN coil temperature from induction module
- Sear at 200-250°C, simmer at 60-100°C with ±5°C accuracy
- Dynamic power management to stay within 2kW household limit

### 3.4 Vision System
- Overhead IMX415-98 camera (8 MP, 98 deg lens, 1280x720 @ 30 fps) mounted inside enclosure lid
- Food color and texture analysis using INT8 edge AI models on the RV1106G3 NPU (RKNN), with hardware ISP dehaze and noise reduction
- Real-time cooking stage detection: raw, browning, simmering, thickening, done
- Anomaly detection for burning, boiling over, or ingredient issues

### 3.5 User Experience
- 4" 480x320 capacitive touchscreen with LVGL-based interface for recipe browsing and cooking status
- Native companion mobile apps (SwiftUI + Jetpack Compose) for remote recipe selection, live camera feed, and notifications
- Multi-language support: English, Hindi, Tamil, Telugu (extensible to more regional languages)
- On-demand pot preview on the touchscreen and live view (RTSP) in the mobile app during cooking
- Grocery list generation and meal planning features in companion app

## 4. Target Use Cases

- **Daily Indian Cooking** - Curries, dal tadka, rajma, sambar, biryani, pulao, and everyday meals
- **Apartment/Compact Kitchens** - Countertop form factor (50x40x30cm) designed for space-constrained urban homes
- **Elderly/Mobility-Impaired Users** - Autonomous operation reduces physical effort; accessible UI with large touch targets
- **Hostel/Mess Kitchen Automation** - Scalable for small institutional kitchens with repeatable batch cooking
- **Meal Prep (Set-and-Forget)** - Load ingredients before work, schedule cooking, return to a ready meal

## 5. Key Features Comparison

| Feature | Posha (Commercial) | Epicura (Design Target) |
|---------|--------------------|-----------------------|
| **Autonomy** | Fully hands-off after prep | Identical, with CV fallback loops and anomaly alerts |
| **Customization** | Spice/allergen swaps via app | App-driven recipe DB with ingredient substitutions and dietary profiles |
| **Monitoring** | Live camera feed in app | App + local 4" touchscreen, anomaly alerts with push notifications |
| **Cleanup** | Dishwasher-safe pot | Removable non-stick pot, optional auto-rinse cycle |
| **Size/Power** | Countertop, ~1.8kW | 50x40x30cm, <2kW for standard Indian 15A outlets |
| **Recipes** | Curated library, cloud-updated | 100+ Indian recipes at launch, cloud-updatable, offline fallback |
| **Connectivity** | WiFi, app-paired | WiFi + BT, native companion apps (iOS + Android), OTA updates |
| **Price Target** | ~$800 USD (commercial) | $400-600 USD (target retail for Indian market) |

## 6. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Epicura System Architecture                           │
│                                                                             │
│  ┌──────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │     Luckfox Pico Zero (RV1106G3)     │  │     STM32 MCU               │  │
│  │     (Application Processor)          │  │     (Real-Time Controller)  │  │
│  │                                      │  │                             │  │
│  │  ┌──────────────────────────────┐    │  │  ┌─────────────────────┐    │  │
│  │  │  Buildroot Linux             │    │  │  │  FreeRTOS           │    │  │
│  │  └────────────┬─────────────────┘    │  │  └────────────┬────────┘    │  │
│  │               │                      │  │               │             │  │
│  │  ┌────────────▼─────────────────┐    │  │  ┌────────────▼────────┐    │  │
│  │  │  Recipe State Machine        │    │  │  │  Heater Interlock   │    │  │
│  │  │  CV Pipeline (ISP → NPU)     │◄───┼──┼─►│  Servo Motor Driver │    │  │
│  │  │  LVGL Touchscreen UI         │CAN │  │  │  Sensor Polling     │    │  │
│  │  │  Cloud Sync / OTA            │iso │  │  │  Safety Watchdog    │    │  │
│  │  │  SQLite Recipe DB            │    │  │  │  Dispensing Control │    │  │
│  │  └──────────────────────────────┘    │  │  └─────────────────────┘    │  │
│  │                                      │  │                             │  │
│  └──────────┬─────────────┬─────────────┘  └──────┬──────────┬───────────┘  │
│             │             │                       │          │              │
│     ┌───────▼──────┐ ┌───▼──────────┐    ┌───────▼────┐ ┌───▼──────────┐.   │
│     │ 4" Touch     │ │ IMX415-98 Cam│    │ Induction  │ │ Servo Arm    │    │
│     │ Display      │ │ (720p)       │    │ Heater     │ │ (Stirring)   │    │
│     │ (LVGL UI)    │ │              │    │ (1,800W)   │ │              │    │
│     └──────────────┘ └──────────────┘    └────────────┘ └──────────────┘    │
│                                                                             │
│     ┌──────────────┐ ┌──────────────┐    ┌────────────┐ ┌──────────────┐    │
│     │ WiFi / BT    │ │ 2S Li-ion    │    │ Reed       │ │ Ingredient   │    │
│     │ Module       │ │ Backup       │    │ Switch     │ │ Hoppers      │    │
│     │              │ │              │    │(Pot Detect)│ │ (4-6 compt.) │    │
│     └──────────────┘ └──────────────┘    └────────────┘ └──────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Data Flow Overview

```
┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│  User    │    │  Recipe      │    │  CV Pipeline  │    │  Actuators   │
│  Input   │───►│  State       │───►│  (ISP→NPU)    │───►│  (Heat/Stir/ │
│  (App/   │    │  Machine     │    │               │    │   Dispense)  │
│   Touch) │    │  (RV1106)    │    │  Stage?       │    │  (STM32)     │
└──────────┘    └──────┬───────┘    └───────┬───────┘    └──────┬───────┘
                       │                    │                   │
                       │            ┌───────▼───────┐           │
                       │            │  IMX415-98 Cam│           │
                       │            │  Module temp  │           │
                       │            └───────────────┘           │
                       │                                        │
                       ▼                                        ▼
                ┌──────────────┐                    ┌──────────────┐
                │  UI Display  │                    │  Physical    │
                │  (Status,    │                    │  Output      │
                │   Camera,    │                    │  (Cooked     │
                │   Progress)  │                    │   Meal)      │
                └──────────────┘                    └──────────────┘
```

## 7. Physical Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | 50 x 40 x 30 cm (W x D x H) |
| Weight | ~12-15 kg (estimated) |
| Power Input | 220-240V AC, 50 Hz (Indian standard) |
| Max Power Draw | < 2,000W (compatible with 15A household outlets) |
| Induction Heater | 1,800W peak, variable power |
| Display | 4" 480x320 capacitive touchscreen (SPI, ST7796S + FT6336) |
| Camera | IMX415-98 8 MP, 1280x720 @ 30 fps, overhead mounted |
| Connectivity | Wi-Fi 6 (2.4 GHz), Bluetooth 5.2 LE |
| Pot Capacity | 3-5 liters (removable, non-stick, dishwasher-safe) |
| Ingredient Dispensing | FID (6-canister carousel, 3 servos) + CID (5-slot carousel, 1 servo) + SLD (2 liquid channels) |
| Operating Temperature | 5°C - 45°C ambient |

## 8. Project Status

Early concept and design phase. No source code or hardware prototypes exist yet. The project definition and subsystem documentation are being established. Estimated timeline from prototype to production-ready product is 12-24 months.

### 8.1 Milestone Timeline

```
Phase 1: Prototype          Phase 2: Alpha              Phase 3: Beta               Phase 4: Production
(3-6 months)                (3-6 months)                (3-6 months)                (3-6 months)
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐    ┌───────────────────┐
│ - Off-shelf parts │       │ - Custom PCB      │       │ - 100+ recipes    │       │ - Manufacturing   │
│ - Basic recipe    │──────►│ - 20+ recipes     │──────►│ - Field testing   │──────►│ - BIS/CE cert     │
│   execution       │       │ - App integration │       │ - Pre-compliance  │       │ - Market launch   │
│ - Vision PoC      │       │ - Safety testing  │       │ - User feedback   │       │ - Support setup   │
└───────────────────┘       └───────────────────┘       └───────────────────┘       └───────────────────┘
```

## 9. Related Documentation

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]] - Detailed hardware specs
- [[01-Epicura-Architecture|Epicura Architecture]] - System block diagrams and wiring
- [[03-Sensors-Acquisition|Sensors & Acquisition]] - Sensor system design
- [[04-Mechanical-Design|Mechanical Design]] - Physical design and enclosure
- [[02-Controller-Software-Architecture|Controller & Software Architecture]] - Software design
- [[01-Tech-Stack|Tech Stack]] - Technology choices
- [[01-UI-UX-Design|UI/UX Design]] - User interface design
- [[01-Induction-Heating|Induction Heating]] - Heater subsystem
- [[02-Robotic-Arm|Robotic Arm]] - Stirring arm subsystem
- [[03-Ingredient-Dispensing|Ingredient Dispensing]] - Dispensing subsystem
- [[04-Vision-System|Vision System]] - Computer vision subsystem
- [[05-Exhaust-Fume-Management|Exhaust & Fume Management]] - Fume extraction subsystem
- [[01-Safety-Compliance|Safety & Compliance]] - Regulatory compliance
- [[01-Prototype-Development-Plan|Prototype Development Plan]] - Development roadmap
- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/08-Components/04-Total-Component-Cost|Total Component Cost]] - Full BOM and cost analysis

## 10. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-14 | Manas Pradhan | Initial document creation |
| 1.0 | 2026-02-15 | Manas Pradhan | Added revision history and metadata |
| 1.1 | 2026-11-04 | Manas Pradhan | Application processor changed from Raspberry Pi CM5 to Luckfox Pico Zero (RV1106G3): Buildroot, LVGL on 4" SPI LCD, SC3336 camera with ISP + NPU vision, UART/CAN bridge |
| 1.2 | 2026-11-04 | Manas Pradhan | Dispensing summary updated for servo carousels (FID/CID on one Dispenser Servo Block) |
| 1.3 | 2026-11-04 | Manas Pradhan | Camera IMX415-98 IR-CUT (8 MP, 98 deg lens) |
| 1.4 | 2026-11-04 | Manas Pradhan | Shared isolated CAN bus (RV1106 + STM32 + induction surface); heater PID on the RV1106 |
| 1.5 | 2026-11-04 | Manas Pradhan | IR thermometer removed (module-internal temperature control); 2S Li-ion backup on the Unified PCB; CAN servo stirring motor |
