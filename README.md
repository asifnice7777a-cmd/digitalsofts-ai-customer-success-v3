# DigitalSofts AI Customer Success Agent

An autonomous, multi-agent AI Customer Success system built for the DigitalSofts AI Engineering Internship assignment. The system routes client conversations to specialized agents (Sales, Technical, Documentation, Meeting), grounds responses in a company knowledge base using Retrieval-Augmented Generation, lets the LLM decide which tools to invoke, and self-evaluates its own output quality with a single automatic retry.

This README documents the system as it is actually implemented — architecture, features, limitations, and design rationale — for technical reviewers evaluating engineering quality and AI system design.

---

## Badges

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1C3C3C)
![LangChain](https://img.shields.io/badge/LangChain-Tool%20Calling-1C3C3C)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)

---

## Project Overview

DigitalSofts needed an AI-driven customer success assistant capable of answering sales, technical, documentation, and scheduling queries without human intervention. This project implements that assistant as a **graph-orchestrated multi-agent system**:

- A **supervisor** classifies each incoming message and extracts client profile details.
- The message is routed to one of four **specialized agents**, each scoped to its own tools.
- Agents use **LLM-driven tool calling** (via `bind_tools`) to decide, at inference time, whether to query the knowledge base, estimate cost/timeline, generate a proposal, or book a meeting.
- Responses are passed through a **rule-based evaluation node** that scores confidence and triggers a single retry if the response looks incomplete.
- All of this is exposed through a **FastAPI** backend with a minimal HTML/CSS/JS chat frontend.

The system is built to be inspectable end-to-end: every routing decision, tool call, and evaluation outcome is logged and traceable.

---

## Assignment Coverage

| Requirement | Status |
|---|---|
| RAG Knowledge Base | ✅ |
| Multi-Agent Architecture | ✅ |
| Tool Calling | ✅ |
| Conversation Memory | ✅ |
| Evaluation & Self-Correction | ✅ |
| FastAPI Backend | ✅ |
| Basic Frontend | ✅ |
| Logging | ✅ |
| Error Handling | ✅ |
| Docker | ✅ |
| Unit Tests | ✅ |
| README | ✅ |
| Architecture Diagram | ✅ |
| API Documentation | ✅ |

**Bonus Features**

| Bonus Item | Status |
|---|---|
| Vector database other than FAISS | ✅ (PostgreSQL + pgvector) |
| Conversation analytics | ⚠️ Partial — basic usage metrics via `/metrics`, not a full analytics dashboard |
| Human Handoff | ❌ Not implemented |
| MCP | ❌ Not implemented |
| Multiple LLM Providers | ❌ Not implemented — single provider (OpenRouter), model is configurable but there is no provider abstraction layer |
| Deployment | ❌ Not implemented — Dockerfile only, no live deployment target configured |

---

## Architecture Diagram

## System Architecture
                                      ┌─────────────────────────────┐
                                      │          Client             │
                                      │   (Web UI / REST API)       │
                                      └──────────────┬──────────────┘
                                                     │
                                            POST /chat Request
                                                     │
                                                     ▼
                         ┌────────────────────────────────────────────────┐
                         │              FastAPI Backend                   │
                         │                  (main.py)                     │
                         └───────────────┬────────────────────────────────┘
                                         │
                                         ▼
                 ┌─────────────────────────────────────────────────────────────┐
                 │                    Session Memory                           │
                 │─────────────────────────────────────────────────────────────│
                 │ • Client Profile                                            │
                 │ • Conversation History                                      │
                 │ • Update Memory                                             │
                 └───────────────┬─────────────────────────────────────────────┘
                                 │
                                 ▼
                 ┌─────────────────────────────────────────────────────────────┐
                 │              LangGraph Workflow (graph.py)                  │
                 └───────────────┬─────────────────────────────────────────────┘
                                 │
                                 ▼
          ┌──────────────────────────────────────────────────────────────────────────┐
          │                  Supervisor Agent (supervisor.py)                        │
          │──────────────────────────────────────────────────────────────────────────│
          │ • Intent Detection                                                       │
          │ • Route Request                                                          │
          │ • Extract Client Information                                             │
          │   - Name                                                                 │
          │   - Company                                                              │
          │   - Budget                                                               │
          │   - Timeline                                                             │
          │   - Preferred Technology                                                 │
          │   - Project Type                                                         │
          └──────────────┬────────────────┬────────────────┬────────────────────────┘
                         │                │                │
         ┌───────────────▼──────┐ ┌──────▼─────────┐ ┌────▼────────────┐ ┌────────────▼──────────┐
         │    Sales Agent       │ │ Technical Agent│ │Documentation    │ │   Meeting Agent       │
         │                      │ │                │ │Agent            │ │                       │
         └──────────┬───────────┘ └──────┬─────────┘ └────────┬────────┘ └──────────┬───────────┘
                    │                    │                    │                     │
                    ▼                    ▼                    ▼                     ▼
           ┌────────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
           │ ChatOpenAI LLM │   │ ChatOpenAI LLM │   │ ChatOpenAI LLM │   │ ChatOpenAI LLM │
           │ (OpenRouter)   │   │ (OpenRouter)   │   │ (OpenRouter)   │   │ (OpenRouter)   │
           └───────┬────────┘   └──────┬─────────┘   └──────┬─────────┘   └──────┬─────────┘
                   │                   │                    │                    │
          bind_tools()         bind_tools()        bind_tools()        bind_tools()
                   │                   │                    │                    │
                   ▼                   ▼                    ▼                    ▼

      ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  ┌────────────────────┐
      │ search_company_     │  │ search_company_     │  │ generate_proposal_  │  │ create_meeting_    │
      │ knowledge()         │  │ knowledge()         │  │ summary()           │  │ request()          │
      ├─────────────────────┤  ├─────────────────────┤  └─────────────────────┘  └────────────────────┘
      │ estimate_project_   │  │ estimate_project_   │
      │ cost()              │  │ timeline()          │
      └──────────┬──────────┘  └──────────┬──────────┘
                 │                        │
                 └──────────────┬─────────┘
                                ▼
              ┌───────────────────────────────────────────────┐
              │        PostgreSQL + pgvector Vector Database    │
              │                                               │
              │   DigitalSofts Knowledge Base (RAG Search)    │
              └──────────────────────────┬────────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Evaluation & Self-Correction      │
                      │──────────────────────────────────────│
                      │ • Verify Completeness                │
                      │ • Calculate Confidence               │
                      │ • Retry Once (if confidence is low)  │
                      │ • Log Retry Reason                   │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                             ┌────────────────────────┐
                             │    Final Response      │
                             └────────────────────────┘


**RAG path (Knowledge Search tool only):**

```
Knowledge Tool → Vector Store (PostgreSQL + pgvector) → Top-K Matches → Agent → LLM
```

---

## Project Structure

```
DIGITALSOFTS-AGENT/
├── app/
│   ├── agents/
│   │   ├── supervisor.py          # Routing + profile field extraction
│   │   ├── sales_agent.py         # Sales Agent (pricing, services)
│   │   ├── technical_agent.py     # Technical Consultant Agent
│   │   ├── documentation_agent.py # Proposal/documentation Agent
│   │   └── meeting_agent.py       # Meeting scheduling Agent
│   ├── memory/
│   │   └── session_memory.py      # In-memory session store (thread-safe)
│   ├── rag/
│   │   ├── knowledge_base.py      # Seed knowledge records
│   │   └── vector_store.py        # PostgreSQL + pgvector client
│   ├── config.py                  # Environment-driven settings
│   ├── evaluation.py              # Rule-based confidence scoring
│   ├── graph.py                   # LangGraph StateGraph definition
│   ├── llm.py                     # LLM client + tool-calling loop
│   ├── logging_config.py          # Logging setup
│   └── models.py                  # Pydantic request/response schemas
├── tools/
│   ├── cost_tool.py                # estimate_project_cost
│   ├── knowledge_tool.py           # search_company_knowledge
│   ├── meeting_tool.py             # create_meeting_request
│   ├── proposal_tool.py            # generate_proposal_summary
│   └── timeline_tool.py            # estimate_project_timeline
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── sql/
│   └── init_pgvector.sql          # pgvector schema
├── tests/
│   ├── test_api.py
│   ├── test_memory.py
│   └── test_tools.py
├── main.py                        # FastAPI application entrypoint
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Technology Stack

**Backend**
- FastAPI — HTTP API layer
- Uvicorn — ASGI server
- Pydantic — request/response and profile schema validation

**AI / Orchestration**
- LangGraph — stateful multi-agent graph orchestration
- LangChain (`langchain-openai`, `langchain-core`) — LLM client, `@tool` definitions, `bind_tools` tool calling
- OpenRouter — LLM provider gateway (default model: `deepseek/deepseek-chat`)

**RAG**
- PostgreSQL — persistent data store
- pgvector — vector similarity search extension (cosine distance)
- Sentence-Transformers (`all-MiniLM-L6-v2`) — text embeddings

**Frontend**
- Vanilla HTML / CSS / JavaScript — single-page chat widget, no build tooling

**Testing**
- pytest, FastAPI `TestClient`

**Deployment**
- Docker (single-container image; no orchestration/hosting configured)

---

## Features

### Multi-Agent Workflow

The system is built as a `StateGraph` in `graph.py` with a single entry point (`supervisor`) that fans out to four terminal agent nodes, each of which feeds into a shared `evaluation` node. Each agent node wraps its agent function in a `try/except`, so a failure in one agent (LLM error, tool error) degrades gracefully into a fallback message rather than crashing the request.

### Retrieval-Augmented Generation (RAG)

Company knowledge (services, pricing, FAQs, timelines) lives in `app/rag/knowledge_base.py` as 24 structured records. On first startup, `VectorStore` embeds each record with `SentenceTransformer` and stores it in PostgreSQL as a `vector(384)` column. Queries are embedded the same way and matched using pgvector's `<=>` cosine-distance operator, returning the top-K closest records with a normalized similarity score.

### LLM-Driven Tool Calling

Each agent binds only its own tools to the LLM via `llm.bind_tools([...])`. The LLM — not application code — decides whether a tool is needed, which tool to call, and with what arguments. Python's role is limited to executing the requested tool call and returning the result as a `ToolMessage`, looping until the model produces a final answer or a safety iteration cap is reached. This means, for example, the Sales Agent will only call `estimate_project_cost` when the model judges it relevant to the client's message — not on a fixed Python condition.

### Conversation Memory

`SessionMemory` maintains an in-process dictionary keyed by `session_id`, protected by a `threading.Lock`. Each session holds a `ClientProfile` (name, company, project type, preferred technology, budget, timeline) and a full message history. The supervisor extracts profile fields from every incoming message via regex and merges them into the session so agents can reference known client details without re-asking.

### Evaluation & Self-Correction

After an agent responds, `evaluate_response()` applies a small set of heuristics — response length, presence of error/refusal phrases, and whether a question was left unanswered — to produce a confidence score. If confidence falls below `CONFIDENCE_THRESHOLD` (default `0.75`) and no retry has occurred yet, the graph routes back to the same agent once. This is a **rule-based** quality gate, not a learned or LLM-based evaluator.

### Logging

`logging_config.py` configures Python's standard `logging` module with a consistent format (`timestamp | level | logger | message`), controlled by the `LOG_LEVEL` environment variable. Supervisor routing decisions, agent failures, retry triggers, and vector search errors are all logged.

### Metrics

`main.py` tracks in-memory counters — total requests, total retries, per-agent usage counts, and active session count — exposed via `GET /metrics`. This is basic operational visibility, not a full analytics pipeline.

### Frontend

A single-page chat UI (`frontend/`) served directly by FastAPI. It posts messages to `/chat`, displays which agent answered, shows a loading indicator, and supports resetting the session via `/reset-session`.

---

## Agent Workflow

```
User Message
     │
     ▼
Supervisor
  - extract_profile_fields() → merge into session profile
  - route_request()          → keyword match → agent name
     │
     ▼
Agent Selection (sales | technical | documentation | meeting)
     │
     ▼
Tool Calling (LLM decides via bind_tools)
  - zero, one, or multiple tool calls per turn
     │
     ▼
Evaluation
  - confidence = f(length, error phrases, unanswered question)
     │
     ├── confidence < 0.75 AND retry_count == 0 ──► back to same Agent
     │
     ▼
Final Response
```

---

## RAG Pipeline

```
knowledge_base.py (24 records)
          │
          ▼
  SentenceTransformer
  (all-MiniLM-L6-v2, 384-dim)
          │
          ▼
  PostgreSQL + pgvector
  (vector(384) column, seeded once)
          │
          ▼
   Cosine similarity search
   (embedding <=> query_embedding)
          │
          ▼
      Top-K matches
          │
          ▼
   search_company_knowledge tool
          │
          ▼
      Agent → LLM → Answer
```

---

## Memory Flow

```
session_id (generated client-side, per browser session)
       │
       ▼
  SessionMemory.get(session_id)
       │
       ▼
  ClientProfile
  (name, company, project_type, preferred_technology, budget, timeline)
       │
       ▼
  History (all user + assistant turns, in order)
       │
       ▼
  Reused by agents in system prompts
  (avoids asking the client to repeat known details)
```

Memory is **in-process and non-persistent** — it lives for the lifetime of the running server process and is lost on restart.

---

## Tool Calling

Every tool is a `@tool`-decorated LangChain function, scoped to exactly one agent.

| Tool | Used By | Purpose |
|---|---|---|
| `search_company_knowledge` | Sales, Technical | Semantic search over the pgvector-backed knowledge base; returns top-3 matching records. |
| `estimate_project_cost` | Sales | Looks up a rate card by project type (web development, mobile app, ERP, AI solution, cloud migration, custom software) and applies a low/medium/high complexity multiplier to produce a cost range in USD. |
| `estimate_project_timeline` | Technical | Same rate-card pattern as cost estimation, but returns a delivery timeline in weeks. |
| `generate_proposal_summary` | Documentation | Formats a structured proposal (client, company, project type, budget, timeline) from known client details. |
| `create_meeting_request` | Meeting | Creates a **mocked** meeting booking — generates a meeting ID and timestamp, but does not integrate with any real calendar or scheduling system. |

Tool selection is entirely LLM-driven per agent; no agent has access to another agent's tools.

---

## Evaluation

`evaluate_response(user_message, response)` computes a confidence score using simple, deterministic rules:

1. **Length check** — responses under 20 characters or empty are scored `0.4` and marked incomplete.
2. **Word count** — fewer than 15 words drops confidence to `0.6` ("Response lacks sufficient detail").
3. **Error/refusal detection** — presence of `"error"` or `"sorry, i cannot"` caps confidence at `0.5`.
4. **Unanswered question heuristic** — if the user's message ends in `?`, the response contains no `?`, and is under 25 words, confidence is capped at `0.65`.

If the resulting confidence is below `CONFIDENCE_THRESHOLD` (default `0.75`) and no retry has happened yet for that request, LangGraph routes back to the same agent **exactly once**. A second low-confidence result is accepted as final — there is no unbounded retry loop.

This is intentionally a lightweight, rule-based gate rather than an LLM-as-judge system. It catches obvious failure modes (empty responses, refusals, clearly truncated answers) without adding a second model call per turn.

---

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with the ability to install the `pgvector` extension
- An OpenRouter API key

### Windows

```powershell
git clone <repository-url>
cd DIGITALSOFTS-AGENT
python -m venv venv
venv\Scripts\activate
or
.venv\Scripts\activate
or 
cd ..
pip install -r requirements.txt
copy .env.example .env
```

### Linux / macOS

```bash
git clone <repository-url>
cd DIGITALSOFTS-AGENT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and set your `OPENROUTER_API_KEY` and `DATABASE_URL`.

Initialize the database schema:

```bash
psql "$DATABASE_URL" -f sql/init_pgvector.sql
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | API key for OpenRouter | *(required, empty by default)* |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL | `https://openrouter.ai/api/v1` |
| `MODEL_NAME` | Chat model identifier used for all agents | `deepseek/deepseek-chat` |
| `EMBEDDING_MODEL` | Sentence-Transformers model for embeddings | `all-MiniLM-L6-v2` |
| `DATABASE_URL` | PostgreSQL connection string (pgvector-enabled) | `postgresql://postgres:postgres@localhost:5432/digitalsofts` |
| `CONFIDENCE_THRESHOLD` | Minimum confidence before a retry is triggered | `0.75` |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `CHROMA_PERSIST_DIR` | Legacy setting from an earlier ChromaDB-based version; unused since migrating to PostgreSQL + pgvector | `./chroma_db` |

---

## Running the Application
pip install -r requirements.txt
```bash
.venv\Scripts\activate
uvicorn main:app --reload
cd digitalsofts-agent
```

The chat UI is served at `http://localhost:8000/`. Interactive API docs (via FastAPI's built-in OpenAPI UI) are available at `http://localhost:8000/docs`.

---

## Docker

**Build:**

```bash
docker build -t digitalsofts-agent .
```

**Run:**

```bash
docker run -p 8000:8000 --env-file .env digitalsofts-agent
```

The container expects a reachable PostgreSQL instance (with `pgvector` installed) via `DATABASE_URL`; it is not bundled in the image and must be provisioned separately.

---

## API Documentation

### `POST /chat`

Send a message and receive an agent-generated reply.

**Request**

```json
{
  "session_id": "b3f1c2e4-1a2b-4c3d-9e8f-123456789abc",
  "message": "What would an AI chatbot project cost?"
}
```

**Response**

```json
{
  "session_id": "b3f1c2e4-1a2b-4c3d-9e8f-123456789abc",
  "reply": "Great question! For an AI solution like a chatbot, pricing typically ranges from $10,000 to $40,000 depending on complexity...",
  "agent": "sales",
  "confidence": 0.9,
  "client_profile": {
    "client_name": null,
    "company": null,
    "project_type": "ai solution",
    "preferred_technology": null,
    "budget": null,
    "timeline": null
  }
}
```

**Errors**

- `400 Bad Request` — empty `message` field.
- `500 Internal Server Error` — unhandled failure during graph execution.

### `POST /reset-session`

Clears a session's profile and history.

**Request**

```json
{ "session_id": "b3f1c2e4-1a2b-4c3d-9e8f-123456789abc" }
```

**Response**

```json
{ "status": "reset", "session_id": "b3f1c2e4-1a2b-4c3d-9e8f-123456789abc" }
```

### `GET /health`

**Response**

```json
{ "status": "ok", "timestamp": 1752300000.123 }
```

### `GET /metrics`

**Response**

```json
{
  "total_requests": 42,
  "total_retries": 3,
  "agent_usage": { "sales": 20, "technical": 12, "documentation": 6, "meeting": 4 },
  "active_sessions": 5
}
```

---

## API Endpoints Table

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the chat frontend |
| `GET` | `/style.css` | Frontend stylesheet |
| `GET` | `/script.js` | Frontend script |
| `POST` | `/chat` | Send a message, receive an agent reply |
| `POST` | `/reset-session` | Reset a session's memory |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Basic usage metrics |

---

## Testing

Unit tests cover the API surface, session memory, and tool functions:

- `test_api.py` — health check, metrics, end-to-end `/chat` flow, session reset, empty-message validation.
- `test_memory.py` — profile update/retrieval, reset behavior, history tracking.
- `test_tools.py` — cost estimation, timeline estimation, proposal generation, and meeting request creation, invoked directly.

Run the suite:

```bash
pytest
```

---

## Logging

Logging is configured once at startup (`logging_config.py`) using Python's standard `logging` module, with level controlled by `LOG_LEVEL`. Key events logged include:

- Supervisor routing decisions (`Session %s routed to '%s' agent`)
- Agent execution failures, with fallback response substitution
- Retry triggers, including the computed confidence and reason
- Vector search failures in the RAG layer

Logs are written to stdout in a single consistent format, suitable for container log aggregation.

---

## Design Decisions

**Why FastAPI** — Async-native, minimal boilerplate, automatic OpenAPI documentation, and native Pydantic integration made it the natural fit for a small, testable service exposing a handful of well-typed endpoints.

**Why LangGraph** — The assignment required explicit multi-agent orchestration with conditional routing and retry behavior. LangGraph's `StateGraph` makes the control flow (supervisor → agent → evaluation → conditional retry) explicit and inspectable as a graph, rather than burying routing logic inside nested `if/else` chains.

**Why PostgreSQL + pgvector** — The project originally used ChromaDB for local prototyping. Migrating to PostgreSQL + pgvector moves the knowledge base onto infrastructure that's easy to operate, back up, and scale alongside a relational schema, without introducing a separate specialized vector database service. pgvector's cosine-distance operator integrates directly into standard SQL queries.

**Why Sentence-Transformers (`all-MiniLM-L6-v2`)** — A small, fast, CPU-friendly embedding model that produces good-quality semantic embeddings for a 24-record knowledge base without requiring GPU infrastructure or an external embedding API call per query.

**Why OpenRouter** — Provides a single API surface over multiple underlying model providers, making the model (`MODEL_NAME`) a configuration value rather than a code change. This kept the LLM client code provider-agnostic at the `ChatOpenAI`-compatible interface level.

**Why in-memory Session Memory** — For the scope of this assignment (single-process demo service), an in-memory store with a `threading.Lock` gives correct, simple concurrency behavior without standing up Redis or a database table purely for ephemeral session state. The tradeoff — no persistence across restarts, no multi-instance sharing — is called out explicitly in Limitations.

**Why LLM-driven tool calling (`bind_tools`) over manual invocation** — Initially, tools were invoked unconditionally or behind simple Python `if` checks (e.g., "only estimate cost if `project_type` is set"). This meant the tool logic, not the model, was deciding what "needs" a tool call — which doesn't generalize well as conversations get more varied. Binding tools directly to the LLM lets the model make that judgment call per turn based on the actual conversation, while Python's role shrinks to safe, mechanical execution of whatever the model requests.

---

## Challenges

- **Agent routing accuracy** — The supervisor uses keyword matching against fixed word lists (`SALES_KEYWORDS`, `TECH_KEYWORDS`, etc.). Overlapping vocabulary (e.g., "meeting to discuss pricing") can route to an unintended agent, since routing is evaluated in a fixed priority order rather than by intent confidence.
- **Maintaining conversation memory across turns** — Profile fields are extracted independently on every message via regex; ensuring previously captured fields aren't silently overwritten by a weaker match on a later message required care in `SessionMemory.update_profile`'s "only overwrite if truthy" logic.
- **Tool orchestration under the new `bind_tools` flow** — Moving from deterministic tool calls to LLM-decided tool calls introduced the possibility of the model looping on tool calls or never terminating with a final answer; this is bounded with a `max_iterations` cap in the tool-calling loop.
- **Evaluation without a second LLM call** — Designing heuristics that catch genuinely bad responses (empty, refused, clearly truncated) without being so strict that reasonable short answers get needlessly retried required tuning the word-count and question-mark thresholds empirically.
- **RAG retrieval quality on a small corpus** — With only 24 knowledge records, some queries at the edge of two categories (e.g., "AI project timeline" touching both `ai` and general `pricing`/`erp` timeline content) return plausible but not perfectly ranked matches; embedding quality on short documents at this scale has natural limits.

---

## Limitations

- **Keyword-based supervisor** — Routing is regex/keyword-based, not model-based, so it can misroute messages that don't contain expected trigger words.
- **In-memory session storage** — Session data is lost on process restart and is not shared across multiple server instances.
- **Mock meeting scheduling** — `create_meeting_request` generates a fake meeting ID and confirmation text; it does not integrate with any real calendar system (Google Calendar, Outlook, etc.).
- **Rule-based evaluation** — Confidence scoring uses simple heuristics (length, keyword presence, punctuation), not a learned or LLM-based judge.
- **Single LLM provider** — All agents use one configured model via OpenRouter; there is no runtime provider fallback or multi-model routing.
- **No authentication** — API endpoints are unauthenticated and CORS is fully open (`allow_origins=["*"]`), appropriate for a local/demo deployment only.
- **No live deployment** — A Dockerfile is provided, but the project is not deployed to any hosting platform as part of this submission.

---

## Future Improvements

- Replace keyword-based supervisor routing with an LLM-based intent classifier.
- Move session memory to Redis (or PostgreSQL) for persistence and multi-instance support.
- Integrate real calendar APIs for meeting scheduling instead of a mocked confirmation.
- Add authentication and per-client rate limiting to the API.
- Build a proper conversation analytics dashboard on top of the existing `/metrics` counters.
- Add human handoff for low-confidence or explicitly escalated conversations.
- Support streaming responses over the `/chat` endpoint.
- Add multi-LLM-provider support with automatic fallback.
- Deploy to a managed hosting platform with CI/CD.

---

## Example Conversation

```
User: Hi, I'm Sarah from Northbridge Retail. We're looking at building a mobile app, budget around $30k.
Assistant (sales): Thanks for reaching out, Sarah! For a mobile app project like yours,
DigitalSofts typically delivers within 8-16 weeks, with pricing in the $8,000-$25,000 range
depending on complexity — your $30k budget comfortably covers a full-featured build...

User: What tech stack would you use?
Assistant (technical): For mobile app development, we typically build with Flutter or React
Native for cross-platform delivery, or native Swift/Kotlin if you need deep platform-specific
integrations. Given your project, delivery would land in the 8-16 week range...

User: Can we set up a call next week to discuss further?
Assistant (meeting): You're all set! I've created a meeting request (ID: 7a3f9c21) for Sarah,
purpose: mobile app project discussion, preferred time: next week. Our team will confirm via
email shortly.
```

---

## Performance Notes

The system is optimized for correctness and clarity over throughput. Embedding generation and vector search run synchronously per request; with a 24-record knowledge base this adds negligible latency. The dominant cost per request is the LLM round-trip(s), including any tool-calling iterations. No caching, batching, or async LLM streaming is currently implemented.

---

## License

MIT