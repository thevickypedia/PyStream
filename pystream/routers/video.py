import os
import pathlib
import urllib.parse
from typing import Optional, Union

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasicCredentials

from pystream.logger import logger
from pystream.models import authenticator, config, squire, stream
from pystream.routers import auth

router = APIRouter()


@router.get("/%s/{video_path:path}" % config.static.VAULT, response_model=None)
async def stream_video(request: Request,
                       video_path: str,
                       credentials: HTTPBasicCredentials = Depends(auth.security)) -> auth.templates.TemplateResponse:
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
    squire.log_connection(request)
    video_file = config.env.video_source / video_path
    if video_file.is_dir():
        return auth.templates.TemplateResponse(
            name=config.fileio.list_files,
            context={
                "request": request,
                "files": [os.path.join(pathlib.Path(video_path).parts[-1], file)  # Use only the final dir in a path
                          for file in os.listdir(video_file) if file.endswith(".mp4")]
            }
        )
    if video_file.exists():
        return auth.templates.TemplateResponse(
            name=config.fileio.index, headers=None,
            context={"request": request, "title": video_path,
                     "path": f"video?vid_name={urllib.parse.quote(str(video_file))}"}
        )
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video file {video_path!r} not found")


# noinspection PyShadowingBuiltins
@router.get("/video", response_model=None)
async def video_endpoint(request: Request, range: Optional[str] = Header(None),
                         credentials: HTTPBasicCredentials = Depends(auth.security)) \
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
    squire.log_connection(request)
    if not range or not range.startswith("bytes"):
        logger.info("/video endpoint accessed directly. Redirecting to login page.")
        return RedirectResponse(url="/login", headers=None)

    if config.session.info.get(request.client.host) != request.query_params['vid_name']:
        config.session.info[request.client.host] = request.query_params['vid_name']
        logger.info(f"Streaming: {request.query_params['vid_name']}")

    return stream.range_requests_response(
        range_header=range, file_path=os.path.join(config.env.video_source, request.query_params['vid_name'])
    )
