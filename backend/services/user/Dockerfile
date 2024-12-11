# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY ../../requirements.txt /app/

# Copy the codegen directory
COPY ../../codegen /app/codegen

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the user service code
COPY ./services/user/user_service.py /app/

# Expose the gRPC port
EXPOSE 50051

# Command to run the service
CMD ["python", "user_service.py"]