# By Marshall University on 7/13/2021

import os
from stat import *
import uuid

from colorama import reinit, Fore
from sys import exit

from pyaff4 import aff4_map
from pyaff4 import container
from pyaff4 import data_store, linear_hasher
from pyaff4 import lexicon, logical, escaping
from pyaff4 import rdfvalue, hashes, utils
import shutil
import sys
import errno
import platform
import utilities
import zipfile

reinit()  # Colorama
printUtils = utilities.Utilities.get_instance()

def next_or_none(iterable):
    try:
        return next(iterable)
    except:
        return None


def print_volume_info(file, volume):
    """
        Print AFF4 volume information.
    """

    volume_urn = volume.urn
    printUtils.multi_print("AFF4Container: file://%s <%s>" % (file, str(volume_urn)))


def print_turtle(resolver, volume):
    """
        Print the data stored in information.turtle.

        Parameters:
            resolver:
            volume:
    """

    metadata_urn = volume.urn.Append("information.turtle")
    try:
        with resolver.AFF4FactoryOpen(metadata_urn) as fd:
            txt = fd.ReadAll()
            for line in txt.split(b'\n'):
                if b'aff4://' in line:
                    printUtils.multi_print(Fore.GREEN + utils.SmartUnicode(line))
                else:
                    printUtils.multi_print(utils.SmartUnicode(line))
    except:
        pass


