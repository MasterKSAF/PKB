FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8083

EXPOSE 8083

CMD ["sh", "-c", "uvicorn app.main:app --host $APP_HOST --port $APP_PORT"]
