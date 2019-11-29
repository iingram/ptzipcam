import socket
import struct
import pickle
import cv2

import screeninfo

import numpy as np

from dnntools import draw

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

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print('Socket created')

    s.bind((HOST, PORT))
    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    conn, addr = s.accept()
    print('Socket connection made')

    data = b""
    header_size = struct.calcsize(">L")
    print("header_size: {}".format(header_size))

    x = 0
    y = 0

    while True:
        # while len(data) < header_size:
        #     print("Recv: {}".format(len(data)))
        #     data += conn.recv(4096)

        # i commented out the above in favor of just the one line below
        # but i see now that the code below allows for the idea that some
        # of the payload data gets received in that first call to recv so
        # maybe there is some argument for doing it the way they had done
        # it?  One hiccup (but I haven't thought through this carefully)
        # could be that if a payload was smaller than the remainder of the
        # 4096 bytes that could cause a problem with their implementation?

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

        draw.image_onto_image(canvas, frame, (340*x, 260*y))
        x += 1
        if x >= 11:
            x = 0
            y += 1

        if y >= 8:
            y = 0

        cv2.imshow(window_name, canvas)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
