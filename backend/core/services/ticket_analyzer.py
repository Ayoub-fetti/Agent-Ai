import json
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from ..models import Ticket, TicketAnalysis
from .llm_client import LLMClient
from .zammad_api import ZammadAPIService
from .knowledge_base_service import KnowledgeBaseService


logger = logging.getLogger(__name__)

class TicketAnalyzerService:
    def __init__(self):
        self.llm_client = LLMClient()
        self.zammad_api = ZammadAPIService()
        self.kb_service = KnowledgeBaseService()  # Nouveau service
    
    def analyze_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """Analyse complète du ticket avec suggestion d'article KB"""
        try:
            # Analyse existante...
            analysis_result = self._send_to_llm(ticket)
            if not analysis_result['success']:
                return {'success': False, 'error': analysis_result['error']}
            
            parsed_analysis = self._parse_analysis(analysis_result['content'])
            ai_response_structured = self._generate_response(ticket, parsed_analysis)
            analysis_obj = self._save_analysis(ticket, parsed_analysis, str(ai_response_structured))
            
            # NOUVEAU: Suggérer un article de base de connaissance
            kb_suggestion = None
            if parsed_analysis.get('category') in ['technique', 'facturation']:
                try:
                    ticket_data = {
                        'title': ticket.title,
                        'body': ticket.body,
                        'status': ticket.status
                    }
                    kb_suggestion = self.kb_service.suggest_knowledge_article(
                        parsed_analysis, ticket_data
                    )
                except Exception as e:
                    logger.warning(f"Erreur suggestion KB: {e}")
            
            result = {
                'success': True,
                'analysis': {
                    'id': analysis_obj.id,
                    'priority': parsed_analysis.get('priority_label', 'Normal'),
                    'priority_level': parsed_analysis.get('priority', 'medium'),
                    'recommended_status': parsed_analysis.get('recommended_status', 'ouvert'),
                    'status_reason': parsed_analysis.get('status_reason', ''),
                    'category': parsed_analysis.get('category', 'technique'),
                    'intention': parsed_analysis.get('intention', ''),
                    'estimated_time': parsed_analysis.get('estimated_time', '30 minutes'),
                    'urgency_indicators': parsed_analysis.get('urgency_indicators', []),
                    'next_actions': parsed_analysis.get('next_actions', []),
                    'ai_response': {
                        'response': ai_response_structured.get('response_text', ''),
                        'solution': ai_response_structured.get('solution_steps', [])
                    }
                },
                'ai_response': str(ai_response_structured),
                'ready_for_publish': True
            }
            
            # Ajouter la suggestion KB si disponible
            if kb_suggestion and kb_suggestion.get('success'):
                result['kb_suggestion'] = kb_suggestion['suggestion']
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur analyse ticket {ticket.zammad_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _send_to_llm(self, ticket: Ticket) -> Dict[str, Any]:
        """Envoi du contenu au LLM avec gestion d'erreur réseau"""
        
        # Essayer de récupérer les articles, mais continuer même en cas d'erreur
        full_content = ticket.body
        try:
            articles = self.zammad_api.get_ticket_articles(ticket.zammad_id)
            full_content = self._build_full_content(ticket, articles)
            logger.info(f"Articles récupérés pour ticket {ticket.zammad_id}")
        except Exception as e:
            logger.warning(f"API Zammad inaccessible pour ticket {ticket.zammad_id}: {e}")
            logger.info("Analyse avec contenu principal uniquement")
        
        prompt = f"""
        Analyse ce ticket de support et fournis une analyse complète en JSON:
        
        TICKET:
        Titre: {ticket.title}
        Statut actuel: {ticket.status}
        Contenu: {full_content}
        Client: {ticket.customer_email}
        
        ANALYSE REQUISE - Réponds en JSON avec ces champs EXACTS:
        {{
            "intention": "Description claire de ce que veut le client",
            "category": "technique|commercial|facturation|autre",
            "priority": "low|medium|high|urgent",
            "priority_label": "Bas|Normal|Haute|Urgente",
            "recommended_status": "nouveau|ouvert|rappel_en_attente|en_attente_de_cloture|cloture",
            "status_reason": "Pourquoi recommander ce statut",
            "estimated_time": "Temps estimé de résolution",
            "urgency_indicators": ["liste", "des", "indicateurs", "d'urgence"],
            "next_actions": ["actions", "recommandées", "pour", "traiter", "ce", "ticket"]
        }}
        
        CRITÈRES PRIORITÉ:
        - Bas: Questions simples, demandes d'info
        - Normal: Problèmes standards, bugs mineurs
        - Haute: Problèmes impactant le service, bugs majeurs
        - Urgente: Panne totale, sécurité, perte de données
        
        CRITÈRES STATUT:
        - nouveau: Ticket juste créé, première analyse
        - ouvert: En cours de traitement actif
        - rappel_en_attente: Attente réponse client
        - en_attente_de_cloture: Solution proposée, attente confirmation
        - cloture: Problème résolu et confirmé
        """
        
        system_prompt = """Tu es un expert en analyse de tickets de support. 
        Analyse précisément le contenu et fournis une évaluation détaillée.
        Réponds UNIQUEMENT en JSON valide."""
        
        return self.llm_client.call_api(prompt, system_prompt)

    def _build_full_content(self, ticket: Ticket, articles: list) -> str:
        """Construire le contenu complet avec historique"""
        content_parts = [f"Message initial: {ticket.body}"]
        
        for article in articles:
            sender = article.get('from', 'Inconnu')
            body = article.get('body', '').strip()
            if body and body != ticket.body:
                content_parts.append(f"[{sender}]: {body}")
        
        return "\n\n".join(content_parts)
    
    def _parse_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parser la réponse LLM avec valeurs par défaut"""
        try:
            # Nettoyer la réponse des backticks markdown
            cleaned_response = llm_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Enlever ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]   # Enlever ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Enlever ```
            
            cleaned_response = cleaned_response.strip()
            
            analysis = json.loads(cleaned_response)
            
            # Validation et normalisation
            analysis.setdefault('intention', 'Demande de support')
            analysis.setdefault('category', 'technique')
            analysis.setdefault('priority', 'medium')
            analysis.setdefault('priority_label', 'Normal')
            analysis.setdefault('recommended_status', 'ouvert')
            analysis.setdefault('status_reason', 'Ticket en cours de traitement')
            analysis.setdefault('estimated_time', '30 minutes')
            analysis.setdefault('urgency_indicators', [])
            analysis.setdefault('next_actions', ['Analyser le problème', 'Proposer une solution'])
            
            return analysis
            
        except json.JSONDecodeError:
            logger.error(f"Réponse LLM invalide: {llm_response}")
            return {
                'intention': 'Demande de support',
                'category': 'technique',
                'priority': 'medium',
                'priority_label': 'Normal',
                'recommended_status': 'ouvert',
                'status_reason': 'Analyse automatique par défaut',
                'estimated_time': '30 minutes',
                'urgency_indicators': [],
                'next_actions': ['Analyser le problème']
            }

    def _generate_response(self, ticket: Ticket, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Générer une réponse IA structurée (JSON)"""
        
        prompt = f"""
        Tu es un agent support professionnel.

        CONTEXTE:
        - Titre: {ticket.title}
        - Message client: {ticket.body}
        - Catégorie: {analysis.get('category')}
        - Priorité: {analysis.get('priority_label')}

        RÉPONDS UNIQUEMENT EN JSON VALIDE (AUCUN TEXTE AUTOUR):

        {{
            "response_text": "Accusé de réception clair et empathique (max 80 mots)",
            "solution_steps": [
                "Étape 1 concrète",
                "Étape 2 concrète",
                "Étape 3 si nécessaire"
            ]
        }}
        """

        system_prompt = "Tu es un expert support. Tu DOIS répondre uniquement en JSON valide, sans balises, sans texte."

        result = self.llm_client.call_api(prompt, system_prompt)

        # Sécurité si l'API échoue
        if not result.get("success"):
            return {
                "response_text": "Nous avons bien reçu votre demande et notre équipe est en cours d'analyse.",
                "solution_steps": ["Analyse en cours", "Réponse sous 24h"]
            }

        try:
            # Parser la réponse JSON
            cleaned_response = result['content'].strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            response_data = json.loads(cleaned_response.strip())
            return {
                "response_text": response_data.get('response_text', 'Demande reçue'),
                "solution_steps": response_data.get('solution_steps', ['En cours de traitement'])
            }
        except:
            return {
                "response_text": "Nous avons bien reçu votre demande.",
                "solution_steps": ["Analyse en cours"]
            }

    def _save_analysis(self,ticket: Ticket,parsed_analysis: Dict[str, Any],ai_response: Dict[str, Any]) -> TicketAnalysis:

        analysis_obj, created = TicketAnalysis.objects.get_or_create(
            ticket=ticket,
            defaults={
                'intention': parsed_analysis.get('intention'),
                'category': parsed_analysis.get('category'),
                'priority': parsed_analysis.get('priority'),
                'ai_response': ai_response,
                'publish_mode': self._determine_publish_mode(
                    parsed_analysis.get('priority', 'medium')
                )
            }
        )

        if not created:
            analysis_obj.intention = parsed_analysis.get('intention')
            analysis_obj.category = parsed_analysis.get('category')
            analysis_obj.priority = parsed_analysis.get('priority')
            analysis_obj.ai_response = ai_response
            analysis_obj.save()

        return analysis_obj
 
    def _determine_publish_mode(self, priority: str) -> str:
        """Mode de publication selon priorité"""
        auto_priorities = ['low', 'medium']
        return 'auto' if priority in auto_priorities else 'suggestion'
    
    def get_priority_info(self, priority_level: str) -> Dict[str, str]:
        """Informations détaillées sur la priorité"""
        priority_map = {
            'low': {'label': 'Bas', 'color': 'green', 'description': 'Demande simple, non urgente'},
            'medium': {'label': 'Normal', 'color': 'blue', 'description': 'Problème standard à traiter'},
            'high': {'label': 'Haute', 'color': 'orange', 'description': 'Problème important, traitement prioritaire'},
            'urgent': {'label': 'Urgente', 'color': 'red', 'description': 'Problème critique, intervention immédiate'}
        }
        return priority_map.get(priority_level, priority_map['medium'])
    
    def get_status_recommendations(self, current_status: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Recommandations d'état basées sur l'analyse"""
        status_map = {
            'nouveau': 'Ticket nouvellement créé, première analyse nécessaire',
            'ouvert': 'Ticket en cours de traitement actif',
            'rappel_en_attente': 'En attente de réponse ou action du client',
            'en_attente_de_cloture': 'Solution proposée, attente confirmation client',
            'cloture': 'Problème résolu et confirmé par le client'
        }
        
        recommended = analysis.get('recommended_status', 'ouvert')
        
        return {
            'current': current_status,
            'recommended': recommended,
            'reason': analysis.get('status_reason', ''),
            'description': status_map.get(recommended, 'Statut à définir'),
            'next_actions': analysis.get('next_actions', [])
        }

    def publish_to_zammad(self, analysis: TicketAnalysis) -> Dict[str, Any]:
        """Publication vers Zammad avec gestion d'erreur réseau"""
        try:
            if analysis.publish_mode == 'suggestion':
                return {
                    'success': True,
                    'mode': 'suggestion',
                    'message': 'Réponse en attente de validation'
                }
            
            # Tentative de publication automatique
            try:
                result = self.zammad_api.post_ticket_response(
                    analysis.ticket.zammad_id,
                    analysis.ai_response
                )
                analysis.published = True
                analysis.save()
                
                return {
                    'success': True,
                    'mode': 'auto',
                    'zammad_response': result
                }
            except Exception as e:
                logger.error(f"Erreur publication Zammad: {e}")
                return {
                    'success': False,
                    'error': 'API Zammad inaccessible',
                    'mode': 'suggestion'
                }
            
        except Exception as e:
            logger.error(f"Erreur publication ticket {analysis.ticket.zammad_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'mode': analysis.publish_mode
            }
