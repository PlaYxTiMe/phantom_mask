# Third party package
from sqlalchemy import Column, Integer, Float, String, Time, ForeignKey
from sqlalchemy.orm import relationship

# Import from other folders
from core.database import Base


class Opentime(Base):
    __tablename__ = "opentime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_day = Column(String(10), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    stores_opentime = relationship(
        "StoresOpentime", 
        foreign_keys="StoresOpentime.opentime_id", 
        back_populates="opentime", 
        cascade="all, delete-orphan"
    )


class StoresProducts(Base):
    __tablename__ = "stores_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)

    store = relationship("Stores", foreign_keys=[store_id], back_populates="products")
    product = relationship("Products", foreign_keys=[product_id], back_populates="stores")


class StoresOpentime(Base):
    __tablename__ = "stores_opentime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    opentime_id = Column(Integer, ForeignKey("opentime.id"), nullable=False)

    store = relationship("Stores", foreign_keys=[store_id], back_populates="stores_opentime")
    opentime = relationship("Opentime", foreign_keys=[opentime_id], back_populates="stores_opentime")
