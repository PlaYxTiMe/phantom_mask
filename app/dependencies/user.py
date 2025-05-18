# Language native package
import logging
from typing_extensions import Annotated

# Third party package
from sqlalchemy import select
from fastapi import Depends, status, HTTPException

# Import from other folders
from core.auth import JWT, TokenType
from core.config import settings
from core.database import db_session
from app.auth import oauth2_scheme
from app.v1.users.service import UserService, ValidateUserService
from app.v1.users.schemas import RegisterPayload, UpdatePasswordPayload
from app.v1.users.modules import Users
from app.v1.authtication.schemas import TokenPayload
from app.v1.authtication.modules import Token


error_logger = logging.getLogger("errorLogger")


async def get_current_user(
    db: db_session,
    token: Annotated[str, Depends(oauth2_scheme)],
    service: Annotated[UserService, Depends()]
) -> Users:
    """
    Dependency to get the current user from the token.
    :param db: Database session.
    :param token: The token to be validated.
    :param service: UserService instance.
    """
    payload: TokenPayload = JWT.decode_token(
        token,
        settings.JWT_ACCESS_SECRET_KEY
    )

    token_exists = db.scalar(
        select(Token).where(
            Token.user_id == int(payload.sub),
            Token.jti == payload.jti,
            Token.token_type == TokenType.ACCESS.value
        )
    )
    user_id = int(payload.sub)
    if user_id is None or token_exists is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": JWT.JWT_TYPE}
        )
    user = service.get_user(user_id)
    if user.revoke:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been revoked",
            headers={"WWW-Authenticate": JWT.JWT_TYPE}
        )

    return user


async def check_admin(
    current_user: Annotated[Users, Depends(get_current_user)]
) -> None:
    """
    Dependency to check if the current user is an admin.
    :param db: Database session.
    :param current_user: The current user.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )


def validate_create_data(
    validate: Annotated[ValidateUserService, Depends()],
    data: RegisterPayload
) -> RegisterPayload:
    """
    Validate the user data for registration.
    :param validate: ValidateUserService instance.
    :param data: The user data to be validated.
    """
    validate.valid_account(data.account)
    validate.valid_nickname(data.nickname)

    return data


def validate_password_data(
    validate: Annotated[ValidateUserService, Depends()],
    data: UpdatePasswordPayload
) -> UpdatePasswordPayload:
    """
    Validate the password data for registration.
    :param validate: ValidateUserService instance.
    :param data: The user data to be validated.
    """
    validate.valid_change_password(data)

    return data
