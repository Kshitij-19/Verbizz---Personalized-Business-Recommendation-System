# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the shared requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire codebase (adjust as needed)
COPY . /app/

# Expose the gRPC server port
EXPOSE 50051

# Command to run the server
CMD ["python", "server.py"]