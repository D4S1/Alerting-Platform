FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY ui .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "ui.app:app"]
