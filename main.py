# Language native package
from contextlib import asynccontextmanager

# Third party package
from fastapi import FastAPI, Request

# Import from other folders
from app import modules
from app.v1 import router as api_router
from core.config import settings
from core.database import Base, engine
from core.exception import regist_core_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    This function is called when the application starts up and shuts down.
    """
    # Code to run on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Code to run on shutdown


app = FastAPI(
    debug=settings.DEBUG_MODE,
    lifespan=lifespan,
    title="Store Management API",
    description="API for managing stores, products, customers, and transactions.",
)


@app.middleware("http")
async def main_middleware(request: Request, call_next):
    """
    Middleware to handle requests and responses.
    """
    response = await call_next(request)
    return response


app.include_router(api_router)

regist_core_exception_handler(app)
