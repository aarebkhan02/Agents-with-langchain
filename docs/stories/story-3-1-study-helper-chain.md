# Story 3.1 — Study-helper chain

## Purpose

Add a second, separately named LangChain chain that explains beginner technical concepts and ends with one next step. It is created and callable in development only; the app route stays unchanged. Endpoints, Grok settings, request/response behavior, Open WebUI connection and history handling stay as they are.

## What this story implements in plain English

- The project now holds a "study helper" behaviour next to the normal chat behaviour.
- Given a beginner technical question (e.g. "What is an API?"), it gives a short plain-language explanation, a small example where useful, and one suggested next learning step.
- It uses the same Grok model and the same request conversation history as normal chat.
- Open WebUI still gets the normal chat behaviour; the study helper is only reachable from a local development command until Story 3.2.
- It does not browse, research, look up course data, or promise its answers are correct.

## Prerequisites

- Stories 1.1, 2.1 and 2.2 complete; Open WebUI connected to `http://127.0.0.1:8000/v1`.
- `.env` holds a working `GENERATION_API_KEY` and `GENERATION_MODEL_NAME`; no new settings.
- No `docs/config.yaml` exists; project path = repository root.

## Work to do

1. `src/learning_companion/study.py` (new; `chain.py` and `main.py` are not edited)
   - `STUDY_SYSTEM_INSTRUCTION`: Learning Companion study helper; explain beginner technical concepts in plain language; concise explanation, a small example where useful, end with exactly one "Next step:" suggestion; do not claim to research, browse, retrieve course data, or guarantee correctness.
   - `STUDY_PROMPT = ChatPromptTemplate`: `SystemMessage(STUDY_SYSTEM_INSTRUCTION)`, `MessagesPlaceholder("history")`, `HumanMessagePromptTemplate("{question}")`. User content never goes into the system text.
   - `study_answer(question, history=None) -> str`: `STUDY_PROMPT | ChatXAI(same settings as general chain) | StrOutputParser()`; raise `ConfigurationError` (imported from `chain.py`) if key/model unset.
   - Dev entry: `python -m learning_companion.study "<question>"` prints the answer.
2. `docs/architecture.md`
   - Document two chain behaviours: **general chat** (greetings/ordinary conversation; active for all requests) and **study helper** (beginner concept explanation + one next step; available, not wired in). State this story creates the capability only; choosing between chains is Story 3.2. Same model, history and endpoint for both.

Do not add: routing, LLM classification, more specialists, loops, review steps, tools, MCP, LangGraph, retrieval, database, new endpoint/UI/provider, broad tests, production controls.

## Completion checks

```
uv run ruff format src tests
uv run ruff check src tests
uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
uv run python -m learning_companion.study "What is an API?"
```

1. In Open WebUI send "Hello": normal general-chat reply, same as before this story.
2. Study-helper command output contains a plain explanation and exactly one next step.

Record the commands actually run in the handover.

## Handover

- Changed files: `src/learning_companion/study.py` (new), `docs/architecture.md`.
- Report commands run and results (format/lint, Open WebUI "Hello", study output with one next step).
- Story 3.2 extends this by adding the visible `/study` route rule that selects the study-helper chain from the endpoint; general chat stays the default.
