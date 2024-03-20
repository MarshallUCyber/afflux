# -*- coding: utf-8 -*-
# By Marshall University on 11/2/2021
# PyQt GUI for the imager

from os import listdir, path, environ
from sys import argv, exit

from PyQt5 import QtCore, QtWidgets
from colorama import init, Fore
import utilities

utils = utilities.Utilities()
utils.set_gui()

try:
    import pyi_splash

    pyi_splash.update_text("Afflux!")
except Exception as e:
    pass

init(autoreset=True)

# Temporarily set 'QT_STYLE_OVERRIDE' environment variable to suppress QT warnings on some systems.
environ["QT_STYLE_OVERRIDE"] = ""

import imaging
from plugin_manager import PluginCollection
from gui.afflux_gui_threads import (ImageFolderThread, SSHImageThread, iOSAFCImageThread, AndroidImageThread,
                                    FTPImageThread, SMBImageThread, plugin_names)
from gui import afflux_gui_ui
from gui import breeze_resources

plugins = PluginCollection('plugins', False)
imager = imaging.Imager(False)


class AffluxGui:

    def __init__(self, ui):
        """
            Constructor for the Ui_MainWindow class.
        """

        self.android_combo_box = None
        self.ui = ui
        self.no_errors = True
        self.encryption = None
        self.drivesList = None
        self.driveSelected = False
        self.success = True
        self.files_image = False
        self.android_devices = []
        self.files_image_filenames = []
        self.prompt_overwrite = True

    def output_text(self, output):
        """
            Outputs text to the GUI output box.
        """

        if "[-] Error" in str(output):
            self.no_errors = False
            self.warning_box("Error", output.replace("[-] Error: ", ""))
            self.ui.outputTextBrowser.append(output)
        else:
            self.ui.outputTextBrowser.append(output)

    def warning_box(self, text, details):
        """
            Create a warning alert box.
        """

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(text)
        msg.setInformativeText(details)
        msg.setWindowTitle("Afflux GUI")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def information_box(self, text, details):
        """
            Create an information alert box.
        """

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(text)
        msg.setInformativeText(details)
        msg.setWindowTitle("Afflux GUI")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def yes_no_box(self, text, details):
        """
            Create a yes/no alert box.
        """

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(text)
        msg.setInformativeText(details)
        msg.setWindowTitle("Afflux GUI")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        result = msg.exec_()
        if result == msg.Yes:
            return True
        else:
            return False

    def finished_imaging(self):
        """
            A finished imaging alert box.
        """
        try:
            # Check the return value from the imaging
            if self.image_thread.result:
                if self.ui.zipImageCheckBox.isChecked():
                    self.information_box("Imaging completed!", "An zip container has been created.")
                else:
                    self.information_box("Imaging completed!", "An AFF4 logical image container has been created.")
                self.ui.outputTextBrowser.append("[+] Finished imaging!")
            else:
                if self.no_errors:
                    self.warning_box("Imaging failed!", "An error has occurred and an AFF4 container was not created.")
                    self.no_errors = True
                    pass
        except:
            pass

    def check_output_file(self):
        """
            Check if the output file box has text entered, if not, prompt the user for a file.
        """

        if self.ui.outputFileLineEdit.text() == "":
            output_file = QtWidgets.QFileDialog.getSaveFileName(self.ui.centralwidget, 'Save File')[0]
            self.prompt_overwrite = False
            print(output_file)
        else:
            output_file = self.ui.outputFileLineEdit.text()
        return output_file

    def output_file_button_clicked(self):
        """
            Event for the output file button.
        """

        output_file = QtWidgets.QFileDialog.getSaveFileName(self.ui.centralwidget, 'Save File')[0]
        self.ui.outputFileLineEdit.setText(output_file)
        self.prompt_overwrite = False

    def check_encryption(self):
        """
            Check if the encryption options are enabled.
        """

        if (self.ui.encryptionPasswordLineEdit.text() != "") and (self.ui.encryptImageCheckBox.isChecked()):
            return [self.ui.encryptionPasswordLineEdit.text().strip()]

    def image_files_clicked(self):
        """
            Image multiple files using the small button.
        """

        # Setup dialog to prompt for files
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)

        if dlg.exec_():
            for path in dlg.selectedFiles():
                self.files_image_filenames.append(path)

        # Check to see if any files were given
        if not dlg.selectedFiles():
            return False

        for path in self.files_image_filenames:
            utils.multi_print(Fore.GREEN + "[*] File added: " + path + Fore.RESET)
            self.ui.outputTextBrowser.append("[*] File added: " + path)

        return True

    def image_folders_clicked(self):
        """
            Image multiple files using the small button.
        """

        # Setup dialog to prompt for files
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.Directory)

        if dlg.exec_():
            for path in dlg.selectedFiles():
                self.files_image_filenames.append(path)

        # Check to see if any files were given
        if not dlg.selectedFiles():
            return False

        for path in self.files_image_filenames:
            utils.multi_print(Fore.GREEN + "[*] Folder added: " + path + Fore.RESET)
            self.ui.outputTextBrowser.append("[*] Folder added: " + path)

        return True

    def try_image_files(self):
        """
            Check if the files image button has been clicked, if so, image.
        """

        if self.files_image_filenames:
            output_file = self.check_output_file()
            self.image_thread = ImageFolderThread(self.ui.verboseCheckBox.isChecked(),
                                                  self.files_image_filenames,
                                                  self.ui.filesystemRecursiveCheckBox.isChecked(),
                                                  output_file,
                                                  self.encryption,
                                                  self.ui.filesystemFollowSymlinksCheckbox.isChecked(),
                                                  self.ui.zipImageCheckBox.isChecked())
            # Pass the thread through so we can emit a signal back to us with text to output
            utils.set_text_worker(self.image_thread)
            self.image_thread.start()
            self.image_thread.signal.connect(self.output_text)
            self.image_thread.finished.connect(self.finished_imaging)
        elif self.ui.filesystemPathLineEdit.text() != "":
            if not self.files_image_filenames:
                output_file = self.check_output_file()
                self.image_thread = ImageFolderThread(self.ui.verboseCheckBox.isChecked(),
                                                      self.ui.filesystemPathLineEdit.text().split(),
                                                      self.ui.filesystemRecursiveCheckBox.isChecked(),
                                                      output_file,
                                                      self.encryption,
                                                      self.ui.filesystemFollowSymlinksCheckbox.isChecked(),
                                                      self.ui.zipImageCheckBox.isChecked())
                utils.set_text_worker(self.image_thread)
                self.image_thread.start()
                self.image_thread.signal.connect(self.output_text)
                self.image_thread.finished.connect(self.finished_imaging)
        else:
            pass

    def try_image_android(self):
        """
            Attempt to image an Android device.
        """

        if self.ui.androidAddressLineEdit.text() == "" and (int(self.ui.androidDeviceComboBox.currentIndex() == -1)):
            self.warning_box("No Android device selected.", "No Android device was selected from the dropdown or "
                                                            "no IP address was entered.")
            return False

        if self.ui.androidDirectoryLineEdit.text() != "" or self.ui.androidAddressLineEdit.text() != "":

            # If an IP is entered in the text box, set the labels for the phone information
            if self.ui.androidAddressLineEdit.text() != "":
                plugin = plugins.return_plugin(plugin_names["android"])
                plugin.arguments = type('', (), {})
                plugin.arguments.verbose = self.ui.verboseCheckBox.isChecked()
                plugin.arguments.append = False
                plugin.verbose = True
                if self.ui.androidKeygenCheckbox.isChecked():
                    plugin.key_gen("adb")
                plugin.sign("adb")
                if ":" in self.ui.androidAddressLineEdit.text():
                    ip_address, port = self.ui.androidAddressLineEdit.text().split(":")
                    out = plugin.connect(ip_address=ip_address, port=port)
                else:
                    out = plugin.connect(ip_address=self.ui.androidAddressLineEdit.text(), port=5555)
                version = plugin.execute_command("getprop ro.build.version.release")
                if not version:
                    self.warning_box("Could not Connect", "ADB could not be connected. Make sure the device IP and"
                                                          " Port is correct.")
                    return False
                model = plugin.execute_command("getprop ro.product.model")
                build = plugin.execute_command("getprop ro.build.version.sdk")
                name = plugin.execute_command("getprop ro.product.name")
                self.android_combo_box.addItem(name)
                plugin.close()
                self.ui.androidVersionLabel.setText(version.strip())
                self.ui.androidModelLabel.setText(model.strip())
                self.ui.androidBuildLabel.setText(build.strip())

            directory = self.ui.androidDirectoryLineEdit.text().strip()
            self.encryption = self.check_encryption()
            if self.ui.androidAddressLineEdit.text() != "":
                device = self.ui.androidAddressLineEdit.text()
                network = True
            else:
                device = self.android_devices[self.ui.androidDeviceComboBox.currentIndex()]
                network = False

            output_file = self.check_output_file()
            self.image_thread = AndroidImageThread(self.ui.verboseCheckBox.isChecked(),
                                                   directory,
                                                   output_file,
                                                   self.encryption,
                                                   device,
                                                   network,
                                                   self.ui.androidFollowSymlinksCheckbox.isChecked(),
                                                   self.ui.androidRootCheckbox.isChecked(),
                                                   self.ui.zipImageCheckBox.isChecked(),
                                                   keygen=self.ui.androidKeygenCheckbox.isChecked())
            # Pass the thread through so we can emit a signal back to us with text to output
            utils.set_text_worker(self.image_thread)
            self.image_thread.start()
            self.image_thread.signal.connect(self.output_text)
            self.image_thread.finished.connect(self.finished_imaging)

    def try_image_ios(self):
        """
            Attempt to image a selected iOS device.
        """

        # Check for encrypting the aff4 image
        self.encryption = self.check_encryption()

        if self.ui.iosAFCRadioButton.isChecked():
            service = "com.apple.afc"
        else:
            service = "com.apple.afc2"

        if int(self.ui.iosDeviceComboBox.currentIndex()) == -1:
            self.warning_box("No device selected.", "No device was selected from the dropdown list.")
            return False

        # Start a QThread that does the imaging work
        output_file = self.check_output_file()
        self.image_thread = iOSAFCImageThread(self.ui.verboseCheckBox.isChecked(),
                                              service,
                                              output_file,
                                              self.encryption,
                                              int(self.ui.iosDeviceComboBox.currentIndex()),
                                              self.ui.iosClearPairsCheckbox.isChecked(),
                                              self.ui.iosRePairCheckbox.isChecked(),
                                              self.ui.zipImageCheckBox.isChecked())
        # Pass the thread through so we can emit a signal back to us with text to output
        utils.set_text_worker(self.image_thread)
        self.image_thread.start()
        self.image_thread.signal.connect(self.output_text)
        self.image_thread.finished.connect(self.finished_imaging)

    def try_image_drive(self):
        """
            Attempt to image a selected drive.
        """

        self.encryption = self.check_encryption()
        drive = self.ui.drivesComboBox.currentText()
        if drive != "<select drive>":
            if self.os == "Linux":
                # Get the current username and use that to get the media path
                drive_path = ("/media/%s" % path.expanduser('~').split("/")[-1] + "/") + drive
            if self.os == "Windows":
                drive_path = "%s:\\" % drive
            output_file = self.check_output_file()
            self.image_thread = ImageFolderThread(self.ui.verboseCheckBox.isChecked(),
                                                  [drive_path],
                                                  self.ui.drivesRecursiveCheckBox.isChecked(),
                                                  output_file,
                                                  self.encryption,
                                                  self.ui.drivesFollowSymlinksCheckbox.isChecked(),
                                                  self.ui.zipImageCheckBox.isChecked())
            # Pass the thread through so we can emit a signal back to us with text to output
            utils.set_text_worker(self.image_thread)
            self.image_thread.start()
            self.image_thread.signal.connect(self.output_text)
            self.image_thread.finished.connect(self.finished_imaging)

    def try_image_ssh(self):
        """
            Attempt to image via SSH.
        """

        output_file = self.check_output_file()
        self.encryption = self.check_encryption()
        if self.ui.sshServerLineEdit.text() != "":
            self.image_thread = SSHImageThread(self.ui.verboseCheckBox.isChecked(),
                                               self.ui.sshServerLineEdit.text(),
                                               output_file,
                                               self.encryption,
                                               self.ui.sshUsernameLineEdit.text(),
                                               self.ui.sshPasswordLineEdit.text(),
                                               self.ui.sshDirectoryLineEdit.text(),
                                               int(self.ui.sshPortLineEdit.text()),
                                               self.ui.sshFollowSymlinksCheckbox.isChecked(),
                                               self.ui.sshRecursiveCheckbox.isChecked(),
                                               self.ui.zipImageCheckBox.isChecked())
            # Pass the thread through so we can emit a signal back to us with text to output
            utils.set_text_worker(self.image_thread)
            self.image_thread.start()
            self.image_thread.signal.connect(self.output_text)
            self.image_thread.finished.connect(self.finished_imaging)
        else:
            self.warning_box("Error", "No hostname or IP specified.")

    def try_image_ftp(self):
        """
            Attempt to image via FTP.
        """

        output_file = self.check_output_file()
        self.encryption = self.check_encryption()
        if self.ui.ftpServerLineEdit.text() != "":
            self.image_thread = FTPImageThread(self.ui.verboseCheckBox.isChecked(),
                                               self.ui.ftpServerLineEdit.text(),
                                               output_file,
                                               self.encryption,
                                               self.ui.ftpUsernameLineEdit.text(),
                                               self.ui.ftpPasswordLineEdit.text(),
                                               self.ui.ftpDirectoryLineEdit.text(),
                                               int(self.ui.ftpPortLineEdit.text()),
                                               self.ui.ftpFollowSymlinksCheckbox.isChecked(),
                                               self.ui.ftpRecursiveCheckbox.isChecked(),
                                               self.ui.zipImageCheckBox.isChecked())
            # Pass the thread through so we can emit a signal back to us with text to output
            utils.set_text_worker(self.image_thread)
            self.image_thread.start()
            self.image_thread.signal.connect(self.output_text)
            self.image_thread.finished.connect(self.finished_imaging)
        else:
            self.warning_box("Error", "No hostname or IP specified.")

    def try_image_smb(self):
        """
            Attempt to image via SMB.
        """

        output_file = self.check_output_file()
        self.encryption = self.check_encryption()
        if self.ui.smbHostnameLineEdit.text() != "":
            if self.ui.smbShareLineEdit.text() != "":
                self.image_thread = SMBImageThread(self.ui.verboseCheckBox.isChecked(),
                                                   self.ui.smbHostnameLineEdit.text(),
                                                   output_file,
                                                   self.encryption,
                                                   self.ui.smbUsernameLineEdit.text(),
                                                   self.ui.smbPasswordLineEdit.text(),
                                                   self.ui.smbShareLineEdit.text(),
                                                   int(self.ui.smbPortLineEdit.text()),
                                                   self.ui.smbFollowSymlinksCheckbox.isChecked(),
                                                   self.ui.smbRecursiveCheckbox.isChecked(),
                                                   self.ui.zipImageCheckBox.isChecked())
                # Pass the thread through so we can emit a signal back to us with text to output
                utils.set_text_worker(self.image_thread)
                self.image_thread.start()
                self.image_thread.signal.connect(self.output_text)
                self.image_thread.finished.connect(self.finished_imaging)
            else:
                self.warning_box("Error", "No share specified.")
        else:
            self.warning_box("Error", "No hostname specified.")

    def image_button_clicked(self):
        """
            Handler for the 'Image' button being clicked.
        """

        if self.ui.outputFileLineEdit.text() == "":
            self.warning_box("Error:", "An ouptut file must be selected.")
            return False

        if self.prompt_overwrite:
            if path.isfile(self.ui.outputFileLineEdit.text()):
                result = self.yes_no_box("Overwrite file?",
                                         "%s already exists, overwrite it?" % self.ui.outputFileLineEdit.text())
                if not result:
                    return False

        # Check if we are imaging iOS
        if self.ui.tabWidget.currentIndex() == 0:
            self.try_image_ios()

        # Check if we are imaging Android
        if self.ui.tabWidget.currentIndex() == 1:
            self.try_image_android()

        # Check if we are imaging a file path
        if self.ui.tabWidget.currentIndex() == 2:
            self.try_image_files()

        # Check if twe are imaging a drive:
        if self.ui.tabWidget.currentIndex() == 3:
            self.try_image_drive()

        # Check if we are imaging SSH
        if self.ui.tabWidget.currentIndex() == 4:
            self.try_image_ssh()

        # Check if we are imaging FTP
        if self.ui.tabWidget.currentIndex() == 5:
            self.try_image_ftp()

        # Check if we are imaging SMB
        if self.ui.tabWidget.currentIndex() == 6:
            self.try_image_smb()

        return True

    def kill_threads(self):
        """
            Kill any running threads and cleanup.
        """

        try:
            self.image_thread.terminate()
            imager.cleanup()
        except:
            pass

    def setup_button_events(self):
        """
            Setup any button events and handlers.
        """

        self.ui.imagePushButton.clicked.connect(self.image_button_clicked)
        self.ui.cancelButton.clicked.connect(self.kill_threads)
        self.ui.filesystemFilesButton.clicked.connect(self.image_files_clicked)
        self.ui.filesystemFoldersButton.clicked.connect(self.image_folders_clicked)
        self.ui.outputFileButton.clicked.connect(self.output_file_button_clicked)
        self.ui.iosRefreshButton.clicked.connect(self.update_ios_devices)
        self.ui.androidRefreshButton.clicked.connect(self.update_android_devices)

    def update_ios_devices(self):
        """
            Attempt to image a selected iOS device.
        """

        plugin = plugins.return_plugin(plugin_names["apple"])
        plugin.verbose = True
        plugin.service = "com.apple.afc"
        # TODO: Add fix for if usbmuxd is not running.
        devices = plugin.get_device()
        combo_box = self.ui.iosDeviceComboBox
        for device in devices:
            combo_box.addItem(device.all_values['DeviceName'] + ", Version: " + device.all_values['ProductVersion'])

        def selectionchange(i):
            try:
                self.ui.iosVersionLabel.setText(devices[i].all_values['ProductVersion'])
                self.ui.iosBuildLabel.setText(devices[i].all_values['BuildVersion'])
                self.ui.iosModelLabel.setText(devices[i].all_values['ProductType'])
            except:
                pass

        # Go ahead and change selection to update the device info labels
        selectionchange(0)
        combo_box.currentIndexChanged.connect(selectionchange)

    def update_android_devices(self):
        """
            Update Android devices.
        """

        plugin = plugins.return_plugin(plugin_names["android"])
        plugin.verbose = True
        self.android_devices = plugin.list_devices()
        self.android_combo_box = self.ui.androidDeviceComboBox
        for device in self.android_devices:
            self.android_combo_box.addItem(device)

        def selectionchange(i):
            try:
                plugin.sign("adb")
                result = plugin.connect(serial=device)
                version = plugin.execute_command("getprop ro.build.version.release")
                model = plugin.execute_command("getprop ro.product.model")
                build = plugin.execute_command("getprop ro.build.version.sdk")
                plugin.close()
                self.ui.androidVersionLabel.setText(version.strip())
                self.ui.androidModelLabel.setText(model.strip())
                self.ui.androidBuildLabel.setText(build.strip())
            except:
                pass

        selectionchange(0)
        self.android_combo_box.currentIndexChanged.connect(selectionchange)

    def update_drives(self):
        """
            Populate the drives combobox
        """

        self.ui.drivesComboBox.addItem("<select drive>")
        imager.check_os()
        self.os = imager.os
        if self.os == "Linux":
            try:
                self.drivesList = listdir("/media/%s" % path.expanduser('~').split("/")[-1])
            except FileNotFoundError:
                self.drivesList = listdir("/media/")
            for dir in self.drivesList:
                self.ui.driveComboBox.addItem(dir)
        if self.os == "Windows":
            from ctypes import windll
            import string
            self.drivesList = []
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    self.drivesList.append(letter)
                bitmask >>= 1
            for dir in self.drivesList:
                self.ui.drivesComboBox.addItem(dir)


