#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import yaml
import time

import cv2
import numpy as np

from ptz_camera import PtzCam
from camera import Camera
import ui

from zooSpotter import neuralnetwork as nn
from zooSpotter import draw

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
    
# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']

# ptz camera setup constants
INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']

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

if __name__ == '__main__':
    # construct core objects
    ptzCam = PtzCam(IP, PORT, USER, PASS)
    cam = Camera()

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    window_name = 'Detect, Track, and Zoom'
    uih = ui.UI_Handler(frame, window_name)

    network = nn.NeuralNetworkHandler(MODEL_CONFIG,
                                      MODEL_WEIGHTS,
                                      INPUT_WIDTH,
                                      INPUT_HEIGHT)

    frame = cam.get_frame()
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]

    if RECORD:
        vid_writer = cv2.VideoWriter('detectTrackZoom.avi',
                                     cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                     15,
                                     (frame_width, frame_height))

    # initialize position of camera
    x_dir = 0
    y_dir = 0
    zoom_command = 0
    ptzCam.zoom_out_full()
    time.sleep(1)
    ptzCam.absmove(INIT_POS[0], INIT_POS[1])
    # ptzCam.absmove(0, -0.5)
    time.sleep(2)

    x_err = 0
    y_err = 0

    frames_since_last_acq = 0

    while True:
        raw_frame = cam.get_frame()
        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        outs, inferenceTime = network.infer(frame)
        lboxes = nn.NeuralNetworkHandler.filterBoxes(outs,
                                                     frame,
                                                     CONF_THRESHOLD,
                                                     NMS_THRESHOLD)

        # extract the lbox with the highest confidence (that is a target type)
        highest_confidence_tracked_class = 0
        target_lbox = None
        for lbox in lboxes:
            if CLASSES[lbox['classId']] in TRACKED_CLASS:
                if lbox['confidence'] > highest_confidence_tracked_class:
                    highest_confidence_tracked_class = lbox['confidence']
                    target_lbox = lbox

        # if there is an appropriate lbox attempt to adjust ptz cam 
        if target_lbox:
            frames_since_last_acq = 0
            draw.labeledBox(frame, CLASSES, target_lbox)
            xc, yc = draw.box_to_coords(target_lbox['box'],
                                        return_kind='center')
            ret = draw.box_to_coords(target_lbox['box'])
            x, y, box_width, box_height = ret
            x_err = frame_width/2 - xc
            y_err = frame_height/2 - yc

            if x_err < 50 and y_err < 50:
                zoom_command += .1
                if zoom_command >= 1.0:
                    zoom_command = 1.0
                # zoom_command = 1.0

            if box_width >= .7 * frame_width or box_height >= .7 * frame_height:
                zoom_command = 0.0
        else:
            frames_since_last_acq += 1
            if frames_since_last_acq > 5:
                x_err = 0
                # x_err = -300  # TEMPORARY: IS HACK TO GET A SCAN
                y_err = 0
            if frames_since_last_acq > 30:
                ptzCam.absmove(INIT_POS[0], INIT_POS[1])
            zoom_command -= .1
            if zoom_command <= -1.0:
                zoom_command = -1.0
            # zoom_command = -1.0

        # update ui and handle user input
        key = uih.update(frame, hud=False)
        if RECORD:
            vid_writer.write(frame.astype(np.uint8))

        if key == ord('q'):
            break

        # run position controller on ptz system
        ptzCam.move_w_zoom(x_dir, y_dir, zoom_command)

        def calc_command(err, k):
            command = k * err
            if command >= 1.0:
                command = 1.0
            if command <= -1.0:
                command = -1.0

            # if command > -0.1 and command < 0.1:
            #     command = 0.0

            return command

        # x_dir = calc_command(x_err, -.005)
        # y_dir = calc_command(y_err, .005)

        if ORIENTATION=='down':
            x_err = -x_err
            y_err = -y_err
        
        x_dir = calc_command(x_err, -.0008)
        y_dir = calc_command(y_err, .002)

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    if RECORD:
        vid_writer.release()
    cam.release()
    ptzCam.stop()
    uih.clean_up()
