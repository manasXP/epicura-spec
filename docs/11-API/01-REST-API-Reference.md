---
created: 2026-02-15
modified: 2026-11-04
version: 1.2
status: Draft
---

# REST API Reference

## 1. Base URL

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:3000/api/v1` |
| Production | `https://api.epicura.io/api/v1` |

---

## 2. Authentication

All endpoints except `/auth/register`, `/auth/login`, `/auth/otp/request`, and `/auth/otp/verify` require a valid JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via the login flow. See [[01-Backend-Architecture#JWT Authentication Flow|JWT Authentication Flow]] for details.

---

## 3. Common Response Format

### 3.1 Success

```json
{
  "success": true,
  "data": { ... }
}
```

### 3.2 Paginated

```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 142,
    "total_pages": 8
  }
}
```

### 3.3 Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {"field": "email", "message": "Must be a valid email address"}
    ]
  }
}
```

---

## 4. Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request body/params failed validation |
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `TOKEN_EXPIRED` | 401 | Access token has expired |
| `TOKEN_INVALID` | 401 | Malformed or revoked token |
| `FORBIDDEN` | 403 | Insufficient permissions (e.g., non-admin) |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Duplicate resource (e.g., email already registered) |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## 5. Rate Limits

| Scope | Limit | Window |
|-------|-------|--------|
| Authentication endpoints | 10 requests | 1 minute |
| General API | 100 requests | 1 minute |
| Recipe sync (device) | 30 requests | 1 minute |
| Telemetry ingestion | 600 requests | 1 minute |

---

## 6. Endpoints

### 6.1 Auth

#### 6.1.1 `POST /auth/register`

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "Manas Pradhan"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "Manas Pradhan",
      "role": "user"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

```bash
curl -X POST https://api.epicura.io/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securePassword123","name":"Manas Pradhan"}'
```

#### 6.1.2 `POST /auth/login`

Authenticate and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "Manas Pradhan",
      "role": "user"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

```bash
curl -X POST https://api.epicura.io/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securePassword123"}'
```

#### 6.1.3 `POST /auth/otp/request`

Request a one-time password sent via SMS to the user's phone number. This is the **primary authentication method** for mobile apps. Register-on-first-login: if the phone number is not yet registered, a new account is created on successful OTP verification.

**Request:**
```json
{
  "phone": "+919876543210"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "OTP sent successfully",
    "expires_in_seconds": 300,
    "retry_after_seconds": 30
  }
}
```

**Errors:**
- `VALIDATION_ERROR` (400) — Invalid phone number format
- `RATE_LIMITED` (429) — Too many OTP requests (max 5 per phone per hour)

```bash
curl -X POST https://api.epicura.io/api/v1/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"phone":"+919876543210"}'
```

#### 6.1.4 `POST /auth/otp/verify`

Verify an OTP and receive JWT tokens. If the phone number is new, a user account is created automatically (register-on-first-login).

**Request:**
```json
{
  "phone": "+919876543210",
  "otp": "123456"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "phone": "+919876543210",
      "name": null,
      "role": "user",
      "is_new_user": true
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Errors:**
- `INVALID_CREDENTIALS` (401) — Wrong or expired OTP
- `RATE_LIMITED` (429) — Too many failed attempts (max 5 per OTP)

```bash
curl -X POST https://api.epicura.io/api/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"phone":"+919876543210","otp":"123456"}'
```

#### 6.1.5 `POST /auth/refresh`

Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

#### 6.1.6 `POST /auth/logout`

Revoke the current refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": { "message": "Logged out successfully" }
}
```

---

### 6.2 Recipes

#### 6.2.1 `GET /recipes`

List published recipes with optional filtering.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page (max 50) |
| `category` | string | — | Filter by category (`dal`, `curry`, `rice`, etc.) |
| `cuisine` | string | — | Filter by cuisine: `indian`, `italian`, `american`, `chinese`, `mexican`, `korean`, `thai`, `asian`, `global` |
| `difficulty` | string | — | Filter by difficulty (`easy`, `medium`, `hard`) |
| `tags` | string | — | Comma-separated tag filter: `vegan`, `healthy`, `vegetarian`, `protein-rich`, `stir-fry`, `gluten-free`, `quick`. Use `all` or omit for no filter |
| `search` | string | — | Full-text search query |
| `sort` | string | `name` | Sort field (`name`, `time_minutes`, `created_at`) |
| `order` | string | `asc` | Sort order (`asc`, `desc`) |

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "recipe-uuid-001",
      "name": "Dal Tadka",
      "category": "dal",
      "cuisine": "indian",
      "difficulty": "easy",
      "time_minutes": 35,
      "servings": 4,
      "tags": ["vegetarian", "protein-rich"],
      "nutrition": {
        "calories": 320,
        "protein_g": 18,
        "carbs_g": 42,
        "fats_g": 8
      },
      "image_url": "https://cdn.epicura.io/recipes/dal-tadka.jpg",
      "version": 2
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 142,
    "total_pages": 8
  }
}
```

