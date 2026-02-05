# Quickstart: Power Outage Monitor

**Branch**: `001-power-outage-monitor`  
**Date**: 2026-02-04

## Prerequisites

- Docker and Docker Compose installed
- A Telegram bot token (create via @BotFather)
- A Telegram group/channel ID for alerts

## Local Development Setup

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd power_monitor

# Copy environment template
cp .env.example .env.docker_local

# Edit .env.docker_local with your settings
# Required variables:
#   DJANGO_SECRET_KEY=your-secret-key
#   POSTGRES_PASSWORD=your-db-password
#   ADMIN_USERNAME=admin
#   ADMIN_PASSWORD=your-admin-password
```

### 2. Start Services

```bash
# Build and start all services
make up

# Or manually:
docker-compose -f docker-compose.local.yml up -d --build
```

### 3. Initialize Database

```bash
# Run migrations
make migrate

# Create admin user (uses ADMIN_USERNAME/ADMIN_PASSWORD from .env)
make createsuperuser
```

### 4. Access Admin Panel

Open http://localhost:8000/admin/locations/

Login with credentials from .env.

## Adding Your First Location

1. Click "Add Location"
2. Fill in:
   - **Name**: "Home Kyiv" (or your location name)
   - **Heartbeat Period**: 60 (seconds - how often ESP32 will ping)
   - **Grace Period**: 30 (seconds - extra time before marking offline)
   - **Telegram Bot Token**: Your bot token from @BotFather
   - **Telegram Chat ID**: Your group/channel ID
3. Click "Save"
4. Copy the displayed API key and endpoint URL

## ESP32 Setup

Minimal Arduino code for ESP32:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "https://your-domain.com/api/heartbeat/";
const char* apiKey = "YOUR_API_KEY_FROM_ADMIN_PANEL";
const int heartbeatInterval = 60000; // 60 seconds in milliseconds

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected!");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("X-API-Key", apiKey);
    
    int httpCode = http.POST("");
    
    if (httpCode > 0) {
      Serial.printf("Heartbeat sent, response: %d\n", httpCode);
    } else {
      Serial.printf("Heartbeat failed: %s\n", http.errorToString(httpCode).c_str());
    }
    
    http.end();
  }
  
  delay(heartbeatInterval);
}
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | View logs (follow mode) |
| `make migrate` | Run database migrations |
| `make shell` | Django shell |
| `make bash` | Shell into app container |
| `make createsuperuser` | Create admin user |

## Production Deployment

### 1. Configure Production Environment

```bash
cp .env.example .env.docker_production

# Edit with production values:
#   DJANGO_SECRET_KEY=<generate-strong-key>
#   DJANGO_DEBUG=false
#   DJANGO_ALLOWED_HOSTS=your-domain.com
#   POSTGRES_PASSWORD=<strong-password>
#   ADMIN_USERNAME=admin
#   ADMIN_PASSWORD=<strong-password>
```

### 2. Deploy

```bash
# On your VPS
make up-prod

# Run migrations
make migrate-prod

# Create admin user
make createsuperuser-prod
```

### 3. Configure Reverse Proxy

Set up nginx/caddy on host to proxy port 8000 with HTTPS.

## Verification Checklist

- [ ] Admin panel accessible at /admin/locations/
- [ ] Can create a new location
- [ ] ESP32 config page shows API key and endpoint
- [ ] Heartbeat endpoint responds to POST with API key
- [ ] Power status updates in admin panel after first heartbeat
- [ ] Telegram alert received when simulating outage
- [ ] Weekly diagram appears in Telegram at midnight

## Troubleshooting

### Heartbeat not registering
- Check API key is correct
- Verify endpoint URL includes `/api/heartbeat/`
- Check container logs: `make logs`

### Telegram alerts not sending
- Verify bot token is valid (test with @BotFather)
- Ensure bot is admin in the group/channel
- Check chat ID is correct (negative for groups)
- Check `alerting_failed` flag in admin panel

### Diagram not generating
- Wait for 00:00 Kyiv time for first diagram
- Check worker container is running: `docker ps`
- Check worker logs: `make logs`
