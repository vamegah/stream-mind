from locust import HttpUser, task, between, events
import json
import random


class StreamMindUser(HttpUser):
    wait_time = between(0.5, 2)  # simulate realistic user think time

    def on_start(self):
        # Simulate a user token (privacy budget aware)
        self.user_token = f"user_{random.randint(1, 100000)}"

    @task(3)
    def get_metrics(self):
        self.client.get("/api/v1/metrics/live", name="/metrics/live")

    @task(2)
    def get_anomalies(self):
        self.client.get("/api/v1/anomalies", name="/anomalies")

    @task(1)
    def chat_query(self):
        # Simple AI query (no streaming for load test)
        payload = {"query": "What is trending now?"}
        self.client.post("/api/v1/ai/chat", json=payload, name="/ai/chat")

    @task(1)
    def privacy_budget(self):
        self.client.get(
            f"/api/v1/privacy/budget/{self.user_token}", name="/privacy/budget"
        )

    @task(1)
    def websocket(self):
        # Locust doesn't natively support WebSocket in HttpUser; we can use a separate client or ignore.
        # For simplicity, we skip WebSocket load testing here.
        pass


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Starting load test against StreamMind API")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Load test finished")
