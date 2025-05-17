# Third party package
from sqlalchemy import Column, Integer, Float, String, Boolean
from sqlalchemy.orm import relationship

# Import from other folders
from core.database import Base


class Stores(Base):
    """
    Model for stores table.
    """
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True, nullable=False)
    store_type = Column(String(50), index=True, nullable=False)
    cashbalance = Column(Float, nullable=False, default=0)
    is_active = Column(Boolean, default=True)

    products = relationship("StoresProducts", foreign_keys="StoresProducts.store_id", back_populates="store", cascade="all, delete-orphan")
    stores_opentime = relationship("StoresOpentime", foreign_keys="StoresOpentime.store_id", back_populates="store", cascade="all, delete-orphan")
    transactions = relationship("Transactions", foreign_keys="Transactions.store_id", back_populates="store")
