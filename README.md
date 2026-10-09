# Learning Companion Chatbot

Local app that answers Open WebUI chats via LangChain and Grok.

## Setup

1. `uv sync`
2. `cp .env.example .env` — put your real `GENERATION_API_KEY` only in this untracked file. The instructor supplies `GENERATION_MODEL_NAME`.
3. Run: `uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000`

## Open WebUI connection

OpenAI-compatible base URL: `http://127.0.0.1:8000/v1`; select the configured model.
