# By Marshall University on 7/12/2021
# Plugin to image a generic device over SSH

import argparse
from os import makedirs, chdir, listdir

from smbclient import scandir, stat, open_file, register_session
from smbprotocol import exceptions
from datetime import datetime
from shutil import rmtree
from colorama import reinit, Fore

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class GenericSMB(plugin_manager.Plugin):
    """
        This class is used to connect to a device via SMB, copy files from the device, then image those files.
    """

    def __init__(self):
        """
            Constructor for GenericSMB class.
        """
        super().__init__()
        self.parser = None
        self.separator = None
        self.name = "generic_smb"
        self.description = "Image a device via network SMB"
        self.imager = None
        self.arguments = None
        self.first_pass = True
        self.tmp_path = None
        self.temp = None
        self.seperator = "/"

    def smb_copy_and_image_r(self, smb, hostname, share, password, symlinks, recursive, preserve_mtime=True):
        """
            Copy over a file from the device via SMB and immediately append it to the image.
        """
        # Get the files on the SMB server
        remote_path = f"\\{hostname}\\{share}"
        for file_info in scandir(remote_path):
            local_path = utils.check_file_names(self.tmp_path + self.seperator + share.replace("\\", self.seperator) +
                                                self.seperator + file_info.name)

            # Directory
            if file_info.is_dir(follow_symlinks=symlinks):
                try:
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.GREEN}\tCreating directory: {Fore.RESET}{share}\\{file_info.name}")
                    makedirs(local_path)
                except OSError:
                    pass
                if recursive:
                    self.smb_copy_and_image_r(smb, hostname, f"{share}\\{file_info.name}", password, symlinks,
                                              preserve_mtime)

            # File
            elif file_info.is_file():
                try:
                    # Use stat so we can get the file modified time
                    file_stat = stat(f"{remote_path}\\{file_info.name}")
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.GREEN}\tCopying file: {Fore.RESET}{share}\\{file_info.name}")
                    with open(local_path, "wb") as file:
                        with open_file(f"{remote_path}\\{file_info.name}", mode="rb") as fd:
                            file_bytes = fd.read()
                            file.write(file_bytes)
                    # Set the modified time.
                    info = {'st_mtime': datetime.fromtimestamp(file_stat.st_mtime)}
                    utils.modify_time(info, local_path)
                except PermissionError:
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.RED}\t[-] Error: Permission denied.")
                except FileNotFoundError as e:
                    print(e)
                    if self.arguments.verbose:
                        utils.multi_print(f"{Fore.RED}\t[-] Error: File not found or not accessible: "
                                          f"{remote_path}\\{file_info.name}")

            else:
                print(local_path)
                print(remote_path)
                print("Permissions thing? Shouldn't be here.")
                exit()

    def image_smb(self, output_file, encryption_password, share, hostname, username, password, symlinks, recursive,
                  zip_image, port=445):
        """
            Connect to the device and initiate the imaging process.
        """

        self.imager = imaging.Imager(self.arguments.verbose, zip=zip_image)

        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Hostname, share: {Fore.RESET}{hostname}, {share}")
            utils.multi_print(f"{Fore.GREEN}[*] Username, Password: {Fore.RESET}{username}, {password}")

        try:
            # Initialize the SMB connection.
            smb = register_session(hostname, username=username, password=password, connection_timeout=10, port=port)
        except exceptions.LogonFailure:
            utils.multi_print(f"{Fore.RED}[-] Error: Incorrect password.")
            return False
        except exceptions.SMBException:
            utils.multi_print(f"{Fore.RED}[-] Error: Incorrect username.")
            return False
        except ValueError:
            utils.multi_print(f"{Fore.RED}[-] Error: Could not connect to host.")
            return False
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[+] Connected to SMB service.")

        output_path, old_path, self.tmp_path = self.imager.setup_tmp_directory(self.temp, output_file)
        chdir(self.tmp_path)

        makedirs(self.tmp_path + self.seperator + share)

        utils.multi_print(f"{Fore.GREEN}[*] Copying files...")
        self.smb_copy_and_image_r(smb, hostname, share, encryption_password, symlinks, recursive,
                                  preserve_mtime=True)
        if self.arguments.verbose:
            utils.multi_print(f"{Fore.GREEN}[*] Closing SMB connection.")
        smb.disconnect()
        directories = listdir()
        self.imager.add_path_names(output_path, directories, True, False, encryption_password)
        chdir(old_path)
        rmtree(self.tmp_path, ignore_errors=True)
        return True

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}Generic SSH Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        self.parser.add_argument('-a', "--address", nargs=1, action="store", metavar='HOSTNAME',
                                 help='IP address  or server name to connect to.')
        self.parser.add_argument('-S', "--share", nargs=1, action="store", metavar='SHARE',
                                 help='SMB share for imaging.')
        self.parser.add_argument('-u', "--username", nargs=1, action="store", default=[None],
                                 help='SMB username to connect with.')
        self.parser.add_argument('-P', "--password", nargs=1, action="store", default=[None],
                                 help='password for the SMB user.')
        self.parser.add_argument("--port", nargs=1, action="store", metavar='PORT',
                                 help='port to connect over SMB.')
        self.parser.add_argument('-s', "--symlinks", action="store_true", default=False,
                                 help='Enable traversing symlinks.')
        self.parser.add_argument('-r', "--recursive", action="store_true", default=False,
                                 help='add files and folders recursively.')
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded SMB plugin!")
        if self.arguments.temp:
            self.temp = self.arguments.temp
        if self.arguments.address:
            if self.arguments.share:
                self.image_smb(self.arguments.output[0],
                               self.arguments.container_password,
                               self.arguments.share[0],
                               self.arguments.address[0],
                               self.arguments.username[0],
                               self.arguments.password[0],
                               self.arguments.symlinks,
                               self.arguments.recursive,
                               self.arguments.zip)
                return True
        else:
            self.parser.print_help()
            return False
