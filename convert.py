def degrees_to_pan_command(degrees, full_range):
    if degrees > full_range:
        logging.error('Angle higher than full range')
        degrees = full_range
    elif degrees < 0.0:
        logging.error('Angle lower than zero')
        degrees = 0.0

    half_range = full_range/2.0
    return (degrees - half_range)/half_range


def pan_command_to_degrees(command, full_range):
    half_range = full_range/2.0
    return command * half_range + half_range
