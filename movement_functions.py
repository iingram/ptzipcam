import time

import yaml

import numpy as np

from ptz_camera import PtzCam

import convert
import globals

with open('configs.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
ONVIF_PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']

with open('config_mow.yaml') as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
PAN_MIN = configs['PAN_MIN']
PAN_MAX = configs['PAN_MAX']
PAN_STEPS = configs['PAN_STEPS']
STEP_DUR = configs['STEP_DUR']
TILT_MIN = configs['TILT_MIN']
TILT_MAX = configs['TILT_MAX']
TILT_STEPS = configs['TILT_STEPS']

def mow_the_lawn():
    """Thread function for moving the camera through a "mow the lawn"
    pattern: panning across, then tilting up a step, panning back, tilting
    up a step, etc.
    """
    # global globals.camera_still
    ptz = PtzCam(IP, ONVIF_PORT, USER, PASS)

    pan_min = convert.degrees_to_command(PAN_MIN, 350.0)
    pan_max = convert.degrees_to_command(PAN_MAX, 350.0)
    ptz.absmove(pan_min, TILT_MIN/45.0)
    time.sleep(3)

    going_forward = True
    going_up = True

    pan_pass_duration_estimate = int(((2 + 2 + STEP_DUR) * PAN_STEPS)/60)

    print('Will take about {} minutes to complete a pan pass.'.format(pan_pass_duration_estimate))

    while True:
        if going_up:
            tilt_positions = np.linspace(TILT_MIN,
                                         TILT_MAX,
                                         TILT_STEPS)
        else:
            tilt_positions = np.linspace(TILT_MAX,
                                         TILT_MIN,
                                         TILT_STEPS)
        for y_pos in tilt_positions:
            if going_forward:
                pan_positions = np.linspace(pan_min,
                                            pan_max,
                                            PAN_STEPS)
            else:
                pan_positions = np.linspace(pan_max,
                                            pan_min,
                                            PAN_STEPS)
            for x_pos in pan_positions:
                ptz.absmove(x_pos, y_pos/45.0)
                x_pos_degrees = convert.pan_command_to_degrees(x_pos, 350.0)
                print('Moving to {x_pos:.2f} degrees pan and {y_pos:.2f} degrees tilt.'.format(x_pos=x_pos_degrees, y_pos=y_pos))
                time.sleep(2)
                globals.camera_still = True
                time.sleep(2)
                globals.camera_still = False
                time.sleep(STEP_DUR)

            going_forward = not going_forward

        going_up = not going_up

    ptz.stop()


def visit_spots():
    """Thread function for moving the camera through a series of spots of interest
    """

    spots = [[210.0, 80.0, 3.0],
             [200.0, 75.0, 1.0],
             [275.0, 60.0, 2.0],
             [300.0, 85.0, 0.0]]
    
    # global globals.camera_still
    ptz = PtzCam(IP, ONVIF_PORT, USER, PASS)

    while True:
        for pan_degrees, tilt_degrees, zoom_factor in spots:
            print('Moving to {pan_degrees:.2f} degrees pan, {tilt_degrees:.2f} degrees tilt, {zoom_factor:.1f}x zoom'.format(pan_degrees=pan_degrees, tilt_degrees=tilt_degrees, zoom_factor=zoom_factor))
            pan_command = convert.degrees_to_command(pan_degrees, 350.0)
            tilt_command = convert.degrees_to_command(tilt_degrees, 90.0)
            zoom_command = zoom_factor/25.0

            ptz.absmove_w_zoom(pan_command, tilt_command, zoom_command)
            time.sleep(15)
            globals.camera_still = True
            time.sleep(2)
            globals.camera_still = False
            time.sleep(STEP_DUR)

    ptz.stop()
