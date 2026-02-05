# Data Model: Power Outage Monitor

**Branch**: `001-power-outage-monitor`  
**Date**: 2026-02-04

## Entity Relationship Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                              Location                                │
│─────────────────────────────────────────────────────────────────────│
│ PK: id (UUID)                                                        │
│ name (VARCHAR 100, unique)                                           │
│ heartbeat_period_seconds (INTEGER, default 60)                       │
│ grace_period_seconds (INTEGER, default 30)                           │
│ telegram_bot_token (VARCHAR 100, encrypted)                          │
│ telegram_chat_id (VARCHAR 50)                                        │
│ api_key (VARCHAR 64, unique, auto-generated)                         │
│ current_power_status (ENUM: 'unknown', 'on', 'off')                  │
│ monitoring_started_at (TIMESTAMP, nullable)                          │
│ last_heartbeat_at (TIMESTAMP, nullable)                              │
│ last_status_change_at (TIMESTAMP, nullable)                          │
│ alerting_enabled (BOOLEAN, default true)                             │
│ alerting_failed (BOOLEAN, default false)                             │
│ created_at (TIMESTAMP)                                               │
│ updated_at (TIMESTAMP)                                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                              Heartbeat                               │
│─────────────────────────────────────────────────────────────────────│
│ PK: id (BIGINT, auto-increment)                                      │
│ FK: location_id → Location.id                                        │
│ received_at (TIMESTAMP, indexed)                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                             PowerEvent                               │
│─────────────────────────────────────────────────────────────────────│
│ PK: id (BIGINT, auto-increment)                                      │
│ FK: location_id → Location.id                                        │
│ event_type (ENUM: 'power_on', 'power_off')                           │
│ occurred_at (TIMESTAMP, indexed)                                     │
│ previous_state_duration_seconds (INTEGER, nullable)                  │
│ alert_sent (BOOLEAN, default false)                                  │
│ alert_sent_at (TIMESTAMP, nullable)                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           DiagramMessage                             │
│─────────────────────────────────────────────────────────────────────│
│ PK: id (BIGINT, auto-increment)                                      │
│ FK: location_id → Location.id                                        │
│ telegram_message_id (BIGINT)                                         │
│ diagram_date (DATE, indexed)                                         │
│ is_pinned (BOOLEAN, default false)                                   │
│ last_updated_at (TIMESTAMP)                                          │
│ created_at (TIMESTAMP)                                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Entity Details

### Location

Represents a monitored property/house with its configuration.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| name | VARCHAR(100) | unique, not null | Human-readable location name |
| heartbeat_period_seconds | INTEGER | not null, default 60, min 10 | Expected interval between heartbeats |
| grace_period_seconds | INTEGER | not null, default 30, min 10 | Extra time before marking as offline |
| telegram_bot_token | VARCHAR(100) | not null, encrypted | Bot token for this location's alerts |
| telegram_chat_id | VARCHAR(50) | not null | Chat/channel ID for alerts |
| api_key | VARCHAR(64) | unique, not null, auto-generated | ESP32 authentication key |
| current_power_status | ENUM | not null, default 'unknown' | Current status: unknown, on, off |
| monitoring_started_at | TIMESTAMP | nullable | When first heartbeat was received |
| last_heartbeat_at | TIMESTAMP | nullable | Most recent heartbeat timestamp |
| last_status_change_at | TIMESTAMP | nullable | When status last changed |
| alerting_enabled | BOOLEAN | not null, default true | Whether to send Telegram alerts |
| alerting_failed | BOOLEAN | not null, default false | True if bot token is invalid |
| created_at | TIMESTAMP | not null, auto | Record creation time |
| updated_at | TIMESTAMP | not null, auto | Record update time |

**Validation Rules**:
- `heartbeat_period_seconds` must be >= 10
- `grace_period_seconds` must be >= 10
- `telegram_bot_token` format: `\d+:[A-Za-z0-9_-]+`
- `telegram_chat_id` can be negative (groups) or positive (users/channels)

**State Transitions**:
```text
[created] → unknown
unknown + first_heartbeat → on (monitoring_started_at set)
on + timeout → off
off + heartbeat → on
```

### Heartbeat

Records each heartbeat signal received from ESP32 devices.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, auto-increment | Unique identifier |
| location_id | UUID | FK → Location, indexed | Associated location |
| received_at | TIMESTAMP | not null, indexed | When heartbeat was received |

**Notes**:
- High-volume table; consider partitioning by date for long-term storage
- Index on (location_id, received_at DESC) for quick latest-heartbeat queries
- Duplicate heartbeats within 5 seconds are ignored (application logic)

### PowerEvent

Records power status changes for historical tracking and analytics.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, auto-increment | Unique identifier |
| location_id | UUID | FK → Location, indexed | Associated location |
| event_type | ENUM | not null | 'power_on' or 'power_off' |
| occurred_at | TIMESTAMP | not null, indexed | When the status changed |
| previous_state_duration_seconds | INTEGER | nullable | How long previous state lasted |
| alert_sent | BOOLEAN | not null, default false | Whether alert was dispatched |
| alert_sent_at | TIMESTAMP | nullable | When alert was sent |

**Notes**:
- Used for diagram generation (query events in date range)
- `previous_state_duration_seconds` enables "power was out for X hours" messages

### DiagramMessage

Tracks Telegram messages containing weekly diagrams for pin/unpin management.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGINT | PK, auto-increment | Unique identifier |
| location_id | UUID | FK → Location, indexed | Associated location |
| telegram_message_id | BIGINT | not null | Telegram's message ID |
| diagram_date | DATE | not null, indexed | Date the diagram represents |
| is_pinned | BOOLEAN | not null, default false | Whether currently pinned |
| last_updated_at | TIMESTAMP | not null | Last hourly update time |
| created_at | TIMESTAMP | not null, auto | When message was first sent |

**Notes**:
- Unique constraint on (location_id, diagram_date)
- Only one diagram per location per day

## Indexes

```sql
-- Location lookups
CREATE INDEX idx_location_api_key ON location(api_key);

-- Heartbeat queries
CREATE INDEX idx_heartbeat_location_received ON heartbeat(location_id, received_at DESC);

-- Power event queries for diagrams
CREATE INDEX idx_power_event_location_occurred ON power_event(location_id, occurred_at);

-- Diagram message lookups
CREATE UNIQUE INDEX idx_diagram_location_date ON diagram_message(location_id, diagram_date);
CREATE INDEX idx_diagram_pinned ON diagram_message(is_pinned) WHERE is_pinned = true;
```

## Data Retention

| Entity | Retention Policy |
|--------|------------------|
| Location | Permanent |
| Heartbeat | Permanent (consider archiving after 1 year) |
| PowerEvent | Permanent (required for future analytics) |
| DiagramMessage | Permanent (low volume, ~365 per location per year) |
