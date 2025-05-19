# Language native package
from typing import List
from datetime import datetime
from pydantic import BaseModel, model_validator, Field

# Third party package
from fastapi import HTTPException, status


class CommonPayload(BaseModel):
    """
    Common request payload containing shared parameters for transaction queries.

    Attributes:
        transactions_type (str): Type of transaction, e.g. "purchase", "recharge", "refund".
        product_type (str): Product category, e.g. "mask".
        start_time (datetime): Start datetime of the query range.
        end_time (datetime): End datetime of the query range.
    """
    transactions_type: str = Field(..., min_length=1, description="Type of transaction, e.g. 'purchase', 'recharge', 'refund'")
    product_type: str = Field(..., min_length=1, description="Category of the product, e.g. 'mask'")
    start_time: datetime = Field(..., description="Start datetime of the query range")
    end_time: datetime = Field(..., description="End datetime of the query range")

    @model_validator(mode='after')
    def check_argument(self) -> 'CommonPayload':
        if self.start_time >= self.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Start time must be before end time"
            )
        return self


class TopByTransactionsPayload(CommonPayload):
    """
    Request payload for fetching top customers by transaction amount.

    Extends CommonPayload with:

    Attributes:
        rank_scope (int): Number of top records to return, must be > 0 (default 10).
    """
    rank_scope: int = Field(10, gt=0, description="Number of top records to return, must be > 0")


class SummaryByTransactionsPayload(CommonPayload):
    """
    Request payload for retrieving summary information of transactions.

    Inherits all parameters from CommonPayload.
    """


class CustomerCommonPayload(BaseModel):
    """
    Common payload schema for customer-related operations.

    Attributes:
        customer_name (str): Name of the customer. Only English letters allowed.
        customer_phone_number (str): Phone number of the customer. Only digits allowed.
        description (str, optional): Optional description of the transaction or request.
    """
    customer_name: str = Field(..., min_length=1, description="Name of the customer")
    customer_phone_number: str = Field(..., min_length=1, description="Phone number of the customer")
    description: str = Field(None, description="Description of the transaction")


class PurchasePayload(CustomerCommonPayload):
    """
    Represents the required payload to perform a product purchase transaction.

    Attributes:
        customer_name (str): Name of the customer making the purchase.
        customer_phone_number (str): Phone number of the customer.
        store_name (str): Name of the store from which the product is purchased.
        store_type (str): Type/category of the store (e.g., pharmacy, supermarket).
        product_type (str): Type/category of the product (e.g., mask, sanitizer).
        brand (str): Brand of the product.
        color (str): Color of the product.
        pack_size (int): Size of one product pack; must be greater than 0.
        unit (int): Number of units being purchased; must be greater than 0.
        description (str, optional): Optional text describing the transaction (e.g., notes or purpose).
    """
    store_name: str = Field(..., min_length=1, description="Name of the store")
    store_type: str = Field(..., min_length=1, description="Type of the store")
    product_type: str = Field(..., min_length=1, description="Type of the product")
    brand: str = Field(..., min_length=1, description="Brand of the product")
    color: str = Field(..., min_length=1, description="Color of the product")
    pack_size: int = Field(..., gt=0, description="Pack size of the product")
    unit: int = Field(..., gt=0, description="Unit of the product")


class RechargePayload(CustomerCommonPayload):
    """
    Payload schema for customer recharge requests.

    Inherits:
        CustomerCommonPayload: Includes customer name, phone number, and optional description.

    Attributes:
        cashbalance (float): The amount of money to recharge. Must be greater than 0.
    """
    cashbalance: float = Field(..., gt=0, description="Cash balance to recharge")


class TransactionRecordResponse(BaseModel):
    transaction_date: datetime = Field(..., description="Date and time of the transaction")
    product_type: str = Field(..., description="Type of the product")
    product_brand: str = Field(..., description="Brand of the product")
    product_color: str = Field(..., description="Color of the product")
    product_pack_size: int = Field(..., description="Pack size of the product")
    unit: int = Field(..., description="Number of units bought")
    amount: float = Field(..., description="Total amount for this transaction")


class TopByTransactionResponse(BaseModel):
    customer_name: str = Field(..., description="Name of the customer")
    customer_phone_number: str = Field(..., description="Customer's phone number")
    customer_cashbalance: float = Field(..., description="Customer's current cash balance")
    customer_registered_time: datetime = Field(..., description="Registration datetime of the customer")
    total_amount: float = Field(..., description="Total transaction amount by this customer")
    transaction_records: List[TransactionRecordResponse] = Field(..., description="List of customer's transactions")


class SummaryResponse(BaseModel):
    total_amount: float = Field(..., description="Total amount of all transactions")
    total_unit: int = Field(..., description="Total units of all transactions")


class TransactionRecordWithStoreResponse(TransactionRecordResponse):
    store_name: str = Field(..., description="Name of the store")
    store_type: str = Field(..., description="Type of the store")


class SummaryByTransactionsResponse(BaseModel):
    summary: SummaryResponse = Field(..., description="Summary of total amount and total unit")
    transaction_records: List[TransactionRecordWithStoreResponse] = Field(..., description="List of transaction records with store info")


class PurchaseResponse(BaseModel):
    customer_name: str = Field(..., description="Name of the customer")
    customer_cashbalance: float = Field(..., description="Customer's current cash balance")


class RechargeResponse(PurchaseResponse):
    pass
