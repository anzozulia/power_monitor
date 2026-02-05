"""
Startup Command

Run on application startup to recover state after restarts.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import ProgrammingError


class Command(BaseCommand):
    help = 'Run startup tasks (state recovery after restart)'
    
    def handle(self, *args, **options):
        # Check if tables exist before running recovery
        if not self._tables_exist():
            self.stdout.write(
                self.style.WARNING('Database tables not yet created, skipping startup recovery')
            )
            return
        
        self.stdout.write('Running startup recovery...')
        
        from monitoring.services import cleanup_non_valuable_heartbeats, recover_from_restart
        recover_from_restart()
        cleanup_non_valuable_heartbeats()
        
        self.stdout.write(
            self.style.SUCCESS('Startup recovery complete')
        )
    
    def _tables_exist(self) -> bool:
        """Check if core_location table exists."""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'core_location')"
                )
                return cursor.fetchone()[0]
        except ProgrammingError:
            return False
