# Third party package
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_400_BAD_REQUEST


def regist_core_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Custom exception handler for HTTPException.
        """
        content = {"success": False, "message": exc.detail}
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )
    
    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Custom exception handler for RequestValidationError.
        """
        content = {
            "success":False,
            "message": "Missing or invalid parameter(s)"
        }
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content=content
        )
    
    @app.exception_handler(Exception)
    async def custom_exception_handler(request: Request, exc: Exception):
        """
        Custom exception handler for Exception.
        """
        content = {
            "success": False,
            "message": "Internal server error"
        }
        return JSONResponse(
            status_code=500,
            content=content
        )
