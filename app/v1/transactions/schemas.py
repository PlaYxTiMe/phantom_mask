# Language native package
from datetime import datetime
from pydantic import BaseModel, model_validator

# Third party package
from fastapi import HTTPException, status


class TopByTransactionsPayload(BaseModel):
    """
    Request payload for retrieving top customers by transaction amount.

    This model includes transaction filters such as type, product category, 
    date range, and ranking scope. It also performs validation to ensure the input 
    data is logically consistent.

    Attributes:
        transactions_type (str): The type of transaction (e.g., "purchase").
        product_type (str): The category of product (e.g., "mask").
        start_time (datetime): Start of the transaction date range.
        end_time (datetime): End of the transaction date range.
        rank_scope (int): Number of top results to return (default is 10).

    Validation:
        - All required fields must be non-empty.
        - `start_time` must be earlier than `end_time`.
        - `rank_scope` must be greater than 0.
    """
    transactions_type: str
    product_type: str
    start_time: datetime
    end_time: datetime
    rank_scope: int = 10

    @model_validator(mode='after')
    def check_argument(self) -> 'TopByTransactionsPayload':
        if not all([self.transactions_type, self.product_type, self.start_time, self.end_time]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arguments cannot be empty")
        
        if self.start_time >= self.end_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time must be before end time")
        if self.rank_scope <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rank scope must be greater than 0")

        return self
