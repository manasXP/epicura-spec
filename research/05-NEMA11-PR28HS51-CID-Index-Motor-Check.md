---
created: 2026-11-04
status: Assessment
tags: [epicura, research, dispensing, cid, stepper, actuator]
---

# Robu Pro-Range NEMA11 PR28HS51-0674JX5.18 as the CID Index Motor — Suitability Check

**Candidate:** Robu.in SKU 1736844, "Pro-Range NEMA11 PR28HS51-0674JX5.18 1.2 kg-cm Stepper Motor", ₹2,759 incl. GST, in stock ([product page](https://robu.in/product/nema11-pr28hs51-0674jx5-18-1-2kg-cm-stepper-motor-d-type-shaft/))
**Datasheet:** [[jkong-JK28HS51-0674-nema11-stepper-datasheet.pdf]] (JKongMotor drawing JK28HS51-0674, rev A, downloaded from the Robu listing)
**Incumbent:** C1 carousel index = DS3218-class 270° servo on the Dispenser Servo Block, 4:3 gear-up to the carousel ring gear ([[../docs/05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing]] §3.1–3.2)

---

### Verdict

**Not as a drop-in, and not as listed.** The datasheet Robu attaches is for the *bare* JK28HS51-0674 motor (1.2 kg·cm holding, no gearbox) and the product photos show a bare 51 mm motor with a plain shaft, while the part name ("JX5.18") and the description claim a 5.18:1 planetary gearbox. Which one ships has to be confirmed with Robu before ordering.

- **Bare motor:** about 0.6–0.9 kg·cm at the carousel. The CID needs roughly 3–5 kg·cm. Rejected.
- **With the 5.18:1 gearbox (if actually fitted):** about 5.6 kg·cm at the gearbox output. Workable only with a ≥3:1 reduction into the ring gear (replacing the 4:3 gear-up), plus a bipolar stepper driver, a 12 V feed and a home sensor. That reinstates the stepper hardware the v6.0 architecture / v7.1 dispensing redesign just removed, at about three times the actuator cost.

Recommendation: keep the DS3218 servo for C1. Revisit a stepper only if the servo's 300° carousel travel limit (no continuous rotation, no shortest-path return to COVER) becomes a real problem; in that case pick a geared stepper with ≥10:1 total reduction and stall detection (e.g. TMC2209 StallGuard), not this part.

---

### What the datasheet says

| Item | JK28HS51-0674 (bare motor) |
|---|---|
| Frame | NEMA11, 28 × 28 mm, body 51 mm, 0.2 kg |
| Shaft | Ø5 h6 × 20 mm, round (title says D-type, page says round); Ø22 pilot |
| Mounting | 4× M2.5, 23 mm square pattern |
| Phases / step | 2-phase bipolar, 4 leads (BLK/GRN = A/C, RED/BLU = B/D), 1.8° (200 steps/rev) |
| Rated | 6.16 V, 0.67 A/phase peak, 9.2 Ω, 7.2 mH ±20 % |
| Holding torque | 1200 g·cm (1.2 kg·cm, 0.118 N·m) |
| Insulation | Class B (130 °C), 80 K rise max |
| Leads | UL1061 26 AWG, 300 mm |
| Gearbox | **None on the drawing.** Listing text claims an integrated 5.18:1 planetary, backlash ≤ 1°, not high precision |

---

### CID torque requirement (estimate)

The CID ring is lift-off, open-bottom bins over a fixed base plate (§2.2). The ring itself rides on a thin-section bearing, so bearing drag is small; the dominant load is dragging the bin contents across the plate.

| Quantity | Value | Basis |
|---|---|---|
| Food mass, 5 bins full | ≤ 1.0 kg | 5 × 200 mL, cut vegetables / dal / rice up to ~1 kg/L |
| Area-weighted mean radius | 83 mm | bins span r = 40 mm (hub) to 115 mm (ring) |
| Friction coefficient, wet food on PP | 0.3–0.6 | assumed |
| Sliding torque | 2.5–5 kg·cm | μ · m · g · r |
| Breakaway / wedged piece at a sector wall | higher, unquantified | why the spec keeps margin |
| **Spec allowance (servo via 4:3 gear-up)** | **≈ 13 kg·cm** | §3.2, ~3–4× margin |

---

### Candidate vs requirement

| Configuration | Torque at carousel | Margin vs 3–5 kg·cm | Result |
|---|---|---|---|
| Bare motor through the existing 4:3 gear-up | 0.9 kg·cm holding, ~0.6 running | 0.15–0.3× | Fails |
| Bare motor direct 1:1 | 1.2 holding, ~0.8 running | 0.2–0.4× | Fails |
| 5.18:1 planetary output through 4:3 gear-up | ~4.2 kg·cm | ~1× | Marginal, no reserve for wedging |
| 5.18:1 planetary + 3:1 ring reduction (15.5:1 total) | ~15 kg·cm | 3–5× | OK; 60° index ≈ 517 full steps ≈ 1 s at 500 pps |

Running torque is taken as ~65 % of holding at the step rates involved; planetary efficiency ~90 %.

---

### What a stepper C1 would add to the design

- **Driver and rail:** a bipolar chopper driver (TMC2209 / A4988 class) on the 12 V rail; STEP, DIR, EN on three STM32 GPIOs. The DSB's PCA9685 cannot drive it. The v6.0 architecture deleted exactly this (DRV8876 #2, J_CID).
- **Position feedback:** open loop with no absolute reference. Needs a home sensor at the COVER position (opto or Hall) and ideally stall detection for a wedged piece of food; the servo has an absolute internal potentiometer and needs neither (§3.2 "no homing required").
- **Idle:** rail switched off between dispenses as today, so no holding torque; base-plate friction keeps the ring in place. Acceptable.
- **Cost:** ₹2,759 (~$33) + driver vs ~$10 for the DS3218.
- **Gains, if ever needed:** continuous rotation (no 300° travel cap, shortest path home), finer and quieter indexing, no servo jitter.

---

### Open items

1. Confirm with Robu whether SKU 1736844 ships with the 5.18:1 planetary gearbox and what its output shaft and length are. The attached datasheet and photos say no.
2. Confirm the shaft profile (title: D-type, page: round).
3. If a stepper is pursued for any dispenser axis, measure the actual breakaway torque of a loaded CID ring on the printed base plate before sizing.

---

### Related

- [[../docs/05-Subsystems/03-Ingredient-Dispensing|Ingredient Dispensing System]] v7.1 (servo carousel, C1 index drive)
- [[../docs/02-Hardware/01-Epicura-Architecture|Epicura Architecture]] v8.0 §12 (DSB wiring, removed CID stepper hardware)
