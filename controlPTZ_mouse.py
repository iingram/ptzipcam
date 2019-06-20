import cv2
import numpy as np
import time


from onvif import ONVIFCamera

IP="192.168.1.64"   # Camera IP address
PORT=80           # Port
USER="admin"         # Username
PASS="NyalaChow22"        # Password

moverequest = None
ptz = None

mouseX = 250
mouseY = 250

def getMouseCoords(event,x,y,flags,param):
    global mouseX
    global mouseY

    if event == cv2.EVENT_MOUSEMOVE:
        mouseX = x
        mouseY = y

def setup_move():
    mycam = ONVIFCamera(IP, PORT, USER, PASS)
    # Create media service object
    media = mycam.create_media_service()
    
    # Create ptz service object
    global ptz
    ptz = mycam.create_ptz_service()

    # Get target profile
    media_profile = media.GetProfiles()[0]

    global moverequest
    moverequest = ptz.create_type('ContinuousMove')
    moverequest.ProfileToken = media_profile.token
    if moverequest.Velocity is None:
        # moverequest.Velocity = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        moverequest.Velocity =  {'PanTilt': {'x': -1, 'y': -1}, 'Zoom': {'x': 0.0}}
    
if __name__ == '__main__':
    # global mouseX
    # global mouseY
    
    setup_move()
    moverequest.Velocity =  {'PanTilt': {'x': -1, 'y': 1}, 'Zoom': {'x': 0.0}}

    key = 'd'
    canvas = np.zeros((500,500), np.uint8)
    cv2.imshow('Control PTZ Camera', canvas)
    cv2.setMouseCallback('Control PTZ Camera', getMouseCoords)

    x_dir = 0
    
    while True:
        print(f'mouseX: {mouseX}, mouseY: {mouseY}')
        key = cv2.waitKey(10)
                
        if key == ord('w'):
            break

        ptz.ContinuousMove(moverequest)

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
            ptz.Stop({'ProfileToken': moverequest.ProfileToken})

        moverequest.Velocity =  {'PanTilt': {'x': x_dir, 'y': y_dir}, 'Zoom': {'x': 0.0}}
           
           
    cv2.destroyAllWindows()


    
