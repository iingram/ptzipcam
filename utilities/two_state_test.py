import time
import argparse
import yaml
import curses

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.ptz_camera import MotorController

parser = argparse.ArgumentParser()
parser.add_argument('config',
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

# ptz camera setup constants
INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']
PID_GAINS = configs['PID_GAINS']


def core_function(stdscr):
    key = None

    stdscr.clear()
    stdscr.refresh()

    ptz = PtzCam(IP, PORT, USER, PASS)
    motor_controller = MotorController(PID_GAINS, ORIENTATION)

    # initialize position of camera
    zoom_command = 0
    ptz.zoom_out_full()
    time.sleep(1)
    pan, tilt, zoom = ptz.get_position()
    # ptz.absmove(INIT_POS[0], INIT_POS[1])
    pan_init = INIT_POS[0]/180.0
    tilt_init = INIT_POS[1]/45.0
    zoom_init = INIT_POS[2]/25.0

    print("move to start position")
    ptz.absmove_w_zoom_waitfordone(pan_init,
                                   tilt_init,
                                   zoom_init,
                                   close_enough=.01)

    x_err = 400
    y_err = 0

    while key != ord('q'):
        stdscr.clear()
        time.sleep(.1)
        pan, tilt, zoom = ptz.get_position()
        # run position controller on ptz system
        x_velocity, y_velocity = motor_controller.run(x_err, y_err)
        if x_velocity == 0 and y_velocity == 0 and zoom < 0.001:
            # print('stop action')
            ptz.stop()

        ptz.move_w_zoom(x_velocity, y_velocity, zoom_command)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        key = stdscr.getch()

    ptz.stop()


def main():
    curses.wrapper(core_function)


if __name__ == '__main__':
    main()
