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

# PAN_MIN = -0.94
# PAN_MAX = -0.5
PAN_MIN = 30 # in degrees
PAN_MAX = 179 # in degrees
PAN_STEPS = 10 #400

STEP_DUR = 10

TILT_MIN = -44 # in degrees
TILT_MAX = 44 # in degrees
# TILT_MIN = .7
# TILT_MAX = .9
TILT_STEPS = 10


def mow_the_lawn():
    global camera_still
    ptzCam = PtzCam(IP, PORT, USER, PASS)

    ptzCam.absmove(PAN_MIN/180.0, TILT_MIN/45.0)
    time.sleep(3)

    going_forward = True
    going_up = True

    while True:
        if going_up:
            tilt_positions = np.linspace(TILT_MIN,
                                         TILT_MAX,
                                         TILT_STEPS)
        else:
            tilt_positions = np.linspace(TILT_MAX,
                                         TILT_MIN,
                                         TILT_STEPS)
        for y_pos in tilt_positions:
            if going_forward:
                pan_positions = np.linspace(PAN_MIN,
                                            PAN_MAX,
                                            PAN_STEPS)
            else:
                pan_positions = np.linspace(PAN_MAX,
                                            PAN_MIN,
                                            PAN_STEPS)
            for x_pos in pan_positions:
                ptzCam.absmove(x_pos/180.0, y_pos/45.0)
                print(f'Moving to pan {x_pos} and tilt {y_pos}.') 
                time.sleep(2)
                camera_still = True
                time.sleep(2)
                camera_still = False
                time.sleep(STEP_DUR)

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
