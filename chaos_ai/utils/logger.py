import click
import logging

def verbosity_to_level(verbosity: int) -> int:
    if verbosity == 0:
        return logging.INFO
    else:
        return logging.DEBUG

def get_module_logger(mod_name):
    '''Main Logging module'''
    try:
        ctx = click.get_current_context()
    except RuntimeError:
        ctx = None

    logger = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    if ctx:
        logger.setLevel(ctx.obj.verbose)
    else:
        logger.setLevel(logging.INFO)

    return logger
