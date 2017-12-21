"""
Defines logging in CloudWatch
"""

import logging
import sys


def configure_logging(debug=False, silent=False):
    """
    Sets the logger to appropriate levels of chattiness.
    """

    logger = logging.getLogger('')

    if silent and debug:
        raise Exception('Debug and silent logging options are mutually exclusive')

    if silent:
        logging.disable(logging.CRITICAL)
    elif debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # If there are any handlers on the root logger, remove them so that if this function is called more
    # than once, we don't get the same statement logged multiple times.
    for handler in logger.handlers:
        logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.__stdout__)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
    logger.addHandler(stream_handler)
