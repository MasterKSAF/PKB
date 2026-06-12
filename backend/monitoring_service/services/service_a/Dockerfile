FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt (путь относительно контекста ./services)
COPY service_a/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование общей библиотеки telemetry_lib (находится в корне контекста)
COPY telemetry_lib/ /app/telemetry_lib/

# Копирование кода сервиса
COPY service_a/main.py .

ENV OTEL_EXPORTER_OTLP_INSECURE=true

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]