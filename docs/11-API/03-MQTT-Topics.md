---
created: 2026-02-15
modified: 2026-11-04
version: 1.1
status: Draft
---

# MQTT Topics

## 1. Overview

MQTT is the primary telemetry protocol between Epicura devices (RV1106) and the cloud backend. The device publishes real-time cooking data, device status, and alerts; the backend publishes commands for live view, recipe sync, OTA checks, remote cooking control, and configuration updates. The device side is the `epicurad` sync thread using libmosquitto as a client only: there is no broker on the device and no broker bridge.

This document extends the MQTT telemetry format defined in [[02-Controller-Software-Architecture#5.6 Cloud Sync (RV1106)|Controller Software Architecture - Cloud Sync]].

---

## 2. Broker Configuration

| Setting | Development | Production |
|---------|-------------|------------|
| **Broker** | Eclipse Mosquitto 2.x | AWS IoT Core |
| **Port** | 1883 (TCP) / 9001 (WebSocket) | 8883 (TLS) |
| **Protocol** | MQTT 3.1.1 | MQTT 3.1.1 |
| **Auth (Dev)** | Username/password | X.509 device certificates |
| **Auth (Prod)** | — | AWS IoT policy per device |
| **TLS** | Optional (dev) | Required (mutual TLS) |
| **Max Message Size** | 256 KB | 128 KB (AWS IoT limit) |
| **Keep Alive** | 60 seconds | 60 seconds |

The device connects to this broker directly over TLS as a libmosquitto client (persistent session, reconnect with backoff). The Mosquitto instance is a development-host broker, never an on-device one.

---

## 3. Topic Hierarchy

All topics follow the pattern: `epicura/{device_id}/{category}/{event}`

```
epicura/
└── {device_id}/                          Device-specific namespace
    ├── telemetry                          Periodic sensor readings
    ├── session/
    │   ├── started                        Cooking session began
    │   ├── progress                       Stage/temp/stir updates
    │   ├── completed                      Cooking finished successfully
    │   └── error                          Cooking error or abort
    ├── status                             Device online/offline/health
    ├── alert                              Warnings and critical events
    └── cmd                                Commands TO device (single topic subscribed by
                                           epicurad; `command` field selects the action)
```

---

## 4. Device Telemetry (RV1106 → Cloud)

### 4.1 `epicura/{device_id}/telemetry`

Periodic sensor readings published every 10 seconds during cooking, every 60 seconds when idle.

**QoS:** 1 (at least once)

**Offline:** while the broker is unreachable, telemetry rows are spooled to the device's SQLite `sync_outbox` table (capped at 1,000 rows, oldest dropped first) and replayed in order on reconnect.

**Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T12:30:00Z",
  "state": "COOKING",
  "recipe": "dal_tadka",
  "stage": "Simmer Dal",
  "temperature": 96.2,
  "target_temperature": 95.0,
  "stir_active": true,
  "stir_pattern": "intermittent",
  "stir_rpm": 30,
  "weight_g": 1250,
  "progress_pct": 72,
  "cv_class": "thick_consistency",
  "cv_confidence": 0.81,
  "power_pct": 45,
  "ambient_temp": 28.3,
  "coil_temp": 142.0
}
```

This extends the telemetry payload format from [[02-Controller-Software-Architecture#5.6.2 MQTT Telemetry|Controller Software Architecture]] with additional fields (`target_temperature`, `stir_pattern`, `stir_rpm`, `weight_g`, `cv_class`, `cv_confidence`, `power_pct`, `coil_temp`).

---

### 4.2 `epicura/{device_id}/session/started`

Published when a cooking session begins.

**QoS:** 1 (at least once)

**Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T12:30:05Z",
  "session_id": "local-session-uuid",
  "recipe_id": "recipe-uuid-001",
  "recipe_name": "Dal Tadka",
  "total_stages": 6,
  "estimated_time_minutes": 35,
  "customizations": {
    "spice_level": 4,
    "servings": 2
  }
}
```

### 4.3 `epicura/{device_id}/session/progress`

Published on stage transitions and significant events (every 5-10 seconds during cooking).

**QoS:** 0

**Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T12:38:00Z",
  "session_id": "local-session-uuid",
  "current_stage": 3,
  "stage_name": "Saute Onions",
  "total_stages": 6,
  "progress_pct": 42,
  "temperature": 148.5,
  "target_temperature": 150,
  "stir_active": true,
  "time_elapsed_s": 480,
  "cv_status": {
    "class": "golden_brown",
    "confidence": 0.72
  }
}
```

### 4.4 `epicura/{device_id}/session/completed`

Published when cooking finishes successfully.

**QoS:** 1

**Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T13:05:22Z",
  "session_id": "local-session-uuid",
  "recipe_name": "Dal Tadka",
  "total_duration_s": 2122,
  "stages_completed": 6,
  "peak_temperature": 182.5,
  "result": "success"
}
```

