import logging
import mimetypes
import os
import pathlib
import warnings

import jinja2
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from models.config import env
from models.filters import VideoFilter
from templates.template import CustomTemplate

logger = logging.getLogger(name="uvicorn.default")

video_path = pathlib.Path(os.path.join(os.getcwd(), "video.mp4"))
if not os.path.isfile(video_path):
    raise FileNotFoundError(
        f"{video_path} does not exist."
    )
media_type = mimetypes.guess_type(video_path, strict=True)[0]
if not media_type:
    warnings.warn(
        message=f"Unable to guess the media type for {video_path}. Using 'video/mp4' instead."
    )
    media_type = "video/mp4"

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.getcwd(), "templates"))

CHUNK_SIZE = 1024 * 1024
BROWSER = {}

logging.getLogger("uvicorn.access").addFilter(VideoFilter())
template = CustomTemplate.source.strip()
rendered = jinja2.Template(template).render(TITLE=env.video_title,
                                            VIDEO_HOST_URL=f"http://{env.video_host}:{env.video_port}/video")
with open(file=os.path.join(os.getcwd(), "templates", "index.html"), mode="w") as file:
    file.write(rendered)


@app.get(path="/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """Gets the favicon.ico and adds to the API endpoint.

    Returns:
        FileResponse:
        Uses FileResponse to send the favicon.ico to support the robinhood script's robinhood.html.
    """
    if os.path.isfile('favicon.ico'):
        return FileResponse('favicon.ico')


@app.get("/")
async def read_root(request: Request) -> templates.TemplateResponse:
    """Reads the root request to render HTMl page.

    Args:
        request: Request class.

    Returns:
        templates.TemplateResponse:
        Template response.
    """
    BROWSER["agent"] = request.headers.get("sec-ch-ua")
    return templates.TemplateResponse("index.html", context={"request": request})


# noinspection PyShadowingBuiltins
@app.get("/video")
async def video_endpoint(request: Request, range: str = Header(None)) -> Response:
    """Opens the video file to stream the content.

    Args:
        request: Takes the ``Request`` class as an argument.
        range: Header information.

    Returns:
        Response:
        Response class.
    """
    logger.info(f"Connection received from {request.client.host} via {request.headers.get('host')}")
    logger.info(f"User agent: {request.headers.get('user-agent')}")
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    with open(video_path, "rb") as video:
        video.seek(start)
        if BROWSER.get("agent") and "chrome" in BROWSER["agent"].lower():
            data = video.read()
        else:
            data = video.read(end - start)
        file_size = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{file_size}',
            'Accept-Ranges': 'bytes'
        }
        return Response(content=data, status_code=206, headers=headers, media_type=media_type)
