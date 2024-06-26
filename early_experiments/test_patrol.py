import time

import asyncio
import sys

import cv2
import numpy as np

from onvif import ONVIFCamera

IP="192.168.1.64"   # Camera IP address
PORT=80           # Port
USER="username"         # Username
PASS="password"        # Password


XMAX = 1
XMIN = -1
YMAX = 1
YMIN = -1
MAX_ZOOM = 1.0
MIN_ZOOM = 0.0

x_command = .5
y_command = .5

moverequest = None
ptz = None
active = False


def do_move(ptz, request):
    # Start continuous move
    global active
    if active:
        ptz.Stop({'ProfileToken': request.ProfileToken})
    active = True
    ptz.AbsoluteMove(request)

    
def checkZeroness(number):
    e = .001

    if number < e and number > -e:
        return 0.0
    else:
        return number


def move_up(ptz, request):
    global y_command

    #print ('move up...')
    y_command += .1
    y_command = checkZeroness(y_command)
    if y_command >= YMAX:
        y_command = YMAX
    request.Position.PanTilt.y = y_command
    # request.Position.PanTilt.y = YMAX
    
    do_move(ptz, request)

    
def move_down(ptz, request):
    global y_command
    #print ('move down...')
    y_command -= .1
    y_command = checkZeroness(y_command)
    if y_command <= YMIN:
        y_command = YMIN
    request.Position.PanTilt.y = y_command
    # request.Position.PanTilt.y = YMIN

    do_move(ptz, request)

    
def move_right(ptz, request):
    global x_command
    #print ('move right...')
    x_command += .05
    if x_command >= XMAX:
        x_command = XMAX
    x_command = checkZeroness(x_command)
    request.Position.PanTilt.x = x_command
    # request.Position.PanTilt.x = XMIN
    do_move(ptz, request)

    
def move_left(ptz, request):
    global x_command
    #print ('move left...')
    x_command -= .05
    if x_command <= XMIN:
        x_command = XMIN
    x_command = checkZeroness(x_command)
    request.Position.PanTilt.x = x_command
    # request.Position.PanTilt.x = XMAX
    do_move(ptz, request)

    
# def move_upleft(ptz, request):
#     print ('move up left...')
#     request.Position.PanTilt.x = XMIN
#     request.Position.PanTilt.y = YMAX
#     do_move(ptz, request)


# def move_upright(ptz, request):
#     print ('move up right...')
#     request.Position.PanTilt.x = XMAX
#     request.Position.PanTilt.y = YMAX
#     do_move(ptz, request)


# def move_downleft(ptz, request):
#     print ('move down left...')
#     request.Position.PanTilt.x = XMIN
#     request.Position.PanTilt.y = YMIN
#     do_move(ptz, request)


# def move_downright(ptz, request):
#     print ('move down left...')
#     request.Position.PanTilt.x = XMAX
#     request.Position.PanTilt.y = YMIN
#     do_move(ptz, request)


def zoom_in(ptz, request):
    #print ('zoom in...')
    request.Position.Zoom.x = MAX_ZOOM
    do_move(ptz, request)

    
def zoom_out(ptz, request):
    #print ('zoom out...')
    request.Position.Zoom.x = MIN_ZOOM
    do_move(ptz, request)

    
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
    moverequest = ptz.create_type('AbsoluteMove')
    moverequest.ProfileToken = media_profile.token
    if moverequest.Position is None:
        moverequest.Position = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        moverequest.Speed = media_profile.PTZConfiguration.DefaultPTZSpeed


    # Get range of pan and tilt
    # NOTE: X and Y are velocity vector
    # Get PTZ configuration options for getting continuous move range
    request = ptz.create_type('GetConfigurationOptions')
    request.ConfigurationToken = media_profile.PTZConfiguration.token
    ptz_configuration_options = ptz.GetConfigurationOptions(request)
    
    global XMAX, XMIN, YMAX, YMIN, MAX_ZOOM, MIN_ZOOM
    XMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max
    XMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min
    YMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max
    YMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min

    MAX_ZOOM = ptz_configuration_options.Spaces.AbsoluteZoomPositionSpace[0].XRange.Max
    MIN_ZOOM = ptz_configuration_options.Spaces.AbsoluteZoomPositionSpace[0].XRange.Min
            
if __name__ == '__main__':
    # global moverequest, ptz
    setup_move()
    # loop = asyncio.get_event_loop()
    # try:
    #     loop.add_reader(sys.stdin,readin)
    #     print("Use Ctrl-C to quit")
    #     print("Your command: ", end='',flush=True)
    #     loop.run_forever()
    # except:
    #     pass
    # finally:
    #     loop.remove_reader(sys.stdin)
    #     loop.close()

    move_up(ptz,moverequest)
    move_right(ptz,moverequest)
    zoom_out(ptz,moverequest)
    time.sleep(3)
    key = 'd'

    # canvas = np.zeros((500,500), np.uint8)
    # cv2.imshow('Control PTZ Camera', canvas)

    forward = True


    jump = .125
    
    while True:
        setup_move()
        if forward:
            x_command += jump
            if x_command >= XMAX:
                x_command = XMAX
                forward = False
        else:
            x_command -= jump
            if x_command <= XMIN:
                x_command = XMIN
                forward = True

        x_command = checkZeroness(x_command)
        print(x_command)
        moverequest.Position.PanTilt.x = x_command
        do_move(ptz, moverequest)
        time.sleep(.3)
