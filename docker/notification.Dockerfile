# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY requirements.txt .
COPY notification_module .
# Set environment variables (can also be set in Cloud Run console)
ENV PYTHONUNBUFFERED True

# Command to run your notification app
# -b 0.0.0.0:$PORT to bind to all interfaces on the port defined by Cloud Run
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app



