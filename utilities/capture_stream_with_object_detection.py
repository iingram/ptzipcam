#!/usr/bin/env python
"""Utility to simply connect to a camera's video stream, display it,
record it, and run an object detector on it

"""

import os
import argparse
import yaml

from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder

from dnntools import neuralnetwork as nn
# from dnntools import neuralnetwork_coral as nn

from dnntools import draw

parser = argparse.ArgumentParser()
parser.add_argument('config_file_path',
                    help='Filename of configuration file')
args = parser.parse_args()

with open(args.config_file_path) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
RTSP_PORT = configs['RTSP_PORT']
CAM_BRAND = configs['CAM_BRAND']
USER = configs['USER']
PASS = configs['PASS']
if CAM_BRAND == 'hikvision':
    STREAM = configs['STREAM']
else:
    STREAM = None

ORIENTATION = configs['ORIENTATION']
RECORD = configs['RECORD']

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

if __name__ == '__main__':
    # cam = Camera()
    cam = Camera(ip=IP,
                 user=USER,
                 passwd=PASS,
                 cam_brand=CAM_BRAND,
                 rtsp_port=RTSP_PORT,
                 stream=STREAM)

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    window_name = 'Display stream from IP Camera'

    if not HEADLESS:
        uih = ui.UI_Handler(frame, window_name)

    print("[INFO] Using: " + nn.__name__)
    network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                       MODEL_WEIGHTS,
                                       INPUT_WIDTH,
                                       INPUT_HEIGHT)

    frame = cam.get_frame()
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]

    total_pixels = frame_width * frame_height

    if RECORD:
        recorder = ImageStreamRecorder('/home/ian/images_dtz')
        print('[INFO] Recording is ON')
    else:
        print('[INFO] Recording is OFF')

    while True:
        raw_frame = cam.get_frame()
        if raw_frame is None:
            print('Frame is None.')
            continue

        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        outs, inference_time = network.infer(frame)
        msg = ("[INFO] Inference time: "
               + "{:.1f} milliseconds".format(inference_time))
        print(msg)
        lboxes = network.filter_boxes(outs,
                                      frame,
                                      CONF_THRESHOLD,
                                      NMS_THRESHOLD)

        for lbox in lboxes:
            detected_class = CLASSES[lbox['class_id']]
            score = 100 * lbox['confidence']
            print('Detected: {} with score {:.1f}'.format(detected_class, score)) 
            draw.labeled_box(frame, CLASSES, lbox)

        # update ui and handle user input

        if not HEADLESS:
            key = uih.update(frame, hud=False)
            if key == ord('q'):
                break

        if RECORD:
            recorder.record_image(frame,
                                  0.0,
                                  0.0,
                                  'N/A',
                                  0.0)

    del cam
    if not HEADLESS:
        uih.clean_up()
