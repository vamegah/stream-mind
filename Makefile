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