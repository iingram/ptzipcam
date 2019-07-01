import cv2
import threading

from ptz_camera import PtzCam
import ui

IP = "192.168.1.64"   # Camera IP address
PORT = 80           # Port
USER = "admin"         # Username
PASS = "NyalaChow22"        # Password

frame = None
latest_frame = None
latest_frame_return = None
lo = threading.Lock()
cap = cv2.VideoCapture('udp://127.0.0.1:5000', cv2.CAP_FFMPEG)
ok, frame = cap.read()


def camera_thread_function(cap):
    global latest_frame, lo, latest_frame_return
    while True:
        with lo:
            latest_frame_return, latest_frame = cap.read()

            
if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)

    cam_thread = threading.Thread(target=camera_thread_function,
                                  args=(cap,),
                                  daemon=True)
    cam_thread.start()

    ui = ui.UI_Handler(frame)

    x_dir = 0
    y_dir = 0

    while True:
        if (latest_frame_return is not None) and (latest_frame is not None):
            frame = latest_frame.copy()

        key = ui.update(frame)
        if key == ord('q'):
            break

        ptzCam.move(x_dir, y_dir)

        x_dir, y_dir = ui.read_mouse()

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cv2.destroyAllWindows()
    cap.release()
    ptzCam.stop()
