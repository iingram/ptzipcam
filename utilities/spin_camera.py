"""Spins camera based off some "speed" given as cli argument.

Serves as an example of the basic bits to connect to and control a
camera using an concrete class of the MotorController class.

"""
import time
import argparse

import yaml
import numpy as np

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.ptz_camera import CalmMotorController
from ptzipcam import convert

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
parser.add_argument('-s',
                    '--speed',
                    required=True,
                    help='"Speed" to go. 200 is a good start.')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE, encoding='utf-8') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']

# ptz camera setup constants
INIT_POS = configs['INIT_POS']
CAM_ZOOM_POWER = configs['CAM_ZOOM_POWER']
ORIENTATION = configs['ORIENTATION']
PID_GAINS = configs['PID_GAINS']


def main():
    """Main function of the program

    """

    ptz = PtzCam(IP, PORT, USER, PASS)
    fake_frame = np.zeros([10, 10])
    motor_controller = CalmMotorController(PID_GAINS, ORIENTATION, fake_frame)

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    pan_init = convert.degrees_to_command(INIT_POS[0], 360.0)
    tilt_init = convert.degrees_to_command(INIT_POS[1], 90.0)
    zoom_init = convert.power_to_zoom(INIT_POS[2], CAM_ZOOM_POWER)

    print("Move to start position")
    ptz.absmove_w_zoom_waitfordone(pan_init,
                                   tilt_init,
                                   zoom_init,
                                   close_enough=.01)

    x_err = int(args.speed)
    y_err = 0

    while True:
        time.sleep(.1)
        # run position controller on ptz system
        commands = motor_controller.update(x_err,
                                           y_err,
                                           zoom_init)
        x_velocity, y_velocity, zoom_command = commands

        if x_velocity == 0 and y_velocity == 0:
            ptz.stop()

        ptz.move_w_zoom(x_velocity, y_velocity, zoom_command)

    ptz.stop()


if __name__ == '__main__':
    main()
