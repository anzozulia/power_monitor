"""
Send Diagram Command

Manually trigger diagram generation and sending for a location.
"""

from django.core.management.base import BaseCommand, CommandError

from core.models import Location


class Command(BaseCommand):
    help = 'Generate and send a diagram for a specific location'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'location',
            type=str,
            help='Location name or UUID',
        )
        parser.add_argument(
            '--save-local',
            type=str,
            help='Save diagram to local file instead of sending to Telegram',
        )
        parser.add_argument(
            '--no-pin',
            action='store_true',
            help='Send without pinning the message',
        )
    
    def handle(self, *args, **options):
        location_identifier = options['location']
        save_local = options.get('save_local')
        no_pin = options.get('no_pin', False)
        
        # Find the location
        location = None
        
        # Try by name first (most common use case)
        try:
            location = Location.objects.get(name=location_identifier)
        except Location.DoesNotExist:
            pass
        
        # Try UUID if name didn't work
        if location is None:
            try:
                import uuid
                uuid_val = uuid.UUID(location_identifier)
                location = Location.objects.get(pk=uuid_val)
            except (ValueError, Location.DoesNotExist):
                pass
        
        if location is None:
            raise CommandError(f'Location not found: {location_identifier}')
        
        self.stdout.write(f'Generating diagram for: {location.name}')
        
        # Generate the diagram
        from analytics.diagram import generate_diagram_for_location
        diagram_bytes = generate_diagram_for_location(location)
        
        if save_local:
            # Save to local file
            with open(save_local, 'wb') as f:
                f.write(diagram_bytes.read())
            self.stdout.write(self.style.SUCCESS(f'Diagram saved to: {save_local}'))
            return
        
        # Check if Telegram is configured
        if 'MOCK' in location.telegram_bot_token or 'MOCK' in location.telegram_chat_id:
            self.stdout.write(self.style.ERROR(
                'Telegram credentials not configured! Update telegram_bot_token and telegram_chat_id first.'
            ))
            self.stdout.write('Use --save-local <filename> to save the diagram locally instead.')
            return
        
        # Send to Telegram
        from analytics.services import send_and_pin_diagram, send_diagram_without_pin
        
        try:
            if no_pin:
                result = send_diagram_without_pin(location, diagram_bytes)
                self.stdout.write(self.style.SUCCESS(
                    f'Diagram sent (not pinned). Message ID: {result}'
                ))
            else:
                result = send_and_pin_diagram(location, diagram_bytes)
                self.stdout.write(self.style.SUCCESS(
                    f'Diagram sent and pinned! Message ID: {result.telegram_message_id}'
                ))
        except Exception as e:
            raise CommandError(f'Failed to send diagram: {e}')
