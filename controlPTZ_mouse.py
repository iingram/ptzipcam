import argparse

import yaml
import cv2
import numpy as np

from ptzipcam.ptz_camera import PtzCam

ap = argparse.ArgumentParser()
ap.add_argument('-c',
                '--config',
                default='config.yaml',
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


def getMouseCoords(event, x, y, flags, param):
    global mouseX
    global mouseY

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y


if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)

    key = 'd'
    canvas = np.zeros((500, 500), np.uint8)
    cv2.imshow('Control PTZ Camera', canvas)
    cv2.setMouseCallback('Control PTZ Camera', getMouseCoords)

    x_dir = 0
    y_dir = 0

    while True:
        # print(f'mouseX: {mouseX}, mouseY: {mouseY}')
        key = cv2.waitKey(10)

        if key == ord('w'):
            break

        ptzCam.move(x_dir, y_dir)

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
            ptzCam.stop()

    cv2.destroyAllWindows()
    ptzCam.stop()
