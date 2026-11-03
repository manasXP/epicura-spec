---
created: 2026-11-03
status: Assessment
tags: [epicura, research, compute, rv1106, cm5]
---

# Luckfox Pico Zero (RV1106G3) as a CM5 Replacement — Suitability Assessment

**Candidate:** Luckfox Pico Zero, Rockchip RV1106G3 | **Incumbent:** Raspberry Pi CM5 (4 GB / 64 GB) + CM5IO
**Datasheet:** [[rockchip-rv1106-datasheet-v1.9.pdf]] (Rockchip RV1106 Datasheet Rev 1.9, 2025)
**Trigger:** Proposal to swap the CM5 for the Luckfox Pico Zero sold by ThinkRobotics India.

---

### Verdict

**The Luckfox Pico Zero cannot replace the CM5 for the architecture as currently specified.** The RV1106 is an IP-camera class vision SoC, not an application processor. The CM5-side software stack in [[../docs/03-Software/02-Controller-Software-Architecture|Controller Software Architecture]] (Docker, PostgreSQL, Fastify, Kivy, Python TFLite) does not fit in 256 MB of RAM, Kivy has no GPU to run on, and the 10.1" DSI/HDMI display has no interface on this chip. It is only viable if the CM5 software plan is redesigned around it, and even then the Pico Zero board itself is the wrong Luckfox variant because it does not expose the RGB LCD pins.

Where it is genuinely strong: NPU inference, ISP image quality in steam, power, thermals, and cost.

---

### Side-by-Side

| Item | Luckfox Pico Zero (RV1106G3) | CM5 as specified | Impact |
|---|---|---|---|
| CPU | 1x Cortex-A7, 32-bit ARMv7, 1.2 GHz, NEON + FPU | 4x Cortex-A76, 64-bit, 2.4 GHz | ~10-15x less general compute |
| RAM | 256 MB DDR3L, 16-bit, in-package | 4 GB LPDDR4X | **Blocker** for current stack |
| Storage | 8 GB eMMC (HS200) + microSD | 64 GB eMMC | Fine for a lean stack |
| NPU | 1 TOPS INT8 (INT4/INT8/INT16), RKNN toolkit | None, CPU TFLite | Strong positive |
| GPU | None. 2D RGA only (scale, rotate, blend) | VideoCore VII, OpenGL ES 3.1 | **Blocker** for Kivy |
| Video | H.264/H.265 encoder up to 8 MP @ 15 fps; no decoder | Full codec | Streaming to app is free |
| ISP | 5 MP @ 30 fps hardware ISP: 3A, HDR, 2D/3D NR, dehaze, LSC, sharpen | libcamera software ISP pipeline | Strong positive for steam |
| Camera input | 2x 2-lane MIPI CSI (combinable to 4-lane), 1x DVP | 2x 4-lane CSI | OK; driver list is narrow: Luckfox supports only the IMX415-98 IR-CUT (colour) and ISG1321 (mono) on the Pico Zero, and marks its SC3336 module as not compatible with the Zero; 22-pin FPC connector |
| Display | Parallel RGB666/RGB565, serial RGB, MCU LCD; **max 1280x720**. No DSI, no HDMI. **Pico Zero header does not expose LCD pins** | 2x HDMI 2.0 or 2x 4-lane DSI | **Blocker** for 10.1" 1280x800 panel |
| Wireless | 2.4 GHz Wi-Fi 6, BT 5.2 LE, on-board + external antenna | Dual-band 802.11ac, BT 5.0 | 2.4 GHz only |
| Ethernet | 10/100 MAC + PHY on chip, not on the Zero board | Gigabit on CM5IO | Minor |
| USB | 1x USB 2.0 host/device (USB-C) | 2x USB 3.0 + USB 2.0 | Minor |
| Header | 40-pin RPi-style, 28 GPIO: SPI0 (master, 2 CS), SPI1 CS only, UART0/2/3/4, I2C1/2/3, 12 PWM. No SARADC pin exposed | 40-pin GPIO | Covers STM32 SPI bridge + touch I2C |
| Power | ~1 W class, 0.9 V core; no heatsink | 5-12 W, needs heatsink/fan | Strong positive |
| Thermal rating | Ambient -20 to +85 °C, Tj max 125 °C, θJA 27.3 °C/W | Throttles above ~80 °C | Strong positive inside hot enclosure |
| Package | QFN128, 12.3 mm, 0.35 mm pitch | SO-DIMM-style module | Custom PCB is feasible |
| Board size | 65 x 30 mm | 55 x 40 mm + carrier | Smaller |
| Price | $43.99 Luckfox, $46.99 Waveshare, ₹3,339 Hubtronics, ₹5,835 Evelta | ~$85 (CM5 $65 + CM5IO $20) | ~Half |

