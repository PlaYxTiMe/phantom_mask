# Language native package
import time
import logging
from enum import Enum
from typing import Tuple
from datetime import datetime, timezone, timedelta

# Third party package
from sqlalchemy import delete
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException, status

# Import from other folders
from core.config import settings
from core.database import db_session
from app.v1.authtication.schemas import TokenPayload
from app.v1.authtication.modules import Token


error_logger = logging.getLogger("errorLogger")


class TokenType(Enum):
    """
    Encapsulates token logic using an Enum class.
    """
    ACCESS = "access"
    REFRESH = "refresh"

    @property
    def secret_key(self):
        """
        Returns the corresponding secret key based on the token type.
        """
        if self == TokenType.REFRESH:
            return settings.JWT_REFRESH_SECRET_KEY
        return settings.JWT_ACCESS_SECRET_KEY

    @property
    def expires_minutes(self):
        """
        Returns the expiration time in minutes based on the token type.
        """
        if self == TokenType.REFRESH:
            return settings.JWT_REFRESH_EXPIRE
        return settings.JWT_ACCESS_EXPIRE


class JWT:
    """
    A class that handles JWT-related operations.
    """
    JWT_TYPE = "Bearer"

    @staticmethod
    def create_token(db: db_session, token_type: TokenType, data: dict) -> Tuple[str, datetime]:
        """
        Create a JWT token.
        :param db: Database session.
        :param token_type: The type of the token (access or refresh).
        :param data: The data to include in the token.
        :return: The generated JWT token and its expiration time.
        """
        # From the token type, get the secret key and expiration time
        secret_key = token_type.secret_key
        expires_minutes = token_type.expires_minutes
        
        to_encode = data.copy()
        iat = int(time.time())
        exp = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        to_encode.update({"iat": iat, "exp": exp})
        token_encode = encode(to_encode, secret_key, algorithm=settings.ALGORITHM)

        try:
            db.execute(
                delete(Token).where(
                    Token.user_id == to_encode.get("sub"),
                    Token.token_type == token_type.value
                )
            )
            db_token = Token(
                jti=to_encode.get("jti"),
                user_id=to_encode.get("sub"),
                token_type=token_type.value,
                token=token_encode,
                issued_at=iat,
                expires_at=exp
            )
            db.add(db_token)
            db.commit()
            db.refresh(db_token)
        except Exception as e:
            db.rollback()
            error_logger.error(f"Failed to create token in database: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create token in database, check error log",
                headers={"WWW-Authenticate": JWT.JWT_TYPE},
            ) from e
        return token_encode, exp
    
    @staticmethod
    def decode_token(token: str, secret_key: str) -> TokenPayload:
        """
        Decode a JWT token.
        :param token: The JWT token to decode.
        :param secret_key: The secret key used to decode the token.
        :return: The decoded data from the token.
        """
        # Define the exception to be raised if credentials are invalid
        http_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="",
            headers={"WWW-Authenticate": JWT.JWT_TYPE},
        )
    
        try:
            # Calculate the time difference between local time and UTC.
            now_time = datetime.now()
            utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
            diff_time = utc_now - now_time
            leeway = diff_time.total_seconds()

            payload = decode(
                token,
                secret_key,
                algorithms=[settings.ALGORITHM],
                options={"leeway": leeway},
            )
            return TokenPayload(**payload)
        except ExpiredSignatureError as e:
            http_exception.detail = "Token has expired"
            raise http_exception from e
        except InvalidTokenError as e:
            http_exception.detail = "Could not validate credentials"
            raise http_exception from e
        except Exception as e:
            error_logger.error(f"Error in decode_token: {e}", exc_info=True)
            http_exception.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            http_exception.detail = "Error occurred while validating credentials, check error log."
            raise http_exception from e
