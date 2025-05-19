# Language native package
import logging
from typing import List
from typing_extensions import Annotated
from datetime import datetime, timezone

# Third party package
from sqlalchemy import select, or_, delete
from fastapi import Request, HTTPException, status, Depends

# Import from other folders
from core.auth import TokenType
from core.service import BaseService
from core.database import db_session
from app.v1.users.modules import Users
from app.v1.users.schemas import RegisterPayload, UpdatePasswordPayload
from app.v1.authtication.modules import Token
from lib.auth_utils import verify_pass, hash_pass


error_logger = logging.getLogger("errorLogger")


class UserService(BaseService):
    """
    Service class for user-related operations.

    Attributes:
        request (Request): The current HTTP request object.
        db (db_session): Database session for performing database operations.
    """
    def __init__(self, request: Request, db: db_session):
        self.request = request
        self.db = db
    
    def raise_exception(self, status_code:int=400, detail:str=""):
        raise HTTPException(status_code=status_code, detail=detail)
    
    def authenticate_user(self, account: str, password: str) -> Users:
        """
        Authenticate a user by verifying their account and password.

        Args:
            account (str): The user's account identifier.
            password (str): The plaintext password to verify.

        Returns:
            Users: The authenticated user object.
        """
        user = self.fetch_user_by_account(account)
        if not user or not verify_pass(password, user.password):
            self.raise_exception(status_code=status.HTTP_403_FORBIDDEN, detail="ID or password is incorrect.")

        if user.revoke:
            self.raise_exception(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been revoked.")
        return user

    def fetch_user_by_id(self, user_id: int) -> Users:
        return self.db.scalar(select(Users).where(Users.id == user_id))

    def fetch_user_by_account(self, account: str) -> Users:
        return self.db.scalar(select(Users).where(Users.account == account))
    
    def fetch_user_by_nickname(self, nickname: str) -> Users:
        return self.db.scalar(select(Users).where(Users.nickname == nickname))

    def get_user(self, user_id: int) -> Users:
        """
        Retrieve a user by their unique ID, ensuring the user exists and is not revoked.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            Users: The user object corresponding to the given ID.
        """
        user = self.fetch_user_by_id(user_id)
        if not user:
            self.raise_exception(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        if user.revoke:
            self.raise_exception(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been revoked.")
        return user
    
    def create_user(self, user_payload: RegisterPayload) -> Users:
        """
        Create a new user record in the database using the provided registration data.

        Args:
            user_payload (RegisterPayload): Data required to register a new user.

        Returns:
            Users: The newly created user object.
        """
        try:
            user = Users(
                account=user_payload.account,
                password=user_payload.password,
                nickname=user_payload.nickname,
                registered_time=datetime.now(timezone.utc)
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        except Exception as e:
            self.db.rollback()
            error_logger.error(f"Error creating user: {e}", exc_info=True)
            self.raise_exception(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating user, check error log")
        return user
    
    def all_users(self) -> List[Users]:
        """
        Get all users models.
        """
        users = self.db.scalars(select(Users)).all()
        return users

    def query_user(self, account: str=None, nickname: str=None) -> List[Users]:
        """
        Query users from the database by optional account and/or nickname filters.

        Args:
            account (str, optional): Partial or full account name to filter users.
            nickname (str, optional): Partial or full nickname to filter users.

        Returns:
            List[Users]: A list of user objects matching the search criteria.
        """        
        query = self.db.query(Users)

        if account or nickname:
            filters = []
            if account:
                filters.append(Users.account.ilike(f"%{account}%"))
            if nickname:
                filters.append(Users.nickname.ilike(f"%{nickname}%"))
            
            query = query.filter(or_(*filters))
        users = query.all()
        
        return users

    def revoke_user(self, user_account: str) -> None:
        """
        Revoke a user account by setting its revoke status to True and recording the revoke timestamp.

        Args:
            user_account (str): The account identifier of the user to be revoked.
        """
        user = self.fetch_user_by_account(user_account)
        if not user:
            self.raise_exception(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if user.revoke:
            self.raise_exception(status_code=status.HTTP_409_CONFLICT, detail="User already revoked.")
        
        try:
            user.revoke = True
            user.revoked_time = datetime.now(timezone.utc)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            error_logger.error(f"Error revoking user: {e}", exc_info=True)
            self.raise_exception(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error revoking user, check error log.")
    
    def change_password(self, account: str, new_password: str) -> None:
        """
        Change the password for a specified user account, hash the new password, 
        and invalidate all existing access and refresh tokens for security.

        Args:
            account (str): The user account whose password will be changed.
            new_password (str): The new password to set for the user.
        """
        user = self.fetch_user_by_account(account)
        try:
            user.password = hash_pass(new_password)
            self.db.execute(
                delete(Token).where(
                    Token.user_id == user.id,
                    Token.token_type.in_([TokenType.ACCESS.value, TokenType.REFRESH.value])
                )
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            error_logger.error(f"Error change password: {e}", exc_info=True)
            self.raise_exception(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error changeing password, check error log.")


class ValidateUserService(BaseService):
    """
    Service class responsible for validating user-related operations.

    This class depends on UserService for user management functionalities and
    provides additional validation logic as needed.

    Attributes:
        request (Request): The current HTTP request object.
        db (db_session): The database session for performing queries.
        user_service (UserService): Dependency-injected service for user management.
    """
    def __init__(self, request: Request, db: db_session, user_service: Annotated[UserService, Depends()]) -> None:
        self.request = request
        self.db = db
        self.user_service = user_service
    
    def raise_exception(self, status_code: int, detail: str) -> None:
        raise HTTPException(status_code=status_code, detail=detail)
    
    def valid_account(self, user_account: int) -> None:
        """
        Validate whether the given user account already exists.

        Args:
            user_account (int): The account identifier to check.
        """
        user = self.user_service.fetch_user_by_account(user_account)
        if user:
            self.raise_exception(status_code=status.HTTP_409_CONFLICT, detail="Account already exists.")

    def valid_nickname(self, user_nickname: str) -> None:
        """
        Validate whether the given user nickname already exists.

        Args:
            user_nickname (str): The nickname to check.
        """
        user = self.user_service.fetch_user_by_nickname(user_nickname)
        if user:
            self.raise_exception(status_code=status.HTTP_409_CONFLICT, detail="Nickname already exists.")

    def valid_change_password(self, data:UpdatePasswordPayload) -> None:
        """
        Validate the conditions for changing a user's password.

        Args:
            data (UpdatePasswordPayload): Payload containing account, old password, and new password.
        """
        user = self.user_service.fetch_user_by_account(data.account)
        if not user:
            self.raise_exception(status_code=status.HTTP_403_FORBIDDEN, detail="User not found")
        if user.revoke:
            self.raise_exception(status_code=status.HTTP_409_CONFLICT, detail="This account has been revoked.")
        if not verify_pass(data.old_password, user.password):
            self.raise_exception(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is incorrect.")
