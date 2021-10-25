#!/usr/bin/env python
"""Control PTZ camera with mouse with object detection

Allows control of a PTZ IP camera while object detector runs on
incoming frames.

"""
import logging
import argparse
import os
import yaml

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.camera import Camera
from ptzipcam import ui, logs

from dnntools import neuralnetwork as nn
from dnntools import draw

log = logs.prep_log(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
parser.add_argument('-s',
                    '--stream',
                    default=None,
                    help='Stream to use if want to override config file.')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

ORIENTATION = configs['ORIENTATION']

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
STREAM = configs['STREAM']

# CV constants
CONF_THRESHOLD = configs['CONF_THRESHOLD']
NMS_THRESHOLD = configs['NMS_THRESHOLD']
INPUT_WIDTH = configs['INPUT_WIDTH']
INPUT_HEIGHT = configs['INPUT_HEIGHT']

MODEL_PATH = configs['MODEL_PATH']
MODEL_CONFIG = os.path.join(MODEL_PATH, configs['MODEL_CONFIG_FILE'])
MODEL_WEIGHTS = os.path.join(MODEL_PATH, configs['MODEL_WEIGHTS_FILE'])
CLASSES_FILE = os.path.join(MODEL_PATH, configs['CLASS_NAMES_FILE'])
CLASSES = nn.read_classes_from_file(CLASSES_FILE)

if __name__ == '__main__':
    ptz_cam = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

    frame = cam.get_frame()
    if frame is None:
        log.warning('Frame is None.')

    window_name = 'Control PTZ Camera with mouse'
    uih = ui.UI_Handler(frame, window_name)

    network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                       MODEL_WEIGHTS,
                                       INPUT_WIDTH,
                                       INPUT_HEIGHT)

    x_dir = 0
    y_dir = 0
    zoom_command = False
    ptz_cam.zoom_out_full()

    while True:
        raw_frame = cam.get_frame()
        if raw_frame is None:
            log.warning('Frame is None.')
            continue

        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        outs, inference_time = network.infer(frame)
        lboxes = network.filter_boxes(outs,
                                      frame,
                                      CONF_THRESHOLD,
                                      NMS_THRESHOLD)

        for lbox in lboxes:
            draw.labeled_box(frame, CLASSES, lbox)

        key = uih.update(frame)

        if key == ord('q'):
            break

        if zoom_command == 'i':
            ptz_cam.zoom_in_full()
        elif zoom_command == 'o':
            ptz_cam.zoom_out_full()

        if ORIENTATION == 'left':
            ptz_cam.move(y_dir, -x_dir)
        elif ORIENTATION == 'down':
            ptz_cam.move(-x_dir, -y_dir)
        else:
            ptz_cam.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = uih.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptz_cam.stop()

    cam.release()
    ptz_cam.stop()
    uih.clean_up()
