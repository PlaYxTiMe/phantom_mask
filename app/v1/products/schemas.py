# Language native package
from typing import Literal, Annotated, Optional, List
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
    page: int = Field(1, ge=1, description="The current page number, must be >= 1")
    per_page: int = Field(10, gt=0, description="The number of items to display per page, must be > 0")


class QueryProductsPayload(CommonPage):
    """
    Data model for querying products with optional filtering and activity status.

    Attributes:
        product_type (str): The type/category of the product to filter by.
        search_fields (Literal["", "brand", "color"]): Optional field to specify which product attribute to search.
            Can be empty string (no search), 'brand', or 'color'.
        fields_value (str): The search keyword/value to match against the selected search field.
        only_active (bool): If True, limits results to only active products and stores.
    """
    product_type: str = Field(..., description="The type/category of the product to filter by")
    search_fields: Annotated[
        Optional[Literal["brand", "color"]],
        Field(default=None, description="Optional search field, can be one of: 'brand', 'color'")
    ]
    fields_value: str = Field("", description="The value to match for the selected search field")
    only_active: bool = Field(True, description="If True, only returns active products & stores")


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
    product_type: str = Field(..., description="The type of product to filter by")
    price: float = Field(..., gt=0, description="The price value to compare against")
    condition: Literal["gt", "lt", "ge", "le", "eq"] = Field(..., description="Comparison operator")
    store_type: str = Field("", description="The store category to filter by")
    only_active: bool = Field(True, description="If True, only include active products and stores")


class StoreCommonResponse(BaseModel):
    store_name: str = Field(..., description="Name of the store")
    store_type: str = Field(..., description="Type of the store")
    is_active: bool = Field(..., description="Is the store active or not")


class ProductCommonResponse(BaseModel):
    product_type: str = Field(..., description="Type of the product")
    brand: str = Field(..., description="Brand of the product")
    color: str = Field(..., description="Color of the product")
    pack_size: int = Field(..., description="Size of the product pack")


class StoreWithPriceResponse(StoreCommonResponse):
    price: float = Field(..., description="Price of the product in the store")


class ProductResponse(ProductCommonResponse):
    stores: List[StoreWithPriceResponse] = Field(..., description="List of stores selling the product")


class ProductListResponse(BaseModel):
    products: List[ProductResponse] = Field(..., description="List of products with their details")
    total_pages: int = Field(..., description="Total number of pages available for the query")


class ProductWithPriceResponse(ProductCommonResponse):
    is_active: bool
    price: float


class StoreWithProductsResponse(StoreCommonResponse):
    products: List[ProductWithPriceResponse]
