# By Marshall University on 7/12/2021
# Image an Android via ADB

# pip install adb-shell, pip install adb-shell[usb]

import argparse
from datetime import datetime
from os import getlogin, path, mkdir, makedirs, chdir, listdir
from shutil import rmtree
from socket import timeout
from stat import *

from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.exceptions import UsbReadFailedError, AdbCommandFailureException, TcpTimeoutException, \
    UsbDeviceNotFoundError, AdbTimeoutError, AdbConnectionError
from adb_shell.transport.usb_transport import UsbTransport
from colorama import reinit, Fore

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class AndroidImage(plugin_manager.Plugin):
    """
        This class is used to connect to an Android device via ADB.
    """

    def __init__(self):
        """
            Constructor for the AndroidImage class.
        """
        super().__init__()
        self.arguments = None
        self.parser = None
        self.imager = None
        self.name = "android_adb"
        self.description = "Image an Android device via ADB over USB or over network. Supports root filesystems."
        self.device = None
        self.signer = None
        self.temp = None
        self.no_image = []

    def sign(self, keys):
        """
            Get and sign keys, so we can connect to the device.
        """

        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Attempting to sign....")
        try:
            with open(keys) as f:
                priv = f.read()
            with open(keys + '.pub') as f:
                pub = f.read()
        except FileNotFoundError:
            # Windows
            if self.imager.os == "Windows":
                keys = "C:\\Users\\" + getlogin() + "\\.android\\adbkey"
                if path.exists(keys):
                    with open(keys) as f:
                        priv = f.read()
                    with open(keys + '.pub') as f:
                        pub = f.read()
                else:
                    return False
            # Linux
            else:
                keys = path.expanduser("~") + "/.android/adbkey"
                if path.exists(keys):
                    with open(keys) as f:
                        priv = f.read()
                    with open(keys + '.pub') as f:
                        pub = f.read()
                else:
                    return False
        self.signer = PythonRSASigner(pub, priv)
        return True

    def key_gen(self, file):
        """
            Generate device keys if specified by the user.
        """

        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Generating keyfile to device.")
        keygen(file)

    def connect(self, ip_address=None, serial=None, port=5555, auth_timeout=0.1, transport_timeout=5):
        """
            Connect to the device via ADB over USB or with IP address.
        """

        try:
            # Connect via IP address
            if ip_address:
                self.device = AdbDeviceTcp(ip_address, port, default_transport_timeout_s=transport_timeout)
                self.device.connect(rsa_keys=[self.signer], auth_timeout_s=auth_timeout)
            # Connect via USB
            else:
                self.device = AdbDeviceUsb(serial=serial)
                self.device.connect(rsa_keys=[self.signer], auth_timeout_s=auth_timeout)
        except UsbReadFailedError:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to device. Did you accept the computers key on "
                              f"the device?")
            return False
        except TcpTimeoutException:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to remote device.")
            return False
        except OSError:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to remote device.")
            return False
        except ConnectionRefusedError:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to device. Are the IP amd port correct?")
            return False
        except UsbDeviceNotFoundError:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to device. Is it plugged in?")
            return False
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Connected to device.")
        return True

    def close(self):
        """
            Close connection to the device.
        """

        self.device.close()

    def root(self):
        """
            Attempt to get root privileges.
        """

        try:
            if self.arguments.verbose:
                utils.multi_print(f"{Fore.GREEN}[+] Checking root.")
            self.device.root()
        except AdbTimeoutError:
            if self.arguments.verbose:
                utils.multi_print(f"{Fore.GREEN}[+] Got timeout, trying again...")
            self.device.root()

    def execute_command(self, command):
        """
            Execute a shell command on the device.
        """
        try:
            if self.arguments.verbose:
                utils.multi_print(f"{Fore.GREEN}[*] Executing command: {Fore.RESET}{command}")
            return self.device.shell(command)
        except AdbConnectionError:
            return None

    def list_devices(self):
        """
            Get a list of devices by serial number.
        """

        devices = []
        for device in UsbTransport.find_all_adb_devices():
            devices.append(device.serial_number)
        return devices

    def walk(self, directory, symlink_follow, no_image):
        """
            Traverse the Android file structure.
        """

        dirs = []
        files = []
        try:
            directories = self.device.list(directory)
            for path_name in directories:
                name = bytes(path_name.filename).decode("utf-8")
                if name in ('.', '..', ''):
                    continue
                # Directory
                if S_ISDIR(path_name.mode):
                    dirs.append(name)
                # Symlink
                elif S_ISLNK(path_name.mode):
                    if symlink_follow:
                        dirs.append(name)
                    else:
                        utils.multi_print(f"{Fore.RED}\tSkipping Symlink: {Fore.RESET}{name}")
                # File
                else:
                    files.append(name)

        except TcpTimeoutException as e:
            utils.multi_print(f"{Fore.RED}\tTimeout: {Fore.RESET}{str(e)}")

        except Exception as e:
            print(e)

        yield directory, dirs, files

        if dirs:
            for d in dirs:
                if directory == "/":
                    directory = ""
                result = directory + "/" + d
                if no_image:

                    # Check if the path is in a directory we shouldn't traverse
                    dont_image = False
                    for no_image_path in no_image:
                        if result in no_image_path:
                            dont_image = True

                    # Safe to traverse path
                    if dont_image is False:
                        for walk_result in self.walk(result, symlink_follow, no_image):
                            yield walk_result

                    # Don't traverse path
                    else:
                        if self.arguments.verbose:
                            utils.multi_print(Fore.RED + "\t[*] Skipping path: %s" % result)

                # No excluded directories specified, so traverse away.
                else:
                    for walk_result in self.walk(result, symlink_follow, no_image):
                        yield walk_result

    def image_device(self, specified_directories, output_file, encryption_password, symlink_follow, root, zip_image):
        """
            Image an Android device.
        """
        no_image = []
        imager = imaging.Imager(self.arguments.verbose, zip=zip_image)
        output_path, old_path, tmp_path = self.imager.setup_tmp_directory(self.temp, output_file)

        if specified_directories[0] == '':
            specified_directories = ["/"]

        for pathname in specified_directories:
            if pathname[-1] == "-":
                no_image.append(pathname[:-1])

        for not_image_path in no_image:
            specified_directories.remove(not_image_path + "-")

        if output_file[1:2] != ":":
            if output_file[:1] != "/":
                output_file = old_path + self.imager.separator + output_file

        try:
            # Check if we want to attempt root access
            if root:
                self.root()

            # Check if the specified directory exists
            for directory in specified_directories:
                if self.device.stat(directory) == (0, 0, 0):
                    utils.multi_print(f"{Fore.RED}\tSpecified directory not found: {Fore.RESET}{directory}")
                    return False

        except AdbTimeoutError:
            if self.arguments.verbose:
                utils.multi_print(f"{Fore.GREEN}[+] Got timeout checking for root privs. Continuing...")

        except TcpTimeoutException:
            utils.multi_print(f"{Fore.RED}\tDevice connection timeout.")
            return False

        for directory in specified_directories:
            if directory != "/":
                makedirs(tmp_path + directory)

            for path_name in self.walk(directory, symlink_follow, no_image):
                try:
                    for directories in path_name[1]:
                        local_dir = utils.check_file_names(tmp_path + path_name[0] + self.imager.separator + directories)
                        if self.arguments.verbose:
                            if path_name[0] == "/":  # TODO: Find a better solution for the path printing issue
                                utils.multi_print(f"{Fore.GREEN}\tMaking dir: {Fore.RESET}{path_name[0] + directories}")
                            else:
                                utils.multi_print(f"{Fore.GREEN}\tMaking dir: "
                                                  f"{Fore.RESET}{str(path_name[0]) + '/' + directories}")
                        mkdir(local_dir)

                    for file_name in path_name[2]:
                        output_file_path = utils.check_file_names(tmp_path + path_name[0] + self.imager.separator +
                                                                  file_name)
                        stat = self.device.stat((str(path_name[0]) + "/" + file_name))
                        if self.arguments.verbose:
                            if path_name[0] == "/":
                                utils.multi_print(f"{Fore.GREEN}\tCopying file: {Fore.RESET}{path_name[0] + file_name}")
                            else:
                                utils.multi_print(f"{Fore.GREEN}\tCopying file: "
                                                  f"{Fore.RESET}{str(path_name[0]) + '/' + file_name}")
                        self.device.pull((str(path_name[0]) + "/" + file_name), output_file_path)
                        # Change 'st_mtime' to the original time from the device
                        info = {'st_mtime': datetime.fromtimestamp(stat[2])}
                        utils.modify_time(info, output_file_path)

                except AdbCommandFailureException:
                    utils.multi_print(f"{Fore.RED}\tPermission error: "
                                      f"{Fore.RESET}{str(path_name[0]) + '/' + file_name}")
                    continue

                except TcpTimeoutException:
                    utils.multi_print(f"{Fore.RED}\tTimeout: {Fore.RESET}{str(path_name[0]) + '/' + file_name}")
                    continue

                except ConnectionResetError:
                    utils.multi_print(f"{Fore.RED}[-] Error: {Fore.RESET}Connection Reset.")
                    continue

        self.close()
        chdir(tmp_path)
        directories = listdir()
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Directory list: {Fore.RESET}{', '.join(directories)}")
        utils.multi_print(f"{Fore.GREEN}[+] Adding to container...")
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Container path: {Fore.RESET}{output_file}")
        success = imager.add_path_names(output_file, directories, True, self.arguments.append, encryption_password)
        chdir(old_path)
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Cleaning up...")
        rmtree(tmp_path, ignore_errors=True)
        utils.multi_print(f"{Fore.GREEN}[+] Imaging completed.")
        return success

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}Android ADB Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        self.parser.add_argument('-a', "--android", action="store", metavar='USB/IP:PORT',
                                 help='create an image from a connected Android device using ADB. Method can be USB or '
                                      'via IP.')
        self.parser.add_argument('-d', "--directory", action="store", nargs="*",
                                 help='Directory to image on the device.')
        self.parser.add_argument('-s', "--symlinks", action="store_true",
                                 help='follow and image any symlinks.')
        self.parser.add_argument("--root", action="store_true",
                                 help='check and acquire root privileges if possible.')
        self.parser.add_argument('-k', "--keygen", action="store_true",
                                 help='regenerate pairing keys for the device.')
        self.parser.add_argument("--timeout", action="store", nargs=1, default=5, type=int, metavar='TIMEOUT',
                                 help='ADB timeout.')
        self.parser.add_argument("--auth-timeout", action="store", nargs=1, default=0.1, type=int,
                                 metavar='AUTH TIMEOUT', help='Timeout for \'CNXN\' authentication response.')
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded Android plugin!")
        if self.arguments.temp:
            self.temp = self.arguments.temp
        self.imager = imaging.Imager(self.arguments.verbose)
        if not self.arguments.directory:
            self.arguments.directory = ["/"]
        if self.arguments.output is None:
            utils.multi_print(f"{Fore.RED}\tNo output file specified.")
            return False
        if self.arguments.android:
            # If the user specifies, generate keys
            if self.arguments.keygen:
                self.key_gen("adb")
            # If we can't find keys, generate them
            if not self.sign("adb"):
                self.key_gen("adb")
                self.sign("adb")
            if self.arguments.android.lower() == "usb":
                result = self.connect(transport_timeout=self.arguments.timeout,
                                      auth_timeout=self.arguments.auth_timeout)
                if result:
                    self.image_device(self.arguments.directory,
                                      self.arguments.output[0],
                                      self.arguments.container_password,
                                      self.arguments.symlinks,
                                      self.arguments.root,
                                      self.arguments.zip)
            else:
                if ":" in self.arguments.android:
                    ip_address, port = self.arguments.android.split(":")
                    print(f"{Fore.GREEN}[*] Device IP: {Fore.RESET}{ip_address} {Fore.GREEN}Port: "
                          f"{Fore.RESET}{str(port)}")
                    result = self.connect(ip_address=ip_address, port=port,
                                          transport_timeout=self.arguments.timeout,
                                          auth_timeout=self.arguments.auth_timeout)
                else:
                    print(f"{Fore.GREEN}[*] Device IP: {Fore.RESET}{self.arguments.android}")
                    result = self.connect(ip_address=self.arguments.android, port=5555,
                                          transport_timeout=self.arguments.timeout,
                                          auth_timeout=self.arguments.auth_timeout)
                if result:
                    self.image_device(self.arguments.directory,
                                      self.arguments.output[0],
                                      self.arguments.container_password,
                                      self.arguments.symlinks,
                                      self.arguments.root,
                                      self.arguments.zip)
            return True

        else:
            self.parser.print_help()
            return False
