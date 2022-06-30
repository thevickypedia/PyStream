import logging
import time

import jinja2
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials

from models.config import env, fileio, settings
from models.filters import VideoFilter, RootFilter
from templates.template import CustomTemplate

logging.getLogger("uvicorn.access").addFilter(VideoFilter())
logging.getLogger("uvicorn.access").addFilter(RootFilter())

logger = logging.getLogger(name="uvicorn.default")

rendered = jinja2.Template(source=CustomTemplate.source.strip()).render(
    TITLE=env.video_title,
    VIDEO_HOST_URL=f"http://{env.video_host}:{env.video_port}/video"
)
with open(file=fileio.html, mode="w") as file:
    file.write(rendered)


def reset_auth() -> bool:
    """Tells if the authentication header has to be reset and cache to be cleared.

    Returns:
        bool:
        True if it is the first login attempt, or it has been more than the set timeout since the first/previous expiry.
    """
    if settings.first_run:
        settings.first_run = False
        return True
    if time.time() - settings.session_time > env.auth_timeout:
        settings.session_time = int(time.time())
        return True


async def verify_auth(credentials: HTTPBasicCredentials) -> JSONResponse:
    """Verifies authentication.

    Args:
        credentials: Credentials from client.

    Returns:
        JSONResponse:
        Returns JSON response with content and status code.
    """
    if reset_auth():
        logger.warning("Resetting authentication headers.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password are required to proceed.",
            headers=None
        )

    if not credentials.username or not credentials.password:
        logger.warning("No credentials received in payload.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password are required to proceed.",
            headers=None
        )

    if credentials.username == env.username and credentials.password == env.password:
        logger.info("Authentication success.")
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
