import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from threading import Thread, Event
import time
import logging

logger = logging.getLogger(__name__)

thread = None
  
class Mp_detection:
    def __init__(self, app, camera, callback):
        base_options = python.BaseOptions(model_asset_path='efficientdet.tflite')
        options = vision.ObjectDetectorOptions(base_options=base_options,
                                       score_threshold=0.5)
        self.detector = vision.ObjectDetector.create_from_options(options)
        self.camera = camera
        self.app = app
        self.stop_event = Event()
        self.thread = Thread(target=self.polling_task)
        self.thread.daemon = True
        self.callback = callback
        self.repeat = 0

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()
        self.detector.close()

    def polling_task(self):
        while not self.stop_event.is_set():
            time.sleep(0.25)

            ret, name, confidence, image = self.check_condition()
            if ret:
                with self.app.app_context():
                    self.callback(name, confidence, image)

    def check_condition(self):
        image = self.camera.get_frame(_bytes=False)
        category = None
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            detection_result = self.detector.detect(mp_image)
        except:
            return False, None, None, None
        if len(detection_result.detections) > 0:
            # get the highest category.score object
            detection_result.detections = sorted(detection_result.detections, key=lambda x: x.categories[0].score, reverse=True)
            
            category = detection_result.detections[0].categories[0]
            if category.category_name == 'person':
                if category.score > 0.5:
                    logger.debug(f"Category Name : {category.category_name} , Confidence : {category.score}")
                    self.repeat = self.repeat + 1
                else:
                    self.repeat = 0
            else:
                logger.debug(f"Category Name : {category.category_name} , Confidence : {category.score}")
                return False, category.category_name, category.score, image
        else :
            logger.debug("No object detected")
            return False, None, None, None
        
        if self.repeat > 3:
            logger.debug(f"Got Positive Category Name : {category.category_name} , Confidence : {category.score}")
            self.repeat = 0
            return True, category.category_name, category.score, image
        else:
            return False, None, None, None

    