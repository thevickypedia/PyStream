import os
from typing import Dict, Set

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


def get_stream_content() -> Dict[str, Set[str]]:
    """Get video files or folders that contain video files to be streamed.

    Yields:
        Path for video files or folders that contain the video files.
    """
    structure = {'files': set(), 'directories': set()}
    for __path, __directory, __file in os.walk(config.env.video_source):
        if __path.endswith('__'):
            continue
        for file_ in __file:
            if file_.startswith('__'):
                continue
            if file_.endswith('.mp4'):
                if path := __path.replace(str(config.env.video_source), ""):
                    structure['directories'].add(os.path.join(config.static.VAULT, path.lstrip(os.path.sep)))
                else:
                    structure['files'].add(os.path.join(config.static.VAULT, file_))
    return structure
