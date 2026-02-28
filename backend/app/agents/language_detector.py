"""
Language Detection Agent

Detects whether the user's message is Polish (pl), Czech (cs), or English (en).
Returns a lowercase two-letter code.
"""
import logging

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

SYSTEM_PROMPT = (
    "You are a language detection tool. "
    "Detect the language of the user's message. "
    "Reply with ONLY one of these three codes: pl, cs, en. "
    "No punctuation, no explanation, no extra text."
)


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def detect_language(text: str) -> str:
    """Return 'pl', 'cs', or 'en'. Falls back to 'en' on error."""
    try:
        response = await _get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=5,
        )
        lang = response.choices[0].message.content.strip().lower()
        if lang not in ("pl", "cs", "en"):
            logger.warning("Unexpected language code '%s', defaulting to en", lang)
            return "en"
        logger.debug("Detected language: %s", lang)
        return lang
    except Exception:
        logger.exception("Language detection failed, defaulting to en")
        return "en"
