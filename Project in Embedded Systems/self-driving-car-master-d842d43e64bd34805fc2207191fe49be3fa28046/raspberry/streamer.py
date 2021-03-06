"""Stream video over network."""

import io
import time
import threading
import picamera
import logging

# Create a pool of image processors
done = False
lock = threading.Lock()
pool = []


class ImageProcessor(threading.Thread):
    """Image processor class for cutting video into frames."""

    def __init__(self):
        """Initialize class."""
        super(ImageProcessor, self).__init__()
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.logger = logging.getLogger('raspberry.ImageProcessorThread')
        self.start()

    def run(self):
        """Run thread."""
        # This method runs in a separate thread
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    self.stream.seek(0)
                    # Read the image and do some processing on it

                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return ourselves to the pool
                    with lock:
                        pool.append(self)


def streams():
    """Handle threads and return img file name."""
    # Set done to True if you want the script to terminate
    # at some point
    # done=True
    while not done:
        with lock:
            if pool:
                processor = pool.pop()
            else:
                processor = None
        if processor:
            yield processor.stream
            processor.event.set()
        else:
            # When the pool is starved, wait a while for it to refill
            time.sleep(0.1)


def start_recording():
    """Start recording images."""
    global pool
    with picamera.PiCamera() as camera:
        pool = [ImageProcessor() for i in range(4)]
        camera.resolution = (160, 120)
        camera.color_effects = (128, 128)
        camera.framerate = 30
        camera.start_preview()
        time.sleep(2)
        camera.capture_sequence(streams(), use_video_port=True)


def end_recording():
    """End recoring and kill threads."""
    # Shut down the processors in an orderly fashion
    while pool:
        with lock:
            processor = pool.pop()
        processor.terminated = True
        processor.join()
