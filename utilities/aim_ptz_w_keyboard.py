import time
import yaml
import argparse

import cv2

from ptzipcam.camera import Camera
from ptzipcam.ptz_camera import PtzCam
from ptzipcam import ui

parser = argparse.ArgumentParser()
parser.add_argument('-c',
                    '--config',
                    default='../config.yaml',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
STREAM = configs['STREAM']

# ptz camera setup constants
# INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']

cam = Camera(ip=IP, user=USER, passwd=PASS, stream=2)

Y_DELTA = .1
Y_DELTA_FINE = .001
X_DELTA = .1
X_DELTA_FINE = .001
Z_DELTA = .1

if __name__ == '__main__':
    ptz = PtzCam(IP, PORT, USER, PASS)

    # pan_command = INIT_POS[0]/180.0
    # tilt_command = INIT_POS[1]/45.0
    # zoom_command = INIT_POS[2]/25.0

    # ptz.absmove_w_zoom_waitfordone(pan_command,
    #                                tilt_command,
    #                                zoom_command,
    #                                close_enough=.01)

    pan, tilt, zoom = ptz.get_position()
    pan_command = pan
    tilt_command = tilt
    zoom_command = zoom

    key = 'd'

    print("Keys:\n",
          "w: quit\n",
          "y: tilt up (fine)\n",
          "u: tilt up\n",
          "i: tilt down\n",
          "o: tilt down (fine)\n",
          "h: pan left (fine)\n",
          "j: pan left\n",
          "k: pan right\n",
          "l: pan right (fine)\n",
          "a: focus in (fine)\n",
          "s: focus in \n",
          "d: focus out \n",
          "f: focus out (fine)\n",
          "x: zoom in \n",
          "c: zoom out \n")

    while True:

        if key == ord('w'):
            break
        elif key == ord('y'):
            # tilt up fine
            tilt_command -= Y_DELTA_FINE
        elif key == ord('u'):
            # tilt up
            tilt_command -= Y_DELTA
        elif key == ord('i'):
            # tilt down
            tilt_command += Y_DELTA
        elif key == ord('o'):
            # tilt down fine
            tilt_command += Y_DELTA_FINE
        elif key == ord('h'):
            # pan right fine
            pan_command += X_DELTA_FINE
        elif key == ord('j'):
            # pan right
            pan_command += X_DELTA
        elif key == ord('k'):
            # pan left
            pan_command -= X_DELTA
        elif key == ord('l'):
            # pan left fine
            pan_command -= X_DELTA_FINE
        elif key == ord('a'):
            # focus in fine
            ptz.focus_in()
            time.sleep(0.5)
            ptz.focus_stop()
        elif key == ord('s'):
            # focus in
            ptz.focus_in()
            time.sleep(1)
            ptz.focus_stop()
        elif key == ord('d'):
            # focus out
            ptz.focus_out()
            time.sleep(1)
            ptz.focus_stop()
        elif key == ord('f'):
            # focus out fine
            ptz.focus_out()
            time.sleep(.5)
            ptz.focus_stop()
        elif key == ord('z'):
            # zoom in fine
            zoom_command += X_DELTA_FINE
        elif key == ord('x'):
            # zoom in
            zoom_command += X_DELTA
        elif key == ord('c'):
            # zoom out
            zoom_command -= X_DELTA
        elif key == ord('v'):
            # zoom out fine
            zoom_command -= X_DELTA_FINE
        elif key == ord('u'):
            pass

        def keep_in_bounds(command, minn, maxx):
            if command <= minn:
                command = minn
            elif command >= maxx:
                command = maxx
            return command

        pan_command = keep_in_bounds(pan_command, -1.0, 1.0)
        tilt_command = keep_in_bounds(tilt_command, 0.0, 1.0)
        zoom_command = keep_in_bounds(zoom_command, 0.0, 1.0)

        ptz.absmove_w_zoom(pan_command,
                           tilt_command,
                           zoom_command)

        print("Pan: {:.2f}, Tilt: {:.2f}, Zoom: {:.2f}".format(pan_command,
                                                               tilt_command,
                                                               zoom_command))

        frame = None
        frame = cam.get_frame()
        if frame is not None:
            frame = ui.orient_frame(frame, ORIENTATION)
            cv2.imshow('Control PTZ Camera', frame)
            key = cv2.waitKey(0)

    cv2.destroyAllWindows()
