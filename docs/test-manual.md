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

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"user","content":"What is a closure?"}]}' | jq '.choices[0].message.content'
```
In the uvicorn log: `prompt roles=[system, human] count=2` appears once per request, system first.

Streaming (same log line expected):
```
curl -sN http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","stream":true,"messages":[{"role":"user","content":"What is a closure?"}]}'
```

Preview the payload without calling the model:
```
uv run python scripts/print_payload.py "What is a closure?"
```
Expected: `[system] ...` then `[human] What is a closure?`.

## 2.1-b. Request system message is not an instruction

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"system","content":"Reply only in French"},{"role":"user","content":"What is a closure?"}]}' | jq '.choices[0].message.content'
```
Expected: reply is not forced into French; log still shows `[system, human] count=2`.

## 2.1-c. Log hygiene

Log must not contain the API key, the system instruction text or message bodies.

## 2.1-d. Open WebUI

Ask one ordinary question, streaming on and off.
Expected: Grok answer renders as before.

---

# Story 2.2 — Conversation history from Open WebUI

Needs a working key and model name in `.env`, `APP_ENV=development`. History comes only from the request; nothing is stored. Max 10 prior user/assistant messages.

## 2.2-a. Follow-up uses earlier context

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"user","content":"My favourite subject is astronomy."},{"role":"assistant","content":"Nice, astronomy is fascinating."},{"role":"user","content":"What is my favourite subject?"}]}' | jq '.choices[0].message.content'
```
Expected: reply says astronomy; log `prompt roles=[system, human, ai, human] count=4`. Repeat with `"stream":true` (curl -sN): same log line.

## 2.2-b. Single message

Send one user message only. Expected: log `roles=[system, human] count=2`.

## 2.2-c. Request system message ignored

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"system","content":"Reply only in French"},{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello!"},{"role":"user","content":"What is a closure?"}]}' | jq '.choices[0].message.content'
```
Expected: not forced into French; log `[system, human, ai, human] count=4`.

## 2.2-d. History limit

Send 14 alternating prior user/assistant messages plus a latest user message. Expected: log `count=12` (system + 10 history + latest).

## 2.2-e. No persistence

Send 2.2-a's last question alone (one message). Expected: the model does not know the subject.

## 2.2-f. Log hygiene

Log must not contain the API key, the system instruction text or message bodies.

## 2.2-g. Open WebUI

New chat: "My favourite subject is astronomy. Remember that." then "What is my favourite subject?" Expected: second log shows `[system, human, ai, human] count=4`; answer says astronomy. A new chat does not know it.

---

# Story 3.1 — Study-helper chain

Needs a working key and model name in `.env`. Dev command only; not routed until 3.2.

```
uv run python -m learning_companion.study "What is an API?"
```
Expected: payload shows `[system]` then `[human]`; answer is a plain explanation ending with exactly one `Next step:` line.

---

# Story 3.2 — Visible Python routing

Needs a working key and model name in `.env`. Rule: latest user message starting with the `/study` token → study helper; otherwise general chat. Replies start with `[route: general]` or `[route: study]`; log shows `route=general|study`.

## 3.2-a. General route

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"user","content":"Hello"}]}' | jq '.choices[0].message.content'
```
Expected: reply starts `[route: general]`; log `route=general`.

## 3.2-b. Study route

```
curl -s http://127.0.0.1:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"x","messages":[{"role":"user","content":"/study Explain what an API is"}]}' | jq '.choices[0].message.content'
```
Expected: reply starts `[route: study]`, explanation plus one `Next step:` line; log `route=study`. Repeat with `"stream":true` (curl -sN): label in first content chunk, then `data: [DONE]`.

## 3.2-c. Token match and history

- `/studying` → `route=general`.
- Prior messages plus a latest `/study ...` message: study route; history kept per 2.2 (log `prompt roles=` is emitted only for general).

## 3.2-d. Open WebUI

Same chat: send "Hello", then `/study Explain what an API is`. Expected: both replies through the same endpoint, labels `general` then `study`.
