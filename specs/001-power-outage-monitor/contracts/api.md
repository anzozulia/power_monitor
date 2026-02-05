# API Contracts: Power Outage Monitor

**Branch**: `001-power-outage-monitor`  
**Date**: 2026-02-04

## Overview

The system exposes two API surfaces:
1. **Admin Panel** - Django views for authenticated admin user
2. **Heartbeat API** - Lightweight endpoint for ESP32 devices

## Authentication

### Admin Panel
- Session-based authentication via Django auth
- Login at `/login/`
- All `/admin/*` routes require authentication

### Heartbeat API
- API key authentication via `X-API-Key` header
- Each location has a unique auto-generated API key
- No session/cookies required

---

## Admin Panel Routes

### Authentication

#### POST /login/
Login to admin panel.

**Request**:
```
Content-Type: application/x-www-form-urlencoded

username=admin&password=secret123
```

**Response (success)**: Redirect to `/admin/locations/`

**Response (failure)**: Re-render login page with error message

---

#### POST /logout/
Logout from admin panel.

**Response**: Redirect to `/login/`

---

### Dashboard

#### GET /admin/
Dashboard redirect.

**Response**: Redirect to `/admin/locations/`

---

### Locations

#### GET /admin/locations/
List all locations with current power status.

**Response**: HTML page with locations table

**Data displayed per location**:
- Name
- Power status (ON/OFF/Not Started) with colored indicator
- Last heartbeat time (relative, e.g., "2 minutes ago")
- Actions: Edit, Delete, View Config

---

#### GET /admin/locations/new/
Form to create new location.

**Response**: HTML form with fields:
- Name (text)
- Heartbeat period (number, seconds, default 60)
- Grace period (number, seconds, default 30)
- Telegram bot token (text)
- Telegram chat ID (text)

---

#### POST /admin/locations/
Create new location.

**Request**:
```
Content-Type: application/x-www-form-urlencoded

name=Home+Kyiv
&heartbeat_period_seconds=60
&grace_period_seconds=30
&telegram_bot_token=123456:ABC-DEF...
&telegram_chat_id=-1001234567890
```

**Response (success)**: Redirect to `/admin/locations/{id}/config/`

**Response (validation error)**: Re-render form with errors

---

#### GET /admin/locations/{id}/
View location details.

**Response**: HTML page with:
- Location configuration
- Current power status
- Recent power events (last 10)
- Link to ESP32 configuration

---

#### GET /admin/locations/{id}/edit/
Form to edit location.

**Response**: HTML form (same fields as create)

---

#### POST /admin/locations/{id}/
Update location.

**Request**: Same as create

**Response (success)**: Redirect to `/admin/locations/`

**Response (validation error)**: Re-render form with errors

---

#### POST /admin/locations/{id}/delete/
Delete location.

**Request**: CSRF token only

**Response**: Redirect to `/admin/locations/`

---

#### GET /admin/locations/{id}/config/
Display ESP32 configuration details.

**Response**: HTML page with:
- Heartbeat endpoint URL
- API key (with copy button)
- Example ESP32 code snippet

**Example displayed content**:
```
Endpoint: https://your-domain.com/api/heartbeat/
API Key: abc123def456...
Location ID: (included in API key, not needed separately)

Example ESP32 code:
  http.begin("https://your-domain.com/api/heartbeat/");
  http.addHeader("X-API-Key", "abc123def456...");
  http.POST("");
```

---

## Heartbeat API

### POST /api/heartbeat/
Receive heartbeat from ESP32 device.

**Request Headers**:
```
X-API-Key: {location_api_key}
```

**Request Body**: Empty (no payload required)

**Response (success)**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok",
  "received_at": "2026-02-04T12:34:56Z"
}
```

**Response (invalid API key)**:
```json
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": "invalid_api_key"
}
```

**Response (rate limited - duplicate within 5 seconds)**:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "duplicate_ignored",
  "received_at": "2026-02-04T12:34:51Z"
}
```

**Notes**:
- Minimal response to reduce bandwidth
- ESP32 should retry on network failure
- No body parsing required (empty POST)

---

## Internal Endpoints (Background Tasks)

These are not HTTP endpoints but document the background task contracts.

### check_heartbeats
**Frequency**: Every 10 seconds  
**Logic**:
1. Query all locations where `monitoring_started_at IS NOT NULL`
2. For each location: check if `now - last_heartbeat_at > heartbeat_period + grace_period`
3. If timeout and `current_power_status = 'on'`: trigger power_off event
4. Create PowerEvent record
5. Trigger send_alert task

### send_alert
**Triggered by**: Power status change  
**Input**: location_id, event_type, duration_seconds  
**Logic**:
1. Load location
2. Format alert message with emoji and styling
3. Call Telegram API `sendMessage`
4. Update PowerEvent.alert_sent = true
5. On failure: log error, set location.alerting_failed = true

### update_hourly_diagram
**Frequency**: Every hour at :00  
**Logic**:
1. For each location with `monitoring_started_at IS NOT NULL`
2. Generate diagram image for current week
3. If DiagramMessage exists for today: edit message with new image
4. Else: skip (will be created by daily job)

### generate_daily_diagram
**Frequency**: Daily at 00:00 Kyiv time  
**Logic**:
1. For each location with `monitoring_started_at IS NOT NULL`
2. Update yesterday's diagram one final time
3. Unpin yesterday's DiagramMessage
4. Generate new diagram image
5. Send new image to Telegram
6. Pin new message
7. Create DiagramMessage record

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| invalid_api_key | 401 | API key not found or invalid |
| rate_limited | 429 | Too many requests (Telegram) |
| telegram_error | 502 | Telegram API failure |
| validation_error | 400 | Invalid form input |
