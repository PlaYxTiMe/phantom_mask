# Language native package
from typing_extensions import Annotated

# Third party package
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

# Import from other folders
from core.config import settings


def get_connect_args(db_url: str) -> dict:
    """
    Get the connection arguments for the database engine.
    :param db_url: The database URL.
    :return: A dictionary of connection arguments.

    Other database settings can also be placed here (such as MySQL, PostgreSQL, etc.)
    """
    connect_args = {}
    if db_url.startswith("sqlite"):
        # SQLite specific settings
        connect_args = {
            "check_same_thread": False
        }
    return connect_args


# Database URL from settings
DATABASE_URL = settings.DB_URL

# The engine settings are used to configure the connection pool and other parameters
common_kwargs = {
    "poolclass": QueuePool,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30
}

# Create the synchronous engine
engine = create_engine(
    DATABASE_URL,
    connect_args=get_connect_args(DATABASE_URL),
    **common_kwargs
)

# Create a sessionmaker factory that will create new Session objects
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for the models to inherit from
Base = declarative_base()

# Dependency to provide the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency injection uses
db_session = Annotated[Session, Depends(get_db)]
