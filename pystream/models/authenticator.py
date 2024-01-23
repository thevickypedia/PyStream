import base64
import secrets
import time

import jwt
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from pystream.logger import logger
from pystream.models import config


async def verify_login(credentials) -> JSONResponse:
    """Verifies authentication.

    Returns:
        JSONResponse:
        Returns JSON response with content and status code.
    """
    decoded_auth = base64.b64decode(credentials).decode('utf-8')
    auth = bytes(decoded_auth, "utf-8").decode(encoding="unicode_escape")
    username, password = auth.split(':')
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password is required to proceed.",
            headers=None
        )

    username_validation = secrets.compare_digest(username, config.env.username)
    password_validation = secrets.compare_digest(password, config.env.password.get_secret_value())

    if username_validation and password_validation:
        return JSONResponse(
            content={
                "authenticated": True
            },
            status_code=200,
        )

    logger.error("Incorrect username [%s] or password [%s]", username, password)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers=None
    )


async def verify_timestamp(timestamp: int):
    # todo: include html files to specify this and redirect upon refresh or button click
    if time.time() - timestamp > config.env.session_duration:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has timed out")


async def verify_token(token: str):
    go_home = HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                            detail="Missing or invalid session token",
                            headers={"Location": "/"})  # redirect to root page for login
    if not token:
        raise go_home
    try:
        decoded = config.WebToken(**jwt.decode(jwt=token, key=config.env.secret.get_secret_value(), algorithms="HS256"))
    except jwt.InvalidSignatureError as error:
        logger.error(error)
        raise go_home
    await verify_login(decoded.credentials)
    await verify_timestamp(decoded.timestamp)
