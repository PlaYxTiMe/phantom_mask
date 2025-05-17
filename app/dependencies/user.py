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
from app.v1.users.service import UserService
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

    return user
