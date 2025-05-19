# Third party package
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_PATH = ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding='utf-8',
        extra='ignore',  # extra=forbid (default)
    )

    # Server debug mode
    DEBUG_MODE: bool = True

    # API version
    API_VERSION: str = "v1"

    # Database
    DB_URL: str = "sqlite:///sqlite.db"

    # JWT settings
    JWT_ACCESS_SECRET_KEY: str = "access_secret_key"
    JWT_REFRESH_SECRET_KEY: str = "refresh_secret_key"
    ALGORITHM: str = "HS256"

    # JWT expire time settings(minutes)
    JWT_ACCESS_EXPIRE: int = 30
    JWT_REFRESH_EXPIRE: int = 60 * 24 * 7

    # Default admin user
    ACCOUNT: str = "admin"
    PASSWORD: str = "admin"

settings = Settings()
