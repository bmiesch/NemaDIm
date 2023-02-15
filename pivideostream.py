"""
Brendan Miesch (Mieschbr) - 3/15/2022
Class for controlling a Raspberry Pi camera video stream with the PiCamera interface
"""

from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import cv2

class PiVideoStream:

    def __init__(self, resolution=(640, 480), framerate=30):
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,format='bgr', use_video_port=True)
        self.image = None
        self.stopped = False

    def start(self):
        t = Thread(target=self.update, daemon=True)
        t.start()
        return self

    def update(self):
        for frame in self.stream:
            self.image = frame.array
            self.rawCapture.truncate(0)

            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return  

    def read(self):
        return self.image

    def stop(self):
        self.stopped = True