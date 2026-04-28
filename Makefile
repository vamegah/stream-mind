.PHONY: up down logs ps clean

# Start all services in detached mode
up:
	docker compose up -d

# Stop and remove all containers, networks, but keep volumes
down:
	docker compose down

# Stop and remove containers AND volumes (reset data)
clean:
	docker compose down -v

# Tail logs from all services
logs:
	docker compose logs -f

# Show running containers status
ps:
	docker compose ps

# Restart all services
restart: down up

# ===== Phase 1: Event Producer =====
simulate:
	@echo "Starting event simulator at $(or $(RATE),1000) events/sec..."
	cd services/kafka-producer && python simulator.py --rate $(or $(RATE),1000)

simulate-load:
	cd services/kafka-producer && ./load_test.sh $(or $(RATE),1000) $(or $(DURATION),60)

consume-debug:
	cd services/kafka-producer && python consumer_debug.py --topic raw-events

test-integration:
	pytest tests/integration/test_kafka_producer.py -v

# Phase 3: API + Dashboard
api-up:
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d api frontend redis-aggregator

api-down:
	docker compose -f docker-compose.override.yml down api frontend redis-aggregator

dashboard-logs:
	docker compose logs -f api frontend redis-aggregator

.PHONY: api-up api-down dashboard-logs

all: up api-up
	@echo "All services started. Access dashboard at http://localhost:5173"