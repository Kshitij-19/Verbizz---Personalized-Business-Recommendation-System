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

# Copy the business service code
COPY ./services/business/business_service.py /app/

# Expose the gRPC port
EXPOSE 50052

# Command to run the service
CMD ["python", "business_service.py"]
