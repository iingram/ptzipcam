#!/home/ian/.virtualenvs/ptzSpotter/bin/python

from ptz_camera import PtzCam
from camera import Camera
import ui

IP = "192.168.1.64"   # Camera IP address
PORT = 80           # Port
USER = "admin"         # Username
PASS = "NyalaChow22"        # Password
       
if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)
    cam = Camera()

    frame = cam.get_frame()
    ui = ui.UI_Handler(frame)

    x_dir = 0
    y_dir = 0

    while True:
        frame = cam.get_frame()
        key = ui.update(frame)
        if key == ord('q'):
            break
        elif key == ord('o'):
            ptzCam.zoom_out_full()
        elif key == ord('i'):
            ptzCam.zoom_in_full()
        
        ptzCam.move(x_dir, y_dir)

        x_dir, y_dir = ui.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cam.release()
    ptzCam.stop()
    ui.clean_up()
