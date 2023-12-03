import secrets

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials

from pystream.logger import logger
from pystream.models import config


async def verify(credentials: HTTPBasicCredentials) -> JSONResponse:
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

    username_validation = secrets.compare_digest(credentials.username, config.env.username)
    password_validation = secrets.compare_digest(credentials.password, config.env.password)

    if username_validation and password_validation:
        return JSONResponse(
            content={
                "authenticated": True
            },
            status_code=200,
        )

    logger.error("Incorrect username or password")
    logger.error(credentials.__dict__)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers=None
    )
