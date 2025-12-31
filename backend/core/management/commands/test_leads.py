# backend/core/management/commands/test_leads.py
from django.core.management.base import BaseCommand
from core.services.lead_service import LeadService
from core.models import Lead


class Command(BaseCommand):
    help = 'Teste le système de recherche et scoring de leads GTB/GTEB'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Test du système de leads GTB/GTEB ===\n'))
        
        # Test 1: Recherche de leads (avec exemples pour les tests)
        self.stdout.write('1. Test de recherche de leads...')
        lead_service = LeadService()
        
        try:
            # Pour les tests, on peut utiliser les exemples
            from core.services.lead_search import LeadSearchService
            search_service = LeadSearchService()
            
            # Générer des exemples pour les tests
            example_leads = search_service.generate_example_leads(['Maroc', 'France'])
            
            # Traiter les exemples comme de vrais leads
            results = {
                'total_found': len(example_leads),
                'created': 0,
                'updated': 0,
                'errors': 0,
                'leads': [],
                'search_report': {
                    'sources_consulted': [],
                    'sources_with_results': ['Données de test'],
                    'sources_without_results': [],
                    'errors': [],
                    'total_leads_found': len(example_leads)
                }
            }
            
            # Traiter chaque lead d'exemple
            for raw_lead in example_leads:
                try:
                    # Normaliser
                    normalized_lead = lead_service.normalizer.normalize_lead_data(raw_lead)
                    
                    # Enrichir
                    enriched_lead = lead_service.enricher.enrich_lead(normalized_lead)
                    
                    # Calculer le score
                    scoring_result = lead_service.scorer.calculate_score(enriched_lead)
                    enriched_lead.update(scoring_result)
                    
                    # Créer ou mettre à jour le lead
                    lead, created = lead_service._create_or_update_lead(enriched_lead)
                    
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
                    self.stdout.write(self.style.ERROR(f'   ✗ Erreur traitement lead: {e}'))
                    results['errors'] += 1
                    continue
            
            self.stdout.write(self.style.SUCCESS(f'   ✓ Recherche terminée'))
            self.stdout.write(f'   - Total trouvé: {results["total_found"]}')
            self.stdout.write(f'   - Créés: {results["created"]}')
            self.stdout.write(f'   - Mis à jour: {results["updated"]}')
            self.stdout.write(f'   - Erreurs: {results["errors"]}')
            
            if results['leads']:
                self.stdout.write('\n   Leads créés:')
                for lead_info in results['leads'][:5]:  # Afficher les 5 premiers
                    self.stdout.write(f'   - {lead_info["title"][:50]}... (Score: {lead_info["score"]}, {lead_info["temperature"]})')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Erreur: {str(e)}'))
        
        # Test 2: Statistiques
        self.stdout.write('\n2. Statistiques des leads...')
        total = Lead.objects.count()
        chaud = Lead.objects.filter(temperature='chaud').count()
        tiede = Lead.objects.filter(temperature='tiede').count()
        froid = Lead.objects.filter(temperature='froid').count()
        
        self.stdout.write(f'   - Total: {total}')
        self.stdout.write(f'   - Chauds: {chaud}')
        self.stdout.write(f'   - Tièdes: {tiede}')
        self.stdout.write(f'   - Froids: {froid}')
        
        # Test 3: Afficher quelques leads
        if total > 0:
            self.stdout.write('\n3. Exemples de leads:')
            leads = Lead.objects.order_by('-score')[:3]
            for lead in leads:
                self.stdout.write(f'\n   Organisation: {lead.organization_name}')
                self.stdout.write(f'   Titre: {lead.title[:60]}...')
                self.stdout.write(f'   Localisation: {lead.city}, {lead.country}')
                self.stdout.write(f'   Score: {lead.score}/100 ({lead.temperature})')
                if lead.project_type:
                    self.stdout.write(f'   Type: {lead.project_type}')
        
        self.stdout.write(self.style.SUCCESS('\n=== Test terminé ==='))

