import time
import threading

import numpy as np

from ptz_camera import PtzCam

def mow_the_lawn():
    ptzCam = PtzCam()

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


if __name__ == '__main__':
    movement_control_thread = threading.Thread(target=mow_the_lawn,
                                               daemon=True)
    movement_control_thread.start()
    
    while True:
        pass
