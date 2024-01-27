import secrets
import time
from typing import Dict, List, NoReturn

from cryptography.fernet import InvalidSignature, InvalidToken
from fastapi import HTTPException, Request, status
from pydantic import ValidationError

from pystream.logger import logger
from pystream.models import config, secure, squire


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


async def extract_credentials(request: Request) -> List[str]:
    """Extract the credentials from ``Authorization`` headers and decode it before returning as a list of strings."""
    # decode the Base64-encoded ASCII string
    decoded_auth = await secure.base64_decode(request.headers.get("authorization", ""))
    # convert hex to a string
    auth = await secure.hex_decode(decoded_auth)
    return auth.split(',')


async def raise_error(request) -> NoReturn:
    """Raises a 401 Unauthorized error in case of bad credentials."""
    await failed_auth_counter(request)
    logger.error("Incorrect username or password: %d", config.session.invalid[request.client.host])
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers=None
    )


async def verify_login(request: Request) -> Dict[str, str]:
    """Verifies authentication and generates session token for each user.

    Returns:
        Dict[str, str]:
        Returns a dictionary with the payload required to create the session token.
    """
    username, signature, timestamp = await extract_credentials(request)
    if username not in config.env.users_allowed:
        await raise_error(request)
    for item in config.env.authorization:
        if password := item.get(username):
            break
    else:
        await raise_error(request)
    hex_user = await secure.hex_encode(username)
    hex_pass = await secure.hex_encode(password.get_secret_value())
    message = f"{hex_user}{hex_pass}{timestamp}"
    expected_signature = await secure.calculate_hash(message)
    if signature == expected_signature:
        config.session.invalid[request.client.host] = 0
        key = squire.keygen()
        # Store session token for each apikey
        config.session.mapping[username] = key
        return {"username": username, "token": key, "timestamp": int(time.time())}
    await raise_error(request)


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
    except (InvalidToken, InvalidSignature, ValidationError) as error:
        logger.error(type(error))
        raise config.RedirectException(location="/error", detail="Invalid session token")
    if not secrets.compare_digest(decoded.token, config.session.mapping.get(decoded.username, '')):
        raise config.RedirectException(location="/error", detail="Invalid session token")
    if time.time() - decoded.timestamp > config.env.session_duration:
        raise config.RedirectException(location="/error", detail="Session expired")
