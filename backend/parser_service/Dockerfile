# Используем официальный образ Python 3.11 slim
FROM python:3.11-slim

# Установка переменных окружения для Python (без буферизации, логи сразу)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка системных зависимостей:
# - openjdk-11-jre-headless: для работы opendataloader-pdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Установка Java 11 в PATH (обычно уже прописан)
ENV JAVA_HOME=/usr/lib/jvm/default-jre

# Создание непривилегированного пользователя
RUN groupadd -r parser && useradd -r -g parser parser

WORKDIR /app

# Копирование только requirements.txt для установки зависимостей (кэширование слоя)
COPY requirements.txt .

# Установка Python-зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего исходного кода (с учётом .dockerignore)
COPY --chown=parser:parser ./app /app/app

# Переключение на непривилегированного пользователя
USER parser

# Порт, указанный в конфигурации (по умолчанию 8087)
EXPOSE 8087

# Запуск uvicorn сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8087"]