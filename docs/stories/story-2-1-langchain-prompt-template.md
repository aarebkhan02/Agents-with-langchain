# Story 2.1 — LangChain prompt template

## Purpose

Make the seed's LangChain flow reusable and easy to understand: a small chat prompt with a stable application instruction and the current user message, kept clearly separate. Endpoints, settings and the Open WebUI connection stay as they are.

## What this story implements in plain English

- You chat in Open WebUI exactly as before and still get a reply, both all-at-once and word-by-word.
- The tutor's rules now live in one fixed place owned by the app; nothing you type can replace them.
- Only your latest message is sent to the model for now. It does not remember earlier turns (Story 2.2).
- If a chat request carries its own "system" message, it is treated as ordinary user text, not as new rules.
- A development-only log line shows which message roles were sent and how many, never keys or the hidden instruction text.

## Prerequisites

- Story 1.1 complete: app runs, Open WebUI connected to `http://127.0.0.1:8000/v1`.
- `.env` holds a working key and model name (`GENERATION_API_KEY`, `GENERATION_MODEL_NAME`); no new settings are needed.
- No `docs/config.yaml` exists; project path = repository root.

## Work to do

1. `src/learning_companion/chain.py`
   - Replace the tuple-based prompt with `ChatPromptTemplate` built from a `SystemMessage` (the existing `SYSTEM_INSTRUCTION`, not a template variable) plus a `HumanMessagePromptTemplate` for `{question}`. No string concatenation.
   - Keep one chain: prompt → Grok model → `StrOutputParser`, used by both `answer` and `stream_answer`.
   - Add `build_messages(question) -> list[BaseMessage]` that returns the formatted prompt messages (inspectable helper).
   - Add a dev-only log (when `APP_ENV=development`) of roles and count, e.g. `prompt roles=[system, human] count=2`. Never log keys or instruction text.
2. `src/learning_companion/main.py`
   - Keep `_latest_user`: use only the latest `user` message. Ignore request `system` and `assistant` messages for prompt construction (they are never promoted to the application instruction). No history.
   - Endpoints, JSON and SSE shapes, and error handling unchanged.
3. `docs/architecture.md`
   - Add the message flow: `request → latest user message → [system instruction, user message] → Grok → text` and the deliberate no-persistence boundary (no history, database or memory yet).

Do not add: a CLI chatbot, a second chat path, history, database, memory, RAG, tools, MCP, LangGraph, a new frontend, an evaluation harness or a broad test suite.

## Completion checks

```
uv run ruff format src tests
uv run ruff check src tests
uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
```

- Send one ordinary question from the existing Open WebUI chat.
- Dev log shows `roles=[system, human] count=2`, system first, user second.
- Expected result: Open WebUI renders the Grok answer as before.

Record the commands actually run in the handover.

## Handover

- Changed files: `src/learning_companion/chain.py`, `src/learning_companion/main.py` (only if needed), `docs/architecture.md`.
- Report the commands run and the check results.
- Story 2.2 extends this prompt with a conversation-history placeholder and history handling.
