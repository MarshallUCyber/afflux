# By Marshall University on 7/12/2021
# Image a jailbroken device over SSH

import argparse

from colorama import reinit, Fore

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class DiskImage(plugin_manager.Plugin):
    """
        This class is used to image a folder or files from the local disk.
    """

    def __init__(self):
        """
            Constructor for Disk Imager Plugin.
        """
        super().__init__()
        # Values used to select the plugin and show a description of the plugin.
        self.name = "disk_image"
        self.description = "Image a file or folder on the local disk."

        # Variables used by the plugin.
        self.arguments = None
        self.parser = None

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        """
            Setup arguments required by the plugin. Any arguments not recognized as default Afflux arguments are passed
            as `plugin_args`.
        """

        # Setup parser to include parent arguments.
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}Local Disk Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter,
                                              add_help=False)
        self.parser.add_argument('-f', "--folder", action="store", nargs="*",
                                 help='create image from a local folder.')
        self.parser.add_argument('-F', "--file", action="store", nargs="*",
                                 help='create image from a local file or files.')
        self.parser.add_argument('-r', "--recursive", action="store_true", default=False,
                                 help='add files and folders recursively.')
        self.parser.add_argument('-s', "--symlinks", action="store_true",
                                 help='follow and image any symlinks.')
        # Parse afflux and plugin arguments, and store them in `self.arguments`.
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded Disk Imaging plugin.")
        imager = imaging.Imager(self.arguments.verbose, zip=self.arguments.zip)
        # Image a folder
        if self.arguments.folder or self.arguments.file:
            if self.arguments.folder:
                imager.add_path_names(self.arguments.output[0],             # Output AFF4 container name.
                                      self.arguments.folder,                # Path names to image.
                                      self.arguments.recursive,             # Recursively image.
                                      self.arguments.append,                # Append files to pre-existing image.
                                      self.arguments.container_password,    # Encryption password.
                                      symlinks=self.arguments.symlinks)     # Enable symlinks.

            # Image a file
            elif self.arguments.file:
                imager.add_path_names(self.arguments.output[0],
                                      self.arguments.file,
                                      self.arguments.recursive,
                                      self.arguments.append,
                                      self.arguments.container_password,
                                      symlinks=self.arguments.symlinks)
            return True
        else:
            utils.multi_print(f"{Fore.RED} \n[-] No folder or file supplied.")
            return False
