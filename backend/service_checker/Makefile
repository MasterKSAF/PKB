# PKB Neuroassistant — Service Checker
# ============================================================================
# Targets:
#   make setup   — подготовить модель + запустить Docker Compose
#   make model   — только подготовить модель TEI
#   make up      — запустить Docker Compose
#   make down    — остановить Docker Compose
#   make restart — перезапустить Docker Compose
#   make logs    — логи Docker Compose
#   make ps      — статус контейнеров
#   make test    — запустить unit-тесты
# ============================================================================

.PHONY: setup model up down restart logs ps test

# Полный setup с нуля
setup: model up
	@echo "✓ Setup complete. Run 'make logs' to see container logs."

# Подготовка локальной модели TEI
model:
	@echo "→ Installing huggingface-hub (if needed)..."
	@pip install huggingface-hub -q
	@echo "→ Preparing TEI model..."
	@python docker/prepare_tei_model.py
	@echo "✓ Model prepared."

# Запуск Docker Compose
up:
	@docker compose -f docker/docker-compose.yml up -d
	@echo "✓ Docker Compose started."

# Остановка Docker Compose
down:
	@docker compose -f docker/docker-compose.yml down
	@echo "✓ Docker Compose stopped."

# Перезапуск
restart: down up

# Логи
logs:
	@docker compose -f docker/docker-compose.yml logs -f

# Статус контейнеров
ps:
	@docker compose -f docker/docker-compose.yml ps

# Unit-тесты
test:
	@python -m pytest tests/ -v
