import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from .user import utc_now


if TYPE_CHECKING:
    from .task import Task
    from .user import User


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    task_id: str = Field(foreign_key="tasks.id", index=True)
    previous_status: str = Field(max_length=20)
    new_status: str = Field(max_length=20)
    timestamp: datetime = Field(
        default_factory=utc_now, sa_type=DateTime(timezone=True), index=True
    )

    user: "User" = Relationship(back_populates="audit_logs")
    task: "Task" = Relationship(back_populates="audit_logs")
