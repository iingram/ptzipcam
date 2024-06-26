#!/usr/bin/env python
"""Utility to simply connect to a camera's video stream, display it,
and record it.

"""
import time
import logging
import argparse
import yaml

from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s (%(name)s)')

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
parser.add_argument('-s',
                    '--stream',
                    required=False,
                    help='Camera stream')
parser.add_argument('-n',
                    '--no_record',
                    action='store_true',
                    help='Override recording.')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE, encoding="utf-8") as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
RTSP_PORT = configs['RTSP_PORT']
CAM_BRAND = configs['CAM_BRAND']
USER = configs['USER']
PASS = configs['PASS']
if CAM_BRAND == 'hikvision':
    if args.stream:
        STREAM = args.stream
    else:
        STREAM = configs['STREAM']
else:
    STREAM = None

ORIENTATION = configs['ORIENTATION']
RECORD = configs['RECORD']
if args.no_record:
    RECORD = False
RECORD_FOLDER = configs['RECORD_FOLDER']

# GUI constants
HEADLESS = configs['HEADLESS']

FRAME_RATE = 12
TIME_BETWEEN_FRAMES = 1/FRAME_RATE


def main():
    """Main function of utility

    """
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
    logging.info('Resolution %dx%d', frame_width, frame_height)

    if RECORD:
        logging.info('Recording is ON.')
        recorder = ImageStreamRecorder(RECORD_FOLDER)
    else:
        logging.info('Recording is OFF.')

    start_time = time.time()
    while True:
        raw_frame = cam.get_frame()
        if raw_frame is None:
            logging.info('Frame is None.')
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
                                  (0.0, 0.0, 0.0),
                                  'N/A',
                                  0.0)

        elapsed = time.time() - start_time
        remainder = TIME_BETWEEN_FRAMES - elapsed
        logging.debug('Remainder is %d', remainder)
        if remainder > 0:
            time.sleep(remainder)
        else:
            logging.debug('Too much time elapsed between frames.')

        start_time = time.time()

    # cam.release()
    del cam
    if not HEADLESS:
        uih.clean_up()


if __name__ == "__main__":
    main()
