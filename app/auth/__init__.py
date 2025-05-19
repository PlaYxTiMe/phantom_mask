# Third party package
from fastapi.security import OAuth2PasswordBearer

# Import from other folders
from core.config import settings


# Token endpoint URL
TOKEN_URL = f'/api/{settings.API_VERSION}/auth/token'

# FastAPI helper to extract the "Authorization: Bearer <token>" header
# - Automatically reads the Bearer token from requests
# - Returns 401 if the header is missing
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=TOKEN_URL,
    description="""After issuing an Access Token through login, add the Authorization header when requesting the API.  
> Authorization: Bearer {Access Token}"""
)
