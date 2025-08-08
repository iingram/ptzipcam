"""Script to generate a timelapse with camera movement

Captures frames for a timelapse movie while moving the camera in a
prescribed manner so that in the resulting timelapse video the camera
is, for example, panning across the scene.

"""

import logging
import sys
import time
import threading
import socket
import pickle
import struct
import argparse

import cv2

from ptzipcam.camera import Camera
from ptzipcam import ui
from ptzipcam.io import ImageStreamRecorder, read_configs

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

ZOOM_POWER = 4.0

if args.host_ip:
    CLIENT_MODE = True
    HOST = args.host_ip
    PORT = int(args.port)
else:
    CLIENT_MODE = False

configs = read_configs(args.config_file_path)
timelapse_configs = read_configs(configs['TIMELAPSE_CONFIG_FILENAME'])

RECORD_FOLDER = configs['RECORD_FOLDER']
TIMELAPSE_CONFIG_FILENAME = configs['TIMELAPSE_CONFIG_FILENAME']

# ptz camera setup constants
ORIENTATION = configs['ORIENTATION']

# init global variables
globalvars.init()


class Sender():
    """Handles sending frames to a remote program."""

    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    def send(self, frame, pan_angle, tilt_angle):
        """Send frame and meta data over socket."""
        _, frame_to_send = cv2.imencode('.jpg',
                                        frame,
                                        self.encode_param)
        data = pickle.dumps(frame_to_send, 0)
        size = len(data)
        header = struct.pack(">Lff", size, pan_angle, tilt_angle)
        self.sock.sendall(header + data)

    def close(self):
        """Close socket."""
        self.sock.close()


if __name__ == '__main__':
    log.info("---- TIMELAPSE ----")
    log.info("Starting up.")
    if CLIENT_MODE:
        sender = Sender(HOST, PORT)

    WINDOW_NAME = "Timelapse View"
    if not configs['HEADLESS']:
        cv2.namedWindow(WINDOW_NAME,
                        cv2.WINDOW_NORMAL)

        cv2.setWindowProperty(WINDOW_NAME,
                              cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN)

    recorder = ImageStreamRecorder(RECORD_FOLDER)

    if timelapse_configs['MODE'] == 'mow':
        log.info("Movement function: Mow the lawn")
        movement_function = movement_functions.mow_the_lawn
    elif timelapse_configs['MODE'] == 'spots':
        log.info("Movement function: Visit spots")
        movement_function = movement_functions.visit_spots
    else:
        log.error("Invalid movement function specified in config file. "
                  "Quitting.")
        sys.exit()

    movement_control_thread = threading.Thread(target=movement_function,
                                               args=(ZOOM_POWER,
                                                     args.config_file_path),
                                               daemon=True)
    movement_control_thread.start()

    cam = Camera(
        configs['IP'],
        configs['USER'],
        configs['PASS'],
        configs['STREAM']
    )

    width, height = cam.get_resolution()

    hostname = socket.gethostname()

    time.sleep(1)

    # vid_writers = []
    # num_output_videos = np.prod(globalvars.grid)
    # print('Number of output videos is {}'.format(num_output_videos))
    # for i in range(num_output_videos):
    #     video_filename = ('video_timelapse_'
    #                       + timelapse_configs['MODE']
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

                    if not configs['HEADLESS']:
                        cv2.imshow(WINDOW_NAME, frame)
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

        if not configs['HEADLESS']:
            cv2.destroyAllWindows()

        sys.exit()
