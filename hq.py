import threading
import socket
import struct
import pickle
import argparse

import cv2
import imutils

import numpy as np

from dnntools import draw
from viztools import visualization as viz

import viz_hq 

parser = argparse.ArgumentParser()
parser.add_argument('-p',
                    '--port',
                    required=True,
                    help='Port for socket connection')
args = parser.parse_args()

JUMP_SCREENS = False
NUM_COLS = 10
NUM_ROWS = 7
COL_WIDTH = 330
ROW_HEIGHT = 250
NUM_SPOTS = NUM_ROWS * NUM_COLS

HOST = ''
PORT = int(args.port)

WINDOW_NAME = "HQ"
display = viz_hq.Display(WINDOW_NAME, JUMP_SCREENS)

flypics = []
pics = []

for i in range(NUM_SPOTS):
    pics.append(list())

layout = viz_hq.create_layout(NUM_ROWS, NUM_COLS, COL_WIDTH, ROW_HEIGHT)
print('Grid: ' + str(NUM_COLS) + 'x' + str(NUM_ROWS))


def socket_function():
    global flypics, pics

    header_format = '>Lff'
    header_size = struct.calcsize(header_format)
    print("header_size: {}".format(header_size))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print('Socket created')

        s.bind((HOST, PORT))
        print('Socket bound')
        s.listen(10)
        print('Socket now listening on port', PORT)

        conn, addr = s.accept()
        print('Socket connection made')

        data = b""

        spot = 0

        # total_spots = NUM_ROWS * NUM_COLS

        spot_count = 0
        while True:
            data += conn.recv(header_size)

            # if no data, quit.  is there a gotcha here?
            if len(data) == 0:
                break

            print("Done Recv: {}".format(len(data)))
            header = data[:header_size]
            data = data[header_size:]
            msg_size, pan_angle, tilt_angle = struct.unpack(header_format, header)
            print("msg_size: {}".format(msg_size))
            print("pan_angle: {:.2f}".format(pan_angle))
            print("tilt_angle: {:.2f}".format(tilt_angle))
            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data,
                                 fix_imports=True,
                                 encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            frame = imutils.resize(frame, width=320)

            flypics.append(viz.FlyingPicBox(frame,
                                            np.array([layout[spot_count][0], 0]),
                                            np.array(layout[spot_count])))
            spot_count += 1
            if spot_count >= NUM_SPOTS:
                spot_count = 0

            pics[spot].append(frame)
            spot += 1
            if spot >= NUM_SPOTS:
                spot = 0


socket_thread = threading.Thread(target=socket_function,
                                 daemon=True)
socket_thread.start()

counts = []
for i in range(NUM_SPOTS):
    counts.append(0)

while True:
    display.refresh_canvas()
    
    for pic in flypics:
        pic.update()
        pic.display(display.canvas)

    if len(flypics) > 10:
        flypics = flypics[1:]

    for i in range(NUM_SPOTS):
        counts[i] += 1
        if counts[i] > len(pics[i]) - 1:
            counts[i] = 0

        if len(pics[i]):
            draw.image_onto_image(display.canvas,
                                  pics[i][counts[i]],
                                  layout[i])
                                  # (i * (10 + pics[i][0].shape[1]),
                                  #  260))

    key = display.draw()
    if key == ord('q'):
        break
