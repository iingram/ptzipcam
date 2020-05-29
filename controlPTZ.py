import yaml

import cv2

from ptzipcam.camera import Camera
from ptzipcam.ptz_camera import PtzCam

with open('config.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']
STREAM = configs['STREAM']

# ptz camera setup constants
INIT_POS = configs['INIT_POS']
ORIENTATION = configs['ORIENTATION']

cam = Camera(ip=IP, user=USER, passwd=PASS, stream=2)

Y_DELTA = .1
Y_DELTA_FINE = .01
X_DELTA = .1
X_DELTA_FINE = .01
Z_DELTA = .1

if __name__ == '__main__':
    ptz = PtzCam(IP, PORT, USER, PASS)

    pan, tilt, zoom = ptz.get_position()
    pan_command = INIT_POS[0]/180.0
    tilt_command = INIT_POS[1]/45.0
    zoom_command = INIT_POS[2]/25.0

    ptz.absmove_w_zoom_waitfordone(pan_command,
                                   tilt_command,
                                   zoom_command,
                                   close_enough=.01)
    
    key = 'd'

    print("Keys:\n",
          "w: quit\n",
          "k: up\n",
          "m: up (fine)\n",
          "i: down\n",
          "u: down (fine)\n",
          "j: left\n",
          "h: left (fine)\n",
          "l: right\n",
          "p: right (fine)\n",
          "z: zoom in (full)\n",
          "a: zoom out (full)\n")

    
    
    while True:

        if key == ord('w'):
            break
        elif key == ord('i'):
            # move_up(ptz, moverequest)
            tilt_command -= Y_DELTA 
        elif key == ord('u'):
            # move_up(ptz, moverequest, fine=True)
            tilt_command -= Y_DELTA_FINE
        elif key == ord('k'):
            # move_down(ptz, moverequest)
            tilt_command += Y_DELTA
        elif key == ord('m'):
            # move_down(ptz, moverequest, fine=True)
            tilt_command += Y_DELTA_FINE
        elif key == ord('j'):
            # move_right(ptz, moverequest)
            pan_command += X_DELTA
        elif key == ord('h'):
            # move_right(ptz, moverequest, fine=True)
            pan_command += X_DELTA_FINE
        elif key == ord('l'):
            # move_left(ptz, moverequest)
            pan_command -= X_DELTA
        elif key == ord('p'):
            # move_left(ptz, moverequest, fine=True)
            pan_command -= X_DELTA_FINE
        elif key == ord('z'):
            # zoom_in(ptz, moverequest)
            zoom_command += X_DELTA
        elif key == ord('a'):
            # zoom_out(ptz, moverequest)
            zoom_command -= X_DELTA
        elif key == ord('u'):
            pass

        def keep_in_bounds(command, minn, maxx):
            if command <= minn:
                command = minn
            elif command >= maxx:
                command = maxx
            return command

        pan_command = keep_in_bounds(pan_command, -1.0, 1.0)
        tilt_command = keep_in_bounds(tilt_command, 0.0, 1.0)
        zoom_command = keep_in_bounds(zoom_command, 0.0, 1.0)
        
        ptz.absmove_w_zoom(pan_command,
                           tilt_command,
                           zoom_command)

        print("Pan: {:.2f}, Tilt: {:.2f}, Zoom: {:.2f}".format(pan_command,
                                                               tilt_command,
                                                               zoom_command))
        
        frame = None
        frame = cam.get_frame()
        if frame is not None:
            cv2.imshow('Control PTZ Camera', frame)
            key = cv2.waitKey(0)
            
    cv2.destroyAllWindows()
