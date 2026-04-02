import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


if TYPE_CHECKING:
    from .audit_log import AuditLog
    from .refresh_token import RefreshToken
    from .task import Task


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(index=True, unique=True, max_length=320)
    hashed_password: str = Field(max_length=255)
    role: str = Field(default="member", index=True, max_length=20)

    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))

    tasks_assigned: List["Task"] = Relationship(back_populates="assigned_to")
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")
