from typing import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph

from .chain import answer, logger
from .study import study_answer


class GraphState(TypedDict, total=False):
    user_message: str  # latest user message as received
    messages: list[BaseMessage]  # prior request history (Story 2.2)
    route: str  # "general" or "study", written by the router
    answer: str  # final text, written by an answer node


def _split(user_message: str) -> tuple[str, str]:
    text = user_message.lstrip()
    if text.startswith("/study") and (len(text) == 6 or text[6].isspace()):
        return "study", text[6:].strip()
    return "general", user_message


def router_node(state: GraphState) -> dict:
    route, _ = _split(state["user_message"])
    return {"route": route}


def general_node(state: GraphState) -> dict:
    return {"answer": answer(state["user_message"], state["messages"])}


def study_node(state: GraphState) -> dict:
    _, question = _split(state["user_message"])
    return {"answer": study_answer(question, state["messages"])}


_builder = StateGraph(GraphState)
_builder.add_node("router", router_node)
_builder.add_node("general", general_node)
_builder.add_node("study", study_node)
_builder.add_edge(START, "router")
_builder.add_conditional_edges(
    "router", lambda s: s["route"], {"general": "general", "study": "study"}
)
_builder.add_edge("general", END)
_builder.add_edge("study", END)
GRAPH = _builder.compile()


def run_graph(user_message: str, messages: list[BaseMessage]) -> tuple[str, str]:
    state = GRAPH.invoke({"user_message": user_message, "messages": messages})
    logger.info("route=%s nodes=router>%s", state["route"], state["route"])
    return state["route"], state["answer"]
