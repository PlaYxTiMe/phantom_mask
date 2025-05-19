# Language native package
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator, Field

# Third party package
from fastapi import HTTPException, status

# Import from other folders
from lib.users_utils import validate_user_info


class CommonAccount(BaseModel):
    """
    Data model representing a common user account input.

    Attributes:
        account (str): The user account identifier.

    Validation:
        Ensures the 'account' field is not empty and passes additional
        user info validation via `validate_user_info`.
    """
    account: str = Field(..., min_length=3, max_length=20, description="User account identifier")

    @model_validator(mode='after')
    def check_argument(self) -> 'CommonAccount':
        validate_user_info(self.account, "Account")
        return self


class CommonNickname(BaseModel):
    """
    Data model representing a common user nickname input.

    Attributes:
        nickname (str): The user nickname identifier.

    Validation:
        Ensures the 'nickname' field is not empty and passes additional
        user info validation via `validate_user_info`.
    """
    nickname: str = Field(..., min_length=3, max_length=20, description="User nickname identifier")

    @model_validator(mode='after')
    def check_argument(self) -> 'CommonNickname':
        validate_user_info(self.nickname, "Nickname")
        return self


class RegisterPayload(CommonAccount, CommonNickname):
    """
    Data model for user registration input.

    Inherits:
        - CommonAccount: Contains the 'account' field and validation.
        - CommonNickname: Contains the 'nickname' field and validation.

    Attributes:
        password (str): User's password.

    Validation:
        Ensures the 'password' field is not empty and passes additional
        user info validation via `validate_user_info`.
    """
    password: str = Field(..., min_length=6, max_length=8, description="User password")

    @model_validator(mode='after')
    def check_argument(self) -> 'RegisterPayload':
        validate_user_info(self.password, "Password")        
        return self


class QueryUser(BaseModel):
    """
    Data model for querying user information.

    Attributes:
        account (Optional[str]): Optional account identifier for querying.
        nickname (Optional[str]): Optional nickname for querying.

    Validation:
        If provided, validates 'account' and 'nickname' fields using
        the `validate_user_info` function.
    """
    account: Optional[str] = Field(None, min_length=3, max_length=20, description="User account identifier")
    nickname: Optional[str] = Field(None, min_length=3, max_length=20, description="User nickname identifier")

    @model_validator(mode='after')
    def check_argument(self) -> 'QueryUser':
        if self.account:
            validate_user_info(self.account, "Account")
        if self.nickname:
            validate_user_info(self.nickname, "Nickname")
        return self
    

class RevokePayload(CommonAccount):
    """
    Data model for revoking an account-related action.

    Inherits:
        CommonAccount: Includes the 'account' field and its validation.
    """


class UpdatePasswordPayload(CommonAccount):
    """
    Payload model for updating a user's password.

    Attributes:
        old_password (str): The current password of the user.
        new_password (str): The new password to replace the old one.

    Validation:
        - Ensures neither old_password nor new_password are empty.
        - Checks that the new password is different from the old password.
        - Applies user info validation on both passwords.
    """
    old_password: str = Field(..., min_length=6, max_length=8, description="Old password")
    new_password: str = Field(..., min_length=6, max_length=8, description="New password")

    @model_validator(mode='after')
    def check_argument(self) -> 'UpdatePasswordPayload':
        if self.old_password == self.new_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as old password")
        validate_user_info(self.old_password, "Password")
        validate_user_info(self.new_password, "Password")
        return self


class UpdatePasswordByAdmin(CommonAccount):
    """
    Payload model for an administrator to update a user's password.

    Attributes:
        new_password (str): The new password to set for the user.

    Validation:
        - Ensures the new password is not empty.
        - Applies user info validation on the new password.
    """
    new_password: str = Field(..., min_length=6, max_length=8, description="New password")

    @model_validator(mode='after')
    def check_argument(self) -> 'UpdatePasswordByAdmin':
        validate_user_info(self.new_password, "Password")
        return self


class RegisterResponse(BaseModel):
    """
    Register response model for user registration.
    """
    account: str = Field(..., description="User account identifier")
    nickname: str = Field(..., description="User nickname identifier")
    is_admin: bool = Field(..., description="Is the user an admin")


class UsersResponse(RegisterResponse):
    """
    Users response model for user information retrieval.
    """
    registered_time: datetime = Field(..., description="Time when the user registered")
    revoke: bool = Field(..., description="Is the user revoked")
    revoked_time: Optional[datetime] = Field(None, description="Time when the user was revoked")
