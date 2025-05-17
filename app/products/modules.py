# Third party package
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

# Import from other folders
from core.database import Base


class Products(Base):
    """
    Model for products table.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_type = Column(String(50), index=True, nullable=False)
    brand = Column(String(50), index=True, nullable=False)
    color = Column(String(50), index=True, nullable=False)
    pack_size = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    stores = relationship("StoresProducts", foreign_keys="StoresProducts.product_id", back_populates="product", cascade="all, delete-orphan")
    transactions = relationship("Transactions", foreign_keys="Transactions.product_id", back_populates="product")
