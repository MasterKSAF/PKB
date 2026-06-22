"""Unit-тесты для config.py: Settings, env aliases, properties."""

from __future__ import annotations

from app.config import Settings


class TestSettingsDefaults:
    """Тесты значений по умолчанию (с перекрытием env)."""

    def test_default_values(self, monkeypatch):
        # Перекрываем env-переменные чтобы Settings взял явные значения
        monkeypatch.setenv("DB_USERNAME", "rag_user")
        monkeypatch.setenv("DB_PASSWORD", "rag_password")
        monkeypatch.setenv("DB_DATABASE", "knowledge_base")
        monkeypatch.setenv("DB_HOST", "127.0.0.1")
        monkeypatch.setenv("DB_PORT", "5432")
        for key in [
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
        ]:
            monkeypatch.delenv(key, raising=False)

        s = Settings()
        assert s.postgres_user == "rag_user"
        assert s.postgres_password == "rag_password"
        assert s.postgres_db == "knowledge_base"
        assert s.postgres_host == "127.0.0.1"
        assert s.postgres_port == 5432

    def test_service_defaults(self):
        s = Settings()
        assert s.service_name == "rag-search"
        assert s.service_version == "0.1.0"
        assert s.service_port == 8091
        assert s.log_level == "INFO"
        assert s.embedding_dim == 1024
        assert s.search_top_k == 10
        assert s.search_max_top_k == 100
        assert s.search_rrf_k == 60
        assert s.search_fetch_multiplier == 2


class TestDatabaseUrl:
    """Тесты формирования database_url."""

    def test_database_url_format(self, monkeypatch):
        monkeypatch.setenv("DB_USERNAME", "rag_user")
        monkeypatch.setenv("DB_PASSWORD", "rag_password")
        monkeypatch.setenv("DB_DATABASE", "knowledge_base")
        monkeypatch.setenv("DB_HOST", "127.0.0.1")
        monkeypatch.setenv("DB_PORT", "5432")
        for key in [
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
        ]:
            monkeypatch.delenv(key, raising=False)

        s = Settings()
        url = s.database_url
        assert url.startswith("postgresql://")
        assert "rag_user" in url
        assert "knowledge_base" in url

    def test_database_url_with_custom_values(self, monkeypatch):
        monkeypatch.setenv("DB_USERNAME", "custom_user")
        monkeypatch.setenv("DB_PASSWORD", "custom_pass")
        monkeypatch.setenv("DB_DATABASE", "custom_db")
        monkeypatch.setenv("DB_HOST", "custom.host")
        monkeypatch.setenv("DB_PORT", "5433")
        # Удаляем конфликтующие POSTGRES_* чтобы DB_* были единственными
        for key in [
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
        ]:
            monkeypatch.delenv(key, raising=False)

        s = Settings()
        url = s.database_url
        assert "custom_user" in url
        assert "custom_pass" in url
        assert "custom_db" in url
        assert "custom.host" in url
        assert "5433" in url


class TestPiiFieldsList:
    """Тесты парсинга PII-полей."""

    def test_comma_separated(self, monkeypatch):
        monkeypatch.setenv("LOG_PII_FIELDS", "password,token,secret")
        s = Settings()
        assert s.pii_fields_list == ["password", "token", "secret"]

    def test_with_whitespace(self, monkeypatch):
        monkeypatch.setenv("LOG_PII_FIELDS", " password , token ")
        s = Settings()
        assert s.pii_fields_list == ["password", "token"]

    def test_empty_string(self, monkeypatch):
        monkeypatch.setenv("LOG_PII_FIELDS", "")
        s = Settings()
        assert s.pii_fields_list == []

    def test_single_field(self, monkeypatch):
        monkeypatch.setenv("LOG_PII_FIELDS", "password")
        s = Settings()
        assert s.pii_fields_list == ["password"]


class TestGetSettingsSingleton:
    """Тесты что get_settings() возвращает синглтон."""

    def test_returns_same_instance(self):
        from app.config import get_settings

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cache_can_be_cleared(self):
        from app.config import get_settings

        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        # После сброса кэша создаётся новый экземпляр
        assert s1 is not s2
