# backend/core/services/llm_client.py
import logging
import time
import json
from typing import Dict, Any
from decouple import config
import requests

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = config('OPEN_ROUTER_API_KEY')
        self.timeout = 30
        self.max_retries = 3
    
    def call_api(self, prompt: str, system_prompt: str = "", model: str = "meta-llama/llama-3.1-8b-instruct:free") -> Dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                }
                
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                duration = time.time() - start_time
                logger.info(f"OpenRouter API - {duration:.2f}s")
                
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"]
                }
                
            except Exception as e:
                logger.error(f"API error attempt {attempt + 1}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": str(e)}
                time.sleep(2 ** attempt)
        
        return {"success": False, "error": "Max retries exceeded"}
