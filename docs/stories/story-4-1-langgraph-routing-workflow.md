# Story 4.1 — LangGraph routing workflow

## Purpose

Replace only the internal Python `if/else` route from Story 3.2 with one small LangGraph workflow that reuses the existing general-chat and study-helper chains. FastAPI service, `/v1/chat/completions`, Open WebUI connection, Grok settings, history conversion (Story 2.2) and normal JSON/SSE response shapes stay unchanged. No second app or chat route.

## What this story implements in plain English

- A question enters the same endpoint as before; history conversion is unchanged.
- A small router step looks at the latest message: starts with `/study` → study path, otherwise → general path.
- Exactly one answer step runs (general chat or study helper), using the existing chain, and writes the final answer.
- The final answer goes through the existing normal/streaming adapter to Open WebUI.
- The log shows the route and the steps that ran, e.g. `route=study nodes=router>study`.

## Prerequisites

- Stories 1.1, 2.1, 2.2, 3.1 and 3.2 complete; Open WebUI connected to `http://127.0.0.1:8000/v1`.
- `.env` holds a working `GENERATION_API_KEY` and `GENERATION_MODEL_NAME`; no new settings.
- No `docs/config.yaml` exists; project path = repository root.

## Terms and state (read before implementing)

- **Node**: a focused piece of work in the workflow. Not automatically an agent.
- **Router node**: ordinary application Python, not an agent and not an LLM. Same `/study` rule as 3.2.
- **General-chat / study-helper nodes**: small specialist behaviours that each call one existing Grok-powered chain.
- **State**: the small record passed between nodes. `TypedDict` fields:
  - `user_message: str` — the latest user message, as received (router reads it; study marker stripped into the question the study node uses).
  - `messages: list[BaseMessage]` — prior conversation from the request (Story 2.2 history, ≤10).
  - `route: str` — `general` or `study`, written by the router.
  - `answer: str` — final text, written by the answer node.
- MCP tool calls could live inside a future node; MCP is **not** implemented here.

## Work to do

1. `pyproject.toml` / `uv.lock`: add `langgraph` (`uv add langgraph`) — the only dependency change.
2. `src/learning_companion/graph.py` (new)
   - `GraphState` TypedDict as above.
   - `router_node(state)`: move `_route` logic here unchanged (whole `/study` token, strip only the marker); write `route`.
   - `general_node(state)`: `answer(question, messages)` from `chain.py`; write `answer`.
   - `study_node(state)`: `study_answer(question, messages)` from `study.py`; write `answer`.
   - Build `StateGraph(GraphState)`: `START → router`; `add_conditional_edges("router", lambda s: s["route"], {"general": "general", "study": "study"})`; `general → END`; `study → END`. Compile once at module level.
   - `run_graph(user_message, messages) -> (route, answer)`: invoke the graph; log one compact line `route=<r> nodes=router>general|study` (no message text, keys or prompts).
3. `src/learning_companion/main.py`
   - Remove `_route` and the `if/else` selection; call `run_graph`. Keep `_history`, `ConfigurationError` handling, route label prefix (`[route: …]`) and JSON shape.
   - Streaming: the graph returns the finished answer; emit it via the existing SSE helper (`_chunk`) as content chunks, then stop and `[DONE]`. Chunk shape unchanged. (Token-by-token graph streaming is out of scope.)
4. `docs/architecture.md`: add the graph diagram (`START → router → {general | study} → END`), the state fields, node responsibilities, edge rules, and out of scope (LLM routing, review/loop/retry, MCP/tools, persistence, extra agents).

Do not add: reviewer, improver, loops, retries, MCP/tool execution, RAG, web search, database/persistence, human approval, extra agents, custom response fields, broad tests, observability or production work.

## Completion checks

```
uv run ruff format src tests
uv run ruff check src tests
uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
```

1. Open WebUI: send "Hello" → general reply, `[route: general]`; log `route=general nodes=router>general`.
2. Same chat: send `/study Explain what an API is` → `[route: study]`, clear explanation and one `Next step:` line; log `route=study nodes=router>study`.
3. Both replies arrive through the same endpoint, normal and streaming.

Record the commands actually run in the handover.

## Handover

- Changed files: `src/learning_companion/graph.py` (new), `src/learning_companion/main.py`, `pyproject.toml`, `uv.lock`, `docs/architecture.md`.
- Report commands run and results (format/lint, both Open WebUI messages, trace lines).
- Story 4.2 extends this with a bounded review path (reviewer/improver) on the same graph; routing and state stay as defined here.
