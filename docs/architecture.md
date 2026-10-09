# Architecture — Learning Companion Chatbot

## Flow

`Open WebUI → local application's OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI`

Message flow: `request → latest user message + last ≤10 prior user/assistant messages (request-provided, original order) → [system instruction, history, user message] → Grok → text`. Request `system` messages are ignored and never replace the app instruction. Deliberate no-persistence boundary: history comes only from the current request; nothing is saved (no database, memory, RAG, tools, MCP, routing or LangGraph).

## Components

- **Open WebUI**: already installed and working; the supplied chat client only. Do not reinstall, reconfigure, modify, or build it.
- **Local application** (Python, FastAPI): exposes `/health`, `/v1/models`, `/v1/chat/completions` (normal and streaming).
- **LangChain chains** (same Grok model, request history and endpoint):
  - **General chat** (`chain.py`): greetings and ordinary conversation; active for all requests.
  - **Study helper** (`study.py`): beginner concept explanation + one next step; available only via `python -m learning_companion.study "<question>"`, not wired into the endpoint. Story 3.1 creates this capability only; selecting between chains is Story 3.2.

## Scope

- Small Learning Companion Chatbot. No custom frontend, no second demo application.

## Boundaries

- API keys only in untracked `.env`.
- Application instructions kept separate from user messages.

## Out of scope

Authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, extensive tests.
