from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatProject(Base):
    __tablename__ = "chat_projects"

    project_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="project")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("chat_projects.project_id", ondelete="SET NULL"))
    title: Mapped[str | None] = mapped_column(String(256))
    document_ids: Mapped[list] = mapped_column(JSON, default=list)
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project: Mapped["ChatProject | None"] = relationship(back_populates="sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.session_id", ondelete="CASCADE"))
    answer_id: Mapped[int | None] = mapped_column(BigInteger)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(32), default="pending")
    message: Mapped[str | None] = mapped_column(Text)
    missing_fields: Mapped[list | None] = mapped_column(JSON)
    conflicts: Mapped[list | None] = mapped_column(JSON)
    answer_items: Mapped[list | None] = mapped_column(JSON)
    model_used: Mapped[str | None] = mapped_column(String(64))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
    sources: Mapped[list["ChatSource"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    feedback: Mapped[list["ChatFeedback"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class ChatSource(Base):
    __tablename__ = "chat_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.message_id", ondelete="CASCADE"))
    chunk_id: Mapped[int | None] = mapped_column(BigInteger)
    fragment_id: Mapped[str | None] = mapped_column(String(64))
    document_id: Mapped[str] = mapped_column(String(64))
    document_title: Mapped[str | None] = mapped_column(String(256))
    section_id: Mapped[int | None] = mapped_column(BigInteger)
    page_number: Mapped[int | None] = mapped_column(Integer)
    clause: Mapped[str | None] = mapped_column(String(256))
    section_title: Mapped[str | None] = mapped_column(String(256))
    excerpt: Mapped[str | None] = mapped_column(String(512))
    text: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    page_preview_url: Mapped[str | None] = mapped_column(String(512))
    document_url: Mapped[str | None] = mapped_column(String(512))

    message: Mapped["ChatMessage"] = relationship(back_populates="sources")


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("chat_messages.message_id", ondelete="SET NULL"))
    answer_id: Mapped[int | None] = mapped_column(BigInteger)
    user_id: Mapped[str] = mapped_column(String(64))
    rating: Mapped[str | None] = mapped_column(String(16))  # positive | negative | neutral
    useful: Mapped[bool | None] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text)
    aspects: Mapped[list | None] = mapped_column(JSON)
    opened_citation_ids: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    message: Mapped["ChatMessage | None"] = relationship(back_populates="feedback")


class ChatExport(Base):
    __tablename__ = "chat_exports"

    export_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int | None] = mapped_column(BigInteger)
    format: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="completed")
    url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
