import curses
import time
import yaml
import argparse
import cv2

from ptzipcam.camera import Camera
from ptzipcam.ptz_camera import PtzCam
from ptzipcam import ui

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

# ptz camera setup constants
# INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']

Y_DELTA = .05
Y_DELTA_FINE = .001
X_DELTA = .05
X_DELTA_FINE = .001
Z_DELTA = .01
Z_DELTA_FINE = .004
F_TIME = 1
F_TIME_FINE = .05

if ORIENTATION == 'down':
    Y_DELTA = -Y_DELTA
    Y_DELTA_FINE = -Y_DELTA_FINE
    X_DELTA = -X_DELTA
    X_DELTA_FINE = -X_DELTA_FINE


def main_ui_function(stdscr):
    # PREP CAMERA CONTROL
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

    pan, tilt, zoom = ptz.get_position()
    pan_command = pan
    tilt_command = tilt
    zoom_command = zoom

    # PREP UI ELEMENTS
    key = 0
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
    title = "SageCam Keyboard Control:"[:width-1]
    subtitle = "Aim PTZ IP Camera with Keyboard"[:width-1]
    statusbarstr = ("Pan: j,l |"
                    "Tilt: i,k |"
                    "Zoom: z,x |"
                    "Focus: f,g |"
                    "Shift: finer |"
                    "q to exit")

    # MAIN LOOP
    while (key != ord('q')):
        # retrieve and display frame
        frame = None
        frame = cam.get_frame()
        if frame is not None:
            frame = ui.orient_frame(frame, ORIENTATION)
            cv2.imshow('Control PTZ Camera', frame)
            _ = cv2.waitKey(33)

        # Initialization
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if key == ord('k'):
            tilt_command += Y_DELTA
        elif key == ord('K'):
            tilt_command += Y_DELTA_FINE
        elif key == ord('i'):
            tilt_command -= Y_DELTA
        elif key == ord('I'):
            tilt_command -= Y_DELTA_FINE

        elif key == ord('l'):
            pan_command -= X_DELTA
        elif key == ord('L'):
            pan_command -= X_DELTA_FINE
        elif key == ord('j'):
            pan_command += X_DELTA
        elif key == ord('J'):
            pan_command += X_DELTA_FINE

        elif key == ord('z'):
            zoom_command += Z_DELTA
        elif key == ord('Z'):
            zoom_command += Z_DELTA_FINE
        elif key == ord('x'):
            zoom_command -= Z_DELTA
        elif key == ord('X'):
            zoom_command -= Z_DELTA_FINE

        elif key == ord('f'):
            ptz.focus_in()
            time.sleep(F_TIME)
            ptz.focus_stop()
        elif key == ord('F'):
            ptz.focus_in()
            time.sleep(F_TIME_FINE)
            ptz.focus_stop()
        elif key == ord('g'):
            ptz.focus_out()
            time.sleep(F_TIME)
            ptz.focus_stop()
        elif key == ord('G'):
            ptz.focus_out()
            time.sleep(F_TIME_FINE)
            ptz.focus_stop()

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

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        try:
            stdscr.addstr(8, 0, statusbarstr)
            stdscr.addstr(8,
                          len(statusbarstr),
                          " " * (width - len(statusbarstr) - 1))
        except:
            print('error')

        stdscr.attroff(curses.color_pair(3))

        # Turning on attributes for title
        stdscr.attron(curses.color_pair(2))
        stdscr.attron(curses.A_BOLD)

        # Rendering title
        stdscr.addstr(0, 0, title)

        # Turning off attributes for title
        stdscr.attroff(curses.color_pair(2))
        stdscr.attroff(curses.A_BOLD)

        # Print rest of text
        stdscr.addstr(1, 0, subtitle)
        stdscr.addstr(2, 0, '-' * 31)

        # Print pan, tilt, zoom values
        angle_str = "Pan: {:.3f}".format(pan_command)
        stdscr.addstr(3, 0, angle_str, curses.color_pair(1))
        angle_str = "Tilt: {:.3f}".format(tilt_command)
        stdscr.addstr(4, 0, angle_str, curses.color_pair(1))
        angle_str = "Zoom: {:.3f}".format(zoom_command)
        stdscr.addstr(5, 0, angle_str, curses.color_pair(1))
        angle_str = "Focus: Sorta unknown"
        stdscr.addstr(6, 0, angle_str, curses.color_pair(1))

        curses.curs_set(0)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        key = stdscr.getch()

    cv2.destroyAllWindows()
    # cam.release()
    del cam
    del ptz


def main():
    curses.wrapper(main_ui_function)


if __name__ == "__main__":
    main()