if __name__ == "__main__":
    # Cleanup any temp files during the splash screen
    imager.cleanup()

    # Initialize Window
    app = QtWidgets.QApplication(argv)

    # Add dark and light mode :)
    if len(argv) > 1:
        file = None
        if argv[1] == '-d':
            file = QtCore.QFile(":/dark/stylesheet.qss")
        elif argv[1] == '-dg':
            file = QtCore.QFile(":/dark-green/stylesheet.qss")
        elif argv[1] == '-dp':
            file = QtCore.QFile(":/dark-purple/stylesheet.qss")
        elif argv[1] == '-l':
            file = QtCore.QFile(":/light/stylesheet.qss")
        elif argv[1] == '-lg':
            file = QtCore.QFile(":/light-green/stylesheet.qss")
        elif argv[1] == '-lp':
            file = QtCore.QFile(":/light-purple/stylesheet.qss")
        try:
            file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
            stream = QtCore.QTextStream(file)
            app.setStyleSheet(stream.readAll())
        except:
            pass

    MainWindow = QtWidgets.QMainWindow()
    ui = afflux_gui_ui.Ui_MainWindow()
    ui.setupUi(MainWindow)
    try:
        pyi_splash.close()
    except Exception as e:
        pass
    MainWindow.show()

    # Go ahead and print to output window
    textBrowser = ui.outputTextBrowser
    textBrowser.setAcceptRichText(True)
    textBrowser.append("Afflux! <i>By Marshall University</i>\n")

    afflux_ui = AffluxGui(ui)
    # Setup button events
    afflux_ui.setup_button_events()

    # Search for connected iOS devices and display them
    afflux_ui.update_ios_devices()
    afflux_ui.update_android_devices()

    # Update connected drives
    afflux_ui.update_drives()

    # Start allowing printing to the GUI window

    exit(app.exec_())
