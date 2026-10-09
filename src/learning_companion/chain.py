import logging
from collections.abc import Iterator

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_xai import ChatXAI

from .config import get_settings

logger = logging.getLogger("uvicorn.error")

SYSTEM_INSTRUCTION = (
    "You are the Learning Companion, a friendly tutor. "
    "Explain clearly and concisely, and help the learner understand."
)

PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=SYSTEM_INSTRUCTION),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)


class ConfigurationError(Exception):
    pass


def build_messages(question: str) -> list[BaseMessage]:
    messages = PROMPT.format_messages(question=question)
    if get_settings().app_env == "development":
        roles = ", ".join(m.type for m in messages)
        logger.info("prompt roles=[%s] count=%d", roles, len(messages))
        for m in messages:
            logger.info("payload %s: %s", m.type, m.content)
    return messages


def _build_chain():
    s = get_settings()
    if not s.generation_api_key or not s.generation_model_name:
        raise ConfigurationError(
            "GENERATION_API_KEY and GENERATION_MODEL_NAME must be set in .env."
        )
    llm = ChatXAI(
        model=s.generation_model_name,
        api_key=s.generation_api_key,
        xai_api_base=s.generation_api_base_url,
    )
    return PROMPT | llm | StrOutputParser()


def answer(question: str) -> str:
    chain = _build_chain()
    build_messages(question)
    return chain.invoke({"question": question})


def stream_answer(question: str) -> Iterator[str]:
    chain = _build_chain()
    build_messages(question)
    return chain.stream({"question": question})
