import logging
import json
import re
from typing import Dict, Any

from .zammad_api import ZammadAPIService
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


def extract_json_from_llm(text: str) -> Dict[str, Any]:
    """
    Extrait le premier objet JSON valide depuis une réponse LLM.
    """
    if not text:
        raise ValueError("Réponse IA vide")

    text = text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("Aucun JSON trouvé dans la réponse IA")

    return json.loads(match.group(0))


class KnowledgeBaseService:
    def __init__(self):
        self.zammad_api = ZammadAPIService()
        self.llm_client = LLMClient()

    # ==========================================================
    # SUGGESTION IA
    # ==========================================================
    def suggest_knowledge_article(
        self,
        ticket_analysis: Dict[str, Any],
        ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        try:
            article_content = self._generate_article_content(
                ticket_analysis, ticket_data
            )

            if not article_content["success"]:
                return article_content

            return {
                "success": True,
                "suggestion": {
                    "title": article_content["title"],
                    "content": article_content["content"],
                    "category": article_content["category"],
                    "should_create": article_content["should_create"],
                    "reason": article_content["reason"],
                },
            }

        except Exception as e:
            logger.exception("Erreur suggestion article KB")
            return {"success": False, "error": str(e)}

    def _generate_article_content(
        self,
        ticket_analysis: Dict[str, Any],
        ticket_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        prompt = f"""
Analyse ce ticket et crée un article de base de connaissance.

TICKET:
- Titre: {ticket_data.get('title', '')}
- Description: {ticket_data.get('body', '')}
- Statut: {ticket_data.get('status', '')}
- Catégorie: {ticket_analysis.get('category', '')}
- Priorité: {ticket_analysis.get('priority_label', '')}

Réponds STRICTEMENT en JSON valide.
"""

        system_prompt = """
Tu es un service backend.
Réponds UNIQUEMENT avec un JSON strictement valide.
Aucun texte avant ou après.
Aucun markdown.

Format :
{
  "should_create": true,
  "reason": "Justification",
  "title": "Titre",
  "content": "Contenu",
  "category": "Procédures Internes"
}
"""

        result = self.llm_client.call_api(prompt, system_prompt)

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Erreur IA"),
            }

        raw_content = result.get("content", "")
        logger.info("Réponse IA brute:\n%s", raw_content)

        try:
            data = extract_json_from_llm(raw_content)

            return {
                "success": True,
                "should_create": data.get("should_create", False),
                "reason": data.get("reason", ""),
                "title": data.get("title", ""),
                "content": data.get("content", ""),
                "category": data.get("category", "Procédures Internes"),
            }

        except Exception as e:
            logger.error("Erreur parsing JSON IA: %s", e)
            return {"success": False, "error": "Réponse IA invalide"}

    # ==========================================================
    # CRÉATION ARTICLE (CORRIGÉ)
    # ==========================================================
    def create_knowledge_article(
        self,
        title: str,
        content: str,
        category: str = "Procédures Internes",
        knowledge_base_id: int = 1
    ) -> Dict[str, Any]:
        """
        Crée un article de base de connaissance dans Zammad.
        Signature COMPATIBLE avec la view.
        """
        try:
            if not title or not content:
                return {
                    "success": False,
                    "error": "Titre et contenu requis"
                }

            # Mapping catégories → category_id Zammad
            category_mapping = {
                "Procédures Internes": 1,
                "commercial": 1,
                "technique": 2,
                "support": 3,
            }

            category_id = category_mapping.get(category, 1)

            result = self.zammad_api.create_knowledge_base_answer(
                category_id=category_id,
                title=title,
                content=content,
                internal=True
            )

            return {
                "success": True,
                "article_id": result.get("id"),
                "message": "Article créé avec succès"
            }

        except Exception as e:
            logger.exception("Erreur création article KB")
            return {"success": False, "error": str(e)}
