"""
Generate Mock Data Command

Creates a test location with realistic power event data for testing diagrams.
"""

import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import EventType, Heartbeat, Location, PowerEvent, PowerStatus


class Command(BaseCommand):
    help = 'Generate mock location with power event data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Test Location',
            help='Name of the mock location',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=5,
            help='Number of days of data to generate',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            default='2026-01-31',
            help='Start date in YYYY-MM-DD format',
        )
    
    def handle(self, *args, **options):
        name = options['name']
        days = options['days']
        start_date_str = options['start_date']
        
        # Parse start date
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        self.stdout.write(f'Creating mock location: {name}')
        self.stdout.write(f'Generating {days} days of data from {start_date}')
        
        # Create or get the location
        location, created = Location.objects.get_or_create(
            name=name,
            defaults={
                'heartbeat_period_seconds': 60,
                'grace_period_seconds': 30,
                'telegram_bot_token': 'MOCK_TOKEN_REPLACE_ME',
                'telegram_chat_id': 'MOCK_CHAT_ID_REPLACE_ME',
            }
        )
        
        if not created:
            self.stdout.write(self.style.WARNING(f'Location "{name}" already exists, clearing old data...'))
            # Clear existing events and heartbeats
            PowerEvent.objects.filter(location=location).delete()
            Heartbeat.objects.filter(location=location).delete()
        
        # Set monitoring start time
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        location.monitoring_started_at = start_datetime
        location.last_heartbeat_at = start_datetime
        location.current_power_status = PowerStatus.ON
        location.last_status_change_at = start_datetime
        location.save()
        
        # Create initial power on event
        PowerEvent.objects.create(
            location=location,
            event_type=EventType.POWER_ON,
            occurred_at=start_datetime,
            previous_state_duration_seconds=None,
        )
        
        # Generate power events
        current_time = start_datetime
        end_time = timezone.now()
        current_status = PowerStatus.ON
        events_created = 0
        
        while current_time < end_time:
            # Random time until next event (1-8 hours)
            hours_until_event = random.uniform(1, 8)
            current_time += timedelta(hours=hours_until_event)
            
            if current_time >= end_time:
                break
            
            # Toggle status
            if current_status == PowerStatus.ON:
                new_status = PowerStatus.OFF
                event_type = EventType.POWER_OFF
            else:
                new_status = PowerStatus.ON
                event_type = EventType.POWER_ON
            
            # Calculate duration
            duration_seconds = int(hours_until_event * 3600)
            
            # Create event
            PowerEvent.objects.create(
                location=location,
                event_type=event_type,
                occurred_at=current_time,
                previous_state_duration_seconds=duration_seconds,
                alert_sent=True,
                alert_sent_at=current_time,
            )
            
            current_status = new_status
            events_created += 1
            
            # For power off events, add a shorter duration (30min - 3hrs)
            if current_status == PowerStatus.OFF:
                outage_hours = random.uniform(0.5, 3)
                current_time += timedelta(hours=outage_hours)
                
                if current_time >= end_time:
                    break
                
                # Power back on
                PowerEvent.objects.create(
                    location=location,
                    event_type=EventType.POWER_ON,
                    occurred_at=current_time,
                    previous_state_duration_seconds=int(outage_hours * 3600),
                    alert_sent=True,
                    alert_sent_at=current_time,
                )
                current_status = PowerStatus.ON
                events_created += 1
        
        # Update location with final status
        location.current_power_status = current_status
        location.last_status_change_at = current_time if current_time < end_time else end_time
        location.last_heartbeat_at = timezone.now()
        location.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Created {events_created} power events for "{name}"'
        ))
        self.stdout.write(f'Location ID: {location.id}')
        self.stdout.write(f'API Key: {location.api_key}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'Remember to update telegram_bot_token and telegram_chat_id before sending diagrams!'
        ))
