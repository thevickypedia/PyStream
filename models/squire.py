import os
import pathlib
from collections.abc import Generator

from models import config


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
            filepath = pathlib.PurePath(file_)
            if filepath.suffix == '.mp4':
                path = __path.replace(str(config.env.video_source), "")
                yield os.path.join(config.settings.FAKE_DIR, path, filepath)
