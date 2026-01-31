# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
COPY notification_module/ ./notification_module/
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (can also be set in Cloud Run console)
ENV PYTHONUNBUFFERED=true

# Command to run your notification app
# -b 0.0.0.0:$PORT to bind to all interfaces on the port defined by Cloud Run
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "0", "notification_module.main:app"]
