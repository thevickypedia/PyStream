import html
import os
import pathlib
from typing import Optional, Union
from urllib import parse as urlparse

from fastapi import APIRouter, Cookie, Header, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse

from pystream.logger import logger
from pystream.models import (authenticator, config, images, squire, stream,
                             subtitles)

router = APIRouter()


@router.get("/%s/{img_path:path}" % config.static.preview, response_model=None)
async def preview_loader(request: Request,
                         img_path: str,
                         session_token: str = Cookie(None)) -> FileResponse:
    """Returns the file for preview image.

    Args:
        request: Takes the ``Request`` object as an argument.
        img_path: Path of the image file that has to be rendered.
        session_token: Token setup for each session.

    Returns:
        FileResponse:
        FileResponse for preview image.
    """
    await authenticator.verify_token(session_token)
    squire.log_connection(request)
    img_path = pathlib.PosixPath(html.unescape(img_path))
    if img_path.exists():
        config.static.deletions.add(img_path)
        return FileResponse(img_path)
    logger.critical("'%s' not found", img_path)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{img_path!r} NOT FOUND")


@router.get("/%s/{track_path:path}" % config.static.track, response_model=None)
async def track_loader(request: Request,
                       track_path: str,
                       session_token: str = Cookie(None)) -> FileResponse:
    """Returns the file for subtitles.

    Args:
        request: Takes the ``Request`` object as an argument.
        track_path: Path of the subtitle track that has to be rendered.
        session_token: Token setup for each session.

    Returns:
        FileResponse:
        FileResponse for subtitle track.
    """
    await authenticator.verify_token(session_token)
    squire.log_connection(request)
    return FileResponse(html.unescape(track_path))


@router.get("/%s/{video_path:path}" % config.static.stream, response_model=None)
async def stream_video(request: Request,
                       video_path: str,
                       session_token: str = Cookie(None)) -> squire.templates.TemplateResponse:
    """Returns the template for streaming page.

    Args:
        request: Takes the ``Request`` object as an argument.
        video_path: Path of the video file that has to be rendered.
        session_token: Token setup for each session.

    Returns:
        templates.TemplateResponse:
        Returns the listing page for video streaming.
    """
    await authenticator.verify_token(session_token)
    squire.log_connection(request)
    pure_path = config.env.video_source / video_path
    if pure_path.is_dir():
        # Use only the final dir in the path, since rest of it will be loaded in the login page itself
        # Not doing this will result in redundant path, like /home/GOT/season1/season1/episode1.mp4 resulting in 404
        child_dir = pathlib.Path(video_path).parts[-1]
        return squire.templates.TemplateResponse(
            name=config.fileio.listing,
            context={
                "request": request,
                "dir_name": child_dir,  # For GOT/season1/episode1.mp4, this will just display 'season1' in landing page
                "files": squire.get_dir_stream_content(pure_path, child_dir),
                "home": config.static.home_endpoint,
                "logout": config.static.logout_endpoint
            }
        )
    if pure_path.exists():
        attrs = {
            "request": request, "video_title": video_path,
            "home": config.static.home_endpoint, "logout": config.static.logout_endpoint,
            "path": f"{config.static.streaming_endpoint}?{config.static.query_param}={urlparse.quote(str(pure_path))}"
        }
        prev_, next_ = squire.get_iter(pure_path)
        if prev_:
            attrs["previous"] = urlparse.quote(prev_)
            attrs["previous_title"] = prev_
        if next_:
            attrs["next"] = urlparse.quote(next_)
            attrs["next_title"] = next_
        # set default to avoid broken image sign in thumbnail
        preview_src = os.path.join(pathlib.PurePath(__file__).parent, "blank.jpg")
        if config.env.auto_thumbnail:
            # Uses preview file if exists at source, else tries to create one at video_source (reuses when refreshed)
            pys_preview = os.path.join(pure_path.parent,
                                       f"_{pure_path.name.replace(pure_path.suffix, '_pys_preview.jpg')}")
            if os.path.isfile(pys_preview) or images.Images(filepath=pure_path).generate_preview(pys_preview):
                preview_src = pys_preview
        attrs['preview'] = urlparse.quote(f"/{config.static.preview}/{preview_src}")
        sfx = pathlib.PosixPath(str(os.path.join(pure_path.parent, pure_path.name.replace(pure_path.suffix, ''))))
        vtt = sfx.with_suffix('.vtt')
        srt = sfx.with_suffix('.srt')
        if vtt.exists():
            attrs['track'] = urlparse.quote(f"/{config.static.track}/{vtt}")
        elif srt.exists():
            logger.info("Converting '%s.srt' to '%s.vtt' for subtitles", sfx.name, sfx.name)
            await subtitles.srt_to_vtt(srt)
            if vtt.exists():
                config.static.deletions.add(vtt)
                attrs['track'] = urlparse.quote(f"/{config.static.track}/{vtt}")
        return squire.templates.TemplateResponse(name=config.fileio.landing, headers=None, context=attrs)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video file {video_path!r} not found")


# noinspection PyShadowingBuiltins
@router.get("%s" % config.static.streaming_endpoint, response_model=None, include_in_schema=False)
async def video_endpoint(request: Request,
                         range: Optional[str] = Header(None),
                         session_token: str = Cookie(None)) -> Union[RedirectResponse, StreamingResponse]:
    """Streams the video file by sending bytes using StreamingResponse.

    Args:
        request: Takes the ``Request`` object as an argument.
        range: Header information.
        session_token: Token setup for each session.

    Returns:
        Union[RedirectResponse, StreamingResponse]:
        Streams the video name received as cookie.
    """
    await authenticator.verify_token(session_token)
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
