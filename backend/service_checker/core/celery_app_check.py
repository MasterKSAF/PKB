"""
PKB Neuroassistant — Celery app для health check (уникальное имя).

Импортирует реальное приложение оркестратора, но с уникальным именем,
чтобы не конфликтовать с production. Использует тот же брокер.
"""
from app.celery_app import celery_app
