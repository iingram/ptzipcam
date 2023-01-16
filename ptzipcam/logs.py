"""Logging configuration, customization, and helpers.

"""

import logging


def prep_log(level, suppress_verbose_loggers=True):
    """Prepare logging

    Parameters
    ----------

    level :

    suppress_verbose_loggers : bool

        A lot of this code's dependencies have very verbose debug
        logging that is often not wanted when debugging more local
        issues.  This flag allows toggling suppression of those.

    Returns
    -------

    log :

    """
    log = logging.getLogger()
    log.setLevel(level)
    if log.hasHandlers():
        log.handlers.clear()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s (%(name)s)')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    if suppress_verbose_loggers:
        dont_log_list = ['zeep.xsd.schema', 'zeep', 'zeep.transports',
                         'urllib3.connectionpool', 'zeep.wsdl.wsdl',
                         'zeep.xsd.visitor']
        for blisted in dont_log_list:
            logging.getLogger(blisted).disabled = True

    return log


def log_configuration(log, configs):
    """Logs some of the configuration parameters for current run

    """
    log.info('-----------------------------------')
    log.info("Detection threshold: " + str(configs['CONF_THRESHOLD']))
    log.info('Tracked classes: ' + str(configs['TRACKED_CLASS']))
    ipan, itilt, izoom = configs['INIT_POS']
    log.info(f'Initial position: {ipan} pan, {itilt} tilt, {izoom} zoom')

    if configs['RECORD']:
        log.info('Recording is turned ON')
        strg = configs['RECORD_FOLDER']
        log.info(f'Recordings will be stored in {strg}')
        strg = configs['TIMELAPSE_DELAY']
        log.info(f'{strg} seconds between timelapse frames.')
    else:
        log.info('Recording is turned OFF')

    if configs['RECORD_ONLY_DETECTIONS']:
        log.info('Record only detections: True')

    log.info('-----------------------------------')
