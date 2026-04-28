import pytest
import time
import json
from confluent_kafka import Consumer, Producer, KafkaError
import sys

sys.path.insert(0, "services/kafka-producer")
from simulator import load_config, create_producer, generate_event

KAFKA_TOPIC = "raw-events"
BOOTSTRAP_SERVERS = "localhost:9092"


@pytest.fixture(scope="module")
def kafka_consumer():
    conf = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": "test-group",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_TOPIC])
    yield consumer
    consumer.close()


def test_produce_and_consume(kafka_consumer):
    # Produce 1000 events using the simulator's generator
    producer_conf = {"bootstrap.servers": BOOTSTRAP_SERVERS, "acks": 1}
    producer = Producer(producer_conf)
    config = load_config("services/kafka-producer/config.yaml")
    topic = config["kafka"]["topic"]

    events = []
    for _ in range(1000):
        event = generate_event(config)
        events.append(event)
        producer.produce(topic, value=json.dumps(event).encode("utf-8"))
        producer.poll(0)
    producer.flush()

    # Consume and verify each event matches schema
    consumed_count = 0
    start = time.time()
    timeout = 10  # seconds
    while consumed_count < 1000 and (time.time() - start) < timeout:
        msg = kafka_consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                pytest.fail(f"Consumer error: {msg.error()}")
        value = msg.value().decode("utf-8")
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON: {value}")
        # Basic schema validation
        required_fields = [
            "event_id",
            "event_type",
            "user_id_token",
            "content_id",
            "timestamp_ms",
            "region",
            "device_type",
        ]
        for field in required_fields:
            assert field in data, f"Missing field {field}"
        # event_type must be one of allowed types
        assert data["event_type"] in ["play", "pause", "search", "click"]
        assert isinstance(data["timestamp_ms"], int)
        consumed_count += 1

    assert consumed_count == 1000, f"Only consumed {consumed_count}/1000 events"
    print("✅ Integration test passed: 1000 events produced and validated.")
