import pathlib
import logging
import mimetypes
from collections.abc import Generator
import os
from multiprocessing import Process
from typing import AsyncIterable, BinaryIO, ByteString, Optional, Tuple, Union

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (FileResponse, HTMLResponse, RedirectResponse,
                               StreamingResponse)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn._logging import ColourizedFormatter  # noqa: PyProtectedMember

from models.config import env, fileio, settings
from models.settings import verify_auth
from ngrok import run_tunnel

logger = logging.getLogger(name="uvicorn.default")

app = FastAPI()
app.mount(f"/{env.video_source}", StaticFiles(directory=env.video_source), name="Video Dump")

templates = Jinja2Templates(directory="templates")

security = HTTPBasic(realm="simple")


def get_stream_files() -> Generator[os.PathLike]:
    """Get files to be streamed.

    Yields:
        Path for video files.
    """
    for __path, __directory, __file in os.walk(env.video_source):
        if __path.endswith('__'):
            continue
        for file_ in __file:
            if file_.startswith('__'):
                continue
            filepath = pathlib.PurePath(file_)
            if filepath.suffix == '.mp4':
                path = __path.replace(str(env.video_source), "")
                yield os.path.join(settings.FAKE_DIR, path, filepath)


# source_path = list(get_stream_files())
source_path = [os.path.join(settings.FAKE_DIR, file) for file in os.listdir(env.video_source)
               if not file.startswith(".") and file.endswith(".mp4")]
source_path.sort(key=lambda a: a.lower())
last_log = {'log': ''}


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
    """Add CORSMiddleware to allow restricted resources on the API. Start reverse proxy in a dedicated process."""
    origins = [
        "http://localhost.com",
        "https://localhost.com"
    ]

    if env.website:
        origins.extend([
            f"http://{env.website}",
            f"https://{env.website}",
            f"http://{env.website}/*",
            f"https://{env.website}/*"
        ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex='https://.*\.ngrok\.io/*',  # noqa: W605
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if env.ngrok_token:
        Process(target=run_tunnel, args=(logger,)).start()


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
                credentials: HTTPBasicCredentials = Depends(security)) -> templates.TemplateResponse:
    """Login request handler.

    Args:
        request: Request class.
        credentials: HTTPBasicCredentials for authentication.

    Returns:
        templates.TemplateResponse:
        Template response for listing page.
    """
    await verify_auth(credentials=credentials)
    return templates.TemplateResponse(
        name=fileio.list_files, context={"request": request, "files": source_path}
    )


@app.get("/%s/{video_name}" % settings.FAKE_DIR)  # noqa: SFS101
async def stream(request: Request, video_name: str,
                 credentials: HTTPBasicCredentials = Depends(security)) -> templates.TemplateResponse:
    """Returns the template for streaming page.

    Args:
        request: Takes the ``Request`` class as an argument.
        video_name: Name of the video file that has to be rendered.
        credentials: HTTPBasicCredentials for authentication.

    Returns:
        templates.TemplateResponse:
        Template response for streaming page.
    """
    await verify_auth(credentials=credentials)
    return templates.TemplateResponse(name=fileio.name,
                                      context={
                                          "request": request, "title": video_name,
                                          "url": f"http://{env.video_host}:{env.video_port}/video?vid_name={video_name}"
                                      },
                                      headers=None)


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
    with file_obj as streamer:
        streamer.seek(start)
        while (pos := streamer.tell()) <= end:
            read_size = min(settings.CHUNK_SIZE, end + 1 - pos)
            yield streamer.read(read_size)


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


def range_requests_response(range_header: str, file_path: str) -> StreamingResponse:
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
        "content-type": mimetypes.guess_type(os.path.basename(file_path), strict=True)[0],
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


@app.get("/logout")
async def logout(request: Request):
    """Raises a 401 with no headers to log out the user.

    Raises:
        HTTPException:
        401 with a logout message.
    """
    logger.info("Logout successful")
    if request.headers.get('authorization'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Logged out successfully. Refresh the page to navigate to login.",
            headers=None
        )
    else:
        logger.info("Redirecting to login page")
        return RedirectResponse(url="/login", headers=None)


# noinspection PyShadowingBuiltins
@app.get("/video")
async def video_endpoint(request: Request, range: Optional[str] = Header(None),
                         credentials: HTTPBasicCredentials = Depends(security)) \
        -> Union[RedirectResponse, StreamingResponse]:
    """Streams the video file by sending bytes using StreamingResponse.

    Args:
        request: Takes the ``Request`` class as an argument.
        range: Header information.
        credentials: HTTPBasicCredentials for authentication.

    Returns:
        Union[RedirectResponse, StreamingResponse]:
        Streams the video name received as cookie.
    """
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
    if last_log['log'] != request.query_params['vid_name']:
        last_log['log'] = request.query_params['vid_name']
        logger.info(f"Streaming: {request.query_params['vid_name']}")
    return range_requests_response(
        range_header=range, file_path=os.path.join(env.video_source, request.query_params['vid_name'])
    )


if __name__ == '__main__':
    # TODO: Implement choosing videos within sub-folders
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(levelprefix)s [%(module)s:%(lineno)d] - %(message)s"
    argument_dict = {
        "app": f"{__name__}:app",
        "host": env.video_host,
        "port": env.video_port,
        "reload": True,
        "log_config": log_config,
        "workers": env.workers
    }
    uvicorn.run(**argument_dict)
