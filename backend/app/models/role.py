"""Role database model."""
import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, UniversalJSON, TimestampMixin


class Role(Base, TimestampMixin):
    """System RBAC Role."""

    __tablename__ = "roles"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    permissions = Column(UniversalJSON, nullable=True, default=list)

    # Relationships
    users = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role name={self.name}>"
