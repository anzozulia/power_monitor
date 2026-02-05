# Feature Specification: Power Outage Monitor

**Feature Branch**: `001-power-outage-monitor`  
**Created**: 2026-02-04  
**Status**: Draft  
**Input**: User description: "Power outage monitoring, alerting and analytics tool for personal use across multiple houses"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Location Setup and Management (Priority: P1)

As a home owner, I want to register my houses in the system and configure monitoring parameters so that each location can be independently tracked for power outages.

**Why this priority**: Without location setup, no monitoring can occur. This is the foundational capability that enables all other features.

**Independent Test**: Can be fully tested by logging into the admin panel, creating a location with all required parameters, and verifying the location appears in the list with correct configuration.

**Acceptance Scenarios**:

1. **Given** I am logged into the admin panel, **When** I navigate to locations, **Then** I see a list of all my configured locations with their current power status.
2. **Given** I am on the locations page, **When** I click "Add Location", **Then** I see a form requesting: name, expected heartbeat period, grace time, Telegram bot token, and chat/channel ID.
3. **Given** I have filled in all location details, **When** I save the location, **Then** I receive ESP32 configuration information (endpoint URL, location identifier, authentication details).
4. **Given** a location exists, **When** I edit its configuration, **Then** the changes are saved and applied to future monitoring.
5. **Given** a location exists, **When** I delete it, **Then** monitoring stops and the location is removed from my list.

---

### User Story 2 - Heartbeat Reception and Power Monitoring (Priority: P2)

As the system, I need to receive heartbeats from ESP32 devices and determine power status based on heartbeat patterns so that outages are detected automatically.

**Why this priority**: This is the core monitoring logic. Without heartbeat processing, no power status can be determined.

**Independent Test**: Can be tested by sending simulated heartbeats to a configured location endpoint and verifying the power status changes appropriately in the admin panel.

**Acceptance Scenarios**:

1. **Given** a location is configured but has never received a heartbeat, **When** the first heartbeat arrives, **Then** monitoring begins and power is marked as ON.
2. **Given** monitoring is active and power is ON, **When** heartbeats continue arriving within the expected period, **Then** power status remains ON.
3. **Given** monitoring is active and power is ON, **When** no heartbeat is received for longer than (expected period + grace time), **Then** power is marked as OFF.
4. **Given** power is OFF for a location, **When** a new heartbeat arrives, **Then** power is marked as ON.
5. **Given** any status change occurs, **When** the change is detected, **Then** the timestamp and duration since last change are recorded.

---

### User Story 3 - Telegram Alerting (Priority: P3)

As a home owner, I want to receive Telegram notifications when power goes out or comes back on so that I am immediately informed of power status changes at my properties.

**Why this priority**: Alerting provides immediate value by notifying the user of events. Depends on heartbeat monitoring being functional.

**Independent Test**: Can be tested by triggering a power status change (simulating outage/restoration) and verifying the appropriate Telegram message is sent to the configured chat.

**Acceptance Scenarios**:

1. **Given** power goes OFF at a location, **When** the outage is detected, **Then** a styled alert is sent via Telegram showing: location name, "Power OFF" status, and duration power was ON before this outage.
2. **Given** power comes back ON at a location, **When** the restoration is detected, **Then** a styled alert is sent via Telegram showing: location name, "Power ON" status, and duration power was OFF.
3. **Given** a Telegram message fails to send, **When** the failure occurs, **Then** the system retries and logs the failure for troubleshooting.
4. **Given** alert styling is applied, **When** viewing alerts, **Then** power OFF alerts are visually distinct from power ON alerts (different formatting/emoji).

---

### User Story 4 - Weekly Analytics Diagram (Priority: P4)

As a home owner, I want to receive a daily visual summary of power status over the past 7 days so that I can identify patterns and compare outage frequency across days.

**Why this priority**: Analytics provides historical insights. Requires monitoring data to be collected first.

**Independent Test**: Can be tested by populating a location with historical power status data and triggering the daily diagram generation, then verifying the image is sent and pinned to the Telegram channel.

**Acceptance Scenarios**:

1. **Given** it is 00:00 Kyiv time, **When** the daily job runs, **Then** a new weekly diagram image is generated and sent to the location's Telegram channel.
2. **Given** a new diagram is sent, **When** it posts, **Then** the previous day's pinned diagram is unpinned and the new one is pinned.
3. **Given** the diagram is generated, **When** viewing it, **Then** it shows 7 horizontal lines (Monday at top, Sunday at bottom) with weekday code and date (DD.MM) to the right of each line.
4. **Given** the diagram is generated, **When** viewing the time scale, **Then** each line has hour marks from 0-24 with major marks at 0, 6, 12, 18, 24.
5. **Given** the diagram displays power status, **When** viewing colors, **Then** green indicates power ON, red indicates power OFF, gray indicates no data.
6. **Given** today is mid-week, **When** viewing the diagram, **Then** days from the previous week are displayed with dimmed styling to distinguish them from current week.
7. **Given** it is any hour of the day, **When** the hourly update job runs, **Then** the current day's pinned diagram message is updated with fresh data.
8. **Given** it is 00:00, **When** the new diagram is about to be sent, **Then** the previous diagram receives one final update before being unpinned.

