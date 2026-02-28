"""
Response Formatting Agent

Converts Neo4j result records into a natural-language response
in the user's detected language (pl / cs / en).
"""
import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

SYSTEM_PROMPT = """You are a friendly family-tree assistant.
You receive JSON data from a Neo4j database query and convert it into a clear, natural response.

Rules:
- Reply in the language specified by the "language" field
- If the result is empty, clearly state that no data was found (in the correct language)
- If the list has more than 10 items, summarize (e.g. "There are 15 cousins: ...")
- Do not mention technical details (Cypher, Neo4j, JSON)
- Be warm and conversational — this is a family app
- If dates are present, format them readably"""

LANGUAGE_NAMES = {"pl": "Polish", "cs": "Czech", "en": "English"}


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def format_response(records: list[dict[str, Any]], language: str, question: str) -> str:
    """Convert Neo4j result records into a natural-language answer."""
    lang_name = LANGUAGE_NAMES.get(language, "English")
    user_content = json.dumps(
        {
            "language": lang_name,
            "original_question": question,
            "data": records,
        },
        ensure_ascii=False,
        indent=2,
    )
    try:
        response = await _get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        answer = response.choices[0].message.content or ""
        logger.debug("Formatted response (%s): %s", language, answer[:100])
        return answer
    except Exception as exc:
        logger.exception("Response formatting failed")
        # Fallback: raw JSON
        return f"Result: {json.dumps(records, ensure_ascii=False)}"
