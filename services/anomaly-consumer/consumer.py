#!/usr/bin/env python3
import json
from cassandra.cluster import Cluster
from confluent_kafka import Consumer, KafkaError
import uuid
import time

KAFKA_BOOTSTRAP = "kafka:9092"
ANOMALY_TOPIC = "anomalies"
CASSANDRA_HOST = "cassandra"
CASSANDRA_KEYSPACE = "streammind"


def init_cassandra():
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect()
    session.execute(
        f"CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE} WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}"
    )
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS streammind.anomaly_log (
            anomaly_id text PRIMARY KEY,
            content_id text,
            detected_at timestamp,
            drop_percent double,
            window_end timestamp,
            resolved boolean
        )
    """
    )
    return session


def consume_and_store():
    session = init_cassandra()
    conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": "anomaly-consumer",
        "auto.offset.reset": "earliest",
    }
    consumer = Consumer(conf)
    consumer.subscribe([ANOMALY_TOPIC])
    print("Listening for anomalies...")
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print(f"Error: {msg.error()}")
            continue
        try:
            data = json.loads(msg.value().decode("utf-8"))
            anomaly_id = data.get("anomaly_id", str(uuid.uuid4()))
            session.execute(
                """
                INSERT INTO streammind.anomaly_log (anomaly_id, content_id, detected_at, drop_percent, window_end, resolved)
                VALUES (%s, %s, toTimestamp(now()), %s, %s, false)
            """,
                (
                    anomaly_id,
                    data["content_id"],
                    data["drop_percent"],
                    data["window_end"],
                ),
            )
            print(f"Stored anomaly: {anomaly_id}")
        except Exception as e:
            print(f"Error processing: {e}")


if __name__ == "__main__":
    consume_and_store()
