import yaml
import argparse
# import time

from ptzipcam.ptz_camera import PtzCam
from ptzipcam.camera import Camera
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

ORIENTATION = configs['ORIENTATION']

if __name__ == '__main__':
    ptz = PtzCam(IP, PORT, USER, PASS)
    cam = Camera(ip=IP, user=USER, passwd=PASS, stream=STREAM)

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    window_name = 'Control PTZ Camera with mouse'
    uih = ui.UI_Handler(frame, window_name)

    x_dir = 0
    y_dir = 0
    zoom_command = False
    ptz.zoom_out_full()

    print('Tool to control ptz ip camera with mouse and see stream.')

    while True:
        # time.sleep(1)
        frame = cam.get_frame()
        if frame is None:
            continue

        frame = ui.orient_frame(frame, ORIENTATION)

        key = uih.update(frame)
        if key == ord('q'):
            break

        pan, tilt, zoom = ptz.get_position()
        print(pan, tilt, zoom)

        if zoom_command == 'i':
            ptz.zoom_in_full()
        elif zoom_command == 'o':
            ptz.zoom_out_full()

        if ORIENTATION == 'left':
            ptz.move(y_dir, -x_dir)
        elif ORIENTATION == 'down':
            ptz.move(-x_dir, -y_dir)
        elif ORIENTATION == 'right':
            ptz.move(-y_dir, x_dir)
        else:
            ptz.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = uih.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptz.stop()

    cam.release()
    ptz.stop()
    uih.clean_up()
