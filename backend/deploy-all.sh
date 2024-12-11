#!/bin/bash

# Deploy all services
kubectl apply -f services/business/business_service_deployment.yaml --validate=false
kubectl apply -f services/recommendation/recommendation_deployment.yaml --validate=false
kubectl apply -f services/user/user_service_deployment.yaml --validate=false
kubectl apply -f redis/redis_deployment.yaml --validate=false
kubectl apply -f kafka/kafka_deployment.yaml --validate=false

echo "All deployments applied successfully!"