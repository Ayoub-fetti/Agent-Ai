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
    
    def call_api(self, prompt: str, system_prompt: str = "", model: str = "meta-llama/llama-3.2-3b-instruct:free") -> Dict[str, Any]:
        logger.info(f"Using API key: {self.api_key[:20]}...")
        
        for attempt in range(self.max_retries):
            try:
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
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://agent-ai.local",
                        "X-Title": "Agent-AI"
                    },
                    json=payload,
                    timeout=self.timeout
                )
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response text: {response.text}")
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"]
                }
                
            except Exception as e:
                logger.error(f"API error: {str(e)}")
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": str(e)}
                time.sleep(2)
        
        return {"success": False, "error": "Max retries exceeded"}
