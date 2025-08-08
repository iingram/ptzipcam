import logging
import time

import yaml

import numpy as np

from ptzipcam.io import read_configs
from ptzipcam.ptz_camera import PtzCam

from ptzipcam import convert
import globalvars

log = logging.getLogger(__name__)




def mow_the_lawn(zoom_power, config_file):
    """Thread function for moving the camera through a "mow the lawn"
    pattern: panning across, then tilting up a step, panning back, tilting
    up a step, etc.
    """
    zoom_factor = 4.0
    raster_pattern = True

    configs = read_configs(config_file)
    timelapse_configs = read_configs(configs['TIMELAPSE_CONFIG_FILENAME'])

    log.info("Grid: %d %d",
             timelapse_configs['PAN_STEPS'],
             timelapse_configs['TILT_STEPS'])
    globalvars.grid = (timelapse_configs['PAN_STEPS'],
                       timelapse_configs['TILT_STEPS'])

    # global globalvars.camera_still
    ptz = PtzCam(
        configs['IP'],
        configs['PORT'],
        configs['USER'],
        configs['PASS']
    )

    log.info("Connected to camera.")
    ptz.twitch()
    log.info("Twitching camera so user has some indication things are OK.")

    pan_min = convert.degrees_to_command(timelapse_configs['PAN_MIN'],
                                         350.0)
    pan_max = convert.degrees_to_command(timelapse_configs['PAN_MAX'],
                                         350.0)
    tilt_min = convert.degrees_to_command(timelapse_configs['TILT_MIN'],
                                          90.0)
    tilt_max = convert.degrees_to_command(timelapse_configs['TILT_MAX'],
                                          90.0)
    zoom_command = zoom_factor/zoom_power

    log.info("Moving to initial position. "
             "Pan: %.2f deg, Tilt: %.2f deg, Zoom: %.2f",
             timelapse_configs['PAN_MIN'],
             timelapse_configs['TILT_MIN'],
             zoom_factor)
    ptz.absmove_w_zoom_waitfordone(pan_min,
                                   tilt_min,
                                   zoom_command,
                                   close_enough=.1)
    log.info("Finished moving camera to initial position")

    going_up = True

    step_dur = timelapse_configs['STEP_DUR']
    pan_steps = timelapse_configs['PAN_STEPS']
    pan_pass_duration_estimate = int(((2 + 2 + step_dur) * pan_steps)/60)

    log.info("Will take about %s minutes to complete a pan pass",
             pan_pass_duration_estimate)

    while True:
        going_forward = True

        if going_up:
            tilt_positions = np.linspace(tilt_min,
                                         tilt_max,
                                         timelapse_configs['TILT_STEPS'])
        else:
            tilt_positions = np.linspace(tilt_max,
                                         tilt_min,
                                         timelapse_configs['TILT_STEPS'])
        for y_pos in tilt_positions:
            if going_forward:
                pan_positions = np.linspace(pan_min,
                                            pan_max,
                                            timelapse_configs['PAN_STEPS'])
            else:
                pan_positions = np.linspace(pan_max,
                                            pan_min,
                                            timelapse_configs['PAN_STEPS'])
            for x_pos in pan_positions:
                x_pos_degrees = convert.command_to_degrees(x_pos, 350.0)
                y_pos_degrees = convert.command_to_degrees(y_pos, 90.0)
                log.info("Moving to Pan: %.2f deg, Tilt: %.2f deg",
                         x_pos_degrees,
                         y_pos_degrees)

                ptz.absmove_w_zoom(x_pos, y_pos, zoom_command)
                time.sleep(9)
                globalvars.pan_angle = x_pos_degrees
                globalvars.tilt_angle = y_pos_degrees
                globalvars.camera_still = True
                time.sleep(2)
                globalvars.camera_still = False
                time.sleep(timelapse_configs['STEP_DUR'])

            going_forward = not going_forward

        if not raster_pattern:
            going_up = not going_up

    ptz.stop()


def log_spot(spot_num, spot):
    pan_degrees, tilt_degrees, zoom_factor = spot

    log.info(
        "Moving to spot %d: %.2f deg pan, %.2f deg tilt, %.1fx zoom",
        spot_num,
        pan_degrees,
        tilt_degrees,
        zoom_factor
    )


def visit_spots(zoom_power, config_file):
    """Move camera through a series of spots of interest."""

    configs = read_configs(config_file)
    timelapse_configs = read_configs(configs['TIMELAPSE_CONFIG_FILENAME'])

    with open('spots_to_visit.yaml', 'r', encoding='utf8') as spots_fh:
        spots = yaml.load(spots_fh, Loader=yaml.SafeLoader)
        spots = np.array(spots)

    ptz = PtzCam(
        configs['IP'],
        configs['PORT'],
        configs['USER'],
        configs['PASS']
    )

    while True:
        for num, spot in enumerate(spots):
            pan_degrees, tilt_degrees, zoom_factor = spot

            log_spot(num, spot)

            pan_command = convert.degrees_to_command(pan_degrees, 350.0)
            tilt_command = convert.degrees_to_command(tilt_degrees, 90.0)
            zoom_command = zoom_factor/zoom_power

            ptz.absmove_w_zoom(pan_command, tilt_command, zoom_command)
            time.sleep(2)
            globalvars.camera_still = True
            time.sleep(2)
            globalvars.camera_still = False
            time.sleep(timelapse_configs['STEP_DUR'])

    ptz.stop()


def visit_spots_two_cameras(zoom_power, config_file):
    """Move two cameras through a series of spots of interest."""

    spots = [[210.0, 90.0, 4.0],
             [288.75, 90.0, 4.0],
             [91.88, 85.0, 4.0],
             [10.0, 85.0, 3.0],
             [230.0, 80.0, 2.0],
             [78.0, 80.0, 4.0]]

    configs = read_configs(config_file)
    timelapse_configs = read_configs(configs['TIMELAPSE_CONFIG_FILENAME'])

    ptz = PtzCam(
        configs['IP'],
        configs['PORT'],
        configs['USER'],
        configs['PASS']
    )

    ptz_2 = PtzCam(
        '192.168.1.63',
        configs['PORT'],
        configs['USER'],
        configs['PASS']
    )

    while True:
        for num, spot in enumerate(spots):
            log_spot(num, spot)
            pan_degrees, tilt_degrees, zoom_factor = spot

            pan_command = convert.degrees_to_command(pan_degrees, 350.0)
            tilt_command = convert.degrees_to_command(tilt_degrees, 90.0)
            zoom_command = zoom_factor/zoom_power

            ptz.absmove_w_zoom(pan_command, tilt_command, zoom_command)
            ptz_2.absmove_w_zoom(pan_command, tilt_command, zoom_command)
            time.sleep(2)
            globalvars.camera_still = True
            time.sleep(1)
            globalvars.camera_still = False
            time.sleep(timelapse_configs['STEP_DUR'])

    ptz.stop()
    ptz_2.stop()