---

### Edge Cases

- What happens when ESP32 sends duplicate heartbeats in rapid succession? System ignores duplicates within a short window (e.g., 5 seconds) to prevent noise.
- How does system handle Telegram API rate limits? System queues messages and respects rate limits with exponential backoff.
- What happens if a location has no data for an entire week? The diagram shows all gray (no data) for that location.
- How does system handle timezone changes (DST)? All times stored in UTC, displayed in Kyiv timezone. DST transitions handled automatically.
- What happens if the VPS restarts during an outage? On startup, system checks last known status and time, resumes monitoring without false alerts.
- What if the admin deletes a location while an outage is in progress? Monitoring stops immediately, no further alerts sent.
- What happens if Telegram bot token becomes invalid? System logs error, marks location alerting as failed, displays warning in admin panel.

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Authorization**

- **FR-001**: System MUST require authentication to access the admin panel using username/password credentials.
- **FR-002**: System MUST support single-user access for personal use.

**Location Management**

- **FR-003**: Admin MUST be able to create locations with: name, expected heartbeat period (seconds), grace time (seconds), Telegram bot token, Telegram chat/channel ID.
- **FR-004**: Admin MUST be able to view all locations with their current power status (ON/OFF/Not Started).
- **FR-005**: Admin MUST be able to edit location configuration.
- **FR-006**: Admin MUST be able to delete locations.
- **FR-007**: System MUST generate and display ESP32 configuration details upon location creation.

**Heartbeat Processing**

- **FR-008**: System MUST expose an endpoint to receive heartbeats from ESP32 devices (minimal ping: auth token + location ID only, no payload).
- **FR-009**: System MUST authenticate heartbeat requests using location-specific credentials.
- **FR-010**: System MUST record timestamp of each heartbeat received.
- **FR-011**: System MUST mark monitoring as "started" upon first heartbeat for a location.
- **FR-012**: System MUST determine power status based on heartbeat timing and configured thresholds.

**Power Status Logic**

- **FR-013**: System MUST mark power as OFF when no heartbeat received for (expected period + grace time).
- **FR-014**: System MUST mark power as ON when heartbeat received after an outage.
- **FR-015**: System MUST track and store duration of each power state for historical analysis.

**Alerting**

- **FR-016**: System MUST send Telegram alert when power status changes to OFF.
- **FR-017**: System MUST send Telegram alert when power status changes to ON.
- **FR-018**: Alerts MUST include: location name, new status, duration of previous status.
- **FR-019**: Alerts MUST have distinct visual styling for ON vs OFF events.

**Analytics**

- **FR-020**: System MUST generate weekly diagram image daily at 00:00 Kyiv time.
- **FR-021**: Diagram MUST show 7 days (Monday-Sunday) with power status color-coded.
- **FR-022**: Diagram MUST include hour scale (0-24) with major marks at 0, 6, 12, 18, 24.
- **FR-023**: System MUST pin new diagram and unpin previous diagram.
- **FR-024**: System MUST update pinned diagram hourly throughout the day.
- **FR-025**: Previous week days MUST be displayed dimmed in the diagram.

**Data Persistence**

- **FR-026**: System MUST store all historical power status data indefinitely for future analytics.
- **FR-027**: System MUST store all heartbeat timestamps for audit purposes.

### Key Entities

- **Location**: Represents a monitored property. Attributes: name, heartbeat period, grace time, Telegram bot token, chat ID, ESP32 credentials, current power status, monitoring start timestamp.
- **Heartbeat**: A signal received from an ESP32 device. Attributes: location reference, timestamp.
- **PowerEvent**: A recorded change in power status. Attributes: location reference, event type (ON/OFF), timestamp, duration of previous state.
- **DiagramMessage**: Reference to a Telegram message containing a diagram. Attributes: location reference, message ID, date, is pinned.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can set up a new location and receive ESP32 configuration in under 2 minutes.
- **SC-002**: Power outage is detected and alert sent within (grace time + 30 seconds) of actual outage.
- **SC-003**: Power restoration alert is sent within 30 seconds of first heartbeat after outage.
- **SC-004**: Weekly diagram is generated and posted within 5 minutes of 00:00 Kyiv time.
- **SC-005**: System supports monitoring at least 10 locations simultaneously without degradation.
- **SC-006**: All historical power data is preserved and accessible for future analytics expansion.
- **SC-007**: Telegram alerts are delivered successfully 99% of the time (excluding Telegram service outages).
- **SC-008**: Hourly diagram updates complete within 2 minutes of the hour.

## Clarifications

### Session 2026-02-04

- Q: Admin authentication method? → A: Simple username/password (details deferred to planning)
- Q: ESP32 heartbeat data content? → A: Minimal ping only (auth token + location ID, no payload)

## Assumptions

- Single admin user (personal use) - no multi-tenancy required at this stage.
- ESP32 devices have reliable internet connectivity when power is available.
- Telegram API remains available and stable for bot operations.
- VPS has sufficient uptime (99%+) for reliable monitoring.
- Kyiv timezone (Europe/Kyiv) is used for all display and scheduling purposes.
- Admin is responsible for creating and configuring Telegram bots and obtaining tokens.
- Maximum 10 locations for initial deployment (scalable architecture for future growth).
