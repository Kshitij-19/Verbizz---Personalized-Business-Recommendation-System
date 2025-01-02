#!/bin/bash

# Deploy the gRPC server service
kubectl apply -f grpc-server-deployment.yaml --validate=false

# Deploy Redis service
kubectl apply -f redis/redis_deployment.yaml --validate=false

# Deploy Kafka service
kubectl apply -f kafka/kafka_deployment.yaml --validate=false

# Deploy Postgres service
kubectl apply -f db/postgres-deployment.yaml --validate=false
kubectl apply -f db/postgres-pvc.yaml --validate=false
kubectl apply -f db/postgres-secret.yaml --validate=false
kubectl apply -f db/postgres-backup-cronjob.yaml --validate=false

echo "All deployments applied successfully!"