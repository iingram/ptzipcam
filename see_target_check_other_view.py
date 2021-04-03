#!/usr/bin/env python
import logging
logging.basicConfig(level='INFO',
                    format='[%(levelname)s] %(message)s (%(name)s)')

import time
import os
import time
import argparse
from threading import Thread

import cv2
import yaml

from ptzipcam.ptz_camera import PtzCam
# from ptzipcam.ptz_camera import MotorController
from ptzipcam.camera import Camera
#from ptzipcam import ui
#from ptzipcam.io import ImageStreamRecorder
# from ptzipcam.video_writer import DilationVideoWriter

from dnntools import neuralnetwork as nn
# from dnntools import neuralnetwork_coral as nn

from dnntools import draw

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


class Capturer(Thread):

    def __init__(self, stop_flag):
        super().__init__()
        self.cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)
        self.frame = self.cam.get_frame()
        if self.frame is None:
            log.warning('Frame is None.')

    def run(self):
        while True:
            self.frame = self.cam.get_frame()
            if self.frame is None:
                print('Frame is None.')
                continue

            # time.sleep(.03)

            cv2.imshow('frame', self.frame)
            k = cv2.waitKey(1)
            if k == ord('q'):
                stop_flag[0] = True
                del self.cam
                break
                
            
if __name__ == '__main__':
    stop_flag = [False]

    capturer = Capturer(stop_flag)
    capturer.setDaemon(True)
    capturer.start()
    
    ptz = PtzCam(IP, PORT, USER, PASS)

    # motor_controller = MotorController(PID_GAINS, ORIENTATION, frame)

    detector = nn.TargetDetector(MODEL_CONFIG,
                                 MODEL_WEIGHTS,
                                 INPUT_WIDTH,
                                 INPUT_HEIGHT,
                                 CONF_THRESHOLD,
                                 NMS_THRESHOLD,
                                 CLASSES,
                                 TRACKED_CLASS)

    log.info("Using: " + nn.__name__)

    # if RECORD:
    #     recorder = ImageStreamRecorder('/home/ian/images_dtz')

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    pan, tilt, zoom = ptz.get_position()

    log.info('Moving to initial PTZ position')
    commands = convert_commands(INIT_POS,
                                COMMAND_DIVISORS)
    ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                   commands['tilt'],
                                   commands['zoom'],
                                   close_enough=.01)
    log.info('Moved to initial PTZ position')

    frames_since_last_target = 0

    while True:
        if stop_flag[0] is True:
            break
        # pan, tilt, zoom = ptz.get_position()

        # raw_frame = ui.orient_frame(raw_frame, ORIENTATION)

        frame = capturer.frame.copy()
        target_lbox = detector.detect(frame)

        if target_lbox:
            detected_class = detector.class_names[target_lbox['class_id']]
            score = 100 * target_lbox['confidence']
            print("[INFO] Detected: "
                  + "{} with confidence {:.1f}".format(detected_class,
                                                       score))

            frames_since_last_target = 0
            draw.labeled_box(frame, detector.class_names, target_lbox)

            commands = convert_commands((100.0, 34.0, 0.0),
                                        COMMAND_DIVISORS)
            ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                           commands['tilt'],
                                           commands['zoom'],
                                           close_enough=.01)

            time.sleep(5)
            
        else:
            detected_class = 'nothing detected'
            score = 0.0

            commands = convert_commands((-100.0, 34.0, 0.0),
                                        COMMAND_DIVISORS)
            ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                           commands['tilt'],
                                           commands['zoom'],
                                           close_enough=.01)


            # frames_since_last_target += 1
            # if frames_since_last_target > 10:
            #     x_err = 0
            #     y_err = 0

            # if frames_since_last_target > 30:
            #     # x_err = -300
            #     x_err = 0

            # if frames_since_last_target > 30:
            #     zoom_command -= .05
            #     if zoom_command <= -1.0:
            #         zoom_command = -1.0

    ptz.stop()
