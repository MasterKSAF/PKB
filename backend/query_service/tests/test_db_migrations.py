from app.db import _PG_MIGRATIONS
from app.models import ChatSession


def test_new_session_columns_have_pg_migration():
    migration_text = " ".join(_PG_MIGRATIONS).lower()
    for col in ("summary", "summarized_until_message_id"):
        assert col in ChatSession.__table__.columns
        assert col in migration_text


def test_session_model_exposes_summary_fields():
    cols = ChatSession.__table__.columns
    assert "summary" in cols
    assert "summarized_until_message_id" in cols
