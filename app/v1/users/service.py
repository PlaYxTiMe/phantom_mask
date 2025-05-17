# Language native package
import logging

# Third party package
from sqlalchemy import select
from fastapi import Request, HTTPException

# Import from other folders
from core.service import BaseService
from core.database import db_session
from app.v1.users.modules import Users
from lib.auth_utils import verify_pass


error_logger = logging.getLogger("errorLogger")


class UserService(BaseService):
    """
    UserService class for handling user-related operations.
    """
    def __init__(self, request: Request, db: db_session):
        self.request = request
        self.db = db
    
    def raise_exception(self, status_code: int = 400, detail: str = ""):
        raise HTTPException(status_code=status_code, detail=detail)
    
    def authenticate_user(self, account: str, password: str) -> Users:
        """
        Authenticate a user using their account and password.
        """
        user = self.fetch_user_by_account(account)
        if not user or not verify_pass(password, user.password):
            self.raise_exception(status_code=403, detail="ID or password is incorrect.")

        if user.revoke:
            self.raise_exception(status_code=403, detail="This account has been revoked.")
        return user

    def fetch_user_by_id(self, user_id: int) -> Users:
        return self.db.scalar(select(Users).where(Users.id == user_id))

    def fetch_user_by_account(self, account: str) -> Users:
        return self.db.scalar(select(Users).where(Users.account == account))

    def get_user(self, user_id: int) -> Users:
        """
        Query user by ID.
        """
        user = self.fetch_user_by_id(user_id)
        if not user:
            self.raise_exception(status_code=404, detail="User not found.")
        
        if user.revoke:
            self.raise_exception(status_code=403, detail="This account has been revoked.")
        return user
