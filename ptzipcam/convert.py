import logging

log = logging.getLogger(__name__)


def degrees_to_command(degrees, full_range):
    if degrees > full_range:
        log.warning('Angle higher than full range')
        degrees = full_range
    elif degrees < 0.0:
        log.warning('Angle lower than zero')
        degrees = 0.0

    half_range = full_range/2.0
    return (degrees - half_range)/half_range


def command_to_degrees(command, full_range):
    half_range = full_range/2.0
    return command * half_range + half_range


def zoom_to_power(zoom, camera_zoom_power):
    return (zoom * (camera_zoom_power - 1)) + 1


def power_to_zoom(power, camera_zoom_power):
    if power < 1.0:
        log.warning('Zoom power command is less than 1.0.'
                    + ' Forcing to 1.0')
        power = 1.0

    if power > camera_zoom_power:
        log.warning('Zoom power command is greater than full zoom'
                    + ' Forcing to full zoom')
        power = camera_zoom_power

    return (power - 1)/(camera_zoom_power - 1)
