# Test manual — Story 1.1

Run from repo root. Use `curl -s`; never pretty-print full responses.

## 1. Setup checks

```
uv sync
uv run ruff format src tests
uv run ruff check src tests
uv run pytest tests/test_health.py
```
Expected: all pass.

## 2. Start app (terminal A)

```
uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
```
Expected: starts with no `.env` key set.

## 3. Endpoints (terminal B)

| Test | Command | Expected |
|---|---|---|
| Health | `curl -s http://127.0.0.1:8000/health` | `{"status":"ok"}` |
| Models | `curl -s http://127.0.0.1:8000/v1/models` | list with configured `GENERATION_MODEL_NAME` (empty list if unset) |

## 4. No key / no model name (config error)

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"user","content":"hi"}]}'
```
Expected: HTTP 500, `{"error":{"message":"GENERATION_API_KEY and GENERATION_MODEL_NAME must be set in .env.", ...}}`. Repeat with `"stream":true`: same error JSON.

## 5. With key and model name in `.env` (restart app)

Normal:
```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"user","content":"Explain recursion in one line"}]}' | jq '.choices[0].message.content'
```
Expected: one Grok reply, `finish_reason` `stop`.

Streaming:
```
curl -sN http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","stream":true,"messages":[{"role":"user","content":"Explain recursion in one line"}]}'
```
Expected: `data: {...}` chunks with `delta.content`, a stop chunk, then `data: [DONE]`.

## 5b. Only latest user message used

Send `messages` with an earlier user turn plus a new one; the reply addresses only the latest.

## 6. Open WebUI

1. Connection base URL `http://127.0.0.1:8000/v1`; select the configured model.
2. Send a message with streaming off: one Grok reply appears.
3. Send a message with streaming on: reply appears progressively.

Do not modify Open WebUI itself.

## 7. Secrets

`git status` must not list `.env`.
