import pathlib

from fastapi import FastAPI, Request, Response, Header
from fastapi.templating import Jinja2Templates

video_path = pathlib.Path("video.mp4")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

CHUNK_SIZE = 1024 * 1024


@app.get("/")
async def read_root(request: Request) -> templates.TemplateResponse:
    """Reads the root request to render HTMl page.

    Args:
        request: Request class.

    Returns:
        templates.TemplateResponse:
        Template response.
    """
    return templates.TemplateResponse("index.htm", context={"request": request})


@app.get("/video")
async def video_endpoint(range: str = Header(None)) -> Response:
    """Opens the video file to stream the content.

    Args:
        range: Header information.

    Returns:
        Response:
        Response class.
    """
    start, end = range.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    with open(video_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
        file_size = str(video_path.stat().st_size)
        headers = {
            'Content-Range': f'bytes {str(start)}-{str(end)}/{file_size}',
            'Accept-Ranges': 'bytes'
        }
        return Response(content=data, status_code=206, headers=headers, media_type="video/mp4")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(reload=True, app=app)
