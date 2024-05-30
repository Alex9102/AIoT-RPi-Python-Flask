import torch
import json

from threading import Thread, Event
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

class Yolo:
    def __init__(self, app, camera, callback):
        self.model = torch.hub.load(r'yolov5', 'custom', path=r'yolov5s_best.pt', source='local')
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

    def polling_task(self):
        while not self.stop_event.is_set():
            time.sleep(0.25)

            ret, name, confidence, image = self.check_condition()
            if ret:
                with self.app.app_context():
                    self.callback(name, confidence, image)

    def check_condition(self):
        image = self.camera.get_frame(_bytes=False)
        results = self.model(image, size=320)
        str = results.pandas().xyxy[0].to_json(orient="records")
        jdata = json.loads(str)
        dict = {}
        if len(jdata) > 0:
            # get the highest confidence object
            jdata = sorted(jdata, key=lambda x: x['confidence'], reverse=True)
            dict = jdata[0]
            if dict['confidence'] > 0.2:
                self.repeat = self.repeat + 1
            else:
                self.repeat = 0
        else:
            logger.debug("No object detected")
            self.repeat = 0
            return False, None, None, None
        
        if self.repeat > 5:
            logger.debug(f"Category Name : {dict['name']} , Confidence : {dict['confidence']}")
            self.repeat = 0
            return True, dict['name'], dict['confidence'], image
        else:
            return False, None, None, None
