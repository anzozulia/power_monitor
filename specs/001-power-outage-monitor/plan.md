# Implementation Plan: Power Outage Monitor

**Branch**: `001-power-outage-monitor` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-power-outage-monitor/spec.md`

## Summary

Build a power outage monitoring system for personal use across multiple houses. ESP32 devices send heartbeats to a Django-based VPS service. The system detects power outages when heartbeats stop, sends styled Telegram alerts, and generates weekly analytics diagrams. Custom admin panel built with Tailwind CSS for location management.

## Technical Context

**Language/Version**: Python 3.12  
**Framework**: Django 6.0  
**Primary Dependencies**:
- Django 6.0 (web framework + background tasks)
- python-telegram-bot 21.x (Telegram API)
- matplotlib + numpy (diagram generation)
- psycopg 3.x (PostgreSQL driver)
- django-tailwind (CSS framework)
- gunicorn (production WSGI server)

**Storage**: PostgreSQL 16  
**Testing**: None (explicitly excluded per user requirement)  
**Target Platform**: Linux VPS (Docker)  
**Project Type**: Single Django project  
**Performance Goals**: Handle 10 locations, heartbeats every 10-60 seconds  
**Constraints**: <30 second detection latency, VPS with 1GB+ RAM  
**Scale/Scope**: Single user, 10 locations max, ~8.6M heartbeats/year max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is in placeholder state (v0.1.0). No defined principles to check against.
Proceeding with plan.md documentation of all workflow decisions as required by constitution governance section.

**Workflow Decisions Documented**:
- No test requirements (user specified)
- Single Django project structure (simplicity)
- Docker-based deployment with PostgreSQL
- Environment-based configuration via .env files
- Makefile for all management commands

## Project Structure

### Documentation (this feature)

```text
specs/001-power-outage-monitor/
├── plan.md              # This file
├── research.md          # Technology decisions and rationale
├── data-model.md        # Database schema and entities
├── quickstart.md        # Setup and deployment guide
├── contracts/           # API specifications
│   └── api.md           # REST API and internal task contracts
└── tasks.md             # Implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
power_monitor/
├── .env.example                    # Environment template
├── .env.docker_local              # Local Docker config (gitignored)
├── .env.docker_production         # Production config (gitignored)
├── Dockerfile                      # Multi-stage build
├── docker-compose.local.yml        # Local development
├── docker-compose.prod.yml         # Production deployment
├── Makefile                        # Management commands
├── requirements.txt                # Python dependencies
│
├── src/                            # Django project root
│   ├── manage.py
│   ├── config/                     # Django settings
│   │   ├── __init__.py
│   │   ├── settings.py             # Base settings
│   │   ├── urls.py                 # Root URL config
│   │   └── wsgi.py
│   │
│   ├── core/                       # Core app (models, shared utilities)
│   │   ├── __init__.py
│   │   ├── models.py               # Location, Heartbeat, PowerEvent, DiagramMessage
│   │   ├── admin.py                # Not used (custom admin panel)
│   │   └── migrations/
│   │
│   ├── admin_panel/                # Custom admin panel app
│   │   ├── __init__.py
│   │   ├── views.py                # Location CRUD, login/logout
│   │   ├── forms.py                # Location forms
│   │   ├── urls.py                 # Admin routes
│   │   └── templates/
│   │       └── admin_panel/
│   │           ├── base.html       # Tailwind base template
│   │           ├── login.html
│   │           ├── locations/
│   │           │   ├── list.html
│   │           │   ├── form.html
│   │           │   ├── detail.html
│   │           │   └── config.html
│   │           └── components/
│   │               ├── navbar.html
│   │               ├── status_badge.html
│   │               └── flash_messages.html
│   │
│   ├── heartbeat/                  # Heartbeat API app
│   │   ├── __init__.py
│   │   ├── views.py                # POST /api/heartbeat/
│   │   ├── urls.py
│   │   └── authentication.py       # API key auth
│   │
│   ├── monitoring/                 # Background monitoring app
│   │   ├── __init__.py
│   │   ├── tasks.py                # check_heartbeats, send_alert
│   │   └── services.py             # Power status logic
│   │
│   ├── analytics/                  # Diagram generation app
│   │   ├── __init__.py
│   │   ├── tasks.py                # update_hourly_diagram, generate_daily_diagram
│   │   ├── diagram.py              # Matplotlib diagram generation
│   │   └── services.py             # Telegram message management
│   │
│   ├── telegram_client/            # Telegram integration
│   │   ├── __init__.py
│   │   ├── client.py               # python-telegram-bot wrapper
│   │   └── formatting.py           # Alert message formatting
│   │
│   └── static/
│       └── css/
│           └── output.css          # Compiled Tailwind CSS
│
├── docker_data/                    # Persistent data (gitignored)
│   └── postgres/
│
├── logs/                           # Application logs (gitignored)
│
└── backups/                        # Database backups (gitignored)
```

**Structure Decision**: Single Django project with feature-based apps. Chose this over monolithic structure for:
- Clear separation of concerns (admin, heartbeat API, monitoring, analytics)
- Independent development of each feature
- Easier navigation and maintenance

## Complexity Tracking

No constitution violations to justify. Complexity is minimal:
- Single project (not multi-service)
- No external cache (PostgreSQL handles all persistence)
- No message broker (django.tasks uses PostgreSQL)
- Standard Django patterns throughout

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Background Tasks | django.tasks (native) | No Redis needed; PostgreSQL backend; simplest for small scale |
| Diagram Generation | Matplotlib | Direct PNG export; simple API; well-documented |
| Telegram Library | python-telegram-bot | Async support; simple API; full Bot API coverage |
| Admin Panel | Custom Django views + Tailwind | User requirement; more control than Django admin |
| Authentication | Django session auth | Simple; secure; built-in password hashing |
| ESP32 Auth | API key in header | Stateless; simple for microcontrollers |

## Dependencies

```text
# requirements.txt
Django>=6.0,<7.0
psycopg[binary]>=3.1
python-telegram-bot>=21.0
matplotlib>=3.8
numpy>=1.26
gunicorn>=21.0
django-tailwind>=3.8
python-dotenv>=1.0
```

## Environment Variables

```bash
# .env.example
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=power_monitor
POSTGRES_USER=power_monitor
POSTGRES_PASSWORD=change-me

ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me

TZ=Europe/Kyiv
```

## Docker Services

| Service | Image | Purpose | Ports |
|---------|-------|---------|-------|
| app | Custom (Dockerfile) | Django web server | 8000:8000 |
| worker | Custom (Dockerfile) | Background tasks | - |
| postgres | postgres:16-alpine | Database | - (internal) |

## Next Steps

Run `/speckit.tasks` to generate implementation task breakdown.
