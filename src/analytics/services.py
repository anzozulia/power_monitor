"""
Analytics Services

Diagram message management and Telegram integration.
"""

import logging
from datetime import date, timedelta
from typing import Optional

from django.utils import timezone

from core.i18n import get_diagram_caption
from core.models import DiagramMessage, Location

logger = logging.getLogger('analytics')


def get_today_diagram_message(location: Location) -> Optional[DiagramMessage]:
    """
    Get today's diagram message for a location if it exists.
    
    Args:
        location: The location to check
    
    Returns:
        DiagramMessage if exists, None otherwise
    """
    today = timezone.localdate()
    try:
        return DiagramMessage.objects.get(location=location, diagram_date=today)
    except DiagramMessage.DoesNotExist:
        return None


def create_diagram_message(
    location: Location,
    telegram_message_id: int,
    diagram_date: date,
    is_pinned: bool = False,
) -> DiagramMessage:
    """
    Create a new diagram message record.
    
    Args:
        location: The location
        telegram_message_id: Telegram's message ID
        diagram_date: Date of the diagram
        is_pinned: Whether the message is pinned
    
    Returns:
        Created DiagramMessage
    """
    return DiagramMessage.objects.create(
        location=location,
        telegram_message_id=telegram_message_id,
        diagram_date=diagram_date,
        is_pinned=is_pinned,
    )


def update_diagram_message_pinned(diagram_message: DiagramMessage, is_pinned: bool) -> None:
    """
    Update the pinned status of a diagram message.
    
    Args:
        diagram_message: The diagram message to update
        is_pinned: New pinned status
    """
    diagram_message.is_pinned = is_pinned
    diagram_message.save(update_fields=['is_pinned', 'last_updated_at'])


def get_yesterday_pinned_diagram(location: Location) -> Optional[DiagramMessage]:
    """
    Get yesterday's pinned diagram message for a location.
    
    Args:
        location: The location to check
    
    Returns:
        DiagramMessage if exists and is pinned, None otherwise
    """
    yesterday = timezone.localdate() - timedelta(days=1)
    try:
        diagram = DiagramMessage.objects.get(
            location=location,
            diagram_date=yesterday,
            is_pinned=True,
        )
        return diagram
    except DiagramMessage.DoesNotExist:
        return None


def send_and_pin_diagram(location: Location, diagram_bytes) -> Optional[DiagramMessage]:
    """
    Send a diagram to Telegram and pin it.
    
    Args:
        location: The location
        diagram_bytes: BytesIO containing the PNG image
    
    Returns:
        Created DiagramMessage, or None if failed
    """
    from telegram_client.client import TelegramClient
    
    try:
        client = TelegramClient(location.telegram_bot_token)
        
        # Send the photo
        today = timezone.localdate()
        caption_text = get_diagram_caption(location.alert_language)
        caption = f"📊 {caption_text} - {location.name} ({today.strftime('%d.%m.%Y')})"
        message_id = client.send_photo(
            chat_id=location.telegram_chat_id,
            photo=diagram_bytes,
            caption=caption,
        )
        
        # Pin the message
        client.pin_message(
            chat_id=location.telegram_chat_id,
            message_id=message_id,
        )
        
        # Create record
        diagram_message = create_diagram_message(
            location=location,
            telegram_message_id=message_id,
            diagram_date=today,
            is_pinned=True,
        )
        
        logger.info(f"Sent and pinned diagram for {location.name}")
        return diagram_message
        
    except Exception as e:
        logger.error(f"Failed to send diagram for {location.name}: {e}", exc_info=True)
        return None


def send_diagram_without_pin(location: Location, diagram_bytes) -> Optional[int]:
    """
    Send a diagram to Telegram without pinning it.
    
    Args:
        location: The location
        diagram_bytes: BytesIO containing the PNG image
    
    Returns:
        Telegram message ID, or None if failed
    """
    from telegram_client.client import TelegramClient
    
    try:
        client = TelegramClient(location.telegram_bot_token)
        
        # Send the photo
        today = timezone.localdate()
        caption_text = get_diagram_caption(location.alert_language)
        caption = f"📊 {caption_text} - {location.name} ({today.strftime('%d.%m.%Y')})"
        message_id = client.send_photo(
            chat_id=location.telegram_chat_id,
            photo=diagram_bytes,
            caption=caption,
        )
        
        logger.info(f"Sent diagram (not pinned) for {location.name}")
        return message_id
        
    except Exception as e:
        logger.error(f"Failed to send diagram for {location.name}: {e}", exc_info=True)
        return None


def update_diagram_image(location: Location, diagram_message: DiagramMessage, diagram_bytes) -> bool:
    """
    Update an existing diagram message with a new image.
    
    Args:
        location: The location
        diagram_message: The diagram message to update
        diagram_bytes: BytesIO containing the new PNG image
    
    Returns:
        True if successful, False otherwise
    """
    from telegram_client.client import TelegramClient
    
    try:
        client = TelegramClient(location.telegram_bot_token)
        
        client.edit_message_media(
            chat_id=location.telegram_chat_id,
            message_id=diagram_message.telegram_message_id,
            photo=diagram_bytes,
        )
        
        diagram_message.last_updated_at = timezone.now()
        diagram_message.save(update_fields=['last_updated_at'])
        
        logger.debug(f"Updated diagram for {location.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update diagram for {location.name}: {e}", exc_info=True)
        return False


def unpin_diagram(location: Location, diagram_message: DiagramMessage) -> bool:
    """
    Unpin a diagram message.
    
    Args:
        location: The location
        diagram_message: The diagram message to unpin
    
    Returns:
        True if successful, False otherwise
    """
    from telegram_client.client import TelegramClient
    
    try:
        client = TelegramClient(location.telegram_bot_token)
        
        client.unpin_message(
            chat_id=location.telegram_chat_id,
            message_id=diagram_message.telegram_message_id,
        )
        
        update_diagram_message_pinned(diagram_message, is_pinned=False)
        
        logger.info(f"Unpinned diagram for {location.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to unpin diagram for {location.name}: {e}", exc_info=True)
        return False
