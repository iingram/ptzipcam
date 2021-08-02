#!/usr/bin/env python
"""Aim PTZ camera using a curses keyboard interface

"""
import curses
import time
import yaml
import argparse
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

ptz = PtzCam(IP, PORT, USER, PASS)


def main_ui_function(stdscr):
    # PREP CAMERA CONTROL
    global ptz
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

    pan, tilt, zoom = ptz.get_position()
    pan_command = pan
    tilt_command = tilt
    zoom_command = zoom

    exposure_control_on = False
    focus_control_on = False
    # exptime, gain, iris = ptz.get_exposure()
    # exp_command = exptime
    # gain_command = gain
    # iris_command = iris
    exp_command = 15000.0
    gain_command = 1.0
    iris_command = 0.0

    # PREP UI ELEMENTS
    key = '0'
    height, width = stdscr.getmaxyx()

    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Declaration of strings
    title = "SageCam Test Tools Keyboard Control:"[:width-1]
    subtitle = "Aim PTZ IP Camera with Keyboard"[:width-1]
    usage_note = "(Only updates camera view once per keystroke)"[:width-1]
    statusbarstr = ("PTZ: "
                    "Pan:j,l | "
                    "Tilt:i,k | "
                    "Zoom:z,x")
    statusbarstr2 = ("EXPOSURE: "
                     "Toggle Autoexposure:e | "
                     "Time:t,y | "
                     "Gain:g,h | "
                     "Iris:b,n")
    statusbarstr3 = ("OTHER: "
                     "Toggle Autofocus:f | "
                     "Focus:a,s | "
                     "Shift:finer | "
                     "Exit:q")

    # MAIN LOOP
    while (key != ord('q')):
        # retrieve and display frame
        frame = None
        frame = cam.get_frame()
        if frame is not None:
            frame = ui.orient_frame(frame, ORIENTATION)
            if not HEADLESS:
                cv2.imshow('Control PTZ Camera', frame)
                _ = cv2.waitKey(33)
            else:
                time.sleep(.033)

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # parse keyboard input
        def kchk(command, key, up_key, down_key, delta, delta_fine):
            if key == ord(up_key):
                command += delta
            elif key == ord(up_key.upper()):
                command += delta_fine
            elif key == ord(down_key):
                command -= delta
            elif key == ord(down_key.upper()):
                command -= delta_fine

            return command

        tilt_command = kchk(tilt_command, key, 'k', 'i', Y_DELTA, Y_DELTA_FINE)
        pan_command = kchk(pan_command, key, 'j', 'l', X_DELTA, X_DELTA_FINE)
        zoom_command = kchk(zoom_command, key, 'z', 'x', Z_DELTA, Z_DELTA_FINE)

        exp_command = kchk(exp_command, key, 'y', 't', E_DELTA, E_DELTA_FINE)
        gain_command = kchk(gain_command, key, 'h', 'g', G_DELTA, G_DELTA_FINE)
        iris_command = kchk(iris_command, key, 'n', 'b', I_DELTA, I_DELTA_FINE)

        if key == ord('e'):
            exposure_control_on = not exposure_control_on

            if not exposure_control_on:
                ptz.set_exposure_to_auto()

        if key == ord('f'):
            focus_control_on = not focus_control_on

            if not focus_control_on:
                ptz.set_focus_to_auto()
            else:
                ptz.set_focus_to_manual()

        if key == ord('a'):
            ptz.focus_in()
            time.sleep(F_TIME)
            ptz.focus_stop()
        elif key == ord('a'.upper()):
            ptz.focus_in()
            time.sleep(F_TIME_FINE)
            ptz.focus_stop()
        elif key == ord('s'):
            ptz.focus_out()
            time.sleep(F_TIME)
            ptz.focus_stop()
        elif key == ord('s'.upper()):
            ptz.focus_out()
            time.sleep(F_TIME_FINE)
            ptz.focus_stop()

        def keep_in_bounds(command, minn, maxx):
            if command <= minn:
                command = minn
            elif command >= maxx:
                command = maxx
            return command

        def wrap_pan(command, minn, maxx):
            if command <= minn:
                command = maxx - minn + command
            elif command >= maxx:
                command = minn - maxx + command
            return command

        if INFINITE_PAN:
            pan_command = wrap_pan(pan_command, CAM_PAN_MIN, CAM_PAN_MAX)
        else:
            pan_command = keep_in_bounds(pan_command, CAM_PAN_MIN, CAM_PAN_MAX)
        tilt_command = keep_in_bounds(tilt_command, CAM_TILT_MIN, CAM_TILT_MAX)
        zoom_command = keep_in_bounds(zoom_command, CAM_ZOOM_MIN, CAM_ZOOM_MAX)

        ptz.absmove_w_zoom(pan_command,
                           tilt_command,
                           zoom_command)

        if exposure_control_on:
            ptz.set_exposure_time(exp_command)
            ptz.set_gain(gain_command)
            ptz.set_iris(iris_command)

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        # doing the exception as it appears to prevent a crashing bug
        # brought about when the window is resized so the width is
        # less than the status bar string
        try:
            stdscr.addstr(11, 0, statusbarstr)
            # stdscr.addstr(12,
            #               len(statusbarstr),
            #               " " * (width - len(statusbarstr) - 1))
            stdscr.addstr(12, 0, statusbarstr2)
            stdscr.addstr(13, 0, statusbarstr3)
            # stdscr.addstr(13,
            #               len(statusbarstr2),
            #               " " * (width - len(statusbarstr2) - 1))
        except Exception as e:
            print('Exception')
            print(e)

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
        strng = "Pan: {:.3f} ({:.1f} degrees)".format(pan_command,
                                                      pan_degrees)
        stdscr.addstr(4, 0, strng, curses.color_pair(1))

        tilt_degrees = convert.command_to_degrees(tilt_command, 90.0)
        strng = "Tilt: {:.3f} ({:.1f} degrees)".format(tilt_command,
                                                       tilt_degrees)
        stdscr.addstr(5, 0, strng, curses.color_pair(1))

        zoom_power = convert.zoom_to_power(zoom_command, CAM_ZOOM_POWER)
        strng = "Zoom: {:.3f} ({:.2f} zoom)".format(zoom_command,
                                                    zoom_power)
        stdscr.addstr(6, 0, strng, curses.color_pair(1))

        print(type(exp_command))
        strng = "Exposure Time: {:.3f}".format(exp_command)
        stdscr.addstr(7, 0, strng, curses.color_pair(1))

        strng = "Exposure Gain: {:.3f}".format(gain_command)
        stdscr.addstr(8, 0, strng, curses.color_pair(1))

        strng = "Exposure Iris: {:.3f}".format(iris_command)
        stdscr.addstr(9, 0, strng, curses.color_pair(1))

        strng = "Focus: Sorta unknown"
        stdscr.addstr(10, 0, strng, curses.color_pair(1))

        # hide cursor
        curses.curs_set(0)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        key = stdscr.getch()

    if not HEADLESS:
        cv2.destroyAllWindows()
    # cam.release()
    del cam


def main():
    global ptz

    curses.wrapper(main_ui_function)

    # after curses closed print out PTZ values on CLI
    pan, tilt, zoom = ptz.get_position()
    pan_deg = convert.command_to_degrees(pan, 360.0)
    tilt_deg = convert.command_to_degrees(tilt, 90.0)
    zoom_power = convert.zoom_to_power(zoom, CAM_ZOOM_POWER)

    print(f'Pan: {pan_deg:.2f} Tilt: {tilt_deg:.2f}, Zoom: {zoom_power:.1f}')


if __name__ == "__main__":
    main()
