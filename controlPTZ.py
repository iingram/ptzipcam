# import asyncio
import sys

import yaml

import cv2
import numpy as np

from onvif import ONVIFCamera

from camera import Camera

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
USER = configs['USER']
PASS = configs['PASS']

cam = Camera(ip=IP, user=USER, passwd=PASS)

# IP = "192.168.1.64"   # Camera IP address
PORT = 80           # Onvif Port
# USER = "admin"         # Username
# PASS = "NyalaChow22"        # Password

XMAX = 1
XMIN = -1
YMAX = 1
YMIN = -1
MAX_ZOOM = 1.0
MIN_ZOOM = 0.0

x_command = .5
y_command = -0.5

moverequest = None
ptz = None
active = False

Y_DELTA = .1
X_DELTA = .05
X_DELTA_FINE = .005

def do_move(ptz, request):
    # Start continuous move
    # global active
    # if active:
    #     ptz.Stop({'ProfileToken': request.ProfileToken})
    # active = True
    ptz.AbsoluteMove(request)


def checkZeroness(number):
    e = .001

    if number < e and number > -e:
        return 0
    else:
        return number


def move_up(ptz, request):
    global y_command

    # print ('move up...')
    y_command += Y_DELTA
    y_command = checkZeroness(y_command)
    if y_command >= YMAX:
        y_command = YMAX
    request.Position.PanTilt.y = y_command
    # request.Position.PanTilt.y = YMAX

    do_move(ptz, request)


def move_down(ptz, request):
    global y_command
    # print ('move down...')
    y_command -= Y_DELTA
    y_command = checkZeroness(y_command)
    if y_command <= YMIN:
        y_command = YMIN
    request.Position.PanTilt.y = y_command
    # request.Position.PanTilt.y = YMIN

    do_move(ptz, request)


def move_right(ptz, request, fine=False):
    global x_command
    # print ('move right...')
    if fine:
        x_command += X_DELTA_FINE
    else:
        x_command += X_DELTA
    x_command = checkZeroness(x_command)
    if x_command >= XMAX:
        x_command = XMAX
    request.Position.PanTilt.x = x_command
    # request.Position.PanTilt.x = XMIN
    do_move(ptz, request)


def move_left(ptz, request, fine=False):
    global x_command
    # print ('move left...')
    if fine:
        x_command -= X_DELTA_FINE
    else:
        x_command -= X_DELTA
    x_command = checkZeroness(x_command)
    if x_command <= XMIN:
        x_command = XMIN
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
    # print ('zoom in...')
    request.Position.Zoom.x = MAX_ZOOM
    do_move(ptz, request)


def zoom_out(ptz, request):
    # print ('zoom out...')
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
    media_profile = media.GetProfiles()[1]

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


def readin():
    """Reading from stdin and displaying menu"""
    global moverequest, ptz

    selection = sys.stdin.readline().strip("\n")
    lov = [x for x in selection.split(" ") if x != ""]
    if lov:

        if lov[0].lower() in ["u", "up"]:
            move_up(ptz, moverequest)
        elif lov[0].lower() in ["d", "do", "dow", "down"]:
            move_down(ptz, moverequest)
        elif lov[0].lower() in ["l", "le", "lef", "left"]:
            move_left(ptz, moverequest)
        elif lov[0].lower() in ["l", "le", "lef", "left"]:
            move_left(ptz, moverequest)
        elif lov[0].lower() in ["r", "ri", "rig", "righ", "right"]:
            move_right(ptz, moverequest)
        elif lov[0].lower() in ["ul"]:
            move_upleft(ptz, moverequest)
        elif lov[0].lower() in ["ur"]:
            move_upright(ptz, moverequest)
        elif lov[0].lower() in ["dl"]:
            move_downleft(ptz, moverequest)
        elif lov[0].lower() in ["dr"]:
            move_downright(ptz, moverequest)
        elif lov[0].lower() in ["zi"]:
            zoom_in(ptz, moverequest)
        elif lov[0].lower() in ["zo"]:
            zoom_out(ptz, moverequest)
        elif lov[0].lower() in ["s", "st", "sto", "stop"]:
            ptz.Stop({'ProfileToken': moverequest.ProfileToken})
            active = False
        else:
            print("What are you asking?\tI only know, 'up','down','left','right', 'ul' (up left), \n\t\t\t'ur' (up right), 'dl' (down left), 'dr' (down right) and 'stop'")

    print("")
    print("Your command: ", end='', flush=True)


def printUpdate():
    # currently specific to small hikvisions
    print('Pan, Tilt is {pan:.2f}, {tilt:.2f}'.format(pan=x_command*175.0,
                                                      tilt=y_command*45.0))


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

    move_up(ptz, moverequest)
    move_right(ptz, moverequest)
    zoom_out(ptz, moverequest)

    key = 'd'

    print("Keys:\n",
          "w: quit\n",
          "k: up\n",
          "i: down\n",
          "j: left\n",
          "l: right\n",
          "z: zoom in (full)\n",
          "a: zoom out (full)\n")

    while True:

        if key == ord('w'):
            break
        elif key == ord('i'):
            move_up(ptz, moverequest)
            printUpdate()
        elif key == ord('k'):
            move_down(ptz, moverequest)
            printUpdate()
        elif key == ord('j'):
            move_right(ptz, moverequest)
            printUpdate()
        elif key == ord('h'):
            move_right(ptz, moverequest, fine=True)
            printUpdate()
        elif key == ord('l'):
            move_left(ptz, moverequest)
            printUpdate()
        elif key == ord('p'):
            move_left(ptz, moverequest, fine=True)
            printUpdate()
        elif key == ord('z'):
            zoom_in(ptz, moverequest)
            printUpdate()
        elif key == ord('a'):
            zoom_out(ptz, moverequest)
            printUpdate()
        elif key == ord('u'):
            pass

        # canvas = np.zeros((500, 500), np.uint8)
        frame = cam.get_frame()
        cv2.imshow('Control PTZ Camera', frame)
        key = cv2.waitKey(0)
            
    cv2.destroyAllWindows()
