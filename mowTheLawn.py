import cv2
import numpy as np
import time

from ptz_camera import PtzCam

        
if __name__ == '__main__':
    ptzCam = PtzCam()

    key = 'd'

    x_dir = 0
    y_dir = 0

    count = 0

    # moves = [(-1, -1, 5),
    #          (1, -1, 5),
    #          (1, 0, 5),
    #          (-1, 0, 5)]

    ptzCam.absmove(-1, -1)
    time.sleep(5)
    
    step_dur = 1
    going_forward = True
    going_up = True
    
    while True:

        for y_pos in np.linspace(-1,0,10):
            if going_forward:
                for x_pos in np.linspace(-1,-.5,10):
                    ptzCam.absmove(x_pos, y_pos)
                    time.sleep(step_dur)
                    # ptzCam.stop()
                going_forward = not going_forward
            else:
                for x_pos in np.linspace(-.5,-1,10):
                    ptzCam.absmove(x_pos, y_pos)
                    time.sleep(step_dur)
                    # ptzCam.stop()
                going_forward = not going_forward

    ptzCam.stop()
           


    
