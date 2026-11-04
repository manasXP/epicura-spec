# Epicura — Product Vision

## The Problem

Cooking a home-cooked Indian meal takes 45-90 minutes of active attention — tempering spices at the right oil temperature, stirring dal so it doesn't stick, adding ingredients in precise sequence, and watching the pot so nothing burns or boils over. For working professionals, elderly individuals, and anyone in a compact urban apartment, this daily ritual is a source of friction: skipped meals, unhealthy takeout, or exhausting evenings over a hot stove.

Existing kitchen appliances (pressure cookers, air fryers, instant pots) automate fragments of the process but still require the cook to measure, sequence, monitor, and intervene. No affordable product available in India today can take raw ingredients and autonomously produce a finished one-pot meal.

## The Vision

**Epicura is an autonomous countertop kitchen robot that cooks complete one-pot meals — from raw ingredients to a finished dish — with no human intervention after loading.**

You select a recipe, load the ingredients into labeled compartments, press start, and walk away. Epicura handles the rest: heating oil to the right temperature, dispensing spices in measured quantities, adding vegetables and liquids on cue, stirring with the correct pattern and speed, monitoring the food through a camera to detect cooking stages, and adjusting heat in real time. When the meal is done, your phone buzzes.

### What Epicura Cooks

Epicura targets one-pot recipes that represent the daily cooking reality of Indian households:

- **Dals** — Tadka, Makhani, Moong, Sambar, Panchmel
- **Curries** — Paneer Butter Masala, Chole, Rajma, Aloo Gobi, Butter Chicken, Kadai Paneer
- **Rice dishes** — Jeera Rice, Veg/Chicken/Mutton Biryani, Pulao, Khichdi
- **Beyond Indian** — Pasta, stir-fries, soups, one-pot global recipes

324 recipes at launch across 9 cuisines, expandable over-the-air.

## Target User

**Primary:** Urban Indian households (apartments, compact kitchens) where cooking is a daily necessity but time and energy are scarce — working couples, single professionals, elderly parents living independently, hostel and mess kitchens.

**Key constraints these users share:**
- Standard 220-240V, 15A household outlet (no special wiring)
- Limited countertop space
- Preference for fresh, home-style food over packaged meals
- Familiarity with regional spice profiles and dietary preferences (vegetarian, Jain, vegan)

## Design Principles

### 1. Hands-Off After Loading
The core promise. Once ingredients are in and a recipe is selected, the user's job is done. No stirring, no checking, no adjusting. The machine handles timing, temperature, sequencing, and anomaly detection autonomously.

### 2. Safety Is Non-Negotiable
A 1,300W (assumed) heating plate and moving parts in a home kitchen demand rigorous safety engineering. Epicura implements defense-in-depth: a hardware e-stop relay that cuts AC power independent of firmware, an independent watchdog timer, thermal runaway detection, pan-presence sensing, and torque-limited stirring. The system is designed to be safe even if any single component fails. Certification targets: IEC 60335 (international), BIS IS 302 (India).

### 3. Three Taps to Cooking
The touchscreen and companion app follow a rule: recipe selection to cooking start in three taps or fewer. Home screen shows favorites and recent recipes. One tap opens detail. One tap starts the guided loading flow. One tap begins cooking.

### 4. Works Without Internet
Every recipe, UI asset, and control algorithm runs locally on the device. Cloud connectivity enables recipe updates, remote monitoring, and OTA firmware upgrades — but the machine cooks a full meal with WiFi unplugged.

### 5. Affordable for India
Target retail price of $300-400 USD, roughly quarter of the price of comparable international products. Achieved through commodity ARM processors (Rockchip RV1106G3 on a Luckfox Pico Zero), off-the-shelf rice-cooker-class heating units, and JLCPCB-fabricated custom PCBs with LCSC-sourced components.

## How It Works

### Hardware

A compact countertop unit (50 x 40 x 30 cm, ~12-15 kg) with:

- **1,300W (assumed) electric heating unit** — Commercial rice-cooker-class unit with its own PID and a CAN bus interface. No custom mains electronics; pre-certified for electrical safety; any flat-bottomed pot.
- **Robotic stirring arm** — 24V BLDC motor, 360-degree continuous rotation, removable food-safe silicone paddle. Stirs, scrapes, and folds per recipe instructions.
- **Three dispensing subsystems:**
  - **Liquids (SLD)** — 2 peristaltic pumps for oil and water, closed-loop weight verification via load cells
  - **Spices (FID)** — 6 sealed canisters on a servo carousel, each with a built-in measure wheel dosing in quarter-teaspoon increments
  - **Solids (CID)** — 5-slot servo carousel for vegetables, dal, rice, meat; each slot drops whole into the pot
- **Vision system** — Overhead camera with LED ring illumination, hardware ISP for steam and haze, running MobileNetV2 INT8 on the RV1106's NPU for cooking stage detection (raw, browning, boiling, simmering, done)
- **4-inch touchscreen** — Capacitive, 480x320, showing recipe browser, cooking progress, and an on-demand pot preview
- **Exhaust** — Dual 120mm fans with grease pre-filter and activated carbon cartridge, <45 dB

### Intelligence

