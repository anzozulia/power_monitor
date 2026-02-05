"""
Background Worker Command

Runs scheduled background tasks:
- Heartbeat checks every 5 seconds
- Hourly diagram updates
- Daily diagram generation at midnight
"""

import logging
import signal
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger('worker')

# Configuration
HEARTBEAT_CHECK_INTERVAL = 5  # seconds


class Command(BaseCommand):
    help = 'Run background worker for scheduled tasks'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = True
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting background worker...'))
        
        # Set up graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        
        last_heartbeat_check = time.time()
        last_hourly_update = -1
        last_daily_run = None
        
        # Avoid running daily diagrams on boot before midnight hour
        if timezone.now().hour != 0:
            last_daily_run = timezone.now().date()

        # Run initial heartbeat check immediately
        self._run_heartbeat_check()
        
        while self.running:
            try:
                now = timezone.now()
                current_hour = now.hour
                current_date = now.date()
                current_time = time.time()
                
                # Run heartbeat checks every 5 seconds
                if current_time - last_heartbeat_check >= HEARTBEAT_CHECK_INTERVAL:
                    last_heartbeat_check = current_time
                    self._run_heartbeat_check()
                
                # Run hourly diagram update once per hour (catch up if missed :00)
                if current_hour != last_hourly_update:
                    last_hourly_update = current_hour
                    self._run_hourly_diagrams()

                # Run daily diagrams during the midnight hour
                if current_hour == 0 and last_daily_run != current_date:
                    last_daily_run = current_date
                    self._run_daily_diagrams()
                
                # Sleep for 1 second before next iteration
                time.sleep(1)
                
            except Exception as e:
                logger.exception(f'Worker error: {e}')
                time.sleep(5)  # Wait before retrying on error
        
        self.stdout.write(self.style.SUCCESS('Worker shutdown complete'))
    
    def _handle_signal(self, signum, frame):
        self.stdout.write('Received shutdown signal, stopping...')
        self.running = False
    
    def _run_heartbeat_check(self):
        """Check all locations for missed heartbeats."""
        try:
            from monitoring.services import check_all_locations_for_outages
            check_all_locations_for_outages()
            logger.debug('Heartbeat check completed')
        except Exception as e:
            logger.exception(f'Heartbeat check failed: {e}')
    
    def _run_hourly_diagrams(self):
        """Update hourly diagrams for all locations."""
        try:
            from analytics.tasks import update_hourly_diagrams
            update_hourly_diagrams()
            logger.info('Hourly diagram update completed')
        except Exception as e:
            logger.exception(f'Hourly diagram update failed: {e}')
    
    def _run_daily_diagrams(self):
        """Generate and send daily diagrams for all locations."""
        try:
            from analytics.tasks import generate_daily_diagrams
            generate_daily_diagrams()
            logger.info('Daily diagram generation completed')
        except Exception as e:
            logger.exception(f'Daily diagram generation failed: {e}')
