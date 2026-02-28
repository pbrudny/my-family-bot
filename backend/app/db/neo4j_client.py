import logging
import re
from contextlib import asynccontextmanager
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import settings

logger = logging.getLogger(__name__)

_driver: AsyncDriver | None = None

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(CREATE|DELETE|MERGE|DROP|CALL|SET|REMOVE|FOREACH|LOAD\s+CSV)\b",
    re.IGNORECASE,
)
QUERY_TIMEOUT_S = 5
MAX_RESULT_LIMIT = 100


async def init_driver() -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    await _driver.verify_connectivity()
    logger.info("Neo4j driver initialised")


async def close_driver() -> None:
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


def get_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised — call init_driver() first")
    return _driver


def validate_cypher(query: str) -> None:
    """Raise ValueError if query contains forbidden write/admin keywords."""
    match = FORBIDDEN_KEYWORDS.search(query)
    if match:
        raise ValueError(f"Forbidden Cypher keyword detected: {match.group()}")


def _inject_limit(query: str) -> str:
    """Append LIMIT if not already present to cap result size."""
    if "LIMIT" not in query.upper():
        query = query.rstrip().rstrip(";") + f"\nLIMIT {MAX_RESULT_LIMIT}"
    return query


async def run_read_query(
    cypher: str, parameters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Execute a validated read-only Cypher query and return records as dicts."""
    validate_cypher(cypher)
    cypher = _inject_limit(cypher)
    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        result = await session.run(cypher, parameters or {}, timeout=QUERY_TIMEOUT_S)
        records = await result.data()
    return records


async def run_write_query(
    cypher: str, parameters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Execute a write Cypher query (internal use only — GEDCOM import, admin)."""
    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        result = await session.run(cypher, parameters or {})
        records = await result.data()
    return records
