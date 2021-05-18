import logging


def prep_log():
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    if log.hasHandlers():
        log.handlers.clear()
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s (%(name)s)')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    return log
