# backend/core/services/ai_lead_generator.py
import logging
import json
from typing import List, Dict, Any
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class AILeadGenerator:
    """Service pour générer des leads GTB/GTEB via IA"""
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    def generate_leads(self, countries: List[str] = None, sectors: List[str] = None) -> Dict[str, Any]:
        """Génère des leads commerciaux via IA"""
        if countries is None:
            countries = ["Maroc", "France", "Canada"]
        
        if sectors is None:
            sectors = ["Gestion Technique des Bâtiments", "Gestion Technique d'Énergie des Bâtiments"]
        
        system_prompt = """Tu es un expert commercial spécialisé dans l'extraction et la qualification de leads commerciaux dans le domaine de la GTB (Gestion Technique du Bâtiment) et GTEB (Gestion Technique d'Énergie des Bâtiments).

Tu dois fournir une liste de leads commerciaux réels et pertinents avec des informations détaillées et structurées."""
        
        user_prompt = f"""Génère une liste de 20 leads commerciaux dans le domaine de la gestion technique des bâtiments (GTB) et gestion technique d'énergie des bâtiments (GTEB) pour les pays suivants : {', '.join(countries)}.

Pour chaque lead, fournis les informations suivantes :
- nom_entreprise : Nom de l'entreprise (donneur d'ordres, pas un concurrent)
- secteur : Secteur d'activité (Foncière Tertiaire, Hôtellerie, Transport, Industrie, Santé, Finance, etc.)
- pays : Pays ({', '.join(countries)})
- ville : Ville principale
- profil_decideur : Titre du décideur (ex: Directeur du Patrimoine, Directeur Technique, Responsable Énergie)
- besoin_specifique : Description du besoin en GTB/GTEB (ex: Mise en conformité, Optimisation énergétique, Maintenance prédictive)
- type_projet : Type de projet (GTB, GTEB, CVC, Supervision, Électricité)
- budget_estime : Budget estimé en euros (nombre)
- potentiel : Score de potentiel de 0 à 100
- justification : Justification du potentiel commercial

Concentre-toi sur les DONNEURS D'ORDRES (clients finaux) qui ont des besoins en GTB/GTEB :
- Grands groupes immobiliers
- Hôpitaux et établissements de santé
- Hôtels et chaînes hôtelières
- Aéroports et gares
- Industries (pharmaceutique, agroalimentaire)
- Banques et assurances
- Universités et campus
- Centres commerciaux
- Data centers

Réponds UNIQUEMENT avec un JSON valide au format suivant :
{{
  "leads": [
    {{
      "nom_entreprise": "...",
      "secteur": "...",
      "pays": "...",
      "ville": "...",
      "profil_decideur": "...",
      "besoin_specifique": "...",
      "type_projet": "...",
      "budget_estime": 0,
      "potentiel": 0,
      "justification": "..."
    }}
  ]
}}"""
        
        try:
            logger.info(f"Génération de leads IA pour {countries}")
            
            response = self.llm_client.call_api(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model="command-a-03-2025"
            )
            
            if not response.get('success'):
                return {
                    'success': False,
                    'error': response.get('error', 'Erreur API'),
                    'leads': []
                }
            
            content = response.get('content', '')
            
            # Parser le JSON
            try:
                # Nettoyer le contenu (enlever les markdown code blocks si présents)
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                data = json.loads(content)
                leads_data = data.get('leads', [])
                
                logger.info(f"IA a généré {len(leads_data)} leads")
                
                return {
                    'success': True,
                    'leads': leads_data,
                    'total': len(leads_data)
                }
            
            except json.JSONDecodeError as e:
                logger.error(f"Erreur parsing JSON: {e}")
                logger.error(f"Contenu reçu: {content[:500]}")
                return {
                    'success': False,
                    'error': f'Erreur parsing JSON: {str(e)}',
                    'leads': [],
                    'raw_content': content[:500]
                }
        
        except Exception as e:
            logger.error(f"Erreur génération leads IA: {e}")
            return {
                'success': False,
                'error': str(e),
                'leads': []
            }
