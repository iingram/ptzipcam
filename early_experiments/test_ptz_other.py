import asyncio, sys
from onvif import ONVIFCamera

IP="192.168.1.64"   # Camera IP address
PORT=80           # Port
USER="admin"         # Username
PASS="NyalaChow22"        # Password


XMAX = 1
XMIN = -1
YMAX = 1
YMIN = -1
MAX_ZOOM = 1.0
MIN_ZOOM = 0.0

moverequest = None
ptz = None
active = False

def do_move(ptz, request):
    # Start continuous move
    global active
    if active:
        ptz.Stop({'ProfileToken': request.ProfileToken})
    active = True
    ptz.ContinuousMove(request)

def move_up(ptz, request):
    print ('move up...')
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = YMAX
    # par = {'PanTilt' : {'x' : 5.0, 'y' : 5.0}}  
    # request.Speed = par

    request.Speed.PanTilt.x = .1
    request.Speed.PanTilt.y = .1
    
    print(request)
    
    do_move(ptz, request)

def move_down(ptz, request):
    print ('move down...')
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = YMIN
    do_move(ptz, request)

def move_right(ptz, request):
    print ('move right...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = 0
    do_move(ptz, request)

def move_left(ptz, request):
    print ('move left...')
    request.Velocity.PanTilt.x = XMIN
    request.Velocity.PanTilt.y = 0
    do_move(ptz, request)

def move_upleft(ptz, request):
    print ('move up left...')
    request.Velocity.PanTilt.x = XMIN
    request.Velocity.PanTilt.y = YMAX
    do_move(ptz, request)
    
def move_upright(ptz, request):
    print ('move up right...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = YMAX
    do_move(ptz, request)
    
def move_downleft(ptz, request):
    print ('move down left...')
    request.Velocity.PanTilt.x = XMIN
    request.Velocity.PanTilt.y = YMIN
    do_move(ptz, request)
    
def move_downright(ptz, request):
    print ('move down left...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = YMIN
    do_move(ptz, request)

def zoom_in(ptz, request):
    print ('zoom in...')
    request.Velocity.Zoom.x = MAX_ZOOM
    do_move(ptz, request)

def zoom_out(ptz, request):
    print ('zoom out...')
    request.Velocity.Zoom.x = MIN_ZOOM
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

    # Get PTZ configuration options for getting continuous move range
    request = ptz.create_type('GetConfigurationOptions')
    request.ConfigurationToken = media_profile.PTZConfiguration.token
    ptz_configuration_options = ptz.GetConfigurationOptions(request)

    global moverequest
    # moverequest = ptz.create_type('AbsoluteMove')
    moverequest = ptz.create_type('ContinuousMove')
    moverequest.ProfileToken = media_profile.token
    if moverequest.Velocity is None:
        moverequest.Velocity = ptz.GetStatus({'ProfileToken': media_profile.token}).Position

    # Get range of pan and tilt
    # NOTE: X and Y are velocity vector
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
    lov=[ x for x in selection.split(" ") if x != ""]
    if lov:
        
        if lov[0].lower() in ["u","up"]:
            move_up(ptz,moverequest)
        elif lov[0].lower() in ["d","do","dow","down"]:
            move_down(ptz,moverequest)
        elif lov[0].lower() in ["l","le","lef","left"]:
            move_left(ptz,moverequest)
        elif lov[0].lower() in ["l","le","lef","left"]:
            move_left(ptz,moverequest)
        elif lov[0].lower() in ["r","ri","rig","righ","right"]:
            move_right(ptz,moverequest)
        elif lov[0].lower() in ["ul"]:
            move_upleft(ptz,moverequest)
        elif lov[0].lower() in ["ur"]:
            move_upright(ptz,moverequest)
        elif lov[0].lower() in ["dl"]:
            move_downleft(ptz,moverequest)
        elif lov[0].lower() in ["dr"]:
            move_downright(ptz,moverequest)
        elif lov[0].lower() in ["zi"]:
            zoom_in(ptz,moverequest)
        elif lov[0].lower() in ["zo"]:
            zoom_out(ptz,moverequest)
        elif lov[0].lower() in ["s","st","sto","stop"]:
            ptz.Stop({'ProfileToken': moverequest.ProfileToken})
            active = False
        else:
            print("What are you asking?\tI only know, 'up','down','left','right', 'ul' (up left), \n\t\t\t'ur' (up right), 'dl' (down left), 'dr' (down right) and 'stop'")
         
    print("")
    print("Your command: ", end='',flush=True)
       
            
if __name__ == '__main__':
    setup_move()
    loop = asyncio.get_event_loop()
    try:
        loop.add_reader(sys.stdin,readin)
        print("Use Ctrl-C to quit")
        print("Your command: ", end='',flush=True)
        loop.run_forever()
    except:
        pass
    finally:
        loop.remove_reader(sys.stdin)
        loop.close()
