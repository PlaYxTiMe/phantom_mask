# Language native package
import logging
from typing_extensions import Annotated

# Third party package
from sqlalchemy import select
from jwt import ExpiredSignatureError, InvalidTokenError
from fastapi import Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

# Import from other folders
from core.auth import JWT, TokenType
from core.config import settings
from core.database import db_session
from app.v1.users.service import UserService
from app.v1.users.modules import Users
from app.v1.authtication.modules import Token


error_logger = logging.getLogger("errorLogger")


def authenticate_user(
    service: Annotated[UserService, Depends()],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Users:
    """
    Authenticate user using OAuth2 password flow.
    :param service: UserService instance.
    :param form_data: OAuth2PasswordRequestForm containing username and password.
    """
    return service.authenticate_user(form_data.username, form_data.password)


def authenticate_refresh_token(
    db: db_session,
    refresh_token: Annotated[str, Form(...)]
) -> Token:
    """
    Authenticate the refresh token.
    :param db: Database session.
    :param refresh_token: The refresh token to be validated.
    """
    # Define the exception to be raised if credentials are invalid
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        token_decode = JWT.decode_token(
            refresh_token,
            settings.JWT_REFRESH_SECRET_KEY
        )

        # Select the refresh token table from the database
        user_refresh_token_modules = db.scalar(
            select(Token).where(
                Token.user_id == token_decode.sub,
                Token.jti == token_decode.jti,
                Token.token_type == TokenType.REFRESH.value
            )
        )

        if not user_refresh_token_modules:
            raise credentials_exception
        return user_refresh_token_modules
    except ExpiredSignatureError as e:
        credentials_exception.detail = "Refresh Token has expired"
        raise credentials_exception from e
    except InvalidTokenError as e:
        credentials_exception.detail = "Could not validate credentials"
        raise credentials_exception from e
    except Exception as e:
        error_logger.error(f"Error in authenticate_refresh_token: {e}", exc_info=True)
        credentials_exception.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        credentials_exception.detail = "Error occurred while validating credentials, check error log."
        raise credentials_exception from e
