import json
import time
import uuid
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from .chain import (
    MAX_HISTORY_MESSAGES,
    ConfigurationError,
    answer,
    logger,
    stream_answer,
)
from .config import get_settings
from .study import stream_study_answer, study_answer

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


def _route(question: str) -> tuple[str, str]:
    text = question.lstrip()
    if text.startswith("/study") and (len(text) == 6 or text[6].isspace()):
        return "study", text[6:].strip()
    return "general", question


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
    route, question = _route(_latest_user(req.messages))
    history = _history(req.messages)
    cid = f"chatcmpl-{uuid.uuid4().hex}"
    logger.info("route=%s", route)
    label = f"[route: {route}] "
    # Session 4 replaces this if/else with an explicit LangGraph route.
    if route == "study":
        run, run_stream = study_answer, stream_study_answer
    else:
        run, run_stream = answer, stream_answer
    try:
        if not req.stream:
            text = label + run(question, history)
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
        stream = run_stream(question, history)
        first = next(stream, None)
    except ConfigurationError as e:
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "configuration_error"}},
        )

    def events():
        yield _chunk(cid, model, {"role": "assistant"})
        yield _chunk(cid, model, {"content": label + (first or "")})
        for piece in stream:
            if piece:
                yield _chunk(cid, model, {"content": piece})
        yield _chunk(cid, model, {}, "stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
