---
created: 2026-02-14
modified: 2026-11-05
version: 1.15
status: Draft
tags: [epicura, project-overview, kitchen-robot]
---

# Epicura - Project Overview

## 1. Project Description

Development of an autonomous countertop kitchen robot that cooks complete one-pot meals using AI-powered computer vision, robotic stirring, and precise electric heat control. Epicura is designed for the Indian home market, inspired by the commercial Posha robot chef, and engineered to operate within compact Indian kitchens on standard household outlets (under 2kW). The system combines embedded Linux compute, real-time motor control, and edge AI inference to deliver fully autonomous cooking from ingredient loading to finished meal.

## 2. Key Components

This project encompasses the following major subsystems:

- [[__Workspaces/Appliance/Epicura/epi-Spec/docs/02-Hardware/02-Technical-Specifications|Technical Specifications]] - Heating, robotic arm, sensors, and power budget
- [[01-Epicura-Architecture|Epicura Architecture]] - System block diagrams and hardware wiring
- [[03-Sensors-Acquisition|Sensors & Acquisition]] - Camera, module-reported cooking temperature, and pot detection
- [[04-Mechanical-Design|Mechanical Design]] - Three-unit enclosure (Cooking Surface, Stirring Unit, lift-off Dispensing Unit), arm mechanism, dock and industrial design
- [[02-Controller-Software-Architecture|Controller & Software Architecture]] - Software modules across the RV1106 and the two STM32G0B1 controllers, and the recipe state machine
- [[01-Tech-Stack|Tech Stack]] - Hardware platforms, software frameworks, and tools
- [[01-UI-UX-Design|UI/UX Design]] - Touchscreen interface and companion mobile app
- [[01-Electric-Heating|Electric Heating]] - 1,300W (assumed) electric heating unit of the rice-cooker class with CAN bus control (unit-internal temperature loop); reference unit Philips OneChef NX5300/00, whose body is the Cooking Surface (Epicura's pot is a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot, 6 L max fill)
- [[02-Robotic-Arm|Robotic Arm]] - Single-axis servo arm and stir patterns
- [[03-Ingredient-Dispensing|Ingredient Dispensing]] - Three-subsystem dispensing (FID/CID/SLD)
- [[04-Vision-System|Vision System]] - HD camera, edge AI, and cooking stage detection
- [[05-Exhaust-Fume-Management|Exhaust & Fume Management]] - Exhaust fan, grease/carbon filtration
- [[01-Safety-Compliance|Safety & Compliance]] - Electrical safety and food contact regulations

## 3. Core Features

### 3.1 Autonomous Cooking
- Fully hands-off operation after ingredient loading and recipe selection
- State machine recipe execution: detect cooking stage via CV, adjust heat/stir, dispense ingredients
- Automatic ingredient dispensing via three subsystems: FID (fine ingredients, 6-canister servo carousel with ¼ tsp dosing), CID (coarse items, 5-slot servo carousel), SLD (liquids, drawer tanks with pumps in the body, open-loop tach metering)
- Supports one-pot recipes: curries, dal, rice, biryani, stir-fries, pasta, soups

### 3.2 Recipe Intelligence
- 100+ curated Indian recipes at launch with regional variations (North, South, East, West)
- App-driven customization for spice levels, allergen substitutions, and dietary preferences
- Cloud-updatable recipe library with new recipes pushed via OTA
- Full offline fallback with local SQLite recipe database for uninterrupted cooking

### 3.3 Precision Control
- Temperature-controlled electric heating (the heating unit's own loop on its spring-loaded centre sensor; the RV1106 sends setpoints over the shared isolated CAN bus) with dynamic temperature range (60-200°C)
- Pot-bottom and element temperature reported by the heating unit over CAN (no thermometer of Epicura's own)
- Sear at 180-200°C, simmer at 60-100°C with ±5°C accuracy
- Dynamic power management to stay within 2kW household limit

### 3.4 Vision System
- Overhead IMX415-98 camera (8 MP, 98 deg lens, 1280x720 @ 30 fps) on the underside of the lift-off Dispensing Unit, looking straight down into the pot behind a sealed window, with a white PWM LED ring
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
- **Apartment/Compact Kitchens** - Countertop form factor (50x40x35cm, height to be confirmed) designed for space-constrained urban homes
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
| **Size/Power** | Countertop, ~1.8kW | 50x40x35cm (height TBC), <2kW for standard Indian 15A outlets |
| **Recipes** | Curated library, cloud-updated | 100+ Indian recipes at launch, cloud-updatable, offline fallback |
| **Connectivity** | WiFi, app-paired | WiFi + BT, native companion apps (iOS + Android), OTA updates |
| **Price Target** | ~$800 USD (commercial) | $400-600 USD (target retail for Indian market) |

## 6. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Epicura System Architecture                           │
│                                                                             │
│  DISPENSING UNIT (DU) — lifts straight off, battery is the primary supply   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Unified PCB v5.0: Luckfox Pico Zero (RV1106G3) + DU STM32G0B1RE     │  │
│  │  (UART host link), 2S Li-ion pack, dispenser drivers (PCA9685 DSB,    │  │
│  │  6 V pumps + Hall tachs), SLD tank sensing, INA219 battery monitor,   │  │
│  │  DU STM32 CAN node (FDCAN1 + ISO1050), dock pads                      │  │
│  │  ┌────────────────────────────────┐  ┌──────────────────────────────┐ │  │
│  │  │  Buildroot Linux / epicurad    │  │  4" Touch Display (LVGL)     │ │  │
│  │  │  Recipe State Machine          │  │  IMX415-98 Camera + white    │ │  │
│  │  │  CV Pipeline (ISP → NPU)       │  │   LED ring (underside, into  │ │  │
│  │  │  Dispense thread (FID/CID/SLD  │  │   the pot)                   │ │  │
│  │  │   via the DU STM32 host link)  │  │  FID + CID carousels, SLD    │ │  │
│  │  │  Power/dock status, LVGL UI    │  │   oil + water drawer tanks   │ │  │
│  │  │  Cloud Sync / OTA, SQLite      │  │  WiFi / BT, buzzer           │ │  │
│  │  └────────────────────────────────┘  └──────────────────────────────┘ │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │ J_DOCK: 8 magnetic pogo contacts on the  │
│                                  │ left pillar (DOCK_24V charge + isolated  │
│                                  │ CAN + dock sense); dead when lifted      │
│  COOKING SURFACE (CS) — mains    ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Cooking Surface Controller (CSC): STM32G0B1RE, FreeRTOS              │  │
│  │  ┌─────────────────────┐   ┌──────────────────┐  ┌──────────────────┐ │  │
│  │  │  Heater Interlock   │   │  Electric Heating│  │  3× PSU: 2× LRS- │ │  │
│  │  │  Stir Motor (CAN)   │◄─►│  Unit (1,300 W,  │  │ 75-24 + LRS-35-12│ │  │
│  │  │  Safety Watchdog    │CAN│  own PID, own AC │  │  IEC C14, E-stop,│ │  │
│  │  │  Fans, dock switch  │iso│  via K_SAFE; CAN)│  │  relays, 2x fans │ │  │
│  │  └──────────┬──────────┘   └──────────────────┘  └──────────────────┘ │  │
│  └─────────────┼─────────────────────────────────────────────────────────┘  │
│                │ J_SU (24V_SU + isolated CAN) harness in the right pillar   │
│                ▼  STIRRING UNIT (SU) — own PSU (LRS-75-24 #2), no mains     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Gantry between the rear pillars: 24 V CAN servo stir motor, shaft,   │  │
│  │  paddle, fume hood                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Data Flow Overview

```
┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│  User    │    │  Recipe      │    │  CV Pipeline  │    │  Actuators   │
│  Input   │───►│  State       │───►│  (ISP→NPU)    │───►│ (STM32: heat,│
│  (App/   │    │  Machine     │    │               │    │ stir; RV1106:│
│   Touch) │    │  (RV1106)    │    │  Stage?       │    │ dispense)    │
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
| Dimensions | 50 x 40 x ≈37 cm (W x D x H; height to be confirmed); Dispensing Unit a Ø35 cm disc ≤ 15 cm tall |
| Weight | ~12-15 kg (estimated); Dispensing Unit ≤ 4 kg fully loaded (two-hand lift) |
| Units | Cooking Surface (mains: electric heating unit, PSU, Cooking Surface Controller with the STM32, E-stop, fans) + Stirring Unit (24 V + CAN from the CS over one internal harness) + Dispensing Unit (lifts off with no cable: RV1106 brain, 2S Li-ion primary supply, all three dispensers, LCD, camera; docks on the left pillar for charge + CAN) |
| Battery | 2S2P 18650 Li-ion, 5,200 mAh (~38 Wh) in the Dispensing Unit; > 12 h lifted, 1 A charge while docked (≈ 5.5 h) |
| Power Input | 220-240V AC, 50 Hz (Indian standard) |
| Max Power Draw | < 2,000W (compatible with 15A household outlets) |
| Electric Heater | 1,300W peak (assumed; rice-cooker-class unit, TBD), variable power |
| Display | 4" 480x320 capacitive touchscreen (SPI, ST7796S + FT6336) |
| Camera | IMX415-98 8 MP, 1280x720 @ 30 fps, on the Dispensing Unit underside looking straight down |
| Connectivity | Wi-Fi 6 (2.4 GHz), Bluetooth 5.2 LE |
| Pot Capacity | 6 L usable at the max-fill line, ≈ 7.3 L brim (25 × 25 × 12 cm rounded-square rounded-square non-stick pot; removable, dishwasher-safe) |
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
- [[01-Electric-Heating|Electric Heating]] - Heater subsystem
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
| 1.6 | 2026-11-04 | Manas Pradhan | Three-unit architecture: STM32 on the Cooking Surface Controller, dispensers + battery + brain in the lift-off Dispensing Unit (Unified PCB v4.0), Stirring Unit on one harness, magnetic pogo dock with charge + CAN; system diagram, data flow and physical specifications updated; height ≈ 35 cm (TBC) |
| 1.7 | 2026-11-04 | Manas Pradhan | Heater changed from the induction surface to a commercial electric heating unit of the rice-cooker class (1,300 W assumed, own PID, CAN port; same CAN contract): summary, features, system diagram and physical specifications updated; temperature source wording corrected (pot-bottom + element temperature over CAN) |
| 1.8 | 2026-11-04 | Manas Pradhan | Reference unit Philips OneChef NX5300/00 named (donor body = Cooking Surface, 6 L non-stick pot ~4.8 L usable); temperature range 60-200°C, sear 180-200°C |
| 1.11 | 2026-11-04 | Manas Pradhan | MCU back in the Dispensing Unit: Unified PCB v5.0 carries the RV1106 and a DU STM32G0B1RE (dispensing, battery/dock monitor, DU CAN node, UART host link to the RV1106); three controllers (RV1106 + two STM32G0B1); system diagram and index line updated |
| 1.12 | 2026-11-04 | Manas Pradhan | Stirring Unit on its own floating PSU (second LRS-75-24, AC cut by K_SU) and both CSC CAN ports isolated: system diagram updated |
| 1.9 | 2026-11-04 | Manas Pradhan | Pot changed to a 25 × 25 × 12 cm rounded-square rounded-square non-stick pot (≈ 7.3 L brim, 6 L max fill) replacing the donor's round 6 L inner pot; subsystem summary and physical specifications updated |
| 1.10 | 2026-11-04 | Manas Pradhan | Dispensing Unit battery 2S2P 18650, 5,200 mAh (~38 Wh), > 12 h lifted |
| 1.13 | 2026-11-05 | Manas Pradhan | CSC powered by a 12 V SELV tap from the heating unit's control board (CSC v1.5): system diagram updated |
| 1.14 | 2026-11-05 | Manas Pradhan | CSC on its own Mean Well LRS-35-12, K_SAFE on the heating unit's AC inlet, nothing tapped from the unit (CSC v1.6, reversing 1.13): system diagram updated |
| 1.15 | 2026-11-05 | Manas Pradhan | Robot-mop SLD and Ø350 mm DU disc: feature bullet, system diagram line and dimensions row updated |
