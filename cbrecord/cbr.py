"""Manages a run session.

Classes:
    - CBRecord: Encapsulates attributes and functions for the run session.
"""

import os
import requests
import subprocess

from base64 import b64decode
from datetime import datetime

from cbrecord import const
from cbrecord import init
from cbrecord import ws
from cbrecord import util
from cbrecord.util import log


class CBRecord:
    """Encapsulates attributes and functions for the run session.

    Object variables:
        - runlog: The Python logger.
        - debugLog: The Python logger for debugging.
        - cbr_config: Configuration dictionary.
        - session: Web session object.
        - tasks: Information holder of Streamlink and FFmpeg tasks.
        - cycle: Counter of the run session cycles.

    Functions:
        - __init__: Constructor.
        - do_cycle: Do a cycle.
        - clean_tasks: Clean tasks list, remove ended processes.
        - streamlink_ended: Handle an ended Streamlink task.
        - run_ffmpeg: Run FFmpeg to re-encode the video.
        - ffmpeg_ended: Handle an ended FFmpeg task.
        - process_models: Process model if isn't already being recorded.
        - is_recording: Check if model is already being recorded.
        - record: Start recording.
        - kill_processes: Kill all processes in the tasks list.
    """
    def __init__(self):
        """Constructor."""
        self.runLog = None
        self.debugLog = None
        self.cbr_config = {
            'username': None,
            'password': None,
            'crtimer': None,
            'ffmpeg': None,
            'ffmpeg-flags': None
        }
        self.session = None
        self.tasks = []
        self.cycle = 0

        init.startup_init(self)
        log("Startup initializations OK", self)

        util.check_sl_ffmpeg(self)

        self.session = requests.Session()
        log("HTTP session created", self)

        url = b64decode(b'aHR0cHM6Ly9jaGF0dXJiYXRlLmNvbS8=').decode("utf-8")
        ws.make_request(url, self, True)

        log("Cycle repeat timer: {} seconds".format(
            self.cbr_config['crtimer']),
            self)

        log("Listening to followed models", self, 20)

    def do_cycle(self):
        """Do a cycle."""
        self.cycle += 1

        self.clean_tasks()

        modelList = ws.get_models(self)
        self.process_models(modelList)

    def clean_tasks(self):
        """Clean tasks list, remove ended processes."""
        remove = []

        for task in self.tasks:
            if task['process'].poll() is not None:
                remove.append(task['id'])
                if task['type'] == 'streamlink':
                    self.streamlink_ended(task)
                elif task['type'] == 'ffmpeg':
                    self.ffmpeg_ended(task)
            else:
                if self.cycle % 2 == 0:
                    size = os.path.getsize(task['file'])
                    if size == task['size']:
                        remove.append(task['id'])
                        task['process'].terminate()
                        log("Process stuck: ", self, 10, task['id'])
                        self.streamlink_ended(task)
                    else:
                        task['size'] = size

        if len(remove) > 0:
            log("Remove tasks: ", self, 10, remove)
            temp = [item for item in self.tasks if item['id'] not in remove]
            self.tasks = temp

    def streamlink_ended(self, task):
        """Handle an ended Streamlink task.

        Parameters:
            - task (dict): Informations about the ended task.
        """
        log("Record END: ", self, 20, "{}:{}".format(task['id'],
                                                     task['model']))
        if os.path.isfile(task['file']):
            if os.path.getsize(task['file']) > 0:
                if self.cbr_config['ffmpeg'] is True:
                    self.run_ffmpeg(task)
            else:
                log("Removing 0 size recording: ", self, 10, task['file'])
                os.remove(task['file'])

    def run_ffmpeg(self, task):
        """Run FFmpeg to re-encode the video.

        Parameters:
            - task (dict): Informations about the ended task.
        """
        ffmpeg_file = task['file'].replace(".ts", ".mp4")

        cmd = [
            ['ffmpeg', '-nostats', '-loglevel', 'quiet', '-y', '-i',
             task['file']],
            self.config['ffmpeg-flags'].split(),
            [ffmpeg_file]
        ]
        cmd = [item for sublist in cmd for item in sublist]

        ffmpeg_process = subprocess.Popen(cmd,
                                          shell=False,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)

        self.tasks.append({
            'id': ffmpeg_process.pid,
            'model': task['model'],
            'process': ffmpeg_process,
            'type': 'ffmpeg',
            'file': task['file'],
            'ffmpeg_file': ffmpeg_file
        })

        log("Encode START: ", self, 20, "{}:{}".format(ffmpeg_process.pid,
                                                       task['model']))

    def ffmpeg_ended(self, task):
        """Handle an ended FFmpeg task.

        Parameters:
            - task (dict): Informations about the ended task.
        """
        if task['process'].poll() == 0:
            log("Encode END: ", self, 20, "{}:{}".format(task['id'],
                                                         task['model']))
            os.remove(task['file'])
        else:
            log("Encode ERROR: ", self, 30, "{}:{}".format(task['id'],
                                                           task['model']))

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
        for task in self.tasks:
            if task['model'] == model and task['type'] == 'streamlink':
                return True
        return False

    def record(self, model):
        """Start recording.

        Parameters:
            - model (string): Model to record.
        """
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
            log("Can not start record: ", self, 10,
                "{}:{}".format(process.pid, model))
        except subprocess.TimeoutExpired as ex:
            self.tasks.append({
                'id': process.pid,
                'model': model,
                'process': process,
                'type': 'streamlink',
                'file': file,
                'size': 0
            })

            log("Record START: ", self, 20, "{}:{}".format(process.pid, model))

    def kill_processes(self):
        """Kill all process in the tasks list."""
        for task in self.tasks:
            if task['process'].poll() is not None:
                task['process'].terminate()
