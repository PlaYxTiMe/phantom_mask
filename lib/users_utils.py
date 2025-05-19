# Language native package
import re

# Third party package
from fastapi import HTTPException, status


def validate_user_info(value: str, field:str) -> None:
    """
    Validate user input for account-related fields such as password, account name, or nickname.

    Args:
        value (str): The string value to validate.
        field (str): The name of the field being validated (e.g., "password", "account", "nickname").
    """

    if field.lower() == "password":
        pattern = r"^[A-Za-z0-9_#]+$"
        if not re.match(pattern, value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"{field} must be 6-8 characters long and can only contain letters, numbers, underscores and #"
            )
    else:
        pattern = r"^[A-Za-z0-9_]+$"

        if not re.match(pattern, value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"{field} must be 3-20 characters long and can only contain letters, numbers, and underscores."
            )
    