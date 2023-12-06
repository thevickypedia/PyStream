import os.path

import cv2
import numpy


class ImageLoader:
    def __init__(self, filename: str):
        self.filename = filename
        self.video_capture = cv2.VideoCapture(self.filename)

    def generate_thumbnails(self):
        success, image = self.video_capture.read()
        count = 0
        while success:
            "frame_%d.jpg"
            count += 1

    def _capture_frame(self, name: str, image: numpy.ndarray):
        print(type(image))
        cv2.imwrite(name, image)  # save frame as JPEG file
        success, image = self.video_capture.read()
        print('Read a new frame: ', success)

    def generate_preview(self):
        success, image = self.video_capture.read()
        if success:
            self._capture_frame(f"{self.filename}_preview.jpg", image)


if __name__ == '__main__':
    ImageLoader("video.mp4").generate_preview()
