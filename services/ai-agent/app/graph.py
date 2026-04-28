from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any
import httpx
import json


class AgentState(TypedDict):
    query: str
    intent: str
    tool_calls: List[dict]
    tool_results: List[str]
    final_answer: str


# Simple intent classifier (rule-based for demo)
def classify_intent(state: AgentState) -> AgentState:
    q = state["query"].lower()
    if "trending" in q or "top" in q:
        intent = "fetch_trending"
    elif "anomaly" in q or "drop" in q:
        intent = "detect_anomaly"
    else:
        intent = "unknown"
    state["intent"] = intent
    return state


async def call_tools(state: AgentState) -> AgentState:
    results = []
    for tool in state["tool_calls"]:
        tool_name = tool["name"]
        params = tool.get("params", {})
        async with httpx.AsyncClient() as client:
            if tool_name == "query_metrics":
                resp = await client.post(
                    "http://ai-agent:8001/tools/query_metrics", json=params
                )
            elif tool_name == "detect_anomaly":
                resp = await client.get(
                    "http://ai-agent:8001/tools/detect_anomaly", params=params
                )
            else:
                continue
            results.append(resp.text)
    state["tool_results"] = results
    return state


def synthesize(state: AgentState) -> AgentState:
    # Use a simple LLM call (replace with OpenAI)
    from openai import OpenAI  # add to requirements

    client = OpenAI()
    prompt = f"Question: {state['query']}\nTool results: {state['tool_results']}\nAnswer concisely:"
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
    )
    state["final_answer"] = response.choices[0].message.content
    return state


def route_after_classify(state: AgentState):
    if state["intent"] == "fetch_trending":
        state["tool_calls"] = [
            {"name": "query_metrics", "params": {"metric": "trending"}}
        ]
        return "call_tools"
    elif state["intent"] == "detect_anomaly":
        state["tool_calls"] = [
            {"name": "detect_anomaly", "params": {"time_range": "last_1h"}}
        ]
        return "call_tools"
    else:
        # fallback to direct LLM answer without tools
        return "synthesize"


# Build graph
builder = StateGraph(AgentState)
builder.add_node("classify", classify_intent)
builder.add_node("call_tools", call_tools)
builder.add_node("synthesize", synthesize)
builder.set_entry_point("classify")
builder.add_conditional_edges(
    "classify",
    route_after_classify,
    {"call_tools": "call_tools", "synthesize": "synthesize"},
)
builder.add_edge("call_tools", "synthesize")
builder.add_edge("synthesize", END)
graph = builder.compile()
