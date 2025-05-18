# Language native package
from typing import Literal, Annotated
from pydantic import BaseModel, model_validator, Field

# Third party package
from fastapi import HTTPException, status


class PriceConditionPayload(BaseModel):
    """
    Payload schema for querying products by price conditions.

    Attributes:
        product_type (str): The type of product to filter (e.g., "mask").
        price (float): The price value to compare against.
        condition (Literal): The comparison operator. Accepts:
            - "gt" (greater than)
            - "lt" (less than)
            - "ge" (greater than or equal to)
            - "le" (less than or equal to)
            - "eq" (equal to)
        store_type (str): The store category to filter by (e.g., "pharmacy"). Defaults to an empty string (no filter).
        only_active (bool): If True, only include active products and stores. Defaults to True.

    Validation:
        Ensures the provided price is non-negative.
    """
    product_type: str
    price: float
    condition: Literal["gt", "lt", "ge", "le", "eq"]
    store_type: Annotated[Literal["", "pharmacy"], Field(default="")]
    only_active: bool = True

    @model_validator(mode='after')
    def check_argument(self) -> 'PriceConditionPayload':
        if self.price < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price cannot be negative")
        return self
