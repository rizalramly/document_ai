"""User and AuditLog models."""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, JSON, func
)
from app.database import Base


class UserRole(str, enum.Enum):
    ENGINEER = "engineer"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    email = Column(String(300), nullable=True, unique=True)
    role = Column(Enum(UserRole), default=UserRole.ENGINEER)
    created_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)  # e.g., "upload", "delete", "chat_query"
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    metadata_json = Column(JSON, nullable=True)
