from django.core.management.base import BaseCommand
from core.services.zammad_sync import ZammadSyncService

class Command(BaseCommand):
    help = 'Synchronise les tickets depuis Zammad'
    
    def handle(self, *args, **options):
        sync_service = ZammadSyncService()
        try:
            count = sync_service.sync_new_tickets()
            self.stdout.write(f'{count} tickets synchronisés')
        except Exception as e:
            self.stdout.write(f'Erreur: {e}')
