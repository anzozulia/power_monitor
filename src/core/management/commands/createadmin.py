"""
Create Admin User Command

Creates the admin user from environment variables if it doesn't exist.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create admin user from environment variables'
    
    def handle(self, *args, **options):
        User = get_user_model()
        
        username = getattr(settings, 'ADMIN_USERNAME', None)
        password = getattr(settings, 'ADMIN_PASSWORD', None)
        
        if not username or not password:
            self.stderr.write(
                self.style.ERROR(
                    'ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment'
                )
            )
            return
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists')
            )
            return
        
        User.objects.create_superuser(
            username=username,
            password=password,
            email='',
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin user "{username}"')
        )
