# backend/core/services/llm_client.py
import logging
import time
from typing import Dict, Any
from decouple import config
import cohere

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_key = config('COHERE_API_KEY')
        self.client = cohere.ClientV2(api_key=self.api_key)
        self.timeout = 30
        self.max_retries = 3

    def call_api(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str = "command-a-03-2025"  # modèle actif recommandé
    ) -> Dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        logger.info(f"Using Cohere API key: {self.api_key[:20]}...")

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat(
                    model=model,
                    messages=messages
                )

                gen_text = ""
                if response.message and response.message.content:
                    gen_text = response.message.content[0].text

                return {"success": True, "content": gen_text}

            except Exception as e:
                logger.error(f"API error: {str(e)}")
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": str(e)}
                time.sleep(2)

        return {"success": False, "error": "Max retries exceeded"}
