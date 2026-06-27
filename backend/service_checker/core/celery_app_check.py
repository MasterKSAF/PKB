"""
PKB Neuroassistant — Celery app для health check (уникальное имя).

Не импортирует реальный celery_app оркестратора, чтобы не пересекаться
с production. Используется только для проверки доступности Redis-брокера
внутри Docker-окружения.
"""
from celery import Celery

celery_app = Celery("orchestrator_pipeline_check")
