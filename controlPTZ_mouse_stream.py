import cv2

from ptz_camera import PtzCam

IP = "192.168.1.64"   # Camera IP address
PORT = 80           # Port
USER = "admin"         # Username
PASS = "NyalaChow22"        # Password

mouseX = 250
mouseY = 250

WINDOW_NAME = 'Control PTZ Camera with mouse'


def getMouseCoords(event, x, y, flags, param):
    global mouseX
    global mouseY

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y


if __name__ == '__main__':
    ptzCam = PtzCam(IP, PORT, USER, PASS)

    key = 'd'
    cap = cv2.VideoCapture(0)
    ok, frame = cap.read()
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
        ok, frame = cap.read()
        cv2.rectangle(frame, zone['start'], zone['end'], (255, 0, 0))
        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(10)

        if key == ord('w'):
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
