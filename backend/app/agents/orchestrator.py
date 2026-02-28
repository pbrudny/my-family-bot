"""
Orchestrator Agent

Coordinates the full pipeline:
  1. Detect language
  2. Generate Cypher
  3. Execute query
  4. Format response
"""
import logging

from app.agents.cypher_generator import generate_cypher
from app.agents.language_detector import detect_language
from app.agents.response_formatter import format_response
from app.db.neo4j_client import run_read_query

logger = logging.getLogger(__name__)


class OrchestratorError(Exception):
    """Raised when the pipeline cannot produce a safe response."""


async def process(
    message: str,
    user_id: str,
    language: str | None = None,
) -> str:
    """
    Run the full agent pipeline for a user message.

    Args:
        message:  Raw user question.
        user_id:  Person.id from Neo4j (the identity of the asking user).
        language: Pre-detected language code (pl/cs/en); detected automatically if None.

    Returns:
        Natural-language answer string.
    """
    # Step 1: Language detection
    lang = language or await detect_language(message)
    logger.info("Processing message | user=%s lang=%s", user_id, lang)

    # Step 2: Cypher generation (may raise ValueError for forbidden queries)
    try:
        cypher = await generate_cypher(message, lang)
    except ValueError as exc:
        logger.warning("Cypher validation failed: %s", exc)
        raise OrchestratorError(
            _no_data_msg(lang, reason="security")
        ) from exc
    except RuntimeError as exc:
        logger.error("Cypher generation error: %s", exc)
        raise OrchestratorError(_error_msg(lang)) from exc

    # Step 3: Execute read-only query
    try:
        records = await run_read_query(cypher, {"userId": user_id})
    except Exception as exc:
        logger.error("Neo4j query failed: %s", exc)
        raise OrchestratorError(_error_msg(lang)) from exc

    # Step 4: Format response
    try:
        answer = await format_response(records, lang, message)
    except Exception as exc:
        logger.error("Response formatting failed: %s", exc)
        raise OrchestratorError(_error_msg(lang)) from exc

    return answer


# --- Localised fallback messages ---

def _no_data_msg(lang: str, reason: str = "") -> str:
    msgs = {
        "pl": "Nie mogę przetworzyć tego zapytania.",
        "cs": "Tento dotaz nemohu zpracovat.",
        "en": "I cannot process this query.",
    }
    return msgs.get(lang, msgs["en"])


def _error_msg(lang: str) -> str:
    msgs = {
        "pl": "Wystąpił błąd podczas przetwarzania zapytania. Spróbuj ponownie.",
        "cs": "Při zpracování dotazu došlo k chybě. Zkuste to znovu.",
        "en": "An error occurred while processing your query. Please try again.",
    }
    return msgs.get(lang, msgs["en"])
