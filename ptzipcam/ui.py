import cv2

import numpy as np

mouseX = 250
mouseY = 250
zoom_command = None


def orient_frame(frame, ORIENTATION):
    if ORIENTATION == 'left':
        frame = np.rot90(frame)
    elif ORIENTATION == 'down':
        frame = np.rot90(frame, 2)
    elif ORIENTATION == 'right':
        frame = np.rot90(frame, 3)

    # returning a copy solves a bug that keeps one from drawing on the
    # resultant frame but might also allay other problems that spawn
    # from the same source.  The underlying bug might be in the opencv
    # library.
    return frame.copy()


# callback function for mouse ui
def mouse_callback(event, x, y, flags, param):
    global mouseX
    global mouseY
    global zoom_command

    zoom_command = None

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y

    if event == cv2.EVENT_LBUTTONDOWN:
        zoom_command = 'i'
    elif event == cv2.EVENT_LBUTTONUP or event == cv2.EVENT_RBUTTONDOWN:
        zoom_command = 'o'


class UI_Handler():

    def __init__(self, frame, window_name, scale_display=1.0):
        self.window_name = window_name

        width = frame.shape[1]
        height = frame.shape[0]
        display_width = int(width * scale_display)
        display_height = int(height * scale_display)

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name,
                         display_width,
                         display_height)

        cv2.imshow(self.window_name, frame)
        cv2.setMouseCallback(self.window_name, mouse_callback)

        self.zone = {'start': (int(.3*width), int(.3*height)),
                     'end': (int(.7*width), int(.7*height))}

    def update(self, frame, hud=True):

        if hud:
            cv2.rectangle(frame,
                          self.zone['start'],
                          self.zone['end'],
                          (255, 0, 0),
                          thickness=2)

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(10)

        return key

    def read_mouse(self):

        if(mouseX < self.zone['start'][0]):
            x_dir = -1
        elif(mouseX > self.zone['end'][0]):
            x_dir = 1
        else:
            x_dir = 0

        if(mouseY < self.zone['start'][1]):
            y_dir = 1
        elif(mouseY > self.zone['end'][1]):
            y_dir = -1
        else:
            y_dir = 0

        return x_dir, y_dir, zoom_command

    def clean_up(self):
        cv2.destroyAllWindows()
