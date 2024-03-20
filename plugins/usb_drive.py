# By Marshall University on 7/12/2021
# Plugin for imaging a USB drive or mounted device

import argparse
from getpass import getuser
from os import chdir, getcwd

from colorama import reinit, Fore

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class UsbDriveImage(plugin_manager.Plugin):
    """
        This class is used to connect to a device via SSH, copy files from the device, then image those files.
    """

    def __init__(self):
        """
            Constructor for Disk imager Plugin.
        """
        super().__init__()
        self.name = "usb_drive"
        self.description = "Image a local USB device or mounted drive."
        self.arguments = None
        self.parser = None

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}USB Drive Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter,
                                              add_help=False)
        self.parser.add_argument('-u', "--usb", action="store", metavar='USB NAME',
                                 help='create image from a connected USB device.')
        self.parser.add_argument('-s', "--symlinks", action="store_true",
                                 help='follow and image any symlinks.')
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded USB Imaging plugin.")
        if self.arguments.usb:
            image_path, output_path = "", ""
            current_path = getcwd()
            imager = imaging.Imager(self.arguments.verbose, zip=self.arguments.zip)
            utils.multi_print(f"{Fore.GREEN}[*] Make sure your USB device is mounted.")
            if '/' in self.arguments.usb or '\\' in self.arguments.usb:
                image_path = self.arguments.usb
            else:
                if imager.os == "Linux":
                    chdir("/media/%s" % getuser())
                    image_path = "%s/" % self.arguments.usb
                    output_path = current_path + "/" + self.arguments.output[0]
                elif imager.os == "Windows":
                    image_path = "%s:\\" % self.arguments.usb[0]
                    output_path = current_path + "\\" + self.arguments.output[0]
            imager.add_path_names(output_path,
                                  [image_path],
                                  True,
                                  self.arguments.append,
                                  self.arguments.container_password,
                                  symlinks=self.arguments.symlinks)
            chdir(current_path)
            return True
        else:
            self.parser.print_help()
            return False
