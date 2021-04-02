#!/usr/bin/env python
import time
import logging
import os
import time
import argparse

import yaml

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.ptz_camera import MotorController
from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder
# from ptzipcam.video_writer import DilationVideoWriter

from dnntools import neuralnetwork as nn
# from dnntools import neuralnetwork_coral as nn

from dnntools import draw

logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s (%(name)s)')
log = logging.getLogger('main')

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

FRAME_RATE = 15
FRAME_WINDOW = 30

COMMAND_DIVISORS = {'pan': 180.0,
                    'tilt': 45.0,
                    'zoom': 25.0}

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
STREAM = configs['STREAM']

# ptz camera setup constants
INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']
PID_GAINS = configs['PID_GAINS']

# CV constants
TRACKED_CLASS = configs['TRACKED_CLASS']
CONF_THRESHOLD = configs['CONF_THRESHOLD']
NMS_THRESHOLD = configs['NMS_THRESHOLD']
INPUT_WIDTH = configs['INPUT_WIDTH']
INPUT_HEIGHT = configs['INPUT_HEIGHT']

MODEL_PATH = configs['MODEL_PATH']
MODEL_CONFIG = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
MODEL_WEIGHTS = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
CLASSES_FILE = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
CLASSES = nn.read_classes_from_file(CLASSES_FILE)

# GUI constants
HEADLESS = configs['HEADLESS']


def convert_commands(raw_command,
                     divisors):
    commands = {}
    commands['pan'] = raw_command[0]/divisors['pan']
    commands['tilt'] = raw_command[1]/divisors['tilt']
    commands['zoom'] = raw_command[2]/divisors['zoom']
    
    return commands


if __name__ == '__main__':
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)
    frame = cam.get_frame()
    if frame is None:
        log.warning('Frame is None.')

    motor_controller = MotorController(PID_GAINS, ORIENTATION, frame)

    detector = nn.TargetDetector(MODEL_CONFIG,
                                 MODEL_WEIGHTS,
                                 INPUT_WIDTH,
                                 INPUT_HEIGHT,
                                 CONF_THRESHOLD,
                                 NMS_THRESHOLD,
                                 CLASSES,
                                 TRACKED_CLASS)

    window_name = 'Detect, Track, and Zoom'

    if not HEADLESS:
        uih = ui.UI_Handler(frame, window_name)

    log.info("[INFO] Using: " + nn.__name__)

    if RECORD:
        recorder = ImageStreamRecorder('/home/ian/images_dtz')

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    pan, tilt, zoom = ptz.get_position()

    commands = convert_commands(INIT_POS,
                                COMMAND_DIVISORS)
    ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                   commands['tilt'],
                                   commands['zoom'],
                                   close_enough=.01)

    frames_since_last_target = 0

    while True:
        # pan, tilt, zoom = ptz.get_position()
        raw_frame = cam.get_frame()
        if raw_frame is None:
            print('Frame is None.')
            continue

        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        # target_lbox = detector.detect(frame)

        # if target_lbox:
        #     detected_class = detector.class_names[target_lbox['class_id']]
        #     score = 100 * target_lbox['confidence']
        #     print("[INFO] Detected: "
        #           + "{} with confidence {:.1f}".format(detected_class,
        #                                                score))

        #     frames_since_last_target = 0
        #     draw.labeled_box(frame, detector.class_names, target_lbox)

        # else:
        #     detected_class = 'nothing detected'
        #     score = 0.0

        #     # frames_since_last_target += 1
        #     # if frames_since_last_target > 10:
        #     #     x_err = 0
        #     #     y_err = 0

        #     # if frames_since_last_target > 30:
        #     #     # x_err = -300
        #     #     x_err = 0

        #     # if frames_since_last_target > 30:
        #     #     zoom_command -= .05
        #     #     if zoom_command <= -1.0:
        #     #         zoom_command = -1.0

        if not HEADLESS:
            key = uih.update(frame, hud=False)
            if key == ord('q'):
                break

        # if RECORD:
        #     recorder.record_image(frame,
        #                           pan,
        #                           tilt,
        #                           detected_class,
        #                           score)

        # # run position controller on ptz system
        # x_velocity, y_velocity = motor_controller.run(x_err, y_err)
        # if x_velocity == 0 and y_velocity == 0 and zoom < 0.001:
        #     # print('stop action')
        #     ptz.stop()

        commands = convert_commands((100.0, 34.0, 0.0),
                                    COMMAND_DIVISORS)
        ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                       commands['tilt'],
                                       commands['zoom'],
                                       close_enough=.01)
        time.sleep(3)
        commands = convert_commands((-100.0, 34.0, 0.0),
                                    COMMAND_DIVISORS)
        ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                       commands['tilt'],
                                       commands['zoom'],
                                       close_enough=.01)
        time.sleep(3)

        
    del cam
    ptz.stop()
    if not HEADLESS:
        uih.clean_up()
