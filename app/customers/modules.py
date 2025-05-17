# Third party package
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

# Import from other folders
from core.database import Base


class Customers(Base):
    """
    Model for customers table.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True, nullable=False)
    phone_number = Column(String(10), index=True, nullable=False)
    cashbalance = Column(Integer, nullable=False, default=0)
    registered_time = Column(DateTime, nullable=False)
    registered_by = Column(Integer, ForeignKey("users.id"))
    revoke = Column(Boolean, default=False)
    revoked_time = Column(DateTime, nullable=True, default=None)
    revoked_by = Column(Integer, ForeignKey("users.id"), nullable=True, default=None)

    registered_user = relationship("Users", foreign_keys=[registered_by], back_populates="registered_customers")
    revoked_user = relationship("Users", foreign_keys=[revoked_by], back_populates="revoked_customers")
    transactions = relationship("Transactions", foreign_keys="Transactions.customer_id", back_populates="customer")
