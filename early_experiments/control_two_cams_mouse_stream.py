#!/home/ian/.virtualenvs/ptzSpotter/bin/python

# Need to do something in the realm of this first:
# ffmpeg -rtsp_transport tcp -i rtsp://admin:NyalaChow22@192.168.1.64:554/Streaming/Channels/103 -b 1900k -f mpegts udp://127.0.0.1:5000

import ui
import yaml
import argparse
# import time

from ptz_camera import PtzCam
from camera import Camera

ap = argparse.ArgumentParser()

ap.add_argument('-n',
                '--num',
                default='64',
                help='last bit of camera IP (assumes rest')

args = ap.parse_args()

IP = "192.168.1." + args.num  # Camera IP address
PORT = 80           # Port
USER = "admin"         # Username
PASS = "NyalaChow22"        # Password

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

ORIENTATION = configs['ORIENTATION']

if __name__ == '__main__':
    ptz_cam = PtzCam(IP, PORT, USER, PASS)
    ptz_cam_2 = PtzCam('192.168.1.63', PORT, USER, PASS)
    cam = Camera()

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, ORIENTATION)

    window_name = 'Control PTZ Camera with mouse'
    uih = ui.UI_Handler(frame, window_name)

    x_dir = 0
    y_dir = 0
    zoom_command = False
    ptz_cam.zoom_out_full()
    ptz_cam_2.zoom_out_full()

    while True:
        # time.sleep(1)
        frame = cam.get_frame()
        frame = ui.orient_frame(frame, ORIENTATION)

        key = uih.update(frame)
        if key == ord('q'):
            break

        if zoom_command == 'i':
            ptz_cam.zoom_in_full()
            ptz_cam_2.zoom_in_full()
        elif zoom_command == 'o':
            ptz_cam.zoom_out_full()
            ptz_cam_2.zoom_out_full()

        if ORIENTATION == 'left':
            ptz_cam.move(y_dir, -x_dir)
            ptz_cam_2.move(y_dir, -x_dir)
        elif ORIENTATION == 'down':
            ptz_cam.move(-x_dir, -y_dir)
            ptz_cam_2.move(-x_dir, -y_dir)
        elif ORIENTATION == 'right':
            ptz_cam.move(-y_dir, x_dir)
            ptz_cam_2.move(-y_dir, x_dir)
        else:
            ptz_cam.move(x_dir, y_dir)
            ptz_cam_2.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = uih.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptz_cam.stop()
            ptz_cam_2.stop()

    cam.release()
    ptz_cam.stop()
    ptz_cam_2.stop()
    uih.clean_up()
