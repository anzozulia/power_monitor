"""
Reset diagrams command.

Clears all diagram records and sends fresh pinned diagrams.
"""

import logging

from django.core.management.base import BaseCommand

from core.models import DiagramMessage, Location

logger = logging.getLogger("analytics")


class Command(BaseCommand):
    help = "Reset diagram records and send fresh pinned diagrams for all locations"

    def handle(self, *args, **options):
        self.stdout.write("Clearing diagram records...")
        DiagramMessage.objects.all().delete()

        from analytics.diagram import generate_diagram_for_location
        from analytics.services import send_and_pin_diagram

        locations = Location.objects.filter(
            monitoring_started_at__isnull=False,
            alerting_enabled=True,
        )

        if not locations.exists():
            self.stdout.write(self.style.WARNING("No locations eligible for diagrams."))
            return

        sent_count = 0
        for location in locations:
            try:
                diagram_bytes = generate_diagram_for_location(location)
                if send_and_pin_diagram(location, diagram_bytes):
                    sent_count += 1
            except Exception as exc:
                logger.error(
                    "Failed to reset diagram for %s: %s",
                    location.name,
                    exc,
                    exc_info=True,
                )

        self.stdout.write(self.style.SUCCESS(f"Sent {sent_count} fresh diagrams."))
