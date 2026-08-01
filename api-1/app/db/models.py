from datetime import datetime
import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class EpisodicLog(Base):
    __tablename__ = "episodic_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    thread_id = Column(String, index=True, nullable=False)
    run_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    reasoning_steps = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="started")
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    action_taken = Column(String, nullable=True)
    original_args = Column(JSON, nullable=True)
    modified_args = Column(JSON, nullable=True)
    human_feedback = Column(Text, nullable=True)

class UserToken(Base):
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    service_name = Column(String, nullable=False) # e.g., 'google'
    encrypted_data = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
