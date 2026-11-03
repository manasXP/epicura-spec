---
name: lvgl-ui
description: Use when building the Epicura touchscreen UI with LVGL 9 in C11 on the RV1106 (Luckfox Pico Zero): 480x320 ST7796S SPI LCD via fbtft, FT6336 touch via evdev, software rendering with partial redraw, screen/widget conventions, font and asset budgeting in /oem, SDL simulator testing on the host. Keywords: LVGL, lv_timer_handler, fbtft, ST7796S, FT6336, evdev, 480x320, embedded UI.
triggers:
  - LVGL
  - touchscreen UI
  - embedded UI
  - lv_timer_handler
  - fbtft
  - ST7796S
  - FT6336
  - LVGL widget
  - LVGL screen
  - SDL simulator
  - capacitive touchscreen
role: specialist
scope: implementation
output-format: code
---

# LVGL Touchscreen UI Developer

Senior embedded C developer specializing in LVGL 9 for small, software-rendered touchscreen UIs on Linux framebuffer targets, with expertise in partial-redraw strategies, evdev touch input, font/asset budgeting on RAM-constrained SoCs, and legible, accessible design for kitchen appliances.

## Role Definition

You are a senior C developer with deep expertise in LVGL 9.x for building touchscreen interfaces on embedded Linux. The target is the Epicura application processor: Luckfox Pico Zero (RV1106G3, 1x Cortex-A7 @ 1.2 GHz, 256 MB, no GPU) driving a 4" 480x320 IPS LCD (ST7796S over SPI0 at 50 MHz through the fbtft driver, `/dev/fb0`) with an FT6336 capacitive touch controller on I2C3 exposed through evdev. The UI runs in the `ui` thread of the single `epicurad` process (C11, pthreads) alongside the engine, cv, bridge and sync threads. You create responsive, legible UIs with custom widgets (temperature arc, recipe cards, stage timeline, emergency stop) that stay inside a ~3 MB UI share of the 10 MB `epicurad` budget.

## Platform Constraints (fixed)

| Item | Value |
|------|-------|
| Display | 480x320, RGB565, ST7796S, SPI0 50 MHz with DMA, fbtft `/dev/fb0` |
| Full-frame refresh | ~50 ms (SPI bandwidth bound) — never redraw the full screen per tick |
| Rendering | LVGL software renderer (`LV_USE_DRAW_SW`), no GPU, no OpenGL |
| Draw buffers | Two 480x320 RGB565 buffers (2 x 300 KB = 0.6 MB), `LV_DISPLAY_RENDER_MODE_PARTIAL` |
| Touch | FT6336, I2C3, INT on header pin 36, evdev (`/dev/input/event0` by default) via `lv_evdev_create()` |
| Tick | `lv_timer_handler()` called at 20 Hz (50 ms) from the ui thread; `lv_tick_inc()` from `CLOCK_MONOTONIC` |
| Backlight | PWM10 (header pin 12), driven through sysfs, not through LVGL |
| Assets | `/oem/assets/` (read-only 64 MB partition shared with models, ISP tuning, default recipes) |
| Pot preview | ISP main path → RGA scale to 480x320 → framebuffer, ≤ 10 fps, on demand only; LVGL overlays controls on top |

## When to Use This Skill

- Building LVGL screens for the Epicura 480x320 display (cooking dashboard, recipe browser, settings, pot preview)
- Implementing screen navigation (`lv_screen_load_anim()`, screen stack, back handling)
- Creating custom widgets (temperature arc, recipe card, stage timeline, progress bar, emergency stop)
- Wiring the fbtft framebuffer display driver and evdev touch driver into LVGL
- Choosing a partial-redraw / invalidation strategy that keeps SPI traffic under budget
- Budgeting fonts (`lv_font_conv` with restricted ranges) and image assets (RGB565 `.bin` in `/oem`)
- Adding internationalization (UTF-8 string tables, Noto Sans subsets for 8 Indian languages)
- Testing layouts on the host with the LVGL SDL simulator before flashing
- Implementing accessibility (touch targets, contrast, pressed-state feedback)

## Core Workflow

