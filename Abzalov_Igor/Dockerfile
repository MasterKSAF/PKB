FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

COPY pyproject.toml ./
COPY src ./src
COPY .env.example ./
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN pip install --no-cache-dir -e .
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8090

CMD ["/app/docker-entrypoint.sh"]
