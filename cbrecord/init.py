"""Performs initializations.

Fuctions:
    - startup_init: Perform startup initializations.
    - init_logging: Initialize logging functionality.
    - init_config_loading: Initialize configuration holding functionality.
"""

import configparser
import logging
import os

from logging import config

from cbrecord import const
from cbrecord import util


def startup_init(cbr):
    """Perform startup initializations.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    util.create_dir(const.LOGS_DIR)
    util.create_dir(const.CONFIG_DIR)
    init_logging(cbr)
    init_config_loading(cbr)


def init_logging(cbr):
    """Initialize logging functionality.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    file = const.CONFIG_DIR + const.LOGGING_FN

    if not os.path.exists(file):
        with open(file, 'w+') as f:
            f.write("[loggers]\nkeys=root, runLog, debugLog\n\n" +
                    "[handlers]\nkeys=consoleHandler, runLogHandler, " +
                    "debugLogHandler\n\n" +
                    "[formatters]\nkeys=genericFormatter\n\n" +
                    "[logger_root]\nlevel=DEBUG\nhandlers=consoleHandler\n\n" +
                    "[logger_runLog]\nlevel=DEBUG\nhandlers=runLogHandler\n" +
                    "propagate=1\nqualname=runLog\n\n" +
                    "[logger_debugLog]\nlevel=DEBUG\n" +
                    "handlers=debugLogHandler\n" +
                    "propagate=0\nqualname=debugLog\n\n" +
                    "[handler_consoleHandler]\nclass=StreamHandler\n" +
                    "level=DEBUG\nformatter=genericFormatter\n" +
                    "args=(sys.stdout, )\n\n" +
                    "[handler_runLogHandler]\n" +
                    "class=handlers.RotatingFileHandler\n" +
                    "level=DEBUG\nformatter=genericFormatter\n" +
                    "args=('logs/log.txt', 'a', 4*1024*1024, 4)\n\n" +
                    "[handler_debugLogHandler]\n" +
                    "class=handlers.RotatingFileHandler\n" +
                    "level=DEBUG\nformatter=genericFormatter\n" +
                    "args=('logs/debug.txt', 'a', 4*1024*1024, 4)\n\n" +
                    "[formatter_genericFormatter]\n" +
                    "format=%(asctime)s [%(levelname)s] %(message)s\n" +
                    "datefmt=%Y-%m-%d %H:%M:%S\nclass=logging.Formatter\n")

    try:
        config.fileConfig(const.CONFIG_DIR + const.LOGGING_FN)
        cbr.runLog = logging.getLogger("runLog")
        cbr.debugLog = logging.getLogger("debugLog")
    except (Exception, configparser.Error):
        if os.path.exists(file):
            os.remove(file)
        init_logging(cbr)


def init_config_loading(cbr):
    """Initialize configuration holding functionality.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    file = const.CONFIG_DIR + const.CONFIG_FN

    if not os.path.exists(file):
        with open(file, 'w+') as f:
            f.write("[User]\nusername=john\npassword=johnpw\n\n" +
                    "[FFmpeg]\nenable=false\n" +
                    "flags=-c:v libx264 -c:a copy -bsf:a aac_adtstoasc")
        print("You need to set your login information.")
        raise SystemExit(0)

    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(const.CONFIG_DIR + const.CONFIG_FN)
        cbr.cbr_config['username'] = config_parser.get('User', 'username')
        cbr.cbr_config['password'] = config_parser.get('User', 'password')

        try:
            cbr.cbr_config['ffmpeg'] = config_parser.getboolean('FFmpeg',
                                                                'enable')
            cbr.cbr_config['ffmpeg-flags'] = config_parser.get('FFmpeg',
                                                               'flags')
        except configparser.NoSectionError:
            pass
    except (Exception, configparser.Error):
        if os.path.exists(file):
            os.remove(file)
        init_config_loading(cbr)
