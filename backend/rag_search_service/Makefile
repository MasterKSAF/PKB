.PHONY: install run test test-unit test-int db-up db-down lint format clean

# Установка зависимостей
install:
	pip install -e ".[dev]"

# Запуск сервиса
run:
	uvicorn app.main:app --reload --port 8091

# Запуск всех тестов
test:
	pytest tests/ -v

# Запуск только unit-тестов
test-unit:
	pytest tests/unit/ -v

# Запуск integration-тестов (требует запущенную БД)
test-int:
	pytest tests/integration/ -v

# Поднять БД в Docker
db-up:
	docker compose up -d
	@echo "Waiting for DB to initialize..."
	@sleep 5
	docker compose exec postgres psql -U rag_user -d knowledge_base -c "SELECT COUNT(*) FROM rag.document_chunks;"

# Остановить и удалить БД (с удалением данных!)
db-down:
	docker compose down -v

# Форматирование
format:
	ruff format app/ tests/

# Очистка кэша и временных файлов
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +