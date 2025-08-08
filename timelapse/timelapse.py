import logging
import sys
import time
import threading
import socket
import pickle
import struct
import argparse

import cv2
import yaml

from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder

import movement_functions
import globalvars

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(message)s (%(name)s)')
log = logging.getLogger('main')

parser = argparse.ArgumentParser()
parser.add_argument('config_file_path',
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

CONFIG_FILE = args.config_file_path

ZOOM_POWER = 4.0

if args.host_ip:
    CLIENT_MODE = True
    HOST = args.host_ip
    PORT = int(args.port)
else:
    CLIENT_MODE = False

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
USER = configs['USER']
PASS = configs['PASS']
STREAM = configs['STREAM']

RECORD_FOLDER = configs['RECORD_FOLDER']
TIMELAPSE_CONFIG_FILENAME = configs['TIMELAPSE_CONFIG_FILENAME']

# ptz camera setup constants
ORIENTATION = configs['ORIENTATION']

with open(TIMELAPSE_CONFIG_FILENAME, 'r', encoding='utf-8') as f:
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
        _, frame_to_send = cv2.imencode('.jpg',
                                        frame,
                                        self.encode_param)
        data = pickle.dumps(frame_to_send, 0)
        size = len(data)
        header = struct.pack(">Lff", size, pan_angle, tilt_angle)
        self.sock.sendall(header + data)

    def close(self):
        self.sock.close()


if __name__ == '__main__':
    log.info("---- TIMELAPSE ----")
    log.info("Starting up.")
    if CLIENT_MODE:
        sender = Sender(HOST, PORT)

    window_name = 'Mow The Lawn'
    # if not HEADLESS:
    #     cv2.namedWindow(window_name,
    #                     cv2.WINDOW_NORMAL)

    #     cv2.setWindowProperty(window_name,
    #                           cv2.WND_PROP_FULLSCREEN,
    #                           cv2.WINDOW_FULLSCREEN)

    recorder = ImageStreamRecorder(RECORD_FOLDER)

    if MODE == 'mow':
        log.info("Movement function: Mow the lawn")
        movement_function = movement_functions.mow_the_lawn
    elif MODE == 'spots':
        log.info("Movement function: Visit spots")
        movement_function = movement_functions.visit_spots
    else:
        log.error("Invalid movement function specified in config file.  Quitting.")
        sys.exit()

    movement_control_thread = threading.Thread(target=movement_function,
                                               args=(ZOOM_POWER, CONFIG_FILE),
                                               daemon=True)
    movement_control_thread.start()

    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)
    width, height = cam.get_resolution()

    hostname = socket.gethostname()

    time.sleep(1)

    # vid_writers = []
    # num_output_videos = np.prod(globalvars.grid)
    # print('Number of output videos is {}'.format(num_output_videos))
    # for i in range(num_output_videos):
    #     video_filename = ('video_timelapse_'
    #                       + MODE
    #                       + '_'
    #                       + hostname
    #                       + '_'
    #                       + str(i)
    #                       + '.avi')

    #     video_filename = os.path.join('/home/ian/special/videos',
    #                                   video_filename)
    #     vid_writers.append(cv2.VideoWriter(video_filename,
    #                                        cv2.VideoWriter_fourcc(*'MJPG'),
    #                                        30,
    #                                        (width, height)))
    time.sleep(1)

    latch = True

    try:
        while True:

            frame = cam.get_frame()
            if frame is None:
                log.warning('Frame is None.')

            if globalvars.camera_still and frame is not None:
                if latch:
                    log.info("Capturing an image.")

                    frame = ui.orient_frame(frame, ORIENTATION)

                    if not HEADLESS:
                        cv2.imshow(window_name, frame)
                        key = cv2.waitKey(30)
                        if key == ord('q'):
                            break

                    recorder.record_image(frame,
                                          (globalvars.pan_angle,
                                           globalvars.tilt_angle,
                                           -1),
                                          'N/A',
                                          0.0)

                    # vid_writers[j].write(frame.astype(np.uint8))
                    # j += 1
                    # if j == num_output_videos:
                    #     j = 0

                    latch = False
                    if CLIENT_MODE:
                        sender.send(frame,
                                    globalvars.pan_angle,
                                    globalvars.tilt_angle)
            elif not latch:
                latch = True

    except KeyboardInterrupt:

        # for i in range(num_output_videos):
        #     vid_writers[i].release()

        del cam

        if CLIENT_MODE:
            sender.close()

        if not HEADLESS:
            cv2.destroyAllWindows()

        sys.exit()
