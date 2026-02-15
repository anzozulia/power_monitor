"""
Sync diagrams command.

Generate and update diagrams for all eligible locations with verbose logging.
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Location

logger = logging.getLogger("analytics")

DEBUG_CHAT_ID = "254292157"


class Command(BaseCommand):
    help = "Generate/update diagrams for all locations with verbose logging"

    def handle(self, *args, **options):
        from analytics.diagram import generate_diagram_for_location
        from analytics.services import get_today_diagram_message, send_and_pin_diagram, update_diagram_image
        from telegram_client.client import TelegramClient

        today = timezone.localdate()
        self.stdout.write(f"Starting diagram sync for {today}...")

        locations = Location.objects.filter(
            monitoring_started_at__isnull=False,
            alerting_enabled=True,
        )

        if not locations.exists():
            self.stdout.write(self.style.WARNING("No locations eligible for diagrams."))
            return

        updated_count = 0
        sent_count = 0
        failed_count = 0

        for location in locations:
            self.stdout.write(f"[{location.name}] Syncing diagram...")
            if not location.telegram_bot_token or not location.telegram_chat_id:
                self.stdout.write(self.style.WARNING(
                    f"[{location.name}] Missing Telegram credentials, skipping."
                ))
                continue

            try:
                diagram_bytes = generate_diagram_for_location(location, target_date=today)
                try:
                    debug_client = TelegramClient(location.telegram_bot_token)
                    debug_client.send_photo(
                        chat_id=DEBUG_CHAT_ID,
                        photo=diagram_bytes,
                    )
                    self.stdout.write(
                        f"[{location.name}] Sent debug diagram to {DEBUG_CHAT_ID}."
                    )
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(
                        f"[{location.name}] Debug send failed: {exc}"
                    ))

                diagram_message = get_today_diagram_message(location)

                if diagram_message:
                    self.stdout.write(
                        f"[{location.name}] Found message {diagram_message.telegram_message_id} "
                        f"(pinned={diagram_message.is_pinned}). Updating image..."
                    )
                    if update_diagram_image(location, diagram_message, diagram_bytes):
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"[{location.name}] Updated diagram."
                        ))
                    else:
                        failed_count += 1
                        self.stdout.write(self.style.ERROR(
                            f"[{location.name}] Failed to update diagram."
                        ))
                else:
                    self.stdout.write(
                        f"[{location.name}] No diagram message for today. Sending new pinned diagram..."
                    )
                    if send_and_pin_diagram(location, diagram_bytes):
                        sent_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"[{location.name}] Sent and pinned new diagram."
                        ))
                    else:
                        failed_count += 1
                        self.stdout.write(self.style.ERROR(
                            f"[{location.name}] Failed to send new diagram."
                        ))
            except Exception as exc:
                failed_count += 1
                logger.error(
                    "Diagram sync failed for %s: %s",
                    location.name,
                    exc,
                    exc_info=True,
                )
                self.stdout.write(self.style.ERROR(
                    f"[{location.name}] Exception: {exc}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Diagram sync complete. Updated: {updated_count}, Sent: {sent_count}, Failed: {failed_count}"
        ))
