import os
import pathlib
from typing import Dict

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


def get_dir_content(parent: pathlib.PosixPath, subdir: str):
    """Get the video files inside a particular directory.

    Args:
        parent: Parent directory as displayed in the login page.
        subdir: Subdirectory within which video files exist.

    Yields:
        A dictionary of filename and the filepath as key-value pairs.
    """
    files = []
    sort_by = "len"
    for file in os.listdir(parent):
        if file.endswith(".mp4"):
            if file[0].isdigit():
                sort_by = "index"
            files.append({"name": file, "path": os.path.join(subdir, file)})
    if sort_by == "len":
        return sorted(files, key=lambda x: len(x['name']))
    return sorted(files, key=lambda x: x['name'])


def get_stream_content() -> Dict[str, list[str]]:
    """Get video files or folders that contain video files to be streamed.

    Yields:
        Path for video files or folders that contain the video files.
    """
    structure = {'files': [], 'directories': []}
    file_sort_by = "len"
    dir_sort_by = "len"
    for __path, __directory, __file in os.walk(config.env.video_source):
        if __path.endswith('__'):
            continue
        for file_ in __file:
            if file_.startswith('__'):
                continue
            if file_.endswith('.mp4'):
                if path := __path.replace(str(config.env.video_source), "").lstrip(os.path.sep):
                    if path[0].isdigit():
                        dir_sort_by = "index"
                    entry = {"name": path, "path": os.path.join(config.static.VAULT, path)}
                    if entry in structure['directories']:
                        continue
                    structure['directories'].append(entry)
                else:
                    if file_[0].isdigit():
                        file_sort_by = "index"
                    structure['files'].append({"name": file_, "path": os.path.join(config.static.VAULT, file_)})
    if file_sort_by == "len":
        structure['files'] = sorted(structure['files'], key=lambda x: len(x['name']))
    else:
        structure['files'] = sorted(structure['files'], key=lambda x: x['name'])
    if dir_sort_by == "len":
        structure['directories'] = sorted(structure['directories'], key=lambda x: len(x['name']))
    else:
        structure['directories'] = sorted(structure['directories'], key=lambda x: x['name'])
    return structure
