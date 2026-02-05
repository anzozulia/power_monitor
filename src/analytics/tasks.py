"""
Analytics Background Tasks

Scheduled tasks for diagram generation and updates.
"""

import logging
from datetime import timedelta

from django.utils import timezone

from core.models import Location

logger = logging.getLogger('analytics')


def generate_daily_diagrams() -> None:
    """
    Generate and send daily diagrams for all locations.
    
    Should run at 00:00 Kyiv time.
    """
    from analytics.diagram import generate_diagram_for_location
    from analytics.services import (
        get_yesterday_pinned_diagram,
        send_and_pin_diagram,
        unpin_diagram,
        update_diagram_image,
    )
    
    logger.info("Starting daily diagram generation")
    
    # Get all locations with active monitoring
    locations = Location.objects.filter(
        monitoring_started_at__isnull=False,
        alerting_enabled=True,
    )
    
    for location in locations:
        try:
            # Step 1: Update yesterday's diagram one final time
            yesterday_diagram = get_yesterday_pinned_diagram(location)
            if yesterday_diagram:
                yesterday = timezone.localdate() - timedelta(days=1)
                diagram_bytes = generate_diagram_for_location(location, target_date=yesterday)
                update_diagram_image(location, yesterday_diagram, diagram_bytes)
                
                # Step 2: Unpin yesterday's diagram
                unpin_diagram(location, yesterday_diagram)
            
            # Step 3: Generate and send new diagram
            diagram_bytes = generate_diagram_for_location(location, target_date=timezone.localdate())
            send_and_pin_diagram(location, diagram_bytes)
            
            logger.info(f"Daily diagram complete for {location.name}")
            
        except Exception as e:
            logger.error(f"Failed daily diagram for {location.name}: {e}", exc_info=True)
    
    logger.info("Daily diagram generation complete")


def update_hourly_diagrams() -> None:
    """
    Update all pinned diagrams with fresh data.
    
    Should run every 15 minutes at :15/:30/:45.
    """
    from analytics.diagram import generate_diagram_for_location
    from analytics.services import get_today_diagram_message, update_diagram_image
    
    logger.debug("Starting hourly diagram update")
    
    # Get all locations with active monitoring
    locations = Location.objects.filter(
        monitoring_started_at__isnull=False,
        alerting_enabled=True,
    )
    
    updated_count = 0
    
    for location in locations:
        try:
            # Get today's diagram message
            diagram_message = get_today_diagram_message(location)
            
            if diagram_message and diagram_message.is_pinned:
                # Generate fresh diagram
                diagram_bytes = generate_diagram_for_location(location)
                
                # Update the message
                if update_diagram_image(location, diagram_message, diagram_bytes):
                    updated_count += 1
            
        except Exception as e:
            logger.error(f"Failed hourly update for {location.name}: {e}", exc_info=True)
    
    logger.debug(f"Hourly diagram update complete: {updated_count} updated")
