import json
import time
import uuid
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from .chain import MAX_HISTORY_MESSAGES, ConfigurationError
from .config import get_settings
from .graph import run_graph

app = FastAPI(title="Learning Companion")


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Message]
    stream: bool = False


def _latest_user(messages: list[Message]) -> str:
    return next((m.content for m in reversed(messages) if m.role == "user"), "")


def _history(messages: list[Message]) -> list[BaseMessage]:
    last = next(
        (i for i in range(len(messages) - 1, -1, -1) if messages[i].role == "user"),
        0,
    )
    prior = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content)
        for m in messages[:last]
        if m.role in ("user", "assistant") and m.content.strip()
    ]
    return prior[-MAX_HISTORY_MESSAGES:]


def _chunk(cid: str, model: str, delta: dict, finish: str | None = None) -> str:
    data = {
        "id": cid,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }
    return f"data: {json.dumps(data)}\n\n"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/models")
def models():
    name = get_settings().generation_model_name
    data = [{"id": name, "object": "model", "owned_by": "xai"}] if name else []
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    model = get_settings().generation_model_name or (req.model or "")
    history = _history(req.messages)
    cid = f"chatcmpl-{uuid.uuid4().hex}"
    try:
        route, reply = run_graph(_latest_user(req.messages), history)
    except ConfigurationError as e:
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "configuration_error"}},
        )
    text = f"[route: {route}] {reply}"
    if not req.stream:
        return {
            "id": cid,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
        }

    def events():
        yield _chunk(cid, model, {"role": "assistant"})
        yield _chunk(cid, model, {"content": text})
        yield _chunk(cid, model, {}, "stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
