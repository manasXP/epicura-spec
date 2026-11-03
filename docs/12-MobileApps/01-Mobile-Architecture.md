---
created: 2026-02-15
modified: 2026-11-04
version: 1.1
status: Draft
---

# Mobile Architecture

## 1. Native vs Cross-Platform Decision

Epicura uses native mobile development (Swift/SwiftUI for iOS, Kotlin/Jetpack Compose for Android) instead of the originally considered Flutter approach.

| Criteria | Native (Swift + Kotlin) | Flutter | Decision Factor |
|----------|------------------------|---------|-----------------|
| **BLE Performance** | Direct platform APIs (Core Bluetooth, CompanionDeviceManager) | Plugin-based (`flutter_blue_plus`), limited control | BLE pairing and WiFi provisioning are critical setup flow |
| **Camera Streaming** | Native RTSP/H.264 playback (MobileVLCKit / Media3 ExoPlayer) | Plugin-based, frame decoding overhead | Live cooking camera feed requires low-latency rendering |
| **Platform Feel** | 100% native UI, gestures, animations | Custom Skia rendering, approximates native | Indian users expect platform-consistent experience |
| **Background Processing** | Full OS-level support (BGTasks, WorkManager) | Limited plugin support | Cooking notifications must arrive reliably in background |
| **Push Notifications** | Native APNs/FCM integration | Plugin-based | Critical for cooking alerts |
| **App Size** | ~15-25 MB per platform | ~25-40 MB (Dart runtime + Skia engine) | Smaller app size preferred for Indian market (data constraints) |
| **Maintenance** | Two codebases, platform expertise needed | Single codebase, Dart expertise | Acceptable trade-off for better BLE and camera support |
| **Long-term** | Apple/Google invest directly in platform SDKs | Flutter updates may lag platform features | Guaranteed compatibility with new OS versions |

**Decision:** Native development provides superior BLE integration, camera streaming performance, and platform-native user experience — all critical for Epicura's core flows.

---

## 2. MVVM Architecture

Both iOS and Android apps use the MVVM (Model-View-ViewModel) pattern with a shared architectural philosophy:

```
┌───────────────────────────────────────────────────────────────────┐
│                        Mobile App                                 │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                      View Layer                            │   │
│  │  SwiftUI Views (iOS) / Composable Functions (Android)      │   │
│  │  Observes ViewModel state, dispatches user actions         │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                               │                                   │
│  ┌────────────────────────────▼───────────────────────────────┐   │
│  │                    ViewModel Layer                         │   │
│  │  Holds UI state, processes user actions                    │   │
│  │  Transforms data models into display models                │   │
│  │  iOS: @Observable classes + Combine                        │   │
│  │  Android: ViewModel + StateFlow + Kotlin coroutines        │   │
│  └────────────────────────────┬───────────────────────────────┘   │
│                               │                                   │
│  ┌────────────────────────────▼───────────────────────────────┐   │
│  │                    Repository Layer                        │   │
│  │  Coordinates data sources, caching strategy                │   │
│  │  Single source of truth for each data type                 │   │
│  └──────────┬───────────────────────────┬─────────────────────┘   │
│             │                           │                         │
│  ┌──────────▼──────────┐    ┌───────────▼────────────┐            │
│  │   Remote Sources    │    │    Local Sources       │            │
│  │  ┌───────────────┐  │    │  ┌─────────────────┐   │            │
│  │  │ API Client    │  │    │  │ SwiftData/Room  │   │            │
│  │  │ (REST + JWT)  │  │    │  │ (local cache)   │   │            │
│  │  ├───────────────┤  │    │  ├─────────────────┤   │            │
│  │  │ WebSocket     │  │    │  │ Keychain /      │   │            │
│  │  │ (real-time)   │  │    │  │ DataStore       │   │            │
│  │  ├───────────────┤  │    │  │ (secure store)  │   │            │
│  │  │ BLE Manager   │  │    │  └─────────────────┘   │            │
│  │  │ (pairing)     │  │    │                        │            │
│  │  └───────────────┘  │    └────────────────────────┘            │
│  └─────────────────────┘                                          │
└───────────────────────────────────────────────────────────────────┘
```

---

## 3. Feature Priority Matrix

