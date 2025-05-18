# Language native package
from typing_extensions import Annotated

# Third party package
from fastapi import APIRouter, Depends, Body

# Import from other folders
from app.v1.users.service import UserService
from app.v1.users.schemas import (
    RegisterPayload, 
    RegisterResponse, 
    QueryUser, 
    UsersResponse, 
    RevokePayload, 
    UpdatePasswordByAdmin
)
from app.v1.common.schemas import ResponseModel
from app.dependencies.user import validate_create_data


router = APIRouter()


@router.post('/register', response_model=ResponseModel[RegisterResponse])
async def register_user(
    service: Annotated[UserService, Depends()],
    data: Annotated[RegisterPayload, Depends(validate_create_data)]
):
    """
    Register a new user.
    """
    user = service.create_user(data)
    return ResponseModel(
        success=True,
        data=RegisterResponse(
            account=user.account,
            nickname=user.nickname,
            is_admin=user.is_admin
        )
    )


@router.post('/unregister', response_model=ResponseModel[None])
async def unregister_user(
    service: Annotated[UserService, Depends()],
    data: Annotated[RevokePayload, Body()]
):
    """
    Unregister a user.
    """
    service.revoke_user(data.account)
    return ResponseModel(
        success=True,
        data=None
    )


@router.put('/update_password_by_admin', response_model=ResponseModel[str])
async def update_password(
    service: Annotated[UserService, Depends()],
    data: Annotated[UpdatePasswordByAdmin, Body()]
):
    """
    Update user password by admin, only admin can do this.
    It will not check the old password.
    """
    service.change_password(data.account, data.new_password)
    return ResponseModel(
        success=True,
        data="The update is complete."
    )


@router.get('/get_users', response_model=ResponseModel[list[UsersResponse]])
async def get_users(
    service: Annotated[UserService, Depends()],
    query: Annotated[QueryUser, Depends()]
):
    """
    Get all users or search.
    """
    if not query.account and not query.nickname:
        users = service.all_users()
    else:
        users = service.query_user(query.account, query.nickname)

    users_response = [
        UsersResponse(
            account=user.account,
            nickname=user.nickname,
            is_admin=user.is_admin,
            registered_time=user.registered_time,
            revoke=user.revoke,
            revoked_time=user.revoked_time
        ) for user in users
    ]

    return ResponseModel(
        success=True,
        data=users_response
    )
