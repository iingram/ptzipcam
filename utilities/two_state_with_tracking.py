import time
import argparse
import yaml
import curses
import random

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.ptz_camera import MotorController
from ptzipcam.tracker import Tracker

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    CONFIGS = yaml.load(f, Loader=yaml.SafeLoader)


class Behaver():

    def __init__(self, configs):
        self.tracker = Tracker(configs)
        self.state = 'search'
        
        # ptz camera networking constants
        IP = configs['IP']
        PORT = configs['PORT']
        USER = configs['USER']
        PASS = configs['PASS']

        # ptz camera setup constants
        INIT_POS = configs['INIT_POS']
        ORIENTATION = configs['ORIENTATION']
        PID_GAINS = configs['PID_GAINS']

        self.ptz = PtzCam(IP, PORT, USER, PASS)
        self.pan, self.tilt, self.zoom = self.ptz.get_position()
        self.motor_controller = MotorController(PID_GAINS, ORIENTATION)

        # initialize position of camera
        self.zoom_command = 0
        self.ptz.zoom_out_full()
        time.sleep(1)
        # pan, tilt, zoom = self.ptz.get_position()
        # ptz.absmove(INIT_POS[0], INIT_POS[1])
        pan_init = INIT_POS[0]/180.0
        tilt_init = INIT_POS[1]/45.0
        zoom_init = INIT_POS[2]/25.0

        print("move to start position")
        self.ptz.absmove_w_zoom_waitfordone(pan_init,
                                            tilt_init,
                                            zoom_init,
                                            close_enough=.01)

        self.x_err = 0
        self.y_err = 0

        self.x_velocity = 0
        self.y_velocity = 0

        self.updates_since_target = 0
        
    def update(self):
        self.tracker.update()
        # self.state = random.choice(['track', 'search'])
        if self.tracker.target_present:
            self.state = 'tracking'

            self.x_err, self.y_err = self.tracker.get_errors() 
            self._control()

            self.updates_since_target = 0
        else:
            self.state = 'searching'

            self.updates_since_target += 1
            if self.updates_since_target > 10:
                self.updates_since_target = 0
                self.x_velocity = -.3
                self.y_velocity = 0

        self._command()

    # def update(self):
    #     print('updating')
    #     self.state = random.choice(['track', 'search'])
    #     if self.state == 'track'
    #         self.switch_to_track()
    #     elsif self.state == 'search'
    #         self.switch_to_search()

    # def switch_to_search(self):
    #     self.x_velocity = -.3
    #     self._command()

    # def switch_to_track(self):
    #     self.x_err = -400
    #     self._control()
    #     self._command()

    def _control(self):
        command = self.motor_controller.run(self.x_err,
                                            self.y_err)
        self.x_velocity, self.y_velocity = command

    def _command(self):
        if self.x_velocity == 0 and self.y_velocity == 0 and self.zoom < 0.001:
            # print('stop action')
            self.ptz.stop()

        self.ptz.move_w_zoom(self.x_velocity,
                             self.y_velocity,
                             self.zoom_command)

    def __del__(self):
        self.ptz.stop()


def core_function(stdscr):
    key = None

    stdscr.clear()
    stdscr.refresh()
    stdscr.nodelay(1)

    behaver = Behaver(CONFIGS)

    while key != ord('q'):
        stdscr.clear()
        # time.sleep(2)

        behaver.update()
        stdscr.addstr(0, 0, behaver.state)
        stdscr.addstr(1, 0, str(behaver.tracker.target_present))
        stdscr.addstr(2, 0, str(behaver.x_err))
        stdscr.addstr(3, 0, str(behaver.tracker.detected_class))
        stdscr.addstr(4, 0, str(behaver.updates_since_target))

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        key = stdscr.getch()


def main():
    curses.wrapper(core_function)


if __name__ == '__main__':
    main()
