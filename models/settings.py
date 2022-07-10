import logging
import secrets

import jinja2
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials

from models.config import env, fileio
from models.filters import RootFilter, VideoFilter
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
