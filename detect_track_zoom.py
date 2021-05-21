#!/usr/bin/env python
"""Tracks targets detected via object detection using PTZ IP camera.

Attempts to detect, track, and zoom in on target classes (usually
various animal species of interest) by running an object detector on
frames captured from the camera and using their offset and size in the
frame to run a control system around the PTZ attributes on the IP
camera.
"""
import os
import time
import argparse

import yaml

from ptzipcam import logs, ui, convert
from ptzipcam.ptz_camera import PtzCam, MotorController
from ptzipcam.camera import Camera
from ptzipcam.io import ImageStreamRecorder
# from ptzipcam.video_writer import DilationVideoWriter

# from dnntools import neuralnetwork as nn
from dnntools import neuralnetwork_coral as nn

from dnntools import draw

log = logs.prep_log()

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

# DILATION = True
FRAME_RATE = 15
FRAME_WINDOW = 30

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
RECORD_ONLY_DETECTIONS = configs['RECORD_ONLY_DETECTIONS']
RECORD_FOLDER = configs['RECORD_FOLDER']

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

if __name__ == '__main__':
    # construct core objects
    ptz = PtzCam(IP, PORT, USER, PASS)
    # cam = Camera()
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

    log.info("Using: " + nn.__name__)
    log.info("Frame shape: " + str(frame.shape[:2]))
    log.info("Detection threshold: " + str(CONF_THRESHOLD))
    log.info('Tracked classes: ' + str(TRACKED_CLASS))

    if RECORD:
        log.info('Recording is turned ON')
        strg = configs['RECORD_FOLDER']
        log.info('Recordings will be stored in {}'.format(strg))
        recorder = ImageStreamRecorder(configs['RECORD_FOLDER'])

        # codec = cv2.VideoWriter_fourcc(*'MJPG')
        # filename = 'video_dtz'
        # if 'neuralnetwork_coral' in nn.__name__:
        #     filename = filename + '_coral'
        # else:
        #     filename = filename + '_dnn'

        # if not DILATION:
        #     filename = filename + '_lineartime' + '.avi'
        #     vid_writer = cv2.VideoWriter(filename,
        #                                  codec,
        #                                  FRAME_RATE,
        #                                  (frame_width, frame_height))
        # else:
        #     filename = filename + '_dilation' + '.avi'
        #     dilation_vid_writer = DilationVideoWriter(filename,
        #                                               codec,
        #                                               FRAME_RATE,
        #                                               (frame_width,
        #                                                frame_height),
        #                                               FRAME_WINDOW)
    else:
        log.info('Recording is turned OFF')

    if RECORD_ONLY_DETECTIONS:
        log.info('Record only detections: True')

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    # ptz.absmove(INIT_POS[0], INIT_POS[1])
    pan_init = convert.degrees_to_command(INIT_POS[0], 360.0)
    tilt_init = convert.degrees_to_command(INIT_POS[1], 90.0)
    zoom_init = INIT_POS[2]/25.0

    log.info('Moving to initial position.')
    ptz.absmove_w_zoom_waitfordone(pan_init,
                                   tilt_init,
                                   zoom_init,
                                   close_enough=.01)
    log.info('Completed move to initial position.')

    pan, tilt, zoom = ptz.get_position()
    if RECORD:
        frame = ui.orient_frame(frame, ORIENTATION)
        recorder.record_image(frame,
                              pan,
                              tilt,
                              'n/a: start-up frame',
                              0.0)

    x_err = 0.0
    y_err = 0.0

    frames_since_last_target = 0

    while True:
        pan, tilt, zoom = ptz.get_position()
        raw_frame = cam.get_frame()
        if raw_frame is None:
            print('Frame is None.')
            continue

        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        target_lbox = detector.detect(frame)

        if target_lbox:
            detected_class = detector.class_names[target_lbox['class_id']]
            score = 100 * target_lbox['confidence']
            print("[INFO] Detected: "
                  + "{} with confidence {:.1f}".format(detected_class,
                                                       score))

            frames_since_last_target = 0
            draw.labeled_box(frame, detector.class_names, target_lbox)

            errors = motor_controller.calc_errors(target_lbox)
            x_err, y_err = errors
        else:
            time.sleep(.03)
            detected_class = 'nothing detected'
            score = 0.0
            zoom_command = 0

            frames_since_last_target += 1
            if frames_since_last_target > 10:
                x_err = 0
                y_err = 0

            if frames_since_last_target > 30:
                # log.info('Since nothing detected, panning right.')
                # x_err = -0.2
                x_err = 0

            # # commenting this bit out because it doesn't always work
            # # and may be source of wandering bug
            # if frames_since_last_target > 30:
            #     ptz.absmove(INIT_POS[0], INIT_POS[1])
            if frames_since_last_target > 30:
                zoom_command -= .05
                if zoom_command <= -1.0:
                    zoom_command = -1.0
                # zoom_command = -1.0

        # update ui and handle user input

        if not HEADLESS:
            key = uih.update(frame, hud=False)
            if key == ord('q'):
                break

        if RECORD:
            if((RECORD_ONLY_DETECTIONS and target_lbox)
               or not RECORD_ONLY_DETECTIONS):
                log.info('Recording frame.')
                recorder.record_image(frame,
                                      pan,
                                      tilt,
                                      detected_class,
                                      score)

            # if not DILATION:
            #     vid_writer.write(frame.astype(np.uint8))
            # else:
            #     dilation_vid_writer.update(frame, target_lbox is not None)

        # run position controller on ptz system
        commands = motor_controller.update(x_err,
                                           y_err,
                                           zoom_command)
        x_velocity, y_velocity, zoom_command = commands

        # forget to commit this when it was written.  a little
        # uncertain what the goal was.  leaving it in as a timebomb.
        if tilt >= 1.0 and y_velocity <= 0:
            y_velocity = 0.0

        # log.info(f'{pan}, {tilt}, {zoom}')
        log.debug(f'x_err: {x_err:.2f} || y_err: {y_err:.2f}')
        log.debug(f'x_vel: {x_velocity:.2f} || y_vel: {y_velocity:.2f}')

        if x_velocity == 0 and y_velocity == 0 and zoom < 0.001:
            # print('stop action')
            ptz.stop()

        ptz.move_w_zoom(x_velocity, y_velocity, zoom_command)

    # if RECORD:
    #     if not DILATION:
    #         vid_writer.release()
    #     else:
    #         dilation_vid_writer.release()
    del cam
    ptz.stop()
    if not HEADLESS:
        uih.clean_up()
