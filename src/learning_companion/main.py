import json
import time
import uuid
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from .chain import ConfigurationError, answer, stream_answer
from .config import get_settings

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
    question = _latest_user(req.messages)
    cid = f"chatcmpl-{uuid.uuid4().hex}"
    try:
        if not req.stream:
            text = answer(question)
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
        stream = stream_answer(question)
        first = next(stream, None)
    except ConfigurationError as e:
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "configuration_error"}},
        )

    def events():
        yield _chunk(cid, model, {"role": "assistant"})
        if first:
            yield _chunk(cid, model, {"content": first})
        for piece in stream:
            if piece:
                yield _chunk(cid, model, {"content": piece})
        yield _chunk(cid, model, {}, "stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
