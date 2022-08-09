#!/usr/bin/env python
"""Demo of script for camera on side with angle correction

"""
import random
import logging
import time
import argparse

import yaml
import numpy as np
from scipy import ndimage

from ptzipcam import logs, ui, convert
from ptzipcam.ptz_camera import PtzCam
from ptzipcam.camera import Camera

log = logs.prep_log(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

FRAME_RATE = 15
FRAME_WINDOW = 30
CLOSE_ENUF_ON_INIT = .05

PAN_RANGE = 360.0
TILT_RANGE = 90.0

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

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


def main():
    # construct core objects
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)
    frame = cam.get_frame()
    if frame is None:
        log.warning('Frame is None.')

    window_name = 'Look around randomly'

    canvas = np.zeros((2000, 2000, 3), dtype=np.uint8)
    if not HEADLESS:
        uih = ui.UI_Handler(canvas, window_name)

    log.info("Frame shape: " + str(frame.shape[:2]))
    logs.log_configuration(log, configs)

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)

    pan_init = convert.degrees_to_command(INIT_POS[0], 360.0)
    tilt_init = convert.degrees_to_command(INIT_POS[1], 90.0)
    zoom_init = convert.power_to_zoom(INIT_POS[2], CAM_ZOOM_POWER)

    log.debug(f'Inits: {pan_init}, {tilt_init}, {zoom_init}')
    log.info('Moving to initial position.')
    ptz.absmove_w_zoom_waitfordone(pan_init,
                                   tilt_init,
                                   zoom_init,
                                   close_enough=CLOSE_ENUF_ON_INIT)
    log.info('Completed move to initial position.')

    pan, tilt, zoom = ptz.get_position()

    start_time = time.time()
    returning_from_look = False
    pan_command = pan_init
    tilt_command = tilt_init
    zoom_command = zoom_init

    wait_time = 1.0

    while True:
        pan, tilt, zoom = ptz.get_position()
        frame = cam.get_frame()
        if frame is None:
            print('Frame is None.')
            continue

        frame = ui.orient_frame(frame, ORIENTATION)

        # update ui and handle user input
        if not HEADLESS:
            canvas = np.zeros((2000, 2000, 3), dtype=np.uint8)
            angle = convert.command_to_degrees(pan, PAN_RANGE)
            rotated_frame = ndimage.rotate(frame, angle)
            h, w, _ = rotated_frame.shape
            ch, cw, _ = canvas.shape
            left = int(ch/2 - h/2)
            right = int(ch/2 + h/2)
            top = int(cw/2 - w/2)
            bottom = int(cw/2 + w/2)
            canvas[left:right, top:bottom, :] = rotated_frame
            
            key = uih.update(canvas, hud=False)
            if key == ord('q'):
                break

        log.debug(f'{pan}, {tilt}, {zoom}')

        if time.time() - start_time > wait_time:
            if not returning_from_look:
                log.info('go to look.')
                pan_d = PAN_RANGE * random.random()
                # tilt_d = TILT_RANGE * (random.random())
                # to keep within bottom half
                tilt_d = TILT_RANGE * (random.random() * 0.5 + 0.5)

                pan_command = convert.degrees_to_command(pan_d, PAN_RANGE)
                tilt_command = convert.degrees_to_command(tilt_d, TILT_RANGE)
                zoom_command = random.random()

                ptz.absmove_w_zoom(pan_command,
                                   tilt_command,
                                   zoom_command)
                wait_time = random.uniform(4, 10)
            else:
                log.info('returning from look')
                ptz.absmove_w_zoom_waitfordone(pan_command,
                                               tilt_command,
                                               0.0)
                wait_time = random.uniform(3, 6)
            start_time = time.time()
            returning_from_look = not returning_from_look

    del cam
    ptz.stop()
    if not HEADLESS:
        uih.clean_up()


if __name__ == '__main__':
    main()
