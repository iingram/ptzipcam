import cv2
import numpy as np
import time


from onvif import ONVIFCamera

# moverequest = None
# ptz = None

mouseX = 250
mouseY = 250

class PtzCam():

    def __init__(self):
        IP="192.168.1.64"   # Camera IP address
        PORT=80           # Port
        USER="admin"         # Username
        PASS="NyalaChow22"        # Password

        mycam = ONVIFCamera(IP, PORT, USER, PASS)
        # Create media service object
        media = mycam.create_media_service()
    
        # Create ptz service object
        # global ptz
        self.ptz = mycam.create_ptz_service()

        # Get target profile
        media_profile = media.GetProfiles()[0]

        # global moverequest
        self.moverequest = self.ptz.create_type('ContinuousMove')
        self.moverequest.ProfileToken = media_profile.token
        if self.moverequest.Velocity is None:
            self.moverequest.Velocity =  {'PanTilt': {'x': -1, 'y': -1}, 'Zoom': {'x': 0.0}}

        self.moverequest.Velocity =  {'PanTilt': {'x': -1, 'y': 1}, 'Zoom': {'x': 0.0}}

    def move(self, x_dir, y_dir):
        self.moverequest.Velocity =  {'PanTilt': {'x': x_dir, 'y': y_dir}, 'Zoom': {'x': 0.0}}
        self.ptz.ContinuousMove(self.moverequest)

    def stop(self):
        self.ptz.Stop({'ProfileToken': self.moverequest.ProfileToken})
    
def getMouseCoords(event,x,y,flags,param):
    global mouseX
    global mouseY

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y


if __name__ == '__main__':
    ptzCam = PtzCam()

    key = 'd'
    canvas = np.zeros((500,500), np.uint8)
    cv2.imshow('Control PTZ Camera', canvas)
    cv2.setMouseCallback('Control PTZ Camera', getMouseCoords)

    x_dir = 0
    y_dir = 0
    
    while True:
        # print(f'mouseX: {mouseX}, mouseY: {mouseY}')
        key = cv2.waitKey(10)
                
        if key == ord('w'):
            break

        ptzCam.move(x_dir, y_dir)
        
        if(mouseX < 200):
            x_dir = -1
        elif(mouseX > 300):
            x_dir = 1
        else:
            x_dir = 0

        if(mouseY < 200):
            y_dir = 1
        elif(mouseY > 300):
            y_dir = -1
        else:
            y_dir = 0

        if x_dir == 0 and y_dir == 0:
            ptzCam.stop()

           
           
    cv2.destroyAllWindows()


    
