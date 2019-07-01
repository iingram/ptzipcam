import cv2
import threading

from ptz_camera import PtzCam

IP = "192.168.1.64"   # Camera IP address
PORT = 80           # Port
USER = "admin"         # Username
PASS = "NyalaChow22"        # Password

mouseX = 250
mouseY = 250

WINDOW_NAME = 'Control PTZ Camera with mouse'

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


# callback function for mouse pointer tracking
def getMouseCoords(event, x, y, flags, param):
    global mouseX
    global mouseY

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y


if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)

    cam_thread = threading.Thread(target=camera_thread_function,
                                  args=(cap,),
                                  daemon=True)
    cam_thread.start()

    cv2.imshow(WINDOW_NAME, frame)
    cv2.setMouseCallback(WINDOW_NAME, getMouseCoords)

    width = frame.shape[1]
    height = frame.shape[0]

    zone = {'start': (int(.3*width), int(.3*height)),
            'end': (int(.7*width), int(.7*height))}

    x_dir = 0
    y_dir = 0

    while True:
        # print(f'mouseX: {mouseX}, mouseY: {mouseY}')
        # ok, frame = cap.read()
        if (latest_frame_return is not None) and (latest_frame is not None):
            frame = latest_frame.copy()

        cv2.rectangle(frame, zone['start'], zone['end'], (255, 0, 0))
        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(10)

        if key == ord('q'):
            break

        ptzCam.move(x_dir, y_dir)

        if(mouseX < zone['start'][0]):
            x_dir = -1
        elif(mouseX > zone['end'][0]):
            x_dir = 1
        else:
            x_dir = 0

        if(mouseY < zone['start'][1]):
            y_dir = 1
        elif(mouseY > zone['end'][1]):
            y_dir = -1
        else:
            y_dir = 0

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

    cv2.destroyAllWindows()
    cap.release()
    ptzCam.stop()
