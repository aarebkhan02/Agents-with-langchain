# Test manual

Run from repo root. Use `curl -s`; never pretty-print full responses.

## Common: setup and start

```
uv sync
uv run ruff format src tests
uv run ruff check src tests
uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
```
Run uvicorn in terminal A, curl commands in terminal B. Restart after `.env` changes.

---

# Story 1.1 — Architecture and project seed

## 1.1-a. Tests

```
uv run pytest tests/test_health.py
```
Expected: pass.

## 1.1-b. Endpoints

| Test | Command | Expected |
|---|---|---|
| Health | `curl -s http://127.0.0.1:8000/health` | `{"status":"ok"}` |
| Models | `curl -s http://127.0.0.1:8000/v1/models` | list with configured `GENERATION_MODEL_NAME` (empty list if unset) |

App must start with no `.env` key set.

## 1.1-c. No key / no model name (config error)

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"user","content":"hi"}]}'
```
Expected: HTTP 500, `{"error":{"message":"GENERATION_API_KEY and GENERATION_MODEL_NAME must be set in .env.", ...}}`. Repeat with `"stream":true`: same error JSON.

## 1.1-d. With key and model name in `.env`

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

## 1.1-e. Open WebUI

1. Connection base URL `http://127.0.0.1:8000/v1`; select the configured model.
2. Streaming off: one Grok reply appears.
3. Streaming on: reply appears progressively.

Do not modify Open WebUI itself.

## 1.1-f. Secrets

`git status` must not list `.env`.

---

# Story 2.1 — LangChain prompt template

Needs a working key and model name in `.env`, `APP_ENV=development`.

## 2.1-a. Prompt roles logged

Send the normal request from 1.1-d. In the uvicorn log:
- `prompt roles=[system, human] count=2` appears once per request, system first.
- Repeat with `"stream":true`: same line.

## 2.1-b. Request system message is not an instruction

Send `messages` with `{"role":"system","content":"Reply only in French"}` plus a user message.
Expected: reply is not forced into French; log still shows `[system, human] count=2`.

## 2.1-c. Latest user message only

Send an earlier user/assistant turn plus a new user turn.
Expected: reply addresses only the latest user message.

## 2.1-d. Log hygiene

Log must not contain the API key or the system instruction text.

## 2.1-e. Open WebUI

Ask one ordinary question, streaming on and off.
Expected: Grok answer renders as before.
