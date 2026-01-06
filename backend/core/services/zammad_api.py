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
    
    def get_tickets(self, limit: int = 500) -> List[Dict]:
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

    def get_knowledge_base_init(self) -> Dict:
        """Initialiser et récupérer la structure KB"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/knowledge_bases/init",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur KB init: {e}")
            raise

    def create_knowledge_base_answer(self, category_id: int, title: str, content: str, internal: bool = True) -> Dict:
        """Créer un article dans la base de connaissance - Format Zammad correct"""
        try:
            data = {
                "category_id": category_id,
                "translations_attributes": [
                    {
                        "content_attributes": {
                            "body": content
                        },
                        "kb_locale_id": 1,
                        "title": title
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/knowledge_bases/1/answers",  # ID de votre KB = 1
                headers=self.headers,
                json=data
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Rendre l'article interne si demandé
            if internal and result.get('id'):
                requests.post(
                    f"{self.base_url}/api/v1/knowledge_bases/1/answers/{result['id']}/internal",
                    headers=self.headers
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur création answer KB: {e}")
            raise

    def make_answer_internal(self, answer_id: int) -> Dict:
        """Rendre un article interne"""
        try:
            from datetime import datetime
            data = {"internal_at": datetime.now().isoformat() + "Z"}
            
            response = requests.patch(
                f"{self.base_url}/api/v1/knowledge_bases/answers/{answer_id}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur rendre interne: {e}")
            raise
