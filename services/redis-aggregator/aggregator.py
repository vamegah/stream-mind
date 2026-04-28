#!/usr/bin/env python3
"""
Consumes raw events from Kafka, aggregates play counts per content_id in 1-minute windows,
and stores top N in Redis sorted set (trending:minute).
"""

import json
import time
from collections import defaultdict
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
import redis
import yaml

# Load config
with open("services/kafka-producer/config.yaml", "r") as f:
    config = yaml.safe_load(f)

KAFKA_BOOTSTRAP = config["kafka"]["bootstrap_servers"]
KAFKA_TOPIC = config["kafka"]["topic"]
REDIS_HOST = "localhost"
REDIS_PORT = 6379
WINDOW_SECONDS = 60
# How often to flush aggregates to Redis (every 5 seconds for near real-time)
FLUSH_INTERVAL = 5


class WindowAggregator:
    def __init__(self):
        self.current_window = {}
        self.window_start = None
        self.redis_client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
        )
        self.last_flush = time.time()

    def add_event(self, event):
        # Only count 'play' events for trending
        if event.get("event_type") != "play":
            return
        content_id = event["content_id"]
        self.current_window[content_id] = self.current_window.get(content_id, 0) + 1

    def flush_to_redis(self):
        if not self.current_window:
            return
        # Sort by count, take top 100
        sorted_items = sorted(
            self.current_window.items(), key=lambda x: x[1], reverse=True
        )[:100]
        # Use Redis sorted set: member = content_id, score = count
        key = "trending:minute"
        pipe = self.redis_client.pipeline()
        # Remove old set (or we can use ZADD with max elements; simpler to replace)
        pipe.delete(key)
        for content_id, count in sorted_items:
            pipe.zadd(key, {content_id: count})
        pipe.execute()
        print(
            f"[Aggregator] Flushed {len(sorted_items)} trending items at {datetime.now()}"
        )
        self.current_window.clear()

    def run(self):
        # Kafka consumer config
        conf = {
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": "redis-aggregator",
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        }
        consumer = Consumer(conf)
        consumer.subscribe([KAFKA_TOPIC])
        print(f"[Aggregator] Subscribed to {KAFKA_TOPIC}. Waiting for events...")
        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Consumer error: {msg.error()}")
                        break
                # Decode JSON
                try:
                    event = json.loads(msg.value().decode("utf-8"))
                except Exception as e:
                    print(f"Parse error: {e}")
                    continue
                self.add_event(event)
                # Periodic flush
                now = time.time()
                if now - self.last_flush >= FLUSH_INTERVAL:
                    self.flush_to_redis()
                    self.last_flush = now
        except KeyboardInterrupt:
            print("Stopping aggregator...")
        finally:
            self.flush_to_redis()
            consumer.close()


if __name__ == "__main__":
    agg = WindowAggregator()
    agg.run()