| Priority | Feature | iOS | Android |
|----------|---------|-----|---------|
| **P0** | BLE pairing + WiFi provisioning | Core Bluetooth | CompanionDeviceManager |
| **P0** | User auth (phone+OTP primary, email fallback) | URLSession | Retrofit/OkHttp |
| **P0** | Recipe browsing + detail view | SwiftUI List/Grid | LazyColumn/LazyGrid |
| **P0** | Live cooking progress (WebSocket) | URLSessionWebSocketTask | OkHttp WebSocket |
| **P0** | Push notifications | APNs | FCM |
| **P1** | Live pot view (RTSP H.264, on demand) | MobileVLCKit | Media3 ExoPlayer (RTSP) |
| **P1** | Cooking history + ratings | SwiftData | Room |
| **P1** | Food preferences (diet, cuisines, seasoning levels, servings) + allergen profile | SwiftData | DataStore + Room |
| **P1** | Offline recipe cache | SwiftData | Room |
| **P1** | Appliance management (rename, status) | REST API | REST API |
| **P2** | Recipe search (full-text) | REST API | REST API |
| **P2** | Grocery list generation | Computed from recipes | Computed from recipes |
| **P2** | Meal planning / scheduling | REST API + local | REST API + local |
| **P2** | Dark mode | System setting | Material 3 dynamic |
| **P2** | Multi-language (Hindi, Tamil, etc.) | String Catalogs | string resources |

---

## 4. Networking Layer

### 4.1 API Client

Both platforms implement a type-safe API client wrapping the [[01-REST-API-Reference|REST API]]:

