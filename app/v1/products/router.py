# Language native package
from typing import List, Dict
from typing_extensions import Annotated

# Third party package
from fastapi import APIRouter, Depends

# Import from other folders
from app.v1.products.service import ProductService
from app.v1.products.schemas import PriceConditionPayload
from app.v1.common.schemas import ResponseModel


router = APIRouter()


@router.get('/get_store_by_product_price', response_model=ResponseModel[List[Dict]])
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
    return ResponseModel(
        success=True,
        data=query_results
    )