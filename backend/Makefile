# Load environment variables from .env file
include .env
export $(shell sed 's/=.*//' .env)

# Define variables
DOCKER_USERNAME := $(DOCKER_USERNAME)
VERSION ?= latest

# Services list (for modular builds, if needed in the future)
SERVICES := grpc-server

# Default target (prepare and build all services)
all: build

# Build Docker image for server.py
build:
	@for service in $(SERVICES); do \
		echo "Building $$service service..."; \
		docker build -t $(DOCKER_USERNAME)/$$service:$(VERSION) .; \
	done

# Push Docker images for server to Docker Hub
push:
	@for service in $(SERVICES); do \
		echo "Pushing $$service service..."; \
		docker push $(DOCKER_USERNAME)/$$service:$(VERSION); \
	done

# Clean up dangling images and Docker cache
clean:
	@echo "Cleaning up dangling Docker images..."
	@if [ "$(docker images -f "dangling=true" -q)" ]; then \
		docker rmi -f $(docker images -f "dangling=true" -q); \
	else \
		echo "No dangling images to clean."; \
	fi

	@echo "Cleaning up all Docker images..."
	@if [ "$(docker images -q)" ]; then \
		docker rmi -f $(docker images -q); \
	else \
		echo "No Docker images to clean."; \
	fi

	@echo "Cleaning up Docker build cache..."
	docker builder prune -f

# Build and Push Docker image for server.py
deploy: build push

# Remove containers, images, and volumes
reset:
	@echo "Stopping and removing all containers..."
	@docker stop $$(docker ps -aq) || true
	@docker rm $$(docker ps -aq) || true
	@echo "Removing all Docker images..."
	@if [ "$(docker images -aq)" ]; then \
		docker rmi -f $$(docker images -aq) || true; \
	else \
		echo "No Docker images to clean."; \
	fi
	@echo "Pruning Docker volumes..."
	docker volume prune -f || true
	@echo "Pruning Docker networks..."
	docker network prune -f || true
