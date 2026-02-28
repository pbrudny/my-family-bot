"""
Cypher Generation Agent

Converts a natural-language family-tree question into a read-only Neo4j Cypher query.
The user is always represented by the $userId parameter.
"""
import logging
import re

from openai import AsyncOpenAI

from app.config import settings
from app.db.neo4j_client import validate_cypher

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

SYSTEM_PROMPT = """You are a Cypher query generator for a family tree graph database.

Graph schema:
  Node: Person
    Properties: id, firstName, lastName, gender, birthDate, deathDate, birthPlace, currentCountry, whatsappId, preferredLanguage

  Relationships:
    (:Person)-[:PARENT_OF]->(:Person)
    (:Person)-[:MARRIED_TO]->(:Person)
    (:Person)-[:LIVES_IN]->(:Place)
    (:Person)-[:BORN_IN]->(:Place)

Rules:
- ALWAYS start the query with: MATCH (me:Person {id: $userId})
- Use $userId as the only parameter — never hardcode IDs
- Output raw Cypher only — no markdown, no code fences, no explanation
- Use ONLY these clauses: MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT
- NEVER use: CREATE, DELETE, MERGE, CALL, DROP, SET, REMOVE, FOREACH
- Queries must be read-only
- If "cousin" is asked: find children of parents' siblings (two PARENT_OF hops)
- If "uncle/aunt" is asked: find siblings of parents
- RETURN human-readable fields (firstName, lastName, etc.)

The question will be in any language, but always write Cypher in English."""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if present."""
    text = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()


async def generate_cypher(question: str, language: str) -> str:
    """
    Generate a Cypher query for the given question.

    Raises ValueError if the generated query contains forbidden keywords.
    """
    user_msg = f"Language: {language}\nQuestion: {question}"
    try:
        response = await _get_client().chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content or ""
        cypher = _strip_fences(raw)
        logger.debug("Generated Cypher: %s", cypher)

        # Security validation
        validate_cypher(cypher)

        return cypher
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Cypher generation failed")
        raise RuntimeError(f"Cypher generation error: {exc}") from exc
