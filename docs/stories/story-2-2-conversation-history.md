# Story 2.2 — Conversation history from Open WebUI

## Purpose

Let a follow-up question use earlier messages of the same chat. History comes only from the current request; nothing is stored. Endpoints, Grok config, the prompt template, JSON/SSE behavior and the Open WebUI connection stay as they are.

## What this story implements in plain English

- Open WebUI already sends the earlier messages of the active chat with every question.
- The app now passes the most recent few of those earlier questions and answers to the tutor, in their original order, before your latest question.
- So "Explain it more simply" or "What was my first question?" can be answered using what was said before.
- The app remembers nothing once the reply is done; a new chat or a restart starts empty.
- A "system" message in the request is never treated as the tutor's rules; the app's own instruction always stays first.

## Prerequisites

- Stories 1.1 and 2.1 complete: app runs, Open WebUI connected to `http://127.0.0.1:8000/v1`.
- `.env` holds a working `GENERATION_API_KEY` and `GENERATION_MODEL_NAME`; no new settings.
- No `docs/config.yaml` exists; project path = repository root.

## Work to do

1. `src/learning_companion/chain.py`
   - Add `MAX_HISTORY_MESSAGES = 10` (prior `user`/`assistant` messages kept, most recent only; excludes the latest user message).
   - Prompt becomes: `SystemMessage(SYSTEM_INSTRUCTION)`, `MessagesPlaceholder("history")`, `HumanMessagePromptTemplate("{question}")`. No string-built prompts.
   - Keep one chain (prompt → Grok → `StrOutputParser`) for `answer` and `stream_answer`; both take `question` and `history: list[BaseMessage]` and invoke with `{"history": history, "question": question}`.
   - Update `build_messages(question, history)` to return the formatted messages. Dev-only log (`APP_ENV=development`): roles and count, e.g. `prompt roles=[system, human, ai, human] count=4`. Remove the existing per-message `payload` content logging so no instruction text or message bodies are logged; never log keys.
2. `src/learning_companion/main.py`
   - Add `_history(messages)`: drop everything from the latest `user` message onward; keep only `user`/`assistant` messages with non-empty string content (ignore `system` and anything else); convert to `HumanMessage`/`AIMessage` in original order; keep the last `MAX_HISTORY_MESSAGES`.
   - Pass `history` to `answer` / `stream_answer`. Request and response shapes, endpoints, SSE and error handling unchanged.
3. `docs/architecture.md`
   - Document the flow `request → latest user message + last ≤10 prior user/assistant messages → [system instruction, history, user message] → Grok → text`, the 10-message limit, and the no-persistence boundary (nothing saved; no database, memory, RAG, tools, MCP, routing or LangGraph).

Do not add: database, persistent memory, RAG, tools, MCP, routing, LangGraph, new endpoint or UI, evaluation harness, broad tests.

## Completion checks

```
uv run ruff format src tests
uv run ruff check src tests
uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
```

In one new Open WebUI chat:

1. Ask: "My favourite subject is astronomy. Remember that." → normal reply.
2. Ask: "What is my favourite subject?"

Expected: dev log for turn 2 shows `roles=[system, human, ai, human] count=4` (system first, latest human last), and the answer says astronomy. Turn 1 shows `roles=[system, human] count=2`. Streaming and non-streaming both render as before. A new chat does not know the subject.

Record the commands actually run in the handover.

## Handover

- Changed files: `src/learning_companion/chain.py`, `src/learning_companion/main.py`, `docs/architecture.md`.
- Report commands run and check results (role sequence, follow-up answer).
- Story 3.1 extends this by building on the same prompt/history flow; persistence stays out until a later story.
