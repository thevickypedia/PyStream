import os

from fastapi import APIRouter, Cookie, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from jinja2 import Template

from pystream.models import config, squire

router = APIRouter()


@router.get(path="/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse('favicon.ico')


@router.get("/", include_in_schema=False)
async def root(request: Request) -> RedirectResponse:
    """Reads the root request to render HTMl page.

    Returns:
        RedirectResponse:
        Redirects to login page.
    """
    squire.log_connection(request)
    return squire.templates.TemplateResponse(
        name=config.fileio.index,
        context={"request": request, "signin": config.static.login_endpoint}
    )


@router.get(path="/error", include_in_schema=False)
async def error(detail: str = Cookie(None)) -> HTMLResponse:
    """Endpoint to serve broken pages as HTML response.

    Args:
        detail: Optional session related information.

    Returns:
        HTMLResponse:
        Rendered HTML response with deleted cookie.
    """
    with open(os.path.join(config.template_storage, "session.html")) as sess_file:
        session_template: Template = Template(sess_file.read())
    with open(os.path.join(config.template_storage, "unauthorized.html")) as auth_file:
        unauthorized_template: str = auth_file.read()
    if detail:
        response = HTMLResponse(session_template.render(reason=detail))
    else:
        response = HTMLResponse(unauthorized_template)
    response.delete_cookie("detail")
    return response
