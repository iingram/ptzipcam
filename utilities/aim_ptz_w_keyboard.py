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
parser.add_argument('-s',
                    '--stream',
                    default=None,
                    help='Stream to use if want to override config file.')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
if args.stream is None:
    STREAM = configs['STREAM']
else:
    STREAM = int(args.stream)
    
# ptz camera setup constants
# INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']

cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

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

    keys = ['w',
            'a','s','d','f',
            'h','j','k','l',
            'y','u','i','o',
            'z','x','c','v',
            'd']

    print("Keys:\n",
          keys[0] + ": quit\n",
          keys[1] + ": tilt up (fine)\n",
          keys[2] + ": tilt up\n",
          keys[3] + ": tilt down\n",
          keys[4] + ": tilt down (fine)\n",
          keys[5] + ": pan left (fine)\n",
          keys[6] + ": pan left\n",
          keys[7] + ": pan right\n",
          keys[8] + ": pan right (fine)\n",
          keys[9] + ": focus in (fine)\n",
          keys[10] + ": focus in \n",
          keys[11] + ": focus out \n",
          keys[12] + ": focus out (fine)\n",
          keys[13] + ": zoom out fine \n",
          keys[14] + ": zoom out  \n",
          keys[15] + ": zoom in \n",
          keys[16] + ": zoom in fine \n",
          keys[17] + ": update frame")

    while True:

        if key == ord(keys[0]):
            break
        elif key == ord(keys[1]):
            # tilt up fine
            tilt_command -= Y_DELTA_FINE
        elif key == ord(keys[2]):
            # tilt up
            tilt_command -= Y_DELTA
        elif key == ord(keys[3]):
            # tilt down
            tilt_command += Y_DELTA
        elif key == ord(keys[4]):
            # tilt down fine
            tilt_command += Y_DELTA_FINE
        elif key == ord(keys[5]):
            # pan right fine
            pan_command += X_DELTA_FINE
        elif key == ord(keys[6]):
            # pan right
            pan_command += X_DELTA
        elif key == ord(keys[7]):
            # pan left
            pan_command -= X_DELTA
        elif key == ord(keys[8]):
            # pan left fine
            pan_command -= X_DELTA_FINE
        elif key == ord(keys[9]):
            # focus in fine
            ptz.focus_in()
            time.sleep(0.5)
            ptz.focus_stop()
        elif key == ord(keys[10]):
            # focus in
            ptz.focus_in()
            time.sleep(1)
            ptz.focus_stop()
        elif key == ord(keys[11]):
            # focus out
            ptz.focus_out()
            time.sleep(1)
            ptz.focus_stop()
        elif key == ord(keys[12]):
            # focus out fine
            ptz.focus_out()
            time.sleep(.5)
            ptz.focus_stop()
        elif key == ord(keys[13]):
            # zoom in fine
            zoom_command -= X_DELTA_FINE
        elif key == ord(keys[14]):
            # zoom in
            zoom_command -= X_DELTA
        elif key == ord(keys[15]):
            # zoom out
            zoom_command += X_DELTA
        elif key == ord(keys[16]):
            # zoom out fine
            zoom_command += X_DELTA_FINE
        elif key == ord(keys[17]):
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

        print("Pan: {:.3f}, Tilt: {:.3f}, Zoom: {:.3f}".format(pan_command,
                                                               tilt_command,
                                                               zoom_command))

        frame = None
        frame = cam.get_frame()
        if frame is not None:
            frame = ui.orient_frame(frame, ORIENTATION)
            cv2.imshow('Control PTZ Camera', frame)
            key = cv2.waitKey(0)

    cv2.destroyAllWindows()
    # cam.release()
    del cam
    del ptz
