#!/bin/bash

# Deploy the gRPC server service
kubectl apply -f grpc-server-deployment.yaml --validate=false

# Deploy Redis service
kubectl apply -f redis/redis_deployment.yaml --validate=false

# Deploy Kafka service
kubectl apply -f kafka/kafka_deployment.yaml --validate=false

echo "All deployments applied successfully!"