# Load environment variables from .env file
include .env
export $(shell sed 's/=.*//' .env)

# Define variables
DOCKER_USERNAME := $(DOCKER_USERNAME)
VERSION ?= latest

# Define services and their directories
SERVICES := business recommendation user

# Default target (prepare and build all services)
all: prepare build

# Prepare: Copy shared requirements.txt to each service directory
prepare:
	@for service in $(SERVICES); do \
		echo "Preparing $$service service..."; \
		cp requirements.txt ./services/$$service/requirements.txt; \
	done

# Build Docker images for all services
build:
	@for service in $(SERVICES); do \
		echo "Building $$service service..."; \
		docker build -t $(DOCKER_USERNAME)/$$service-service:$(VERSION) -f ./services/$$service/Dockerfile .; \
	done

# Push Docker images for all services to Docker Hub
push:
	@for service in $(SERVICES); do \
		echo "Pushing $$service service..."; \
		docker push $(DOCKER_USERNAME)/$$service-service:$(VERSION); \
	done

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

# Build and Push Docker images
deploy: prepare build push