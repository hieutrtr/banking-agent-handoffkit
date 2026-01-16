"""Authentication models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from handoffkit.api.database import Base


class APIKey(Base):
    """API Key model for authentication."""

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
