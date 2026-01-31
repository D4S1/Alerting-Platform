FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
COPY utils/ ./utils/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "utils/db_init_cloudsql.py"]