# backend/core/services/llm_client.py
import logging
import time
from typing import Dict, Any
from decouple import config
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = config('GOOGLE_AI_API_KEY')
        genai.configure(api_key=self.api_key)
        
        # Lister les modèles disponibles
        try:
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            logger.info(f"Available models: {available_models}")
            
            # Utiliser le premier modèle disponible ou un modèle par défaut
            if available_models:
                model_name = available_models[0].split('/')[-1]  # Extraire juste le nom
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Using model: {model_name}")
            else:
                # Fallback vers gemini-pro si aucun modèle trouvé
                self.model = genai.GenerativeModel('gemini-pro')
                
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            # Essayer avec gemini-pro par défaut
            self.model = genai.GenerativeModel('gemini-pro')
            
        self.max_retries = 3
    
    def call_api(self, prompt: str, system_prompt: str = "", model: str = None) -> Dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                # Combiner le system prompt avec le prompt utilisateur
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                
                response = self.model.generate_content(full_prompt)
                
                return {
                    "success": True,
                    "content": response.text
                }
                
            except Exception as e:
                logger.error(f"API error: {str(e)}")
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": str(e)}
                time.sleep(2)
        
        return {"success": False, "error": "Max retries exceeded"}
