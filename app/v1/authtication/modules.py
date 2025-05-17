# Third party package
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

# Import from other folders
from core.database import Base


class Token(Base):
    """
    Model for tokens table.
    """
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    token_type = Column(String(20), nullable=False)
    token = Column(String, unique=True, nullable=False)
    issued_at = Column(Integer, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("Users", foreign_keys=[user_id], back_populates="tokens")
