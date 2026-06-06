FROM python:3.13-slim

RUN useradd -m -r appuser && \
    apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

USER appuser
EXPOSE 8091

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8091/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8091"]