"""Contains utility functions.

Fuctions:
    - check_sl_ffmpeg: Check if Streamlink and FFmpeg is installed.
    - create_dir: Create directory with the given path.
    - log: Send message to the logs.
"""

import os
import whichcraft


def check_sl_ffmpeg(cbr):
    """Check if Streamlink and FFmpeg is installed.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    if whichcraft.which('streamlink') is not None:
        log("Streamlink OK", cbr)
    else:
        log("Streamlink not found", cbr, 40)
        print("Visit: https://streamlink.github.io/install.html.")
        raise SystemExit(1)

    if whichcraft.which('ffmpeg') is not None:
        log("FFmpeg OK", cbr)
    else:
        log("FFmpeg not found", cbr, 40)
        print("Visit: https://www.ffmpeg.org/download.html.")
        raise SystemExit(1)


def create_dir(path):
    """Create directory with the given path.

    Parameters:
        - path (string): Directory to create given as path.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def log(msg, cbr, logger=20, altmsg=""):
    """Send message to the logs.

    Parameters:
        - msg (string): Message to send to logs.
        - cbr (object): The run session object (CBRecord class).
        - logger=20 (object): The selected Python logger.
        - altmsg="" (string): Alternative message to send to logs.
    """
    cycle = 0
    if cbr is not None:
        cycle = cbr.cycle

    message = "({}) {}{}.".format(cycle, msg, altmsg)

    if logger == 10:
        cbr.debugLog.debug(message)
    elif logger == 20:
        cbr.runLog.info(message)
        cbr.debugLog.info(message)
    elif logger == 30:
        cbr.runLog.warning(message)
        cbr.debugLog.warning(message)
    elif logger == 40:
        cbr.runLog.error(message)
        cbr.debugLog.error(message)
    elif logger == 50:
        cbr.runLog.critical(message)
        cbr.debugLog.critical(message)
