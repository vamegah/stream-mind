import asyncio
import json
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Global Redis client
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = await redis.from_url("redis://localhost:6379", decode_responses=True)
    yield
    await redis_client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.get("/api/v1/metrics/live")
async def get_live_metrics():
    """Return current trending and active users count (simulated)."""
    trending = await redis_client.zrevrange("trending:minute", 0, 9, withscores=True)
    # Simulate active users = random walk + events from Kafka? For simplicity, use a mock value.
    # In real implementation, you'd track unique user_id_token in Redis HyperLogLog.
    active_users = (
        await redis_client.pfcount("active_users")
        if await redis_client.exists("active_users")
        else 42
    )
    return {
        "trending": [
            {"content_id": item[0], "count": int(item[1])} for item in trending
        ],
        "active_users": active_users,
        "timestamp": int(asyncio.get_event_loop().time() * 1000),
    }


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send updates every 2 seconds
        while True:
            metrics = await get_live_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
