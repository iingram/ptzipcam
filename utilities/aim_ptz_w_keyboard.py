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


def main_ui_loop(stdscr):
    # prep camera control
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)


    pan, tilt, zoom = ptz.get_position()
    pan_command = pan
    tilt_command = tilt
    zoom_command = zoom

    # prep ui elements
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
                    "Shift: finer |"
                    "q to exit")

    
    # Loop where k is the last character pressed
    while (key != ord('q')):
        # retrieve and display frame
        frame = None
        frame = cam.get_frame()
        if frame is not None:
            frame = ui.orient_frame(frame, ORIENTATION)
            cv2.imshow('Control PTZ Camera', frame)
            key_throwaway = cv2.waitKey(33)
        
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
            stdscr.addstr(7, 0, statusbarstr)
            stdscr.addstr(7,
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

        curses.curs_set(0)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        key = stdscr.getch()

    cv2.destroyAllWindows()
    # cam.release()
    del cam
    del ptz


    
if __name__ == '__main__':
    curses.wrapper(main_ui_loop)
    

    # key = None

    # keys = ['w',
    #         'a', 's', 'd', 'f',
    #         'h', 'j', 'k', 'l',
    #         'y', 'u', 'i', 'o',
    #         'z', 'x', 'c', 'v',
    #         'r']

    # print("Keys:\n",
    #       keys[0] + ": quit\n",
    #       keys[1] + ": tilt up (fine)\n",
    #       keys[2] + ": tilt up\n",
    #       keys[3] + ": tilt down\n",
    #       keys[4] + ": tilt down (fine)\n",
    #       keys[5] + ": pan left (fine)\n",
    #       keys[6] + ": pan left\n",
    #       keys[7] + ": pan right\n",
    #       keys[8] + ": pan right (fine)\n",
    #       keys[9] + ": focus in (fine)\n",
    #       keys[10] + ": focus in \n",
    #       keys[11] + ": focus out \n",
    #       keys[12] + ": focus out (fine)\n",
    #       keys[13] + ": zoom out fine \n",
    #       keys[14] + ": zoom out  \n",
    #       keys[15] + ": zoom in \n",
    #       keys[16] + ": zoom in fine \n",
    #       keys[17] + ": update frame")

    # while True:

    #     if key == ord(keys[0]):
    #         break
    #     elif key == ord(keys[1]):
    #         # tilt up fine
    #         tilt_command -= Y_DELTA_FINE
    #     elif key == ord(keys[2]):
    #         # tilt up
    #         tilt_command -= Y_DELTA
    #     elif key == ord(keys[3]):
    #         # tilt down
    #         tilt_command += Y_DELTA
    #     elif key == ord(keys[4]):
    #         # tilt down fine
    #         tilt_command += Y_DELTA_FINE
    #     elif key == ord(keys[5]):
    #         # pan right fine
    #         pan_command += X_DELTA_FINE
    #     elif key == ord(keys[6]):
    #         # pan right
    #         pan_command += X_DELTA
    #     elif key == ord(keys[7]):
    #         # pan left
    #         pan_command -= X_DELTA
    #     elif key == ord(keys[8]):
    #         # pan left fine
    #         pan_command -= X_DELTA_FINE
    #     elif key == ord(keys[9]):
    #         # focus in fine
    #         ptz.focus_in()
    #         time.sleep(F_TIME_FINE)
    #         ptz.focus_stop()
    #     elif key == ord(keys[10]):
    #         # focus in
    #     elif key == ord(keys[11]):
    #         # focus out
    #         ptz.focus_out()
    #         time.sleep(F_TIME)
    #         ptz.focus_stop()
    #     elif key == ord(keys[12]):
    #         # focus out fine
    #         ptz.focus_out()
    #         time.sleep(F_TIME_FINE)
    #         ptz.focus_stop()
    #     elif key == ord(keys[13]):
    #         # zoom in fine
    #         zoom_command -= Z_DELTA_FINE
    #     elif key == ord(keys[14]):
    #         # zoom in
    #         zoom_command -= Z_DELTA
    #     elif key == ord(keys[15]):
    #         # zoom out
    #         zoom_command += Z_DELTA
    #     elif key == ord(keys[16]):
    #         # zoom out fine
    #         zoom_command += Z_DELTA_FINE
    #     elif key == ord(keys[17]):
    #         pass
    #     else:
    #         pass







# if __name__ == "__main__":
#     main()
