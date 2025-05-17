# Language native package
from datetime import datetime
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """
    Token payload model for authentication.
    """
    iss: str = None
    sub: str = None
    aud: str = None
    exp: int = None
    nbf: int = None
    iat: int = None
    jti: str = None


class TokenResponse(BaseModel):
    """
    Token response model for authentication.
    """
    access_token: str
    access_token_expire_at: datetime
    refresh_token: str
    refresh_token_expire_at: datetime
    token_type: str


class TokenWithUserResponse(TokenResponse):
    """
    Create token response model for authentication.
    """
    account: str
    nickname: str
    is_admin: bool
