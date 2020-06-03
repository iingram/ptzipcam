"""Utility to simply connect to a camera's video stream, display it,
and record it.

"""

import argparse
import yaml

from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder

parser = argparse.ArgumentParser()
parser.add_argument('-c',
                    '--config',
                    default='../config.yaml',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
RTSP_PORT = configs['RTSP_PORT']
CAM_BRAND = configs['CAM_BRAND']
USER = configs['USER']
PASS = configs['PASS']
if CAM_BRAND == 'hikvision':
    STREAM = configs['STREAM']

ORIENTATION = configs['ORIENTATION']
RECORD = configs['RECORD']

# GUI constants
HEADLESS = configs['HEADLESS']

if __name__ == '__main__':
    # cam = Camera()
    cam = Camera(ip=IP,
                 user=USER,
                 passwd=PASS,
                 cam_brand=CAM_BRAND,
                 rtsp_port=RTSP_PORT,
                 stream=STREAM)

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    window_name = 'Display stream from IP Camera'

    if not HEADLESS:
        uih = ui.UI_Handler(frame, window_name)

    frame = cam.get_frame()
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]

    total_pixels = frame_width * frame_height

    if RECORD:
        recorder = ImageStreamRecorder('/home/ian/images_dtz')

    while True:
        raw_frame = cam.get_frame()
        if raw_frame is None:
            print('Frame is None.')
            continue

        raw_frame = ui.orient_frame(raw_frame, ORIENTATION)
        frame = raw_frame.copy()

        # update ui and handle user input

        if not HEADLESS:
            key = uih.update(frame, hud=False)
            if key == ord('q'):
                break

        if RECORD:
            recorder.record_image(frame,
                                  0.0,
                                  0.0,
                                  'N/A',
                                  0.0)

    cam.release()
    if not HEADLESS:
        uih.clean_up()
