"""
Telegram Bot Client

Wrapper for python-telegram-bot library with retry logic.
"""

import asyncio
import logging
import time
from io import BytesIO
from typing import Optional

from telegram import Bot
from telegram.error import RetryAfter, TelegramError

logger = logging.getLogger('telegram_client')


class TelegramClient:
    """
    Wrapper for Telegram Bot API with retry logic and rate limiting.
    """
    
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1  # seconds
    
    def __init__(self, bot_token: str):
        """
        Initialize the Telegram client.
        
        Args:
            bot_token: Telegram bot token from @BotFather
        """
        self.bot_token = bot_token
        self._bot = None
    
    def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> int:
        """
        Send a text message to a chat.
        
        Args:
            chat_id: Telegram chat/channel ID
            text: Message text (HTML formatting supported)
            parse_mode: Parse mode for formatting (HTML or Markdown)
            disable_notification: Send silently without notification
        
        Returns:
            Message ID of the sent message
        
        Raises:
            TelegramError: If message sending fails after retries
        """
        return self._run_with_retry(
            self._send_message_async,
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )
    
    async def _send_message_async(
        self,
        chat_id: str,
        text: str,
        parse_mode: str,
        disable_notification: bool,
    ) -> int:
        """Async implementation of send_message."""
        bot = Bot(token=self.bot_token)
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )
        return message.message_id

    def delete_message(self, chat_id: str, message_id: int) -> bool:
        """
        Delete a message in a chat.

        Args:
            chat_id: Telegram chat/channel ID
            message_id: ID of message to delete

        Returns:
            True if successful
        """
        return self._run_with_retry(
            self._delete_message_async,
            chat_id=chat_id,
            message_id=message_id,
        )

    async def _delete_message_async(self, chat_id: str, message_id: int) -> bool:
        """Async implementation of delete_message."""
        bot = Bot(token=self.bot_token)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    
    def send_photo(
        self,
        chat_id: str,
        photo: BytesIO,
        caption: Optional[str] = None,
    ) -> int:
        """
        Send a photo to a chat.
        
        Args:
            chat_id: Telegram chat/channel ID
            photo: Photo as BytesIO object
            caption: Optional caption for the photo
        
        Returns:
            Message ID of the sent message
        """
        return self._run_with_retry(
            self._send_photo_async,
            chat_id=chat_id,
            photo=photo,
            caption=caption,
        )
    
    async def _send_photo_async(
        self,
        chat_id: str,
        photo: BytesIO,
        caption: Optional[str],
    ) -> int:
        """Async implementation of send_photo."""
        bot = Bot(token=self.bot_token)
        photo.seek(0)  # Reset to beginning
        message = await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
        )
        return message.message_id
    
    def edit_message_media(
        self,
        chat_id: str,
        message_id: int,
        photo: BytesIO,
    ) -> bool:
        """
        Edit a message to update its photo.
        
        Args:
            chat_id: Telegram chat/channel ID
            message_id: ID of message to edit
            photo: New photo as BytesIO object
        
        Returns:
            True if successful
        """
        return self._run_with_retry(
            self._edit_message_media_async,
            chat_id=chat_id,
            message_id=message_id,
            photo=photo,
        )
    
    async def _edit_message_media_async(
        self,
        chat_id: str,
        message_id: int,
        photo: BytesIO,
    ) -> bool:
        """Async implementation of edit_message_media."""
        from telegram import InputMediaPhoto
        bot = Bot(token=self.bot_token)
        photo.seek(0)
        await bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=InputMediaPhoto(media=photo),
        )
        return True
    
    def pin_message(self, chat_id: str, message_id: int) -> bool:
        """
        Pin a message in a chat.
        
        Args:
            chat_id: Telegram chat/channel ID
            message_id: ID of message to pin
        
        Returns:
            True if successful
        """
        return self._run_with_retry(
            self._pin_message_async,
            chat_id=chat_id,
            message_id=message_id,
        )
    
    async def _pin_message_async(self, chat_id: str, message_id: int) -> bool:
        """Async implementation of pin_message."""
        bot = Bot(token=self.bot_token)
        await bot.pin_chat_message(
            chat_id=chat_id,
            message_id=message_id,
            disable_notification=True,
        )
        return True
    
    def unpin_message(self, chat_id: str, message_id: int) -> bool:
        """
        Unpin a specific message in a chat.
        
        Args:
            chat_id: Telegram chat/channel ID
            message_id: ID of message to unpin
        
        Returns:
            True if successful
        """
        return self._run_with_retry(
            self._unpin_message_async,
            chat_id=chat_id,
            message_id=message_id,
        )
    
    async def _unpin_message_async(self, chat_id: str, message_id: int) -> bool:
        """Async implementation of unpin_message."""
        bot = Bot(token=self.bot_token)
        await bot.unpin_chat_message(
            chat_id=chat_id,
            message_id=message_id,
        )
        return True
    
    def _run_with_retry(self, coro_func, **kwargs):
        """
        Run an async function with retry logic.
        
        Handles rate limiting with exponential backoff.
        """
        retry_delay = self.INITIAL_RETRY_DELAY
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Run the async function
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(coro_func(**kwargs))
                    return result
                finally:
                    asyncio.set_event_loop(None)
                    loop.close()
                    
            except RetryAfter as e:
                # Rate limited - wait the specified time
                wait_time = e.retry_after + 1
                logger.warning(f"Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
                last_exception = e
                
            except TelegramError as e:
                logger.error(f"Telegram error (attempt {attempt + 1}): {e}")
                last_exception = e
                
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        # All retries exhausted
        raise last_exception
