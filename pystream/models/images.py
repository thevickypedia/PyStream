import datetime
import os
import pathlib
from typing import Tuple

import cv2

from pystream.logger import logger


class Images:
    """Initiates Images object to generate thumbnails and capture frames for a particular video.

    >>> Images

    """

    def __init__(self, filepath: pathlib.PosixPath):
        """Instantiates the object using opencv's VideoCapture object.

        Args:
            filepath: Path of the video file.
        """
        self.filepath = filepath
        self.video_capture = cv2.VideoCapture(str(self.filepath))

    def generate_thumbnails(self, interval: int = 1, output_dir: pathlib.PosixPath = None) -> bool:
        """Generate thumbnails for a video file.

        Args:
            interval: Interval in seconds to capture frame as thumbnail.
            output_dir: Output directory to store the thumbnails.

        Returns:
            bool:
            Returns a boolean flag to indicate success/failure.
        """
        # todo: put it to use integrating with 'video-js'
        if output_dir and output_dir.exists():
            path = str(output_dir)
        elif output_dir:
            logger.info("Creating %s", output_dir)
            os.makedirs(str(output_dir))
            path = str(output_dir)
        else:
            path = os.getcwd()
        success, image = self.video_capture.read()
        logger.info("Generating thumbnail for '%s'", self.filepath.name)
        count = 0
        n = 0
        while success:
            n += 1
            self.video_capture.set(cv2.CAP_PROP_POS_MSEC, (count * 1000))  # seek to incremental second in video
            cv2.imwrite(os.path.join(path, f"frame_{count}.jpg"), image)  # save frame as JPEG file
            success, image = self.video_capture.read()
            count += interval
        if n:
            logger.info("Generated %d thumbnails", n)
            return True
        logger.error("Failed to generate thumbnails for '%s'", self.filepath.name)

    def get_video_length(self) -> Tuple[int, datetime.timedelta]:
        """Get the number of frames to calculate length of the video.

        Returns:
            Tuple[int, datetime.timedelta]:
            A tuple of seconds and the timedelta value.
        """
        frames = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        seconds = round(frames / fps)
        video_time = datetime.timedelta(seconds=seconds)
        return seconds, video_time

    def generate_preview(self, path: str, at_second: int = None) -> bool:
        """Generate preview image for a video.

        Args:
            path: Filepath to store the preview image.
            at_second: Time in seconds at which the image should be captured for preview.

        Returns:
            bool:
            Returns a boolean flag to indicate success/failure.
        """
        seconds, video_time = self.get_video_length()
        if at_second:
            assert at_second <= seconds, f"Frame at {at_second}s is beyond the video duration of {seconds}s"
        else:
            # at_second = (5 * seconds) / 100  # 5%
            if seconds <= 20:
                at_second = 1
            elif seconds < 3_600:
                at_second = 3
            else:
                at_second = 5
        self.video_capture.set(cv2.CAP_PROP_POS_MSEC, at_second * 1_000)
        success, image = self.video_capture.read()
        if success:
            cv2.imwrite(path, image)  # save frame as JPEG file
            logger.info("Generated preview image for '%s' [%s] at %d seconds",
                        self.filepath.name, video_time, at_second)
            return True
        logger.error("Failed to generate preview image for '%s' [%s]", self.filepath.name, video_time)
