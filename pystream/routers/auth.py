import os
import pathlib

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from pystream.logger import logger
from pystream.models import authenticator, config, squire

router = APIRouter()
security = HTTPBasic(realm="simple")
templates = Jinja2Templates(directory=os.path.join(pathlib.Path(__file__).parent.parent, "templates"))


@router.get("/login", response_model=None)
async def login(request: Request,
                credentials: HTTPBasicCredentials = Depends(security)) -> templates.TemplateResponse:
    """Login request handler.

    Args:
        request: Request class.
        credentials: HTTPBasicCredentials for authentication.

    Returns:
        templates.TemplateResponse:
        Template response for listing page.
    """
    await authenticator.verify(credentials)
    squire.log_connection(request)
    content = squire.get_stream_content()
    return templates.TemplateResponse(
        name=config.fileio.list_files,
        context={"request": request, "files": content['files'], "directories": content['directories']}
    )


@router.get("/logout")
async def logout(request: Request):
    """Raises a 401 with no headers to log out the user.

    Raises:
        HTTPException:
        401 with a logout message.
    """
    if request.headers.get('authorization'):
        logger.info("%s logged out", request.client.host)
        if config.session.info.get(request.client.host):
            del config.session.info[request.client.host]
        else:
            logger.warning(f"Session information for {request.client.host} was never stored.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Logged out successfully. Refresh the page to navigate to login.",
            headers=None
        )
    else:
        logger.info("Redirecting connection from %s to login page", request.client.host)
        return RedirectResponse(url="/login", headers=None)
