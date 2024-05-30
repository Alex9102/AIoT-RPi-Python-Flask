import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

thread = None

class Camera:
	def __init__(self, fps=20, video_source=0):
		logger.info(f"Initializing camera class with {fps} fps and video_source={video_source}")
		self.fps = fps
		self.video_source = video_source
		self.camera = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
		self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
		self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
		self.max_frames = 5*self.fps
		self.frames = []
		self.isrunning = False
		self.isPaused = False

	def run(self):
		logging.debug("Perparing thread")
		global thread
		if thread is None:
			thread = threading.Thread(target=self._capture_loop,daemon=True)
			self.isrunning = True
			thread.start()
			logger.info("Image capture Thread started")

	def _capture_loop(self):
		dt = 1/self.fps
		logger.debug("Observation started")
		while self.isrunning:
			if not self.isPaused:
				v,im = self.camera.read()
				if v:
					if len(self.frames)==self.max_frames:
						self.frames = self.frames[1:]
					self.frames.append(im)
				time.sleep(dt)
		logger.info("Image capture thread stopped successfully")

	def stop(self):
		global thread
		logger.debug("Stopping Image capture thread")
		self.isrunning = False
		thread.join()		
		thread = None

	def pause(self):
		self.isPaused = True

	def resume(self):
		self.isPaused = False

	def get_frame(self, _bytes=True):
		if len(self.frames)>0:
			if _bytes:
				img = cv2.imencode('.png',self.frames[-1])[1].tobytes()
			else:
				img = self.frames[-1]
		else:
			img = cv2.imread("images/not_found.jpeg")
		return img
		