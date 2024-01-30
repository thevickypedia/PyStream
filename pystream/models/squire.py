import os
import pathlib
import re
from typing import Dict, List, Tuple, Union

from fastapi import Request
from fastapi.templating import Jinja2Templates

from pystream.logger import logger
from pystream.models import config

templates = Jinja2Templates(directory=config.template_storage)


def log_connection(request: Request) -> None:
    """Logs the connection information.

    See Also:
        - Only logs the first connection from a device.
        - This avoids multiple logs when same device requests different videos.
    """
    if request.client.host not in config.session.info:
        config.session.info[request.client.host] = None
        logger.info("Connection received from %s via %s", request.client.host, request.headers.get('host'))
        logger.info("User agent: %s", request.headers.get('user-agent'))


def natural_sort_key(filename: str) -> List[Union[int, str]]:
    """Key function for sorting filenames in a natural way.

    Args:
        filename: Takes the filename as an argument.

    Returns:
        List[Union[int, str]]:
        Returns a list of elements derived from splitting the filename into parts using a regular expression.
    """
    parts = re.split(r'(\d+)', filename)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def get_dir_stream_content(parent: pathlib.PosixPath, subdir: str) -> List[Dict[str, str]]:
    """Get the video files inside a particular directory.

    Args:
        parent: Parent directory as displayed in the login page.
        subdir: Subdirectory within which video files exist.

    Returns:
        List[Dict[str, str]]:
        A list of dictionaries with filename and the filepath as key-value pairs.
    """
    files = []
    for file_ in os.listdir(parent):
        if file_.startswith('_') or file_.startswith('.'):
            continue
        if pathlib.PurePath(file_).suffix in config.env.file_formats:
            files.append({"name": file_, "path": os.path.join(subdir, file_)})
    return sorted(files, key=lambda x: natural_sort_key(x['name']))


def get_all_stream_content() -> Dict[str, List[Dict[str, str]]]:
    """Get video files or folders that contain video files to be streamed.

    Returns:
        Dict[str, List[str]]:
        Dictionary of files and directories with name and path as key-value pairs on each section.
    """
    structure = {'files': [], 'directories': []}
    for __path, __directory, __file in os.walk(config.env.video_source):
        if __path.endswith('__'):
            continue
        for file_ in __file:
            if file_.startswith('_') or file_.startswith('.'):
                continue
            if pathlib.PurePath(file_).suffix in config.env.file_formats:
                if path := __path.replace(str(config.env.video_source), "").lstrip(os.path.sep):
                    entry = {"name": path, "path": os.path.join(config.static.stream, path)}
                    if entry in structure['directories']:
                        continue
                    structure['directories'].append(entry)
                else:
                    structure['files'].append({"name": file_, "path": os.path.join(config.static.stream, file_)})
    structure['files'] = sorted(structure['files'], key=lambda x: natural_sort_key(x['name']))
    structure['directories'] = sorted(structure['directories'], key=lambda x: natural_sort_key(x['name']))
    return structure


def get_iter(filename: pathlib.PurePath) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Sort video files at the currently served file's directory, and return the previous and next filenames.

    Args:
        filename: Path to the video file currently rendered.

    Returns:
        Tuple[str, str]:
        Tuple of previous file and next file.
    """
    # Extract only the file formats that are supported
    dir_content = sorted(
        (file for file in os.listdir(filename.parent) if pathlib.PosixPath(file).suffix in config.env.file_formats),
        key=lambda x: natural_sort_key(x)
    )
    idx = dir_content.index(filename.name)
    try:
        previous_ = dir_content[idx - 1]
    except IndexError:
        previous_ = None
    try:
        next_ = dir_content[idx + 1]
    except IndexError:
        next_ = None
    return previous_, next_


def remove_thumbnail(img_path: pathlib.PosixPath) -> None:
    """Triggered by timer to remove the thumbnail file.

    Args:
        img_path: PosixPath to the thumbnail image.
    """
    if img_path.exists():
        os.remove(img_path)
    else:
        logger.warning("%s was removed before hand." % img_path)
