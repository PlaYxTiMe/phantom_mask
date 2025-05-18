# Language native package
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional


T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    """
    Unified response format.
    """
    success: bool
    data: Optional[T] = None
