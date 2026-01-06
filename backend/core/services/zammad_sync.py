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
            
            logger.info(f"Received {len(tickets_data)} tickets from API")
            
            for ticket_data in tickets_data:
                state = str(ticket_data.get('state', '')).lower()
                logger.info(f"Ticket {ticket_data.get('id')}: state={state}")
                
                if state in ['closed', 'fermé']:
                    continue
                    
                if not Ticket.objects.filter(zammad_id=ticket_data['id']).exists():
                    ticket = self._map_zammad_to_model(ticket_data)
                    ticket.save()
                    synced_count += 1
            
            return synced_count
        except Exception as e:
            logger.error(f"Erreur sync: {e}")
            raise
    
    def _map_zammad_to_model(self, data: dict) -> Ticket:
        # Mapping des statuts Zammad vers Agent AI
        zammad_status = str(data.get('state', '')).lower()
        
        status_mapping = {
            'new': 'nouveau',
            'nouveau': 'nouveau',
            'open': 'ouvert',
            'ouvert': 'ouvert',
            'pending reminder': 'rappel_en_attente',
            'rappel en attente': 'rappel_en_attente',
            'pending close': 'en_attente_de_cloture',
            'en attente de clôture': 'en_attente_de_cloture',
            'closed': 'cloture',
            'fermé': 'cloture',
            'cloture': 'cloture'
        }
        
        mapped_status = status_mapping.get(zammad_status, 'nouveau')
        
        return Ticket(
            zammad_id=data['id'],
            title=data.get('title', ''),
            body=data.get('body', ''),
            status=mapped_status,  # Utiliser le statut mappé
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
