FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY monitoring_module .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "monitoring/monitoring_engine.py"]
