""" Allows mouse control of a PTZ-capable IP camera.

Doesn't display stream (which often is a good thing)

NOTE: if you want to display stream, can run separately something like:

ffplay -i rtsp://admin:NyalaChow22@192.168.0.64:554/Streaming/Channels/103
"""

import argparse

import yaml
import cv2
import numpy as np

from ptzipcam.ptz_camera import PtzCam

ap = argparse.ArgumentParser()
ap.add_argument('-c',
                '--config',
                default='../config.yaml',
                help='Configuration file.')
args = ap.parse_args()
config_file = args.config

with open(config_file) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
USER = configs['USER']
PASS = configs['PASS']
PORT = configs['PORT']

mouseX = 250
mouseY = 250


def get_mouse_coords(event, x, y, flags, param):
    """Callback For reading the mouse pointer coordinates
    """
    global mouseX
    global mouseY

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y


if __name__ == '__main__':
    ptz = PtzCam(IP, PORT, USER, PASS)

    key = 'd'
    canvas = np.zeros((500, 500), np.uint8)
    cv2.imshow('Control PTZ Camera', canvas)
    cv2.setMouseCallback('Control PTZ Camera', get_mouse_coords)

    x_dir = 0
    y_dir = 0

    while True:
        # print(f'mouseX: {mouseX}, mouseY: {mouseY}')
        key = cv2.waitKey(10)

        if key == ord('w'):
            break

        ptz.move(x_dir, y_dir)

        if(mouseX < 200):
            x_dir = -1
        elif(mouseX > 300):
            x_dir = 1
        else:
            x_dir = 0

        if(mouseY < 200):
            y_dir = 1
        elif(mouseY > 300):
            y_dir = -1
        else:
            y_dir = 0

        if x_dir == 0 and y_dir == 0:
            ptz.stop()

    cv2.destroyAllWindows()
    ptz.stop()
