"""
Telegram Alert Message Formatting

Creates styled messages for power events.
"""

from core.i18n import get_alert_strings
from core.models import EventType, Location, PowerEvent


def format_power_event_alert(location: Location, event: PowerEvent) -> str:
    """
    Format a power event as a styled Telegram message.
    
    Args:
        location: The location where the event occurred
        event: The power event to format
    
    Returns:
        HTML-formatted message string
    """
    return format_power_status_alert(
        location,
        event.event_type,
        event.previous_state_duration_seconds,
    )


def format_power_status_alert(
    location: Location,
    event_type: EventType,
    previous_state_duration_seconds: int | None,
) -> str:
    """Format a power status alert from heartbeat-derived data."""
    if event_type == EventType.POWER_OFF:
        return format_power_off_alert(location, previous_state_duration_seconds)
    return format_power_on_alert(location, previous_state_duration_seconds)


def format_power_off_alert(
    location: Location,
    previous_state_duration_seconds: int | None,
) -> str:
    """
    Format a power outage alert.
    
    Example output:
    🔴 POWER OFF
    
    Power was ON for: 5h 23m
    """
    strings = get_alert_strings(location.alert_language)
    duration_text = _format_duration(previous_state_duration_seconds, strings)

    message = f"🔴 <b>{strings['power_off']}</b>\n"

    if duration_text:
        message += f"\n⚡ {strings['power_was_on_for']}: <b>{duration_text}</b>"

    return message


def format_power_on_alert(
    location: Location,
    previous_state_duration_seconds: int | None,
) -> str:
    """
    Format a power restoration alert.
    
    Example output:
    🟢 POWER ON
    
    Power was OFF for: 3h 15m
    """
    strings = get_alert_strings(location.alert_language)
    duration_text = _format_duration(previous_state_duration_seconds, strings)

    message = f"🟢 <b>{strings['power_on']}</b>\n"

    if duration_text:
        message += f"\n⚡ {strings['power_was_off_for']}: <b>{duration_text}</b>"

    return message


def _format_duration(seconds: int | None, strings: dict) -> str | None:
    """
    Format a duration in seconds as human-readable string.
    
    Args:
        seconds: Duration in seconds, or None
    
    Returns:
        Formatted string like "5h 23m" or None if input is None
    """
    if seconds is None:
        return None
    
    unit_s = strings["unit_s"]
    unit_m = strings["unit_m"]
    unit_h = strings["unit_h"]

    if seconds < 60:
        return f"{seconds}{unit_s}"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        if secs > 0:
            return f"{minutes}{unit_m} {secs}{unit_s}"
        return f"{minutes}{unit_m}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}{unit_h} {minutes}{unit_m}"
        return f"{hours}{unit_h}"


