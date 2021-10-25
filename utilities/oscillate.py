"""Oscillate PTZ camera back and forth

Takes a speed from the command line and then moves the camera back and
forth using the speed for a fixed number of seconds each way.

"""

import time
import argparse
import yaml

from ptzipcam import convert
from ptzipcam.ptz_camera import PtzCam

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
parser.add_argument('-s',
                    '--speed',
                    required=True,
                    help='"Speed" to go at (0.0-1.0)')
# parser.add_argument('-d',
#                     '--delta',
#                     required=True,
#                     help='Offset from start pan to pan to')
args = parser.parse_args()
CONFIG_FILE = args.config
# OFFSET = float(args.delta)

ZOOM_X_POWER = 25.0

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']

# ptz camera setup constants
INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']
PID_GAINS = configs['PID_GAINS']


def main():
    ptz = PtzCam(IP, PORT, USER, PASS)

    # initialize position of camera
    ptz.zoom_out_full()
    # time.sleep(3)
    pan_init = convert.degrees_to_command(INIT_POS[0], 360.0)
    tilt_init = convert.degrees_to_command(INIT_POS[1], 90.0)
    zoom_init = INIT_POS[2]/ZOOM_X_POWER

    # left_point = pan_init + OFFSET
    
    print("move to start position")
    ptz.absmove_w_zoom_waitfordone(pan_init,
                                   tilt_init,
                                   zoom_init,
                                   close_enough=.01)
    print("at start position")
    time.sleep(7)

    x_speed = float(args.speed)
    y_speed = 0

    going_left = False
    zoom_command = 0.0
    ptz.move_w_zoom(x_speed, y_speed, zoom_command)

    try:
        start = time.time()
        while True:
            if (time.time() - start) > 3:
                start = time.time()
                if going_left:
                    ptz.move_w_zoom(x_speed, y_speed, zoom_command)
                    going_left = False
                    print('now going right')
                elif not going_left:
                    ptz.move_w_zoom(-x_speed, y_speed, zoom_command)
                    going_left = True
                    print('now going left')

            # pan, tilt, zoom = ptz.get_position()
            # print(pan)
            # if going_left and pan > left_point:
            #     ptz.move_w_zoom(x_speed, y_speed, zoom_command)
            #     going_left = False
            #     print('now going right')
            # elif not going_left and pan < pan_init:
            #     ptz.move_w_zoom(-x_speed, y_speed, zoom_command)
            #     going_left = True
            #     print('now going left')
            time.sleep(.04)
    except KeyboardInterrupt:
        print('Received keyboard interrupt.')

    ptz.stop()


if __name__ == '__main__':
    main()
