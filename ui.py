import cv2

mouseX = 250
mouseY = 250

# callback function for mouse pointer tracking
def getMouseCoords(event, x, y, flags, param):
    global mouseX
    global mouseY

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y

WINDOW_NAME = 'Control PTZ Camera with mouse'

class UI_Handler():

    def __init__(self, frame):
        cv2.imshow(WINDOW_NAME, frame)
        cv2.setMouseCallback(WINDOW_NAME, getMouseCoords)

        width = frame.shape[1]
        height = frame.shape[0]
        
        self.zone = {'start': (int(.3*width), int(.3*height)),
                'end': (int(.7*width), int(.7*height))}
        
    def update(self, frame):

        cv2.rectangle(frame,
                      self.zone['start'],
                      self.zone['end'],
                      (255, 0, 0))
        
        cv2.imshow(WINDOW_NAME, frame)
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

        return x_dir, y_dir

    def clean_up(self):
        cv2.destroyAllWindows()
