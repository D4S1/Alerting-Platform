FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .


CMD sh -c "gunicorn --bind 0.0.0.0:$PORT ui.app:app"