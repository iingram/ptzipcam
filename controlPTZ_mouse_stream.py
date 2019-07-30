#!/home/ian/.virtualenvs/ptzSpotter/bin/python

# Need to do something in the realm of this first:
# ffmpeg -rtsp_transport tcp -i rtsp://admin:NyalaChow22@192.168.1.64:554/Streaming/Channels/103 -b 1900k -f mpegts udp://127.0.0.1:5000

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
    window_name = 'Control PTZ Camera with mouse'
    ui = ui.UI_Handler(frame, window_name)

    x_dir = 0
    y_dir = 0
    zoom_command = False
    ptzCam.zoom_out_full()
    
    while True:
        frame = cam.get_frame()
        key = ui.update(frame)
        if key == ord('q'):
            break
        
        if zoom_command == 'i':
            ptzCam.zoom_in_full()
        elif zoom_command == 'o':
            ptzCam.zoom_out_full()
        
        ptzCam.move(x_dir, y_dir)

        x_dir, y_dir, zoom_command = ui.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cam.release()
    ptzCam.stop()
    ui.clean_up()
