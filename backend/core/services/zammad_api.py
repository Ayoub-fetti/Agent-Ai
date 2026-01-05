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
    def create_internal_article(self, ticket_id: int, subject: str, body: str) -> Dict:
        try:
            data = {
                'ticket_id': ticket_id,
                'subject': subject,
                'body': body,
                'content_type': 'text/html',
                'type': 'note',
                'internal': True,
                'sender': 'Agent'
            }
            response = requests.post(
                f"{self.base_url}/api/v1/ticket_articles",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur création article interne ticket {ticket_id}: {e}")
            raise
            # Ajout dans zammad_api.py

    def create_knowledge_base_answer(self, knowledge_base_id: int, title: str, content: str, internal: bool = True) -> Dict:
        """Créer un article dans la base de connaissance"""
        try:
            data = {
                "kb_locale_id": 1,
                "title": title,
                "content": content
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/knowledge_bases/{knowledge_base_id}/answers",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            # Rendre interne si demandé
            if internal and result.get('id'):
                self.make_answer_internal(knowledge_base_id, result['id'])
            
            return result
        except requests.RequestException as e:
            logger.error(f"Erreur création answer KB: {e}")
            raise

    def make_answer_internal(self, knowledge_base_id: int, answer_id: int) -> Dict:
        """Rendre un article interne"""
        try:
            from datetime import datetime
            data = {"internal_at": datetime.now().isoformat() + "Z"}
            
            response = requests.patch(
                f"{self.base_url}/api/v1/knowledge_bases/{knowledge_base_id}/answers/{answer_id}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur rendre interne: {e}")
            raise


