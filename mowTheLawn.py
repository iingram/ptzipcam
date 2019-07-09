import time
import threading

import cv2

import numpy as np

from ptz_camera import PtzCam
from camera import Camera

IP = "192.168.1.64"   # Camera IP address
PORT = 80           # Port
USER = "admin"         # Username
PASS = "NyalaChow22"        # Password

camera_still = False


def mow_the_lawn():
    global camera_still
    ptzCam = PtzCam(IP, PORT, USER, PASS)

    ptzCam.absmove(-1, -1)
    time.sleep(2)

    step_dur = 2
    going_forward = True
    going_up = True

    while True:
        if going_up:
            tilt_positions = np.linspace(-.55, 0, 10)
        else:
            tilt_positions = np.linspace(0, -.55, 10)
        for y_pos in tilt_positions:
            if going_forward:
                pan_positions = np.linspace(-.94, -.5, 400)
            else:
                pan_positions = np.linspace(-.5, -.94, 400)
            for x_pos in pan_positions:
                ptzCam.absmove(x_pos, y_pos)
                time.sleep(step_dur)
                camera_still = True
                time.sleep(1)
                camera_still = False

            going_forward = not going_forward
        going_up = not going_up

    ptzCam.stop()


if __name__ == '__main__':
    movement_control_thread = threading.Thread(target=mow_the_lawn,
                                               daemon=True)
    movement_control_thread.start()

    cam = Camera()

    width, height = cam.get_resolution()

    vid_writer = cv2.VideoWriter('output.avi',
                                 cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                 30,
                                 (width, height))
    time.sleep(1)

    latch = True

    while True:
        frame = cam.get_frame()
        cv2.imshow('Mow The Lawn', frame)
        key = cv2.waitKey(30)
        if key == ord('q'):
            break

        if camera_still:
            if latch:
                vid_writer.write(frame.astype(np.uint8))
                print('Taking a shot.')
                latch = False
        elif not latch:
            latch = True

    vid_writer.release()
    cam.release()
    cv2.destroyAllWindows()
