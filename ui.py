import cv2

mouseX = 250
mouseY = 250
zoom_command = None


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
    elif event == cv2.EVENT_LBUTTONUP:
        zoom_command = 'o'

class UI_Handler():
    WINDOW_NAME = 'Control PTZ Camera with mouse'

    def __init__(self, frame):
        cv2.imshow(self.WINDOW_NAME, frame)
        cv2.setMouseCallback(self.WINDOW_NAME, mouse_callback)

        width = frame.shape[1]
        height = frame.shape[0]

        self.zone = {'start': (int(.3*width), int(.3*height)),
                     'end': (int(.7*width), int(.7*height))}

    def update(self, frame):

        cv2.rectangle(frame,
                      self.zone['start'],
                      self.zone['end'],
                      (255, 0, 0))

        cv2.imshow(self.WINDOW_NAME, frame)
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
