from fastapi import APIRouter
from cassandra.cluster import Cluster

router = APIRouter()


@router.get("/detect_anomaly")
async def detect_anomaly(time_range: str = "last_1h"):
    cluster = Cluster(["cassandra"])
    session = cluster.connect("streammind")
    rows = session.execute(
        "SELECT content_id, drop_percent FROM anomaly_log WHERE detected_at > toTimestamp(now()) - 1h LIMIT 5"
    )
    anomalies = [
        {"content_id": r.content_id, "drop_percent": r.drop_percent} for r in rows
    ]
    return {"anomalies": anomalies}
