from datetime import datetime
from PyQt5 import QtCore
import utilities
import imaging
from plugin_manager import PluginCollection
from colorama import init, Fore

init(autoreset=True)

plugin_names = {
    "apple": "apple_afc",
    "android": "android_adb",
    "ssh": "generic_ssh",
    "ftp": "generic_ftp",
    "smb": "generic_smb"
}

plugins = PluginCollection('plugins', False)

utils = utilities.Utilities()
utils.set_gui()


class ImageFolderThread(QtCore.QThread):
    """
        Thread to image Folders.
    """

    signal = QtCore.pyqtSignal(str)

    def __init__(self, verbose, path_names, recursive, output_file, encryption_password, follow_symlinks, zip_image,
                 parent=None):
        super(ImageFolderThread, self).__init__(parent)
        self.verbose = verbose
        self.path_names = path_names
        self.output_file = output_file
        self.encryption_password = encryption_password
        self.recursive = recursive
        self.follow_symlinks = follow_symlinks
        self.result = True
        self.zip = zip_image

    def run(self):
        imager = imaging.Imager(self.verbose, zip=self.zip)
        start_time = datetime.now()
        utils.multi_print(Fore.GREEN + "\n[*] Imaging..." + Fore.RESET)
        imager.add_path_names(self.output_file, self.path_names, self.recursive, False,
                              self.encryption_password, symlinks=self.follow_symlinks)
        finished_time = str(datetime.now() - start_time)
        utils.multi_print(Fore.GREEN + "\n[*] Time: " + Fore.RESET + finished_time)


class iOSAFCImageThread(QtCore.QThread):
    """
        Thread to image iOS via AFC.
    """

    signal = QtCore.pyqtSignal(str)

    def __init__(self, verbose, service, output_file, encryption_password, device_num, clear_pairs, re_pair,
                 zip_image, parent=None):
        super(iOSAFCImageThread, self).__init__(parent)
        self.verbose = verbose
        self.service = service
        self.output_file = output_file
        self.encryption_password = encryption_password
        self.device_num = device_num
        self.result = False
        self.clear_pairs = clear_pairs
        self.re_pair = re_pair
        self.zip = zip_image

    def run(self):
        plugin = plugins.return_plugin(plugin_names["apple"])
        plugin.verbose = self.verbose
        plugin.service = self.service
        start_time = datetime.now()
        plugin.imager = imaging.Imager(self.verbose)
        # Quick hack to fix verbosity in the GUI without adding a bunch to the ios_afc module.
        plugin.arguments = type('', (), {})
        plugin.arguments.verbose = self.verbose
        plugin.arguments.append = False
        self.result = plugin.image_device_afc(self.output_file, self.encryption_password, self.re_pair,
                                              self.clear_pairs, self.zip, device_num=self.device_num)
        finished_time = str(datetime.now() - start_time)
        utils.multi_print(Fore.GREEN + "\n[*] Time: " + Fore.RESET + finished_time)


class AndroidImageThread(QtCore.QThread):
    """
        Thread to image Android via ADB.
    """

    signal = QtCore.pyqtSignal(str)

    def __init__(self, verbose, directories, output_file, encryption_password, device, network, follow_symlinks, root,
                 zip_image, parent=None, keygen=None):
        super(AndroidImageThread, self).__init__(parent)
        self.verbose = verbose
        self.directories = directories
        self.output_file = output_file
        self.follow_symlinks = follow_symlinks
        self.encryption_password = encryption_password
        self.network = network
        self.device = device
        self.root = root
        self.result = False
        self.zip = zip_image
        self.keygen = keygen

    def run(self):
        # android_imager = android.AndroidImage(self.verbose)
        plugin = plugins.return_plugin(plugin_names["android"])
        # Quick hack to fix verbosity in the GUI without adding a bunch to the android_adb module.
        plugin.arguments = type('', (), {})
        plugin.arguments.append = False
        plugin.arguments.verbose = self.verbose
        plugin.imager = imaging.Imager(self.verbose)
        if self.keygen:
            plugin.key_gen("adb")
        plugin.sign("adb")
        if self.network:
            if ":" in self.device:
                ip_address, port = self.device.split(":")
                utils.multi_print(
                    Fore.GREEN + "[*] Device IP: " + Fore.RESET + ip_address + Fore.GREEN + " Port: " + Fore.RESET +
                    str(port))
                out = plugin.connect(ip_address=ip_address, port=port)
            else:
                utils.multi_print(Fore.GREEN + "[*] Device IP: " + Fore.RESET + self.device)
                out = plugin.connect(ip_address=self.device, port=5555)
        else:
            out = plugin.connect(serial=self.device)
        start_time = datetime.now()
        self.result = plugin.image_device(self.directories.split(" "),
                                          self.output_file,
                                          self.encryption_password,
                                          self.follow_symlinks,
                                          self.root,
                                          self.zip)
        plugin.close()
        finished_time = str(datetime.now() - start_time)
        utils.multi_print(Fore.GREEN + "\n[*] Time: " + Fore.RESET + finished_time)


