FROM python:3.11-slim-bookworm

WORKDIR /app

# Upgrade pip only
RUN pip install --upgrade pip

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY app/ ./app/
COPY .env .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
