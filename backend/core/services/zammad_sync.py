from django.utils import timezone
from datetime import datetime
from core.models import Ticket
from .zammad_api import ZammadAPIService
import logging

logger = logging.getLogger(__name__)

class ZammadSyncService:
    def __init__(self):
        self.api = ZammadAPIService()
    
    def sync_new_tickets(self) -> int:
        try:
            tickets_data = self.api.get_tickets()
            synced_count = 0
            
            for ticket_data in tickets_data:
                if not Ticket.objects.filter(zammad_id=ticket_data['id']).exists():
                    ticket = self._map_zammad_to_model(ticket_data)
                    ticket.save()
                    synced_count += 1
            
            return synced_count
        except Exception as e:
            logger.error(f"Erreur sync: {e}")
            raise
    
    def _map_zammad_to_model(self, data: dict) -> Ticket:
        return Ticket(
            zammad_id=data['id'],
            title=data.get('title', ''),
            body=data.get('body', ''),
            status=data.get('state', 'new'),
            customer_email=data.get('customer', {}).get('email', ''),
            created_at=self._parse_datetime(data.get('created_at')),
            updated_at=self._parse_datetime(data.get('updated_at'))
        )
    
    def _parse_datetime(self, date_str: str) -> datetime:
        if date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return timezone.now()
    
    def mark_ticket_processed(self, ticket_id: int):
        try:
            ticket = Ticket.objects.get(zammad_id=ticket_id)
            ticket.processed = True
            ticket.save()
        except Ticket.DoesNotExist:
            pass
