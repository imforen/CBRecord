"""Manages a run session.

Classes:
    - CBRecord: Encapsulates attributes and functions for the run session.
"""

import logging
import os
import requests
import subprocess

from base64 import b64decode
from datetime import datetime

from cbrecord import const
from cbrecord import init
from cbrecord import ws
from cbrecord import util


class CBRecord:
    """Encapsulates attributes and functions for the run session.

    Object variables:
        - cbr_config: Configuration dictionary.
        - session: Web session object.
        - record_tasks: Information holder of record tasks.
        - cycle: Counter of the run session cycles.

    Functions:
        - __init__: Constructor.
        - do_cycle: Do a cycle.
        - clean_record_tasks: Clean record tasks list, remove ended processes.
        - record_ended: Handle an ended record task.
        - process_models: Process model if isn't already being recorded.
        - is_recording: Check if model is already being recorded.
        - record: Start recording.
        - kill_processes: Kill all processes in the tasks list.
    """
    def __init__(self):
        """Constructor."""
        logger = logging.getLogger(__name__ + ".init")

        self.cbr_config = {
            'username': None,
            'password': None,
            'crtimer': None,
        }
        self.session = None
        self.record_tasks = []
        self.cycle = 0

        init.startup_init(self)
        util.check_streamlink(self)

        self.session = requests.Session()
        logger.info("HTTP session created.")

        url = b64decode(b'aHR0cHM6Ly9jaGF0dXJiYXRlLmNvbS8=').decode("utf-8")
        ws.make_request(url, self, True)

        logger.info("Cycle repeat timer: {} seconds.".format(
            self.cbr_config['crtimer']
        ))

        logger.info("Listening to followed models.")

    def do_cycle(self):
        """Do a cycle."""
        self.cycle += 1

        self.clean_record_tasks()

        modelList = ws.get_models(self)
        self.process_models(modelList)

    def clean_record_tasks(self):
        """Clean record tasks list, remove ended processes."""
        logger = logging.getLogger(__name__ + ".clean_record_tasks")
        remove = []

        for task in self.record_tasks:
            if task['process'].poll() is not None:
                remove.append(task['id'])
                self.record_ended(task)
            else:
                if self.cycle % 2 == 0:
                    size = os.path.getsize(task['file'])
                    if size == task['size']:
                        remove.append(task['id'])
                        task['process'].terminate()
                        logger.debug("Process stuck: {}.".format(task['id']))
                        self.record_ended(task)
                    else:
                        task['size'] = size

        if len(remove) > 0:
            logger.debug("Ended tasks to be removed: {}.".format(remove))
            temp = [item for item in self.record_tasks
                    if item['id'] not in remove]
            self.record_tasks = temp

    def record_ended(self, task):
        """Handle an ended record task.

        Parameters:
            - task (dict): Informations about the ended task.
        """
        logger = logging.getLogger(__name__ + ".record_ended")

        logger.info("Record END: {}:{}.".format(task['id'], task['model']))

        if os.path.isfile(task['file']):
            if os.path.getsize(task['file']) == 0:
                os.remove(task['file'])
                logger.debug("Removed 0 size recording: {}:{}.".format(
                    task['id'],
                    task['file']))

    def process_models(self, models):
        """Process model if isn't already being recorded.

        Parameters:
            - models (list): List of available models.
        """
        for model in models:
            if self.is_recording(model) is True:
                continue
            self.record(model)

    def is_recording(self, model):
        """Check if model is already being recorded.

        Parameters:
            - model (string): Model to check.
        """
        for task in self.record_tasks:
            if task['model'] == model:
                return True
        return False

    def record(self, model):
        """Start recording.

        Parameters:
            - model (string): Model to record.
        """
        logger = logging.getLogger(__name__ + ".record")
        path = "{}{}/{}/".format(const.RECORDINGS_PATH,
                                 model,
                                 datetime.now().strftime('%Y-%m-%d'))

        util.create_dir(path)
        i = 1
        while os.path.exists(path + "rec_%s.ts" % i):
            i += 1
        file = path + "rec_" + str(i) + ".ts"

        url = b64decode(b'Y2hhdHVyYmF0ZS5jb20v').decode("utf-8")
        cmd = [
            'streamlink',
            url + model,
            'best',
            '--quiet',
            '--output', file,
            '--force'
        ]

        process = subprocess.Popen(cmd,
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        try:
            process.wait(4)
            logger.debug("Can not start record: {}:{}.".format(process.pid,
                                                               model))
        except subprocess.TimeoutExpired as ex:
            self.record_tasks.append({
                'id': process.pid,
                'model': model,
                'process': process,
                'file': file,
                'size': 0
            })

            logger.info("Record START: {}:{}.".format(process.pid, model))

    def kill_processes(self):
        """Kill all process in the tasks list."""
        for task in self.record_tasks:
            if task['process'].poll() is not None:
                task['process'].terminate()
