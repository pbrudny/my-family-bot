# AGENTS.md

# Project: Family Tree AI Assistant

GEDCOM → Graph → Multi-Agent AI → Web + WhatsApp

------------------------------------------------------------------------

# 1. System Overview

The system allows family members to ask natural language questions about
the family tree via:

-   🌐 Web Interface
-   💬 WhatsApp Group Bot

Supported languages: - Polish - Czech - English

Graph Database: - Neo4j

LLM Provider: - OpenAI

WhatsApp Integration via: - Meta WhatsApp Business Platform\
OR - Twilio WhatsApp API

------------------------------------------------------------------------

# 2. High-Level Architecture

User (Web or WhatsApp) ↓ Channel Adapter ↓ Orchestrator Agent ↓ Language
Detection Agent ↓ Cypher Generation Agent ↓ Neo4j ↓ Response Agent ↓
Translated Answer (if needed) ↓ User

------------------------------------------------------------------------

# 3. Identity & Personalization Model

## 3.1 WhatsApp Identity Mapping

Each WhatsApp user must be mapped to a Person node.

Add property to Person:

-   whatsappId (string, unique)
-   preferredLanguage (optional)

When message arrives:

1.  Extract WhatsApp sender ID
2.  Lookup Person by whatsappId
3.  Use that Person as `me` in Cypher

------------------------------------------------------------------------

## 3.2 Web Authentication

Options: - Simple login via email - OAuth - Passwordless magic link

After login: - Map user to Person node - Store session → userId

------------------------------------------------------------------------

# 4. Language Handling

## 4.1 Language Detection Agent

Input: - Raw user message

Output: - Detected language (pl / cs / en)

Rules: - Always detect language before Cypher generation - Cypher
generation always in English - Response returned in original language

------------------------------------------------------------------------

# 5. Core Graph Schema

## Node: Person

Properties: - id - firstName - lastName - gender - birthDate -
deathDate - birthPlace - currentCountry - whatsappId - preferredLanguage

## Relationships

(:Person)-\[:PARENT_OF\]-\>(:Person)\
(:Person)-\[:MARRIED_TO\]-\>(:Person)\
(:Person)-\[:LIVES_IN\]-\>(:Place)\
(:Person)-\[:BORN_IN\]-\>(:Place)

No cousin/uncle relationships stored directly.

------------------------------------------------------------------------

# 6. Agents

## 6.1 Channel Adapter Agent

Responsibility:

Normalize input from: - Web - WhatsApp webhook

WhatsApp Rules:

Bot responds only if message starts with: - "!" - "/" - or mentions the
bot

------------------------------------------------------------------------

## 6.2 Orchestrator Agent

Responsibility:

-   Identify sender
-   Detect language
-   Inject user context
-   Route to Cypher agent
-   Route result to Response agent

Must always include:

MATCH (me:Person {{id: \$userId}})

------------------------------------------------------------------------

## 6.3 Cypher Generation Agent

Responsibility:

Convert question → Cypher

Rules: - Output Cypher only - No markdown - No explanation - Use
parameter \$userId - Read-only queries only

Allowed clauses: - MATCH - WHERE - WITH - RETURN - ORDER BY - LIMIT

Forbidden: - CREATE - DELETE - MERGE - CALL - DROP

------------------------------------------------------------------------

## 6.4 Response Formatting Agent

Responsibility:

-   Convert result JSON → natural response
-   Respect original language
-   If no result → clearly state no data found
-   If list \> 10 → summarize

------------------------------------------------------------------------

# 7. Security Model

-   Read-only Neo4j role for AI
-   Parameterized queries only
-   Query timeout
-   Max result limit
-   Rate limit per WhatsApp user
-   Full logging enabled

------------------------------------------------------------------------

# 8. Web Interface Requirements

Pages:

1.  Login
2.  Chat interface
3.  Family graph viewer (optional)
4.  Admin panel:
    -   Map WhatsApp IDs
    -   Upload GEDCOM
    -   Rebuild graph

------------------------------------------------------------------------

# 9. Deployment Architecture

Backend: - Python - FastAPI

Database: - Neo4j

Messaging: - WhatsApp Business API

Frontend: - React / Next.js

Containerized via Docker.

------------------------------------------------------------------------

# 10. Definition of Done

System is complete when:

-   GEDCOM imports correctly
-   WhatsApp users mapped to Person nodes
-   Bot responds correctly in PL / CZ / EN
-   Identity-aware queries work ("my cousins")
-   No destructive database queries possible
-   System is deterministic and secure
