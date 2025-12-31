# backend/core/services/lead_scorer.py
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from ..models import Lead

logger = logging.getLogger(__name__)

class LeadScorer:
    """Service de scoring IA pour les leads GTB/GTEB"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def calculate_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule le score d'un lead selon la logique métier GTB"""
        score = 0
        factors = []
        
        # 1. Projet GTB/GTEB explicite (0-30 points)
        project_type = lead_data.get('project_type')
        keywords_found = lead_data.get('keywords_found', [])
        
        if project_type in ['GTB', 'GTEB']:
            score += 30
            factors.append("Projet GTB/GTEB explicite identifié (+30)")
        elif project_type == 'MIXTE':
            score += 25
            factors.append("Projet mixte GTB/GTEB identifié (+25)")
        elif project_type in ['CVC', 'supervision', 'electricite']:
            score += 15
            factors.append(f"Projet {project_type} identifié (+15)")
        elif len(keywords_found) > 0:
            score += 10
            factors.append(f"Mots-clés GTB détectés: {len(keywords_found)} (+10)")
        
        # 2. Présence d'un marché public (0-25 points)
        lead_type = lead_data.get('lead_type')
        if lead_type == 'marche_public':
            score += 25
            factors.append("Marché public identifié (+25)")
            
            # Bonus si budget disponible
            budget = lead_data.get('budget')
            if budget:
                try:
                    budget_value = float(budget)
                    if budget_value > 1000000:  # > 1M
                        score += 5
                        factors.append("Budget élevé (>1M) (+5)")
                    elif budget_value > 100000:  # > 100K
                        score += 3
                        factors.append("Budget moyen (>100K) (+3)")
                except:
                    pass
            
            # Bonus si date récente
            market_date = lead_data.get('market_date')
            if market_date:
                try:
                    if isinstance(market_date, str):
                        market_date = datetime.strptime(market_date, '%Y-%m-%d')
                    days_old = (datetime.now().date() - market_date.date()).days
                    if days_old < 30:
                        score += 5
                        factors.append("Marché récent (<30 jours) (+5)")
                    elif days_old < 90:
                        score += 3
                        factors.append("Marché récent (<90 jours) (+3)")
                except:
                    pass
        
        # 3. Offre d'emploi GTB active (0-20 points)
        if lead_type == 'offre_emploi':
            score += 20
            factors.append("Offre d'emploi GTB active (indicateur de besoin) (+20)")
        
        # 4. Taille de l'entreprise (0-15 points)
        company_size = lead_data.get('company_size')
        if company_size == 'grande':
            score += 15
            factors.append("Grande entreprise (+15)")
        elif company_size == 'moyenne':
            score += 10
            factors.append("Entreprise moyenne (+10)")
        elif company_size == 'petite':
            score += 5
            factors.append("Petite entreprise (+5)")
        
        # 5. Informations complètes (0-10 points)
        completeness_score = 0
        if lead_data.get('email'):
            completeness_score += 3
        if lead_data.get('phone'):
            completeness_score += 2
        if lead_data.get('website'):
            completeness_score += 2
        if lead_data.get('description'):
            completeness_score += 3
        
        score += completeness_score
        if completeness_score > 0:
            factors.append(f"Informations complètes ({completeness_score}/10) (+{completeness_score})")
        
        # 6. Secteur d'activité (0-10 points)
        sector = lead_data.get('sector')
        if sector in ['hopital', 'industrie', 'public']:
            score += 10
            factors.append(f"Secteur prioritaire: {sector} (+10)")
        elif sector in ['tertiaire']:
            score += 5
            factors.append(f"Secteur: {sector} (+5)")
        
        # Limiter le score à 100
        score = min(score, 100)
        
        # Déterminer la température
        if score >= 70:
            temperature = 'chaud'
        elif score >= 40:
            temperature = 'tiede'
        else:
            temperature = 'froid'
        
        # Générer la justification avec IA si disponible
        justification = self.generate_justification(lead_data, score, factors, temperature)
        
        return {
            'score': score,
            'temperature': temperature,
            'score_justification': justification,
            'factors': factors
        }
    
    def generate_justification(self, lead_data: Dict[str, Any], score: int, 
                              factors: list, temperature: str) -> str:
        """Génère une justification claire du score avec IA"""
        if self.llm_client:
            try:
                prompt = f"""
Analyse ce lead commercial GTB/GTEB et génère une justification claire et professionnelle du score.

Données du lead:
- Type: {lead_data.get('lead_type')}
- Organisation: {lead_data.get('organization_name')}
- Titre: {lead_data.get('title')}
- Localisation: {lead_data.get('city')}, {lead_data.get('country')}
- Type de projet: {lead_data.get('project_type')}
- Secteur: {lead_data.get('sector')}
- Taille entreprise: {lead_data.get('company_size')}
- Score calculé: {score}/100
- Température: {temperature}
- Facteurs: {', '.join(factors)}

Génère une justification professionnelle en 2-3 phrases expliquant pourquoi ce lead a ce score et cette température.
"""
                result = self.llm_client.call_api(
                    prompt,
                    system_prompt="Tu es un expert en analyse de leads commerciaux GTB/GTEB. Génère des justifications claires et professionnelles."
                )
                
                if result.get('success'):
                    return result['content']
            except Exception as e:
                logger.warning(f"Erreur génération justification IA: {e}")
        
        # Fallback: justification manuelle
        justification_parts = [
            f"Score de {score}/100 ({temperature.upper()})",
            f"Basé sur: {len(factors)} facteur(s) d'évaluation"
        ]
        
        if factors:
            justification_parts.append(f"Points clés: {factors[0]}")
            if len(factors) > 1:
                justification_parts.append(f"et {len(factors)-1} autre(s) facteur(s)")
        
        return ". ".join(justification_parts) + "."

