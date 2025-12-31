"""
Sources supplémentaires de recherche de leads GTB/GTEB
"""
import logging
import re
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class AdditionalSourcesSearcher:
    """Classe pour rechercher sur les sources supplémentaires"""
    
    def __init__(self, session: requests.Session, keywords: List[str]):
        self.session = session
        self.keywords = keywords
    
    def _extract_city_from_text(self, text: str) -> str:
        """Extrait la ville depuis un texte"""
        if not text:
            return ""
        cities = ['Paris', 'Lyon', 'Marseille', 'Casablanca', 'Rabat', 'Montréal', 'Toronto']
        text_lower = text.lower()
        for city in cities:
            if city.lower() in text_lower:
                return city
        return ""
    
    def _parse_date(self, date_str: str):
        """Parse une date"""
        if not date_str:
            return None
        try:
            from datetime import datetime
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    return datetime.strptime(date_str[:10], fmt).date()
                except:
                    continue
        except:
            pass
        return None
    
    def _parse_budget(self, budget_str: str):
        """Parse un budget"""
        if not budget_str:
            return None
        try:
            numbers = re.findall(r'[\d\s,\.]+', budget_str.replace(',', '.'))
            if numbers:
                budget = float(numbers[0].replace(' ', '').replace(',', ''))
                if 'M' in budget_str.upper() or 'million' in budget_str.lower():
                    budget *= 1000000
                elif 'K' in budget_str.upper():
                    budget *= 1000
                return budget
        except:
            pass
        return None
    
    def _generic_scrape(self, base_url: str, search_path: str, params: Dict, selectors: Dict, source_name: str) -> List[Dict[str, Any]]:
        """Méthode générique pour scraper un site"""
        leads = []
        try:
            search_url = f"{base_url}{search_path}"
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher les résultats avec différents sélecteurs
                results = []
                for selector in selectors.get('results', []):
                    found = soup.select(selector) or soup.find_all(selector)
                    if found:
                        results = found
                        break
                
                for result in results[:10]:
                    try:
                        # Titre
                        title = ""
                        for sel in selectors.get('title', []):
                            elem = result.select_one(sel) if isinstance(sel, str) else result.find(sel)
                            if elem:
                                title = elem.get_text().strip()
                                break
                        
                        if not title:
                            continue
                        
                        # Détecter les mots-clés
                        text_content = title.lower()
                        keywords_found = [kw for kw in self.keywords if kw.lower() in text_content]
                        
                        if not keywords_found:
                            continue
                        
                        # Lien
                        link_elem = result.find('a', href=True)
                        market_url = ""
                        if link_elem:
                            href = link_elem['href']
                            market_url = href if href.startswith('http') else base_url + href
                        
                        # Organisation
                        organization = ""
                        for sel in selectors.get('organization', []):
                            elem = result.select_one(sel) if isinstance(sel, str) else result.find(sel)
                            if elem:
                                organization = elem.get_text().strip()
                                break
                        
                        lead_data = {
                            'lead_type': 'marche_public',
                            'title': title[:500],
                            'description': result.get_text().strip()[:5000],
                            'organization_name': organization or "Non spécifié",
                            'city': self._extract_city_from_text(title),
                            'country': 'France',
                            'market_url': market_url,
                            'source_url': market_url,
                            'keywords_found': keywords_found,
                            'raw_data': {}
                        }
                        
                        leads.append(lead_data)
                    
                    except Exception as e:
                        logger.warning(f"Erreur parsing {source_name}: {e}")
                        continue
            
            time.sleep(2)  # Respecter les serveurs
            
        except Exception as e:
            logger.warning(f"Erreur recherche {source_name}: {e}")
        
        return leads
    
    # ==================== MARCHÉS PUBLICS FRANCE ====================
    
    def search_marches_publics_gouv(self) -> List[Dict[str, Any]]:
        """https://www.marches-publics.gouv.fr"""
        return self._generic_scrape(
            "https://www.marches-publics.gouv.fr",
            "/recherche",
            {'q': 'GTB'},
            {
                'results': ['.resultat', 'article', '.marche'],
                'title': ['h2', 'h3', 'a.titre'],
                'organization': ['.organisateur', '.acheteur']
            },
            "Marches-publics.gouv.fr"
        )
    
    def search_achatpublic(self) -> List[Dict[str, Any]]:
        """https://www.achatpublic.com"""
        return self._generic_scrape(
            "https://www.achatpublic.com",
            "/recherche",
            {'motcle': 'GTB'},
            {
                'results': ['.resultat', 'tr.ligne'],
                'title': ['td.titre', 'a'],
                'organization': ['td.organisme']
            },
            "Achatpublic.com"
        )
    
    def search_emarchespublics(self) -> List[Dict[str, Any]]:
        """https://www.e-marchespublics.com"""
        return self._generic_scrape(
            "https://www.e-marchespublics.com",
            "/recherche",
            {'q': 'GTB'},
            {
                'results': ['.marche', 'article'],
                'title': ['h2', 'h3'],
                'organization': ['.organisme']
            },
            "E-marchespublics.com"
        )
    
    def search_francemarches(self) -> List[Dict[str, Any]]:
        """https://www.francemarches.com"""
        return self._generic_scrape(
            "https://www.francemarches.com",
            "/recherche",
            {'q': 'GTB'},
            {
                'results': ['.resultat', 'div.marche'],
                'title': ['h3', 'a'],
                'organization': ['.organisateur']
            },
            "Francemarches.com"
        )
    
    def search_ted_europa(self) -> List[Dict[str, Any]]:
        """https://ted.europa.eu"""
        leads = []
        try:
            # TED utilise une API ou un format spécifique
            search_url = "https://ted.europa.eu/TED/search"
            params = {'q': 'GTB OR "Gestion technique bâtiment"'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=lambda x: x and 'notice' in x.lower())
                
                for result in results[:10]:
                    try:
                        title_elem = result.find('h3') or result.find('a')
                        title = title_elem.get_text().strip() if title_elem else ""
                        
                        if not title:
                            continue
                        
                        text_content = title.lower()
                        keywords_found = [kw for kw in self.keywords if kw.lower() in text_content]
                        
                        if keywords_found:
                            lead_data = {
                                'lead_type': 'marche_public',
                                'title': title[:500],
                                'description': result.get_text().strip()[:5000],
                                'organization_name': "Non spécifié",
                                'city': self._extract_city_from_text(title),
                                'country': 'Europe',
                                'source_url': "https://ted.europa.eu",
                                'keywords_found': keywords_found,
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche TED: {e}")
        
        return leads
    
    def search_dgmarket(self) -> List[Dict[str, Any]]:
        """https://www.dgmarket.com"""
        return self._generic_scrape(
            "https://www.dgmarket.com",
            "/tenders",
            {'q': 'GTB'},
            {
                'results': ['.tender', 'tr'],
                'title': ['h3', 'a.title'],
                'organization': ['.organization']
            },
            "Dgmarket.com"
        )
    
    def search_globaltenders(self) -> List[Dict[str, Any]]:
        """https://www.globaltenders.com"""
        return self._generic_scrape(
            "https://www.globaltenders.com",
            "/search",
            {'q': 'GTB'},
            {
                'results': ['.tender', '.result'],
                'title': ['h3', 'a'],
                'organization': ['.org']
            },
            "Globaltenders.com"
        )
    
    def search_tendersinfo(self) -> List[Dict[str, Any]]:
        """https://www.tendersinfo.com"""
        return self._generic_scrape(
            "https://www.tendersinfo.com",
            "/search",
            {'q': 'GTB'},
            {
                'results': ['.tender', 'div.result'],
                'title': ['h2', 'h3'],
                'organization': ['.company']
            },
            "Tendersinfo.com"
        )
    
    def search_eurolegales(self) -> List[Dict[str, Any]]:
        """https://www.eurolegales.com"""
        return self._generic_scrape(
            "https://www.eurolegales.com",
            "/recherche",
            {'q': 'GTB'},
            {
                'results': ['.marche', 'article'],
                'title': ['h3', 'a'],
                'organization': ['.organisme']
            },
            "Eurolegales.com"
        )
    
    # ==================== ANNUAIRES ENTREPRISES ====================
    
    def search_societe_com(self) -> List[Dict[str, Any]]:
        """https://www.societe.com"""
        leads = []
        try:
            search_url = "https://www.societe.com/cgi-bin/search"
            params = {'q': 'GTB OR "Gestion technique bâtiment"'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=lambda x: x and 'entreprise' in x.lower())
                
                for result in results[:10]:
                    try:
                        name_elem = result.find('h3') or result.find('a')
                        name = name_elem.get_text().strip() if name_elem else ""
                        
                        if not name:
                            continue
                        
                        lead_data = {
                            'lead_type': 'entreprise',
                            'title': f"Entreprise {name}",
                            'description': result.get_text().strip()[:1000],
                            'organization_name': name,
                            'city': self._extract_city_from_text(result.get_text()),
                            'country': 'France',
                            'source_url': "https://www.societe.com",
                            'keywords_found': ['GTB', 'GTEB'],
                            'raw_data': {}
                        }
                        leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Societe.com: {e}")
        
        return leads
    
    def search_infogreffe(self) -> List[Dict[str, Any]]:
        """https://www.infogreffe.fr"""
        # Similar to societe.com
        return self.search_societe_com()  # Utiliser la même logique
    
    def search_manageo(self) -> List[Dict[str, Any]]:
        """https://www.manageo.fr"""
        leads = []
        try:
            search_url = "https://www.manageo.fr/recherche"
            params = {'q': 'GTB'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=lambda x: x and 'company' in x.lower())
                
                for result in results[:10]:
                    try:
                        name_elem = result.find('h3') or result.find('a')
                        name = name_elem.get_text().strip() if name_elem else ""
                        
                        if name:
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': f"Entreprise {name}",
                                'description': result.get_text().strip()[:1000],
                                'organization_name': name,
                                'city': self._extract_city_from_text(result.get_text()),
                                'country': 'France',
                                'source_url': "https://www.manageo.fr",
                                'keywords_found': ['GTB', 'GTEB'],
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Manageo: {e}")
        
        return leads
    
    def search_charika_ma(self) -> List[Dict[str, Any]]:
        """https://www.charika.ma"""
        leads = []
        try:
            search_url = "https://www.charika.ma/recherche"
            params = {'q': 'GTB OR "Gestion technique"'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=lambda x: x and 'entreprise' in x.lower())
                
                for result in results[:10]:
                    try:
                        name_elem = result.find('h3') or result.find('a')
                        name = name_elem.get_text().strip() if name_elem else ""
                        
                        if name:
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': f"Entreprise {name}",
                                'description': result.get_text().strip()[:1000],
                                'organization_name': name,
                                'city': self._extract_city_from_text(result.get_text()),
                                'country': 'Maroc',
                                'source_url': "https://www.charika.ma",
                                'keywords_found': ['GTB', 'GTEB'],
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Charika: {e}")
        
        return leads
    
    def search_europages(self) -> List[Dict[str, Any]]:
        """https://www.europages.com"""
        leads = []
        try:
            search_url = "https://www.europages.com/search"
            params = {'q': 'GTB OR "Building Management System"'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=lambda x: x and 'company' in x.lower())
                
                for result in results[:10]:
                    try:
                        name_elem = result.find('h3') or result.find('a')
                        name = name_elem.get_text().strip() if name_elem else ""
                        
                        if name:
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': f"Entreprise {name}",
                                'description': result.get_text().strip()[:1000],
                                'organization_name': name,
                                'city': self._extract_city_from_text(result.get_text()),
                                'country': 'Europe',
                                'source_url': "https://www.europages.com",
                                'keywords_found': ['GTB', 'GTEB'],
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Europages: {e}")
        
        return leads
    
    def search_kompass(self) -> List[Dict[str, Any]]:
        """https://www.kompass.com"""
        leads = []
        try:
            search_url = "https://www.kompass.com/search"
            params = {'q': 'GTB OR "Building Management"'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=lambda x: x and 'company' in x.lower())
                
                for result in results[:10]:
                    try:
                        name_elem = result.find('h3') or result.find('a')
                        name = name_elem.get_text().strip() if name_elem else ""
                        
                        if name:
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': f"Entreprise {name}",
                                'description': result.get_text().strip()[:1000],
                                'organization_name': name,
                                'city': self._extract_city_from_text(result.get_text()),
                                'country': 'Europe',
                                'source_url': "https://www.kompass.com",
                                'keywords_found': ['GTB', 'GTEB'],
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Kompass: {e}")
        
        return leads
    
    # ==================== EMPLOI ====================
    
    def search_linkedin_jobs(self, country: str = "France") -> List[Dict[str, Any]]:
        """https://www.linkedin.com/jobs"""
        leads = []
        try:
            base_url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': 'GTB OR "Gestion technique bâtiment"',
                'location': country
            }
            
            response = self.session.get(base_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
                
                for job in jobs[:10]:
                    try:
                        title_elem = job.find('h3') or job.find('a')
                        title = title_elem.get_text().strip() if title_elem else ""
                        
                        company_elem = job.find('span', class_=lambda x: x and 'company' in x.lower())
                        company = company_elem.get_text().strip() if company_elem else ""
                        
                        if company and title:
                            lead_data = {
                                'lead_type': 'offre_emploi',
                                'title': f"Offre d'emploi GTB - {company}",
                                'description': f"Recherche: {title}",
                                'organization_name': company,
                                'city': self._extract_city_from_text(job.get_text()),
                                'country': country,
                                'source_url': "https://www.linkedin.com/jobs",
                                'keywords_found': ['GTB', 'GTEB'],
                                'raw_data': {'job_title': title}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche LinkedIn Jobs: {e}")
        
        return leads
    
    def search_glassdoor(self) -> List[Dict[str, Any]]:
        """https://www.glassdoor.com"""
        # Similar to LinkedIn
        return self.search_linkedin_jobs()
    
    def search_welcometothejungle(self) -> List[Dict[str, Any]]:
        """https://www.welcometothejungle.com"""
        leads = []
        try:
            search_url = "https://www.welcometothejungle.com/fr/jobs"
            params = {'q': 'GTB'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = soup.find_all('article', class_=lambda x: x and 'job' in x.lower())
                
                for job in jobs[:10]:
                    try:
                        title_elem = job.find('h3') or job.find('a')
                        title = title_elem.get_text().strip() if title_elem else ""
                        
                        company_elem = job.find('span', class_=lambda x: x and 'company' in x.lower())
                        company = company_elem.get_text().strip() if company_elem else ""
                        
                        if company:
                            lead_data = {
                                'lead_type': 'offre_emploi',
                                'title': f"Offre d'emploi GTB - {company}",
                                'description': f"Recherche: {title}",
                                'organization_name': company,
                                'city': self._extract_city_from_text(job.get_text()),
                                'country': 'France',
                                'source_url': "https://www.welcometothejungle.com",
                                'keywords_found': ['GTB', 'GTEB'],
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Welcome to the Jungle: {e}")
        
        return leads
    
    # ==================== BÂTIMENT / ÉNERGIE ====================
    
    def search_batiactu(self) -> List[Dict[str, Any]]:
        """https://www.batiactu.com"""
        leads = []
        try:
            search_url = "https://www.batiactu.com/recherche"
            params = {'q': 'GTB OR "Gestion technique bâtiment"'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('article', class_=lambda x: x and 'article' in x.lower())
                
                for result in results[:10]:
                    try:
                        title_elem = result.find('h2') or result.find('a')
                        title = title_elem.get_text().strip() if title_elem else ""
                        
                        text_content = title.lower()
                        keywords_found = [kw for kw in self.keywords if kw.lower() in text_content]
                        
                        if keywords_found:
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': title[:500],
                                'description': result.get_text().strip()[:5000],
                                'organization_name': "Non spécifié",
                                'city': self._extract_city_from_text(title),
                                'country': 'France',
                                'source_url': "https://www.batiactu.com",
                                'keywords_found': keywords_found,
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Batiactu: {e}")
        
        return leads
    
    def search_lemoniteur(self) -> List[Dict[str, Any]]:
        """https://www.lemoniteur.fr"""
        # Similar to batiactu
        return self.search_batiactu()
    
    def search_construction21(self) -> List[Dict[str, Any]]:
        """https://www.construction21.org"""
        leads = []
        try:
            search_url = "https://www.construction21.org/search"
            params = {'q': 'GTB'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('div', class_=lambda x: x and 'project' in x.lower())
                
                for result in results[:10]:
                    try:
                        title_elem = result.find('h3') or result.find('a')
                        title = title_elem.get_text().strip() if title_elem else ""
                        
                        text_content = title.lower()
                        keywords_found = [kw for kw in self.keywords if kw.lower() in text_content]
                        
                        if keywords_found:
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': title[:500],
                                'description': result.get_text().strip()[:5000],
                                'organization_name': "Non spécifié",
                                'city': self._extract_city_from_text(title),
                                'country': 'France',
                                'source_url': "https://www.construction21.org",
                                'keywords_found': keywords_found,
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Construction21: {e}")
        
        return leads
    
    def search_smartbuildingsmagazine(self) -> List[Dict[str, Any]]:
        """https://www.smartbuildingsmagazine.com"""
        leads = []
        try:
            search_url = "https://www.smartbuildingsmagazine.com/search"
            params = {'q': 'GTB OR BMS'}
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('article', class_=lambda x: x and 'article' in x.lower())
                
                for result in results[:10]:
                    try:
                        title_elem = result.find('h2') or result.find('a')
                        title = title_elem.get_text().strip() if title_elem else ""
                        
                        text_content = title.lower()
                        keywords_found = [kw for kw in self.keywords if kw.lower() in text_content]
                        
                        if keywords_found:
                            lead_data = {
                                'lead_type': 'entreprise',
                                'title': title[:500],
                                'description': result.get_text().strip()[:5000],
                                'organization_name': "Non spécifié",
                                'city': self._extract_city_from_text(title),
                                'country': 'France',
                                'source_url': "https://www.smartbuildingsmagazine.com",
                                'keywords_found': keywords_found,
                                'raw_data': {}
                            }
                            leads.append(lead_data)
                    except:
                        continue
            
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erreur recherche Smart Buildings Magazine: {e}")
        
        return leads

