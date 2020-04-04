import os
import sys
import time
import threading
import socket
import pickle
import struct
import argparse

import cv2
import yaml

import numpy as np

from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder

import movement_functions
import globalvars

parser = argparse.ArgumentParser()
parser.add_argument('-c',
                    '--config',
                    default='config.yaml',
                    help='Filename of configuration file')
parser.add_argument('-i',
                    '--host_ip',
                    required=False,
                    help='Host IP to connect to if in client mode')
parser.add_argument('-p',
                    '--port',
                    required=False,
                    help='Port to use if in client mode')

args = parser.parse_args()

CONFIG_FILE = args.config

ZOOM_POWER = 4.0

if args.host_ip:
    CLIENT_MODE = True
    HOST = args.host_ip
    PORT = int(args.port)
else:
    CLIENT_MODE = False

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
USER = configs['USER']
PASS = configs['PASS']

TIMELAPSE_CONFIG_FILENAME = configs['TIMELAPSE_CONFIG_FILENAME']

# ptz camera setup constants
ORIENTATION = configs['ORIENTATION']

with open(TIMELAPSE_CONFIG_FILENAME) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
HEADLESS = configs['HEADLESS']
MODE = configs['MODE']

# init global variables
globalvars.init()


class Sender():

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    def send(self, frame, pan_angle, tilt_angle):
        result, frame_to_send = cv2.imencode('.jpg',
                                             frame,
                                             self.encode_param)
        data = pickle.dumps(frame_to_send, 0)
        size = len(data)
        header = struct.pack(">Lff", size, pan_angle, tilt_angle)
        self.sock.sendall(header + data)

    def close(self):
        self.sock.close()


if __name__ == '__main__':
    if CLIENT_MODE:
        sender = Sender(HOST, PORT)

    window_name = 'Mow The Lawn'
    # if not HEADLESS:
    #     cv2.namedWindow(window_name,
    #                     cv2.WINDOW_NORMAL)

    #     cv2.setWindowProperty(window_name,
    #                           cv2.WND_PROP_FULLSCREEN,
    #                           cv2.WINDOW_FULLSCREEN)

    # logging.basicConfig(level=logging.DEBUG, filename='/home/ian/timelapse.log')
    # logging.basicConfig(level=logging.DEBUG, filename='timelapse.log')
    # logging.debug('anything?')

    recorder = ImageStreamRecorder('/home/ian/special/')
    with open('/home/ian/timelapse.log', 'w') as f: f.write('[INFO] Just started.\n')
    
    preamble = 'Movement function:'
    if MODE == 'mow':
        print(preamble, 'Mow the lawn')
        movement_function = movement_functions.mow_the_lawn
    elif MODE == 'spots':
        print(preamble, 'Visit spots')
        movement_function = movement_functions.visit_spots
    else:
        print('Invalid movement function specified in config file.  Quitting.')
        sys.exit()

    movement_control_thread = threading.Thread(target=movement_function,
                                               args=(ZOOM_POWER, CONFIG_FILE),
                                               daemon=True)
    movement_control_thread.start()

    with open('/home/ian/timelapse.log', 'a') as f: f.write('[INFO] started movement control thread\n')
    
    cam = Camera(ip=IP, user=USER, passwd=PASS)
    width, height = cam.get_resolution()

    hostname = socket.gethostname()

    vid_writers = []

    time.sleep(1)
    num_output_videos = np.prod(globalvars.grid)
    print('Number of output videos is {}'.format(num_output_videos))
    for i in range(num_output_videos):
        video_filename = ('video_timelapse_'
                          + MODE
                          + '_'
                          + hostname
                          + '_'
                          + str(i)
                          + '.avi')

        video_filename = os.path.join('/home/ian/special/videos', video_filename)
        vid_writers.append(cv2.VideoWriter(video_filename,
                                           cv2.VideoWriter_fourcc(*'MJPG'),
                                           30,
                                           (width, height)))
    time.sleep(1)

    latch = True

    j = 0

    with open('/home/ian/timelapse.log', 'a') as f: f.write('[INFO] about to start main loop\n')
    
    try:
        while True:

            frame = cam.get_frame()
            if frame is None:
                print('Frame is None.')

            if globalvars.camera_still and frame is not None:
                if latch:
                    print('Taking a shot.')
                    with open('/home/ian/timelapse.log', 'a') as f: f.write('[INFO] taking a shot\n')

                    frame = ui.orient_frame(frame, ORIENTATION)

                    if not HEADLESS:
                        cv2.imshow(window_name, frame)
                        key = cv2.waitKey(30)
                        if key == ord('q'):
                            break

                    recorder.record_image(frame,
                                          globalvars.pan_angle,
                                          globalvars.tilt_angle)
                    
                    vid_writers[j].write(frame.astype(np.uint8))
                    j += 1
                    if j == num_output_videos:
                        j = 0

                    latch = False
                    if CLIENT_MODE:
                        sender.send(frame,
                                    globalvars.pan_angle,
                                    globalvars.tilt_angle)
            elif not latch:
                latch = True

    except KeyboardInterrupt:

        for i in range(num_output_videos):
            vid_writers[i].release()

        cam.release()

        if CLIENT_MODE:
            sender.close()

        if not HEADLESS:
            cv2.destroyAllWindows()

        sys.exit()
