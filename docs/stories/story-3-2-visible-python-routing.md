# Story 3.2 — Visible Python routing between the two chains

## Purpose

Make both existing chains reachable from the same Open WebUI chat endpoint using one plain Python `if/else`. Endpoints, Grok settings, Open WebUI connection, history handling (Story 2.2) and normal JSON/SSE response shapes stay unchanged.

## What this story implements in plain English

- An ordinary message (e.g. "Hello") goes to the general-chat chain, exactly as today.
- A message starting with `/study` (e.g. `/study Explain what an API is`) goes to the study-helper chain.
- Only the leading `/study` is removed; the rest is the question the study helper sees. Earlier messages stay as history under the Story 2.2 rules.
- The app logs which route ran (`general` or `study`) and puts a short label such as `[route: study]` at the start of the answer text.
- Both routes use the same endpoint and the same normal/streaming adapter. This is a fixed rule in code, not LLM classification, LangGraph or autonomous routing.

## Prerequisites

- Stories 1.1, 2.1, 2.2 and 3.1 complete; Open WebUI connected to `http://127.0.0.1:8000/v1`.
- `.env` holds a working `GENERATION_API_KEY` and `GENERATION_MODEL_NAME`; no new settings.
- No `docs/config.yaml` exists; project path = repository root.

## Work to do

1. `src/learning_companion/study.py`
   - Add `stream_study_answer(question, history) -> Iterator[str]` using the same chain as `study_answer` (`chain.stream`), mirroring `stream_answer` in `chain.py`.
2. `src/learning_companion/main.py`
   - Add `_route(question) -> tuple[str, str]`: if `question.lstrip()` starts with `/study`, return `("study", question.lstrip()[len("/study"):].strip())`; else `("general", question)`. Match only the whole `/study` token (followed by whitespace or end), so `/studying` stays general.
   - In `chat`, call `_route` on the latest user message, pick `answer`/`stream_answer` or `study_answer`/`stream_study_answer`, and log `route=<general|study>` via the existing uvicorn logger (compact; no message text).
   - Prefix the answer text with `[route: general] ` / `[route: study] ` (first content chunk when streaming). No new response fields; JSON/SSE shapes unchanged.
   - Keep `_history` and `ConfigurationError` handling as is. Add a short comment: Session 4 replaces this `if/else` with an explicit LangGraph route.
3. `docs/architecture.md`
   - Document the `/study` rule, the selected-chain path (`endpoint → _route → general or study chain → same normal/SSE adapter`), update the study-helper bullet (now wired in via `/study`), and the boundary: deterministic application routing, not LLM classification, LangGraph or multi-agent orchestration.

Do not add: LLM routing, extra specialists, review steps, loops, tools, custom response fields, Open WebUI plugins, broad tests, production controls.

## Completion checks

```
uv run ruff format src tests
uv run ruff check src tests
uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
```

1. Open WebUI: send "Hello" → normal general reply labelled `[route: general]`.
2. Open WebUI: send `/study Explain what an API is` → labelled `[route: study]`, with a clear explanation and exactly one `Next step:` line.
3. Server log shows `route=general` then `route=study`; both requests hit `/v1/chat/completions`.

Record the commands actually run in the handover.

## Handover

- Changed files: `src/learning_companion/main.py`, `src/learning_companion/study.py`, `docs/architecture.md`.
- Report commands run and results (format/lint, both Open WebUI messages, route log lines).
- Story 4.1 extends this by replacing the `if/else` internally with an explicit LangGraph route, keeping the same endpoint and `/study` behaviour.
