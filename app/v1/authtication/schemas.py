# Language native package
from datetime import datetime
from pydantic import BaseModel, Field


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
    access_token: str = Field(..., description="Access token")
    access_token_expire_at: datetime = Field(..., description="Access token expiration time")
    refresh_token: str = Field(..., description="Refresh token")
    refresh_token_expire_at: datetime = Field(..., description="Refresh token expiration time")
    token_type: str = Field(..., description="Token type, usually 'Bearer'")


class TokenWithUserResponse(TokenResponse):
    """
    Create token response model for authentication.
    """
    account: str = Field(..., description="User account")
    nickname: str = Field(..., description="User nickname")
    is_admin: bool = Field(..., description="Is the user an admin")
