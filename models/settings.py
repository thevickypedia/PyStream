import logging
import secrets

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials

from models.config import env
from models.filters import RootFilter, VideoFilter

logging.getLogger("uvicorn.access").addFilter(VideoFilter())
logging.getLogger("uvicorn.access").addFilter(RootFilter())

logger = logging.getLogger(name="uvicorn.default")


async def verify_auth(credentials: HTTPBasicCredentials) -> JSONResponse:
    """Verifies authentication.

    Args:
        credentials: Credentials from client.

    Returns:
        JSONResponse:
        Returns JSON response with content and status code.
    """
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password is required to proceed.",
            headers=None
        )

    username_validation = secrets.compare_digest(credentials.username, env.username)
    password_validation = secrets.compare_digest(credentials.password, env.password)

    if username_validation and password_validation:
        return JSONResponse(
            content={
                "authenticated": True
            },
            status_code=200,
        )

    logger.error("Incorrect username or password")
    logger.error(credentials.dict())
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers=None
    )
