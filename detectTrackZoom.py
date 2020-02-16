#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import time

import yaml
import cv2
import numpy as np

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.camera import Camera
from ptzipcam import ui

from dnntools import neuralnetwork as nn
from dnntools import draw

CONFIG_FILE = 'config.yaml'

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
STREAM = 2

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

if __name__ == '__main__':
    # construct core objects
    ptz = PtzCam(IP, PORT, USER, PASS)
    # cam = Camera()
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    window_name = 'Detect, Track, and Zoom'
    uih = ui.UI_Handler(frame, window_name)

    network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                       MODEL_WEIGHTS,
                                       INPUT_WIDTH,
                                       INPUT_HEIGHT)

    frame = cam.get_frame()
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]

    total_pixels = frame_width * frame_height

    if RECORD:
        vid_writer = cv2.VideoWriter('video_detectTrackZoom.avi',
                                     cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                     15,
                                     (frame_width, frame_height))

    # initialize position of camera
    x_velocity = 0
    y_velocity = 0
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    pan, tilt, zoom = ptz.get_position()
    # ptz.absmove(INIT_POS[0], INIT_POS[1])
    pan_init = INIT_POS[0]/180.0
    tilt_init = INIT_POS[1]/45.0
    zoom_init = INIT_POS[2]/25.0
    
    ptz.absmove_w_zoom(pan_init, tilt_init, zoom_init)
    epsilon = .01
    while (pan >= pan_init + epsilon
           or pan <= pan_init - epsilon
           or tilt >= tilt_init + epsilon
           or tilt <= tilt_init - epsilon):
        time.sleep(.1)
        pan, tilt, zoom = ptz.get_position()

    x_err = 0
    y_err = 0

    frames_since_last_acq = 0

    while True:
        pan, tilt, zoom = ptz.get_position()
        print(zoom)

        raw_frame = cam.get_frame()
        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        outs, inference_time = network.infer(frame)
        lboxes = nn.ObjectDetectorHandler.filter_boxes(outs,
                                                       frame,
                                                       CONF_THRESHOLD,
                                                       NMS_THRESHOLD)

        # extract the lbox with the highest confidence (that is a target type)
        highest_confidence_tracked_class = 0
        target_lbox = None
        for lbox in lboxes:
            if CLASSES[lbox['class_id']] in TRACKED_CLASS:
                if lbox['confidence'] > highest_confidence_tracked_class:
                    highest_confidence_tracked_class = lbox['confidence']
                    target_lbox = lbox

        # if there is an appropriate lbox attempt to adjust ptz cam
        if target_lbox:
            frames_since_last_acq = 0
            draw.labeled_box(frame, CLASSES, target_lbox)
            xc, yc = draw.box_to_coords(target_lbox['box'],
                                        return_kind='center')
            ret = draw.box_to_coords(target_lbox['box'])
            x, y, box_width, box_height = ret
            x_err = frame_width/2 - xc
            y_err = frame_height/2 - yc

            target_bb_pixels = box_width * box_height

            # if x_err < 50 and y_err < 50:
            # if x_err != 0 and x_err < 50 and y_err < 50:
            if (target_bb_pixels / total_pixels) < .3:
                zoom_command += .1
                if zoom_command >= 1.0:
                    zoom_command = 1.0
                # zoom_command = 1.0
            else:
                zoom_command = 0.0

            if box_width >= .7 * frame_width or box_height >= .7 * frame_height:
                zoom_command = 0.0
        else:
            zoom_command = 0
            # print(str(time.time()) + ': no target')
            frames_since_last_acq += 1
            if frames_since_last_acq > 10:
                x_err = 0
                y_err = 0

            if frames_since_last_acq > 30:
                x_err = -300

            # # commenting this bit out because it doesn't always work
            # # and may be source of wandering bug
            # if frames_since_last_acq > 30:
            #     ptz.absmove(INIT_POS[0], INIT_POS[1])
            if frames_since_last_acq > 30:
                zoom_command -= .05
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
        ptz.move_w_zoom(x_velocity, y_velocity, zoom_command)

        def calc_command(err, k):
            command = k * err
            if command >= 1.0:
                command = 1.0
            if command <= -1.0:
                command = -1.0

            # if command > -0.1 and command < 0.1:
            #     command = 0.0

            return command

        # x_velocity = calc_command(x_err, -.005)
        # y_velocity = calc_command(y_err, .005)

        if ORIENTATION == 'down':
            x_err = -x_err
            y_err = -y_err

        x_velocity = calc_command(x_err, PID_GAINS[0])

        y_velocity = calc_command(y_err, PID_GAINS[1])

        if x_velocity == 0 and y_velocity == 0 and zoom < 0.001:
            # print('stop action')
            ptz.stop()

    if RECORD:
        vid_writer.release()
    cam.release()
    ptz.stop()
    uih.clean_up()
