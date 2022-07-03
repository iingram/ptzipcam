#!/usr/bin/env python
"""Move through pan and tilt and lay out an "eye" "grid"

"""
import logging
import time
import argparse
from itertools import cycle

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

WAIT_TIME = 0.1
TIME_TO_MOVE = 3.0

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
RTSP_PASS = PASS
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


def position_view_on_canvas(canvas, image, pan, tilt):
    """Positions image based on pan and tilt on a large canvas

    Pan and tilt are in degrees

    """

    width = image.shape[1]
    pivot_point = (width/2, tilt*50)

    rotation_mat = cv2.getRotationMatrix2D(pivot_point, pan, 1.)

    bound_w = canvas.shape[0]
    bound_h = canvas.shape[1]

    rotation_mat[0, 2] += bound_w/2 - pivot_point[0]
    rotation_mat[1, 2] += bound_h/2 - pivot_point[1]

    # rotate image with the new bounds and translated rotation matrix
    rotated_image = cv2.warpAffine(image, rotation_mat, (bound_w, bound_h))

    alpha = np.sum(rotated_image, axis=-1) > 0

    alpha = alpha.astype(float)

    alpha = np.dstack((alpha, alpha, alpha))

    rotated_image = rotated_image.astype(float)
    canvas = canvas.astype(float)

    foreground = cv2.multiply(alpha, rotated_image)
    canvas = cv2.multiply(1.0 - alpha, canvas)

    canvas = cv2.add(foreground, canvas)

    return canvas


def fill_spots_original():
    # if pan_d >= 360:
    #     tilt_d -= 15
    #     pan_d = 1

    #     if tilt_d <= 16:
    #         tilt_d = 90
    # pan_d += 30

    spots = []
    pans = np.arange(0, 360, 30)
    tilts = np.arange(90, 30, -15)

    for tilt in tilts:
        for pan in pans:
            spots.append([pan, tilt])

    spots = cycle(spots)

    return spots


def fill_spots_spaced():
    spots = []
    # 1280x960
    # circles = [[4, 28],
    #            [9, 53],
    #            [13, 78]]

    # 1280x720
    circles = [[4, 23],
               [8, 44],
               [13, 65],
               [17, 86]]
    
    for circle in circles:
        pans = np.linspace(0, 360, circle[0])
        pans = pans[:-1]
        for pan in pans:
            spots.append([pan, circle[1]])

    print(spots)
                
    spots = cycle(spots)

    return spots


def main():
    # construct core objects
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=RTSP_PASS, stream=STREAM)
    frame = cam.get_frame()
    if frame is None:
        log.warning('Frame is None.')

    window_name = 'Radial display'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name,
                     2000,
                     2000)

    log.info("Frame shape: " + str(frame.shape[:2]))
    logs.log_configuration(log, configs)

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
    pan_command = pan_init
    tilt_command = tilt_init
    zoom_command = zoom_init

    canvas = np.zeros((8000, 8000, 3), dtype=np.uint8)

    # spots = fill_spots_original()
    spots = fill_spots_spaced()

    state = 0
    
    while True:
        if state == 0 and time.time() - start_time > WAIT_TIME:
            # move to next spot
            pan_d, tilt_d = next(spots)

            log.info(f'Pan: {pan_d}, Tilt: {tilt_d}')

            pan_command = convert.degrees_to_command(pan_d, PAN_RANGE)
            tilt_command = convert.degrees_to_command(tilt_d, TILT_RANGE)

            ptz.absmove_w_zoom(pan_command,
                               tilt_command,
                               zoom_command)
            state = 1
            start_time = time.time()

        if state== 1 and time.time() - start_time > TIME_TO_MOVE:
            # capture and display photo
            pan, tilt, zoom = ptz.get_position()
            frame = cam.get_frame()
            if frame is None:
                print('Frame is None.')
                continue

            frame = cv2.flip(frame, 0)

            pan_degrees = convert.command_to_degrees(pan, 360.0)
            tilt_degrees = convert.command_to_degrees(tilt, 90.0)
            canvas = position_view_on_canvas(canvas,
                                             frame,
                                             pan_degrees,
                                             tilt_degrees)
            state = 0
            start_time = time.time()


        cv2.imshow(window_name, canvas/255)
        key = cv2.waitKey(10)
        if key == ord('q'):
            break

        log.debug(f'{pan}, {tilt}, {zoom}')


    del cam
    ptz.stop()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
