# Language native package
from typing import Literal, Annotated
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
    page: int = 1
    per_page: int = 10


class QueryStorePayload(CommonPage):
    """
    Request payload for querying store data with optional filters and pagination.

    Inherits:
        CommonPage: Includes standard pagination fields (`page`, `per_page`).

    Attributes:
        store_type (str): Optional filter by store type. Defaults to an empty string.
        search_fields (Literal): Field to search on. Can be one of: "", "name", "datetime", or "day-of-week".
        fields_value (str): The value to match for the selected search field.
        only_active (bool): If True, only returns active stores. Defaults to True.

    Validators:
        - Ensures `fields_value` is provided if `search_fields` is set.
        - Validates `datetime` format if `search_fields` is "datetime".
        - Ensures valid weekday abbreviation if `search_fields` is "day-of-week".
    """
    store_type: str = ""
    search_fields: Annotated[Literal["", "name", "datetime", "day-of-week"], Field(default="")]
    fields_value: str = ""
    only_active: bool = True

    @model_validator(mode='after')
    def check_argument(self) -> 'QueryStorePayload':
        weekday_list = ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]
        if self.search_fields and not self.fields_value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot be null when searching")
        
        if self.search_fields == "datetime":
            try:
                datetime.strptime(self.fields_value, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Datetime format error, expected format is %Y-%m-%dT%H:%M:%SZ")
        elif self.search_fields == "day-of-week":
            if self.fields_value.lower() not in weekday_list:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please input correct abbreviation for weekday.")


class QueryStoreProductsPayload(CommonPage):
    """
    Request payload for querying products within a specific store, with filtering and pagination support.

    Inherits:
        CommonPage: Includes standard pagination fields (`page`, `per_page`).

    Attributes:
        store_name (str): Name of the store. Required.
        store_type (str): Type of the store (e.g., pharmacy). Required.
        product_type (str): Type of product to filter (e.g., mask). Required.
        search_fields (Literal): Optional search field. Can be one of: "", "brand", or "color".
        fields_value (str): The value to search for in the selected search field. Required if `search_fields` is set.
        only_active (bool): If True, only include active products. Defaults to True.
        reverse (bool): If True, reverse the default sorting order. Defaults to False.

    Validators:
        - Ensures `store_name`, `store_type`, and `product_type` are not empty.
        - Ensures `fields_value` is provided if `search_fields` is specified.
    """
    store_name: str
    store_type: str
    product_type: str
    search_fields: Annotated[Literal["", "brand", "color"], Field(default="")]
    fields_value: str = ""
    only_active: bool = True
    reverse: bool = False

    @model_validator(mode='after')
    def check_argument(self) -> 'QueryStoreProductsPayload':
        if not self.store_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store name cannot be empty")
        if not self.store_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store type cannot be empty")
        if not self.product_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product type cannot be empty")
        if self.search_fields and not self.fields_value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot be null when searching")
        return self