```bash
curl https://api.epicura.io/api/v1/recipes?category=dal&difficulty=easy \
  -H "Authorization: Bearer <token>"
```

#### 6.2.2 `GET /recipes/:id`

Get full recipe details including `recipe_data` (stages, ingredients).

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "recipe-uuid-001",
    "name": "Dal Tadka",
    "category": "dal",
    "cuisine": "indian",
    "difficulty": "easy",
    "time_minutes": 35,
    "servings": 4,
    "tags": ["vegetarian", "protein-rich"],
    "nutrition": {
      "calories": 320,
      "protein_g": 18,
      "carbs_g": 42,
      "fats_g": 8
    },
    "image_url": "https://cdn.epicura.io/recipes/dal-tadka.jpg",
    "version": 2,
    "recipe_data": {
      "name": "Dal Tadka",
      "servings": 4,
      "total_time_minutes": 35,
      "stages": [
        {
          "name": "Heat Oil",
          "temp_target": 180,
          "duration_seconds": 120,
          "stir": false,
          "ingredients": [{"subsystem": "SLD", "channel": "OIL", "name": "oil", "amount_g": 30}],
          "cv_check": "oil_shimmer"
        }
      ]
    },
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-02-10T14:22:00Z"
  }
}
```

#### 6.2.3 `POST /recipes` (Admin only)

Create a new recipe.

**Request:**
```json
{
  "name": "Paneer Butter Masala",
  "category": "curry",
  "cuisine": "indian",
  "difficulty": "medium",
  "time_minutes": 45,
  "servings": 4,
  "tags": ["vegetarian", "protein-rich"],
  "nutrition": {
    "calories": 420,
    "protein_g": 22,
    "carbs_g": 28,
    "fats_g": 24
  },
  "recipe_data": {
    "stages": [ ... ]
  }
}
```

**Response (201):** Returns created recipe.

#### 6.2.4 `PUT /recipes/:id` (Admin only)

Update an existing recipe. Increments `version` automatically.

#### 6.2.5 `DELETE /recipes/:id` (Admin only)

Soft-delete a recipe (sets `is_published = false`).

#### 6.2.6 `GET /recipes/sync`

Device recipe sync endpoint, called by `epicurad` daily and on the `recipe_sync_now` MQTT command. Returns recipes updated since a given timestamp; the device upserts them into its SQLite mirror.

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `since` | ISO 8601 | Yes | Return recipes updated after this timestamp |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "recipes": [
      {
        "id": "recipe-uuid-003",
        "name": "Jeera Rice",
        "recipe_data": { ... },
        "version": 3,
        "updated_at": "2026-02-14T08:00:00Z"
      }
    ],
    "deleted_ids": ["recipe-uuid-old-1"],
    "server_timestamp": "2026-02-14T12:00:00Z"
  }
}
```

```bash
curl "https://api.epicura.io/api/v1/recipes/sync?since=2026-02-01T00:00:00Z" \
  -H "Authorization: Bearer <token>"
```

---

### 6.3 Appliances

#### 6.3.1 `POST /appliances/register`

Register a new appliance (called by the device on first boot).

**Request:**
```json
{
  "device_id": "EPIC-001",
  "serial_number": "SN2026020001",
  "firmware_version_rv1106": "1.0.0",
  "firmware_version_stm32": "1.0.0",
  "wifi_mac": "AA:BB:CC:DD:EE:FF"
}
```

**Response (201):** Returns appliance record.

#### 6.3.2 `POST /appliances/pair`

Pair an appliance with a user account using a pairing code obtained via BLE (see [[04-BLE-Services|BLE Services]]).

**Request:**
```json
{
  "pairing_code": "482917"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "appliance": {
      "id": "appliance-uuid-001",
      "device_id": "EPIC-001",
      "name": "My Epicura",
      "status": "online"
    }
  }
}
```

#### 6.3.3 `GET /appliances`

