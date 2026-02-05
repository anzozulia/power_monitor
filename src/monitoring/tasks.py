"""
Monitoring Background Tasks

Periodic tasks for heartbeat checking and alert sending.
"""

import logging
from uuid import UUID

from django.utils import timezone

from core.models import Location, PowerEvent

logger = logging.getLogger('monitoring')


def check_heartbeats() -> None:
    """
    Periodic task to check for power outages.
    
    Should run every 10 seconds via django.tasks scheduler.
    """
    from monitoring.services import check_all_locations_for_outages
    
    try:
        outages = check_all_locations_for_outages()
        if outages > 0:
            logger.info(f"Detected {outages} outage(s)")
    except Exception as e:
        logger.error(f"Error checking heartbeats: {e}", exc_info=True)


def send_alert(location_id: UUID, event_id: int) -> None:
    """
    Send Telegram alert for a power event.
    
    Args:
        location_id: UUID of the location
        event_id: ID of the power event
    """
    try:
        location = Location.objects.get(id=location_id)
        event = PowerEvent.objects.get(id=event_id)
    except (Location.DoesNotExist, PowerEvent.DoesNotExist) as e:
        logger.error(f"Alert failed - record not found: {e}")
        return
    
    if not location.alerting_enabled:
        logger.info(f"Alerting disabled for {location.name}, skipping")
        return
    
    try:
        from telegram_client.client import TelegramClient
        from telegram_client.formatting import format_power_event_alert
        
        # Format the message
        message = format_power_event_alert(location, event)
        
        # Send via Telegram
        client = TelegramClient(location.telegram_bot_token)
        client.send_message(location.telegram_chat_id, message)
        
        # Mark alert as sent
        event.alert_sent = True
        event.alert_sent_at = timezone.now()
        event.save(update_fields=['alert_sent', 'alert_sent_at'])
        
        # Clear any previous failure flag
        if location.alerting_failed:
            location.alerting_failed = False
            location.save(update_fields=['alerting_failed', 'updated_at'])
        
        logger.info(f"Alert sent for {location.name}: {event.get_event_type_display()}")
        
    except Exception as e:
        logger.error(f"Failed to send alert for {location.name}: {e}", exc_info=True)
        
        # Mark alerting as failed
        location.alerting_failed = True
        location.save(update_fields=['alerting_failed', 'updated_at'])
