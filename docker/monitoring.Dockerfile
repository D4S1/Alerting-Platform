FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
COPY monitoring_module/ ./monitoring_module/
COPY utils/ ./utils/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "monitoring_module/monitoring_engine.py"]
