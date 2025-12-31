# backend/core/services/lead_normalizer.py
import logging
import re
from typing import Dict, Any, List
from unidecode import unidecode

logger = logging.getLogger(__name__)

class LeadNormalizer:
    """Service de normalisation des données de leads"""
    
    # Mots-clés pour détecter le type de projet
    GTB_KEYWORDS = ["gtb", "gtc", "bms", "gestion technique", "supervision bâtiment", "automatisme cvc"]
    GTEB_KEYWORDS = ["gteb", "génie technique électrique", "électricité bâtiment", "courants forts", "courants faibles"]
    CVC_KEYWORDS = ["cvc", "chauffage", "ventilation", "climatisation"]
    SUPERVISION_KEYWORDS = ["supervision", "monitoring", "contrôle"]
    ELECTRICITE_KEYWORDS = ["électricité", "électrique", "installation électrique"]
    
    # Normalisation des villes
    CITY_NORMALIZATIONS = {
        "casablanca": "Casablanca",
        "rabat": "Rabat",
        "fes": "Fès",
        "marrakech": "Marrakech",
        "tanger": "Tanger",
        "paris": "Paris",
        "lyon": "Lyon",
        "marseille": "Marseille",
        "montreal": "Montréal",
        "toronto": "Toronto",
        "vancouver": "Vancouver"
    }
    
    # Normalisation des pays
    COUNTRY_NORMALIZATIONS = {
        "maroc": "Maroc",
        "morocco": "Maroc",
        "france": "France",
        "canada": "Canada"
    }
    
    def normalize_company_name(self, name: str) -> str:
        """Normalise le nom d'une entreprise"""
        if not name:
            return ""
        
        # Supprimer les espaces multiples
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Capitaliser correctement
        # Garder les acronymes en majuscules
        words = name.split()
        normalized_words = []
        for word in words:
            if word.isupper() and len(word) > 1:
                normalized_words.append(word)
            elif word.lower() in ['sa', 'sarl', 'sas', 'eurl', 'ltd', 'inc']:
                normalized_words.append(word.upper())
            else:
                normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    
    def normalize_city(self, city: str) -> str:
        """Normalise le nom d'une ville"""
        if not city:
            return ""
        
        city_lower = city.lower().strip()
        city_lower = unidecode(city_lower)  # Enlever les accents pour la recherche
        
        # Chercher dans les normalisations
        for key, value in self.CITY_NORMALIZATIONS.items():
            if key in city_lower:
                return value
        
        # Sinon, capitaliser la première lettre
        return city.strip().title()
    
    def normalize_country(self, country: str) -> str:
        """Normalise le nom d'un pays"""
        if not country:
            return "Maroc"  # Par défaut
        
        country_lower = country.lower().strip()
        country_lower = unidecode(country_lower)
        
        for key, value in self.COUNTRY_NORMALIZATIONS.items():
            if key in country_lower:
                return value
        
        return country.strip().title()
    
    def detect_project_type(self, text: str) -> str:
        """Détecte le type de projet depuis un texte"""
        if not text:
            return None
        
        text_lower = text.lower()
        text_lower = unidecode(text_lower)
        
        # Compter les occurrences de chaque type
        scores = {
            'GTB': sum(1 for kw in self.GTB_KEYWORDS if kw in text_lower),
            'GTEB': sum(1 for kw in self.GTEB_KEYWORDS if kw in text_lower),
            'CVC': sum(1 for kw in self.CVC_KEYWORDS if kw in text_lower),
            'supervision': sum(1 for kw in self.SUPERVISION_KEYWORDS if kw in text_lower),
            'electricite': sum(1 for kw in self.ELECTRICITE_KEYWORDS if kw in text_lower),
        }
        
        # Si plusieurs types détectés
        if sum(scores.values()) > 1:
            return 'MIXTE'
        
        # Retourner le type avec le score le plus élevé
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def normalize_email(self, email: str) -> str:
        """Normalise et valide un email"""
        if not email:
            return ""
        
        email = email.strip().lower()
        
        # Validation basique
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email
        
        return ""
    
    def normalize_phone(self, phone: str) -> str:
        """Normalise un numéro de téléphone"""
        if not phone:
            return ""
        
        # Supprimer tous les caractères non numériques sauf + au début
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Format standard
        if phone.startswith('+'):
            return phone
        elif phone.startswith('00'):
            return '+' + phone[2:]
        elif len(phone) == 10 and phone.startswith('0'):
            # Numéro français/marocain
            return phone
        
        return phone
    
    def normalize_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise toutes les données d'un lead"""
        normalized = lead_data.copy()
        
        # Normaliser les champs texte
        if 'organization_name' in normalized:
            normalized['organization_name'] = self.normalize_company_name(
                normalized.get('organization_name', '')
            )
        
        if 'city' in normalized:
            normalized['city'] = self.normalize_city(normalized.get('city', ''))
        
        if 'country' in normalized:
            normalized['country'] = self.normalize_country(normalized.get('country', ''))
        
        if 'email' in normalized:
            normalized['email'] = self.normalize_email(normalized.get('email', ''))
        
        if 'phone' in normalized:
            normalized['phone'] = self.normalize_phone(normalized.get('phone', ''))
        
        # Détecter le type de projet
        text_for_detection = ' '.join([
            normalized.get('title', ''),
            normalized.get('description', '')
        ])
        project_type = self.detect_project_type(text_for_detection)
        if project_type:
            normalized['project_type'] = project_type
        
        return normalized

