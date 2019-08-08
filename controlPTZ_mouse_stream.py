#!/home/ian/.virtualenvs/ptzSpotter/bin/python

# Need to do something in the realm of this first:
# ffmpeg -rtsp_transport tcp -i rtsp://admin:NyalaChow22@192.168.1.64:554/Streaming/Channels/103 -b 1900k -f mpegts udp://127.0.0.1:5000

import ui
import yaml
import argparse

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

UPSIDE_DOWN = configs['UPSIDE_DOWN']
SIDEWAYS = configs['SIDEWAYS']

if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)
    cam = Camera()

    frame = cam.get_frame()
    frame = ui.orient_frame(frame, SIDEWAYS, UPSIDE_DOWN)

    window_name = 'Control PTZ Camera with mouse'
    uih = ui.UI_Handler(frame, window_name)

    x_dir = 0
    y_dir = 0
    zoom_command = False
    ptzCam.zoom_out_full()

    while True:
        frame = cam.get_frame()
        frame = ui.orient_frame(frame, SIDEWAYS, UPSIDE_DOWN)

        key = uih.update(frame)
        if key == ord('q'):
            break

        if zoom_command == 'i':
            ptzCam.zoom_in_full()
        elif zoom_command == 'o':
            ptzCam.zoom_out_full()

        if SIDEWAYS:
            ptzCam.move(y_dir, -x_dir)
        elif UPSIDE_DOWN:
            ptzCam.move(-x_dir, -y_dir)
        else:
            ptzCam.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = uih.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cam.release()
    ptzCam.stop()
    uih.clean_up()