A dual-processor architecture splits responsibilities:

| Processor | Role |
|-----------|------|
| **Rockchip RV1106G3** (Luckfox Pico Zero; Cortex-A7 + 1 TOPS NPU + ISP) | AI vision, recipe engine, touchscreen UI, cloud sync, heater PID over the isolated CAN bus |
| **STM32G0B1** (Cortex-M0+) | Real-time motor/servo drive, dispensers, sensor polling, CAN node, heater off-switch, safety watchdog |

The RV1106 runs Buildroot Linux with a single native C application, `epicurad`: SQLite (recipe database), MQTT and REST clients to the cloud, a recipe engine with hierarchical state machine, a hardware ISP + NPU (RKNN) vision pipeline, and an LVGL touchscreen application.

The STM32 runs FreeRTOS with priority-scheduled tasks for motor control at 50 Hz, CAN communication, sensors and dispensing, and a safety monitor that operates independently of all application logic. The heating unit runs its own temperature loop; the RV1106 sends setpoints over one isolated CAN bus shared with the STM32 and the heating unit's own controller.

### Software Ecosystem

- **Companion apps** — Native iOS (SwiftUI) and Android (Jetpack Compose) for BLE device pairing, WiFi provisioning, remote recipe browsing, live camera streaming during cooking, push notifications on completion, and dietary preference profiles.
- **Cloud backend** — Fastify (TypeScript) API with PostgreSQL, serving recipe updates, device telemetry, user accounts, and OTA firmware distribution.
- **Admin portal** — Next.js dashboard for recipe management, device fleet monitoring, and user administration.

## Competitive Position

Epicura is modeled after the [Posha robot chef](https://www.posha.com), a commercial product that validates the autonomous cooking concept. Epicura differentiates on:

| Dimension          | Posha           | Epicura                                                                           |
| ------------------ | --------------- | --------------------------------------------------------------------------------- |
| Price              | ~$1400          | $500-700 (target)                                                                 |
| Market             | Global          | India-first (regional recipes, languages, power grid)                             |
| Monitoring         | App only        | App + 4" local touchscreen                                                        |
| Mobile apps        | Single app      | Native iOS + Android                                                              |
| Languages          | English         | 8 languages (English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi) |
| Recipes at launch  | Curated library | 108 across 9 cuisines, heavy Indian focus                                         |
| Offline capability | Cloud-dependent | Fully offline-capable                                                             |
| Updates            | Cloud-pushed    | OTA with A/B partition rollback                                                   |

## Recipe Intelligence

Recipes are not simple timers. Each recipe is a structured YAML document defining up to 5 cooking segments, where each segment specifies:

- Pot surface temperature setpoint
- Which liquids to dispense and how much (ml)
- Which spice canisters to activate and dosage (multiples of 1/4 tsp)
- Which solid ingredient trays to empty
- Heat profile (Low through High) and duration
- Stirring profile (speed, direction, pattern)

![[Cooking-Process-Overview.excalidraw]]
![[Cooking Process Overview.png]]
The recipe engine executes segments as a state machine, using CV feedback to confirm cooking stage transitions before advancing. If the vision system detects an anomaly (burning, boil-over), it can pause cooking, reduce heat, and alert the user.

Users customize recipes through the companion app: adjust spice levels, swap ingredients for allergen or dietary reasons, change serving sizes. Preferences are stored in a profile (vegetarian, vegan, Jain, preferred cuisines, spice tolerance) that filters and adapts the recipe library.

## Product Roadmap

| Phase | Duration | Milestone |
|-------|----------|-----------|
| **Prototype** | Months 1-6 | Off-shelf parts, basic recipe execution, vision proof-of-concept |
| **Alpha** | Months 7-12 | Custom PCBs, 20+ validated recipes, companion app integration, safety testing |
| **Beta** | Months 13-18 | 100+ recipes, field testing in real kitchens, pre-compliance testing |
| **Production** | Months 19-24 | BIS/CE certification, manufacturing, market launch |

## Success Metrics

- **Cooking accuracy** — Finished dish matches reference recipe in taste panel testing for 90%+ of recipes
- **Autonomy** — Zero human intervention required from start to plate for all supported recipes
- **Safety** — Pass IEC 60335 and BIS certification; zero thermal or electrical incidents in 1,000+ hours of endurance testing
- **Reliability** — MTBF > 2,000 hours; successful OTA update and rollback in field conditions
- **User experience** — Recipe selection to cooking start in <60 seconds; 8-language UI with >48px touch targets; companion app rating >4.5 stars
- **Cost** — Bill of materials under $200 at production volume; retail price $400-600

## The Outcome We're Building Toward

A household in Bangalore places dal, vegetables, and rice into Epicura's compartments before leaving for work. From the office, they select tonight's dinner on their phone — Sambar with Jeera Rice. Epicura begins cooking at the scheduled time, tempering mustard seeds in oil, adding lentils and tamarind at the right moment, monitoring the simmer through its camera, and adjusting heat as the consistency thickens. When they walk through the door, dinner is ready, the kitchen smells like home cooking, and the pot lifts out for serving. Tomorrow, they'll try Butter Chicken.

That's the product.
