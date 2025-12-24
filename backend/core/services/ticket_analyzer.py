import json
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from ..models import Ticket, TicketAnalysis
from .llm_client import LLMClient
from .zammad_api import ZammadAPIService

logger = logging.getLogger(__name__)

class TicketAnalyzerService:
    def __init__(self):
        self.llm_client = LLMClient()
        self.zammad_api = ZammadAPIService()
    
    def analyze_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """6.1 Analyse ticket - Processus complet d'analyse"""
        try:
            # Envoyer contenu au LLM
            analysis_result = self._send_to_llm(ticket)
            if not analysis_result['success']:
                return {'success': False, 'error': analysis_result['error']}
            
            # Détecter intention et classifier
            parsed_analysis = self._parse_analysis(analysis_result['content'])
            
            # Définir priorité et générer réponse
            ai_response = self._generate_response(ticket, parsed_analysis)
            
            # 6.2 Stockage résultats IA
            analysis = self._save_analysis(ticket, parsed_analysis, ai_response)
            
            return {
                'success': True,
                'analysis': analysis,
                'ready_for_publish': True
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse ticket {ticket.zammad_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _send_to_llm(self, ticket: Ticket) -> Dict[str, Any]:
        """Envoi du contenu ticket au LLM"""
        
        # Récupérer tous les articles du ticket
        try:
            articles = self.zammad_api.get_ticket_articles(ticket.zammad_id)
            full_content = self._build_full_content(ticket, articles)
        except Exception as e:
            logger.warning(f"Impossible de récupérer les articles: {e}")
            full_content = ticket.body
        
        prompt = f"""
        Analyse ce ticket de support COMPLET et réponds en JSON:
        
        Titre: {ticket.title}
        Conversation complète:
        {full_content}
        Client: {ticket.customer_email}
        
        Format de réponse JSON requis:
        {{
            "intention": "description de l'intention du client",
            "category": "technique|commercial|facturation|autre", 
            "priority": "low|medium|high",
            "estimated_time": "temps estimé en minutes"
        }}
        """
        
        system_prompt = "Tu es un expert en analyse de tickets de support. Réponds uniquement en JSON valide."
        
        return self.llm_client.call_api(prompt, system_prompt)

    def _build_full_content(self, ticket: Ticket, articles: list) -> str:
        """Construire le contenu complet avec tous les articles"""
        content_parts = [f"Message initial: {ticket.body}"]
        
        for article in articles:
            sender = article.get('from', 'Inconnu')
            body = article.get('body', '').strip()
            if body and body != ticket.body:  # Éviter les doublons
                content_parts.append(f"[{sender}]: {body}")
        
        return "\n\n".join(content_parts)

    
    def _parse_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Détecter intention et classifier ticket"""
        try:
            analysis = json.loads(llm_response)
            
            # Validation des champs requis
            required_fields = ['intention', 'category', 'priority']
            if not all(field in analysis for field in required_fields):
                raise ValueError("Champs manquants dans l'analyse")
            
            return analysis
            
        except json.JSONDecodeError:
            logger.error(f"Réponse LLM invalide: {llm_response}")
            # Valeurs par défaut en cas d'erreur
            return {
                'intention': 'Demande de support',
                'category': 'technique',
                'priority': 'medium'
            }
    
    def _generate_response(self, ticket: Ticket, analysis: Dict[str, Any]) -> str:
        """Générer réponse IA"""
        prompt = f"""
        Analyse ce ticket de support et génère une réponse spécifique et personnalisée:
        
        TICKET À ANALYSER:
        - Titre: "{ticket.title}"
        - Contenu: "{ticket.body}"
        - Catégorie détectée: {analysis['category']}
        - Priorité: {analysis['priority']}
        
        INSTRUCTIONS:
        - Réponds DIRECTEMENT au problème mentionné dans le ticket
        - Sois spécifique au contenu du ticket, pas générique
        - Propose des solutions concrètes basées sur le titre et le contenu
        - Utilise un ton professionnel mais direct
        - Maximum 200 mots
        
        Format HTML simple avec:
        <h3 class="text-blue-600 font-bold text-lg mb-2">Réponse à votre demande</h3>
        <p>Contenu personnalisé basé sur le ticket...</p>
        <h4 class="text-red-600 font-bold text-base mt-4 mb-2">Solution proposée:</h4>
        <ul class="ml-4"><li>Étapes spécifiques...</li></ul>

        
        NE génère PAS de template générique. Analyse le contenu réel du ticket.
        """
        
        system_prompt = """Tu es un expert technique. Analyse le ticket et donne une réponse SPÉCIFIQUE au problème mentionné. 
        Évite les réponses génériques. Sois direct et utile."""
        
        result = self.llm_client.call_api(prompt, system_prompt)
        return result['content'] if result['success'] else "Réponse automatique en cours de génération."

    def _save_analysis(self, ticket: Ticket, analysis: Dict[str, Any], ai_response: str) -> TicketAnalysis:
        """6.2 Stockage résultats IA"""
        analysis_obj, created = TicketAnalysis.objects.get_or_create(
            ticket=ticket,
            defaults={
                'intention': analysis['intention'],
                'category': analysis['category'],
                'priority': analysis['priority'],
                'ai_response': ai_response,
                'publish_mode': self._determine_publish_mode(analysis['priority'])
            }
        )
        
        if not created:
            # Mise à jour si existe déjà
            analysis_obj.intention = analysis['intention']
            analysis_obj.category = analysis['category']
            analysis_obj.priority = analysis['priority']
            analysis_obj.ai_response = ai_response
            analysis_obj.save()
        
        return analysis_obj
    
    def _determine_publish_mode(self, priority: str) -> str:
        """Déterminer le mode de publication selon la priorité"""
        auto_priorities = ['low', 'medium']
        return 'auto' if priority in auto_priorities else 'suggestion'
    
    def publish_to_zammad(self, analysis: TicketAnalysis) -> Dict[str, Any]:
        """6.3 Publication Zammad"""
        try:
            if analysis.publish_mode == 'suggestion':
                # Mode suggestion - ne pas publier automatiquement
                return {
                    'success': True,
                    'mode': 'suggestion',
                    'message': 'Réponse en attente de validation'
                }
            
            # Mode automatique - publier via API Zammad
            result = self.zammad_api.post_ticket_response(
                analysis.ticket.zammad_id,
                analysis.ai_response
            )
            
            # Marquer comme publié
            analysis.published = True
            analysis.save()
            
            return {
                'success': True,
                'mode': 'auto',
                'zammad_response': result
            }
            
        except Exception as e:
            logger.error(f"Erreur publication ticket {analysis.ticket.zammad_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'mode': analysis.publish_mode
            }