> ThinkRobotics product page could not be fetched (rate-limited on every attempt). Indian prices above are from Hubtronics and Evelta; both listings were out of stock on 2026-11-03.

---

### Why It Fails the Current Spec

1. **Memory.** The spec runs Docker with PostgreSQL 16, a Node/Fastify API, a Python Kivy UI, a Python TFLite CV pipeline, Mosquitto and a cloud-sync service. That is a multi-gigabyte workload. 256 MB will not boot it. The Luckfox "Docker Image Build" wiki page is about building the firmware inside a Docker container on an Ubuntu PC, not running containers on the board.
2. **Display.** The 10.1" 1280x800 HDMI/DSI panel has no path to this chip. The RV1106 display output is parallel/serial RGB or MCU LCD, capped at 1280x720. The Pico Zero does not break those pins out at all, so only an SPI LCD (practically ≤ 480x320) is possible on this board.
3. **UI framework.** Kivy requires OpenGL ES 2. The RV1106 has no 3D GPU, so Kivy is out regardless of RAM. LVGL (which Luckfox documents) or a framebuffer toolkit in C is the realistic choice.
4. **CPU and toolchain.** Single 32-bit A7. Python and OpenCV exist but will be slow; the NPU is reachable only through the RKNN C API on-board (the Python API runs on a PC simulator). The Fastify/Node layer has no sensible place to run. Everything in the CM5 column of the software architecture would be a rewrite.
5. **Board variant.** Even for a re-architected design the Zero is the wrong SKU. The Pico Ultra and the Core1106 SoM expose the RGB LCD interface; the Zero trades that for Wi-Fi and a compact footprint.

---

### Where It Genuinely Fits

- **Inference.** MobileNetV2 INT8 at 224x224 on a 1 TOPS NPU runs in single-digit milliseconds versus the < 200 ms budget in [[../docs/05-Subsystems/04-Vision-System|Vision System]]. RKNN model zoo supports MobileNet and YOLO on RV1106/RV1103; conversion path is ONNX → RKNN with INT8 calibration.
- **Image quality in steam.** The hardware ISP has dehaze, 2D/3D temporal noise reduction, HDR merge and tone mapping. These directly address the steam and variable-lighting problem the vision doc currently proposes to solve with OpenCV CLAHE on the CPU.
- **Streaming.** H.264/H.265 multi-stream encoder covers live view on the touchscreen and companion app without touching the CPU.
- **Thermals and power.** Roughly a tenth of the CM5's power, no heatsink, rated for 85 °C ambient. The CM5 will throttle inside a cooking enclosure without active cooling.
- **STM32 bridge.** SPI0 master (MOSI/MISO/CLK/CS0/CS1) plus four spare UARTs on the header cover the existing bridge design in [[../docs/02-Hardware/01-Epicura-Architecture|Hardware Architecture]].
- **Cost and footprint.** About half the price of CM5 + CM5IO, in a 65 x 30 mm board, and the QFN128 package is realistic for a custom appliance PCB.

---

### Options

| # | Path | Spec impact | Recommendation |
|---|---|---|---|
| 1 | **Keep CM5 for the prototype.** Revisit compute for production once cooking and mechanics are proven. | None | **Preferred for prototype** |
| 2 | **Move to an RK3566-class board** (e.g. Radxa Zero 3W: 4x Cortex-A55, 2-8 GB, native MIPI DSI + HDMI, 0.8 TOPS NPU, Wi-Fi 6) if the goal is a cheaper, cooler Linux host while keeping the Python + DSI design. | Small: swap compute component, carrier and GPIO map; software plan survives | Best "cheaper CM5" move |
| 3 | **Commit fully to RV1106** for appliance-grade cost: C/C++ or Rust on Buildroot, LVGL on an RGB panel, SQLite instead of PostgreSQL, MQTT client only (no local broker), RKNN C API, Pico Ultra or Core1106 SoM instead of the Zero. | Large: rewrite of the CM5 software architecture, compute components, display choice, repository plan and `epicura-cm5` repo stack | Only if BOM cost is the dominant driver |

A hybrid (RV1106 as a vision co-processor beside a cheaper Linux host) adds a second Linux image, a second boot chain and an extra inter-processor link for little gain; not recommended.

**Decision needed:** Path 1 or 2 keeps the current spec essentially intact. Path 3 requires re-baselining the software architecture before any further CM5-side documents are written.

