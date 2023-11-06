import os
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
            if file_.endswith('.mp4'):
                path = __path.replace(str(config.env.video_source), "")
                if not path:
                    value = os.path.join(config.settings.FAKE_DIR, file_)
                elif path.startswith("/"):
                    value = config.settings.FAKE_DIR + path + os.path.sep + file_
                else:
                    value = config.settings.FAKE_DIR + os.path.sep + path + os.path.sep + file_
                yield value


def get_stream_files_as_dict() -> dict:
    """Get files to be streamed.

    Yields:
        Path for video files.
    """
    final_dict = {}
    for __path, __directory, __file in os.walk(config.env.video_source):
        if __path.endswith('__'):
            continue
        for file_ in __file:
            if file_.startswith('__'):
                continue
            if file_.endswith('.mp4'):
                path = __path.replace(str(config.env.video_source), "")
                if not path:
                    final_dict[os.path.join(config.settings.FAKE_DIR, file_)] = (
                        os.path.join(config.env.video_source, file_))
                elif path.startswith("/"):
                    final_dict[config.settings.FAKE_DIR + path + os.path.sep + file_] = (
                            str(config.env.video_source) + path + os.path.sep + file_)
                else:
                    final_dict[config.settings.FAKE_DIR + os.path.sep + path + os.path.sep + file_] = (
                            str(config.env.video_source) + os.path.sep + path + os.path.sep + file_)
    return final_dict
