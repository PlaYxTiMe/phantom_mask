# Language native package
from typing_extensions import Annotated

# Third party package
from fastapi import APIRouter, Depends

# Import from other folders
from core.error_response import default_error_responses
from app.v1.common.schemas import ResponseModel
from app.v1.stores.service import StoreService
from app.v1.stores.schemas import (
    QueryStorePayload,
    QueryStoreProductsPayload,
    GetStoresResponse,
    ProductByStoreResponse
)


router = APIRouter()


@router.get(
    '/get_stores',
    response_model=ResponseModel[GetStoresResponse],
    responses=default_error_responses()
)
async def get_stores(
    service: Annotated[StoreService, Depends()],
    query: Annotated[QueryStorePayload, Depends()]
):
    """
    Get stores based on the query parameters.
    """
    query_results = service.get_stores(
        **query.model_dump()
    )
    return ResponseModel(
        success=True,
        data=GetStoresResponse(**query_results)
    )


@router.get(
    '/products_by_store',
    response_model=ResponseModel[ProductByStoreResponse],
    responses=default_error_responses()
)
async def get_products_by_store(
    service: Annotated[StoreService, Depends()],
    query: Annotated[QueryStoreProductsPayload, Depends()]
):
    """
    Get products by store based on the query parameters.
    """
    query_results = service.get_store_products(
        **query.model_dump()
    )
    return ResponseModel(
        success=True,
        data=ProductByStoreResponse(**query_results)
    )
