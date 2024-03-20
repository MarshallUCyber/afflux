# By Marshall University on 7/12/2021
# Utilities for printing to terminal and the GUI

from re import compile, sub
from time import mktime
from datetime import datetime
from os import utime


class Utilities:
    """
        This class is used to handle outputting between the GUI and console, and other stuff.
    """
    __instance = None

    @staticmethod                                           # We need one single instance of this class shared across
    def get_instance():                                     # several modules.
        """ Static access method. """
        if Utilities.__instance is None:
            Utilities()
        return Utilities.__instance

    def __init__(self):
        """
            Constructor for Utilities class.
        """

        self.worker = None
        Utilities.__instance = self
        self.gui = False
        self.textBrowser = None
        self.reaesc = compile(r'\x1b[^m]*m')

    def set_gui(self):
        """
            Called when the GUI is initialized and allows for output to be sent to the GUI.
        """

        self.gui = True

    def set_text_worker(self, worker_thread):
        """
            Called to set up the worker from the GUI to handle outputting to the GUI windows.
        """

        self.worker = worker_thread

    def multi_print(self, output, worker=True):
        """
            Prints information to the console when the command line application is used, and also prints to the GUI
            output window when the GUI is used. `worker` is used from `plugin_manager.py` since it gets loaded before
            the PyQt signals.
        """

        if self.gui is True:
            if worker is True:
                try:
                    # Remove any terminal coloring
                    new_text = self.reaesc.sub('', output)

                    # Emit a signal for PyQt to print to the output box
                    worker = self.worker.signal
                    worker.emit(new_text.strip("\t"))
                except:
                    pass
        print(output)

    def check_file_names(self, file):
        """
            Check and change file names if the name is not supported on Windows. Originally from
            https://github.com/jfarley248/pymobiledevice2.
        """

        windows_reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'CLOCK$',
                                  'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM0',
                                  'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9', 'LPT0']
        file = file[:3] + sub('[<>:"|?* ]', '_', file[3:]).strip().replace("../", "").replace("..\\", "")
        for name in windows_reserved_names:
            if name in file.strip():
                file = sub(name, name + "_AFFLUX_RENAMED", file)
        return file

    def modify_time(self, info, file, st_mtime=True):
        """
            Modify timestamps on a file. Used to set the original timestamps on a file once it has been copied over AFC
            or ADB.
        """

        if st_mtime:
            date = info['st_mtime']
        else:
            date = info
        modify_time = datetime.fromtimestamp(mktime(date.timetuple()))
        modTime = mktime(modify_time.timetuple())
        utime(file, (modTime, modTime))