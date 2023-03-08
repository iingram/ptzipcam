#!/usr/bin/env python
"""Aim PTZ camera using a curses keyboard interface

"""
import curses
import time
import argparse
from threading import Thread

import yaml
import cv2

from ptzipcam.camera import Camera
from ptzipcam.ptz_camera import PtzCam
from ptzipcam import ui, convert

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
parser.add_argument('-s',
                    '--stream',
                    default=None,
                    help='Stream to use if want to override config file.')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE, encoding="utf-8") as f:
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

HEADLESS = configs['HEADLESS']

# ptz camera setup constants
# INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']

INFINITE_PAN = configs['INFINITE_PAN']
CAM_TILT_MIN = configs['CAM_TILT_MIN']
CAM_TILT_MAX = configs['CAM_TILT_MAX']
CAM_PAN_MIN = configs['CAM_PAN_MIN']
CAM_PAN_MAX = configs['CAM_PAN_MAX']
CAM_ZOOM_MIN = configs['CAM_ZOOM_MIN']
CAM_ZOOM_MAX = configs['CAM_ZOOM_MAX']
CAM_ZOOM_POWER = configs['CAM_ZOOM_POWER']

Y_DELTA = .05
Y_DELTA_FINE = Y_DELTA/4
X_DELTA = .05
X_DELTA_FINE = .001
Z_DELTA = configs['CAM_ZOOM_STEP']
Z_DELTA_FINE = Z_DELTA / 3
E_DELTA = 1000.0
E_DELTA_FINE = 100.0
G_DELTA = 5.0
G_DELTA_FINE = 1.0
I_DELTA = 5.0
I_DELTA_FINE = 1.0
F_TIME = 1
F_TIME_FINE = .05

if ORIENTATION == 'down':
    Y_DELTA = -Y_DELTA
    Y_DELTA_FINE = -Y_DELTA_FINE
    X_DELTA = -X_DELTA
    X_DELTA_FINE = -X_DELTA_FINE

PTZ = PtzCam(IP, PORT, USER, PASS)

STATUS_BAR_STRING = ("PTZ: "
                     "Pan:j,l | "
                     "Tilt:i,k | "
                     "Zoom:z,x")
STATUS_BAR_STRING2 = ("EXPOSURE: "
                      "Toggle Autoexposure:e | "
                      "Time:t,y | "
                      "Gain:g,h | "
                      "Iris:b,n")
STATUS_BAR_STRING3 = ("OTHER: "
                      "Toggle Autofocus:f | "
                      "Focus:a,s | "
                      "Shift:finer | "
                      "Exit:q")


class CameraStreamDisplayer(Thread):
    """Handles capturing image from camera and display

    """

    def run(self):
        cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

        while True:
            # retrieve and display frame
            frame = cam.get_frame()
            if frame is not None:
                frame = ui.orient_frame(frame, ORIENTATION)
                cv2.imshow('Control PTZ Camera', frame)
                _ = cv2.waitKey(33)


def kchk(command,  # pylint: disable=too-many-arguments
         key,
         up_key,
         down_key,
         delta,
         delta_fine):
    """Parse keyboard input

    """
    if key == ord(up_key):
        command += delta
    elif key == ord(up_key.upper()):
        command += delta_fine
    elif key == ord(down_key):
        command -= delta
    elif key == ord(down_key.upper()):
        command -= delta_fine

    return command


def keep_in_bounds(command, minn, maxx):
    """Force command within bounds

    """
    if command <= minn:
        command = minn
    elif command >= maxx:
        command = maxx
    return command


def wrap_pan(command, minn, maxx):
    """Handle pan command crossing 0/360 angle

    """
    if command <= minn:
        command = maxx - minn + command
    elif command >= maxx:
        command = minn - maxx + command
    return command