---

### Key Datasheet Facts (RV1106 Rev 1.9)

- Cortex-A7 with 32 KB I/D L1, 128 KB L2, NEON, FPU, TrustZone; separate MCU core for low-power tasks with a mailbox to the A7.
- Memory: RV1106G3 SIP 2 Gb (256 MB) DDR3L 16-bit; boot from SPI, eMMC, SD; download over USB/UART.
- Peripherals: 6 UART (up to 4 Mbps), 2 SPI (master/slave), 5 I2C, 12 PWM with capture, 2-channel 10-bit SARADC at 1 MS/s, TS-ADC, RTC, two watchdogs, 8-channel I2S, audio codec, 10/100 Ethernet MAC + PHY, USB 2.0 OTG, SDIO 3.0.
- Video in: 2x MIPI CSI D-PHY v1.2, 2 lanes each at 1.5 Gbps/lane, combinable to 4 lanes; 1x DVP up to 150 MHz.
- Video out: parallel RGB 18/16-bit, serial RGB, MCU LCD; max 1280x720; VOP with one window layer, alpha blend, BCSH.
- Codec: H.265 Main / H.264 High, level 5.0; G3 up to 8 MP @ 15 fps; JPEG 4 MP @ 60 fps; no video decoder.
- NPU: 1 TOPS (G3) INT4/INT8/INT16; TensorFlow, TFLite, PyTorch, ONNX, Caffe via RKNN toolkit.
- RKIVE: hardware CV primitives (Canny, Sobel, LK optical flow, CCL, GMM background, histogram, morphology).
- Security: AES/SHA/RSA engines, secure OTP, secure boot, TRNG.
- Supply: CPU 0.9 V (0.85-1.05), logic 0.9 V, DDR IO 1.35 V, GPIO 1.8/3.3 V banks, RTC 3.3 V.
- Operating: ambient -20 to +85 °C, Tj max 125 °C, θJA 27.3 °C/W, θJC 8.4 °C/W.
- Package: RoHS QFN128, 12.3 x 12.3 mm, 0.35 mm pitch.

### Luckfox Pico Zero Board Facts

- RV1106G3, 256 MB DDR3L, 8 GB eMMC, microSD (storage only), 2.4 GHz Wi-Fi 6 + BT 5.2 module with antenna switch.
- 40-pin header: SPI0 (MOSI 50, MISO 51, CLK 49, CS0 48, CS1 58), SPI1 CS1 only, UART0/2/3/4, I2C1/2/3, PWM0-11 across muxes, 3.3 V IO. No SARADC, no LCD pins.
- Camera FPC (4-lane MIPI CSI), USB-C (power + flashing), on-board mic, MX1.25 speaker header (8 Ω 1 W), RTC battery header, user LED, RESET/BOOT buttons.
- 65 x 30 mm, four Ø3.0 mm mounting holes.
- OS: Buildroot via Luckfox SDK (`./build.sh lunch`, board option 8). No desktop environment; Ubuntu image not documented for the Zero.

---

### Sources

- [Rockchip RV1106 Datasheet Rev 1.9](https://rockchip.fr/RV1106%20datasheet%20V1.9.pdf) (local copy: `rockchip-rv1106-datasheet-v1.9.pdf`)
- [Luckfox Pico Zero wiki](https://wiki.luckfox.com/Luckfox-Pico-Zero)
- [Luckfox Pico Zero store page](https://www.luckfox.com/Luckfox-Pico-Zero)
- [Luckfox RKNN guide](https://wiki.luckfox.com/Luckfox-Pico-Zero/RKNN)
- [Luckfox Docker image build page](https://wiki.luckfox.com/Luckfox-Pico-Zero/Docker-Image-Build)
- [ThinkRobotics listing](https://thinkrobotics.com/products/luckfox-pico-zero-linux-micro-development-board-based-on-luckfox-rv1106g3-chip) (not fetchable at time of writing)
- [Hubtronics listing](https://hubtronics.in/luckfox-pico-zero?tag=zero)
- [Evelta listing](https://evelta.com/luckfox-pico-zero-linux-micro-development-board-8gb-emmc-wireless-module)
- [Waveshare listing](https://www.waveshare.com/Luckfox-Pico-Zero.htm)
- [CNX Software on RV1106 boards](https://www.cnx-software.com/2024/02/29/luckfox-pico-pro-pico-max-rockchip-rv1106-boards-100m-ethernet-5mp-camera/)

---

#epicura #research #compute #rv1106 #cm5
