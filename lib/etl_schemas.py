# Language native package
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class CommonData(BaseModel):
    """
    Common data model for ETL process.
    """
    name: str = Field(..., description="Name of the store or customer")
    cashBalance: float = Field(..., description="Cash balance of the store or customer")

    @model_validator(mode='after')
    def check_argument(self) -> 'CommonData':
        if not self.name:
            raise ValueError("Name cannot be empty")
        if self.cashBalance < 0:
            raise ValueError("Cash balance cannot be negative")
        return self


class ProductItem(BaseModel):
    """
    Product item model for ETL process.
    """
    name: str = Field(..., description="Name of the product")
    price: float = Field(..., description="Price of the product")

    @model_validator(mode='after')
    def check_argument(self) -> 'ProductItem':
        if not self.name:
            raise ValueError("Product name cannot be empty")
        if self.price < 0:
            raise ValueError("Product price cannot be negative")
        return self


class StoreData(CommonData):
    """
    Store data model for ETL process.
    """
    openingHours: str = Field(..., description="Opening hours of the store")
    masks: List[ProductItem] = Field(default_factory=list, description="List of products available in the store")


class PurchaseHistory(BaseModel):
    """
    Purchase history model for ETL process.
    """
    pharmacyName: str = Field(..., description="Name of the pharmacy")
    maskName: str = Field(..., description="Name of the mask")
    transactionAmount: float = Field(..., description="Transaction amount")
    transactionDate: str = Field(..., description="Transaction date in YYYY-MM-DD format")

    @model_validator(mode='after')
    def check_argument(self) -> 'PurchaseHistory':
        if not self.pharmacyName:
            raise ValueError("Pharmacy name cannot be empty")
        if not self.maskName:
            raise ValueError("Mask name cannot be empty")
        if self.transactionAmount < 0:
            raise ValueError("Transaction amount cannot be negative")
        try:
            datetime.strptime(self.transactionDate, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("Transaction date must be in YYYY-MM-DD HH:MM:SS format")
        return self


class CustomerData(CommonData):
    """
    Customer data model for ETL process.
    """
    purchaseHistories: List[PurchaseHistory] = Field(default_factory=list, description="List of purchase histories for the customer")