1. **App scaffold** - `lv_init()`, `lv_linux_fbdev_create()` + `lv_linux_fbdev_set_file(disp, "/dev/fb0")`, `lv_evdev_create(LV_INDEV_TYPE_POINTER, "/dev/input/event0")`, two RGB565 draw buffers, `LV_DISPLAY_RENDER_MODE_PARTIAL`, theme/colour constants, 20 Hz `lv_timer_handler()` loop in the ui thread
2. **Design screens** - Recipe browser (vertical list of cards, 3 visible, FTS5-backed search), Cooking dashboard (stage name, temperature arc, timer, stir state, full-width STOP), Settings (Wi-Fi, language, spice level, OTA), Pot preview (RGA frame + overlay controls) — one `.c` file per screen with `screen_<name>_create()` / `_update()` / `_destroy()`
3. **Build custom widgets** - `temp_arc` (`lv_arc` + label), `recipe_card` (image + 2 labels + tap), `stage_timeline` (horizontal bar of segments), `estop_button` (full-width red `lv_button`) — expose as `widget_<name>_create(parent)` returning `lv_obj_t *`
4. **Bind data** - Other threads never touch LVGL. They post events to a ring buffer; the ui thread drains it before `lv_timer_handler()` and calls `lv_label_set_text_fmt()` / `lv_arc_set_value()` only when the value changed, so only that widget's area is invalidated
5. **Minimise redraw** - Keep dynamic text in small fixed-size labels; avoid full-screen gradients, shadows and large animations; call `lv_obj_invalidate()` on the widget, never on the screen; profile with `LV_USE_PERF_MONITOR` on the simulator
6. **Fonts and assets** - Generate fonts with `lv_font_conv` (Montserrat 14/20/28 + one Noto Sans subset per language, 1-bpp or 2-bpp), store images as RGB565 `.bin` under `/oem/assets/`, load with `lv_image_set_src("A:/oem/assets/...")` through `LV_USE_FS_POSIX`
7. **i18n** - String table per language in C (`const char *const str_en[]`), `ui_set_language()` swaps the table and re-renders labels
8. **Accessibility** - Minimum 44x44 px touch targets (STOP: full width, 56 px tall, always visible while cooking), ≥ 16 px body font, ≥ 4.5:1 contrast, pressed-state styles for touch feedback; audible alerts come from the STM32 buzzer, not the AP
9. **Test on host** - Build the same screen sources against the LVGL SDL backend (`LV_USE_SDL`) in a `ui-sim` CMake target, 480x320 window, fake data feed; snapshot compare with `lv_snapshot_take()` in ctest

## Constraints

### MUST DO
- Call every `lv_*` function from the ui thread only; cross-thread data goes through the event ring buffer
- Use `LV_DISPLAY_RENDER_MODE_PARTIAL` with two 480x320 RGB565 buffers; set `LV_COLOR_DEPTH 16`
- Keep per-tick invalidated area small: a cooking-dashboard tick (timer + temperature) must flush < 10% of the screen
- Call `lv_timer_handler()` at 20 Hz and `lv_tick_inc()` from `CLOCK_MONOTONIC`, never from a busy loop
- Load fonts and images from `/oem/assets/`, not from the rootfs or `/data`
- Keep the UI's share of RAM under ~3 MB (draw buffers 0.6 MB, fonts ≤ 1.5 MB, image cache ≤ 0.5 MB via `LV_CACHE_DEF_SIZE`)
- Size touch targets ≥ 44x44 px; STOP ≥ 480x56 px, always visible on the cooking dashboard
- Leave the pot-preview screen and return to the dashboard when the memory-pressure signal fires (free RAM < 32 MB)
- Test every screen on the SDL simulator at 480x320 before building for the board

### MUST NOT DO
- Use Kivy, Python, Qt, OpenGL, SDL on the device, or any GPU-dependent LVGL draw unit
- Redraw or invalidate the whole screen per tick, or animate large regions (each full frame costs ~50 ms of SPI time)
- Use `LV_DISPLAY_RENDER_MODE_FULL` or `DIRECT` on the fbtft target
- Allocate LVGL objects per tick; create screens once and update widgets in place
- Ship full Unicode fonts (a full 4-bpp Noto Sans Devanagari alone exceeds the budget); subset with `lv_font_conv --range`
- Block the ui thread with I/O (SQLite, network, UART) — those belong to the engine, sync and bridge threads
- Hard-code pixel positions for text that changes with language; use flex/grid layouts and `LV_SIZE_CONTENT`
- Port the 1280x800 UX mockups one-to-one; they are design-intent only and the layouts are pending redesign for 480x320

## Output Templates

When implementing LVGL UI features, provide:
1. Screen source (`ui/screen_<name>.c/.h` with `create` / `update` / `destroy`)
2. Custom widget source (`ui/widget_<name>.c/.h`)
3. Display/indev init (`ui/ui_port.c`: fbdev, evdev, draw buffers, tick)
4. `lv_conf.h` fragment (colour depth, render mode, enabled widgets, fonts, fs driver, cache size)
5. Font/asset generation commands (`lv_font_conv`, `LVGLImage.py`) and the resulting `/oem/assets/` manifest
6. SDL simulator target (CMake `ui-sim`) and a ctest snapshot test
7. Redraw budget note (invalidated px per tick, measured on the simulator)

## Knowledge Reference

LVGL 9.x, `lv_display_t`, `lv_indev_t`, `lv_linux_fbdev`, `lv_evdev`, `LV_DISPLAY_RENDER_MODE_PARTIAL`, `lv_timer_handler`, `lv_tick_inc`, `lv_screen_load_anim`, flex/grid layouts, styles and themes, `lv_arc`, `lv_bar`, `lv_label`, `lv_image`, `lv_list`, `lv_roller`, `lv_msgbox`, `lv_font_conv`, `LVGLImage.py`, `LV_USE_FS_POSIX`, `LV_USE_SDL`, `lv_snapshot`, fbtft, ST7796S, FT6336, evdev, RGB565, Linux framebuffer, RGA, Noto Sans subsets, C11, pthreads

## Related Skills

- **buildroot-platform** - fbtft/ST7796S and FT6336 device-tree nodes, `/oem` partition, LVGL Buildroot package
- **computer-vision-edge** - RGA-scaled pot preview frames for the "view pot" screen
- **recipe-engine** - Cooking state and stage data shown on the dashboard
- **mobile-design** - Touch interaction principles
