import sys
from collections.abc import Iterator

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_xai import ChatXAI

from .chain import ConfigurationError
from .config import get_settings

STUDY_SYSTEM_INSTRUCTION = (
    "You are the Learning Companion study helper. "
    "Explain beginner technical concepts in plain language. "
    "Give a concise explanation, a small example where useful, and end with "
    "exactly one line starting 'Next step:' suggesting one small learning step. "
    "Do not claim to research, browse, retrieve course data, or guarantee "
    "that your answer is correct."
)

STUDY_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=STUDY_SYSTEM_INSTRUCTION),
        MessagesPlaceholder("history"),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)


def study_messages(question: str, history: list[BaseMessage] | None = None):
    return STUDY_PROMPT.format_messages(question=question, history=history or [])


def _build_study_chain():
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
    return STUDY_PROMPT | llm | StrOutputParser()


def study_answer(question: str, history: list[BaseMessage] | None = None) -> str:
    chain = _build_study_chain()
    return chain.invoke({"question": question, "history": history or []})


def stream_study_answer(
    question: str, history: list[BaseMessage] | None = None
) -> Iterator[str]:
    chain = _build_study_chain()
    return chain.stream({"question": question, "history": history or []})


def main() -> None:
    question = " ".join(sys.argv[1:]) or "What is an API?"
    print("=== PAYLOAD SENT TO LLM ===")
    for m in study_messages(question):
        print(f"[{m.type}]\n{m.content}\n")
    print("=== ANSWER ===")
    try:
        print(study_answer(question))
    except ConfigurationError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
