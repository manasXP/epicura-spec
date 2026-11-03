# Epicura Skills

Claude Code skills for all Epicura platform repositories. Each repo should softlink the skills it needs from this directory.

## Skill-to-Repository Mapping

### `epicura-firmware` (STM32 FreeRTOS)
```bash
ln -s ../epicura-spec/skills/embedded-systems .claude/skills/
ln -s ../epicura-spec/skills/stm32-firmware .claude/skills/
ln -s ../epicura-spec/skills/pid-control .claude/skills/
ln -s ../epicura-spec/skills/dispensing-systems .claude/skills/
ln -s ../epicura-spec/skills/safety-compliance .claude/skills/
ln -s ../epicura-spec/skills/mqtt-iot .claude/skills/
```

### `epicura-rv1106` (C11 application on Buildroot, Luckfox Pico Zero)
```bash
ln -s ../epicura-spec/skills/buildroot-platform .claude/skills/
ln -s ../epicura-spec/skills/lvgl-ui .claude/skills/
ln -s ../epicura-spec/skills/computer-vision-edge .claude/skills/
ln -s ../epicura-spec/skills/recipe-engine .claude/skills/
ln -s ../epicura-spec/skills/mqtt-iot .claude/skills/
ln -s ../epicura-spec/skills/embedded-systems .claude/skills/
ln -s ../epicura-spec/skills/devops-engineer .claude/skills/
```
> Note: `devops-engineer` covers the CI that builds the image inside the `luckfoxtech/luckfox_pico:1.0` Docker image on the build host. Docker never runs on the device.

### `epicura-api` (Fastify + Next.js monorepo)
```bash
ln -s ../epicura-spec/skills/fastify-api .claude/skills/
ln -s ../epicura-spec/skills/nextjs-developer .claude/skills/
ln -s ../epicura-spec/skills/typescript-pro .claude/skills/
ln -s ../epicura-spec/skills/postgres-pro .claude/skills/
ln -s ../epicura-spec/skills/mqtt-iot .claude/skills/
ln -s ../epicura-spec/skills/api-designer .claude/skills/
ln -s ../epicura-spec/skills/react-expert .claude/skills/
ln -s ../epicura-spec/skills/devops-engineer .claude/skills/
```

### `epicura-ios` (SwiftUI)
```bash
ln -s ../epicura-spec/skills/swift-expert .claude/skills/
ln -s ../epicura-spec/skills/axiom-ios-ui .claude/skills/
ln -s ../epicura-spec/skills/swiftui-liquid-glass .claude/skills/
ln -s ../epicura-spec/skills/mobile-design .claude/skills/
ln -s ../epicura-spec/skills/api-designer .claude/skills/
```

### `epicura-android` (Kotlin Compose)
```bash
ln -s ../epicura-spec/skills/kotlin-specialist .claude/skills/
ln -s ../epicura-spec/skills/compose-expert .claude/skills/
ln -s ../epicura-spec/skills/mobile-design .claude/skills/
ln -s ../epicura-spec/skills/api-designer .claude/skills/
```

### `epicura-pcb` (KiCad 9)
```bash
ln -s ../epicura-spec/skills/safety-compliance .claude/skills/
```
> Note: `kicad`, `jlcpcb`, `bom`, `lcsc`, `digikey`, `mouser`, `element14`, `pcbway` are system-level Claude Code skills (not file-based) — they are always available.

## Full Inventory (23 skills)

| Skill | Type | Repos |
|-------|------|-------|
| `embedded-systems` | Marketplace | firmware, rv1106 |
| `stm32-firmware` | Marketplace | firmware |
| `pid-control` | Epicura | firmware |
| `dispensing-systems` | Epicura | firmware |
| `safety-compliance` | Epicura | firmware, pcb |
| `buildroot-platform` | Epicura | rv1106 |
| `computer-vision-edge` | Epicura | rv1106 |
| `recipe-engine` | Epicura | rv1106 |
| `lvgl-ui` | Epicura | rv1106 |
| `mqtt-iot` | Epicura | firmware, rv1106, api |
| `fastify-api` | Epicura | api |
| `nextjs-developer` | Marketplace | api |
| `typescript-pro` | Marketplace | api |
| `postgres-pro` | Marketplace | api |
| `api-designer` | Marketplace | api, ios, android |
| `react-expert` | Marketplace | api |
| `devops-engineer` | Marketplace | rv1106, api |
| `swift-expert` | Marketplace | ios |
| `axiom-ios-ui` | Marketplace | ios |
| `swiftui-liquid-glass` | Marketplace | ios |
| `kotlin-specialist` | Marketplace | android |
| `compose-expert` | Marketplace | android |
| `mobile-design` | Marketplace | ios, android |
