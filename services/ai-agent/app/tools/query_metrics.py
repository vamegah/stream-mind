from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import redis
import json

router = APIRouter()
redis_client = redis.Redis(host="redis", decode_responses=True)


class MetricsQuery(BaseModel):
    metric: str
    time_range: str  # e.g., "last_5m", "last_1h"
    content_id: str = None


@router.post("/query_metrics")
async def query_metrics(q: MetricsQuery):
    # For demo, we support "trending" and "play_count"
    if q.metric == "trending":
        top = redis_client.zrevrange("trending:minute", 0, 9, withscores=True)
        return {"trending": [{"content_id": t[0], "count": t[1]} for t in top]}
    elif q.metric == "play_count":
        # For a specific content_id, return the count from Redis sorted set
        count = redis_client.zscore("trending:minute", q.content_id) or 0
        return {"content_id": q.content_id, "play_count": int(count)}
    else:
        raise HTTPException(400, "Unsupported metric")
