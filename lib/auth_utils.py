# Language native package
import os
import hashlib
import binascii
import logging
from uuid import uuid4
from typing import Tuple
from datetime import datetime

# Third party package
from sqlalchemy import delete
from fastapi import HTTPException, status

# Import from other folders
from core.auth import TokenType, JWT
from core.database import db_session
from app.v1.authtication.modules import Token


error_logger = logging.getLogger("errorLogger")


def hash_pass(password:str) -> bytes:
    """
    Hash a password for storing.
    """
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)


def verify_pass(provided_password:str, stored_password:bytes) -> bool:
    """
    Verify a stored password against one provided by user
    :param provided_password: The password provided by the user.
    :param stored_password: The stored password to be verified against.
    """
    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac(
        'sha512',
        provided_password.encode('utf-8'),
        salt.encode('ascii'),
        100000
    )
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def create_token_and_expiration(db: db_session, token_type: TokenType, user_id: int) -> Tuple[str, datetime]:
    """
    Create a JWT token and its expiration time.
    :param token_type: The type of the token (access or refresh).
    :param user_id: The ID of the user for whom the token is created.
    :return: A tuple containing the generated JWT token and its expiration time.
    """
    data = {
        "sub": str(user_id),
        "jti": str(uuid4())
    }
    token, expires_at = JWT.create_token(db, token_type, data)
    return token, expires_at


def revoke_token(db: db_session, user_id: int) -> None:
    """
    Revoke a token for a user.
    :param db: Database session.
    :param user_id: The ID of the user whose token is to be revoked.
    """
    try:
        db.execute(
            delete(Token).where(
                Token.user_id == user_id,
                Token.token_type.in_([TokenType.ACCESS.value, TokenType.REFRESH.value])
            )
        )
        db.commit()
    except Exception as e:
        db.rollback()
        error_logger.error(f"Error revoking token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error revoking token, check error log",
            headers={"WWW-Authenticate": JWT.JWT_TYPE},
        )
