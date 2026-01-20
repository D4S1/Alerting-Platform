FROM python:3.12.3-slim

WORKDIR /
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "ap.main:app", "--host=0.0.0.0", "--port=8080", "--reload"]