class Imager:
    """
        This class is used to image files and folders using the AFF4 image format. This code is largely from
        https://github.com/aff4/pyaff4 with more error handling and cross-platform support.
    """

    def __init__(self, verbose, zip=False):
        """
            Constructor for Imager class.

            Parameters:
                    verbose: Include verbose messages in output.
        """

        self.verbose = verbose
        self.os = ""
        self.container_path = ""
        self.separator = ""
        self.check_os()
        self.zip = zip

    def check_os(self):
        """
            Check and set the OS.
        """

        self.os = platform.system()
        if self.os == "Windows":
            self.separator = "\\"
        else:
            self.separator = "/"
        return True

    def cleanup(self, specified_path=None):
        """
            Cleanup any temporary directories.

            Parameters:
                specified_path: Custom temporary folder if specified.
        """

        try:
            username = os.getlogin()
        except OSError:
            username = ""
        if not specified_path:
            paths = ["/tmp/afflux_files_download",
                     "C:\\Users\\" + username + "\\AppData\\Local\\Temp\\afflux_files_download"]
        else:
            paths = [specified_path[0]]
        for directory in paths:
            try:
                shutil.rmtree(directory)
                if self.verbose:
                    print(f"{Fore.GREEN}[+] Cleaned up: {Fore.RESET}{directory}")
            except FileNotFoundError:
                continue
            except PermissionError:
                printUtils.multi_print(f"{Fore.RED}[-] Could not access temporary folder. Check permissions.\n")
                return False
        return True

    def setup_tmp_directory(self, specified_temp_folder, output_file):
        """
            Get the temporary directory made and return the output path, old path, and temporary path.

            Parameters:
                specified_temp_folder: The temporary folder name and location if specified.
                output_file: Output file name.

            Returns:
                output_path: Full path to the output AFF4 file.
                old_path: Original path afflux was launched from.
                tmp_path: Path to write temporary files.
        """

        old_path = os.getcwd()
        if not specified_temp_folder:
            self.separator = "/"
            tmp_path = "/tmp/afflux_files_download"
            if self.os == "Windows":
                self.separator = "\\"
                tmp_path = "C:\\Users\\" + os.getlogin() + "\\AppData\\Local\\Temp\\afflux_files_download"
        else:
            if self.os == "Windows":
                self.separator = "\\"
            else:
                self.separator = "/"
            tmp_path = specified_temp_folder[0]
        os.mkdir(tmp_path)
        # Check if output file is a positional path or not.
        if os.path.isabs(output_file):
            output_path = output_file
        else:
            output_path = old_path + self.separator + output_file

        return [output_path, old_path, tmp_path]

    def print_image_metadata(self, resolver, volume, image):
        """
            Print all the metadata stored in the AFF4 image.

            Parameters:
                resolver:
                volume: AFF4 Image volume
                image: AFF4 image
        """

        printUtils.multi_print(Fore.GREEN + "\t%s " % (image.name()) + Fore.RESET + "<%s>"
                               % (self.trim_volume(volume.urn, image.urn)))
        with resolver.AFF4FactoryOpen(image.urn) as srcStream:
            if type(srcStream) == aff4_map.AFF4Map2:
                source_ranges = sorted(srcStream.tree)
                for n in source_ranges:
                    d = n.data
                    printUtils.multi_print("\t\t[%x,%x] -> %s[%x,%x]" % (
                        d.map_offset, d.length, srcStream.targets[d.target_id], d.target_offset, d.length))

    def trim_volume(self, volume, image):
        """
            Trim the volume.

            Parameters:
                volume:
                image:
        """

        if not self.verbose:
            vol_string = utils.SmartUnicode(volume)
            image_string = utils.SmartUnicode(image)
            if image_string.startswith(vol_string):
                image_string = image_string[len(vol_string):]
            return image_string
        else:
            return image

    def meta(self, file, password):
        """
            Get metadata.

            Parameters:
                file:
                password:
        """
        with container.Container.openURNtoContainer(rdfvalue.URN.FromFileName(file)) as volume:
            print_turtle(volume.resolver, volume)

            if password is not None:
                assert not issubclass(volume.__class__, container.PhysicalImageContainer)
                volume.setPassword(password[0])
                child_volume = volume.getChildContainer()
                print_turtle(child_volume.resolver, child_volume)
                for image in child_volume.images():
                    self.print_image_metadata(child_volume.resolver, child_volume, image)
            else:
                for image in volume.images():
                    self.print_image_metadata(volume.resolver, volume, image)

    def add_path_names_to_volume(self, resolver, volume, path_names, recursive, follow_symlinks=False):
        """
            Add a path to an AFF4 file.

            Parameters:
                resolver:
                volume:
                path_names:
                recursive:
                follow_symlinks:
        """

        fsmeta = None
        error_paths = []
        no_image = []
        found_container = False
        first_run = True

        # Check if the user supplied paths to not image
        for pathname in path_names:
            if pathname[-1] == "-":
                no_image.append(pathname[:-1])

        # Remove them from the main path list to image
        for path in no_image:
            path_names.remove(path + "-")

        # Skip the specified paths
        # TODO: Positional path changes?
        # Imaging for example:
        #   C:\User\test\Desktop
        # Will extract to:
        #   out/c/User/test/Desktop
        # We should probably not do that.
        for pathname in path_names:
            if pathname in no_image:
                if self.verbose:
                    printUtils.multi_print(Fore.RED + "\t[*] Skipping path: %s" % pathname)
                continue

            if not os.access(pathname, os.R_OK):
                if self.verbose:
                    printUtils.multi_print(Fore.RED + "\tUnable to access: " + Fore.RESET + "%s" % pathname)
                error_paths.append("\t[-] Unable to access: " + Fore.RESET + "%s" % pathname)
                continue
            if not found_container:
                if pathname.lower() == self.container_path:
                    found_container = True
                    if self.verbose:
                        printUtils.multi_print(Fore.RED + "\tSkipping our container.")
                    continue
            pathname = utils.SmartUnicode(pathname)
            if self.verbose:
                printUtils.multi_print(Fore.GREEN + "\tAdding:" + Fore.RESET + " %s" % pathname)
            try:
                fsmeta = logical.FSMetadata.create(pathname)
            except FileNotFoundError:
                if self.verbose:
                    printUtils.multi_print(Fore.RED + "\tFile not found: " + Fore.RESET + "%s" % pathname)
                error_paths.append("\t[-] File not found: " + Fore.RESET + "%s" % pathname)
                continue
            if os.path.islink(pathname):  # Symlink logic
                if not follow_symlinks:
                    if self.verbose:
                        printUtils.multi_print(Fore.RED + "\tSkipping symlink:" + Fore.RESET + " %s" % pathname)
                    continue
                else:
                    symlink_target = os.readlink(pathname)  # Check if we are already imaging the symlink
                    ignore_symlink = False
                    if self.verbose:
                        printUtils.multi_print(Fore.GREEN + "\tFound symlink, points to:" + Fore.RESET
                                               + " %s" % symlink_target)
                    for name in path_names:
                        if name in symlink_target:
                            if self.verbose:
                                printUtils.multi_print(Fore.RED + "\tAlready imaging symlink target, skipping:"
                                                       + Fore.RESET + " %s" % pathname)
                            ignore_symlink = True
                            break
                    if ignore_symlink:
                        continue

            if os.path.isdir(pathname):
                if volume.isAFF4Collision(pathname):
                    image_urn = rdfvalue.URN("aff4://%s" % uuid.uuid4())
                else:
                    image_urn = volume.urn.Append(escaping.arnPathFragment_from_path(pathname), quote=False)

                fsmeta.urn = image_urn
                fsmeta.store(resolver)
                resolver.Set(volume.urn, image_urn, rdfvalue.URN(lexicon.standard11.pathName),
                             rdfvalue.XSDString(pathname))
                resolver.Add(volume.urn, image_urn, rdfvalue.URN(lexicon.AFF4_TYPE),
                             rdfvalue.URN(lexicon.standard11.FolderImage))
                resolver.Add(volume.urn, image_urn, rdfvalue.URN(lexicon.AFF4_TYPE),
                             rdfvalue.URN(lexicon.standard.Image))
                # Recursively image. If just a single folder is specified, we still need to get the paths and files
                # inside it at least once, use first_run for that.
                if recursive or first_run:
                    try:
                        first_run = False
                        for child in os.listdir(pathname):
                            path_names.append(os.path.join(pathname, child))
                    except PermissionError:
                        if self.verbose:
                            printUtils.multi_print(Fore.RED + "\tUnable to access: " + Fore.RESET + "%s" % pathname)
                        error_paths.append("\t[-] Unable to access: " + Fore.RESET + "%s" % pathname)
                        continue
                    except OSError as e:
                        if "Errno 22" in str(e):
                            if self.verbose:
                                printUtils.multi_print(
                                    Fore.RED + "\tUnable to add, file non-existent: " + Fore.RESET + "%s" % pathname)
                            error_paths.append(
                                "\t[-] Unable to add, file non-existent: " + Fore.RESET + "%s" % pathname)
                            continue
                        else:
                            print(e)
            else:
                try:
                    mode = os.stat(pathname).st_mode
                    if S_ISCHR(mode) or S_ISFIFO(mode) or S_ISBLK(mode) or S_ISPORT(mode) or S_ISSOCK(mode):
                        if self.verbose:
                            printUtils.multi_print(Fore.RED + "\tError: Pipe or descriptor file: %s" % pathname)
                        error_paths.append("\t[-] Pipe or descriptor file: %s" % pathname)
                        continue
                    with open(pathname, "rb") as src:
                        hasher = linear_hasher.StreamHasher(src, [lexicon.HASH_SHA1, lexicon.HASH_MD5])
                        try:
                            urn = volume.writeLogicalStream(pathname, hasher, fsmeta.length)
                        except OSError as e:
                            if "Errno 28" in str(e):
                                printUtils.multi_print(Fore.RED + "[-] Out of storage space on machine.")
                                return False
                        fsmeta.urn = urn
                        fsmeta.store(resolver)
                        for h in hasher.hashes:
                            hh = hashes.newImmutableHash(h.hexdigest(), hasher.hashToType[h])
                            resolver.Add(urn, urn, rdfvalue.URN(lexicon.standard.hash), hh)
                except PermissionError:
                    if self.verbose:
                        printUtils.multi_print(Fore.RED + "\tError: Unable to access: " + Fore.RESET + "%s" % pathname)
                    error_paths.append("\t[-] Unable to access: " + Fore.RESET + "%s" % pathname)
                    continue
                except OSError as e:
                    if "Errno 22" in str(e):
                        if self.verbose:
                            printUtils.multi_print(Fore.RED + "\tError: Unable to add, file non-existent: "
                                                   + Fore.RESET + "%s" % pathname)
                        error_paths.append("\t[-] Unable to add, file non-existent: " + Fore.RESET + "%s" % pathname)
                        continue
                    if "Errno 6" in str(e):
                        if self.verbose:
                            printUtils.multi_print(Fore.RED + "\tError: No such device or address: " + Fore.RESET
                                                   + "%s" % pathname)
                        error_paths.append("\t[-] No such device or address: " + Fore.RESET + "%s" % pathname)
                        continue
                    if "Errno 123" in str(e):
                        if self.verbose:
                            printUtils.multi_print(Fore.RED + "\tError: No medium found: " + Fore.RESET + "%s"
                                                   % pathname)
                        error_paths.append("\t[-] No medium found: " + Fore.RESET + "%s" % pathname)
                        continue
                    else:
                        printUtils.multi_print(e)
                        exit()
        if self.verbose:
            if error_paths:
                printUtils.multi_print(Fore.RED + "\n\t[-] Errors:")
                for path in error_paths:
                    printUtils.multi_print(Fore.RED + "%s" % path)

    def add_path_names(self, container_name, path_names, recursive, append, password, continuing=False,
                       symlinks=False):
        """
            Add paths to a volume.

            Parameters:
                container_name:
                path_names:
                recursive:
                append:
                password:
                continuing:
                symlinks:
        """

        try:
            if self.zip:
                if ".zip" not in container_name:
                    zip_name = container_name.replace(".aff4", ".zip")
                else:
                    zip_name = container_name.replace(".aff4", "")
                with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, strict_timestamps=False) as zip_ref:
                    for path in path_names:
                        for folder_name, subfolders, filenames in os.walk(path):
                            # Add the folder
                            if self.verbose:
                                printUtils.multi_print(Fore.GREEN + "\tAdding: " + Fore.RESET + folder_name)
                            zip_ref.write(folder_name, arcname=folder_name)
                            # Add the files
                            for filename in filenames:
                                if self.verbose:
                                    printUtils.multi_print(Fore.GREEN + "\tAdding: " + Fore.RESET + folder_name +
                                                           self.separator + filename)
                                file_path = os.path.join(folder_name, filename)
                                zip_ref.write(file_path, arcname=file_path)

                zip_ref.close()
                return True
        except IsADirectoryError:
            printUtils.multi_print(Fore.RED + "[-] Error: " + Fore.RESET + container_name + " is a directory.")
            return False

        with data_store.MemoryDataStore() as resolver:
            container_urn = rdfvalue.URN.FromFileName(container_name)
            urn = None
            encryption = False
            self.container_path = os.path.abspath(container_name).lower()

            if password is not None:
                encryption = True
                if self.verbose:
                    printUtils.multi_print(Fore.GREEN + "[*] Encryption enabled")
            if not append:
                # The 'aff4:ImageStream' value that Magnet doesn't like is generated here.
                # Specifically 'aff4_image.AFF4Image.NewAFF4Image'. Magnet expects a 'size' value?
                with container.Container.createURN(resolver, container_urn, encryption=encryption) as volume:
                    if not continuing:
                        printUtils.multi_print(Fore.GREEN + "[*] Creating AFF4Container: " + Fore.RESET
                                               + "file://%s <%s>" % (container_name, volume.urn))
                    if password is not None:
                        volume.setPassword(password[0])
                        child_volume = volume.getChildContainer()
                        self.add_path_names_to_volume(child_volume.resolver, child_volume, path_names, recursive,
                                                      follow_symlinks=symlinks)
                    else:
                        self.add_path_names_to_volume(resolver, volume, path_names, recursive, follow_symlinks=symlinks)
            else:
                with container.Container.openURNtoContainer(container_urn, mode="+") as volume:
                    if password is not None:
                        volume.setPassword(password[0])
                        child_volume = volume.getChildContainer()
                        self.add_path_names_to_volume(child_volume.resolver, child_volume, path_names, recursive,
                                                      follow_symlinks=symlinks)
                    else:
                        self.add_path_names_to_volume(resolver, volume, path_names, recursive, follow_symlinks=symlinks)
            return True

    def extract_all_from_volume(self, container_urn, volume, dest_folder):
        """
            Extract files from a volume to a destination folder.

            Parameters:
                container_urn:
                volume:
                dest_folder:
        """

        print_volume_info(container_urn.original_filename, volume)
        resolver = volume.resolver
        for image_urn in resolver.QueryPredicateObject(volume.urn, lexicon.AFF4_TYPE, lexicon.standard11.FolderImage):
            image_urn = utils.SmartUnicode(image_urn)
            path_name = next(resolver.QuerySubjectPredicate(volume.urn, image_urn, lexicon.standard11.pathName)).value
            if path_name.startswith("/"):
                path_name = "." + path_name
            if path_name[1:3] == """:\\""":
                path_name = path_name[3:]
            dest_file = os.path.join(dest_folder, path_name)
            if not os.path.exists(dest_file):
                if self.verbose:
                    printUtils.multi_print(Fore.GREEN + "   Creating directory: " + Fore.RESET + str(path_name))
                os.makedirs(dest_file)

        for image_urn in resolver.QueryPredicateObject(volume.urn, lexicon.AFF4_TYPE, lexicon.standard11.FileImage):
            image_urn = utils.SmartUnicode(image_urn)

            path_name = next(resolver.QuerySubjectPredicate(volume.urn, image_urn, lexicon.standard11.pathName)).value
            if path_name.startswith("/"):
                path_name = "." + path_name
            with resolver.AFF4FactoryOpen(image_urn) as srcStream:
                if dest_folder != "-":
                    if path_name.startswith("/"):
                        path_name = "." + path_name
                    if path_name[1:3] == """:\\""":
                        path_name = path_name[3:]
                    dest_file = os.path.join(dest_folder, path_name)
                    if self.verbose:
                        printUtils.multi_print(f"{Fore.GREEN}Extracting:{Fore.RESET} [{path_name}] -> [{dest_file}]")
                    if self.os == "Windows":  # Desktop.ini requires systems
                        if "desktop.ini" in dest_file:  # privileges to overwrite.
                            if self.verbose:
                                printUtils.multi_print(f"{Fore.RED}Skipping:{Fore.RESET} [{path_name}] -> "
                                                       f"[{dest_file}]")
                            continue
                    if not os.path.exists(os.path.dirname(dest_file)):
                        try:
                            os.makedirs(os.path.dirname(dest_file))
                        except OSError as exc:  # Guard against race condition
                            if exc.errno != errno.EEXIST:
                                raise
                    with open(dest_file, "wb") as destStream:
                        shutil.copyfileobj(srcStream, destStream)
                    last_written = next_or_none(
                        resolver.QuerySubjectPredicate(volume.urn, image_urn, lexicon.standard11.lastWritten))
                    last_accessed = next_or_none(
                        resolver.QuerySubjectPredicate(volume.urn, image_urn, lexicon.standard11.lastAccessed))
                    record_changed = next_or_none(
                        resolver.QuerySubjectPredicate(volume.urn, image_urn, lexicon.standard11.recordChanged))
                    birth_time = next_or_none(
                        resolver.QuerySubjectPredicate(volume.urn, image_urn, lexicon.standard11.birthTime))
                    logical.resetTimestamps(dest_file, last_written, last_accessed, record_changed, birth_time)

                else:
                    shutil.copyfileobj(srcStream, sys.stdout)

    def extract_all(self, container_name, dest_folder, password=None):
        """
            Extract from volume.
        """
        printUtils.multi_print(Fore.GREEN + "\n")
        container_urn = rdfvalue.URN.FromFileName(container_name)

        with container.Container.openURNtoContainer(container_urn) as volume:
            if password is not None:
                assert not issubclass(volume.__class__, container.PhysicalImageContainer)
                volume.setPassword(password[0])
                child_volume = volume.getChildContainer()
                self.extract_all_from_volume(container_urn, child_volume, dest_folder)
            else:
                self.extract_all_from_volume(container_urn, volume, dest_folder)

    def extract_from_volume(self, container_urn, volume, image_urns, dest_folder):
        print_volume_info(container_urn.original_filename, volume)
        resolver = volume.resolver
        for image_urn in image_urns:
            image_urn = utils.SmartUnicode(image_urn)

            path_name = next(resolver.QuerySubjectPredicate(volume.urn, image_urn, volume.lexicon.pathName))

            with resolver.AFF4FactoryOpen(image_urn) as srcStream:
                if dest_folder != "-":
                    path_name = escaping.arnPathFragment_from_path(path_name.value)
                    while path_name.startswith("/"):
                        path_name = path_name[1:]
                    dest_file = os.path.join(dest_folder, path_name)
                    if self.verbose:
                        printUtils.multi_print(Fore.GREEN + "[*] \tAttempting to extract:" + Fore.RESET
                                               + " %s to %s" % (path_name, dest_file))
                    if self.os == "Windows":  # Desktop.ini requires systems
                        if "desktop.ini" in dest_file:  # privileges to overwrite.
                            if self.verbose:
                                printUtils.multi_print(Fore.RED + "   [DEBUG] Skipping:" + Fore.RESET
                                                       + " %s to %s\n" % (path_name, dest_file) + Fore.RED
                                                       + "   [DEBUG] Need system privileges.")
                            continue
                    if not os.path.exists(os.path.dirname(dest_file)):
                        try:
                            os.makedirs(os.path.dirname(dest_file))
                        except OSError as exc:  # Guard against race condition
                            if exc.errno != errno.EEXIST:
                                raise
                    with open(dest_file, "wb") as destStream:
                        shutil.copyfileobj(srcStream, destStream, length=32 * 2014)
                        if self.verbose:
                            printUtils.multi_print(Fore.GREEN + "[+] \tExtracted:" + Fore.RESET
                                                   + " %s to %s" % (path_name, dest_file))
                else:
                    shutil.copyfileobj(srcStream, sys.stdout)

    def extract(self, container_name, image_urns, dest_folder, password):
        with data_store.MemoryDataStore():
            container_urn = rdfvalue.URN.FromFileName(container_name)

            with container.Container.openURNtoContainer(container_urn) as volume:
                if password is not None:
                    assert not issubclass(volume.__class__, container.PhysicalImageContainer)
                    volume.setPassword(password[0])
                    child_volume = volume.getChildContainer()
                    self.extract_from_volume(container_urn, child_volume, image_urns, dest_folder)
                else:
                    self.extract_from_volume(container_urn, volume, image_urns, dest_folder)
