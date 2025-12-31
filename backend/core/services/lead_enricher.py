# backend/core/services/lead_enricher.py
import logging
import re
import requests
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class LeadEnricher:
    """Service d'enrichissement des leads avec des données supplémentaires"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def detect_sector(self, text: str, organization_name: str = "") -> Optional[str]:
        """Détecte le secteur d'activité"""
        if not text:
            text = ""
        
        text_lower = (text + " " + organization_name).lower()
        text_lower = text_lower.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
        
        # Mots-clés par secteur
        sectors = {
            'hopital': ['hopital', 'hospital', 'sante', 'santé', 'medical', 'clinique', 'chirurgie'],
            'industrie': ['industrie', 'industriel', 'usine', 'production', 'manufacturing', 'factory'],
            'tertiaire': ['bureau', 'tertiaire', 'commercial', 'centre commercial', 'shopping', 'magasin'],
            'public': ['mairie', 'prefecture', 'ministere', 'ministere', 'collectivite', 'collectivité', 'public'],
            'residentiel': ['residence', 'résidence', 'appartement', 'logement', 'habitation', 'immeuble']
        }
        
        for sector, keywords in sectors.items():
            if any(kw in text_lower for kw in keywords):
                return sector
        
        return 'autre'
    
    def estimate_company_size(self, organization_name: str, website: str = "", 
                             description: str = "") -> str:
        """Estime la taille de l'entreprise"""
        # Indicateurs de grande entreprise
        large_company_indicators = [
            'groupe', 'group', 'international', 'multinational',
            'holding', 'corporation', 'corp'
        ]
        
        text = (organization_name + " " + description).lower()
        
        # Si présence d'indicateurs de grande entreprise
        if any(indicator in text for indicator in large_company_indicators):
            return 'grande'
        
        # Si site web professionnel avec beaucoup de pages (à implémenter)
        if website:
            try:
                response = self.session.get(website, timeout=5)
                if response.status_code == 200:
                    # Analyser la complexité du site (nombre de liens, etc.)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = soup.find_all('a')
                    if len(links) > 100:
                        return 'grande'
                    elif len(links) > 20:
                        return 'moyenne'
            except:
                pass
        
        # Par défaut, considérer comme moyenne
        return 'moyenne'
    
    def extract_email_from_website(self, website: str) -> Optional[str]:
        """Extrait un email professionnel depuis un site web"""
        if not website:
            return None
        
        try:
            # Ajouter https:// si manquant
            if not website.startswith('http'):
                website = 'https://' + website
            
            response = self.session.get(website, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # Chercher des emails dans le texte
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                
                # Filtrer les emails professionnels (exclure les emails génériques)
                excluded_domains = ['example.com', 'test.com', 'domain.com']
                for email in emails:
                    email_lower = email.lower()
                    domain = email_lower.split('@')[1] if '@' in email_lower else ''
                    
                    # Exclure les emails génériques et les emails de contact génériques
                    if domain and domain not in excluded_domains:
                        if not any(generic in email_lower for generic in ['noreply', 'no-reply', 'donotreply']):
                            return email
        
        except Exception as e:
            logger.warning(f"Erreur extraction email depuis {website}: {e}")
        
        return None
    
    def enrich_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit un lead avec des données supplémentaires"""
        enriched = lead_data.copy()
        
        # Détecter le secteur
        text = ' '.join([
            enriched.get('title', ''),
            enriched.get('description', ''),
            enriched.get('organization_name', '')
        ])
        sector = self.detect_sector(text, enriched.get('organization_name', ''))
        if sector:
            enriched['sector'] = sector
        
        # Estimer la taille de l'entreprise
        company_size = self.estimate_company_size(
            enriched.get('organization_name', ''),
            enriched.get('website', ''),
            enriched.get('description', '')
        )
        enriched['company_size'] = company_size
        
        # Extraire l'email depuis le site web si manquant
        if not enriched.get('email') and enriched.get('website'):
            email = self.extract_email_from_website(enriched['website'])
            if email:
                enriched['email'] = email
        
        return enriched

