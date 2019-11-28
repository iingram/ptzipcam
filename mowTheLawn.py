import sys
import time
import threading
import socket
import logging
import pickle
import struct

import cv2
import yaml

import numpy as np

from ptz_camera import PtzCam
from camera import Camera

if len(sys.argv) > 1:
    CLIENT_MODE = True
    HOST = sys.argv[1]
    PORT = 8485
else:
    CLIENT_MODE = False

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
ONVIF_PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']

with open('config_mow.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
HEADLESS = configs['HEADLESS']
PAN_MIN = configs['PAN_MIN']
PAN_MAX = configs['PAN_MAX']
PAN_STEPS = configs['PAN_STEPS']
STEP_DUR = configs['STEP_DUR']
TILT_MIN = configs['TILT_MIN']
TILT_MAX = configs['TILT_MAX']
TILT_STEPS = configs['TILT_STEPS']

# global variables
camera_still = False


def convert_degrees_to_pan_command(degrees, full_range):
    if degrees > full_range:
        logging.error('Angle higher than full range')
        degrees = full_range
    elif degrees < 0.0:
        logging.error('Angle lower than zero')
        degrees = 0.0

    half_range = full_range/2.0
    return (degrees - half_range)/half_range


def convert_pan_command_to_degrees(command, full_range):
    half_range = full_range/2.0
    return command * half_range + half_range


def mow_the_lawn():
    """Thread function for moving the camera through a "mow the lawn"
    pattern: panning across, then tilting up a step, panning back, tilting
    up a step, etc.
    """
    global camera_still
    ptz = PtzCam(IP, ONVIF_PORT, USER, PASS)

    pan_min = convert_degrees_to_pan_command(PAN_MIN, 350.0)
    pan_max = convert_degrees_to_pan_command(PAN_MAX, 350.0)
    ptz.absmove(pan_min, TILT_MIN/45.0)
    time.sleep(3)

    going_forward = True
    going_up = True

    pan_pass_duration_estimate = int(((2 + 2 + STEP_DUR) * PAN_STEPS)/60)

    print('Will take about {} minutes to complete a pan pass.'.format(pan_pass_duration_estimate))

    while True:
        if going_up:
            tilt_positions = np.linspace(TILT_MIN,
                                         TILT_MAX,
                                         TILT_STEPS)
        else:
            tilt_positions = np.linspace(TILT_MAX,
                                         TILT_MIN,
                                         TILT_STEPS)
        for y_pos in tilt_positions:
            if going_forward:
                pan_positions = np.linspace(pan_min,
                                            pan_max,
                                            PAN_STEPS)
            else:
                pan_positions = np.linspace(pan_max,
                                            pan_min,
                                            PAN_STEPS)
            for x_pos in pan_positions:
                ptz.absmove(x_pos, y_pos/45.0)
                x_pos_degrees = convert_pan_command_to_degrees(x_pos, 350.0)
                print('Moving to {x_pos:.2f} degrees pan and {y_pos:.2f} degrees tilt.'.format(x_pos=x_pos_degrees, y_pos=y_pos))
                time.sleep(2)
                camera_still = True
                time.sleep(2)
                camera_still = False
                time.sleep(STEP_DUR)

            going_forward = not going_forward

        going_up = not going_up

    ptz.stop()


if __name__ == '__main__':
    if CLIENT_MODE:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    if not HEADLESS:
        window_name = 'Mow The Lawn'    
        cv2.namedWindow(window_name,
                        cv2.WINDOW_NORMAL)

        # cv2.setWindowProperty(window_name,
        #                       cv2.WND_PROP_FULLSCREEN,
        #                       cv2.WINDOW_FULLSCREEN)

        
    logging.basicConfig(level=logging.DEBUG, filename='log.log')

    movement_control_thread = threading.Thread(target=mow_the_lawn,
                                               daemon=True)
    movement_control_thread.start()

    cam = Camera(ip=IP, user=USER, passwd=PASS)
    width, height = cam.get_resolution()

    hostname = socket.gethostname()
    video_filename = 'video_mow_the_lawn_' + hostname + '.avi'
    vid_writer = cv2.VideoWriter(video_filename,
                                 cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                 30,
                                 (width, height))
    time.sleep(1)

    latch = True

    try:
        while True:
            frame = cam.get_frame()

            if camera_still:
                if latch:
                    if not HEADLESS:
                        cv2.imshow(window_name, frame)
                        key = cv2.waitKey(30)
                        if key == ord('q'):
                            break

                    vid_writer.write(frame.astype(np.uint8))
                    print('Taking a shot.')
                    latch = False
                    if CLIENT_MODE:
                        result, frame_to_send = cv2.imencode('.jpg',
                                                             frame,
                                                             encode_param)
                        data = pickle.dumps(frame_to_send, 0)
                        size = len(data)
                        sock.sendall(struct.pack(">L", size) + data)
            elif not latch:
                latch = True

    except KeyboardInterrupt:
        pass

    vid_writer.release()
    cam.release()

    if CLIENT_MODE:
        sock.close()

    if not HEADLESS:
        cv2.destroyAllWindows()