def main_ui_function(stdscr):  # pylint: disable=R0912,R0914,R0915
    """Main curses UI function

    Renders all the UI elements for seeing state of the camera and
    commands for changing camera state.

    """

    pan, tilt, zoom = PTZ.get_position()
    pan_command = pan
    tilt_command = tilt
    zoom_command = zoom

    exposure_control_on = False
    focus_control_on = False
    # exptime, gain, iris = PTZ.get_exposure()
    # exp_command = exptime
    # gain_command = gain
    # iris_command = iris
    exp_command = 15000.0
    gain_command = 1.0
    iris_command = 0.0

    # PREP UI ELEMENTS
    key = '0'
    _, width = stdscr.getmaxyx()

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Declaration of strings
    title = "SageCam Test Tools Keyboard Control:"[:width-1]
    subtitle = "Aim PTZ IP Camera with Keyboard"[:width-1]
    usage_note = "(Only updates camera view once per keystroke)"[:width-1]

    # MAIN LOOP
    while key != ord('q'):

        # Initialization
        stdscr.clear()
        _, width = stdscr.getmaxyx()

        tilt_command = kchk(tilt_command, key, 'k', 'i', Y_DELTA, Y_DELTA_FINE)
        pan_command = kchk(pan_command, key, 'j', 'l', X_DELTA, X_DELTA_FINE)
        zoom_command = kchk(zoom_command, key, 'z', 'x', Z_DELTA, Z_DELTA_FINE)

        exp_command = kchk(exp_command, key, 'y', 't', E_DELTA, E_DELTA_FINE)
        gain_command = kchk(gain_command, key, 'h', 'g', G_DELTA, G_DELTA_FINE)
        iris_command = kchk(iris_command, key, 'n', 'b', I_DELTA, I_DELTA_FINE)

        if key == ord('e'):
            exposure_control_on = not exposure_control_on

            if not exposure_control_on:
                PTZ.set_exposure_to_auto()

        if key == ord('f'):
            focus_control_on = not focus_control_on

            if not focus_control_on:
                PTZ.set_focus_to_auto()
            else:
                PTZ.set_focus_to_manual()

        if key == ord('a'):
            PTZ.focus_in()
            time.sleep(F_TIME)
            PTZ.focus_stop()
        elif key == ord('a'.upper()):
            PTZ.focus_in()
            time.sleep(F_TIME_FINE)
            PTZ.focus_stop()
        elif key == ord('s'):
            PTZ.focus_out()
            time.sleep(F_TIME)
            PTZ.focus_stop()
        elif key == ord('s'.upper()):
            PTZ.focus_out()
            time.sleep(F_TIME_FINE)
            PTZ.focus_stop()

        if INFINITE_PAN:
            pan_command = wrap_pan(pan_command, CAM_PAN_MIN, CAM_PAN_MAX)
        else:
            pan_command = keep_in_bounds(pan_command, CAM_PAN_MIN, CAM_PAN_MAX)
        tilt_command = keep_in_bounds(tilt_command, CAM_TILT_MIN, CAM_TILT_MAX)
        zoom_command = keep_in_bounds(zoom_command, CAM_ZOOM_MIN, CAM_ZOOM_MAX)

        PTZ.absmove_w_zoom(pan_command,
                           tilt_command,
                           zoom_command)

        if exposure_control_on:
            PTZ.set_exposure_time(exp_command)
            PTZ.set_gain(gain_command)
            PTZ.set_iris(iris_command)
        try:
            # Render status bar
            stdscr.attron(curses.color_pair(3))
            # doing the exception as it appears to prevent a crashing bug
            # brought about when the window is resized so the width is
            # less than the status bar string
            stdscr.addstr(11, 0, STATUS_BAR_STRING)
            # stdscr.addstr(12,
            #               len(STATUS_BAR_STRING),
            #               " " * (width - len(STATUS_BAR_STRING) - 1))
            stdscr.addstr(12, 0, STATUS_BAR_STRING2)
            stdscr.addstr(13, 0, STATUS_BAR_STRING3)
            # stdscr.addstr(13,
            #               len(STATUS_BAR_STRING2),
            #               " " * (width - len(STATUS_BAR_STRING2) - 1))

            stdscr.attroff(curses.color_pair(3))

            # Curses title section
            stdscr.attron(curses.color_pair(2))
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(0, 0, title)

            stdscr.attroff(curses.color_pair(2))
            stdscr.attroff(curses.A_BOLD)
            stdscr.addstr(1, 0, subtitle)
            stdscr.addstr(2, 0, usage_note)
            # stdscr.addstr(3, 0, '-' * 31)

            # Write pan, tilt, zoom values
            pan_degrees = convert.command_to_degrees(pan_command, 360.0)
            strng = f"Pan: {pan_command:.3f} ({pan_degrees:.2f} degrees)"
            stdscr.addstr(4, 0, strng, curses.color_pair(4))

            tilt_degrees = convert.command_to_degrees(tilt_command, 90.0)
            strng = f"Tilt: {tilt_command:.3f} ({tilt_degrees:.2f} degrees)"
            stdscr.addstr(5, 0, strng, curses.color_pair(4))

            zoom_power = convert.zoom_to_power(zoom_command, CAM_ZOOM_POWER)
            strng = f"Zoom: {zoom_command:.3f} ({zoom_power:.2f} zoom)"
            stdscr.addstr(6, 0, strng, curses.color_pair(4))

            print(type(exp_command))
            strng = f"Exposure Time: {exp_command:.3f}"
            stdscr.addstr(7, 0, strng, curses.color_pair(1))

            strng = f"Exposure Gain: {gain_command:.3f}"
            stdscr.addstr(8, 0, strng, curses.color_pair(1))

            strng = f"Exposure Iris: {iris_command:.3f}"
            stdscr.addstr(9, 0, strng, curses.color_pair(1))

            strng = "Focus: Sorta unknown"
            stdscr.addstr(10, 0, strng, curses.color_pair(1))

        except curses.error as error_msg:
            print('Exception in curses loop')
            print(error_msg)
            try:
                strng = "MAKE WINDOW BIGGER"
                stdscr.addstr(1, 0, strng, curses.color_pair(1))
            except curses.error as deeper_error_msg:
                print('Window not even big enough for guidance.')
                print(deeper_error_msg)

        # hide cursor
        curses.curs_set(0)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        key = stdscr.getch()


def main():
    """Main executable function

    """

    if not HEADLESS:
        displayer = CameraStreamDisplayer()
        displayer.setDaemon(True)
        displayer.start()

    curses.wrapper(main_ui_function)

    # after curses closed print out PTZ values on CLI
    pan, tilt, zoom = PTZ.get_position()
    pan_deg = convert.command_to_degrees(pan, 360.0)
    tilt_deg = convert.command_to_degrees(tilt, 90.0)
    zoom_power = convert.zoom_to_power(zoom, CAM_ZOOM_POWER)

    print(f'Pan: {pan_deg:.2f} Tilt: {tilt_deg:.2f}, Zoom: {zoom_power:.2f}')

    if not HEADLESS:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
