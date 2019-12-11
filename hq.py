import threading
import socket
import struct
import pickle
import cv2

import screeninfo

import numpy as np

from dnntools import draw
from viztools import visualization as viz

HOST = ''
PORT = 8485

window_name = "HQ"

screen_width = screeninfo.get_monitors()[0].width
screen_height = screeninfo.get_monitors()[0].height

cv2.namedWindow(window_name,
                cv2.WINDOW_NORMAL)

cv2.setWindowProperty(window_name,
                      cv2.WND_PROP_FULLSCREEN,
                      cv2.WINDOW_FULLSCREEN)

canvas = np.zeros((screen_height, screen_width, 3), np.uint8)

# cv2.imshow(window_name, canvas)
# cv2.waitKey(1)

frame = canvas

pics = []

def socket_function():
    global pics
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print('Socket created')

        s.bind((HOST, PORT))
        print('Socket bind complete')
        s.listen(10)
        print('Socket now listening on port', PORT)

        conn, addr = s.accept()
        print('Socket connection made')

        data = b""
        header_size = struct.calcsize(">L")
        print("header_size: {}".format(header_size))

        while True:
            data += conn.recv(header_size)

            # if no data, quit.  is there a gotcha here?
            if len(data) == 0:
                break

            print("Done Recv: {}".format(len(data)))
            header = data[:header_size]
            data = data[header_size:]
            msg_size = struct.unpack(">L", header)[0]
            print("msg_size: {}".format(msg_size))
            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            pics.append(viz.FlyingGrowingPicBox(frame,
                                                np.array((0,0)),
                                                np.array((1500, 1500)),
                                                200,
                                                75))

            
            
socket_thread = threading.Thread(target=socket_function,
                                 daemon=True)
socket_thread.start()

x = 0
y = 0

while True:
    canvas = np.zeros((screen_height, screen_width, 3), np.uint8)

    for pic in pics:
        pic.update()
        pic.display(canvas)
    
    # draw.image_onto_image(canvas, frame, (340*x, 260*y))
    # x += 1
    # if x >= 11:
    #     x = 0
    #     y += 1

    # if y >= 8:
    #     y = 0

    cv2.imshow(window_name, canvas)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
