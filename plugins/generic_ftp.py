# By Marshall University on 7/12/2021
# Plugin to image a generic device over SSH

import argparse
from os import makedirs, chdir, listdir

import ftplib
from dateutil import parser, relativedelta
import datetime
from shutil import rmtree
from colorama import reinit, Fore

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class GenericFTP(plugin_manager.Plugin):
    """
        This class is used to connect to a device via FTP, copy files from the device, then image those files.
    """

    def __init__(self):
        """
            Constructor for GenericFTP class.
        """
        super().__init__()
        self.parser = None
        self.separator = None
        self.name = "generic_ftp"
        self.description = "Image a device via network FTP"
        self.imager = None
        self.arguments = None
        self.first_pass = True
        self.tmp_path = None
        self.temp = None
        self.seperator = "/"

    def ftp_copy_and_image_r(self, ftp_server, remote_dir, password, symlinks, no_image, recursive,
                             preserve_mtime=True):
        """
            Copy over a file from the device via FTP and immediately append it to the image.
        """
        output = []
        # Get the files on the FTP server
        ftp_server.dir(remote_dir, output.append)
        for line in output:
            line = line.split(None, 8)

            # Fix for year not appearing for timestamps under 6 months old. If there isn't a year, calculate it and
            # add it to the timestamp.
            if ":" in line[7]:
                test = datetime.datetime.now() - relativedelta.relativedelta(months=6)
                line[6] = line[6] + " " + str(test.year)

            time_str = line[5] + " " + line[6] + " " + line[7]
            time = parser.parse(time_str)

            filename = line[-1]
            if remote_dir != "":
                remote_path = remote_dir + self.seperator + filename
            else:
                remote_path = remote_dir + filename
            if remote_dir == "/":
                remote_dir = ""
            local_path = utils.check_file_names(self.tmp_path + self.seperator + remote_dir + self.seperator + filename)
            skip = False

            # Directory
            if line[0][:1] == "d":
                if no_image:
                    for dir in no_image:
                        if dir == remote_path:
                            utils.multi_print(f"{Fore.RED}\tSkipping directory: {Fore.RESET}{remote_path}")
                            skip = True
                if skip:
                    continue
                try:
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.GREEN}\tCreating directory: {Fore.RESET}{remote_path}")
                    makedirs(local_path)
                except OSError:
                    pass
                if recursive:
                    self.ftp_copy_and_image_r(ftp_server, remote_path, password, symlinks, no_image, preserve_mtime)

            # File
            elif line[0][:1] == "-":
                if no_image:
                    for dir in no_image:
                        if dir == remote_path:
                            utils.multi_print(f"{Fore.RED}\tSkipping file: {Fore.RESET}{remote_path}")
                            skip = True
                if skip:
                    continue
                try:
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.GREEN}\tCopying file: {Fore.RESET}{remote_path}")
                    with open(local_path, "wb") as file:
                        ftp_server.retrbinary(f"RETR {remote_path}", file.write)
                    utils.modify_time(time, local_path, st_mtime=False)
                except PermissionError:
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.RED}\t[-] Error: Permission denied.")
                except FileNotFoundError:
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.RED}\t[-] Error: File not found or not accessible: {remote_dir}")

            # Symlinks? Yes
            elif line[0][:1] == "l":
                symlink_target = line[-1]
                if symlinks:
                    self.ftp_copy_and_image_r(ftp_server, symlink_target, password, symlinks, no_image, preserve_mtime)
                else:
                    utils.multi_print(f"{Fore.GREEN}\tSkipping symlink to: {Fore.RESET}{symlink_target}")
            else:
                print(line)
                print("Permissions thing? Shouldn't be here.")
                exit()

    def image_ftp(self, output_file, encryption_password, remote_dir, hostname, username, password, symlinks, timeout,
                  recursive, zip_image, port=21):
        """
            Connect to the device and initiate the imaging process.
        """

        no_image = []
        self.imager = imaging.Imager(self.arguments.verbose, zip=zip_image)

        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Address, Port: {Fore.RESET}{hostname}, {port}")
            utils.multi_print(f"{Fore.GREEN}[*] Username, Password: {Fore.RESET}{username}, {password}")

        try:
            utils.multi_print(f"{Fore.GREEN}[*] Attempting to connect...")
            ftp_server = ftplib.FTP()
            ftp_server.connect(hostname, port=port, timeout=timeout)
            ftp_server.login(username, password)
        except ConnectionRefusedError:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to service.")
            return False
        except ftplib.error_perm:
            utils.multi_print(f"{Fore.RED}[-] Error: Incorrect login information.")
            return False
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Connected to FTP service.")

        output_path, old_path, self.tmp_path = self.imager.setup_tmp_directory(self.temp, output_file)
        chdir(self.tmp_path)

        # If no `-d` switch is used, start at `/`
        if not remote_dir:
            target_dir = "/"
        else:
            if remote_dir[0] == "/":
                target_dir = "/"
            else:
                target_dir = remote_dir[0]

        if remote_dir:
            for pathname in remote_dir:
                if pathname[-1] == "-":
                    no_image.append(pathname[:-1])

            for not_image_path in no_image:
                remote_dir.remove(not_image_path + "-")

        utils.multi_print(f"{Fore.GREEN}[*] Copying files...")
        self.ftp_copy_and_image_r(ftp_server, target_dir, encryption_password, symlinks, no_image,
                                  recursive, preserve_mtime=True)
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Closing FTP connection.")
        ftp_server.quit()
        directories = listdir()
        self.imager.add_path_names(output_path, directories, True, self.arguments.append, encryption_password)
        chdir(old_path)
        rmtree(self.tmp_path, ignore_errors=True)
        return True

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}Generic SSH Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        self.parser.add_argument('-a', "--address", nargs=1, action="store", metavar='IP',
                                 help='IP address  or server name to connect to.')
        self.parser.add_argument('-u', "--username", nargs=1, action="store",
                                 help='FTP username to connect with.')
        self.parser.add_argument('-P', "--password", nargs=1, action="store",
                                 help='password for the FTP user.')
        self.parser.add_argument("--port", nargs=1, action="store",
                                 help='port to connect over FTP.')
        self.parser.add_argument('-s', "--symlinks", action="store_true",
                                 help='follow and image any symlinks.')
        self.parser.add_argument('-r', "--recursive", action="store_true", default=False,
                                 help='add files and folders recursively.')
        self.parser.add_argument('-d', "--directory", nargs='*', action="store", metavar='REMOTE DIR',
                                 help='Remote directory to begin imaging.')
        self.parser.add_argument("--timeout", action="store", nargs=1, default=[5], type=int, metavar='TIMEOUT',
                                 help='FTP connection timeout.')
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded FTP plugin!")
        if self.arguments.temp:
            self.temp = self.arguments.temp
        if self.arguments.address:
            if self.arguments.port is not None:
                self.image_ftp(self.arguments.output[0],
                               self.arguments.container_password,
                               self.arguments.directory,
                               self.arguments.address[0],
                               self.arguments.username[0],
                               self.arguments.password[0],
                               self.arguments.symlinks,
                               self.arguments.timeout,
                               self.arguments.recursive,
                               port=int(self.arguments.port[0]))
            else:
                self.image_ftp(self.arguments.output[0],
                               self.arguments.container_password,
                               self.arguments.directory,
                               self.arguments.address[0],
                               self.arguments.username[0],
                               self.arguments.password[0],
                               self.arguments.timeout,
                               self.arguments.recursive,
                               self.arguments.symlinks)
            return True
        else:
            self.parser.print_help()
            return False
