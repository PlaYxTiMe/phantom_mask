# Language native package
from typing import List, Dict
from typing_extensions import Annotated
from pydantic import TypeAdapter

# Third party package
from fastapi import APIRouter, Depends, Body

# Import from other folders
from core.error_response import default_error_responses
from app.v1.common.schemas import ResponseModel
from app.v1.customers.service import CustomerService
from app.v1.products.service import ProductService
from app.v1.transactions.service import TransactionService
from app.v1.transactions.schemas import (
    TopByTransactionsPayload,
    SummaryByTransactionsPayload,
    PurchasePayload,
    RechargePayload,
    TopByTransactionResponse,
    SummaryByTransactionsResponse,
    PurchaseResponse,
    RechargeResponse
)


router = APIRouter()


@router.get(
    '/top-by-transactions',
    response_model=ResponseModel[List[TopByTransactionResponse]],
    responses=default_error_responses()
)
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

    # Validate the response using TypeAdapter
    adapter = TypeAdapter(List[TopByTransactionResponse])
    data = adapter.validate_python(query_results)

    return ResponseModel(
        success=True,
        data=data
    )


@router.get(
    '/summary_by_transactions',
    response_model=ResponseModel[SummaryByTransactionsResponse],
    responses=default_error_responses()
)
async def get_summary_by_transactions(
    service: Annotated[TransactionService, Depends()],
    query: Annotated[SummaryByTransactionsPayload, Depends()]
):
    """
    Get the summary of transactions with time range.
    """
    query_results = service.calculate_product_summary_by_date_range(
        **query.model_dump()
    )
    return ResponseModel(
        success=True,
        data=SummaryByTransactionsResponse(**query_results)
    )


@router.post(
    '/purchase',
    response_model=ResponseModel[PurchaseResponse],
    responses=default_error_responses()
)
async def purchase(
    data: Annotated[PurchasePayload, Body()],
    service: Annotated[TransactionService, Depends()],
    customer_service: Annotated[CustomerService, Depends()],
    products_service: Annotated[ProductService, Depends()],
):
    """
    Endpoint to handle purchase transactions.
    """
    customer = customer_service.get_customer_module(
        customer_name=data.customer_name,
        customer_phone_number=data.customer_phone_number
    )
    product_detail = products_service.get_product_price(
        store_name=data.store_name,
        store_type=data.store_type,
        product_type=data.product_type,
        brand=data.brand,
        color=data.color,
        pack_size=data.pack_size
    )
    purchase_result = service.purchase(
        customer=customer,
        product_detail=product_detail,
        unit=data.unit,
        description=data.description
    )

    return ResponseModel(
        success=True,
        data=PurchaseResponse(**purchase_result)
    )


@router.post(
    '/recharge',
    response_model=ResponseModel[RechargeResponse],
    responses=default_error_responses()
)
async def recharge(
    data: Annotated[RechargePayload, Body()],
    service: Annotated[TransactionService, Depends()],
    customer_service: Annotated[CustomerService, Depends()]
):
    """
    Endpoint to handle recharge transactions.
    """
    customer = customer_service.get_customer_module(
        customer_name=data.customer_name,
        customer_phone_number=data.customer_phone_number
    )
    recharge_result = service.recharge(
        customer=customer,
        cashbalance=data.cashbalance,
        description=data.description
    )

    return ResponseModel(
        success=True,
        data=RechargeResponse(**recharge_result)
    )
