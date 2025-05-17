# Third party package
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

# Import from other folders
from core.database import Base


class Transactions(Base):
    """
    Model for transactions table.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transactions_type = Column(String(50), index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    unit = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False)
    transactions_date = Column(DateTime, nullable=False)
    description = Column(String(255), nullable=True)
    by_user = Column(Integer, ForeignKey("users.id"), nullable=False)

    customer = relationship("Customers", foreign_keys=[customer_id], back_populates="transactions")
    store = relationship("Stores", foreign_keys=[store_id], back_populates="transactions")
    product = relationship("Products", foreign_keys=[product_id], back_populates="transactions")
    user = relationship("Users", foreign_keys=[by_user], back_populates="transactions")