### 4.5 `epicura/{device_id}/session/error`

Published when a cooking error or abort occurs.

**QoS:** 1

**Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T12:40:00Z",
  "session_id": "local-session-uuid",
  "error_code": "OVER_TEMPERATURE",
  "message": "Temperature exceeded 260°C. E-stop activated.",
  "severity": "critical",
  "stage_at_error": "Saute Onions",
  "temperature_at_error": 262.3
}
```

---

### 4.6 `epicura/{device_id}/status`

Device health and connectivity status. Published on state changes and every 60 seconds as a heartbeat.

**QoS:** 1
**Retained:** Yes (broker stores last status for new subscribers)

**Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T12:28:00Z",
  "status": "online",
  "firmware_rv1106": "1.2.0",
  "firmware_stm32": "1.1.0",
  "uptime_s": 86400,
  "wifi_rssi": -42,
  "lan_ip": "192.168.1.42",
  "free_memory_mb": 168,
  "disk_usage_pct": 34,
  "cpu_temp": 52.3
}
```

### 4.7 `epicura/{device_id}/alert`

Device alerts that require backend processing or user notification.

**QoS:** 1

**Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T12:29:00Z",
  "alert_type": "sensor_degraded",
  "severity": "warning",
  "message": "IR thermometer readings unstable — using CAN coil temp fallback",
  "details": {
    "sensor": "MLX90614",
    "error_count": 5,
    "last_valid_reading": 145.2
  }
}
```

---

## 5. Device Commands (Cloud → RV1106)

`epicurad` subscribes to the single topic `epicura/{device_id}/cmd`. Every message carries a `command` field that selects the action, plus `command_id` and `timestamp`. All commands use **QoS 1**; the broker holds commands for a disconnected device until it reconnects (persistent session).

| `command` | Purpose | Device action |
|-----------|---------|---------------|
| `live_view_start` | Phone requested live pot view | Bind VENC H.264 1280x720 @ 15 fps, spawn `rtsp-stream` (RTSP `:554/pot`, single client) |
| `live_view_stop` | Viewer closed live view | Kill `rtsp-stream`, unbind VENC, free buffers (also automatic after 60 s with no client) |
| `recipe_sync_now` | Trigger recipe sync | `GET /recipes/sync?since=` → SQLite upsert |
| `ota_check` | Check for firmware update | `GET /firmware/latest`, download and verify signed `.swu` (swupdate A/B) or STM32 `.bin` |
| `cook` | Start cooking remotely | Start session; publishes `session/started` or `session/error` |
| `stop` | Emergency stop | E_STOP to STM32 over the UART bridge |
| `config` | Push configuration | Apply runtime settings |

### 5.1 `live_view_start`

Published by the backend when a mobile app requests the live pot view.

**Payload:**
```json
{
  "command": "live_view_start",
  "command_id": "cmd-uuid-006",
  "initiated_by": "user-uuid-001",
  "idle_timeout_s": 60,
  "timestamp": "2026-02-14T12:32:00Z"
}
```

**Device response:** None on MQTT. The stream becomes available at `rtsp://<lan_ip>:554/pot` (1280x720 H.264, 15 fps, 1.5 Mbps, one viewer). Same-LAN apps connect directly; otherwise the cloud relay pulls the stream. Ignored while a stream is already running.

### 5.2 `live_view_stop`

**Payload:**
```json
{
  "command": "live_view_stop",
  "command_id": "cmd-uuid-007",
  "timestamp": "2026-02-14T12:40:00Z"
}
```

### 5.3 `recipe_sync_now`

Trigger the device to sync recipes from the cloud API.

**Payload:**
```json
{
  "command": "recipe_sync_now",
  "command_id": "cmd-uuid-004",
  "timestamp": "2026-02-14T14:05:00Z"
}
```

### 5.4 `ota_check`

Trigger a firmware update check. The device fetches `GET /firmware/latest` itself; the payload carries no binary URL.

**Payload:**
```json
{
  "command": "ota_check",
  "command_id": "cmd-uuid-003",
  "target": "rv1106",
  "channel": "stable",
  "timestamp": "2026-02-14T14:00:00Z"
}
```

`target` is `rv1106`, `stm32` or `all`. For `rv1106` the device downloads the signed `.swu` to `/data/ota`, verifies it, and swupdate writes the inactive A/B slot; for `stm32` the device streams the `.bin` to the STM32 system bootloader over the bridge UART.

### 5.5 `cook`

Remotely start cooking a recipe (initiated from mobile app via backend).

