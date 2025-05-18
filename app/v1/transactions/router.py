# Language native package
from typing import List, Dict
from typing_extensions import Annotated

# Third party package
from fastapi import APIRouter, Depends

# Import from other folders
from app.v1.common.schemas import ResponseModel
from app.v1.transactions.service import TransactionService
from app.v1.transactions.schemas import TopByTransactionsPayload


router = APIRouter()


@router.get('/top-by-transactions', response_model=ResponseModel[List[Dict]])
async def get_top_by_transactions(
    service: Annotated[TransactionService, Depends()],
    query: Annotated[TopByTransactionsPayload, Depends()]
):
    """
    Get the top customers by total amount of transactions with time range.
    """
    query_results = service.top_by_transactions(
        **query.model_dump()
    )
    return ResponseModel(
        success=True,
        data=query_results
    )
