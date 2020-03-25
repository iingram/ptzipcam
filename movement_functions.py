import time

import yaml

import numpy as np

from ptzipcam.ptz_camera import PtzCam

import convert
import globalvars

CONFIG_FILE = 'config.yaml'

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)
# ptz camera networking constants
IP = configs['IP']
ONVIF_PORT = configs['PORT']
USER = configs['USER']
PASS = configs['PASS']


def mow_the_lawn(zoom_power):
    """Thread function for moving the camera through a "mow the lawn"
    pattern: panning across, then tilting up a step, panning back, tilting
    up a step, etc.
    """
    ZOOM_FACTOR = 4.0
    RASTER_PATTERN = True

    with open('config_timelapse.yaml') as f:
        configs = yaml.load(f, Loader=yaml.SafeLoader)
    PAN_MIN = configs['PAN_MIN']
    PAN_MAX = configs['PAN_MAX']
    PAN_STEPS = configs['PAN_STEPS']
    STEP_DUR = configs['STEP_DUR']
    TILT_MIN = configs['TILT_MIN']
    TILT_MAX = configs['TILT_MAX']
    TILT_STEPS = configs['TILT_STEPS']

    print('Grid: {} {}'.format(PAN_STEPS, TILT_STEPS))
    globalvars.grid = (PAN_STEPS, TILT_STEPS)
    
    # global globalvars.camera_still
    ptz = PtzCam(IP, ONVIF_PORT, USER, PASS)

    pan_min = convert.degrees_to_command(PAN_MIN, 350.0)
    pan_max = convert.degrees_to_command(PAN_MAX, 350.0)
    tilt_min = convert.degrees_to_command(TILT_MIN, 90.0)
    tilt_max = convert.degrees_to_command(TILT_MAX, 90.0)
    zoom_command = ZOOM_FACTOR/zoom_power

    ptz.absmove_w_zoom_waitfordone(pan_min, tilt_min, zoom_command, close_enough=.01)

    going_up = True

    pan_pass_duration_estimate = int(((2 + 2 + STEP_DUR) * PAN_STEPS)/60)

    print('Will take about {} minutes to complete a pan pass.'.format(pan_pass_duration_estimate))

    while True:
        going_forward = True

        if going_up:
            tilt_positions = np.linspace(tilt_min,
                                         tilt_max,
                                         TILT_STEPS)
        else:
            tilt_positions = np.linspace(tilt_max,
                                         tilt_min,
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
                # just for printing for user
                x_pos_degrees = convert.pan_command_to_degrees(x_pos, 350.0) 
                y_pos_degrees = convert.pan_command_to_degrees(y_pos, 90.0)
                print('Moving to {x_pos:.2f} degrees pan and {y_pos:.2f} degrees tilt.'.format(x_pos=x_pos_degrees, y_pos=y_pos_degrees))

                ptz.absmove_w_zoom(x_pos, y_pos, zoom_command)
                time.sleep(10)
                globalvars.pan_angle = x_pos_degrees
                globalvars.tilt_angle = y_pos_degrees
                globalvars.camera_still = True
                time.sleep(2)
                globalvars.camera_still = False
                time.sleep(STEP_DUR)

            going_forward = not going_forward

        if RASTER_PATTERN:
            going_up = going_up
        else:
            going_up = not going_up

    ptz.stop()


def visit_spots(zoom_power):
    """Thread function for moving the camera through a series of spots of interest
    """

    with open('config_timelapse.yaml') as f:
        configs = yaml.load(f, Loader=yaml.SafeLoader)
    STEP_DUR = configs['STEP_DUR']
    
    with open('spots_to_visit.yaml', 'r') as f:
        spots = yaml.load(f, Loader=yaml.SafeLoader)
        spots = np.array(spots)
    
    # global globalvars.camera_still
    ptz = PtzCam(IP, ONVIF_PORT, USER, PASS)

    while True:
        for num, spot in enumerate(spots):
            pan_degrees, tilt_degrees, zoom_factor = spot
            print('Moving to spot {num} at {pan_degrees:.2f} degrees pan, {tilt_degrees:.2f} degrees tilt, {zoom_factor:.1f}x zoom'.format(num=num,
                                                                                                                                           pan_degrees=pan_degrees,
                                                                                                                                           tilt_degrees=tilt_degrees,
                                                                                                                                           zoom_factor=zoom_factor))
            pan_command = convert.degrees_to_command(pan_degrees, 350.0)
            tilt_command = convert.degrees_to_command(tilt_degrees, 90.0)
            zoom_command = zoom_factor/zoom_power

            ptz.absmove_w_zoom(pan_command, tilt_command, zoom_command)
            time.sleep(2)
            globalvars.camera_still = True
            time.sleep(2)
            globalvars.camera_still = False
            time.sleep(STEP_DUR)

    ptz.stop()

    
def visit_spots_two_cameras(zoom_power):
    """Thread function for moving two cameras through a series of spots of
    interest

    """

    spots = [[210.0, 90.0, 4.0],
             [288.75, 90.0, 4.0],
             [91.88, 85.0, 4.0],
             [10.0, 85.0, 3.0],
             [230.0, 80.0, 2.0],
             [78.0, 80.0, 4.0]]
             # [345.0, 85.0, 3.5]]
    
    # global globalvars.camera_still
    ptz = PtzCam(IP, ONVIF_PORT, USER, PASS)
    ptz_2 = PtzCam('192.168.1.63', ONVIF_PORT, USER, PASS)

    while True:
        for num, spot in enumerate(spots):
            pan_degrees, tilt_degrees, zoom_factor = spot
            print('Moving to spot {num} at {pan_degrees:.2f} degrees pan, {tilt_degrees:.2f} degrees tilt, {zoom_factor:.1f}x zoom'.format(num=num,
                                                                                                                                           pan_degrees=pan_degrees,
                                                                                                                                           tilt_degrees=tilt_degrees,
                                                                                                                                           zoom_factor=zoom_factor))
            pan_command = convert.degrees_to_command(pan_degrees, 350.0)
            tilt_command = convert.degrees_to_command(tilt_degrees, 90.0)
            zoom_command = zoom_factor/zoom_power

            ptz.absmove_w_zoom(pan_command, tilt_command, zoom_command)
            ptz_2.absmove_w_zoom(pan_command, tilt_command, zoom_command)
            time.sleep(2)
            globalvars.camera_still = True
            time.sleep(1)
            globalvars.camera_still = False
            time.sleep(STEP_DUR)

    ptz.stop()
    ptz_2.stop()
