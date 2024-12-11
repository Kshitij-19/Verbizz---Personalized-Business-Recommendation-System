#!/bin/bash

echo "Cleaning up Kubernetes resources..."

# Delete all deployments
echo "Deleting deployments..."
kubectl delete deployments --all

# Delete all pods
echo "Deleting pods..."
kubectl delete pods --all

# Delete all services
echo "Deleting services..."
kubectl delete services --all

# Delete all replica sets
echo "Deleting replica sets..."
kubectl delete rs --all

# Delete all config maps (optional, if you have any config maps created)
echo "Deleting config maps..."
kubectl delete configmaps --all

# Delete all persistent volume claims (optional, if you are using PVCs)
echo "Deleting persistent volume claims..."
kubectl delete pvc --all

# Delete all stateful sets (optional, if you have Kafka or other stateful services)
echo "Deleting stateful sets..."
kubectl delete statefulsets --all

echo "Cleanup complete!"