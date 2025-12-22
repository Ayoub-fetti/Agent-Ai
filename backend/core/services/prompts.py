# backend/core/services/prompts.py
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SupportPrompts:
    
    @staticmethod
    def get_system_prompt() -> str:
        return """Tu es un agent de support technique expert. 
Analyse les tickets et génère des réponses professionnelles en français.
Réponds toujours au format JSON avec les champs: analyse, reponse, priorite."""
    
    @staticmethod
    def analyze_ticket(ticket_content: str, client_info: str = "") -> str:
        return f"""
Analyse ce ticket de support:

Contenu: {ticket_content}
Client: {client_info}

Fournis une analyse structurée avec:
- Type de problème
- Urgence (1-5)
- Compétences requises
- Temps estimé de résolution
"""
    
    @staticmethod
    def generate_response(ticket_analysis: str, knowledge_base: str = "") -> str:
        return f"""
Génère une réponse professionnelle basée sur cette analyse:

Analyse: {ticket_analysis}
Base de connaissances: {knowledge_base}

La réponse doit être:
- Courtoise et professionnelle
- Technique mais accessible
- Avec étapes claires si nécessaire
"""
    
    @staticmethod
    def validate_json_format(response: str) -> Dict[str, Any]:
        """Validation format JSON"""
        try:
            parsed = json.loads(response)
            required_fields = ["analyse", "reponse", "priorite"]
            
            if all(field in parsed for field in required_fields):
                return {"valid": True, "data": parsed}
            else:
                missing = [f for f in required_fields if f not in parsed]
                return {"valid": False, "error": f"Champs manquants: {missing}"}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON validation error: {str(e)}")
            return {"valid": False, "error": "Format JSON invalide"}
