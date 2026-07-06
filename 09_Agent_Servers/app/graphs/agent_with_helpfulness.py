from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.models import get_chat_model
from app.tools import get_tool_belt

SYSTEM_PROMPT = (
    "You are a helpful assistant specialized in feline (cat) health. "
    "Use the retrieve_information tool for cat-health questions, web search for "
    "current information, and Arxiv for research papers. Cite tool results when "
    "they inform your answer."
)

HELPFULNESS_PROMPT = (
    "You are a strict grader judging whether an assistant's answer is helpful and "
    "directly addresses the user's original question.\n\n"
    "Original question:\n{question}\n\n"
    "Assistant answer:\n{answer}\n\n"
    "Reply with exactly 'Y' if the answer is helpful and complete, otherwise "
    "reply with exactly 'N'."
)

MAX_ATTEMPTS = 3


class HelpfulnessState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    attempts: int


_tool_belt = get_tool_belt()
_model = get_chat_model().bind_tools(_tool_belt)
_judge = get_chat_model()


def _first_human_question(messages: list[BaseMessage]) -> str:
    for message in messages:
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def call_model(state: HelpfulnessState) -> dict:
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]
    response = _model.invoke(messages)
    return {"messages": [response], "attempts": state.get("attempts", 0)}


def route_after_model(state: HelpfulnessState) -> Literal["tools", "helpfulness"]:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "helpfulness"


def helpfulness_check(state: HelpfulnessState) -> dict:
    return {"attempts": state.get("attempts", 0) + 1}


def route_after_helpfulness(state: HelpfulnessState) -> Literal["continue", "end"]:
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        return "end"

    question = _first_human_question(state["messages"])
    answer = str(state["messages"][-1].content)
    verdict = _judge.invoke(
        [
            HumanMessage(
                content=HELPFULNESS_PROMPT.format(question=question, answer=answer)
            )
        ]
    )
    if "Y" in str(verdict.content).upper():
        return "end"
    return "continue"


def add_retry_nudge(state: HelpfulnessState) -> dict:
    return {
        "messages": [
            HumanMessage(
                content=(
                    "That response was judged not fully helpful. Please try again "
                    "and answer the original question more directly and completely."
                )
            )
        ]
    }


builder = StateGraph(HelpfulnessState)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(_tool_belt))
builder.add_node("helpfulness", helpfulness_check)
builder.add_node("retry", add_retry_nudge)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    route_after_model,
    {"tools": "tools", "helpfulness": "helpfulness"},
)
builder.add_edge("tools", "agent")
builder.add_conditional_edges(
    "helpfulness",
    route_after_helpfulness,
    {"continue": "retry", "end": END},
)
builder.add_edge("retry", "agent")

graph = builder.compile()
