import html
import os
import pathlib
from typing import Optional, Union
from urllib import parse as urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasicCredentials

from pystream.logger import logger
from pystream.models import authenticator, config, squire, stream
from pystream.models.images import Images
from pystream.routers import auth

router = APIRouter()


@router.get("/%s/{img_path:path}" % config.static.preview, response_model=None)
async def preview_loader(request: Request, img_path: str,
                         credentials: HTTPBasicCredentials = Depends(auth.security)) -> FileResponse:
    """Returns the file for preview image.

    Args:
        request: Takes the ``Request`` class as an argument.
        img_path: Path of the image file that has to be rendered.
        credentials: HTTPBasicCredentials for authentication.

    Returns:
        FileResponse:
        FileResponse for preview image.
    """
    await authenticator.verify(credentials)
    squire.log_connection(request)
    img_path = html.unescape(img_path)
    if pathlib.PosixPath(img_path).exists():
        return FileResponse(img_path)
    logger.critical("'%s' not found", img_path)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{img_path!r} NOT FOUND")


@router.get("/%s/{video_path:path}" % config.static.vault, response_model=None)
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
    pure_path = config.env.video_source / video_path
    if pure_path.is_dir():
        # Use only the final dir in the path, since rest of it will be loaded in the login page itself
        # Not doing this will result in redundant path, like /home/GOT/season1/season1/episode1.mp4 resulting in 404
        child_dir = pathlib.Path(video_path).parts[-1]
        return auth.templates.TemplateResponse(
            name=config.fileio.list_files,
            context={
                "request": request,
                "dir_name": child_dir,  # For GOT/season1/episode1.mp4, this will just display 'season1' in landing page
                "files": squire.get_dir_stream_content(pure_path, child_dir),
                "logout": config.static.logout_endpoint
            }
        )
    if pure_path.exists():
        attrs = {
            "request": request, "title": video_path,
            "path": f"{config.static.streaming_endpoint}?{config.static.query_param}={urlparse.quote(str(pure_path))}",
        }
        # set default to avoid broken image sign in thumbnail
        preview_src = os.path.join(pathlib.PurePath(__file__).parent, "blank.jpg")
        if config.env.auto_thumbnail:
            # Uses preview file if exists at source, else tries to create one at video_source (reuses when refreshed)
            pys_preview = os.path.join(pure_path.parent, f"_{pure_path.name.replace('.mp4', '_pys_preview.jpg')}")
            if os.path.isfile(pys_preview) or Images(filepath=pure_path).generate_preview(pys_preview):
                preview_src = pys_preview
        attrs['preview'] = urlparse.quote(f"/{config.static.preview}/{preview_src}")
        return auth.templates.TemplateResponse(name=config.fileio.index, headers=None, context=attrs)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video file {video_path!r} not found")


# noinspection PyShadowingBuiltins
@router.get("%s" % config.static.streaming_endpoint, response_model=None, include_in_schema=False)
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
        return RedirectResponse(url=config.static.index_endpoint, headers=None)
    if not request.query_params.get(config.static.query_param):
        raise HTTPException(status_code=status.HTTP_421_MISDIRECTED_REQUEST,
                            detail="Misdirected request, please route through the login page.")
    # Check if the session is streaming the same video, if so - skip logging
    if config.session.info.get(request.client.host) != request.query_params[config.static.query_param]:
        config.session.info[request.client.host] = request.query_params[config.static.query_param]
        logger.info("Streaming: %s", request.query_params[config.static.query_param])
    return stream.range_requests_response(
        range_header=range,
        file_path=os.path.join(config.env.video_source, request.query_params[config.static.query_param])
    )
