# By Marshall University on 7/12/2021
# Plugin to image a generic device over SSH

import argparse
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

# TODO: Specify directories to avoid.


class GenericSSH(plugin_manager.Plugin):
    """
        This class is used to connect to a device via SSH, copy files from the device, then image those files.
    """

    def __init__(self):
        """
            Constructor for GenericSSH class.
        """
        super().__init__()
        self.parser = None
        self.separator = None
        self.name = "generic_ssh"
        self.description = "Image a device via network SSH"
        self.imager = None
        self.arguments = None
        self.first_pass = True
        self.tmp_path = None
        self.temp = None
        self.seperator = "/"

    def sftp_copy_and_image_r(self, sftp, remote_dir, password, symlinks, no_image, recursive, preserve_mtime=True):
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
                skip = False
                # Directory
                if S_ISDIR(mode):
                    try:
                        if no_image:
                            for dir in no_image:
                                if dir == remote_path:
                                    utils.multi_print(f"{Fore.RED}\tSkipping directory: {Fore.RESET}{remote_path}")
                                    skip = True
                        if skip:
                            continue
                        if self.arguments.verbose:
                            utils.multi_print(f"{Fore.GREEN}\tCreating directory: {Fore.RESET}{remote_path}")
                        makedirs(local_path)
                    except OSError:
                        pass
                    if recursive:
                        self.sftp_copy_and_image_r(sftp, remote_path, password, symlinks, no_image, recursive,
                                                   preserve_mtime)
                # Symlinks
                elif S_ISLNK(mode):
                    if symlinks:
                        if recursive:
                            self.sftp_copy_and_image_r(sftp, remote_path, password, symlinks, no_image, recursive,
                                                       preserve_mtime)
                # File
                elif S_ISREG(mode):
                    try:
                        if no_image:
                            for dir in no_image:
                                if dir == remote_path:
                                    utils.multi_print(f"{Fore.RED}\tSkipping file: {Fore.RESET}{remote_path}")
                                    skip = True
                        if skip:
                            continue
                        if self.arguments.verbose:
                            utils.multi_print(f"{Fore.GREEN}\tCopying file: {Fore.RESET}{remote_path}")
                        sftp.get(remote_path, local_path, preserve_mtime=preserve_mtime)
                    except PermissionError:
                        if self.arguments.verbose:
                            utils.multi_print(f"{Fore.RED}\t[-] Permission denied.")
                elif S_ISSOCK(mode):
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.RED}\t[-] Error: Socket, skipping.")
                    continue
                else:
                    utils.multi_print(f"{Fore.RED}[-] Something went wrong: {remote_dir}, {local_path}, {mode}")
                    continue

        except FileNotFoundError:
            utils.multi_print(f"{Fore.RED}[-] Error: File not found: {remote_dir}")
            return False

        except Exception as e:
            if "EOF during negotiation" in str(e):
                utils.multi_print(f"{Fore.RED}[-] Error: Could not connect. Server may not support SFTP.")
                return False
            else:
                print(e)
                pass

        return True

    def image_ssh(self, output_file, encryption_password, remote_dir, ip_address, username, password, symlinks,
                  recursive, zip_image, port=22):
        """
            Connect to the device and initiate the imaging process.
        """

        sftp = None
        no_image = []
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        self.imager = imaging.Imager(self.arguments.verbose, zip=zip_image)

        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Address, Port: {Fore.RESET}{ip_address}, {port}")
            utils.multi_print(f"{Fore.GREEN}[*] Username, Password: {Fore.RESET}{username}, {password}")

        try:
            sftp = pysftp.Connection(ip_address, username=username, password=password, cnopts=cnopts, port=port)
        except Exception as e:
            if "Unable to connect" in str(e):
                utils.multi_print(f"{Fore.RED}[-] Error: Could not connect via SSH.")
                return False
            elif "Authentication" in str(e):
                utils.multi_print(f"{Fore.RED}[-] Error: Invalid SSH password.")
                return False
            else:
                utils.multi_print(f"{Fore.RED}[-] Error: {e}")
                return False
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Connected to device.")

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

                # If the `-d` option is used, go ahead and make the specified path
                makedirs(self.tmp_path + target_dir)

        if remote_dir:
            for pathname in remote_dir:
                if pathname[-1] == "-":
                    no_image.append(pathname[:-1])

            for not_image_path in no_image:
                remote_dir.remove(not_image_path + "-")

        utils.multi_print(f"{Fore.GREEN}[*] Copying files...")
        result = self.sftp_copy_and_image_r(sftp, target_dir, encryption_password, symlinks, no_image,
                                            recursive, preserve_mtime=True)
        if not result:
            return False
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
                                 help='IP address to connect to.')
        self.parser.add_argument('-u', "--username", nargs=1, action="store",
                                 help='SSH username to connect with.')
        self.parser.add_argument('-P', "--password", nargs=1, action="store",
                                 help='password for the SSH user.')
        self.parser.add_argument("--port", nargs=1, action="store",
                                 help='port to connect over SSH.')
        self.parser.add_argument('-s', "--symlinks", action="store_true",
                                 help='follow and image any symlinks.')
        self.parser.add_argument('-r', "--recursive", action="store_true", default=False,
                                 help='add files and folders recursively.')
        self.parser.add_argument('-d', "--directory", nargs=1, action="store", metavar='REMOTE DIR',
                                 help='Remote directory to begin imaging.')
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded SSH plugin!")
        if self.arguments.temp:
            self.temp = self.arguments.temp
        if self.arguments.address:
            if self.arguments.port is not None:
                self.image_ssh(self.arguments.output[0],
                               self.arguments.container_password,
                               self.arguments.directory,
                               self.arguments.address[0],
                               self.arguments.username[0],
                               self.arguments.password[0],
                               self.arguments.symlinks,
                               self.arguments.recursive,
                               self.arguments.zip,
                               port=int(self.arguments.port[0]),)
            else:
                self.image_ssh(self.arguments.output[0],
                               self.arguments.container_password,
                               self.arguments.directory,
                               self.arguments.address[0],
                               self.arguments.username[0],
                               self.arguments.password[0],
                               self.arguments.symlinks,
                               self.arguments.recursive,
                               self.arguments.zip,)
            return True
        else:
            self.parser.print_help()
            return False