class SSHImageThread(QtCore.QThread):
    """
        Thread to image via SSH.
    """

    signal = QtCore.pyqtSignal(str)

    def __init__(self, verbose, host, output_file, encryption_password, username, password, directory, port,
                 symlinks, recursive, zip_image, parent=None):
        super(SSHImageThread, self).__init__(parent)
        self.verbose = verbose
        self.host = host
        self.output_file = output_file
        self.encryption_password = encryption_password
        self.password = password
        self.username = username
        self.directory = directory
        self.port = port
        self.symlinks = symlinks
        self.result = False
        self.recursive = recursive
        self.zip = zip_image

    def run(self):
        plugin = plugins.return_plugin(plugin_names["ssh"])
        start_time = datetime.now()
        # Quick hack to fix verbosity in the GUI without adding a bunch to the generic_ssh module.
        plugin.arguments = type('', (), {})
        plugin.arguments.verbose = self.verbose
        plugin.arguments.append = False
        plugin.imager = imaging.Imager(self.verbose)
        self.result = plugin.image_ssh(self.output_file, self.encryption_password, [self.directory], self.host,
                                       self.username, self.password, self.symlinks, self.recursive, self.zip,
                                       port=self.port)
        finished_time = str(datetime.now() - start_time)
        utils.multi_print(Fore.GREEN + "\n[*] Time: " + Fore.RESET + finished_time)


class FTPImageThread(QtCore.QThread):
    """
        Thread to image via FTP.
    """

    signal = QtCore.pyqtSignal(str)

    def __init__(self, verbose, host, output_file, encryption_password, username, password, directory, port,
                 symlinks, recursive, zip_image, parent=None):
        super(FTPImageThread, self).__init__(parent)
        self.verbose = verbose
        self.host = host
        self.output_file = output_file
        self.encryption_password = encryption_password
        self.password = password
        self.username = username
        self.directory = directory
        self.port = port
        self.symlinks = symlinks
        self.result = False
        self.recursive = recursive
        self.zip = zip_image

    def run(self):
        plugin = plugins.return_plugin(plugin_names["ftp"])
        start_time = datetime.now()
        # Quick hack to fix verbosity in the GUI without adding a bunch to the generic_ftp module.
        plugin.arguments = type('', (), {})
        plugin.arguments.verbose = self.verbose
        plugin.arguments.append = False
        plugin.imager = imaging.Imager(self.verbose, zip=self.zip)
        self.result = plugin.image_ftp(self.output_file, self.encryption_password, [self.directory], self.host,
                                       self.username, self.password, self.symlinks, 5, self.recursive, self.zip,
                                       port=self.port)
        finished_time = str(datetime.now() - start_time)
        utils.multi_print(Fore.GREEN + "\n[*] Time: " + Fore.RESET + finished_time)


class SMBImageThread(QtCore.QThread):
    """
        Thread to image via SSH.
    """

    signal = QtCore.pyqtSignal(str)

    def __init__(self, verbose, host, output_file, encryption_password, username, password, share, port,
                 symlinks, recursive, zip_image, parent=None):
        super(SMBImageThread, self).__init__(parent)
        self.verbose = verbose
        self.host = host
        self.output_file = output_file
        self.encryption_password = encryption_password
        self.password = password
        self.username = username
        self.share = share
        self.port = port
        self.symlinks = symlinks
        self.result = False
        self.recursive = recursive
        self.zip = zip_image

    def run(self):
        plugin = plugins.return_plugin(plugin_names["smb"])
        start_time = datetime.now()
        # Quick hack to fix verbosity in the GUI without adding a bunch to the generic_smb module.
        plugin.arguments = type('', (), {})
        plugin.arguments.verbose = self.verbose
        plugin.arguments.append = False
        plugin.imager = imaging.Imager(self.verbose, zip=self.zip)
        self.result = plugin.image_smb(self.output_file, self.encryption_password, self.share, self.host,
                                       self.username, self.password, self.symlinks, self.recursive, self.zip,
                                       port=self.port)
        finished_time = str(datetime.now() - start_time)
        utils.multi_print(Fore.GREEN + "\n[*] Time: " + Fore.RESET + finished_time)
