#!/usr/bin/env python
"""If see target, moves to second position momentarily

If a target class is detected while in the home position, the camera
is commanded to second position momentarily to watch what is happening
there.
"""
import logging
import time
import os
import argparse
from threading import Thread

import cv2
import yaml

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.camera import Camera
from ptzipcam import convert, ui, logs
from ptzipcam.io import ImageStreamRecorder

from dnntools import neuralnetwork as nn
from dnntools import draw

log = logs.prep_log(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
parser.add_argument('-w',
                    '--wait',
                    required=True,
                    help='Time to wait at non-home position')
args = parser.parse_args()
CONFIG_FILE = args.config
TIME_AT_NONHOME = int(args.wait)

FRAME_RATE = 15
FRAME_WINDOW = 30

COMMAND_DIVISORS = {'pan': 360.0,
                    'tilt': 90.0,
                    'zoom': 4.0}

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
    commands['pan'] = convert.degrees_to_command(raw_command[0],
                                                 divisors['pan'])
    commands['tilt'] = convert.degrees_to_command(raw_command[1],
                                                  divisors['tilt'])
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
            self.frame = ui.orient_frame(self.frame, ORIENTATION)

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

    detector = nn.TargetDetector(MODEL_CONFIG,
                                 MODEL_WEIGHTS,
                                 INPUT_WIDTH,
                                 INPUT_HEIGHT,
                                 CONF_THRESHOLD,
                                 NMS_THRESHOLD,
                                 CLASSES,
                                 TRACKED_CLASS)

    log.info("Using: " + nn.__name__)
    frame = capturer.frame.copy()
    log.info("Frame shape: " + str(frame.shape[:2]))
    logs.log_configuration(log, configs)

    if RECORD:
        recorder = ImageStreamRecorder(configs['RECORD_FOLDER'])

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
                                   close_enough=.05)

    log.info('Moved to initial PTZ position')

    frames_since_last_target = 0

    while True:
        if stop_flag[0] is True:
            break

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

            commands = convert_commands((270.0, 45.0, 2.0),
                                        COMMAND_DIVISORS)
            ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                           commands['tilt'],
                                           commands['zoom'],
                                           close_enough=.05)

            time.sleep(TIME_AT_NONHOME)

        else:
            detected_class = 'nothing detected'
            score = 0.0

            commands = convert_commands(INIT_POS,
                                        COMMAND_DIVISORS)
            ptz.absmove_w_zoom_waitfordone(commands['pan'],
                                           commands['tilt'],
                                           commands['zoom'],
                                           close_enough=.05)

        if RECORD:
            recorder.record_image(frame,
                                  (0, 0, 0),
                                  detected_class,
                                  target_lbox)

    ptz.stop()
