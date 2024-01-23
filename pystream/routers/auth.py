import time

import jwt
from fastapi import APIRouter, Request, Cookie, status
from fastapi.responses import RedirectResponse, JSONResponse

from pystream.logger import logger
from pystream.models import authenticator, config, squire

router = APIRouter()


@router.get("%s" % config.static.home_endpoint, response_model=None)
async def home_page(request: Request, session_token: str = Cookie(None)):
    squire.log_connection(request)
    await authenticator.verify_token(session_token)
    landing_page = squire.get_all_stream_content()
    return squire.templates.TemplateResponse(
        name=config.fileio.listing,
        context={"request": request, "home": config.static.home_endpoint, "logout": config.static.logout_endpoint,
                 "files": landing_page['files'], "directories": landing_page['directories']},
    )


@router.post("%s" % config.static.login_endpoint, response_model=None)
async def login(request: Request):
    squire.log_connection(request)
    authorization = request.headers.get('authorization')
    await authenticator.verify_login(authorization)
    # todo: instead of storing authorization to cookie
    #  create a db, assign a token to the user and set that token as cookie
    # Since JavaScript cannot handle RedirectResponse from FastAPI
    # Solution is to revert to Form, but that won't allow header auth and additional customization done by JavaScript
    response = JSONResponse(content={"redirect_url": config.static.home_endpoint}, status_code=status.HTTP_200_OK)
    encoded_jwt = jwt.encode(payload={"credentials": authorization, "timestamp": int(time.time())},
                             key=config.env.secret.get_secret_value(), algorithm="HS256")
    response.set_cookie("session_token", encoded_jwt, httponly=True)
    return response


@router.get("%s" % config.static.logout_endpoint, response_model=None)
async def logout(request: Request, session_token: str = Cookie(None)) -> RedirectResponse:
    if session_token:
        logger.info("%s logged out", request.client.host)
        if config.session.info.get(request.client.host):
            del config.session.info[request.client.host]
        else:
            logger.warning("Session information for %s was never stored or no video was played.", request.client.host)
        response = JSONResponse(content="Logged out successfully. Refresh the page to navigate to login.")
        response.delete_cookie("session_token")
    else:
        logger.info("Redirecting connection from %s to login page", request.client.host)
        response = RedirectResponse("/")  # redirect to root page for login
    return response
