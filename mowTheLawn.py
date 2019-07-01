import numpy as np
import time

from ptz_camera import PtzCam

if __name__ == '__main__':
    ptzCam = PtzCam()

    key = 'd'

    x_dir = 0
    y_dir = 0

    count = 0

    ptzCam.absmove(-1, -1)
    time.sleep(5)

    step_dur = 1
    going_forward = True
    going_up = True

    while True:
        if going_up:
            tilt_positions = np.linspace(-1, 0, 5)
        else:
            tilt_positions = np.linspace(0, -1, 5)
        for y_pos in tilt_positions:
            if going_forward:
                pan_positions = np.linspace(-1, -.5, 5)
            else:
                pan_positions = np.linspace(-.5, -1, 5)
            for x_pos in pan_positions:
                ptzCam.absmove(x_pos, y_pos)
                time.sleep(step_dur)
            going_forward = not going_forward
        going_up = not going_up

    ptzCam.stop()