List user's paired appliances.

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "appliance-uuid-001",
      "device_id": "EPIC-001",
      "name": "Kitchen Epicura",
      "status": "online",
      "firmware_version_rv1106": "1.2.0",
      "firmware_version_stm32": "1.1.0",
      "last_seen_at": "2026-02-14T12:28:00Z"
    }
  ]
}
```

#### 6.3.4 `GET /appliances/:id`

Get appliance details.

#### 6.3.5 `PUT /appliances/:id`

Update appliance (e.g., rename).

**Request:**
```json
{
  "name": "Kitchen Epicura"
}
```

---

#### 6.3.6 `POST /appliances/:id/live-view`

Request the on-demand live pot view. The backend publishes the MQTT `live_view_start` command to the device (see [[03-MQTT-Topics|MQTT Topics]] §5.1) and returns the stream location. The device encodes 1280x720 H.264 at 15 fps and serves one RTSP client; the stream tears itself down after `idle_timeout_s` with no viewer.

**Request:**
```json
{
  "prefer": "lan"
}
```

`prefer` is `lan` (default) or `relay`. With `lan`, the response carries the device's last reported `lan_ip`; the app should fall back to `relay` if the RTSP connection fails within 5 s (different network, AP isolation).

**Response (200):**
```json
{
  "success": true,
  "data": {
    "mode": "lan",
    "url": "rtsp://192.168.1.42:554/pot",
    "relay_url": "rtsps://relay.epicura.io/EPIC-001/pot?token=eyJ...",
    "idle_timeout_s": 60,
    "expires_at": "2026-02-14T12:42:00Z"
  }
}
```

`relay_url` is always included so the app can switch without a second request. `expires_at` is the relay token expiry (10 min, refreshed by calling again).

**Errors:** `409 Conflict` if another viewer holds the stream (single client), `503 Service Unavailable` if the appliance is offline or cooking in a state that forbids streaming (E_STOP).

#### 6.3.7 `DELETE /appliances/:id/live-view`

Stop the live view early. The backend publishes `live_view_stop`. Returns `204 No Content`. Not required: the device stops on its own after `idle_timeout_s`.

---

### 6.4 Cooking Sessions

#### 6.4.1 `POST /sessions`

Create a new cooking session (called by the device from its `sync_outbox` when cooking starts, or by the mobile app to upload synced logs).

**Request:**
```json
{
  "appliance_id": "appliance-uuid-001",
  "recipe_id": "recipe-uuid-001",
  "customizations": {
    "spice_level": 4,
    "servings": 2
  }
}
```

**Response (201):** Returns session record with `status: "started"`.

#### 6.4.2 `PUT /sessions/:id`

Update session status and data (called by the device during/after cooking; queued in `sync_outbox` while offline).

**Request (during cooking):**
```json
{
  "status": "cooking",
  "stages_log": [
    {"stage": "Heat Oil", "duration_s": 118, "result": "success", "cv_confidence": 0.87}
  ]
}
```

**Request (on completion):**
```json
{
  "status": "completed",
  "completed_at": "2026-02-14T13:05:22Z",
  "peak_temperature": 182.5,
  "total_duration_s": 2122,
  "stages_log": [ ... ]
}
```

#### 6.4.3 `GET /sessions`

List user's cooking sessions (history).

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page |
| `appliance_id` | uuid | — | Filter by appliance |
| `recipe_id` | uuid | — | Filter by recipe |
| `status` | string | — | Filter by status |

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "session-uuid-001",
      "recipe": {"id": "recipe-uuid-001", "name": "Dal Tadka"},
      "appliance": {"id": "appliance-uuid-001", "device_id": "EPIC-001"},
      "status": "completed",
      "started_at": "2026-02-14T12:30:00Z",
      "completed_at": "2026-02-14T13:05:22Z",
      "total_duration_s": 2122,
      "user_rating": 5,
      "notes": "Perfect consistency"
    }
  ],
  "pagination": { ... }
}
```

#### 6.4.4 `GET /sessions/:id`

Get full session details including stage log.

#### 6.4.5 `PUT /sessions/:id/rate`

Rate a completed cooking session.

**Request:**
```json
{
  "rating": 5,
  "notes": "Perfect consistency, great taste"
}
```

---

### 6.5 User Preferences

#### 6.5.1 `GET /users/me`

