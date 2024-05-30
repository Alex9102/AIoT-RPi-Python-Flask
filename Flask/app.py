from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
import psutil
import cv2
import os
import secrets
from camera import Camera
import argparse, logging, logging.config, conf
import configparser
from openaihelper import OpenAIHelper
from linemessage import LineMessage
import pyimgur
from yolo import Yolo
from mpdetection import Mp_detection

logging.config.dictConfig(conf.dictConfig)
logger = logging.getLogger(__name__)

LOG_FILE_PATH = 'logs/logfile.log'
MP_DETECTION_FLAG = False
YOLO_DETECTION_FLAG = False

#Config Parser
config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
camera = Camera()

openAIHelper = OpenAIHelper(config["OpenAI"]["KEY"])
lineMessage = LineMessage(config["Line"]["CHANNEL_ACCESS_TOKEN"], config["Line"]["USER_ID"])

camera.run()
mp_detection_counter = 0

def getResultOpenAI(file_path, type):
    result = openAIHelper.analyze_image(file_path, type)
    url = upload_image_get_url(config["Imgur"]["CLIENT_ID"], file_path)
    lineMessage.send_imagemessage(url)
    lineMessage.send_textmessage(result)

def trigger_main_thread_action_from_yolo(name, confidence, image):
    global YOLO_DETECTION_FLAG
    logger.debug("Callback triggered from yolo background task")
    with app.app_context():
        logger.debug(f"Category Name : {name} , Confidence : {confidence}")
        cv2.imwrite('images/yolodetection_output.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        YOLO_DETECTION_FLAG = True
        getResultOpenAI("images/yolodetection_output.jpg", "yolo")

def trigger_main_thread_action_from_mpdetection(name, confidence, image):
    global MP_DETECTION_FLAG
    logger.debug("Callback triggered from mpdetection background task")
    with app.app_context():
        logger.debug(f"Category Name : {name} , Confidence : {confidence}")
        cv2.imwrite('images/mpdetection_output.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        MP_DETECTION_FLAG = True
        getResultOpenAI("images/mpdetection_output.jpg", "mp")

yolo = Yolo(app, camera, callback=trigger_main_thread_action_from_yolo)

mp_detection = Mp_detection(app, camera, callback=trigger_main_thread_action_from_mpdetection)

def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
    return camera

def upload_image_get_url(client_id, imgpath):
    im = pyimgur.Imgur(client_id)
    upload_image = im.upload_image(imgpath, title="Uploaded with PyImgur")
    return upload_image.link

@app.route('/')
def index():
    logged_in = 'username' in session
    return render_template('index.html', logged_in=logged_in, username=session.get('username'))

@app.route('/get_log')
def get_log():
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r') as file:
            log_content = file.read()
        return jsonify({"log": log_content})
    else:
        return jsonify({"log": "Log file not found"}), 404

def gen(camera):
	logger.debug("Starting stream")
	while True:
		frame = camera.get_frame()
		yield (b'--frame\r\n'
			   b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

def gen_frames():
    camera = get_camera()
    while camera.isOpened():
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/test')
def test():
    result = openAIHelper.analyze_image("images/fire.jpg")
    url = upload_image_get_url(config["Imgur"]["CLIENT_ID"], "images/fire.jpg")
    lineMessage.send_imagemessage(url)
    lineMessage.send_textmessage(result)
    return jsonify(result=result, action="Line notification")

@app.route('/control_camera', methods=['POST'])
def control_camera():
    global camera
    action = request.json.get('action')
    if action == 'start':
        logger.debug("Start stream")
    elif action == 'stop':
        logger.debug("Stop stream")
    return jsonify(success=True)

@app.route('/system_stats')
def system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    disk_usage = psutil.disk_usage('/')
    disk_free = disk_usage.free / (1024 * 1024 * 1024)
    disk_total = disk_usage.total / (1024 * 1024 * 1024)
    disk_usage_percent = disk_usage.percent
    return jsonify(cpu_usage=cpu_usage, disk_free=disk_free, disk_total=disk_total, disk_usage_percent=disk_usage_percent)

@app.route('/get_detection_result')
def get_detection_result():
    global MP_DETECTION_FLAG, YOLO_DETECTION_FLAG
    mp_detection_result = MP_DETECTION_FLAG
    yolo_detection_result = YOLO_DETECTION_FLAG
    MP_DETECTION_FLAG = False
    YOLO_DETECTION_FLAG = False
    return jsonify(mp_detection_result=mp_detection_result, yolo_detection_result=yolo_detection_result)

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username == 'admin' and password == 'password':
        session['username'] = username
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/toggle', methods=['POST'])
def toggle():
    data = request.get_json()
    toggle_id = data.get('toggleId')
    state = data.get('state')

    if toggle_id == 'toggleObjectdetection':
        if state:
            handle_objectdetection_on()
        else:
            handle_objectdetection_off()
    elif toggle_id == 'toggleFiredetection':
        if state:
            handle_firedetection_on()
        else:
            handle_firedetection_off()
    return jsonify({'message': f'{toggle_id} set to {state}'})

def handle_objectdetection_on():
    # Action when Toggle Object detection is turned on
    logger.debug("Toggle Objectdetection is ON")
    mp_detection.start()

def handle_objectdetection_off():
    # Action when Toggle Object detection is turned off
    logger.debug("Toggle Objectdetection is OFF")
    mp_detection.stop()

def handle_firedetection_on():
    # Action when Toggle fire detection is turned on
    logger.debug("Toggle Fire Detection is ON")
    yolo.start()

def handle_firedetection_off():
    # Action when Toggle fire detection is turned off
    logger.debug("Toggle Fire Detection is OFF")
    yolo.stop()

if __name__ == '__main__':
    with app.app_context():
        try:
            app.run(debug=False)
        finally:
            camera.stop()
            
