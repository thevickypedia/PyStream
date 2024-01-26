import base64
import secrets
import time
from typing import Dict

from cryptography.fernet import InvalidSignature, InvalidToken
from fastapi import HTTPException, Request, status
from pydantic import ValidationError

from pystream.logger import logger
from pystream.models import config, squire


async def failed_auth_counter(request: Request) -> None:
    """Keeps track of failed login attempts from each host, and redirects if failed for 3 or more times.

    Args:
        request: Takes the ``Request`` object as an argument.
    """
    try:
        config.session.invalid[request.client.host] += 1
    except KeyError:
        config.session.invalid[request.client.host] = 1
    if config.session.invalid[request.client.host] >= 3:
        raise config.RedirectException(location="/error")


async def verify_login(request: Request) -> Dict[str, str]:
    """Verifies authentication and generates session token for each user.

    Returns:
        Dict[str, str]:
        Returns a dictionary with the payload required to create the session token.
    """
    # todo: use signature authentication, encoded in JS and decoded in python
    decoded_auth = base64.b64decode(request.headers.get("authorization", "")).decode("utf-8")
    auth = bytes(decoded_auth, "utf-8").decode(encoding="unicode_escape")
    username, password = auth.split(':')
    if not all((username, password)):
        await failed_auth_counter(request)
        logger.error("Blank username [%s] or password [%s]: %d",
                     username, password, config.session.invalid[request.client.host])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username and password is required to proceed.",
            headers=None
        )

    username_validation = username in config.env.users_allowed
    password_validation = any(item.get(username) and
                              secrets.compare_digest(item[username].get_secret_value(), password)
                              for item in config.env.authorization)

    if username_validation and password_validation:
        config.session.invalid[request.client.host] = 0
        key = squire.keygen()
        # Store session token for each apikey
        config.session.mapping[username] = key
        return {"username": username, "token": key, "timestamp": int(time.time())}

    await failed_auth_counter(request)
    logger.error("Incorrect username [%s] or password [%s]: %d",
                 username, password, config.session.invalid[request.client.host])
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers=None
    )


async def verify_token(token: str) -> None:
    """Decrypts the symmetric encrypted token and validates the session token and expiration.

    Args:
        token: Symmetric encrypted key.
    """
    if not token:
        logger.warning("No session token was received")
        raise config.RedirectException(location="/error", detail="Invalid session token")
    try:
        decoded = config.WebToken(**eval(config.static.cipher_suite.decrypt(token).decode()))
    except (InvalidToken, InvalidSignature):
        logger.error("Invalid token or signature")
        raise config.RedirectException(location="/error", detail="Invalid session token")
    except ValidationError as error:
        logger.error(error)
        raise config.RedirectException(location="/error", detail="Invalid session token")
    if not secrets.compare_digest(decoded.token, config.session.mapping.get(decoded.username, '')):
        raise config.RedirectException(location="/error", detail="Invalid session token")
    if time.time() - decoded.timestamp > config.env.session_duration:
        raise config.RedirectException(location="/error", detail="Session expired")