Get current user profile and preferences.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user-uuid-001",
      "email": "user@example.com",
      "name": "Manas Pradhan",
      "role": "user",
      "created_at": "2026-01-10T08:00:00Z"
    },
    "preferences": {
      "language": "en_IN",
      "spice_level": 3,
      "salt_level": 3,
      "oil_level": 3,
      "diet": "no_restrictions",
      "cuisines": ["indian", "italian", "thai", "mexican"],
      "default_servings": 2,
      "allergens": ["mustard"],
      "theme": "light",
      "notifications_enabled": true
    }
  }
}
```

#### 6.5.2 `PUT /users/me`

Update profile and preferences.

**Request:**
```json
{
  "name": "Manas P.",
  "preferences": {
    "spice_level": 4,
    "salt_level": 2,
    "oil_level": 3,
    "diet": "vegetarian",
    "cuisines": ["indian", "italian", "thai"],
    "default_servings": 2,
    "allergens": ["mustard", "nuts"],
    "language": "hi_IN"
  }
}
```

---

### 6.6 Push Notifications

#### 6.6.1 `POST /push/register`

Register a device push token.

**Request:**
```json
{
  "platform": "ios",
  "token": "fcm-or-apns-device-token-string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": { "message": "Push token registered" }
}
```

---

### 6.7 Firmware

#### 6.7.1 `GET /firmware/latest`

Check for firmware updates (called by the device daily and on the `ota_check` MQTT command).

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `target` | string | Yes | `rv1106` or `stm32` |
| `current_version` | string | Yes | Currently installed version |
| `channel` | string | No | `stable` (default), `beta`, `alpha` |

**Response (200) — Update available:**
```json
{
  "success": true,
  "data": {
    "update_available": true,
    "version": "1.2.1",
    "binary_url": "https://cdn.epicura.io/firmware/rv1106/1.2.1.swu",
    "checksum_sha256": "a1b2c3d4...",
    "file_size_bytes": 209715200,
    "is_mandatory": false,
    "release_notes": "Bug fixes and improved PID tuning"
  }
}
```

**Response (200) — No update:**
```json
{
  "success": true,
  "data": {
    "update_available": false
  }
}
```

```bash
curl "https://api.epicura.io/api/v1/firmware/latest?target=rv1106&current_version=1.2.0" \
  -H "Authorization: Bearer <token>"
```

---

## 7. Device as API Client

The Epicura device (RV1106, `epicurad`) hosts **no HTTP server**. It is a client of this cloud API (libcurl + mbedTLS) and of the cloud MQTT broker; mobile apps never connect to the device over HTTP. Outbound requests are queued in the device's `sync_outbox` table while offline and drained in order on reconnect.

| Endpoint | Called by device when | Notes |
|----------|----------------------|-------|
| `POST /appliances/register` | First boot | Reports `firmware_version_rv1106` / `firmware_version_stm32` |
| `GET /recipes/sync?since=` | Daily, and on MQTT `recipe_sync_now` | Upserted into SQLite in one transaction |
| `POST /sessions`, `PUT /sessions/:id` | Session start / progress / completion | From `sync_outbox` (`kind = session`) |
| `PUT /users/me` | Preferences changed on the touchscreen | From `sync_outbox` (`kind = preferences`) |
| `GET /firmware/latest?target=rv1106` | Daily, and on MQTT `ota_check` | Signed `.swu` applied by swupdate (A/B slots) |

Live video is not served over HTTP. The app calls `POST /appliances/:id/live-view` (§6.3.6); the backend relays it to the device as the MQTT `live_view_start` command (see [[03-MQTT-Topics|MQTT Topics]]) and returns the RTSP URL (`rtsp://<lan_ip>:554/pot` on the same LAN) plus a cloud relay URL.

---

## 8. Pagination

All list endpoints support cursor or offset pagination:

| Param | Type | Default | Max | Description |
|-------|------|---------|-----|-------------|
| `page` | integer | 1 | — | Page number (1-indexed) |
| `limit` | integer | 20 | 50 | Items per page |

---

## 9. Related Documentation

- [[01-Backend-Architecture|Backend Architecture]] - Server setup and deployment
- [[02-Database-Schema|Database Schema]] - Tables queried by these endpoints
- [[02-WebSocket-Events|WebSocket Events]] - Real-time cooking events
- [[03-MQTT-Topics|MQTT Topics]] - Device telemetry protocol
- [[04-BLE-Services|BLE Services]] - BLE pairing flow
- [[01-Mobile-Architecture|Mobile Architecture]] - Mobile app networking layer

#epicura #api #rest #endpoints #backend

---

## 10. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Device changed from CM5 to RV1106: removed device-hosted local API section; device is a REST client only; `firmware_version_cm5` → `firmware_version_rv1106`, firmware target `rv1106` with `.swu` binaries |
| 1.2 | 2026-11-04 | Manas Pradhan | Added POST/DELETE /appliances/:id/live-view (§6.3.6–6.3.7) for on-demand RTSP live view |
