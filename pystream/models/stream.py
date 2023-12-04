import mimetypes
import os
from typing import AsyncIterable, BinaryIO, ByteString, Tuple, Union

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from pystream.models import config


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


def get_range_header(range_header: str,
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
        start_range, end_range = get_range_header(range_header=range_header, file_size=file_size)
        size = end_range - start_range + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start_range}-{end_range}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT

    return StreamingResponse(
        content=send_bytes_range_requests(open(file_path, mode="rb"), start_range, end_range),
        headers=headers,
        status_code=status_code,
    )
