import base64
import secrets
import time

import jwt
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from pystream.logger import logger
from pystream.models import config


async def failed_auth_counter(request: Request) -> None:
    """Keeps track of failed login attempts from each host, and redirects if failed for 3 or more times.

    Args:
        request: Takes the ``Request`` object as an argument.
    """
    try:
        config.session.invalid[request.client.host] += 1
    except KeyError:
        config.session.invalid[request.client.host] = 1
    logger.info(config.session.invalid[request.client.host])
    if config.session.invalid[request.client.host] >= 3:
        raise config.RedirectException(location="/error")


async def verify_login(request: Request) -> JSONResponse:
    """Verifies authentication.

    Returns:
        JSONResponse:
        Returns JSON response with content and status code.
    """
    decoded_auth = base64.b64decode(request.headers.get("authorization", "")).decode("utf-8")
    auth = bytes(decoded_auth, "utf-8").decode(encoding="unicode_escape")
    username, password = auth.split(':')
    if not username or not password:
        await failed_auth_counter(request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password is required to proceed.",
            headers=None
        )

    username_validation = secrets.compare_digest(username, config.env.username)
    password_validation = secrets.compare_digest(password, config.env.password.get_secret_value())

    if username_validation and password_validation:
        config.session.invalid[request.client.host] = 0
        return JSONResponse(content={"authenticated": True}, status_code=200)

    logger.error("Incorrect username [%s] or password [%s]", username, password)
    await failed_auth_counter(request)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers=None
    )


async def verify_token(token: str) -> None:
    """Decodes the JWT and validates the session token and expiration.

    Args:
        token: JSON web token.

    Raises:
        RedirectException:
    """
    if not token:
        raise config.RedirectException(location="/error", detail="Invalid session token")
    try:
        decoded = config.WebToken(**jwt.decode(jwt=token, key=config.env.secret.get_secret_value(), algorithms="HS256"))
    except (jwt.InvalidSignatureError, ValidationError) as error:
        logger.error(error)
        raise config.RedirectException(location="/error", detail="Invalid session token")
    if not secrets.compare_digest(decoded.token, config.static.session_token):
        raise config.RedirectException(location="/error", detail="Invalid session token")
    if time.time() - decoded.timestamp > config.env.session_duration:
        raise config.RedirectException(location="/error", detail="Session expired")