```
┌─────────────────────────────────────────────────────┐
│                  API Client                         │
│                                                     │
│  Base URL: https://api.epicura.io/api/v1            │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Request Pipeline:                           │   │
│  │  1. Build request (URL, method, body)        │   │
│  │  2. Attach JWT access token                  │   │
│  │  3. Send request                             │   │
│  │  4. If 401 → refresh token → retry           │   │
│  │  5. Decode response (JSON → model)           │   │
│  │  6. Return Result<T, APIError>               │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Token Management:                            │  │
│  │  - Store access + refresh tokens securely     │  │
│  │  - Auto-refresh on 401 response               │  │
│  │  - Refresh token rotation                     │  │
│  │  - Queue concurrent requests during refresh   │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 4.2 WebSocket Client

Real-time cooking updates via WebSocket (see [[02-WebSocket-Events|WebSocket Events]]):

```
┌─────────────────────────────────────────────────────┐
│              WebSocket Manager                      │
│                                                     │
│  States:                                            │
│  ┌──────────┐  connect  ┌────────────┐              │
│  │Disconnect│──────────►│ Connecting │              │
│  │   ed     │           └─────┬──────┘              │
│  └────▲─────┘                 │                     │
│       │              success  │  failure            │
│       │           ┌───────────┘  │                  │
│       │           ▼              ▼                  │
│       │    ┌────────────┐  ┌──────────┐             │
│       │    │ Connected  │  │ Retrying │             │
│       │    │            │  │ (backoff)│             │
│       │    └─────┬──────┘  └────┬─────┘             │
│       │          │              │                   │
│       │     disconnect    retry │                   │
│       └──────────┘              │                   │
│       └─────────────────────────┘                   │
│                                                     │
│  Features:                                          │
│  - Auto-reconnect with exponential backoff          │
│  - Re-subscribe to appliances on reconnect          │
│  - Ping/pong heartbeat (30s interval)               │
│  - Parse events → dispatch to ViewModel observers   │
└─────────────────────────────────────────────────────┘
```

### 4.3 BLE Manager

BLE state machine for device pairing (see [[04-BLE-Services|BLE Services]]):

```
┌─────────────────────────────────────────────────────┐
│                BLE Manager                          │
│                                                     │
│  ┌──────┐  scan   ┌──────────┐  found  ┌────────┐   │
│  │ Idle │────────►│ Scanning │────────►│Connect-│   │
│  │      │         │          │         │  ing   │   │
│  └──▲───┘         └──────────┘         └────┬───┘   │
│     │                                       │       │
│     │              ┌─────────┐    connected │       │
│     │  disconnect  │Discover-│◄─────────────┘       │
│     │◄─────────────│  ing    │                      │
│     │              │Services │                      │
│     │              └────┬────┘                      │
│     │                   │ services discovered       │
│     │              ┌────▼────┐                      │
│     │              │ Ready   │                      │
│     │              │ (read/  │                      │
│     │              │  write) │                      │
│     │              └────┬────┘                      │
│     │                   │ provisioning complete     │
│     │              ┌────▼────┐                      │
│     └──────────────│  Done   │                      │
│                    └─────────┘                      │
└─────────────────────────────────────────────────────┘
```

---

## 5. Live Pot View (RTSP)

The device does not serve MJPEG or any HTTP/WebSocket video. Live view is **on demand only**: the app asks the cloud, the cloud publishes the MQTT `live_view_start` command, and the device spawns its `rtsp-stream` process (H.264 1280x720, 15 fps, 1.5 Mbps, single viewer). The stream is torn down after 60 s with no client or on `live_view_stop`.

```
App ──(cloud API)──► Cloud ──(MQTT live_view_start)──► Device
App ◄──(RTSP rtsp://<lan_ip>:554/pot, same LAN)────────┘
App ◄──(cloud relay URL, off-LAN)──── Cloud ◄──(RTSP)───┘
```

**Implementation Approach:**

| Platform | Method | Notes |
|----------|--------|-------|
| iOS | RTSP client (MobileVLCKit) → `UIViewRepresentable` in SwiftUI | AVPlayer has no RTSP support |
| Android | Media3 ExoPlayer with `RtspMediaSource` → `PlayerView` in Compose | Hardware H.264 decode via MediaCodec |

**Connection choice:** the app tries `rtsp://<lan_ip>:554/pot` directly when it is on the same Wi-Fi as the device (`lan_ip` comes from the appliance status reported to the cloud); otherwise it plays the relay URL returned by the cloud. The app sends the stop request when the view is dismissed so the device can free its encoder.

---

## 6. Offline Strategy

| Data | Cache Strategy | Sync Direction |
|------|---------------|----------------|
| **Recipes** | Cache all published recipes in local DB | Cloud → Device |
| **Cooking History** | Store locally, upload to cloud | Device → Cloud |
| **User Preferences** | Store locally (diet, cuisines, seasoning levels, servings, allergens), sync on change | Bidirectional |
| **Recipe Images** | Disk cache with LRU eviction | Cloud → Device |
| **Push Tokens** | Register/refresh on app launch | Device → Cloud |

**Offline Behavior:**

- User can browse cached recipes without internet
- Cannot start remote cooking (requires cloud relay)
- Cooking can still be started on the device's own 4" touchscreen (no direct app-to-device API)
- Cooking history queued for upload when connection restored
- Preference changes queued and synced on reconnect

---

## 7. Design System

### 7.1 Epicura Color Palette

| Color | Name | Hex | Usage |
|-------|------|-----|-------|
| Primary | Warm Orange | `#E65100` | CTAs, navigation highlights |
| Primary Variant | Deep Orange | `#BF360C` | Status bar, pressed states |
| Secondary | Forest Green | `#2E7D32` | Success states, positive indicators |
| Background | Cream White | `#FFF8E1` | Main background |
| Surface | White | `#FFFFFF` | Cards, sheets, dialogs |
| Text Primary | Dark Brown | `#3E2723` | Body text, headings |
| Text Secondary | Medium Brown | `#6D4C41` | Captions, labels |
| Emergency | Bright Red | `#D50000` | Emergency stop, critical errors |
| Success | Green | `#43A047` | Cooking complete, success states |
| Warning | Amber | `#FFB300` | Warnings, caution states |

This palette matches the LVGL touchscreen UI colors defined in [[01-UI-UX-Design#Styling|UI/UX Design - Styling]].

### 7.2 Platform-Native Patterns

| Pattern | iOS (SwiftUI) | Android (Compose) |
|---------|--------------|-------------------|
| Navigation | `NavigationStack` + `NavigationLink` | `NavHost` + `NavController` |
| Tab Bar | `TabView` (Recipe, Favourite, Session, Profile) | `NavigationBar` (Material 3) (Recipe, Favourite, Session, Profile) |
| Pull to Refresh | `.refreshable` modifier | `PullToRefreshBox` |
| Haptics | `UIImpactFeedbackGenerator` | `HapticFeedback` compose |
| System Theme | `@Environment(\.colorScheme)` | `isSystemInDarkTheme()` |
| Typography | SF Pro (system) | Roboto / Material 3 type scale |

### 7.3 Recipe Card Layout

Recipe cards in the list use a horizontal layout:
- **Left:** Food image in a bowl (square thumbnail, rounded corners)
- **Right:** Recipe name, cooking time, difficulty badge
- **Bottom-right:** Nutrition per serving — Protein (g), Carbs (g), Fats (g), Calories (kcal)

### 7.4 Recipe List Filters

| Filter Layer | Options |
|-------------|---------|
| **Tag filters** (horizontally scrollable chips) | All Recipes, Vegan, Healthy, Vegetarian, Protein Rich, Stir Fry, Gluten Free, Quick Recipe |
| **Cuisine filters** (horizontally scrollable chips) | Indian, Italian, American, Chinese, Mexican, Korean, Thai, Asian, Global |

---

## 8. Related Documentation

- [[02-iOS-App|iOS App]] - SwiftUI implementation details
- [[03-Android-App|Android App]] - Jetpack Compose implementation details
- [[01-REST-API-Reference|REST API Reference]] - Backend endpoints
- [[02-WebSocket-Events|WebSocket Events]] - Real-time event protocol
- [[04-BLE-Services|BLE Services]] - BLE pairing services
- [[01-UI-UX-Design|UI/UX Design]] - Design language and color palette
- [[01-Tech-Stack|Tech Stack]] - Overall technology choices

#epicura #mobile #architecture #mvvm #ios #android #swift #kotlin #native-mobile

---

## 9. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Manas Pradhan | Initial document creation |
| 1.1 | 2026-11-04 | Manas Pradhan | Device changed from CM5 to RV1106: live view is on-demand RTSP (LAN) or cloud relay, MJPEG removed; no direct app-to-device API; touchscreen UI is LVGL |
