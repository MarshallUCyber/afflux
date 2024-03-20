# By Marshall University on 7/12/2021
# Image a  device over AFC or AFC2
# Inspired by jfarley248's MEAT and more forensically aimed pymobiledevice2
# His AFC copying method and timestamp copying is implemented here for pymobiledevice3

import argparse
from os import mkdir, chdir, listdir
from posixpath import join as posixpath_join
from shutil import rmtree

from colorama import reinit, Fore
from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import LockdownClient, StartServiceError, LockdownError
from pymobiledevice3.exceptions import NotTrustedError, AfcException, MuxException, PasswordRequiredError, \
    InvalidServiceError
from pymobiledevice3.services.afc import AfcService
from pymobiledevice3.common import get_home_folder

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class IosImagerAFC(plugin_manager.Plugin):
    """
        This class is used to connect to a device via AFC, copy files from the device, then image those files.
    """

    def __init__(self):
        """
            Constructor for the IosImagerAfc class.
        """
        super().__init__()
        self.arguments = None
        self.parser = None
        self.name = "apple_afc"
        self.description = "Image a device that support AFC. Supports jailbroken and non-jailbroken devices."
        self.imager = None
        self.service = None
        self.temp = None

    def walk(self, afc_service, dir_name):
        """
            Walk through all directories on a device via AFC. Adapted from
            https://github.com/jfarley248/pymobiledevice2.
        """

        dirs = []
        files = []
        try:
            for fd in afc_service.listdir(dir_name):
                if fd in ('.', '..', ''):
                    continue
                info = afc_service.stat(posixpath_join(dir_name, fd))
                if info and info.get('st_ifmt') == 'S_IFDIR':
                    dirs.append(fd)
                else:
                    files.append(fd)
        except AfcException as e:
            if 'PERM_DENIED' in str(e):
                if self.arguments.verbose:
                    utils.multi_print(f"{Fore.RED}\tPermission denied: {Fore.RESET}{dir_name}")

        yield dir_name, dirs, files

        if dirs:
            for d in dirs:
                for walk_result in self.walk(afc_service, posixpath_join(dir_name, d)):
                    yield walk_result

    @staticmethod
    def get_device():
        """
            Generate a list of connected iOS devices.
        """

        devices = []
        try:
            connected_devices = usbmux.list_devices()
            for device in connected_devices:
                devices.append(LockdownClient(serial=device.serial, autopair=True))
        except FileNotFoundError:
            utils.multi_print(f"{Fore.RED}[-] Error: Couldn't connect to usbmuxd. If on Linux, run \'sudo usbmuxd\'.")
        except IndexError:
            utils.multi_print(f"{Fore.RED}[-] Error: Couldn't find device.")
        except ConnectionRefusedError:
            utils.multi_print(f"{Fore.RED}[-] Error: Couldn't find device.")
        except PasswordRequiredError:
            utils.multi_print(f"{Fore.RED}[-] Error: You must enter password first.")
        except NotTrustedError:
            utils.multi_print(f"{Fore.RED}[-] Error: Device must be trusted.")
        except MuxException:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to usbmuxd. Try restarting it or launching "
                              f"iTunes.")
        return devices

    def image_device_afc(self, output_file, encryption_password, re_pair, clear_pairs, zip_image, device_num=False):
        """
            Connect to the device, copy files, and initiate imaging of copied files.
        """

        afc = None
        if clear_pairs:
            rmtree(get_home_folder(), ignore_errors=True)
            if self.arguments.verbose:
                utils.multi_print(f"{Fore.GREEN}[*] Removed pairing records.")

        device_list = self.get_device()

        # Check if there are no devices connected.
        if (len(device_list) == 0) or not device_list:
            utils.multi_print(f"{Fore.RED}[-] Error: Couldn't connect to a device.")
            return False

        # Print and let the user decide if there are multiple devices connected.
        # Check if GUI specified a device.
        if device_num is False:
            # Check if there are multiple devices.
            if len(device_list) > 1:
                utils.multi_print(f"{Fore.GREEN}[*] Device List:")
                i = 1
                for device in device_list:
                    utils.multi_print(f"\t{i}. {Fore.GREEN}Device: {Fore.RESET}{device.all_values['DeviceName']},"
                                      f" {Fore.RESET}{device.all_values['ProductType']},"
                                      f" {Fore.RESET}{device.all_values['ProductVersion']}")
                    i += 1
                device_number = input(f"{Fore.GREEN}Device: {Fore.RESET}")
                try:
                    if (int(device_number) - 1) > len(device_list):
                        utils.multi_print(f"{Fore.RED}[-] Error: Device not in the list.")
                        return False
                    device = device_list[int(device_number) - 1]
                except ValueError:
                    utils.multi_print(f"{Fore.RED}[-] Error: You must choose a number.")
                    return False
            else:
                device = device_list[0]
        else:
            device = device_list[device_num]
        # Print device information.
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Found device: {Fore.RESET}{device.all_values['UniqueDeviceID']}")
        utils.multi_print(f"{Fore.GREEN}[+] Connected to: {Fore.RESET}{device.all_values['DeviceName']} "
                          f"({device.all_values['ProductType']}, "
                          f"Model: {device.all_values['HardwareModel']}, "
                          f"Version: {device.all_values['ProductVersion']}, "
                          f"Build: {device.all_values['BuildVersion']}).")

        try:
            if self.arguments.verbose:
                utils.multi_print(f"{Fore.GREEN}[*] Validating pair...")
            # Validating pairing throws a SessionActive error often, try and kill all sessions before validation.
            try:
                device.stop_session()
            except:
                pass
            paired = device.validate_pairing()
            if self.arguments.verbose:
                utils.multi_print(f"{Fore.GREEN}[*] Paired: {Fore.RESET}{paired}")
            if re_pair or not paired:
                device.pair()
                if self.arguments.verbose:
                    utils.multi_print(f"{Fore.GREEN}[*] Device Paired.")

            afc = AfcService(lockdown=LockdownClient(serial=device.all_values['UniqueDeviceID']),
                             service_name=self.service)

        # Catch errors that can happen and give a message.
        except StartServiceError as e:
            utils.multi_print(f"{Fore.RED}[-] Error: Couldn't start service: {Fore.RESET}{str(e)}")
            return False
        except InvalidServiceError:
            utils.multi_print(f"{Fore.RED}[-] Error: Couldn't connect to service.")
            return False
        except NotTrustedError:
            utils.multi_print(f"{Fore.RED}[-] Error: Device must be trusted.")
            return False
        except PasswordRequiredError:
            utils.multi_print(f"{Fore.RED}[-] Error: You must enter password first.")
            return False
        except LockdownError as e:
            utils.multi_print(f"{Fore.RED}[-] Error: Lockdownd: {Fore.RESET}{e}")
            return False

        utils.multi_print(f"{Fore.GREEN}[+] Connected to service.")
        imager = imaging.Imager(self.arguments.verbose, zip=zip_image)
        output_path, old_path, tmp_path = self.imager.setup_tmp_directory(self.temp, output_file)
        chdir(tmp_path)
        utils.multi_print(f"{Fore.GREEN}[+] Pulling filesystem...")
        try:
            data = None
            for file_system in self.walk(afc, "/"):
                # Make directories
                for directory in file_system[1]:
                    full_path = utils.check_file_names(tmp_path + file_system[0].replace("/", self.imager.separator)
                                                       + self.imager.separator + directory)
                    info = afc.stat(file_system[0] + "/" + directory)
                    path = "/"
                    if file_system[0] == "/":
                        path = ""
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.GREEN}\tMaking directory: "
                                          f"{Fore.RESET}{file_system[0] + path + directory}")
                    try:
                        mkdir(full_path)
                    # On Windows, folder names are case-insensitive. This catches and renames them.
                    except FileExistsError:
                        if "_AFFLUX_DUPLICATE_" in full_path:
                            full_path = full_path[:-1] + str(int(full_path[-1]) + 1)
                        else:
                            full_path = full_path + "_AFFLUX_DUPLICATE_FOLDERNAME_1"
                        mkdir(full_path)
                        continue
                    # Change directory modify time
                    utils.modify_time(info, full_path)
                # Make and copy file data
                for file in file_system[2]:
                    info = afc.stat(file_system[0] + "/" + file)
                    if info['st_ifmt'] == 'S_IFLNK':
                        if self.arguments.verbose:
                            utils.multi_print(f"{Fore.GREEN}\tIgnoring symlink: {Fore.RESET}{file}")
                        continue
                    path = file_system[0] + "/"
                    if file_system[0] == "/":
                        path = "/"
                    local_file = utils.check_file_names(tmp_path + path.replace("/", self.imager.separator) + file)
                    open(local_file, 'a').close()
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.GREEN}\tCopying file: {Fore.RESET}{path + file}")
                    try:
                        data = afc.get_file_contents(file_system[0] + "/" + file)
                        fd = open(local_file, 'ab')
                        fd.write(data)
                        fd.close()
                    except AfcException:
                        if self.arguments.verbose:
                            utils.multi_print(f"{Fore.RED}\tPermission denied: {Fore.RESET}{path + file}")
                        continue
                    # Files are also case-insensitive.
                    except FileExistsError:
                        if "_AFFLUX_DUPLICATE_FILENAME_" in local_file:
                            local_file = local_file[:-1] + str(int(local_file[-1]) + 1)
                        else:
                            local_file = local_file + "_AFFLUX_DUPLICATE_FILENAME_1"
                        fd = open(local_file, 'ab')
                        fd.write(data)
                        fd.close()
                        continue

                    # Change file modify time
                    utils.modify_time(info, local_file)

        except ConnectionAbortedError:
            utils.multi_print(f"{Fore.RED}[-] Error: Device closed connection.")
            chdir(old_path)
            rmtree(tmp_path, ignore_errors=True)
            return False

        except OSError as e:
            if "Errno 28" in str(e):
                utils.multi_print(f"{Fore.RED}[-] Error: Out of storage space on machine.")
                rmtree(tmp_path, ignore_errors=True)
                return False
            else:
                utils.multi_print(f"{Fore.RED}[-] Error: {e}")

        directories = listdir()
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Directory list: {Fore.RESET}{', '.join(directories)}")
        utils.multi_print(f"{Fore.GREEN}[+] Adding to container...")
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Container path: {Fore.RESET}{output_path}")
        success = imager.add_path_names(output_path, directories, True, self.arguments.append, encryption_password)
        chdir(old_path)
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Cleaning up...")
        rmtree(tmp_path, ignore_errors=True)
        utils.multi_print(f"{Fore.GREEN}[+] Imaging completed.")
        return success

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}Apple AFC Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        self.parser.add_argument('-i', "--iOS", nargs=1, action="store", metavar='METHOD', choices=['AFC', 'AFC2',
                                                                                                    'afc', 'afc2'],
                                 help='create an image from an iOS device using METHOD. Jailbroken methods: AFC, AFC2. '
                                      'Unjailbroken method: AFC.')
        self.parser.add_argument('-c', "--clear", action="store_true",
                                 help='clear any pairing records made by Afflux.')
        self.parser.add_argument('-k', "--pair", action="store_true",
                                 help='pair or re-pair the device before imaging.')
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded Apple AFC plugin!")
        if self.arguments.temp:
            self.temp = self.arguments.temp
        if self.arguments.output is None:
            utils.multi_print(f"{Fore.RED}\tNo output file specified.")
            return False
        self.imager = imaging.Imager(self.arguments.verbose)
        if self.arguments.iOS is not None:
            # Image an iOS device via AFC or AFC2
            self.arguments.iOS = self.arguments.iOS[0].strip().lower()
            if self.arguments.iOS == "afc2":
                self.service = "com.apple.afc2"
            elif self.arguments.iOS == "afc":
                self.service = "com.apple.afc"
            else:
                utils.multi_print(f"{Fore.RED}[-] Error: Method {self.arguments.iOS} is not supported.")
                return False
            self.image_device_afc(self.arguments.output[0],
                                  self.arguments.container_password,
                                  self.arguments.pair,
                                  self.arguments.clear,
                                  self.arguments.zip)
        else:
            utils.multi_print(f"{Fore.RED}[-] Error: No method specified. Use '-h' to see the plugin options.")
            return False
        return True
