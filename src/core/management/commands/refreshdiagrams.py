"""
Refresh diagrams command.

Regenerates and updates today's diagram for all eligible locations with logging.
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Location

logger = logging.getLogger("analytics")


class Command(BaseCommand):
    help = "Regenerate and update today's diagrams for all locations with logs"

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write(f"Refreshing diagrams for {today}...")

        from analytics.diagram import generate_diagram_for_location
        from analytics.services import get_today_diagram_message, send_and_pin_diagram, update_diagram_image

        locations = Location.objects.filter(
            monitoring_started_at__isnull=False,
            alerting_enabled=True,
        )

        if not locations.exists():
            self.stdout.write(self.style.WARNING("No locations eligible for diagrams."))
            return

        updated = 0
        sent = 0
        failed = 0

        for location in locations:
            self.stdout.write(f"Location: {location.name}")
            if not location.telegram_bot_token or not location.telegram_chat_id:
                self.stdout.write(self.style.ERROR("  Missing bot token or chat ID."))
                failed += 1
                continue

            try:
                diagram_bytes = generate_diagram_for_location(location, target_date=today)
                diagram_message = get_today_diagram_message(location)

                if diagram_message:
                    self.stdout.write(
                        f"  Found diagram message {diagram_message.telegram_message_id} (pinned={diagram_message.is_pinned})"
                    )
                    if update_diagram_image(location, diagram_message, diagram_bytes):
                        updated += 1
                        self.stdout.write(self.style.SUCCESS("  Updated diagram image."))
                    else:
                        failed += 1
                        self.stdout.write(self.style.ERROR("  Failed to update diagram image."))
                else:
                    self.stdout.write("  No diagram message found for today. Sending new one...")
                    if send_and_pin_diagram(location, diagram_bytes):
                        sent += 1
                        self.stdout.write(self.style.SUCCESS("  Sent and pinned new diagram."))
                    else:
                        failed += 1
                        self.stdout.write(self.style.ERROR("  Failed to send new diagram."))

            except Exception as exc:
                failed += 1
                logger.error(
                    "Diagram refresh failed for %s: %s",
                    location.name,
                    exc,
                    exc_info=True,
                )
                self.stdout.write(self.style.ERROR(f"  Error: {exc}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated: {updated}, Sent: {sent}, Failed: {failed}."
            )
        )