**Payload:**
```json
{
  "command": "cook",
  "command_id": "cmd-uuid-001",
  "recipe_id": "recipe-uuid-001",
  "customizations": {
    "spice_level": 4,
    "servings": 2
  },
  "initiated_by": "user-uuid-001",
  "timestamp": "2026-02-14T12:30:00Z"
}
```

**Device Response:** Publishes to `epicura/{device_id}/session/started` on success, or `epicura/{device_id}/session/error` on failure.

### 5.6 `stop`

Emergency stop command.

**Payload:**
```json
{
  "command": "stop",
  "command_id": "cmd-uuid-002",
  "reason": "user_requested",
  "initiated_by": "user-uuid-001",
  "timestamp": "2026-02-14T12:40:00Z"
}
```

### 5.7 `config`

Push configuration updates to the device.

**Payload:**
```json
{
  "command": "config",
  "command_id": "cmd-uuid-005",
  "config": {
    "telemetry_interval_s": 5,
    "cv_confidence_threshold": 0.65,
    "mqtt_keepalive_s": 30
  },
  "timestamp": "2026-02-14T14:10:00Z"
}
```

---

## 6. Retained Messages

| Topic | Retained | Reason |
|-------|----------|--------|
| `status` | Yes | New subscribers see current device state immediately |
| `telemetry` | No | High-frequency, no need for last value on connect |
| `session/*` | No | Session-specific, relevant only during active cooking |
| `alert` | No | Alerts are event-driven, processed once |
| `cmd` | No | Commands are one-time actions |

---

## 7. Last Will and Testament (LWT)

Each device registers an LWT message on MQTT connect. If the device disconnects unexpectedly (without a clean DISCONNECT), the broker publishes the LWT:

**LWT Topic:** `epicura/{device_id}/status`
**LWT Payload:**
```json
{
  "device_id": "EPIC-001",
  "timestamp": "2026-02-14T12:00:00Z",
  "status": "offline",
  "reason": "unexpected_disconnect"
}
```
**LWT QoS:** 1
**LWT Retained:** Yes

---

## 8. TLS Security

### 8.1 Development (Mosquitto)

- TLS optional for local development
- Username/password authentication: `epicura_dev` / configured password
- ACL: devices can only publish/subscribe to their own `epicura/{device_id}/` subtree

### 8.2 Production (AWS IoT Core)

- Mutual TLS with X.509 device certificates
- Each device provisioned with unique certificate + private key during manufacturing
- IoT Policy restricts each device to its own topic namespace:

```json
{
  "Effect": "Allow",
  "Action": ["iot:Publish", "iot:Subscribe", "iot:Receive"],
  "Resource": "arn:aws:iot:*:*:topic/epicura/${iot:ClientId}/*"
}
```

---

## 9. Backend Subscription and Bridging

The API server subscribes to device topics and processes messages:

```
┌─────────────────────────────────────────────────────────┐
│                   API Server MQTT Handler                 │
│                                                           │
│  Subscribe: epicura/+/telemetry                          │
│  Subscribe: epicura/+/session/#                          │
│  Subscribe: epicura/+/status                             │
│  Subscribe: epicura/+/alert                              │
│                                                           │
│  On message:                                              │
│  ├── telemetry  → Store in telemetry_events (Postgres)   │
│  ├── session/*  → Update cooking_sessions, notify WS     │
│  ├── status     → Update appliances.status + last_seen   │
│  └── alert      → Log, evaluate push notification rules  │
│                                                           │
│  Publish: epicura/{device_id}/cmd  (`command` field)     │
│  ├── live_view_start/stop → phone RTSP live view         │
│  ├── recipe_sync_now → Trigger recipe download           │
│  ├── ota_check  → Trigger firmware update check          │
│  ├── cook / stop → Remote cook / emergency stop          │
│  └── config     → Push configuration changes             │
└─────────────────────────────────────────────────────────┘
```

The wildcard `+` in subscriptions matches any device ID, so the server handles all devices on a single subscription set.

---

## 10. Related Documentation

- [[01-REST-API-Reference|REST API Reference]] - HTTP endpoints
- [[02-WebSocket-Events|WebSocket Events]] - Mobile app real-time events (bridged from MQTT)
- [[04-BLE-Services|BLE Services]] - BLE pairing and WiFi provisioning
- [[01-Backend-Architecture|Backend Architecture]] - MQTT bridge architecture
- [[02-Controller-Software-Architecture|Controller & Software Architecture]] - RV1106 MQTT client and telemetry format

#epicura #mqtt #telemetry #iot #api #protocol

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Device changed from CM5 to RV1106: single `cmd` topic with `command` field (`live_view_start`, `live_view_stop`, `recipe_sync_now`, `ota_check`, plus `cook`/`stop`/`config`); telemetry QoS 1 with `sync_outbox` offline spool; no on-device broker; status payload `firmware_rv1106`, `lan_ip` |
