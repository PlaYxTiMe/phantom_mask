# Third party package
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary
from sqlalchemy.orm import relationship

# Import from other folders
from core.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    account = Column(String(20), unique=True, nullable=False)
    password = Column(LargeBinary, nullable=False)
    nickname = Column(String(50), unique=True)
    registration = Column(DateTime, nullable=False)
    registered_time = Column(DateTime, nullable=False)
    revoke = Column(Boolean, default=False)
    revoked_time = Column(DateTime, nullable=True)
    admin = Column(Boolean, default=False)

    registered_customers = relationship("Customers", foreign_keys="Customers.registered_by", back_populates="registered_user")
    revoked_customers = relationship("Customers", foreign_keys="Customers.revoked_by", back_populates="revoked_user")
    transactions = relationship("Transactions", foreign_keys="Transactions.by_user", back_populates="user")
    tokens = relationship("Token", foreign_keys="Token.user_id", back_populates="user")
