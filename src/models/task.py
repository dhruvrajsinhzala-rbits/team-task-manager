from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Text
from sqlmodel import Field, Relationship, SQLModel

from .user import utc_now


if TYPE_CHECKING:
    from .audit_log import AuditLog
    from .user import User


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, sa_type=Text)
    status: str = Field(default="pending", index=True, max_length=20)

    assigned_to_id: str | None = Field(default=None, foreign_key="users.id", index=True)
    due_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))

    assigned_to: "User" | None = Relationship(back_populates="tasks_assigned")
    audit_logs: list["AuditLog"] = Relationship(back_populates="task")
