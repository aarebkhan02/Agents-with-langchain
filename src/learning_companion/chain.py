from collections.abc import Iterator

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_xai import ChatXAI

from .config import get_settings

SYSTEM_INSTRUCTION = (
    "You are the Learning Companion, a friendly tutor. "
    "Explain clearly and concisely, and help the learner understand."
)


class ConfigurationError(Exception):
    pass


def _build_chain():
    s = get_settings()
    if not s.generation_api_key or not s.generation_model_name:
        raise ConfigurationError(
            "GENERATION_API_KEY and GENERATION_MODEL_NAME must be set in .env."
        )
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_INSTRUCTION), ("human", "{question}")]
    )
    llm = ChatXAI(
        model=s.generation_model_name,
        api_key=s.generation_api_key,
        xai_api_base=s.generation_api_base_url,
    )
    return prompt | llm | StrOutputParser()


def answer(question: str) -> str:
    return _build_chain().invoke({"question": question})


def stream_answer(question: str) -> Iterator[str]:
    return _build_chain().stream({"question": question})
