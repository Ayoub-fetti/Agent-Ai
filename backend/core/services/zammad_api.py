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
    
    def get_tickets(self, limit: int = 1000) -> List[Dict]:
        try:
            all_tickets = []
            page = 1
            per_page = 100
            
            while len(all_tickets) < limit:
                response = requests.get(
                    f"{self.base_url}/api/v1/tickets",
                    headers=self.headers,
                    params={'page': page, 'per_page': per_page}
                )
                response.raise_for_status()
                tickets = response.json()
                
                if not tickets:  # Plus de tickets
                    break
                    
                # Filtrer pour états 1, 2, 3 seulement
                filtered = [t for t in tickets if t.get('state_id') in [1, 2, 3]]
                all_tickets.extend(filtered)
                page += 1
                
            return all_tickets[:limit]
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
    def create_knowledge_base_category(self, title: str, icon: str = "f115") -> Dict:
        """Créer une nouvelle catégorie dans la base de connaissance"""
        try:
            data = {
                "category_icon": icon,
                "parent_id": "",
                "translations_attributes": [
                    {
                        "content_attributes": {
                            "body": ""
                        },
                        "kb_locale_id": 1,
                        "title": title
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/knowledge_bases/1/categories",
                headers=self.headers,
                json=data
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Erreur création catégorie KB: {e}")
            raise

    def get_or_create_ai_category(self) -> int:
        """Obtenir ou créer la catégorie 'Agent-AI'"""
        try:
            # Essayer de créer la catégorie Agent-AI
            category = self.create_knowledge_base_category("Agent-AI", "f085")
            return category.get('id', 1)
        except:
            # Si elle existe déjà, utiliser l'ID par défaut ou chercher
            return 1  # Fallback sur catégorie existante
