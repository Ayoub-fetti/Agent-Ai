# backend/core/services/lead_service.py
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from django.utils import timezone
from ..models import Lead
from .lead_search import LeadSearchService
from .lead_normalizer import LeadNormalizer
from .lead_enricher import LeadEnricher
from .lead_scorer import LeadScorer
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class LeadService:
    """Service principal pour la gestion des leads GTB/GTEB"""
    
    def __init__(self):
        self.search_service = LeadSearchService()
        self.normalizer = LeadNormalizer()
        self.enricher = LeadEnricher()
        self.llm_client = LLMClient()
        self.scorer = LeadScorer(llm_client=self.llm_client)
    
    def search_and_create_leads(self, countries: List[str] = None, 
                               max_leads_per_source: int = 50,
                               progress_tracker = None) -> Dict[str, Any]:
        """Recherche et crée des leads depuis toutes les sources"""
        if countries is None:
            countries = ["Maroc", "France", "Canada"]
        
        results = {
            'total_found': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
            'leads': [],
            'search_report': {}
        }
        
        try:
            # Rechercher les leads (retourne maintenant un dict avec leads et report)
            search_result = self.search_service.search_all_sources(countries, progress_tracker=progress_tracker)
            raw_leads = search_result.get('leads', [])
            results['search_report'] = search_result.get('report', {})
            results['total_found'] = len(raw_leads)
            
            # Traiter chaque lead
            for raw_lead in raw_leads:
                try:
                    # Normaliser
                    normalized_lead = self.normalizer.normalize_lead_data(raw_lead)
                    
                    # Enrichir
                    enriched_lead = self.enricher.enrich_lead(normalized_lead)
                    
                    # Calculer le score
                    scoring_result = self.scorer.calculate_score(enriched_lead)
                    enriched_lead.update(scoring_result)
                    
                    # Créer ou mettre à jour le lead
                    lead, created = self._create_or_update_lead(enriched_lead)
                    
                    if created:
                        results['created'] += 1
                    else:
                        results['updated'] += 1
                    
                    results['leads'].append({
                        'id': lead.id,
                        'title': lead.title,
                        'score': lead.score,
                        'temperature': lead.temperature,
                        'created': created
                    })
                
                except Exception as e:
                    logger.error(f"Erreur traitement lead: {e}")
                    results['errors'] += 1
                    continue
        
        except Exception as e:
            logger.error(f"Erreur recherche leads: {e}")
            results['error'] = str(e)
        
        return results
    
    def _create_or_update_lead(self, lead_data: Dict[str, Any]) -> Tuple[Lead, bool]:
        """Crée ou met à jour un lead"""
        # Identifier le lead par titre + organisation + source_url
        source_url = lead_data.get('source_url', '')
        title = lead_data.get('title', '')
        organization = lead_data.get('organization_name', '')
        
        # Chercher un lead existant
        existing_lead = None
        if source_url:
            existing_lead = Lead.objects.filter(source_url=source_url).first()
        
        if not existing_lead and title and organization:
            existing_lead = Lead.objects.filter(
                title__iexact=title,
                organization_name__iexact=organization
            ).first()
        
        # Préparer les données pour le modèle
        lead_fields = {
            'lead_type': lead_data.get('lead_type', 'entreprise'),
            'project_type': lead_data.get('project_type'),
            'title': title[:500],
            'description': lead_data.get('description', '')[:5000],
            'organization_name': organization[:255],
            'website': lead_data.get('website'),
            'phone': lead_data.get('phone', '')[:50],
            'email': lead_data.get('email'),
            'city': lead_data.get('city', '')[:100],
            'country': lead_data.get('country', 'Maroc'),
            'market_date': lead_data.get('market_date'),
            'budget': lead_data.get('budget'),
            'market_url': lead_data.get('market_url'),
            'sector': lead_data.get('sector'),
            'company_size': lead_data.get('company_size', 'inconnu'),
            'score': lead_data.get('score', 0),
            'temperature': lead_data.get('temperature', 'froid'),
            'score_justification': lead_data.get('score_justification', ''),
            'source_url': source_url,
            'keywords_found': lead_data.get('keywords_found', []),
            'raw_data': lead_data.get('raw_data', {})
        }
        
        if existing_lead:
            # Mettre à jour si le score est meilleur ou si données plus récentes
            if lead_fields['score'] > existing_lead.score:
                for key, value in lead_fields.items():
                    if value is not None:
                        setattr(existing_lead, key, value)
                existing_lead.last_analyzed_at = timezone.now()
                existing_lead.save()
                return existing_lead, False
            else:
                return existing_lead, False
        else:
            # Créer un nouveau lead
            lead = Lead.objects.create(**lead_fields)
            return lead, True
    
    def reanalyze_lead(self, lead_id: int) -> Dict[str, Any]:
        """Réanalyse un lead existant"""
        try:
            lead = Lead.objects.get(id=lead_id)
            
            # Préparer les données pour l'analyse
            lead_data = {
                'lead_type': lead.lead_type,
                'project_type': lead.project_type,
                'title': lead.title,
                'description': lead.description,
                'organization_name': lead.organization_name,
                'website': lead.website,
                'phone': lead.phone,
                'email': lead.email,
                'city': lead.city,
                'country': lead.country,
                'market_date': lead.market_date,
                'budget': lead.budget,
                'sector': lead.sector,
                'company_size': lead.company_size,
                'keywords_found': lead.keywords_found
            }
            
            # Enrichir à nouveau
            enriched_lead = self.enricher.enrich_lead(lead_data)
            
            # Recalculer le score
            scoring_result = self.scorer.calculate_score(enriched_lead)
            
            # Mettre à jour le lead
            lead.score = scoring_result['score']
            lead.temperature = scoring_result['temperature']
            lead.score_justification = scoring_result['score_justification']
            lead.last_analyzed_at = timezone.now()
            
            # Mettre à jour les champs enrichis
            if enriched_lead.get('sector'):
                lead.sector = enriched_lead['sector']
            if enriched_lead.get('company_size'):
                lead.company_size = enriched_lead['company_size']
            if enriched_lead.get('email') and not lead.email:
                lead.email = enriched_lead['email']
            
            lead.save()
            
            return {
                'success': True,
                'lead_id': lead.id,
                'score': lead.score,
                'temperature': lead.temperature,
                'justification': lead.score_justification
            }
        
        except Lead.DoesNotExist:
            return {'success': False, 'error': 'Lead non trouvé'}
        except Exception as e:
            logger.error(f"Erreur réanalyse lead {lead_id}: {e}")
            return {'success': False, 'error': str(e)}

