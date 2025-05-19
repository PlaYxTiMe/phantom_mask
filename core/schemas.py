# Language native package
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Indicates if the request was successful")
    messages: str = Field("", description="Error message or details")
