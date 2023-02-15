"""
Brendan Miesch (Mieschbr) - 3/15/2022
NemaDIm System Software
"""

from pivideostream import PiVideoStream
from picamera.array import PiRGBArray
from picamera import PiCamera
import RPi.GPIO as GPIO
import numpy as np
import time
import cv2

#-----Variables that may need to be edited-----

SAVE_IMAGE_PATH = '/home/pi/Pictures/Test Images/' # The path to the desired save location
NUM_FRAME_SKIP = 20 # The number of frames skipped between frames that are processed


# RPI GPIO Pin definition for peripherals
RED_PIN = 17
GREEN_PIN = 27
BLUE_PIN = 22
BUTTON_PIN = 16


#-----Careful when editing code below this-----

class Experiment:
    def __init__(self):
        self.positive_count = 0
        self.total_count = 0
        self.threshold = None
        self.mode = None
        self.text_mode = None
        self.duration = None
        self.start_time = None
        self.cur_save_img = 1

# Initialize RGB LED
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BUTTON_PIN, GPIO.IN)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)
GPIO.output(GREEN_PIN, GPIO.HIGH)


def initialize(experiment):
    """Great user and retrive mode selection."""

    print("Hello, Welcome to NemaDIm")
    time.sleep(1)
    print("Please select mode, and hit enter:")
    print("\tType "+"[1]"+" for Timed Mode")
    print("\tType "+"[2]"+" for Button Mode")
    mode = input()
    assert(mode == "1" or mode == "2")


    if mode == "1":
        print("Timed mode has been selected! \nPlease enter the number of minutes you want the system to run for: ")
        duration = input()
        assert(int(experiment.duration) > 0 and int(experiment.duration) < 7200) # Greater than 0 minutes and less than 5 days
        print("Thank you, the experiment will end in " + experiment.duration + " minute(s)")
        experiment.text_mode = "time"
        duration = int(experiment.duration)*60
    if mode == "2":
        print("Button mode has been selected, the experiment will stop when the button is pressed")
        experiment.text_mode = "button"


def blink_light(color_pin):
    """Blink color_pin light 3 times."""

    # Turn off all other lights
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.LOW)

    # Blink chosen light 3 times
    for i in range(3):
        GPIO.output(color_pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(color_pin, GPIO.LOW)
        time.sleep(0.5)


def save_image(image, experiment):
    """Save image to SAVE_IMAGE_PATH."""

    # The images are saved with the name in "FrameX" form where X starts at 1
    cv2.imwrite(SAVE_IMAGE_PATH+'Frame'+str(experiment.cur_save_img)+'.jpg', image)
    cur_save_img += 1


def end(experiment):
    """Stop system and print results of experiment."""

    blink_light(RED_PIN) # UI to show that system stopped
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)
    GPIO.output(BLUE_PIN, GPIO.LOW)
    print("There were nematodes in " + str(experiment.positive_count) + " of the " + str(experiment.total_count) + " frames.")
    return


def calibrate(stream, experiment):
    """Re-calculate threshold value."""

    image = stream.read()
    if np.size(image) == 0:
        print("Problem encountered when calibrating.")
        stream.stop()
        end()

    image_binary = cv2.adaptiveThreshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 401, 5)
    global threshold
    experiment.threshold = np.sum(image_binary == 0)/np.sum(image_binary == 255)


def get_ratio(image):
    """Calculate the black:white pixel ratio of greyscale image."""

    image_binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 401, 5)
    return  np.sum(image_binary == 0)/np.sum(image_binary == 255)


def detect_in_stream(experiment):
    """Grab frames from PiVideoStream and process image."""

    stream = PiVideoStream()
    stream.start()
    time.sleep(2)
    blink_light(redPin)
    GPIO.output(bluePin, GPIO.HIGH)

    # Initial calibration
    calibrate(stream, experiment)

    while True:
        if experiment.text_mode == "time" and time.time() > experiment.start_time + experiment.duration:
            print("Your desired time limit of " + str(int(experiment.duration/60)) + " minutes has been reached.")
            stream.stop()
            end(experiment)

        # If button mode is on and the button is pressed stop the experiment
        if experiment.text_mode == "button" and GPIO.input(16) == 0:
            stream.stop()
            end(experiment)

        image = stream.read()
        experiment.total_count += 1
        if np.size(image) == 0:
            stream.stop()
            end(experiment)

        # Skip NUM_FRAME_SKIP frames
        for i in range(NUM_FRAME_SKIP):
            image = stream.read()
            if np.size(image) == 0:
                stream.stop()
                end(experiment)

        pixel_ratio = get_ratio(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))

        if pixel_ratio > experiment.threshold:
            experiment.positive_count += 1
            save_image(image, experiment)


if __name__ == "main":
    experiment = Experiment()
    initialize(experiment)

    if experiment.text_mode == "time":
        experiment.start_time = time.time()

    detect_in_stream(experiment)