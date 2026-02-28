# Family Tree AI Assistant

Ask natural-language questions about your family tree via a **web chat** or **WhatsApp**.
Answers are returned in the same language as the question — Polish, Czech, or English.

```
GEDCOM → Neo4j → Multi-Agent AI (OpenAI) → Web + WhatsApp (Twilio)
```

---

## Medium article
https://medium.com/@pbrudny/building-a-family-tree-ai-assistant-from-gedcom-to-whatsapp-bot-with-a-graph-database-b1fcf0b3cc9e

## Architecture

```
User (Web or WhatsApp)
  ↓
Channel Adapter          — normalise input, apply WhatsApp trigger filter
  ↓
Orchestrator Agent
  ├─ Language Detection Agent   — detect pl / cs / en
  ├─ Cypher Generation Agent    — question → read-only Cypher
  ├─ Neo4j                      — execute query
  └─ Response Formatting Agent  — result JSON → natural language
  ↓
Answer (in original language)
```

**Stack:** Python 3.12 · FastAPI · OpenAI · Neo4j · Twilio · React/Vite · Docker

---

## Quick start

### 1. Clone and configure

```bash
git clone <repo-url>
cd my-family-bot
cp .env.example .env
# Edit .env and fill in your keys (see Environment variables below)
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| Neo4j    | http://localhost:7474 (browser) |

### 3. Import a GEDCOM file

```bash
curl -X POST http://localhost:8000/admin/upload-gedcom \
  -H "X-Admin-Key: <your-admin-key>" \
  -F "file=@family.ged"
```

### 4. Map a WhatsApp number to a person

```bash
curl -X POST http://localhost:8000/admin/map-whatsapp \
  -H "X-Admin-Key: <your-admin-key>" \
  -H "Content-Type: application/json" \
  -d '{"personId": "I1", "whatsappId": "whatsapp:+48123456789"}'
```

### 5. Chat

- **Web:** open http://localhost:3000, enter your Person ID, and start chatting.
- **WhatsApp:** configure Twilio sandbox webhook → `https://<your-host>/webhook/twilio`.
  Messages must start with `!` or `/`, or mention `familybot`.

---

## Environment variables

Copy `.env.example` to `.env` and set:

| Variable               | Description                                      |
|------------------------|--------------------------------------------------|
| `OPENAI_API_KEY`       | OpenAI API key                                   |
| `OPENAI_MODEL`         | Model name (default: `gpt-4o-mini`)              |
| `NEO4J_URI`            | Bolt URI (default: `bolt://neo4j:7687`)          |
| `NEO4J_USER`           | Neo4j username (default: `neo4j`)                |
| `NEO4J_PASSWORD`       | Neo4j password                                   |
| `TWILIO_ACCOUNT_SID`   | Twilio Account SID                               |
| `TWILIO_AUTH_TOKEN`    | Twilio Auth Token (used to validate signatures)  |
| `TWILIO_WHATSAPP_FROM` | Twilio sandbox number (e.g. `whatsapp:+14155238886`) |
| `SECRET_KEY`           | App secret key (JWT / sessions)                  |
| `ADMIN_API_KEY`        | API key for `/admin/*` endpoints                 |

---

## Project structure

```
my-family-bot/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app
│   │   ├── config.py                 # Settings (pydantic-settings)
│   │   ├── agents/
│   │   │   ├── language_detector.py  # Detect pl / cs / en
│   │   │   ├── cypher_generator.py   # Question → Cypher
│   │   │   ├── response_formatter.py # Result → natural language
│   │   │   └── orchestrator.py       # Pipeline coordinator
│   │   ├── channels/
│   │   │   ├── adapter.py            # Normalise web / WhatsApp input
│   │   │   └── twilio_webhook.py     # Twilio signature validation
│   │   ├── db/
│   │   │   ├── neo4j_client.py       # Read-only Neo4j driver + Cypher validator
│   │   │   └── gedcom_importer.py    # GEDCOM → Neo4j
│   │   ├── models/schemas.py         # Pydantic schemas
│   │   └── routers/
│   │       ├── chat.py               # POST /chat
│   │       ├── whatsapp.py           # POST /webhook/twilio
│   │       └── admin.py              # /admin/* (GEDCOM upload, WhatsApp mapping)
│   ├── tests/
│   │   └── test_agents.py
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/Login.tsx
│   │   ├── pages/Chat.tsx
│   │   └── components/ChatInterface.tsx
│   ├── Dockerfile
│   └── nginx.conf
├── neo4j/init/schema.cypher           # DB constraints and indexes
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## API reference

### `POST /chat`
Ask a question as a web user.

```json
// Request
{ "message": "Kto jest moją babcią?", "userId": "I1" }

// Response
{ "reply": "Twoja babcia to Maria Kowalska, ur. 1930 w Krakowie." }
```

### `POST /webhook/twilio`
Twilio WhatsApp webhook. Called automatically by Twilio; validates signature and returns TwiML.

### `POST /admin/upload-gedcom`
Upload a `.ged` file. Requires `X-Admin-Key` header.

### `POST /admin/map-whatsapp`
Link a WhatsApp number to a Person node. Requires `X-Admin-Key` header.

### `GET /admin/persons`
List all persons in the graph. Requires `X-Admin-Key` header.

### `GET /health`
Returns `{"status": "ok"}`.

---

## Graph schema

**Nodes**

| Label    | Properties                                                                 |
|----------|----------------------------------------------------------------------------|
| `Person` | `id`, `firstName`, `lastName`, `gender`, `birthDate`, `deathDate`, `birthPlace`, `currentCountry`, `whatsappId`, `preferredLanguage` |
| `Place`  | `name`                                                                     |

**Relationships**

```
(:Person)-[:PARENT_OF]->(:Person)
(:Person)-[:MARRIED_TO]->(:Person)
(:Person)-[:LIVES_IN]->(:Place)
(:Person)-[:BORN_IN]->(:Place)
```

---

## Security

- The AI uses a **read-only** Neo4j role — no write operations possible via chat.
- All Cypher queries are validated against a blocklist (`CREATE`, `DELETE`, `MERGE`, `DROP`, `CALL`, …) before execution.
- All queries are **parameterised** — no string interpolation of user input.
- Twilio webhook **signature is validated** on every request.
- Admin endpoints are protected by a static **API key**.
- Query timeout: 5 seconds. Result cap: 100 records.

---

## Development

### Run backend locally

```bash
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Run frontend locally

```bash
cd frontend
npm install
npm run dev
```

### Run tests

```bash
cd backend
pytest
```

### Lint

```bash
ruff check backend/
```
