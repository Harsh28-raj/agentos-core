from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _utcnow():
    # Stored as naive UTC to stay compatible with the existing TIMESTAMP WITHOUT TIME ZONE columns.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EpisodicLog(Base):
    __tablename__ = "episodic_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # User-scoped session key ("agentos_new:<user_id>_<thread_id>"), never a raw client value.
    thread_id = Column(String, index=True, nullable=False)
    run_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    reasoning_steps = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="started")
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    action_taken = Column(String, nullable=True)
    original_args = Column(JSON, nullable=True)
    modified_args = Column(JSON, nullable=True)
    human_feedback = Column(Text, nullable=True)


class UserToken(Base):
    __tablename__ = "user_tokens"
    __table_args__ = (UniqueConstraint("user_id", "service_name", name="uq_user_service"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    service_name = Column(String, nullable=False)  # e.g. 'google'
    encrypted_data = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
