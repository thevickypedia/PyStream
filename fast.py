import logging
import mimetypes
import os
import warnings
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from uvicorn._logging import ColourizedFormatter  # noqa: PyProtectedMember

from models.config import env, fileio, settings
from models.settings import verify_auth

logger = logging.getLogger(name="uvicorn.default")

if not os.path.isfile(env.video_file):
    raise FileNotFoundError(
        f"{env.video_file} does not exist."
    )
if not (media_type := mimetypes.guess_type(env.video_file, strict=True)[0]):
    warnings.warn(
        message=f"Unable to guess the media type for {env.video_file}. Using 'video/mp4' instead."
    )
    media_type = "video/mp4"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_TOKEN)
templates = Jinja2Templates(directory=fileio.templates)
security = HTTPBasic(realm="simple")


@app.on_event(event_type="startup")
async def custom_logger() -> None:
    """Disable existing logging propagation and override uvicorn access log using colorized log format."""
    logger.propagate = False  # Disable existing default logging and wrap a new one
    console_formatter = ColourizedFormatter(fmt="{levelprefix} [{module}:{lineno}] - {message}", style="{",
                                            use_colors=True)
    handler = logging.StreamHandler()
    handler.setFormatter(fmt=console_formatter)
    logger.addHandler(hdlr=handler)
    logger.info('Setting CORS policy.')


@app.on_event(event_type="startup")
async def enable_cors() -> None:
    """Allow ``CORS: Cross-Origin Resource Sharing`` to allow restricted resources on the API."""
    origins = [
        "http://localhost.com",
        "https://localhost.com",
        f"http://{env.website}",
        f"https://{env.website}",
        f"http://{env.website}/*",
        f"https://{env.website}/*",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex='https://.*\.ngrok\.io/*',  # noqa: W605
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get(path="/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse('favicon.ico')


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Reads the root request to render HTMl page.

    Returns:
        RedirectResponse:
        Redirects to login page.
    """
    return RedirectResponse(url="/login", headers=None)


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request,
                credentials: HTTPBasicCredentials = Depends(security),
                session_token: Optional[str] = Cookie(None)) -> templates.TemplateResponse:
    """Login request handler.

    Args:
        request: Request class.
        credentials: HTTPBasicCredentials for authentication.
        session_token: Token stored in cookies.

    Returns:
        templates.TemplateResponse:
        Template response.
    """
    await verify_auth(credentials=credentials)
    response = templates.TemplateResponse(fileio.name, context={"request": request}, headers=None)
    if not session_token:
        response.set_cookie(
            key="session_token",
            value=settings.SESSION_TOKEN,
            httponly=True
        )
    return response


# noinspection PyShadowingBuiltins
@app.get("/video")
async def video_endpoint(request: Request, range: Optional[str] = Header(None),
                         session_token: Optional[str] = Cookie(None),
                         credentials: HTTPBasicCredentials = Depends(security)) -> Response:
    """Opens the video file to stream the content.

    Args:
        request: Takes the ``Request`` class as an argument.
        range: Header information.
        credentials: HTTPBasicCredentials for authentication.
        session_token: Token stored in cookies.

    Returns:
        Response:
        Response class.
    """
    if session_token != settings.SESSION_TOKEN:
        await verify_auth(credentials=credentials)
    if not range or not range.startswith("bytes"):
        logger.info("/video endpoint accessed directly. Redirecting to login page.")
        return RedirectResponse(url="/login", headers=None)

    if request.client.host not in settings.HOSTS:
        settings.HOSTS.append(request.client.host)
        if host := request.headers.get('host'):
            logger.info(f"Connection received from {request.client.host} via {host}")
        if ua := request.headers.get('user-agent'):
            logger.info(f"User agent: {ua}")
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + settings.CHUNK_SIZE
    with open(env.video_file, "rb") as video:
        video.seek(start)
        if "chrome" in request.headers.get("sec-ch-ua", "NO_MATCH").lower():
            data = video.read()
        else:
            data = video.read(end - start)
        file_size = str(env.video_file.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{file_size}',
            'Accept-Ranges': 'bytes'
        }
        return Response(content=data, status_code=206, headers=headers, media_type=media_type)
