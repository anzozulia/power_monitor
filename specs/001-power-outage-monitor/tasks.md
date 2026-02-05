# Tasks: Power Outage Monitor

**Input**: Design documents from `/specs/001-power-outage-monitor/`  
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: No tests required (explicitly excluded per user specification).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/` at repository root
- Paths shown below use the structure from plan.md

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project structure, dependencies, and Docker configuration.

- [x] T001 Create project directory structure per plan.md at repository root
- [x] T002 Create requirements.txt with all dependencies in requirements.txt
- [x] T003 [P] Create .env.example with all environment variables in .env.example
- [x] T004 [P] Create .gitignore with Python, Django, Docker, and IDE patterns in .gitignore
- [x] T005 [P] Create Dockerfile with multi-stage build (dev and prod targets) in Dockerfile
- [x] T006 Create docker-compose.local.yml with app, worker, and postgres services in docker-compose.local.yml
- [x] T007 [P] Create docker-compose.prod.yml with production configuration in docker-compose.prod.yml
- [x] T008 Create Makefile with all management commands (up, down, logs, migrate, shell, bash, createsuperuser) in Makefile

**Checkpoint**: Docker environment ready to build and run.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Django project setup and all database models. MUST complete before any user story.

**Warning**: No user story work can begin until this phase is complete.

### Django Project Initialization

- [x] T009 Initialize Django project with manage.py in src/manage.py
- [x] T010 Create Django settings with database, installed apps, and timezone config in src/config/settings.py
- [x] T011 [P] Create root URL configuration in src/config/urls.py
- [x] T012 [P] Create WSGI configuration in src/config/wsgi.py
- [x] T013 [P] Create config package __init__.py in src/config/__init__.py

### Core App with All Models

- [x] T014 Create core app package in src/core/__init__.py
- [x] T015 Create all database models (Location, Heartbeat, PowerEvent, DiagramMessage) per data-model.md in src/core/models.py
- [x] T016 Create empty admin.py (not using Django admin) in src/core/admin.py
- [ ] T017 Generate initial database migrations by running makemigrations

### App Packages (Empty Structure)

- [x] T018 [P] Create admin_panel app package in src/admin_panel/__init__.py
- [x] T019 [P] Create heartbeat app package in src/heartbeat/__init__.py
- [x] T020 [P] Create monitoring app package in src/monitoring/__init__.py
- [x] T021 [P] Create analytics app package in src/analytics/__init__.py
- [x] T022 [P] Create telegram_client package in src/telegram_client/__init__.py

### Tailwind Setup

- [x] T023 Configure django-tailwind in settings and create theme app in src/config/settings.py
- [x] T024 Create base.html template with Tailwind CDN and common layout in src/admin_panel/templates/admin_panel/base.html
- [x] T025 [P] Create navbar component template in src/admin_panel/templates/admin_panel/components/navbar.html
- [x] T026 [P] Create flash_messages component template in src/admin_panel/templates/admin_panel/components/flash_messages.html
- [x] T027 [P] Create status_badge component template in src/admin_panel/templates/admin_panel/components/status_badge.html

### Logging Configuration

- [x] T028 Configure Python logging with file handlers and rotation in src/config/settings.py

**Checkpoint**: Foundation ready - Django runnable, models migrated, base templates exist. User story implementation can now begin.

---

## Phase 3: User Story 1 - Location Setup and Management (Priority: P1)

**Goal**: Admin can login, view locations, create/edit/delete locations, and see ESP32 configuration.

**Independent Test**: Login to admin panel, create a location, verify it appears in list with config page showing API key.

### Authentication

- [x] T029 [US1] Create custom login view with session authentication in src/admin_panel/views.py
- [x] T030 [US1] Create login.html template with Tailwind styling in src/admin_panel/templates/admin_panel/login.html
- [x] T031 [US1] Create logout view in src/admin_panel/views.py
- [x] T032 [US1] Add login_required decorator and redirect logic in src/admin_panel/views.py

### Location Forms

- [x] T033 [US1] Create LocationForm with all fields and validation in src/admin_panel/forms.py

### Location Views

- [x] T034 [US1] Create location_list view displaying all locations with status in src/admin_panel/views.py
- [x] T035 [US1] Create location_create view with form handling in src/admin_panel/views.py
- [x] T036 [US1] Create location_detail view showing config and recent events in src/admin_panel/views.py
- [x] T037 [US1] Create location_edit view with form pre-population in src/admin_panel/views.py
- [x] T038 [US1] Create location_delete view with confirmation in src/admin_panel/views.py
- [x] T039 [US1] Create location_config view displaying ESP32 setup info in src/admin_panel/views.py

### Location Templates

- [x] T040 [P] [US1] Create locations/list.html with table and status indicators in src/admin_panel/templates/admin_panel/locations/list.html
- [x] T041 [P] [US1] Create locations/form.html for create/edit in src/admin_panel/templates/admin_panel/locations/form.html
- [x] T042 [P] [US1] Create locations/detail.html with config and events in src/admin_panel/templates/admin_panel/locations/detail.html
- [x] T043 [P] [US1] Create locations/config.html with API key and ESP32 code snippet in src/admin_panel/templates/admin_panel/locations/config.html

### URL Routing

- [x] T044 [US1] Create admin_panel URL patterns in src/admin_panel/urls.py
- [x] T045 [US1] Include admin_panel URLs in root urlconf in src/config/urls.py

### API Key Generation

- [x] T046 [US1] Implement auto-generation of API key on Location save in src/core/models.py

**Checkpoint**: User Story 1 complete. Admin can login, CRUD locations, view ESP32 config. Independently testable.

---

## Phase 4: User Story 2 - Heartbeat Reception and Power Monitoring (Priority: P2)

**Goal**: ESP32 can send heartbeats, system tracks power status, detects outages automatically.

**Independent Test**: Send POST to /api/heartbeat/ with valid API key, verify location status changes to ON. Wait for timeout, verify status changes to OFF.

### Heartbeat API Endpoint

- [x] T047 [US2] Create API key authentication middleware in src/heartbeat/authentication.py
- [x] T048 [US2] Create heartbeat POST view with duplicate detection in src/heartbeat/views.py
- [x] T049 [US2] Create heartbeat URL patterns in src/heartbeat/urls.py
- [x] T050 [US2] Include heartbeat URLs in root urlconf (under /api/) in src/config/urls.py

### Power Status Logic

- [x] T051 [US2] Create power status service with state transition logic in src/monitoring/services.py
- [x] T052 [US2] Implement process_heartbeat function (update last_heartbeat_at, create Heartbeat record, handle first heartbeat) in src/monitoring/services.py
- [x] T053 [US2] Implement detect_outage function (check timeout, create PowerEvent, update status) in src/monitoring/services.py

### Background Tasks

- [x] T054 [US2] Configure django.tasks with PostgreSQL backend and queues in src/config/settings.py
- [x] T055 [US2] Create check_heartbeats periodic task (runs every 10 seconds) in src/monitoring/tasks.py
- [x] T056 [US2] Register check_heartbeats task with heartbeats queue in src/monitoring/tasks.py

### Worker Configuration

- [x] T057 [US2] Add worker service command to docker-compose.local.yml in docker-compose.local.yml
- [x] T058 [US2] Add worker service command to docker-compose.prod.yml in docker-compose.prod.yml

**Checkpoint**: User Story 2 complete. Heartbeats received, status tracked, outages detected. Independently testable.

---

## Phase 5: User Story 3 - Telegram Alerting (Priority: P3)

**Goal**: Send styled Telegram alerts when power status changes.

**Independent Test**: Trigger a power status change, verify Telegram message received in configured chat with correct formatting and duration.

### Telegram Client

- [x] T059 [US3] Create async Telegram bot wrapper using python-telegram-bot in src/telegram_client/client.py
- [x] T060 [US3] Implement send_message method with retry logic in src/telegram_client/client.py
- [x] T061 [US3] Implement send_photo method for diagram sending in src/telegram_client/client.py
- [x] T062 [US3] Implement pin_message and unpin_message methods in src/telegram_client/client.py

### Alert Formatting

- [x] T063 [US3] Create alert message formatter with emoji and styling in src/telegram_client/formatting.py
- [x] T064 [US3] Implement format_power_off_alert with duration in src/telegram_client/formatting.py
- [x] T065 [US3] Implement format_power_on_alert with duration in src/telegram_client/formatting.py

### Alert Task

- [x] T066 [US3] Create send_alert background task in src/monitoring/tasks.py
- [x] T067 [US3] Integrate send_alert call into detect_outage service in src/monitoring/services.py
- [x] T068 [US3] Integrate send_alert call into process_heartbeat for power restoration in src/monitoring/services.py
- [x] T069 [US3] Implement alerting_failed flag update on Telegram errors in src/monitoring/tasks.py

### Admin Panel Integration

- [x] T070 [US3] Add alerting_failed warning display to location list template in src/admin_panel/templates/admin_panel/locations/list.html

**Checkpoint**: User Story 3 complete. Telegram alerts sent on status changes. Independently testable.

---

## Phase 6: User Story 4 - Weekly Analytics Diagram (Priority: P4)

**Goal**: Generate and send weekly power status diagram daily, update hourly.

**Independent Test**: Populate location with power event data, trigger diagram generation, verify image sent to Telegram with correct visualization.

### Diagram Generation

- [x] T071 [US4] Create diagram generator class using matplotlib in src/analytics/diagram.py
- [x] T072 [US4] Implement get_power_status_data function to query PowerEvents for date range in src/analytics/diagram.py
- [x] T073 [US4] Implement render_weekly_diagram function with 7 day bars, hour scale, colors in src/analytics/diagram.py
- [x] T074 [US4] Implement dimming for previous week days in diagram in src/analytics/diagram.py
- [x] T075 [US4] Implement save_diagram_to_bytes for Telegram upload in src/analytics/diagram.py

### Diagram Message Management

- [x] T076 [US4] Create diagram message service for pin/unpin tracking in src/analytics/services.py
- [x] T077 [US4] Implement get_or_create_today_diagram function in src/analytics/services.py
- [x] T078 [US4] Implement update_diagram_message function (edit existing Telegram message) in src/analytics/services.py
- [x] T079 [US4] Implement unpin_previous_diagram function in src/analytics/services.py

### Diagram Tasks

- [x] T080 [US4] Create generate_daily_diagram task (runs at 00:00 Kyiv time) in src/analytics/tasks.py
- [x] T081 [US4] Create update_hourly_diagram task (runs every hour at :00) in src/analytics/tasks.py
- [x] T082 [US4] Register diagram tasks with diagrams queue in src/analytics/tasks.py
- [x] T083 [US4] Configure task scheduling for midnight and hourly runs in src/config/settings.py

**Checkpoint**: User Story 4 complete. Diagrams generated, sent, pinned, and updated hourly. Independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and final touches.

- [x] T084 [P] Add VPS restart recovery logic (check last known status on startup) in src/monitoring/services.py
- [x] T085 [P] Add Telegram rate limiting with exponential backoff in src/telegram_client/client.py
- [x] T086 [P] Add duplicate heartbeat detection (5 second window) in src/heartbeat/views.py
- [x] T087 [P] Add timezone handling for Kyiv timezone throughout in src/config/settings.py
- [x] T088 [P] Add comprehensive error logging in all services in src/monitoring/services.py
- [x] T089 [P] Add createsuperuser management command for initial admin user in src/core/management/commands/createadmin.py
- [ ] T090 Validate all admin panel views work end-to-end
- [ ] T091 Validate heartbeat API works with curl/Postman
- [ ] T092 Update quickstart.md with any changes discovered during implementation in specs/001-power-outage-monitor/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup) ──────────────────────────────────────────┐
                                                          │
Phase 2 (Foundational) ◄──────────────────────────────────┘
         │
         │ BLOCKS ALL USER STORIES
         ▼
┌────────┴────────┬─────────────────┬─────────────────────┐
│                 │                 │                     │
▼                 ▼                 ▼                     ▼
Phase 3 (US1)    Phase 4 (US2)    Phase 5 (US3)         Phase 6 (US4)
Location Setup   Heartbeat        Telegram Alerting     Analytics Diagram
                 Monitoring
│                 │                 │                     │
│                 │                 ▲                     │
│                 └─────────────────┘                     │
│                 (US3 needs US2 for                      │
│                  status changes)                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
                  Phase 7 (Polish)
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Location Setup) | Phase 2 only | US2, US3, US4 (after Phase 2) |
| US2 (Heartbeat Monitoring) | Phase 2 only | US1 |
| US3 (Telegram Alerting) | US2 (needs power events) | US4 |
| US4 (Analytics Diagram) | Phase 2 only | US1, US2, US3 |

### Within Each User Story

- Models → Services → Views/Tasks → Templates
- Core logic before integration
- Story complete before Polish phase

---

## Parallel Execution Examples

### Phase 1: Setup

```text
Parallel Group 1 (independent files):
  T003 .env.example
  T004 .gitignore
  T005 Dockerfile
  T007 docker-compose.prod.yml
