# Language native package
from typing_extensions import Annotated

# Third party package
from fastapi import APIRouter, Depends, Body

# Import from other folders
from core.error_response import default_error_responses
from app.v1.common.schemas import ResponseModel
from app.v1.customers.service import CustomerService
from app.v1.customers.schemas import (
    GetCustomersPayload,
    GetCustomersResponse,
    RegisterPayload,
    RegisterResponse
)


router = APIRouter()


@router.get(
    '/get_customers',
    response_model=ResponseModel[GetCustomersResponse],
    responses=default_error_responses()
)
def get_customers(
    service: Annotated[CustomerService, Depends()],
    query: Annotated[GetCustomersPayload, Depends()]
):
    """
    Retrieve a paginated list of customers based on filter conditions.
    """
    query_results = service.get_customers(
        **query.model_dump()
    )
    return ResponseModel(
        success=True,
        data=GetCustomersResponse(**query_results)
    )


@router.post(
    '/register',
    response_model=ResponseModel[RegisterResponse],
    responses=default_error_responses()
)
def register_customer(
    service: Annotated[CustomerService, Depends()],
    payload: Annotated[RegisterPayload, Body()]
):
    """
    Register a new customer.
    """
    add_results = service.create_customer(
        **payload.model_dump()
    )
    return ResponseModel(
        success=True,
        data=RegisterResponse(**add_results)
    )
