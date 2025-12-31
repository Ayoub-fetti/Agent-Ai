# backend/core/services/lead_search.py
import logging
import re
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class LeadSearchService:
    """Service pour rechercher des leads GTB/GTEB depuis différentes sources (100% gratuit)"""
    
    # Mots-clés de recherche
    KEYWORDS = [
        "GTB", "GTC", "BMS", "Gestion technique du bâtiment",
        "Supervision bâtiment", "Automatisme CVC",
        "Electricité bâtiment", "Courants forts", "Courants faibles",
        "GTEB", "Génie Technique Électrique du Bâtiment",
        "Installation électrique", "Maintenance GTB", "Intégration GTB"
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def _extract_city_from_text(self, text: str) -> str:
        """Extrait la ville depuis un texte"""
        if not text:
            return ""
        
        # Villes communes
        cities = {
            'Maroc': ['Casablanca', 'Rabat', 'Fès', 'Fes', 'Marrakech', 'Tanger', 'Agadir', 'Meknès', 'Oujda'],
            'France': ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier', 'Bordeaux'],
            'Canada': ['Montréal', 'Montreal', 'Toronto', 'Vancouver', 'Ottawa', 'Calgary', 'Edmonton', 'Winnipeg']
        }
        
        text_lower = text.lower()
        for city_list in cities.values():
            for city in city_list:
                if city.lower() in text_lower:
                    return city
        
        # Prendre le premier mot significatif en majuscule
        words = text.split()
        for word in words:
            if len(word) > 3 and word[0].isupper() and word.isalpha():
                return word
        
        return ""
    
    def _parse_date(self, date_str: str):
        """Parse une date depuis une chaîne"""
        if not date_str:
            return None
        try:
            # Formats: "DD/MM/YYYY", "YYYY-MM-DD", "DD MM YYYY"
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d %B %Y', '%d-%m-%Y', '%d/%m/%y']:
                try:
                    return datetime.strptime(date_str[:10], fmt).date()
                except:
                    continue
        except:
            pass
        return None
    
    def _parse_budget(self, budget_str: str):
        """Parse un budget depuis une chaîne"""
        if not budget_str:
            return None
        try:
            # Extraire les nombres
            numbers = re.findall(r'[\d\s,\.]+', budget_str.replace(',', '.'))
            if numbers:
                # Nettoyer et convertir
                budget_str_clean = numbers[0].replace(' ', '').replace(',', '')
                budget = float(budget_str_clean)
                
                # Multiplier selon l'unité (M = millions, K = milliers)
                budget_upper = budget_str.upper()
                if 'M' in budget_upper or 'million' in budget_str.lower():
                    budget *= 1000000
                elif 'K' in budget_upper or 'millier' in budget_str.lower():
                    budget *= 1000
                
                return budget
        except:
            pass
        return None
    
    # ==================== MARCHÉS PUBLICS FRANCE (BOAMP) ====================
    
    def search_public_markets_france(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Recherche de marchés publics en France via BOAMP (scraping gratuit)"""
        leads = []
        try:
            base_url = "https://www.boamp.fr"
            
            for keyword in self.KEYWORDS[:5]:
                try:
                    # URL de recherche BOAMP
                    search_url = f"{base_url}/avis"
                    params = {
                        'q': keyword,
                        'type': 'marche'
                    }
                    
                    response = self.session.get(search_url, params=params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Chercher les résultats (plusieurs méthodes)
                        results = (
                            soup.find_all('article') or
                            soup.find_all('div', class_=lambda x: x and 'avis' in x.lower()) or
                            soup.find_all('div', {'data-type': 'avis'}) or
                            soup.find_all('li', class_=lambda x: x and 'resultat' in x.lower())
                        )
                        
                        for result in results[:10]:
                            try:
                                # Extraire le titre
                                title = ""
                                for selector in ['h2', 'h3', 'a.titre', '.titre', 'a[href*="/avis/"]', 'h2 a']:
                                    elem = result.select_one(selector)
                                    if elem:
                                        title = elem.get_text().strip()
                                        break
                                
                                if not title:
                                    continue
                                
                                # Extraire le lien
                                link_elem = result.find('a', href=True)
                                market_url = ""
                                if link_elem:
                                    href = link_elem['href']
                                    market_url = href if href.startswith('http') else base_url + href
                                
                                # Extraire l'organisation
                                org_selectors = ['.maitre-ouvrage', '.organisateur', '.acheteur', 'span[title*="acheteur"]', '.organisme']
                                organization = ""
                                for selector in org_selectors:
                                    elem = result.select_one(selector)
                                    if elem:
                                        organization = elem.get_text().strip()
                                        break
                                
                                # Extraire la date
                                date_elem = result.find('time') or result.find('span', class_=lambda x: x and 'date' in x.lower())
                                date_str = ""
                                if date_elem:
                                    date_str = date_elem.get('datetime') or date_elem.get_text().strip()
                                
                                # Extraire le budget
                                budget_elem = result.find(string=re.compile(r'€|EUR|euros', re.I))
                                budget_str = ""
                                if budget_elem:
                                    parent = budget_elem.parent
                                    budget_str = parent.get_text().strip() if parent else ""
                                
                                # Extraire la localisation
                                location_elem = result.find(string=re.compile(r'France|Paris|Lyon|Marseille', re.I))
                                location = ""
                                if location_elem:
                                    location = location_elem.strip()
                                
                                # Détecter les mots-clés
                                text_content = (title + " " + (result.get_text() or "")).lower()
                                keywords_found = [kw for kw in self.KEYWORDS if kw.lower() in text_content]
                                
                                if title and keywords_found:
                                    lead_data = {
                                        'lead_type': 'marche_public',
                                        'title': title[:500],
                                        'description': result.get_text().strip()[:5000] if result.get_text() else "",
                                        'organization_name': organization or "Non spécifié",
                                        'city': self._extract_city_from_text(location or title),
                                        'country': 'France',
                                        'market_date': self._parse_date(date_str),
                                        'budget': self._parse_budget(budget_str),
                                        'market_url': market_url,
                                        'source_url': market_url,
                                        'keywords_found': keywords_found,
                                        'raw_data': {'html_snippet': str(result)[:500]}
                                    }
                                    
                                    leads.append(lead_data)
                                    
                                    if len(leads) >= max_results:
                                        break
                            
                            except Exception as e:
                                logger.warning(f"Erreur parsing annonce BOAMP: {e}")
                                continue
                    
                    time.sleep(3)  # Respecter les serveurs
                    
                except Exception as e:
                    logger.warning(f"Erreur recherche BOAMP pour {keyword}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erreur recherche marchés publics France: {e}")
        
        return leads
    
    # ==================== MARCHÉS PUBLICS MAROC ====================
    
    def search_public_markets_morocco(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Recherche de marchés publics au Maroc (scraping gratuit)"""
        leads = []
        try:
            base_url = "https://www.marchespublics.gov.ma"
            
            for keyword in self.KEYWORDS[:5]:
                try:
                    # Essayer différentes URLs de recherche
                    search_urls = [
                        f"{base_url}/op/index.php",
                        f"{base_url}/recherche",
                        f"{base_url}/index.php?page=recherche"
                    ]
                    
                    for search_url in search_urls:
                        try:
                            params = {
                                'motcle': keyword,
                                'q': keyword,
                                'recherche': keyword
                            }
                            
                            response = self.session.get(search_url, params=params, timeout=15)
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.text, 'html.parser')
                                
                                # Chercher les résultats
                                results = (
                                    soup.find_all('tr', class_=lambda x: x and ('resultat' in x.lower() or 'ligne' in x.lower())) or
                                    soup.find_all('div', class_=lambda x: x and 'resultat' in x.lower()) or
                                    soup.find_all('li', class_=lambda x: x and 'marche' in x.lower()) or
                                    soup.find_all('div', class_=lambda x: x and 'marche' in x.lower())
                                )
                                
                                for result in results[:10]:
                                    try:
                                        # Titre
                                        title = ""
                                        for elem in [result.find('a'), result.find('h3'), result.find('h4'), result.find('td')]:
                                            if elem:
                                                title = elem.get_text().strip()
                                                if len(title) > 10:  # Filtrer les titres trop courts
                                                    break
                                        
                                        if not title or len(title) < 10:
                                            continue
                                        
                                        # Lien
                                        link_elem = result.find('a', href=True)
                                        market_url = ""
                                        if link_elem:
                                            href = link_elem['href']
                                            market_url = href if href.startswith('http') else base_url + href
                                        
                                        # Organisation
                                        org_text = result.get_text()
                                        organization = ""
                                        for pattern in ['Organisateur', 'Maître', 'Organisme', 'Acheteur', 'Maître d\'ouvrage']:
                                            if pattern in org_text:
                                                parts = org_text.split(pattern)
                                                if len(parts) > 1:
                                                    organization = parts[1].split('\n')[0].strip()[:100]
                                                    break
                                        
                                        # Date
                                        date_elem = result.find('time') or result.find(string=re.compile(r'\d{2}/\d{2}/\d{4}'))
                                        date_str = ""
                                        if date_elem:
                                            if isinstance(date_elem, str):
                                                date_str = date_elem
                                            else:
                                                date_str = date_elem.get('datetime') or date_elem.get_text().strip()
                                        
                                        # Budget
                                        budget_elem = result.find(string=re.compile(r'[0-9\s]+(?:DH|MAD|dirham)', re.I))
                                        budget_str = ""
                                        if budget_elem:
                                            budget_str = budget_elem.strip()
                                        
                                        # Mots-clés
                                        text_content = (title + " " + org_text).lower()
                                        keywords_found = [kw for kw in self.KEYWORDS if kw.lower() in text_content]
                                        
                                        if title and keywords_found:
                                            lead_data = {
                                                'lead_type': 'marche_public',
                                                'title': title[:500],
                                                'description': org_text[:5000],
                                                'organization_name': organization or "Non spécifié",
                                                'city': self._extract_city_from_text(title + " " + org_text),
                                                'country': 'Maroc',
                                                'market_date': self._parse_date(date_str),
                                                'budget': self._parse_budget(budget_str),
                                                'market_url': market_url,
                                                'source_url': market_url,
                                                'keywords_found': keywords_found,
                                                'raw_data': {'html_snippet': str(result)[:500]}
                                            }
                                            
                                            leads.append(lead_data)
                                            
                                            if len(leads) >= max_results:
                                                break
                                    
                                    except Exception as e:
                                        logger.warning(f"Erreur parsing résultat Maroc: {e}")
                                        continue
                                
                                if leads:
                                    break  # Si on a trouvé des résultats, arrêter
                        
                        except Exception as e:
                            logger.warning(f"Erreur avec URL {search_url}: {e}")
                            continue
                    
                    time.sleep(3)
                    
                except Exception as e:
                    logger.warning(f"Erreur recherche marchés Maroc pour {keyword}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erreur recherche marchés publics Maroc: {e}")
        
        return leads
    
    # ==================== MARCHÉS PUBLICS CANADA ====================
    
    def search_public_markets_canada(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Recherche de marchés publics au Canada"""
        leads = []
        try:
            # Sources canadiennes (MERX, Buyandsell.gc.ca)
            base_urls = [
                "https://www.merx.com",
                "https://buyandsell.gc.ca"
            ]
            
            for keyword in self.KEYWORDS[:3]:
                for base_url in base_urls:
                    try:
                        search_url = f"{base_url}/search"
                        params = {'q': keyword, 'keywords': keyword}
                        
                        response = self.session.get(search_url, params=params, timeout=15)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Chercher les résultats
                            results = soup.find_all('div', class_=lambda x: x and ('result' in x.lower() or 'listing' in x.lower()))
                            
                            for result in results[:5]:
                                try:
                                    title_elem = result.find('h3') or result.find('a')
                                    title = title_elem.get_text().strip() if title_elem else ""
                                    
                                    if not title:
                                        continue
                                    
                                    text_content = title.lower()
                                    keywords_found = [kw for kw in self.KEYWORDS if kw.lower() in text_content]
                                    
                                    if keywords_found:
                                        lead_data = {
                                            'lead_type': 'marche_public',
                                            'title': title[:500],
                                            'description': result.get_text().strip()[:5000],
                                            'organization_name': "Non spécifié",
                                            'city': self._extract_city_from_text(title),
                                            'country': 'Canada',
                                            'source_url': base_url,
                                            'keywords_found': keywords_found,
                                            'raw_data': {}
                                        }
                                        
                                        leads.append(lead_data)
                                        
                                        if len(leads) >= max_results:
                                            break
                                
                                except Exception as e:
                                    logger.warning(f"Erreur parsing résultat Canada: {e}")
                                    continue
                        
                        time.sleep(3)
                        
                    except Exception as e:
                        logger.warning(f"Erreur recherche Canada {base_url}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Erreur recherche marchés publics Canada: {e}")
        
        return leads
    
    # ==================== OPENSTREETMAP (GRATUIT) ====================
    
    def search_companies_gtb_osm(self, country: str = "Maroc", max_results: int = 100) -> List[Dict[str, Any]]:
        """Recherche d'entreprises GTB/GTEB via OpenStreetMap (100% gratuit)"""
        leads = []
        try:
            # Overpass API endpoint
            overpass_url = "https://overpass-api.de/api/interpreter"
            
            # Définir les zones géographiques (relation IDs OSM)
            area_map = {
                "Maroc": "relation(1473948);",
                "France": "relation(2202162);",
                "Canada": "relation(1428125);"
            }
            
            area_query = area_map.get(country, area_map["Maroc"])
            
            # Requête Overpass pour trouver des entreprises d'ingénierie et électricité
            query = f"""
            [out:json][timeout:25];
            (
              node["office"="engineering"]({area_query});
              way["office"="engineering"]({area_query});
              relation["office"="engineering"]({area_query});
              node["craft"="electrician"]({area_query});
              way["craft"="electrician"]({area_query});
              relation["craft"="electrician"]({area_query});
            );
            out body;
            >;
            out skel qt;
            """
            
            try:
                response = self.session.post(
                    overpass_url,
                    data={'data': query},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for element in data.get('elements', []):
                        try:
                            tags = element.get('tags', {})
                            name = tags.get('name', '')
                            
                            if not name:
                                continue
                            
                            # Filtrer par mots-clés GTB dans le nom ou les tags
                            name_lower = name.lower()
                            tags_str = str(tags).lower()
                            
                            if not any(kw.lower() in name_lower for kw in ['gtb', 'gtc', 'bms', 'électricité', 'électrique', 'bâtiment', 'building', 'technique']):
                                if not any(kw.lower() in tags_str for kw in ['gtb', 'gtc', 'bms']):
                                    continue
                            
                            # Coordonnées
                            lat = element.get('lat') or (element.get('center', {}).get('lat'))
                            lon = element.get('lon') or (element.get('center', {}).get('lon'))
                            
                            # Adresse
                            city = tags.get('addr:city', '') or tags.get('addr:place', '')
                            if not city:
                                city = tags.get('addr:suburb', '')
                            
                            # Téléphone et site web
                            phone = tags.get('phone', '') or tags.get('contact:phone', '')
                            website = tags.get('website', '') or tags.get('contact:website', '')
                            
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': f"Entreprise {name}",
                                'description': f"Entreprise trouvée via OpenStreetMap: {tags.get('description', '')}",
                                'organization_name': name,
                                'website': website,
                                'phone': phone,
                                'city': city or country,
                                'country': country,
                                'source_url': f"https://www.openstreetmap.org/{element.get('type', 'node')}/{element.get('id', '')}",
                                'keywords_found': ['GTB', 'GTEB'],
                                'raw_data': {
                                    'osm_id': element.get('id'),
                                    'osm_type': element.get('type'),
                                    'tags': tags,
                                    'coordinates': {'lat': lat, 'lon': lon}
                                }
                            }
                            
                            leads.append(lead_data)
                            
                            if len(leads) >= max_results:
                                break
                        
                        except Exception as e:
                            logger.warning(f"Erreur parsing élément OSM: {e}")
                            continue
                
                time.sleep(2)  # Respecter les limites Overpass
                
            except Exception as e:
                logger.warning(f"Erreur requête Overpass: {e}")
        
        except Exception as e:
            logger.error(f"Erreur recherche entreprises OSM: {e}")
        
        return leads
    
    # ==================== KERIX (MAROC - GRATUIT) ====================
    
    def _search_kerix_maroc(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Scraping de Kerix (annuaire marocain gratuit)"""
        leads = []
        try:
            base_url = "https://www.kerix.net"
            
            search_queries = [
                "GTB",
                "Gestion technique bâtiment",
                "Électricité bâtiment",
                "Bureau étude électricité"
            ]
            
            for query in search_queries:
                try:
                    search_url = f"{base_url}/recherche"
                    params = {'q': query}
                    
                    response = self.session.get(search_url, params=params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Chercher les résultats
                        results = (
                            soup.find_all('div', class_=lambda x: x and ('entreprise' in x.lower() or 'resultat' in x.lower())) or
                            soup.find_all('li', class_=lambda x: x and 'entreprise' in x.lower()) or
                            soup.find_all('tr', class_=lambda x: x and 'ligne' in x.lower())
                        )
                        
                        for result in results[:10]:
                            try:
                                # Nom entreprise
                                name_elem = result.find('h3') or result.find('a', class_='nom') or result.find('a')
                                name = name_elem.get_text().strip() if name_elem else ""
                                
                                if not name:
                                    continue
                                
                                # Lien
                                link_elem = result.find('a', href=True)
                                company_url = ""
                                if link_elem:
                                    href = link_elem['href']
                                    company_url = href if href.startswith('http') else base_url + href
                                
                                # Téléphone
                                phone_elem = result.find(string=re.compile(r'0[5-7]\d{8}'))  # Format téléphone marocain
                                phone = phone_elem.strip() if phone_elem else ""
                                
                                # Ville
                                city_elem = result.find('span', class_=lambda x: x and 'ville' in x.lower())
                                city = city_elem.get_text().strip() if city_elem else ""
                                
                                # Site web
                                website_elem = result.find('a', href=re.compile(r'http'))
                                website = website_elem['href'] if website_elem else ""
                                
                                lead_data = {
                                    'lead_type': 'entreprise',
                                    'title': f"Entreprise {name}",
                                    'description': result.get_text().strip()[:1000],
                                    'organization_name': name,
                                    'website': website,
                                    'phone': phone,
                                    'city': city or "Maroc",
                                    'country': 'Maroc',
                                    'source_url': company_url,
                                    'keywords_found': ['GTB', 'GTEB'],
                                    'raw_data': {}
                                }
                                
                                leads.append(lead_data)
                                
                                if len(leads) >= max_results:
                                    break
                            
                            except Exception as e:
                                logger.warning(f"Erreur parsing Kerix: {e}")
                                continue
                    
                    time.sleep(3)
                    
                except Exception as e:
                    logger.warning(f"Erreur recherche Kerix pour {query}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erreur recherche Kerix: {e}")
        
        return leads
    
    # ==================== PAGES JAUNES (FRANCE - GRATUIT) ====================
    
    def _search_pages_jaunes_france(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Scraping de Pages Jaunes France (gratuit)"""
        leads = []
        try:
            base_url = "https://www.pagesjaunes.fr"
            
            search_queries = [
                "bureau étude GTB",
                "intégrateur GTB",
                "électricité bâtiment"
            ]
            
            for query in search_queries:
                try:
                    search_url = f"{base_url}/recherche"
                    params = {'quoiqui': query}
                    
                    response = self.session.get(search_url, params=params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Chercher les résultats
                        results = (
                            soup.find_all('div', class_=lambda x: x and 'bi-bloc' in x.lower()) or
                            soup.find_all('article', class_=lambda x: x and 'bi-bloc' in x.lower()) or
                            soup.find_all('div', class_=lambda x: x and 'resultat' in x.lower())
                        )
                        
                        for result in results[:10]:
                            try:
                                # Nom
                                name_elem = result.find('h2') or result.find('a', class_='denomination-links')
                                name = name_elem.get_text().strip() if name_elem else ""
                                
                                if not name:
                                    continue
                                
                                # Adresse
                                address_elem = result.find('span', class_=lambda x: x and 'ville' in x.lower())
                                city = address_elem.get_text().strip() if address_elem else ""
                                
                                # Téléphone
                                phone_elem = result.find('strong', class_=lambda x: x and 'num' in x.lower())
                                phone = phone_elem.get_text().strip() if phone_elem else ""
                                
                                # Site web
                                website_elem = result.find('a', href=re.compile(r'http'))
                                website = website_elem['href'] if website_elem else ""
                                
                                lead_data = {
                                    'lead_type': 'entreprise',
                                    'title': f"Entreprise {name}",
                                    'description': result.get_text().strip()[:1000],
                                    'organization_name': name,
                                    'website': website,
                                    'phone': phone,
                                    'city': city or "France",
                                    'country': 'France',
                                    'source_url': f"{base_url}/recherche?quoiqui={query}",
                                    'keywords_found': ['GTB', 'GTEB'],
                                    'raw_data': {}
                                }
                                
                                leads.append(lead_data)
                                
                                if len(leads) >= max_results:
                                    break
                            
                            except Exception as e:
                                logger.warning(f"Erreur parsing Pages Jaunes: {e}")
                                continue
                    
                    time.sleep(3)
                    
                except Exception as e:
                    logger.warning(f"Erreur recherche Pages Jaunes pour {query}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erreur recherche Pages Jaunes: {e}")
        
        return leads
    
    # ==================== RECHERCHE D'ENTREPRISES (PRINCIPALE) ====================
    
    def search_companies_gtb(self, country: str = "Maroc", max_results: int = 100) -> List[Dict[str, Any]]:
        """Recherche d'entreprises GTB/GTEB via méthodes gratuites"""
        leads = []
        
        # Méthode 1: OpenStreetMap (gratuit)
        try:
            osm_leads = self.search_companies_gtb_osm(country, max_results // 2)
            leads.extend(osm_leads)
        except Exception as e:
            logger.warning(f"Erreur recherche OSM: {e}")
        
        # Méthode 2: Scraping d'annuaires selon le pays
        try:
            if country == "Maroc":
                kerix_leads = self._search_kerix_maroc(max_results // 2)
                leads.extend(kerix_leads)
            elif country == "France":
                pj_leads = self._search_pages_jaunes_france(max_results // 2)
                leads.extend(pj_leads)
        except Exception as e:
            logger.warning(f"Erreur recherche annuaires: {e}")
        
        return leads[:max_results]
    
    # ==================== INDEED (OFFRES D'EMPLOI - GRATUIT) ====================
    
    def _search_indeed_maroc(self, max_results: int = 25) -> List[Dict[str, Any]]:
        """Scraping Indeed Maroc (gratuit)"""
        leads = []
        try:
            base_url = "https://ma.indeed.com"
            
            for keyword in ["GTB", "Gestion technique bâtiment", "Électricité bâtiment"]:
                try:
                    search_url = f"{base_url}/jobs"
                    params = {
                        'q': keyword,
                        'l': 'Maroc'
                    }
                    
                    response = self.session.get(search_url, params=params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Chercher les offres
                        jobs = (
                            soup.find_all('div', class_=lambda x: x and 'job' in x.lower()) or
                            soup.find_all('div', {'data-jk': True}) or
                            soup.find_all('a', {'data-jk': True})
                        )
                        
                        for job in jobs[:10]:
                            try:
                                # Titre
                                title_elem = job.find('h2') or job.find('a', class_=lambda x: x and 'title' in x.lower())
                                title = title_elem.get_text().strip() if title_elem else ""
                                
                                if not title:
                                    continue
                                
                                # Entreprise
                                company_elem = job.find('span', class_=lambda x: x and 'company' in x.lower())
                                company = company_elem.get_text().strip() if company_elem else ""
                                
                                # Localisation
                                location_elem = job.find('div', class_=lambda x: x and 'location' in x.lower())
                                location = location_elem.get_text().strip() if location_elem else ""
                                
                                # Lien
                                link_elem = job.find('a', href=True)
                                job_url = ""
                                if link_elem:
                                    href = link_elem['href']
                                    job_url = href if href.startswith('http') else base_url + href
                                
                                if company:
                                    lead_data = {
                                        'lead_type': 'offre_emploi',
                                        'title': f"Offre d'emploi GTB - {company}",
                                        'description': f"Recherche: {title}. Localisation: {location}",
                                        'organization_name': company,
                                        'city': self._extract_city_from_text(location),
                                        'country': 'Maroc',
                                        'source_url': job_url,
                                        'keywords_found': ['GTB', 'GTEB'],
                                        'raw_data': {'job_title': title, 'location': location}
                                    }
                                    
                                    leads.append(lead_data)
                                    
                                    if len(leads) >= max_results:
                                        break
                            
                            except Exception as e:
                                logger.warning(f"Erreur parsing offre Indeed: {e}")
                                continue
                    
                    time.sleep(3)
                    
                except Exception as e:
                    logger.warning(f"Erreur recherche Indeed pour {keyword}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erreur recherche Indeed Maroc: {e}")
        
        return leads
    
    def _search_indeed_france(self, max_results: int = 25) -> List[Dict[str, Any]]:
        """Scraping Indeed France (gratuit)"""
        leads = []
        try:
            base_url = "https://fr.indeed.com"
            
            for keyword in ["GTB", "Gestion technique bâtiment", "Électricité bâtiment"]:
                try:
                    search_url = f"{base_url}/jobs"
                    params = {
                        'q': keyword,
                        'l': 'France'
                    }
                    
                    response = self.session.get(search_url, params=params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        jobs = (
                            soup.find_all('div', class_=lambda x: x and 'job' in x.lower()) or
                            soup.find_all('div', {'data-jk': True})
                        )
                        
                        for job in jobs[:10]:
                            try:
                                title_elem = job.find('h2') or job.find('a')
                                title = title_elem.get_text().strip() if title_elem else ""
                                
                                if not title:
                                    continue
                                
                                company_elem = job.find('span', class_=lambda x: x and 'company' in x.lower())
                                company = company_elem.get_text().strip() if company_elem else ""
                                
                                location_elem = job.find('div', class_=lambda x: x and 'location' in x.lower())
                                location = location_elem.get_text().strip() if location_elem else ""
                                
                                if company:
                                    lead_data = {
                                        'lead_type': 'offre_emploi',
                                        'title': f"Offre d'emploi GTB - {company}",
                                        'description': f"Recherche: {title}. Localisation: {location}",
                                        'organization_name': company,
                                        'city': self._extract_city_from_text(location),
                                        'country': 'France',
                                        'source_url': base_url,
                                        'keywords_found': ['GTB', 'GTEB'],
                                        'raw_data': {'job_title': title}
                                    }
                                    
                                    leads.append(lead_data)
                                    
                                    if len(leads) >= max_results:
                                        break
                            
                            except Exception as e:
                                logger.warning(f"Erreur parsing offre Indeed: {e}")
                                continue
                    
                    time.sleep(3)
                    
                except Exception as e:
                    logger.warning(f"Erreur recherche Indeed pour {keyword}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erreur recherche Indeed France: {e}")
        
        return leads
    
    # ==================== RECHERCHE D'OFFRES D'EMPLOI (PRINCIPALE) ====================
    
    def search_job_offers_gtb(self, country: str = "Maroc", max_results: int = 50) -> List[Dict[str, Any]]:
        """Recherche d'offres d'emploi GTB/GTEB (indicateur de besoin) - Gratuit"""
        leads = []
        try:
            if country == "Maroc":
                leads.extend(self._search_indeed_maroc(max_results))
            elif country == "France":
                leads.extend(self._search_indeed_france(max_results))
        except Exception as e:
            logger.error(f"Erreur recherche offres d'emploi: {e}")
        
        return leads
    
    # ==================== GÉNÉRATION D'EXEMPLES (FALLBACK) ====================
    
    def generate_example_leads(self, countries: List[str] = None) -> List[Dict[str, Any]]:
        """Génère des leads d'exemple pour tester le système"""
        if countries is None:
            countries = ["Maroc", "France", "Canada"]
        
        example_leads = []
        
        # Exemples de marchés publics
        if "Maroc" in countries:
            example_leads.append({
                'lead_type': 'marche_public',
                'title': 'Marché public - Installation GTB pour hôpital régional',
                'description': 'Appel d\'offres pour l\'installation d\'un système de gestion technique du bâtiment (GTB) dans un nouvel hôpital régional. Le projet comprend la supervision des équipements CVC, éclairage et sécurité.',
                'organization_name': 'Ministère de la Santé - Maroc',
                'city': 'Casablanca',
                'country': 'Maroc',
                'market_date': datetime.now().date(),
                'budget': 2500000.00,
                'market_url': 'https://example.com/marche-123',
                'source_url': 'https://example.com/marche-123',
                'keywords_found': ['GTB', 'Gestion technique du bâtiment', 'Supervision bâtiment'],
                'raw_data': {}
            })
        
        if "France" in countries:
            example_leads.append({
                'lead_type': 'marche_public',
                'title': 'Maintenance et évolution système GTB - Bâtiment administratif',
                'description': 'Marché public pour la maintenance et l\'évolution du système de gestion technique du bâtiment d\'un bâtiment administratif de 5000 m². Prestations incluant supervision, automatismes CVC et électricité.',
                'organization_name': 'Mairie de Paris',
                'city': 'Paris',
                'country': 'France',
                'market_date': (datetime.now() + timedelta(days=30)).date(),
                'budget': 180000.00,
                'market_url': 'https://example.com/marche-456',
                'source_url': 'https://example.com/marche-456',
                'keywords_found': ['GTB', 'Automatisme CVC', 'Supervision'],
                'raw_data': {}
            })
        
        # Exemples d'entreprises
        for country in countries:
            if country == "Maroc":
                example_leads.append({
                    'lead_type': 'entreprise',
                    'title': 'Bureau d\'études spécialisé en GTB et GTEB',
                    'description': 'Bureau d\'études technique spécialisé dans la conception et l\'intégration de systèmes GTB et GTEB pour le secteur industriel et tertiaire.',
                    'organization_name': 'TechBâtiment Solutions',
                    'city': 'Rabat',
                    'country': 'Maroc',
                    'website': 'https://example.com/techbatiment',
                    'source_url': 'https://example.com/techbatiment',
                    'keywords_found': ['GTB', 'GTEB'],
                    'raw_data': {}
                })
        
        return example_leads
    
    # ==================== RECHERCHE GLOBALE ====================
    
    def search_all_sources(self, countries: List[str] = None) -> Dict[str, Any]:
        """Recherche sur toutes les sources configurées (100% gratuit)
        
        Retourne un rapport détaillé des recherches effectuées
        """
        if countries is None:
            countries = ["Maroc", "France", "Canada"]
        
        all_leads = []
        search_report = {
            'sources_consulted': [],
            'sources_with_results': [],
            'sources_without_results': [],
            'errors': [],
            'total_leads_found': 0
        }
        
        # Marchés publics
        if "France" in countries:
            try:
                logger.info("Recherche sur BOAMP (France)...")
                leads_fr = self.search_public_markets_france()
                search_report['sources_consulted'].append({
                    'name': 'BOAMP (France)',
                    'url': 'https://www.boamp.fr',
                    'type': 'Marchés publics'
                })
                if leads_fr:
                    search_report['sources_with_results'].append('BOAMP (France)')
                    all_leads.extend(leads_fr)
                else:
                    search_report['sources_without_results'].append('BOAMP (France)')
            except Exception as e:
                logger.error(f"Erreur recherche BOAMP: {e}")
                search_report['errors'].append({
                    'source': 'BOAMP (France)',
                    'error': str(e)
                })
        
        if "Maroc" in countries:
            try:
                logger.info("Recherche sur Portail Marocain...")
                leads_ma = self.search_public_markets_morocco()
                search_report['sources_consulted'].append({
                    'name': 'Portail Marocain',
                    'url': 'https://www.marchespublics.gov.ma',
                    'type': 'Marchés publics'
                })
                if leads_ma:
                    search_report['sources_with_results'].append('Portail Marocain')
                    all_leads.extend(leads_ma)
                else:
                    search_report['sources_without_results'].append('Portail Marocain')
            except Exception as e:
                logger.error(f"Erreur recherche Portail Marocain: {e}")
                search_report['errors'].append({
                    'source': 'Portail Marocain',
                    'error': str(e)
                })
        
        if "Canada" in countries:
            try:
                logger.info("Recherche sur sources canadiennes...")
                leads_ca = self.search_public_markets_canada()
                search_report['sources_consulted'].append({
                    'name': 'Sources Canada',
                    'url': 'MERX, Buyandsell.gc.ca',
                    'type': 'Marchés publics'
                })
                if leads_ca:
                    search_report['sources_with_results'].append('Sources Canada')
                    all_leads.extend(leads_ca)
                else:
                    search_report['sources_without_results'].append('Sources Canada')
            except Exception as e:
                logger.error(f"Erreur recherche Canada: {e}")
                search_report['errors'].append({
                    'source': 'Sources Canada',
                    'error': str(e)
                })
        
        # Entreprises
        for country in countries:
            try:
                logger.info(f"Recherche entreprises {country}...")
                companies = self.search_companies_gtb(country=country)
                
                # OpenStreetMap
                search_report['sources_consulted'].append({
                    'name': f'OpenStreetMap ({country})',
                    'url': 'https://www.openstreetmap.org',
                    'type': 'Entreprises'
                })
                
                # Annuaires selon le pays
                if country == "Maroc":
                    search_report['sources_consulted'].append({
                        'name': f'Kerix ({country})',
                        'url': 'https://www.kerix.net',
                        'type': 'Entreprises'
                    })
                elif country == "France":
                    search_report['sources_consulted'].append({
                        'name': f'Pages Jaunes ({country})',
                        'url': 'https://www.pagesjaunes.fr',
                        'type': 'Entreprises'
                    })
                
                if companies:
                    search_report['sources_with_results'].append(f'Entreprises {country}')
                    all_leads.extend(companies)
                else:
                    search_report['sources_without_results'].append(f'Entreprises {country}')
            except Exception as e:
                logger.error(f"Erreur recherche entreprises {country}: {e}")
                search_report['errors'].append({
                    'source': f'Entreprises {country}',
                    'error': str(e)
                })
            
            # Offres d'emploi
            try:
                logger.info(f"Recherche offres d'emploi {country}...")
                jobs = self.search_job_offers_gtb(country=country)
                
                search_report['sources_consulted'].append({
                    'name': f'Indeed ({country})',
                    'url': f'https://{"ma" if country == "Maroc" else "fr"}.indeed.com',
                    'type': 'Offres d\'emploi'
                })
                
                if jobs:
                    search_report['sources_with_results'].append(f'Offres emploi {country}')
                    all_leads.extend(jobs)
                else:
                    search_report['sources_without_results'].append(f'Offres emploi {country}')
            except Exception as e:
                logger.error(f"Erreur recherche offres emploi {country}: {e}")
                search_report['errors'].append({
                    'source': f'Offres emploi {country}',
                    'error': str(e)
                })
        
        search_report['total_leads_found'] = len(all_leads)
        
        # Ne plus utiliser de fallback automatique - retourner un rapport transparent
        if len(all_leads) == 0:
            logger.info("Aucun lead trouvé après recherche sur toutes les sources configurées")
        
        return {
            'leads': all_leads,
            'report': search_report
        }
