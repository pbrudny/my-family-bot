"""
Unit tests for agents and Cypher validator.
All external calls (OpenAI, Neo4j) are mocked.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Language detector
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_detect_language_polish():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "pl"

    with patch("app.agents.language_detector._get_client") as mock_get:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get.return_value = client

        from app.agents.language_detector import detect_language
        result = await detect_language("Kto jest moją babcią?")

    assert result == "pl"


@pytest.mark.asyncio
async def test_detect_language_fallback_on_unknown():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "de"  # Not in allowed set

    with patch("app.agents.language_detector._get_client") as mock_get:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get.return_value = client

        from app.agents.language_detector import detect_language
        result = await detect_language("Wer ist meine Großmutter?")

    assert result == "en"  # Falls back to en


@pytest.mark.asyncio
async def test_detect_language_fallback_on_exception():
    with patch("app.agents.language_detector._get_client") as mock_get:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_get.return_value = client

        from app.agents.language_detector import detect_language
        result = await detect_language("anything")

    assert result == "en"


# ---------------------------------------------------------------------------
# Cypher validator
# ---------------------------------------------------------------------------

def test_cypher_validator_allows_match():
    from app.db.neo4j_client import validate_cypher
    # Should not raise
    validate_cypher("MATCH (me:Person {id: $userId}) RETURN me.firstName")


def test_cypher_validator_blocks_create():
    from app.db.neo4j_client import validate_cypher
    with pytest.raises(ValueError, match="CREATE"):
        validate_cypher("CREATE (p:Person {id: '1'})")


def test_cypher_validator_blocks_delete():
    from app.db.neo4j_client import validate_cypher
    with pytest.raises(ValueError, match="DELETE"):
        validate_cypher("MATCH (p:Person) DELETE p")


def test_cypher_validator_blocks_merge():
    from app.db.neo4j_client import validate_cypher
    with pytest.raises(ValueError, match="MERGE"):
        validate_cypher("MERGE (p:Person {id: '1'})")


def test_cypher_validator_blocks_drop():
    from app.db.neo4j_client import validate_cypher
    with pytest.raises(ValueError, match="DROP"):
        validate_cypher("DROP CONSTRAINT person_id")


def test_cypher_validator_case_insensitive():
    from app.db.neo4j_client import validate_cypher
    with pytest.raises(ValueError):
        validate_cypher("create (p:Person {id: '1'})")


# ---------------------------------------------------------------------------
# Cypher generator — strip fences
# ---------------------------------------------------------------------------

def test_strip_fences():
    from app.agents.cypher_generator import _strip_fences
    raw = "```cypher\nMATCH (me:Person {id: $userId}) RETURN me\n```"
    assert _strip_fences(raw) == "MATCH (me:Person {id: $userId}) RETURN me"


def test_strip_fences_no_fence():
    from app.agents.cypher_generator import _strip_fences
    raw = "MATCH (me:Person {id: $userId}) RETURN me"
    assert _strip_fences(raw) == raw


# ---------------------------------------------------------------------------
# Channel adapter
# ---------------------------------------------------------------------------

def test_web_message_always_processed():
    from app.channels.adapter import from_web, should_respond
    msg = from_web("hello", "user1")
    assert should_respond(msg) is True


def test_whatsapp_trigger_prefix():
    from app.channels.adapter import from_whatsapp, should_respond
    msg = from_whatsapp("!kto jest moją babcią?", "whatsapp:+48123456789")
    assert should_respond(msg) is True


def test_whatsapp_no_trigger_ignored():
    from app.channels.adapter import from_whatsapp, should_respond
    msg = from_whatsapp("just a chat message", "whatsapp:+48123456789")
    assert should_respond(msg) is False


def test_whatsapp_bot_name_trigger():
    from app.channels.adapter import from_whatsapp, should_respond
    msg = from_whatsapp("hey familybot, who is my grandma?", "whatsapp:+48123456789")
    assert should_respond(msg) is True


def test_strip_prefix():
    from app.channels.adapter import from_whatsapp, strip_prefix
    msg = from_whatsapp("!kto jest moją babcią?", "whatsapp:+48123456789")
    assert strip_prefix(msg) == "kto jest moją babcią?"


# ---------------------------------------------------------------------------
# Orchestrator — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_happy_path():
    with (
        patch("app.agents.orchestrator.detect_language", new=AsyncMock(return_value="pl")),
        patch(
            "app.agents.orchestrator.generate_cypher",
            new=AsyncMock(return_value="MATCH (me:Person {id: $userId}) RETURN me.firstName"),
        ),
        patch(
            "app.agents.orchestrator.run_read_query",
            new=AsyncMock(return_value=[{"me.firstName": "Jan"}]),
        ),
        patch(
            "app.agents.orchestrator.format_response",
            new=AsyncMock(return_value="Twoje imię to Jan."),
        ),
    ):
        from app.agents.orchestrator import process
        result = await process("Jak mam na imię?", "I1")

    assert result == "Twoje imię to Jan."


@pytest.mark.asyncio
async def test_orchestrator_forbidden_cypher_raises():
    with (
        patch("app.agents.orchestrator.detect_language", new=AsyncMock(return_value="en")),
        patch(
            "app.agents.orchestrator.generate_cypher",
            new=AsyncMock(side_effect=ValueError("Forbidden Cypher keyword detected: DELETE")),
        ),
    ):
        from app.agents.orchestrator import process, OrchestratorError
        with pytest.raises(OrchestratorError):
            await process("Delete all persons", "I1")
