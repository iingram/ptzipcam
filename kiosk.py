import logging
import os
import argparse
import threading
import socket
import struct
import pickle
import cv2

import yaml
import screeninfo

import numpy as np

from dnntools import draw
from dnntools import neuralnetwork as nn
from viztools import visualization as viz

logging.basicConfig(level='DEBUG',
                    format='[%(levelname)s] %(message)s (%(name)s)')

log = logging.getLogger('main')

JUMP_SCREENS = False

# IMAGE_PATH = '/home/ian/Desktop/outreach_day/raw'
IMAGE_PATH = '/home/ian/media/test'

if os.path.exists(IMAGE_PATH):
    log.info('Path exists.')
else:
    log.warning('Image path does not exist')

parser = argparse.ArgumentParser(
    description="Spotter")

parser.add_argument('config',
                    default='config.yaml',
                    help='Path to config file.')

parser.add_argument('-p',
                    '--port',
                    default='65432',
                    help='Port number to use.')

args = parser.parse_args()

with open(args.config) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

TRACKED_CLASS = configs['TRACKED_CLASS']

confThreshold = configs['CONF_THRESHOLD']
nmsThreshold = configs['NMS_THRESHOLD']
input_width = configs['INPUT_WIDTH']
input_height = configs['INPUT_HEIGHT']

model_path = configs['MODEL_PATH']
CLASSES_FILE = configs['CLASS_NAMES_FILE']
model_config = configs['MODEL_CONFIG_FILE']
model_weights = configs['MODEL_WEIGHTS_FILE']


HOST = ''
PORT = int(args.port)

window_name = "HQ"

cv2.namedWindow(window_name,
                cv2.WINDOW_NORMAL)

screen_resolutions = screeninfo.get_monitors()
screen_width = screen_resolutions[0].width
screen_height = screen_resolutions[0].height

if JUMP_SCREENS:
    log.info("Expecting that a second screen is attached.")
    main_screen_width = screen_resolutions[1].width

    cv2.moveWindow(window_name,
                   main_screen_width,
                   0)

cv2.setWindowProperty(window_name,
                      cv2.WND_PROP_FULLSCREEN,
                      cv2.WINDOW_FULLSCREEN)

canvas = np.zeros((screen_height, screen_width, 3), np.uint8)

# cv2.imshow(window_name, canvas)
# cv2.waitKey(1)

frame = canvas

flypics = []

pics = []

num_spots = 3
for i in range(num_spots):
    pics.append(list())

CLASSES = nn.read_classes_from_file(os.path.join(model_path, CLASSES_FILE))
network = nn.ObjectDetectorHandler(os.path.join(model_path, model_config),
                                   os.path.join(model_path, model_weights),
                                   input_width,
                                   input_height)

# animal images from disk
images = []
for root, dirs, files in os.walk(IMAGE_PATH):
    for filename in files:
        endings = (".jpg", '.JPG', '.jpeg', '.png', '.JPEG')
        if filename.endswith(endings):
            img = cv2.imread(os.path.join(root, filename))
            # img = imutils.resize(img, width=640)
            img = cv2.resize(img, (640, 480))
            images.append(img)

log.info("Number of images from disk is: " + str(len(images)))
count = 0


def socket_function():
    global flypics, pics, images, count

    header_format = '>Lff'

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(10)
        log.info(f'Socket now listening on port {PORT}')

        conn, addr = s.accept()
        log.info('Socket connection made')

        data = b""
        header_size = struct.calcsize(header_format)
        log.info("header_size: {}".format(header_size))

        spot = 0
        while True:
            data += conn.recv(header_size)

            # if no data, quit.  is there a gotcha here?
            if len(data) == 0:
                break

            log.info("Done Recv: {}".format(len(data)))
            header = data[:header_size]
            data = data[header_size:]
            msg_size, pan_angle, tilt_angle = struct.unpack(header_format,
                                                            header)
            log.info("msg_size: {}".format(msg_size))
            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data,
                                 fix_imports=True,
                                 encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            log.info(frame.shape)

            def boxify(the_image):
                outs, inferenceTime = network.infer(the_image)
                lboxes = network.filter_boxes(outs,
                                              the_image,
                                              confThreshold,
                                              nmsThreshold)

                for lbox in lboxes:
                    if CLASSES[lbox['class_id']] in TRACKED_CLASS:
                        draw.labeled_box(the_image, CLASSES, lbox, thickness=2)

            boxify(frame)

            flypics.append(viz.FlyingPicBox(frame,
                                            np.array(((10 + 640)*spot, 0)),
                                            np.array(((10 + 640)*spot, 70))))

            img = images[count].copy()
            count += 1
            if count >= len(images):
                count = 0

            boxify(img)

            flypics.append(viz.FlyingPicBox(img,
                                            np.array(((10 + 640)*spot, 1000)),
                                            np.array(((10 + 640)*spot, 650))))

            pics[spot].append(frame)
            spot += 1
            if spot >= num_spots:
                spot = 0


socket_thread = threading.Thread(target=socket_function,
                                 daemon=True)
socket_thread.start()

x = 0
y = 0

counts = []
for i in range(num_spots):
    counts.append(0)

while True:
    canvas = np.zeros((screen_height, screen_width, 3), np.uint8)

    for pic in flypics:
        pic.update()
        pic.display(canvas)

    if len(flypics) > 10:
        flypics = flypics[1:]

    for i in range(num_spots):
        counts[i] += 1
        if counts[i] > len(pics[i]) - 1:
            counts[i] = 0

    cv2.imshow(window_name, canvas)
    key = cv2.waitKey(30)
    if key == ord('q'):
        break
