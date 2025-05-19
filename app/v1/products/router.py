# Language native package
from typing import List
from pydantic import TypeAdapter
from typing_extensions import Annotated

# Third party package
from fastapi import APIRouter, Depends

# Import from other folders
from core.error_response import default_error_responses
from app.v1.products.service import ProductService
from app.v1.products.schemas import (
    PriceConditionPayload,
    QueryProductsPayload,
    ProductListResponse,
    StoreWithProductsResponse
)
from app.v1.common.schemas import ResponseModel


router = APIRouter()


@router.get('/get_products', response_model=ResponseModel[ProductListResponse], responses=default_error_responses())
async def get_products(
    service: Annotated[ProductService, Depends()],
    query: Annotated[QueryProductsPayload, Depends()]
):
    """
    Endpoint to retrieve products based on query parameters.
    """
    query_results = service.get_products(
        **query.model_dump()
    )
    return ResponseModel(
        success=True,
        data=ProductListResponse(**query_results)
    )


@router.get('/get_store_by_product_price', response_model=ResponseModel[List[StoreWithProductsResponse]], responses=default_error_responses())
async def get_store_by_product_price(
    service: Annotated[ProductService, Depends()],
    query: Annotated[PriceConditionPayload, Depends()]
):
    """
    Get store by product price condition.
    """
    query_results = service.get_store_product_by_price_condition(
        **query.model_dump()
    )
    adapter = TypeAdapter(List[StoreWithProductsResponse])
    data = adapter.validate_python(query_results)

    return ResponseModel(
        success=True,
        data=data
    )