```

### Phase 2: Foundational

```text
Parallel Group 1 (URL/WSGI):
  T011 urls.py
  T012 wsgi.py
  T013 __init__.py

Parallel Group 2 (app packages):
  T018 admin_panel/__init__.py
  T019 heartbeat/__init__.py
  T020 monitoring/__init__.py
  T021 analytics/__init__.py
  T022 telegram_client/__init__.py

Parallel Group 3 (components):
  T025 navbar.html
  T026 flash_messages.html
  T027 status_badge.html
```

### Phase 3: User Story 1

```text
Parallel Group 1 (templates):
  T040 locations/list.html
  T041 locations/form.html
  T042 locations/detail.html
  T043 locations/config.html
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Location Setup)
4. Complete Phase 4: User Story 2 (Heartbeat Monitoring)
5. **STOP and VALIDATE**: Admin can create locations, ESP32 can send heartbeats, status updates visible
6. Deploy/demo MVP

### Incremental Delivery

| Increment | User Stories | Value Delivered |
|-----------|--------------|-----------------|
| MVP | US1 + US2 | Location setup, heartbeat monitoring, status visible in admin |
| +Alerting | +US3 | Telegram notifications on power changes |
| +Analytics | +US4 | Weekly diagrams with power history |
| +Polish | Phase 7 | Error handling, edge cases, stability |

### Recommended Implementation Order

1. **Phase 1**: Setup (T001-T008)
2. **Phase 2**: Foundational (T009-T028)
3. **Phase 3**: US1 - Location Setup (T029-T046)
4. **Phase 4**: US2 - Heartbeat Monitoring (T047-T058)
5. **Phase 5**: US3 - Telegram Alerting (T059-T070)
6. **Phase 6**: US4 - Analytics Diagram (T071-T083)
7. **Phase 7**: Polish (T084-T092)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No tests included (per user specification)
- Total: 92 tasks across 7 phases
