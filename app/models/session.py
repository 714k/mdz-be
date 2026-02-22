"""
Session model for tracking user sessions.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Session(Base):
    """User session tracking."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_jti = Column(String(255), unique=True, index=True, nullable=False)  # JWT ID
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    metadata = Column(JSON, default={})

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", backref="sessions")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id})>"
