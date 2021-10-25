#!/usr/bin/env python
"""Visits a series of PTZ locations in series

Gets a series of PTZ locations from a YAML file (currently locations
are hardcoded in this code) and then visits each one after the other
while stopping for a set amount at each.

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
ORIENTATION = configs['ORIENTATION']
PID_GAINS = configs['PID_GAINS']
CAM_ZOOM_POWER = configs['CAM_ZOOM_POWER']

# GUI constants
HEADLESS = configs['HEADLESS']

SPOTS = [[34.4, 85.5, 25, 1.5],
         [64.3, 82.7, 13.24, 3.5],
         # [39.2, 83, 25, .5],
         # [70.9, 87.2, 25, 3]]
         # [39.2, 87.8, 25, 3]]
         # [34.4, 85.5, 25],
         [355.9, 80.4, 15, 6]]
spot_cycle = cycle(SPOTS)


def get_command_from_spot(spot):
    pan_command = spot[0]
    tilt_command = spot[1]
    zoom_command = spot[2]

    pan_command = convert.degrees_to_command(pan_command, 360)
    tilt_command = convert.degrees_to_command(tilt_command, 90)
    zoom_command = convert.power_to_zoom(zoom_command, CAM_ZOOM_POWER)

    return pan_command, tilt_command, zoom_command


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

    log.info('Moving to initial position.')
    spot = next(spot_cycle)
    ipan, itilt, izoom = get_command_from_spot(spot)
    time_to_wait = spot[3]
    ptz.absmove_w_zoom_waitfordone(ipan,
                                   itilt,
                                   izoom,
                                   close_enough=.01)
    log.info('Completed move to initial position.')

    pan, tilt, zoom = ptz.get_position()

    frames_since_last_target = 10000

    spot_start_time = time.time()
    while True:
        cycle_start_time = time.time()

        frame = cam.get_frame()
        if frame is None:
            print('Frame is None.')
            continue

        frame = ui.orient_frame(frame, ORIENTATION)

        if RECORD:
            recorder.record_image(frame,
                                  (0, 0, 0),
                                  'N/A',
                                  None)
            
        if time.time() - spot_start_time >= time_to_wait:
            spot_start_time = time.time()

            spot = next(spot_cycle)
            pan_com, tilt_com, zoom_com = get_command_from_spot(spot)
            time_to_wait = spot[3]

            ptz.absmove_w_zoom(pan_com,
                               tilt_com,
                               zoom_com)

        if not HEADLESS:
            key = uih.update(frame, hud=False)
            if key == ord('q'):
                break

        cycle_time = time.time() - cycle_start_time
        print(f'Cycle time: {cycle_time}')


    del cam
    ptz.stop()
    if not HEADLESS:
        uih.clean_up()
