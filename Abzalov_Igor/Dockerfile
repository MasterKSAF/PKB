FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY src ./src
COPY .env.example ./

RUN pip install --no-cache-dir -e .

EXPOSE 8090

CMD ["python", "-m", "uvicorn", "rag_builder.main:app", "--host", "0.0.0.0", "--port", "8090"]
