# Architecture — Learning Companion Chatbot

## Flow

`Open WebUI → local application's OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI`

Message flow: `request → latest user message + last ≤10 prior user/assistant messages (request-provided, original order) → [system instruction, history, user message] → Grok → text`. Request `system` messages are ignored and never replace the app instruction. Deliberate no-persistence boundary: history comes only from the current request; nothing is saved (no database, memory, RAG, tools, MCP, routing or LangGraph).

## Components

- **Open WebUI**: already installed and working; the supplied chat client only. Do not reinstall, reconfigure, modify, or build it.
- **Local application** (Python, FastAPI): exposes `/health`, `/v1/models`, `/v1/chat/completions` (normal and streaming).
- **LangChain chains** (same Grok model, request history and endpoint):
  - **General chat** (`chain.py`): greetings and ordinary conversation; active for all requests.
  - **Study helper** (`study.py`): beginner concept explanation + one next step; selected when the latest user message starts with `/study`.
- **LangGraph workflow** (`graph.py`, replaces the Story 3.2 `if/else`): `START → router → {general | study} → END`. Called from the same endpoint; the final answer goes through the existing normal/SSE adapter (streaming emits the finished answer as content chunks).
  - State: `user_message` (latest message), `messages` (request history, ≤10), `route` (`general`/`study`), `answer` (final text).
  - Nodes: **router** (plain Python, not an agent: latest message starts with the `/study` token → `study`, else `general`), **general** (general-chat chain), **study** (study-helper chain; only the `/study` marker is stripped).
  - Edges: `START→router`; conditional router→general|study; general→END; study→END.
  - Trace: log `route=<r> nodes=router><r>`; answer prefixed `[route: …]`.
  - Out of scope: LLM routing, review/improve/loops/retries (Story 4.2), MCP/tools, persistence, extra agents.

## Scope

- Small Learning Companion Chatbot. No custom frontend, no second demo application.

## Boundaries

- API keys only in untracked `.env`.
- Application instructions kept separate from user messages.

## Out of scope

Authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, extensive tests.
