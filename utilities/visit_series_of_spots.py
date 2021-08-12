#!/usr/bin/env python
"""Visits a series of PTZ locations in series

Gets a series of PTZ locations from a YAML file and then visits each
one after the other while stopping for a set amount at each.

"""
import logging
import time
import argparse
from itertools import cycle

import yaml

from ptzipcam import logs, ui, convert
from ptzipcam.ptz_camera import PtzCam
from ptzipcam.camera import Camera
from ptzipcam.io import ImageStreamRecorder

log = logs.prep_log(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

FRAME_RATE = 15
FRAME_WINDOW = 30

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
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
CAM_ZOOM_POWER = configs['CAM_ZOOM_POWER']

# GUI constants
HEADLESS = configs['HEADLESS']

SPOTS = [[180, 90, 5],
         [270, 45, 25],
         [30, 10, 1],
         [330, 80, 20],
         [220, 75, 15]]
spot_cycle = cycle(SPOTS)
TIME_AT_EACH_SPOT = 1

if __name__ == '__main__':
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)
    frame = cam.get_frame()
    if frame is None:
        log.warning('Frame is None.')

    window_name = 'Visit a series of spots in sequence'

    if not HEADLESS:
        uih = ui.UI_Handler(frame, window_name)

    log.info("Frame shape: " + str(frame.shape[:2]))
    ipan, itilt, izoom = INIT_POS
    log.info(f'Initial position: {ipan} pan, {itilt} tilt, {izoom} zoom')

    if RECORD:
        log.info('Recording is turned ON')
        strg = configs['RECORD_FOLDER']
        log.info('Recordings will be stored in {}'.format(strg))
        recorder = ImageStreamRecorder(configs['RECORD_FOLDER'])
    else:
        log.info('Recording is turned OFF')

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    # ptz.absmove(INIT_POS[0], INIT_POS[1])
    pan_init = convert.degrees_to_command(INIT_POS[0], 360.0)
    tilt_init = convert.degrees_to_command(INIT_POS[1], 90.0)
    zoom_init = convert.power_to_zoom(INIT_POS[2], CAM_ZOOM_POWER)

    log.debug(f'Inits: {pan_init}, {tilt_init}, {zoom_init}')
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
                              (pan, tilt, zoom),
                              'n/a: start-up frame',
                              None)

    frames_since_last_target = 10000

    start_time = time.time()
    while True:
        pan, tilt, zoom = ptz.get_position()
        frame = cam.get_frame()
        if frame is None:
            print('Frame is None.')
            continue

        frame = ui.orient_frame(frame, ORIENTATION)
        if RECORD:
            recorder.record_image(frame,
                                  (pan, tilt, zoom),
                                  'N/A',
                                  None)

        if time.time() - start_time >= TIME_AT_EACH_SPOT:
            start_time = time.time()

            spot = next(spot_cycle)
            pan_command = spot[0]
            tilt_command = spot[1]
            zoom_command = spot[2]

            pan_command = convert.degrees_to_command(pan_command, 360)
            tilt_command = convert.degrees_to_command(tilt_command, 90)
            zoom_command = convert.power_to_zoom(zoom_command, CAM_ZOOM_POWER)

            ptz.absmove_w_zoom(pan_command,
                               tilt_command,
                               zoom_command)

        if not HEADLESS:
            key = uih.update(frame, hud=False)
            if key == ord('q'):
                break

    del cam
    ptz.stop()
    if not HEADLESS:
        uih.clean_up()
