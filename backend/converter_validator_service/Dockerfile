FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV HOST=0.0.0.0
ENV PORT=8086

EXPOSE 8086

CMD ["sh", "-c", "uvicorn app.main:app --host $HOST --port $PORT"]
