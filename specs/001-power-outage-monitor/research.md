# Research: Power Outage Monitor

**Branch**: `001-power-outage-monitor`  
**Date**: 2026-02-04

## Background Task Scheduler

**Decision**: Django 6.0 native `django.tasks` with PostgreSQL database backend

**Rationale**:
- Simplest setup using existing PostgreSQL database (no extra services like Redis)
- Works seamlessly with Docker via a single worker container
- Handles all our needs: frequent heartbeat checks, hourly image updates, daily midnight jobs
- Built-in queue support, retries, and priorities
- No additional dependencies beyond Django 6.0

**Alternatives Considered**:
| Tool | Verdict | Reason |
|------|---------|--------|
| Celery + Redis | Rejected | Overkill for small scale; requires Redis container; complex setup |
| Django-Q2 | Rejected | Heavier than native; prefers Redis |
| APScheduler | Rejected | Basic scheduling only; no queues/retries |
| Huey | Rejected | Lightweight but still needs Redis |

**Implementation Notes**:
- Configure separate queues: `default`, `heartbeats`, `diagrams`
- Run heartbeat checks every 10 seconds via dedicated queue
- Hourly diagram updates via scheduled task
- Daily midnight job for new diagram generation
- Single worker container in Docker Compose

## Diagram Image Generation

**Decision**: Matplotlib with NumPy

**Rationale**:
- Best for custom static plots with horizontal bar charts
- Easy control over colors, positions, and hour tick marks
- Direct PNG export with `plt.savefig()`
- Minimal code (~20 lines for our timeline visualization)
- Well-documented, stable, widely used

**Alternatives Considered**:
| Library | Verdict | Reason |
|---------|---------|--------|
| Pillow | Rejected | No built-in charts; requires pixel-by-pixel drawing (~50+ lines) |
| Plotly | Rejected | Resource-intensive; overkill for static images |
| Cairo | Rejected | Too low-level; verbose; not Pythonic for charts |

**Implementation Notes**:
- 7 horizontal bars (Monday-Sunday)
- X-axis: hours 0-24 with major marks at 0, 6, 12, 18, 24
- Colors: green (ON), red (OFF), gray (no data)
- Previous week days rendered with alpha=0.5 for dimming
- Output: PNG at 150 DPI, ~800x400 pixels

## Telegram Bot Library

**Decision**: python-telegram-bot (v20.0+)

**Rationale**:
- Full asyncio-based design (Python 3.10+)
- Simple high-level API with convenience methods
- Full Bot API support including pinChatMessage/unpinChatMessage
- Well-maintained, most recommended Python library
- Easy Django integration via async tasks

**Alternatives Considered**:
| Library | Verdict | Reason |
|---------|---------|--------|
| aiogram | Considered | Strong async but less high-level conveniences |
| telethon | Rejected | User client library, not bot-optimized; complex |

**Implementation Notes**:
- Install with `pip install python-telegram-bot`
- Use `bot.send_message()`, `bot.send_photo()` for alerts
- Use `bot.pin_chat_message()`, `bot.unpin_chat_message()` for diagram management
- Run bot operations in background tasks, not as standalone bot process

## Django + Tailwind Integration

**Decision**: django-tailwind package with standalone Tailwind CLI

**Rationale**:
- Official Tailwind CLI approach (no Node.js in production)
- Hot-reload during development
- Purges unused CSS in production builds
- Works well with Django templates

**Implementation Notes**:
- Install django-tailwind package
- Configure in settings.py
- Use Tailwind CDN for development simplicity (acceptable for personal project)
- For production: compile CSS during Docker build

## Admin Authentication

**Decision**: Django's built-in authentication with custom login view

**Rationale**:
- Simple username/password (as specified)
- Session-based auth using Django's auth system
- No need for JWT/tokens for a web-only admin panel
- Leverage Django's password hashing and session management

**Implementation Notes**:
- Create custom login page with Tailwind styling
- Use `@login_required` decorator for protected views
- Store credentials in .env or Django admin (single user)
