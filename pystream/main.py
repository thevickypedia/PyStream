import logging
import mimetypes
import os
import pathlib
import urllib.parse
from multiprocessing import Process
from typing import AsyncIterable, BinaryIO, ByteString, Optional, Tuple, Union

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from uvicorn.logging import ColourizedFormatter

from pystream.models import authenticator, config, ngrok, squire

logger = logging.getLogger(name="uvicorn.default")

app = FastAPI()

templates = Jinja2Templates(directory=os.path.join(pathlib.Path(__file__).parent, "templates"))

security = HTTPBasic(realm="simple")


def startup_tasks() -> None:
    """Tasks that need to run during the API startup."""
    if not os.listdir(config.env.video_source):
        raise FileNotFoundError(f"no files found in {config.env.video_source!r}")
    config.env.video_host = str(config.env.video_host)
    console_formatter = ColourizedFormatter(fmt="{levelprefix} [{module}:{lineno}] - {message}", style="{",
                                            use_colors=True)
    handler = logging.StreamHandler()
    handler.setFormatter(fmt=console_formatter)
    logger.addHandler(hdlr=handler)
    logger.info('Setting CORS policy.')
    origins = ["http://localhost.com", "https://localhost.com"]
    if config.env.website:
        origins.extend([
            f"http://{config.env.website.host}",
            f"https://{config.env.website.host}",
            f"http://{config.env.website.host}/*",
            f"https://{config.env.website.host}/*"
        ])
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


def log_connection(request: Request):
    """Logs the connection information.

    See Also:
        - Only logs the first connection from a device.
        - This avoids multiple logs when same device requests different videos.
    """
    if request.client.host not in config.session.info:
        config.session.info[request.client.host] = None
        logger.info(f"Connection received from {request.client.host} via {request.headers.get('host')}")
        logger.info(f"User agent: {request.headers.get('user-agent')}")


@app.get("/login", response_model=None)
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
    log_connection(request)
    return templates.TemplateResponse(
        name=config.fileio.list_files, context={"request": request, "files": list(squire.get_stream_files())}
    )


@app.get("/%s/{video_path:path}" % config.static.VAULT, response_model=None)
async def stream_video(request: Request,
                       video_path: str,
                       credentials: HTTPBasicCredentials = Depends(security)) -> templates.TemplateResponse:
    """Returns the template for streaming page.

    Args:
        request: Takes the ``Request`` class as an argument.
        video_path: Path of the video file that has to be rendered.
        credentials: HTTPBasicCredentials for authentication.

    Returns:
        templates.TemplateResponse:
        Template response for streaming page.
    """
    await authenticator.verify(credentials)
    log_connection(request)
    video_file = config.env.video_source / video_path
    if video_file.exists():
        return templates.TemplateResponse(
            name=config.fileio.index, headers=None,
            context={"request": request, "title": video_path,
                     "path": f"video?vid_name={urllib.parse.quote(str(video_file))}"}
        )
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video file {video_path!r} not found")


def send_bytes_range_requests(file_obj: BinaryIO,
                              start_range: int, end_range: int) -> AsyncIterable[Union[str, ByteString]]:
    """Send a file in chunks using Range Requests specification RFC7233.

    Args:
        file_obj: File data as bytes.
        start_range: Start of range.
        end_range: End of range.

    Yields:
        ByteString:
        Bytes as iterable.
    """
    with file_obj as streamer:
        streamer.seek(start_range)
        while (pos := streamer.tell()) <= end_range:
            read_size = min(config.static.CHUNK_SIZE, end_range + 1 - pos)
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
        start_range = int(h[0]) if h[0] != "" else 0
        end_range = int(h[1]) if h[1] != "" else file_size - 1
    except ValueError:
        raise _invalid_range
    if start_range > end_range or start_range < 0 or end_range > file_size - 1:
        raise _invalid_range
    return start_range, end_range


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
    start_range = 0
    end_range = file_size - 1
    status_code = status.HTTP_200_OK

    if range_header:
        start_range, end_range = _get_range_header(range_header=range_header, file_size=file_size)
        size = end_range - start_range + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start_range}-{end_range}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT

    return StreamingResponse(
        content=send_bytes_range_requests(open(file_path, mode="rb"), start_range, end_range),
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


# noinspection PyShadowingBuiltins
@app.get("/video", response_model=None)
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
    await authenticator.verify(credentials)
    log_connection(request)
    if not range or not range.startswith("bytes"):
        logger.info("/video endpoint accessed directly. Redirecting to login page.")
        return RedirectResponse(url="/login", headers=None)

    if config.session.info.get(request.client.host) != request.query_params['vid_name']:
        config.session.info[request.client.host] = request.query_params['vid_name']
        logger.info(f"Streaming: {request.query_params['vid_name']}")

    return range_requests_response(
        range_header=range, file_path=os.path.join(config.env.video_source, request.query_params['vid_name'])
    )


def start(**kwargs) -> None:
    """Starter function for the streaming API.

    Args:
        **kwargs: Keyword arguments to load the env config.
    """
    # todo: Implement websockets to set a counter clock and logout automatically after a set timeout
    config.env = config.EnvConfig(**kwargs)
    startup_tasks()
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(levelprefix)s [%(module)s:%(lineno)d] - %(message)s"
    # reload flag is set to false,
    #   1: reloading in the middle of streaming will make the process to wait for the connection to close
    #   2: connection will be open as long as the streaming stops (this is a circular dependency)
    argument_dict = {
        "app": f"{__name__}:app",
        "host": config.env.video_host,
        "port": config.env.video_port,
        "reload": False,
        "log_config": log_config,
        "workers": config.env.workers
    }
    if config.env.ngrok_token:
        Process(target=ngrok.run_tunnel, args=(logger,)).start()
    uvicorn.run(**argument_dict)
