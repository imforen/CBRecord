"""Contains utility functions.

Fuctions:
    - check_sl_ffmpeg: Check if Streamlink and FFmpeg is installed.
    - create_dir: Create directory with the given path.
    - log: Send message to the logs.
"""

import logging
import os
import whichcraft


def check_sl_ffmpeg(cbr):
    """Check if Streamlink and FFmpeg is installed.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    logger = logging.getLogger(__name__ + ".check_sl_ffmpeg")

    if whichcraft.which('streamlink') is not None:
        logger.info("Streamlink OK.")
    else:
        logger.critical("Streamlink not found.")
        print("Visit: https://streamlink.github.io/install.html.")
        raise SystemExit(1)

    if whichcraft.which('ffmpeg') is not None:
        logger.info("FFmpeg OK.")
    else:
        logger.error("FFmpeg not found.")
        print("Visit: https://www.ffmpeg.org/download.html.")
        raise SystemExit(1)


def create_dir(path):
    """Create directory with the given path.

    Parameters:
        - path (string): Directory to create given as path.
    """
    logger = logging.getLogger(__name__ + ".create_dir")

    if not os.path.exists(path):
        os.makedirs(path)
        logger.debug("Directory created: {}.".format(path))
