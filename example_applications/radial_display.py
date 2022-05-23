#!/usr/bin/env python
"""Goes to random PTZ positions, pausing at each

"""
import random
import logging
import time
import argparse

import yaml
import cv2
import numpy as np

from ptzipcam import logs, convert
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


def basic_rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    result = cv2.warpAffine(image,
                            rot_mat,
                            image.shape[1::-1],
                            flags=cv2.INTER_LINEAR)
    return result


def position_view_on_canvas(image, pan, tilt):
    """Positions image based on pan and tilt on a large canvas

    Pan and tilt are in degrees

    """

    width = image.shape[1]
    pivot_point = (width/2, tilt*30)

    rotation_mat = cv2.getRotationMatrix2D(pivot_point, pan, 1.)

    # size of canvas
    bound_w = 6000
    bound_h = 6000

    rotation_mat[0, 2] += bound_w/2 - pivot_point[0]
    rotation_mat[1, 2] += bound_h/2 - pivot_point[1]

    # rotate image with the new bounds and translated rotation matrix
    rotated_image = cv2.warpAffine(image, rotation_mat, (bound_w, bound_h))
    return rotated_image


def main():
    # construct core objects
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)
    frame = cam.get_frame()
    if frame is None:
        log.warning('Frame is None.')

    window_name = 'Radial display'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name,
                     1000,
                     1000)

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

        frame = cv2.flip(frame, 0)

        pan_degrees = convert.command_to_degrees(pan, 360.0)
        tilt_degrees = convert.command_to_degrees(tilt, 90.0)
        frame = position_view_on_canvas(frame, pan_degrees, tilt_degrees)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(10)
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
                wait_time = random.uniform(1, 2)
            else:
                log.info('returning from look')
                ptz.absmove_w_zoom_waitfordone(pan_command,
                                               tilt_command,
                                               0.0)
                wait_time = random.uniform(1, 2)
            start_time = time.time()
            returning_from_look = not returning_from_look

    del cam
    ptz.stop()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
