# Language native package
from typing import Literal, Annotated, Optional, List
from datetime import datetime
from pydantic import BaseModel, model_validator, Field

# Third party package
from fastapi import HTTPException, status


class CommonPage(BaseModel):
    """
    Pagination parameters used for common paginated API queries.

    Attributes:
        page (int): The current page number. Defaults to 1.
        per_page (int): The number of items to display per page. Defaults to 10.
    """
    page: int = Field(
        1, 
        ge=1, 
        description="The current page number, must be >= 1", 
        example=1
    )
    per_page: int = Field(
        10, 
        gt=0, 
        description="The number of items to display per page, must be > 0", 
        example=10
    )


class GetCustomersPayload(CommonPage):
    """
    Request payload for querying customer data with optional filters and pagination.

    Inherits:
        CommonPage: Includes standard pagination fields (`page`, `per_page`).

    Attributes:
        search_field (Literal): Field to search on. Can be one of: "", "name", "phone-number", or "datetime".
        search_value (str): The value to match for the selected search field.
        only_active (bool): If True, only returns active customers. Defaults to True.
    """
    search_field: Annotated[
        Optional[Literal["name", "phone_number"]],
        Field(
            default=None,
            description="Optional search field, can be one of: 'name', 'phone-number', 'datetime'",
            example="name"
        )
    ]
    search_value: str = Field("", description="The value to match for the selected search field")
    only_active: bool = Field(True, description="If True, only returns active customers", example=True)

    @model_validator(mode='after')
    def check_argument(self) -> 'GetCustomersPayload':
        if self.search_field and not self.search_value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot be null when searching")
        return self


class RegisterPayload(BaseModel):
    """
    """
    name: str = Field(
        ..., 
        min_length=3,
        max_length=50,
        pattern=r'^[A-Za-z ]+$',
        description="Customer's name(only English letters and spaces)",
        example="John Doe"
    )
    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r'^\d{10}$',
        description="Customer's phone number",
        example="0987654321"
    )


class CustomerResponse(BaseModel):
    name: str = Field(..., description="Customer's name")
    phone_number: str = Field(..., description="Customer's phone number")
    cashbalance: float = Field(..., description="Customer's current cash balance")
    registered_time: datetime = Field(..., description="Timestamp when customer was registered")
    registered_by: str = Field(..., description="User who registered the customer")
    revoke: bool = Field(..., description="Whether the customer is revoked")
    revoked_time: Optional[datetime] = Field(None, description="Timestamp of revocation (if revoked)")
    revoked_by: Optional[str] = Field(None, description="User who revoked the customer (if any)")


class GetCustomersResponse(BaseModel):
    customers: List[CustomerResponse] = Field(..., description="List of customers")
    total_pages: int = Field(..., description="Total number of pages for the query")


class RegisterResponse(CustomerResponse):
    pass