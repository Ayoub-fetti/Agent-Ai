import logging
from typing import Dict, Any, Optional
from .zammad_api import ZammadAPIService
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        self.zammad_api = ZammadAPIService()
        self.llm_client = LLMClient()
        
    def suggest_knowledge_article(self, ticket_analysis: Dict[str, Any], ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Suggérer la création d'un article de base de connaissance basé sur l'analyse du ticket"""
        try:
            # Générer le contenu de l'article avec l'IA
            article_content = self._generate_article_content(ticket_analysis, ticket_data)
            
            if not article_content['success']:
                return {'success': False, 'error': article_content['error']}
            
            return {
                'success': True,
                'suggestion': {
                    'title': article_content['title'],
                    'content': article_content['content'],
                    'category': article_content['category'],
                    'should_create': article_content['should_create'],
                    'reason': article_content['reason']
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur suggestion article KB: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_knowledge_article(self, title: str, content: str, category: str = "Procédures Internes", 
                               knowledge_base_id: int = 1) -> Dict[str, Any]:
        """Créer un article dans la base de connaissance Zammad"""
        try:
            # Vérifier/créer la catégorie
            category_id = self._ensure_category_exists(knowledge_base_id, category)
            
            # Créer l'article
            article = self.zammad_api.create_knowledge_base_answer(
                knowledge_base_id=knowledge_base_id,
                title=title,
                content=content,
                category_id=category_id,
                internal=True
            )
            
            return {
                'success': True,
                'article': article,
                'message': f'Article "{title}" créé avec succès dans la base de connaissance'
            }
            
        except Exception as e:
            logger.error(f"Erreur création article KB: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_article_content(self, ticket_analysis: Dict[str, Any], ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Générer le contenu de l'article avec l'IA"""
        
        prompt = f"""
        Analyse ce ticket résolu et détermine s'il mérite un article de base de connaissance.

        TICKET:
        - Titre: {ticket_data.get('title', '')}
        - Catégorie: {ticket_analysis.get('category', '')}
        - Priorité: {ticket_analysis.get('priority_label', '')}
        - Solution: {ticket_analysis.get('ai_response', {}).get('solution_steps', [])}
        - Problème résolu: {ticket_data.get('body', '')}

        CRITÈRES pour créer un article:
        - Problème récurrent ou technique complexe
        - Solution réutilisable pour d'autres cas
        - Procédure interne importante
        - Catégorie technique ou facturation

        RÉPONDS EN JSON:
        {{
            "should_create": true/false,
            "reason": "Pourquoi créer ou ne pas créer l'article",
            "title": "Titre de l'article si création recommandée",
            "content": "Contenu HTML de l'article avec étapes détaillées",
            "category": "Procédures Internes|Solutions Techniques|FAQ Client"
        }}
        """
        
        system_prompt = """Tu es un expert en documentation technique. 
        Crée des articles de base de connaissance clairs et réutilisables.
        Réponds UNIQUEMENT en JSON valide."""
        
        result = self.llm_client.call_api(prompt, system_prompt)
        
        if not result.get('success'):
            return {'success': False, 'error': result.get('error', 'Erreur IA')}
        
        try:
            import json
            # Nettoyer la réponse
            cleaned_response = result['content'].strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            content_data = json.loads(cleaned_response.strip())
            
            return {
                'success': True,
                'should_create': content_data.get('should_create', False),
                'reason': content_data.get('reason', ''),
                'title': content_data.get('title', ''),
                'content': content_data.get('content', ''),
                'category': content_data.get('category', 'Procédures Internes')
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON IA: {e}")
            return {'success': False, 'error': 'Réponse IA invalide'}
    
    def _ensure_category_exists(self, knowledge_base_id: int, category_name: str) -> int:
        """S'assurer qu'une catégorie existe, la créer sinon"""
        try:
            # Récupérer les catégories existantes
            categories = self.zammad_api.get_knowledge_base_categories(knowledge_base_id)
            
            # Chercher la catégorie
            for category in categories:
                if category.get('title') == category_name:
                    return category['id']
            
            # Créer la catégorie si elle n'existe pas
            new_category = self.zammad_api.create_knowledge_base_category(
                knowledge_base_id, category_name
            )
            return new_category['id']
            
        except Exception as e:
            logger.error(f"Erreur gestion catégorie {category_name}: {e}")
            # Retourner un ID par défaut ou lever l'exception
            return 1  # ID de catégorie par défaut
