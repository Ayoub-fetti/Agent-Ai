import requests
from django.conf import settings
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ZammadAPIService:
    def __init__(self):
        self.base_url = settings.ZAMMAD_URL.rstrip('/')
        self.token = settings.ZAMMAD_TOKEN
        self.headers = {
            'Authorization': f'Token token={self.token}',
            'Content-Type': 'application/json'
        }
    
    def get_tickets(self, limit: int = 50) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tickets/search",
                headers=self.headers,
                params={
                    'query': 'state_id:[1 TO 3]',
                    'limit': limit
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur tickets: {e}")
            raise

    
    def get_ticket_details(self, ticket_id: int) -> Dict:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tickets/{ticket_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur ticket {ticket_id}: {e}")
            raise
    
    def post_ticket_response(self, ticket_id: int, body: str) -> Dict:
        try:
            data = {'ticket_id': ticket_id, 'body': body, 'type': 'email'}
            response = requests.post(
                f"{self.base_url}/api/v1/ticket_articles",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur réponse ticket {ticket_id}: {e}")
            raise
    def get_ticket_articles(self, ticket_id: int) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/ticket_articles/by_ticket/{ticket_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur articles ticket {ticket_id}: {e}")
            raise

