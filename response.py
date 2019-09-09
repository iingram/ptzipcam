#!/home/ian/.virtualenvs/ptzSpotter/bin/python

import os
import yaml
import time

import cv2
import numpy as np

from ptz_camera import PtzCam
from ptz_camera import _checkZeroness as checkZeroness
from camera import Camera
import ui

from dnntools import neuralnetwork as nn
from dnntools import draw

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


# t = classType/1000 * 1.5 * np.pi + 2.2 * np.pi

# # t = .5
# # r = int(.8 * (screen_height/2))

# x = screen_width/2 + .5 * screen_width * np.cos(t)
# y = screen_height/2 + .5 * screen_height * np.sin(t)

def make_position_generator(num_steps):
    positions = np.round(.95 * np.sin(np.linspace(0, 2*np.pi, num_steps)), decimals=1)

    while True:
        for i in range(num_steps):
            yield positions[i]

def bittle():
    while True:
        yield (.99, -.99)
        yield (.99, .99)
        yield (-.99, .99)
        yield (-.99, -.99)

if __name__ == '__main__':
    # construct core objects
    ptz_cam = PtzCam(IP, PORT, USER, PASS)
    ptz_cam_2 = PtzCam('192.168.1.63', PORT, USER, PASS)
    cam = Camera()
    cam_r = Camera(address='udp://127.0.0.1:5001')

    frame = cam.get_frame()
    frame_r = cam_r.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)
    frame_r = ui.orient_frame(frame_r, ORIENTATION)

    window_name = 'Detect, Track, and Zoom'

    frame_toshow = np.hstack((frame, frame_r))
    uih = ui.UI_Handler(frame_toshow, window_name)

    network = nn.ObjectDetectorHandler(MODEL_CONFIG,
                                       MODEL_WEIGHTS,
                                       INPUT_WIDTH,
                                       INPUT_HEIGHT)

    frame = cam.get_frame()
    frame_width = frame.shape[0]
    frame_height = frame.shape[1]

    if RECORD:
        vid_writer = cv2.VideoWriter('boggle.avi',
                                     cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                     15,
                                     (frame_width, frame_height))

    # initialize position of camera
    x_dir = 0
    y_dir = 0
    x_dir_2 = 0
    y_dir_2 = 0
    zoom_command = 0
    ptz_cam.zoom_out_full()
    time.sleep(1)
    ptz_cam.absmove(INIT_POS[0], INIT_POS[1])
    ptz_cam_2.absmove(INIT_POS[0], INIT_POS[1])
    # ptz_cam.absmove(0, -0.5)
    time.sleep(2)

    x_err = 0
    y_err = 0

    frames_since_last_acq = 0

    position_generator = make_position_generator(50)
    bitbit = bittle()
    # boggle_x = next(position_generator)

    last_time = 0
    while True:
        raw_frame = cam.get_frame()
        frame_r = cam_r.get_frame()

        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame_r = ui.orient_frame(frame_r, ORIENTATION)
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
            #print(frame_height)
            print(x_err)
            y_err = frame_height/2 - yc

            if x_err < 50 and y_err < 50:
                zoom_command += .1
                if zoom_command >= 1.0:
                    zoom_command = 1.0
                # zoom_command = 1.0

            if box_width >= .7 * frame_width or box_height >= .7 * frame_height:
                zoom_command = 0.0

            # rudimentary boggling of second cam if detection
            if (time.time() - last_time) >= 1:
                # x_dir_2 = float(next(position_generator))
                # if x_dir_2 <= 0:
                #     x_dir_2 = 0.99
                #     y_dir_2 = 0.99
                # elif x_dir_2 > 0:
                #     x_dir_2 = -0.99
                #     y_dir_2 = -0.99
                x_dir_2, y_dir_2 = next(bitbit)
                
                last_time = time.time()
        else:
            frames_since_last_acq += 1
            if frames_since_last_acq > 5:
                x_err = 0
                # x_err = -300  # TEMPORARY: IS HACK TO GET A SCAN
                y_err = 0
            # if frames_since_last_acq > 30:
            #     ptz_cam.absmove(INIT_POS[0], INIT_POS[1])
            zoom_command -= .1
            if zoom_command <= -1.0:
                zoom_command = -1.0
            # zoom_command = -1.0

            ptz_cam_2.stop()


        # update ui and handle user input
        frame_toshow = np.hstack((frame, frame_r))
        key = uih.update(frame_toshow, hud=False)
        if RECORD:
            vid_writer.write(frame.astype(np.uint8))

        if key == ord('q'):
            break

        # run position controller on ptz system
        if ORIENTATION == 'left':
            y_dir = -x_dir
            x_dir = 0

        #print(y_dir)

        ptz_cam.move_w_zoom(x_dir, y_dir, zoom_command)

        # print(x_dir_2)
        # print(type(x_dir_2))
        x_dir_2 = checkZeroness(x_dir_2)
        x_dir_2 = float(x_dir_2)
        ptz_cam_2.move_w_zoom(x_dir_2, y_dir_2, zoom_command)

        
        # boggle_x = checkZeroness(boggle_x)
        # ptz_cam_2.absmove(boggle_x, INIT_POS[1])
        # print(boggle_x)

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

        x_dir = calc_command(x_err, -.005)
        y_dir = calc_command(y_err, .1)

        if x_dir == 0 and y_dir == 0:
            ptz_cam.stop()

    if RECORD:
        vid_writer.release()
    cam.release()
    cam_r.release()
    ptz_cam.stop()
    ptz_cam_2.stop()
    uih.clean_up()
