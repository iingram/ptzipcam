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

from camera import Camera

import movement_functions
import globals

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
USER = configs['USER']
PASS = configs['PASS']

with open('config_mow.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
HEADLESS = configs['HEADLESS']

# init global variables
globals.init()

if __name__ == '__main__':
    if CLIENT_MODE:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    window_name = 'Mow The Lawn'    
    # if not HEADLESS:
    #     cv2.namedWindow(window_name,
    #                     cv2.WINDOW_NORMAL)

        # cv2.setWindowProperty(window_name,
        #                       cv2.WND_PROP_FULLSCREEN,
        #                       cv2.WINDOW_FULLSCREEN)

        
    logging.basicConfig(level=logging.DEBUG, filename='log.log')

    movement_control_thread = threading.Thread(target=movement_functions.mow_the_lawn,
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

            if globals.camera_still:
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
