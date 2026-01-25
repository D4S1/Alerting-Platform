FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Note the ui.app:app here
CMD exec gunicorn --bind 0.0.0.0:$PORT ui.app:app