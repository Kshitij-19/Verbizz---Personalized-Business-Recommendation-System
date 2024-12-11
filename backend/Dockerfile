# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl

# Install grpc_health_probe binary for health checks
ADD https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/v0.4.9/grpc_health_probe-linux-amd64 /usr/local/bin/grpc_health_probe
RUN chmod +x /usr/local/bin/grpc_health_probe

# Copy the shared requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire codebase (adjust as needed)
COPY . /app/

# Expose the gRPC server port
EXPOSE 50051

# Command to run the server
CMD ["python", "server.py"]