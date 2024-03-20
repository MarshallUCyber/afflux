# By Marshall University on 7/12/2021
# Image a jailbroken device over SSH

import argparse
import subprocess
from os import makedirs, chdir, listdir
from stat import S_ISDIR, S_ISREG, S_ISLNK, S_ISSOCK

import pysftp
from shutil import rmtree
from colorama import reinit, Fore

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class IosImagerSSH(plugin_manager.Plugin):
    """
        This class is used to connect to a device via SSH, copy files from the device, then image those files.
    """

    def __init__(self):
        """
            Constructor for IosImagerSSH class.
        """
        super().__init__()
        self.parser = None
        self.separator = None
        self.name = "ios_ssh"
        self.description = "Image a jailbroken device via SSH over network or USB."
        self.imager = None
        self.arguments = None
        self.first_pass = True
        self.tmp_path = None
        self.temp = None
        self.seperator = "/"

    def sftp_copy_and_image_r(self, sftp, remote_dir, password, symlinks, preserve_mtime=True):
        """
            Copy over a file from the device via SFTP and immediately append it to the image.
        """
        try:
            for entry in sftp.listdir_attr(remote_dir):
                remote_path = remote_dir + self.seperator + entry.filename
                if remote_dir == "/":
                    remote_dir = ""
                local_path = utils.check_file_names(self.tmp_path + remote_dir + self.seperator + entry.filename)
                mode = entry.st_mode
                # Directory
                if S_ISDIR(mode):
                    try:
                        if self.arguments.verbose:
                            utils.multi_print(f"{Fore.GREEN}\tCreating directory: {Fore.RESET}{remote_path}")
                        makedirs(local_path)
                    except OSError:
                        pass
                    self.sftp_copy_and_image_r(sftp, remote_path, password, preserve_mtime)
                # Symlinks
                elif S_ISLNK(mode):
                    if symlinks:
                        self.sftp_copy_and_image_r(sftp, remote_path, password, preserve_mtime)
                # File
                elif S_ISREG(mode):
                    try:
                        if self.arguments.verbose:
                            utils.multi_print(f"{Fore.GREEN}\tCopying file: {Fore.RESET}{remote_path}")
                        sftp.get(remote_path, local_path, preserve_mtime=preserve_mtime)
                    except PermissionError:
                        utils.multi_print(f"{Fore.RED}\t[-] Permission denied.")
                elif S_ISSOCK(mode):
                    utils.multi_print(f"{Fore.RED}\t[-] Socket, skipping.")
                    continue
                else:
                    utils.multi_print(f"{Fore.RED}[-] Something went wrong: {remote_dir}, {local_path}, {mode}")
                    continue

        except FileNotFoundError:
            utils.multi_print(f"\t{Fore.RED}[-] File not found: {remote_dir}")
            pass

    def image_device_ssh(self, output_file, encryption_password, local, remote_dir, password="alpine",
                         ip_address="127.0.0.1", symlinks=False):
        """
            Connect to the device and initiate the imaging process.
        """
        sftp = None
        self.imager = imaging.Imager(self.arguments.verbose, zip=self.arguments.zip)
        port = 22
        if local is True:
            if self.imager.os == "Windows":
                # Use iproxy to initialize SSH tunneling over USB. (Note, forwards port 22 -> 2222)
                # port = 2222
                # utils.multiPrint(f"{Fore.GREEN}[*] Make sure Jailbroken device is connected via USB.")
                # subprocess.call(["itunnel_mux --iport 22 --lport 2222"], shell=True, stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL)
                utils.multi_print(Fore.GREEN + "[*] Download this script: "
                                               "https://github.com/TestStudio/usbmuxd/blob/master/python-client/"
                                               "tcprelay.py\n" + "[*] Then run \"tcprelay.py -t 22:2222\"")
            else:
                port = 2222
                utils.multi_print(f"{Fore.GREEN}[*] Make sure Jailbroken device is connected via USB.")
                subprocess.call(["iproxy 2222 22 &"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        try:
            sftp = pysftp.Connection(ip_address, username='root', password=password, cnopts=cnopts, port=port)
        except Exception as e:
            if "Unable to connect" in str(e):
                utils.multi_print(f"{Fore.RED}[-] Could not connect to device.")
                return False
            if "Authentication" in str(e):
                utils.multi_print(f"{Fore.RED}[-] Wrong SSH password.")
                return False

        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Connected to device.")

        output_path, old_path, self.tmp_path = self.imager.setup_tmp_directory(self.temp, output_file)
        chdir(self.tmp_path)

        # If no `-d` switch is used, start at `/`
        if not remote_dir or remote_dir[0] == "/":
            target_dir = "/"
        else:
            target_dir = remote_dir[0]

            # If the `-d` option is used, go ahead and make the specified path
            makedirs(self.tmp_path + target_dir)

        utils.multi_print(f"{Fore.GREEN}[*] Copying files...")
        try:
            self.sftp_copy_and_image_r(sftp, target_dir, encryption_password, symlinks, preserve_mtime=True)
        except Exception as e:
            if "Server connection dropped" in str(e):
                utils.multi_print(f"\n\t{Fore.RED}[-] Connection lost.")
                return False
        directories = listdir()
        self.imager.add_path_names(output_path, directories, True, self.arguments.append, encryption_password)
        chdir(old_path)
        rmtree(self.tmp_path, ignore_errors=True)
        return True

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}iOS SSH Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        self.parser.add_argument('-a', "--address", nargs=1, action="store", metavar='IP',
                                 help='IP address to connect to.')
        self.parser.add_argument('-d', "--directory", nargs=1, action="store", metavar='REMOTE DIR',
                                 help='Remote directory to begin imaging.')
        self.parser.add_argument('-l', "--local", action="store_true",
                                 help='SSH to iOS device via network address instead of USB tunneling.')
        self.parser.add_argument('-R', "--root-password", nargs=1, action="store", metavar='PASSWORD',
                                 help='root password for jailbroken device if using SSH. \nDefaults to \'alpine\'.')
        self.parser.add_argument('-s', "--symlinks", action="store_true",
                                 help='follow and image any symlinks.')
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded iOS SSH plugin!")
        if self.arguments.temp:
            self.temp = self.arguments.temp
        self.imager = imaging.Imager(self.arguments.verbose)
        if self.arguments.address or self.arguments.local:
            if self.arguments.local is True:
                if self.arguments.root_password is None:
                    self.image_device_ssh(self.arguments.output[0],
                                          self.arguments.container_password,
                                          self.arguments.local,
                                          self.arguments.directory)
                else:
                    self.image_device_ssh(self.arguments.output[0],
                                          self.arguments.container_password,
                                          self.arguments.local,
                                          self.arguments.directory,
                                          password=self.arguments.root_password[0])
            else:
                if self.arguments.root_password is None:
                    self.image_device_ssh(self.arguments.output[0],
                                          self.arguments.container_password,
                                          self.arguments.local,
                                          self.arguments.directory,
                                          ip_address=self.arguments.address[0])
                else:
                    self.image_device_ssh(self.arguments.output[0],
                                          self.arguments.container_password,
                                          self.arguments.local,
                                          self.arguments.directory,
                                          password=self.arguments.root_password[0],
                                          ip_address=self.arguments.address[0])
            return True
        else:
            self.parser.print_help()
            return False
