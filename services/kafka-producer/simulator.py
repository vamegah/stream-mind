#!/usr/bin/env python3
"""
Apple TV event simulator – produces events to Kafka at a given rate.
Usage: python simulator.py [--rate events_per_second] [--duration seconds]
"""

import argparse
import time
import random
import uuid
import yaml
from datetime import datetime
from confluent_kafka import Producer
from faker import Faker

fake = Faker()

def load_config(config_path="config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_producer(config):
    conf = config['kafka']['producer_conf'].copy()
    conf['bootstrap.servers'] = config['kafka']['bootstrap_servers']
    return Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        # Optional: print success for debugging (disable in production)
        # print(f"✅ Delivered to {msg.topic()} [{msg.partition()}]")
        pass

def generate_event(config):
    """Generate one random Apple TV event."""
    event_type = random.choice(config['simulation']['event_types'])
    user_id_token = f"user_{fake.uuid4()}"   # tokenized, no PII
    content_id = f"show_{random.randint(1, config['simulation']['content_pool_size'])}"
    region = random.choice(config['simulation']['regions'])
    device_type = random.choice(config['simulation']['device_types'])
    # Use current time in milliseconds
    timestamp_ms = int(time.time() * 1000)
    event_id = str(uuid.uuid4())

    event = {
        "event_id": event_id,
        "event_type": event_type,
        "user_id_token": user_id_token,
        "content_id": content_id,
        "timestamp_ms": timestamp_ms,
        "region": region,
        "device_type": device_type
    }
    return event

def produce_events(producer, topic, rate_per_sec, duration_sec=None):
    """Produce events at given rate (events per second)."""
    interval = 1.0 / rate_per_sec
    start_time = time.time()
    count = 0
    try:
        while True:
            if duration_sec and (time.time() - start_time) >= duration_sec:
                break
            event = generate_event(config)
            # Serialize as JSON (simple for now, later Avro)
            producer.produce(topic, value=str(event).encode('utf-8'), callback=delivery_report)
            producer.poll(0)  # trigger callbacks
            count += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n🛑 Stopped by user. Produced {count} events.")
    finally:
        producer.flush()
        print(f"📤 Flushed. Total produced: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apple TV event simulator")
    parser.add_argument("--rate", type=int, help="Events per second (overrides config)")
    parser.add_argument("--duration", type=int, help="Duration in seconds (default: infinite)")
    args = parser.parse_args()

    config = load_config()
    rate = args.rate if args.rate else config['simulation']['events_per_second']
    producer = create_producer(config)
    topic = config['kafka']['topic']
    print(f"🚀 Starting producer: {rate} events/sec to topic '{topic}'")
    produce_events(producer, topic, rate, args.duration)