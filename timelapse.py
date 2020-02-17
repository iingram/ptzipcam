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

from ptzipcam.camera import Camera
from ptzipcam import ui

import movement_functions
import globals

CONFIG_FILE = 'config.yaml'

NUM_OUTPUT_VIDEOS = 6
ZOOM_POWER = 4.0


if len(sys.argv) > 1:
    CLIENT_MODE = True
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
else:
    CLIENT_MODE = False

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
USER = configs['USER']
PASS = configs['PASS']

# ptz camera setup constants
ORIENTATION = configs['ORIENTATION']

with open('config_timelapse.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
HEADLESS = configs['HEADLESS']
MODE = configs['MODE']

# init global variables
globals.init()

class Sender():

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    def send(self, frame):
        result, frame_to_send = cv2.imencode('.jpg',
                                             frame,
                                             self.encode_param)
        data = pickle.dumps(frame_to_send, 0)
        size = len(data)
        self.sock.sendall(struct.pack(">L", size) + data)

    def close(self): 
        self.sock.close()       


if __name__ == '__main__':
    if CLIENT_MODE:
        sender = Sender(HOST, PORT)
        
    window_name = 'Mow The Lawn'    
    # if not HEADLESS:
    #     cv2.namedWindow(window_name,
    #                     cv2.WINDOW_NORMAL)

        # cv2.setWindowProperty(window_name,
        #                       cv2.WND_PROP_FULLSCREEN,
        #                       cv2.WINDOW_FULLSCREEN)

        
    logging.basicConfig(level=logging.DEBUG, filename='log.log')

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
                                               args=(ZOOM_POWER,),
                                               daemon=True)
    movement_control_thread.start()

    cam = Camera(ip=IP, user=USER, passwd=PASS)
    width, height = cam.get_resolution()

    hostname = socket.gethostname()

    vid_writers = []
    for i in range(NUM_OUTPUT_VIDEOS):
        video_filename = 'video_timelapse_' + MODE + '_' + hostname + '_' + str(i) + '.avi'
        vid_writers.append(cv2.VideoWriter(video_filename,
                                          cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                          30,
                                          (width, height)))
    time.sleep(1)

    latch = True

    j = 0
    try:
        while True:
            frame = cam.get_frame()
            if frame is None:
                print('Frame is None.')
            
            if globals.camera_still and frame is not None:
                if latch:
                    print('Taking a shot.')

                    frame = ui.orient_frame(frame, ORIENTATION)

                    if not HEADLESS:
                        cv2.imshow(window_name, frame)
                        key = cv2.waitKey(30)
                        if key == ord('q'):
                            break

                    vid_writers[j].write(frame.astype(np.uint8))
                    j += 1
                    if j == NUM_OUTPUT_VIDEOS:
                        j = 0
                    
                    latch = False
                    if CLIENT_MODE:
                        sender.send(frame)
            elif not latch:
                latch = True

    except KeyboardInterrupt:

        for i in range(NUM_OUTPUT_VIDEOS):
            vid_writers[i].release()
        
        cam.release()

        if CLIENT_MODE:
            sender.close()

        if not HEADLESS:
            cv2.destroyAllWindows()

        sys.exit()
