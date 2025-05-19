# Third party package
from typing import Dict
from fastapi import APIRouter

# Import from other folders
from core.schemas import ErrorResponse


def default_error_responses(
    status_codes: list[int] = [400, 401, 403, 404, 409, 422, 500]
) -> Dict[int, dict]:
    return {code: {"model": ErrorResponse} for code in status_codes}