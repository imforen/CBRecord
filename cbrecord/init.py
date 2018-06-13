"""Performs initializations.

Fuctions:
    - startup_init: Perform startup initializations.
    - init_logging: Initialize logging functionality.
    - init_config_loading: Initialize configuration holding functionality.
"""

import configparser
import logging
import os

from cbrecord import const
from cbrecord import util


def startup_init(cbr):
    """Perform startup initializations.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    logger = logging.getLogger(__name__ + ".startup_init")

    util.create_dir(const.CONFIG_DIR)
    init_config_loading(cbr)
    logger.info("Startup initializations OK.")


def init_config_loading(cbr):
    """Initialize configuration holding functionality.

    Parameters:
        - cbr (object): The run session object (CBRecord class).
    """
    file = const.CONFIG_DIR + const.CONFIG_FN

    if not os.path.exists(file):
        with open(file, 'w+') as f:
            f.write("[User]\nusername=\npassword=\n\n" +
                    "[Settings]\n" +
                    "# Cycle repeat timer in seconds (default: 60, " +
                    "minimum: 30)\ncrtimer=60")
        print("You need to set your login information.")
        raise SystemExit(0)

    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(const.CONFIG_DIR + const.CONFIG_FN)
        cbr.cbr_config['username'] = config_parser.get('User', 'username')
        cbr.cbr_config['password'] = config_parser.get('User', 'password')

        try:
            crtimer = int(config_parser.get('Settings', 'crtimer'))
            if crtimer < 30 or crtimer > 86400:
                crtimer = 60
            cbr.cbr_config['crtimer'] = crtimer
        except (ValueError, configparser.NoSectionError):
            cbr.cbr_config['crtimer'] = 60
    except (Exception, configparser.Error):
        if os.path.exists(file):
            os.remove(file)
        init_config_loading(cbr)
