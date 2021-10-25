import logging


def prep_log(level):
    log = logging.getLogger()
    log.setLevel(level)
    if log.hasHandlers():
        log.handlers.clear()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s (%(name)s)')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    return log


def log_configuration(log, configs):
    log.info('-----------------------------------')
    log.info("Detection threshold: " + str(configs['CONF_THRESHOLD']))
    log.info('Tracked classes: ' + str(configs['TRACKED_CLASS']))
    ipan, itilt, izoom = configs['INIT_POS']
    log.info(f'Initial position: {ipan} pan, {itilt} tilt, {izoom} zoom')
    
    if configs['RECORD']:
        log.info('Recording is turned ON')
        strg = configs['RECORD_FOLDER']
        log.info('Recordings will be stored in {}'.format(strg))
        strg = configs['TIMELAPSE_DELAY']
        log.info(f'{strg} seconds between timelapse frames.')
    else:
        log.info('Recording is turned OFF')

    if configs['RECORD_ONLY_DETECTIONS']:
        log.info('Record only detections: True')

    log.info('-----------------------------------')
