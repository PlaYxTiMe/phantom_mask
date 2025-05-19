# Language native package
from typing_extensions import Annotated
from datetime import datetime, timedelta, timezone

# Third party package
from fastapi import Depends, APIRouter

# Import from other folders
from core.auth import TokenType, JWT
from core.config import settings
from core.database import db_session
from core.error_response import default_error_responses
from lib.auth_utils import create_token_and_expiration, revoke_token
from app.v1.authtication import router
from app.v1.authtication.schemas import TokenResponse, TokenWithUserResponse
from app.v1.authtication.modules import Token
from app.v1.users.modules import Users
from app.v1.common.schemas import ResponseModel
from app.dependencies.auth import authenticate_user, authenticate_refresh_token
from app.dependencies.user import get_current_user


router = APIRouter()


@router.post(
    "/token",
    response_model=ResponseModel[TokenWithUserResponse],
    responses=default_error_responses()
)
async def token(
    db: db_session,
    user: Annotated[Users, Depends(authenticate_user)],
) -> TokenWithUserResponse:
    """
    Generate access and refresh tokens for the authenticated user.
    """
    access_token, access_token_expire_at = create_token_and_expiration(
        db, TokenType.ACCESS, user.id
    )
    refresh_token, refresh_token_expire_at = create_token_and_expiration(
        db, TokenType.REFRESH, user.id
    )

    return ResponseModel(
        success=True,
        data = TokenWithUserResponse(
            access_token=access_token,
            access_token_expire_at=access_token_expire_at,
            refresh_token=refresh_token,
            refresh_token_expire_at=refresh_token_expire_at,
            token_type=JWT.JWT_TYPE,
            account=user.account,
            nickname=user.nickname,
            is_admin=user.is_admin
        )
    )


@router.post(
    "/token/refresh",
    response_model=ResponseModel[TokenResponse],
    responses=default_error_responses()
)
async def token_refresh(
    db: db_session,
    refresh_token_modules: Annotated[Token, Depends(authenticate_refresh_token)]
) -> TokenResponse:
    """
    Refresh the access token using the refresh token.
    :param db: Database session.
    :param refresh_token_modules: The token db module.
    """
    now_time = datetime.now(timezone.utc)
    access_token, access_token_expire_at = create_token_and_expiration(
        db, TokenType.ACCESS, refresh_token_modules.user_id
    )

    # If the refresh token's expiration time is less than the access token's validity period in minutes, then update it.
    if refresh_token_modules.expires_at.replace(tzinfo=timezone.utc) - now_time < timedelta(minutes=settings.JWT_ACCESS_EXPIRE):
        refresh_token, refresh_token_expire_at = create_token_and_expiration(
            db, TokenType.REFRESH, refresh_token_modules.user_id
        )
    else:
        refresh_token = refresh_token_modules.token
        refresh_token_expire_at = refresh_token_modules.expires_at

    return ResponseModel(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            access_token_expire_at=access_token_expire_at,
            refresh_token=refresh_token,
            refresh_token_expire_at=refresh_token_expire_at,
            token_type=JWT.JWT_TYPE
        )
    )


@router.post("/token/revoke", response_model=ResponseModel[dict])
async def token_revoke(
    db: db_session,
    user: Annotated[Users, Depends(get_current_user)],
):
    """
    Revoke the access and refresh tokens for the authenticated user.
    """
    revoke_token(db, user.id)
    return ResponseModel(success=True, data={})
