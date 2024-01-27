import os
import time

from fastapi import APIRouter, Cookie, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Template

from pystream.logger import logger
from pystream.models import authenticator, config, squire

router = APIRouter()


def get_expiry(lease_start: int, lease_duration: int) -> str:
    """Get expiry datetime as string using max age.

    Args:
        lease_start: Time when the authentication was made.
        lease_duration: Number of seconds until expiry.

    Returns:
        str:
        Returns the date and time of expiry in GMT.
    """
    end = time.gmtime(lease_start + lease_duration)
    return time.strftime('%a, %d-%b-%Y %T GMT', end)


@router.get("%s" % config.static.home_endpoint, response_model=None)
async def home_page(request: Request,
                    session_token: str = Cookie(None)) -> squire.templates.TemplateResponse:
    """Serves the home/index page for the UI.

    Args:
        request: Takes the ``Request`` object as an argument.
        session_token: Session token set after verifying username and password.

    Returns:
        TemplateResponse:
        Returns the listing page for video streaming.
    """
    squire.log_connection(request)
    await authenticator.verify_token(session_token)
    landing_page = squire.get_all_stream_content()
    return squire.templates.TemplateResponse(
        name=config.fileio.listing,
        context={"request": request, "home": config.static.home_endpoint, "logout": config.static.logout_endpoint,
                 "files": landing_page['files'], "directories": landing_page['directories']},
    )


@router.post("%s" % config.static.login_endpoint, response_model=None)
async def login(request: Request) -> JSONResponse:
    """Authenticates the user input and returns a redirect response with the session token set as a cookie.

    Args:
        request: Takes the ``Request`` object as an argument.

    Returns:
        JSONResponse:
        Returns the JSONResponse with content, status code and cookie.
    """
    squire.log_connection(request)
    auth_payload = await authenticator.verify_login(request)
    # AJAX calls follow redirect and return the response instead of replacing the URL
    # Solution is to revert to Form, but that won't allow header auth and additional customization done by JavaScript
    response = JSONResponse(content={"redirect_url": config.static.home_endpoint}, status_code=status.HTTP_200_OK)
    expiration = get_expiry(lease_start=auth_payload['timestamp'], lease_duration=config.env.session_duration)
    logger.info("Session for '%s' will be valid until %s", auth_payload['username'], expiration)
    response.set_cookie(key="session_token",
                        value=config.static.cipher_suite.encrypt(str(auth_payload).encode("utf-8")).decode(),
                        max_age=config.env.session_duration,
                        expires=expiration,
                        httponly=True)
    return response


@router.get("%s" % config.static.logout_endpoint, response_model=None)
async def logout(request: Request,
                 session_token: str = Cookie(None)) -> HTMLResponse:
    """Terminates the user's session by deleting the cookie and redirecting back to login page upon refresh.

    Args:
        request: Takes the ``Request`` object as an argument.
        session_token: Session token set after verifying username and password.

    Returns:
        HTMLResponse:
        HTML page for logout with content rendered based on current login status.
    """
    with open(os.path.join(config.template_storage, "logout.html")) as log_file:
        logout_template: Template = Template(log_file.read())
    if session_token:
        logger.info("%s logged out", request.client.host)
        if config.session.info.get(request.client.host):
            del config.session.info[request.client.host]
        else:
            logger.warning("Session information for %s was not stored or no video was played.", request.client.host)
        response = HTMLResponse(logout_template.render(
            detail="You have been logged out successfully.", show_login=False
        ))
        response.delete_cookie("session_token")
    else:
        logger.info("Redirecting connection from %s to login page", request.client.host)
        response = HTMLResponse(logout_template.render(
            detail="You are not logged in. Please click the button below to proceed.", show_login=True
        ))
    return response
