from fastapi import FastAPI
from pydantic import BaseModel
from tools import query_metrics, detect_anomaly, fetch_top_trending
from graph import graph

app = FastAPI()

# Mount tool routers
app.include_router(query_metrics.router, prefix="/tools")
app.include_router(detect_anomaly.router, prefix="/tools")
app.include_router(fetch_top_trending.router, prefix="/tools")


class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
async def chat(req: ChatRequest):
    initial_state = {
        "query": req.query,
        "intent": "",
        "tool_calls": [],
        "tool_results": [],
        "final_answer": "",
    }
    final_state = await graph.ainvoke(initial_state)
    return {"answer": final_state["final_answer"]}
