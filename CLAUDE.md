# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Python 3.12, FastAPI)

```bash
# Install (from repo root)
uv pip install -e ".[dev]"

# Run dev server (requires Neo4j running)
uvicorn app.main:app --reload   # run from backend/ dir

# Run all tests
pytest

# Run a single test
pytest backend/tests/test_agents.py::test_orchestrator_happy_path

# Lint
ruff check backend/
ruff format backend/
```

### Frontend (React/Vite/TypeScript)

```bash
cd frontend
npm install
npm run dev      # Vite dev server → http://localhost:5173
npm run build    # tsc + vite build
```

### Full stack (Docker Compose — preferred)

```bash
docker compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Neo4j:    http://localhost:7474
```

### Import GEDCOM / admin setup

```bash
# Upload a GEDCOM file
curl -X POST http://localhost:8000/admin/upload-gedcom \
  -H "X-Admin-Key: <ADMIN_API_KEY>" -F "file=@family.ged"

# Map a WhatsApp number to a Person node
curl -X POST http://localhost:8000/admin/map-whatsapp \
  -H "X-Admin-Key: <ADMIN_API_KEY>" -H "Content-Type: application/json" \
  -d '{"personId": "I1", "whatsappId": "whatsapp:+48123456789"}'
```

## Architecture

```
User (Web or WhatsApp)
  ↓
channels/adapter.py       — normalise input; WhatsApp trigger filter (!, /, bot name)
  ↓
routers/chat.py           — POST /chat (web)
routers/whatsapp.py       — POST /webhook/twilio (Twilio signature validation)
  ↓
agents/orchestrator.py    — pipeline coordinator
  ├─ agents/language_detector.py   — detect pl / cs / en
  ├─ agents/cypher_generator.py    — question → read-only Cypher (OpenAI)
  ├─ db/neo4j_client.py            — validate + execute Cypher
  └─ agents/response_formatter.py  — result JSON → natural language (OpenAI)
  ↓
Answer in original language
```

### Key design decisions

- **Identity:** Every user maps to a `Person` node. Web auth stores `userId` in `localStorage` (Person.id). WhatsApp users are looked up by `whatsappId` property. Every generated Cypher must start with `MATCH (me:Person {id: $userId})`.
- **Security:** Cypher queries are validated against a blocklist (`FORBIDDEN_KEYWORDS` in `neo4j_client.py`) before execution. Write access via `run_write_query` is only used internally (GEDCOM import, admin endpoints). The AI only calls `run_read_query`.
- **Languages:** Supported languages are `pl`, `cs`, `en`. Language is detected first; Cypher is always generated in English; the response is formatted back in the detected language. Unknown language codes fall back to `en`.
- **Config:** All settings come from `backend/app/config.py` (pydantic-settings), reading from `.env`. Copy `.env.example` to `.env` to get started.

### Graph schema

```
(:Person {id, firstName, lastName, gender, birthDate, deathDate, birthPlace,
          currentCountry, whatsappId, preferredLanguage})
(:Place  {name})

(:Person)-[:PARENT_OF]->(:Person)
(:Person)-[:MARRIED_TO]->(:Person)
(:Person)-[:LIVES_IN]->(:Place)
(:Person)-[:BORN_IN]->(:Place)
```

Cousin/uncle/aunt relationships are not stored — derived via Cypher traversal (two `PARENT_OF` hops for cousins).

### Frontend routes

- `/login` — enter Person ID; stored in `localStorage` as `userId`
- `/` — chat interface (protected, redirects to `/login` if no `userId`)
- `/admin` — admin panel (GEDCOM upload, WhatsApp mapping, person list)

### Ruff config

Line length 100, Python 3.12 target, rules `E`, `F`, `I`.

### Test conventions

All tests mock OpenAI and Neo4j — no live connections needed. `asyncio_mode = "auto"` in `pyproject.toml` (no `@pytest.mark.asyncio` decorator needed, but currently used explicitly in tests).
