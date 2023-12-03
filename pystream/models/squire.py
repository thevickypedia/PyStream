import os
from collections.abc import Generator

from fastapi import Request

from pystream.logger import logger
from pystream.models import config


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


def get_stream_files() -> Generator[os.PathLike]:
    """Get files to be streamed.

    Yields:
        Path for video files.
    """
    for __path, __directory, __file in os.walk(config.env.video_source):
        if __path.endswith('__'):
            continue
        for file_ in __file:
            if file_.startswith('__'):
                continue
            if file_.endswith('.mp4'):
                path = __path.replace(str(config.env.video_source), "")
                if not path:
                    value = os.path.join(config.static.VAULT, file_)
                elif path.startswith("/"):
                    value = config.static.VAULT + path + os.path.sep + file_
                else:
                    value = config.static.VAULT + os.path.sep + path + os.path.sep + file_
                yield value
