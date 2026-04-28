from fastapi import APIRouter, HTTPException
from cassandra.cluster import Cluster
import os

router = APIRouter(prefix="/api/v1/anomalies", tags=["anomalies"])


def get_cassandra_session():
    cluster = Cluster([os.getenv("CASSANDRA_HOST", "cassandra")])
    return cluster.connect("streammind")


@router.get("/")
async def list_anomalies(limit: int = 20):
    session = get_cassandra_session()
    rows = session.execute(
        f"SELECT anomaly_id, content_id, detected_at, drop_percent, resolved FROM anomaly_log LIMIT {limit}"
    )
    anomalies = []
    for row in rows:
        anomalies.append(
            {
                "anomaly_id": row.anomaly_id,
                "content_id": row.content_id,
                "detected_at": row.detected_at.isoformat(),
                "drop_percent": row.drop_percent,
                "resolved": row.resolved,
            }
        )
    return anomalies
