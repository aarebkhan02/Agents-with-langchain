# Architecture — Learning Companion Chatbot

## Flow

`Open WebUI → local application's OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI`

## Components

- **Open WebUI**: already installed and working; the supplied chat client only. Do not reinstall, reconfigure, modify, or build it.
- **Local application** (Python, FastAPI): exposes `/health`, `/v1/models`, `/v1/chat/completions` (normal and streaming).
- **LangChain chain**: fixed Learning Companion system instruction + latest user message → Grok chat model → string.

## Scope

- Small Learning Companion Chatbot. No custom frontend, no second demo application.

## Boundaries

- API keys only in untracked `.env`.
- Application instructions kept separate from user messages.

## Out of scope

Authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, extensive tests.
