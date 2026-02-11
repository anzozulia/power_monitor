"""
Power Monitoring Services

Core business logic for heartbeat processing and power status detection.
"""

import logging
from datetime import datetime
from typing import Optional

from django.utils import timezone

from core.models import EventType, Heartbeat, Location, PowerEvent, PowerStatus

logger = logging.getLogger('monitoring')

ROUTER_RECONNECT_WINDOW_SECONDS = 5 * 60
ROUTER_RECONNECT_GRACE_SECONDS = 3 * 60


def process_heartbeat(location: Location, received_at: Optional[datetime] = None) -> None:
    """
    Process a heartbeat from a device.
    
    Handles:
    - Recording every heartbeat
    - Starting monitoring on first heartbeat
    - Detecting power restoration after outage
    
    Args:
        location: The location that sent the heartbeat
        received_at: When the heartbeat was received (defaults to now)
    """
    if received_at is None:
        received_at = timezone.now()
    
    Heartbeat.objects.create(location=location, received_at=received_at)

    # Check if this is the first heartbeat (start monitoring)
    if not location.is_monitoring_active:
        _start_monitoring(location, received_at)
        return
    
    # Check if this is a power restoration (was off, now getting heartbeats)
    if location.current_power_status == PowerStatus.OFF:
        _handle_power_restoration(location, received_at)
    
    # Update last heartbeat timestamp
    location.last_heartbeat_at = received_at
    location.save(update_fields=['last_heartbeat_at', 'updated_at'])


def _start_monitoring(location: Location, started_at: datetime) -> None:
    """Start monitoring for a location (first heartbeat received)."""
    logger.info(f"Starting monitoring for {location.name}")
    
    location.monitoring_started_at = started_at
    location.last_heartbeat_at = started_at
    location.current_power_status = PowerStatus.ON
    location.last_status_change_at = started_at
    location.save(update_fields=[
        'monitoring_started_at',
        'last_heartbeat_at',
        'current_power_status',
        'last_status_change_at',
        'updated_at',
    ])
    
    # Create initial power event
    PowerEvent.objects.create(
        location=location,
        event_type=EventType.POWER_ON,
        occurred_at=started_at,
        previous_state_duration_seconds=None,
    )


def _handle_power_restoration(location: Location, restored_at: datetime) -> None:
    """Handle power coming back on after an outage."""
    logger.info(f"Power restored at {location.name}")
    
    # Calculate how long power was off (from last heartbeat before off to first after on)
    duration_seconds = None
    if location.last_status_change_at:
        duration = restored_at - location.last_status_change_at
        duration_seconds = int(duration.total_seconds())
    
    # Update location status
    location.current_power_status = PowerStatus.ON
    location.last_status_change_at = restored_at
    location.save(update_fields=[
        'current_power_status',
        'last_status_change_at',
        'updated_at',
    ])
    
    # Create power event
    event = PowerEvent.objects.create(
        location=location,
        event_type=EventType.POWER_ON,
        occurred_at=restored_at,
        previous_state_duration_seconds=duration_seconds,
    )
    
    # Trigger alert
    if location.alerting_enabled:
        from monitoring.tasks import send_alert
        send_alert(
            location.id,
            EventType.POWER_ON,
            duration_seconds,
            event_id=event.id,
        )


def check_all_locations_for_outages() -> int:
    """
    Check all monitored locations for power outages.
    
    Called periodically by background task.
    
    Returns:
        Number of outages detected
    """
    now = timezone.now()
    outages_detected = 0
    
    # Get all locations with active monitoring and power ON
    locations = Location.objects.filter(
        monitoring_started_at__isnull=False,
        current_power_status=PowerStatus.ON,
    )
    
    for location in locations:
        if _is_location_timed_out(location, now):
            if location.is_offline_detection_disabled:
                continue
            _handle_power_outage(location, now)
            outages_detected += 1
    
    return outages_detected


def _is_location_timed_out(location: Location, now: datetime) -> bool:
    """Check if a location has exceeded its timeout threshold."""
    if not location.last_heartbeat_at:
        return False

    elapsed = (now - location.last_heartbeat_at).total_seconds()
    timeout_seconds = location.timeout_seconds

    if _should_apply_router_reconnect_grace(location):
        timeout_seconds += ROUTER_RECONNECT_GRACE_SECONDS

    return elapsed > timeout_seconds


def _should_apply_router_reconnect_grace(location: Location) -> bool:
    """
    Apply extra grace if heartbeats stopped during the first power-on window.

    This handles router reconnects after power restoration for locations without UPS.
    """
    if not location.is_router_reconnect_window_enabled:
        return False
    if location.current_power_status != PowerStatus.ON:
        return False
    if not location.last_status_change_at or not location.last_heartbeat_at:
        return False

    elapsed_since_on = (
        location.last_heartbeat_at - location.last_status_change_at
    ).total_seconds()
    return elapsed_since_on <= ROUTER_RECONNECT_WINDOW_SECONDS


def _handle_power_outage(location: Location, detected_at: datetime) -> None:
    """Handle a detected power outage."""
    logger.warning(f"Power outage detected at {location.name}")
    
    # Calculate how long power was on (from first heartbeat after on to last before off)
    # The actual outage happened at last_heartbeat_at, not detected_at.
    outage_time = location.last_heartbeat_at or detected_at
    
    duration_seconds = None
    if location.last_status_change_at and location.last_heartbeat_at:
        duration = location.last_heartbeat_at - location.last_status_change_at
        duration_seconds = int(duration.total_seconds())

    if outage_time:
        has_heartbeat = Heartbeat.objects.filter(
            location=location,
            received_at=outage_time,
        ).exists()
        if not has_heartbeat:
            Heartbeat.objects.create(location=location, received_at=outage_time)
    
    # Update location status (use last heartbeat as the actual outage time)
    location.current_power_status = PowerStatus.OFF
    location.last_status_change_at = outage_time
    location.save(update_fields=[
        'current_power_status',
        'last_status_change_at',
        'updated_at',
    ])
    
    # Create power event (occurred at last heartbeat, not detection time)
    event = PowerEvent.objects.create(
        location=location,
        event_type=EventType.POWER_OFF,
        occurred_at=outage_time,
        previous_state_duration_seconds=duration_seconds,
    )
    
    # Trigger alert
    if location.alerting_enabled:
        from monitoring.tasks import send_alert
        send_alert(
            location.id,
            EventType.POWER_OFF,
            duration_seconds,
            event_id=event.id,
        )


def recover_from_restart() -> None:
    """
    Recovery logic after VPS restart.
    
    Checks all locations and resumes monitoring without false alerts.
    """
    logger.info("Running VPS restart recovery")
    
    now = timezone.now()
    
    # Get all locations with active monitoring
    locations = Location.objects.filter(monitoring_started_at__isnull=False)
    
    for location in locations:
        # If power was ON and we've timed out, mark as OFF
        # but don't send alert (we don't know exactly when it went off)
        if location.current_power_status == PowerStatus.ON:
            if _is_location_timed_out(location, now):
                if location.is_offline_detection_disabled:
                    continue
                logger.info(f"Marking {location.name} as offline after restart")
                location.current_power_status = PowerStatus.OFF
                location.last_status_change_at = now
                location.save(update_fields=[
                    'current_power_status',
                    'last_status_change_at',
                    'updated_at',
                ])

                # Create event but don't alert
                PowerEvent.objects.create(
                    location=location,
                    event_type=EventType.POWER_OFF,
                    occurred_at=now,
                    previous_state_duration_seconds=None,
                    alert_sent=True,  # Mark as sent to skip alerting
                    alert_sent_at=now,
                )


