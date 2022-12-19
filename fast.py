import logging
import mimetypes
import os
import warnings
from typing import Optional, BinaryIO, Tuple, Union, ByteString, AsyncIterable

from fastapi import Cookie, Depends, FastAPI, Header, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from uvicorn._logging import ColourizedFormatter  # noqa: PyProtectedMember

from models.config import env, fileio, settings
from models.settings import verify_auth

logger = logging.getLogger(name="uvicorn.default")

if not (content_type := mimetypes.guess_type(env.video_file, strict=True)[0]):
    warnings.warn(message=f"Unable to guess the media type for {env.video_file}. Using 'video/mp4' instead.")
    content_type = "video/mp4"

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


def send_bytes_range_requests(file_obj: BinaryIO,
                              start: int, end: int) -> AsyncIterable[Union[str, ByteString]]:
    """Send a file in chunks using Range Requests specification RFC7233.

    Args:
        file_obj: File data as bytes.
        start: Start of range.
        end: End of range.

    Yields:
        ByteString:
        Bytes as iterable.
    """
    with file_obj as stream:
        stream.seek(start)
        while (pos := stream.tell()) <= end:
            read_size = min(settings.CHUNK_SIZE, end + 1 - pos)
            yield stream.read(read_size)


def _get_range_header(range_header: str,
                      file_size: int) -> Tuple[int, int]:
    """Proces range header.

    Args:
        range_header: Range values from the headers.
        file_size: Size of the file.

    Returns:
        Tuple:
        Start and end of the video file.
    """
    _invalid_range = HTTPException(
        status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
        detail=f"Invalid request range (Range:{range_header!r})",
    )
    try:
        h = range_header.replace("bytes=", "").split("-")
        start = int(h[0]) if h[0] != "" else 0
        end = int(h[1]) if h[1] != "" else file_size - 1
    except ValueError:
        raise _invalid_range
    if start > end or start < 0 or end > file_size - 1:
        raise _invalid_range
    return start, end


def range_requests_response(range_header: str,
                            file_path: str) -> StreamingResponse:
    """Returns StreamingResponse using Range Requests of a given file.

    Args:
        range_header: Range values from the headers.
        file_path: Path of the file.

    Returns:
        StreamingResponse:
        Streaming response from fastapi.
    """
    file_size = os.stat(file_path).st_size
    headers = {
        "content-type": content_type,
        "accept-ranges": "bytes",
        "content-encoding": "identity",
        "content-length": file_size,
        "access-control-expose-headers": (
            "content-type, accept-ranges, content-length, "
            "content-range, content-encoding"
        ),
    }
    start = 0
    end = file_size - 1
    status_code = status.HTTP_200_OK

    if range_header is not None:
        start, end = _get_range_header(range_header=range_header, file_size=file_size)
        size = end - start + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start}-{end}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT

    return StreamingResponse(
        content=send_bytes_range_requests(open(file_path, mode="rb"), start, end),
        headers=headers,
        status_code=status_code,
    )


# noinspection PyShadowingBuiltins
@app.get("/video")
async def video_endpoint(request: Request, range: Optional[str] = Header(None),
                         session_token: Optional[str] = Cookie(None),
                         credentials: HTTPBasicCredentials = Depends(security)) -> Union[RedirectResponse,
                                                                                         StreamingResponse]:
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
    return range_requests_response(
        range_header=range, file_path=env.video_file
    )
