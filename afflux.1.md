% AFFLUX(1) Afflux Manual
% Andrew Clark IV
% April 23, 2023

# NAME

afflux - AFF4 logical imager

# SYNOPSIS

afflux [-hvrx] [-t DIRECTORY] [-A] [-e PASSWORD] [-o OUTPUT_FILE] [-m AFF4_IMAGE] [-p PLUGIN_NAME] [-x AFF4_IMAGE] [PLUGIN_OPTIONS]

# DESCRIPTION

Afflux is an AFF4 logical imager. The goal of the tool is to logically image modern devices when a physical image may not be possible. Afflux supports several optional arguments no matter which plugin is selected. 
These are shown with "afflux -h" and are also shown with each plugin's "-h" argument.

# OPTIONS

**-h**, **--help**
: Print help output.

**-v**, **--verbose**
: Enable verbose output.

**-t PATH**, **--temp PATH**
: Directory to create any temporary files.

**-A**, **--append**
: Append to an existing AFF4 image specified with "-o".

**-e PASSWORD**, **--container_password PASSWORD**
: Password to create an encrypted AFF4 container.

**-o OUTPUT_FILE**, **--output OUTPUT_FILE**
: Output AFF4 file name.
**--overwrite**
: Overwrite AFF4 file if it already exists.

**-m AFF4_IMAGE**, **--meta AFF4_IMAGE**
: Print the AFF4 image's metadata.

**-p PLUGIN_NAME**, **--plugin PLUGIN_NAME**
: Specify a plugin to load, or use "list" to list all plugins.

**-z**, **--zip**
: Write to a Zip container instead of AFF4.

**-x AFF4_IMAGE**, **--extract AFF4_IMAGE**
: Extract all files and folders from an AFF4 image.

# DEFAULT PLUGINS

**android_adb**
: Image an Android device via ADB over USB or over network. Supports root filesystems.

**apple_afc**
: Image a device that support AFC. Supports jailbroken and non-jailbroken devices.

**disk_image**
: Image a file or folder on the local disk.

**generic_ftp**
: Image a device via network FTP

**generic_http**
: Image a file or folder via http.

**generic_smb**
: Image a device via network SMB.

**generic_ssh**
: Image a device via network SSH.

**ios_ssh**
: Image a jailbroken device via SSH over network or USB.

**usb_drive**
: Image a local USB device or mounted drive.

# Apple_AFC Plugin

The "apple_afc" plugin allows for creating logical images from Apple devices using the AFC protocol. 
The iPod Touch, iPhone, and Apple Watch are supported. 
"-i" is used to specify "AFC" for non-jailbroken devices or "AFC2" for jailbroken devices with "Apple File Conduit 2" installed.
"-c" is used to remove all previous pairing records and "-k" is used to initiate pairing before imaging.

**-i METHOD**, **--iOS METHOD**
: Create an image from an iOS device using METHOD. Jailbroken methods: AFC, AFC2. Unjailbroken method: AFC.

**-c**, **--clear**
: Clear any pairing records made by Afflux.

**-k**, **--pair**
: Pair or re-pair the device before imaging.

# iOS_SSH Plugin

The "ios_ssh" plugin is used to image a Jailbroken device via SSH protocol. 
"-a" is used to specify the devices IP address to connect to or "-l" is used for a device connected via USB.
"-R" is used to specify the root password if it is known, default is "alpine". 
"-s" is used to enable traversing symlinks.

**-a IP**, **--address IP**
: IP address to connect to.

**-d REMOTE DIR**, **--directory REMOTE DIR**
: Remote directory to begin imaging.

**-l**, **--local**
: SSH to iOS device via network address instead of USB tunneling.

**-R ROOT_PASSWORD**, **--root-password ROOT_PASSWORD**
: Root password for jailbroken device if using SSH. Defaults to "alpine".

**-s**, **--symlinks**
: Follow and image any symlinks.

# Android_ADB Plugin
The "android_adb" plugin allows for imaging an Android device over the ADB protocol. 
"-a" is used to specify the "IP:PORT" of the device if it is on the network or "USB" if it is connected via USB. 
"-d" is used to specify the directory to image. 
Default directory is "/".
Directories that should be ignored can be specified here by placing a "-" after the directory to ignore. 
For example, to image "/" and ignore "/proc" you would use "-d / /proc-".
"-s" is used to enable the imaging to traverse symlinks. 
And "-k" is used to pair or repair the device.

**-a USB/IP:PORT**, **--android USB/IP:PORT**
: Create an image from a connected Android device using ADB. Method can be USB or via IP.

**-d [DIRECTORY [DIRECTORY ...]]**, **--directory [DIRECTORY [DIRECTORY ...]]**
: Directory to image on the device.

**-s**, **--symlinks**
: Follow and image any symlinks.

**--root**
: Check and acquire root privileges if possible.

**-k**, **--keygen**
: Regenerate pairing keys for the device.

**--timeout**
: ADB timeout amount.

**--auth-timeout**
: Timeout for CNXN authentication response.

# Generic_SSH Plugin
The "generic_ssh" plugin is used for imaging any device that supports a network SSH connection. 
"-a" is used to specify the IP address.
"-u" is used to specify the username.
"-P" is the user's password.
"-q" can specify the port. 
The default is "22".
"-s" will enable symlink traversal and "-d" is used to specify a directory to image. 

**-a IP**, **--address IP**
: IP address to connect to.

**-u USERNAME**, **--username USERNAME**
: SSH username to connect with.

**-P PASSWORD**, **--password PASSWORD**
: Password for the SSH user.

**--port PORT**
: Port to connect over SSH.

**-s**, **--symlinks**
: Follow and image any symlinks.

**-r**, **--recursive**
: Add files and folders recursively.

**-d REMOTE DIR**, **--directory REMOTE DIR**
: Remote directory to begin imaging.

# Generic_FTP Plugin
The "generic_ftp" plugin is used for imaging any device that supports a network FTP connection. 
"-a" is used to specify the hostname or IP address.
"-u" is used to specify the username.
"-P" is the user's password.
"-q" can specify the port. 
The default is "21".
"-s" will enable symlink traversal and "-d" is used to specify a directory to image. 

**-a IP**, **--address IP**
: IP address  or server name to connect to.

**-u USERNAME**, **--username USERNAME**
: FTP username to connect with.

**-P PASSWORD**, **--password PASSWORD**
: Password for the FTP user.

**--port PORT**
: Port to connect over FTP.

**-s**, **--symlinks**
: Follow and image any symlinks.

**-r**, **--recursive**
: Add files and folders recursively.

**-d REMOTE_DIR**, **--directory REMOTE_DIR**
: Remote directory to begin imaging.

# USB_Drive Plugin
The "usb_drive" image is used for imaging a USB drive.
Simply add the flash drive name with "-u".

**-u USB_NAME**, **--usb USB_NAME**
: Create image from a connected USB device.

**-s**, **--symlinks**
: Follow and image any symlinks.

**--timeout**
: FTP connection timeout.

# Disk_Image Plugin
The "disk_image" plugin is used to image files or folders on a disk. 
"-f" is used to specify a folder.
"-F" is used to specify a file. 
And again, "-s" is used enable symlink traversal. 

**-f [FOLDER [FOLDER ...]]**, **--folder [FOLDER [FOLDER ...]]**
: Create image from a local folder.

**-F [FILE [FILE ...]]**, **--file [FILE [FILE ...]]**
: Create image from a local file or files.

**-s**, **--symlinks**
: Follow and image any symlinks.

**-r**, **--recursive**
: Add files and folders recursively.

# Generic_SMB Plugin
The "generic_smb" plugin is used for imaging SMB shares across systems.
"-a" is used to specify the hostname/address for the share.
"-u" is the username and "-P" is the password. 
The port can also be specified to a non-standard SMB port with "-p".
Symlinks can also be traversed with "-s". 
"-S" is used to specify the share directory to image. 

**-a HOSTNAME**, **--address HOSTNAME**
: IP address  or server name to connect to.

**-S SHARE**, **--share SHARE**
: SMB share for imaging.

**-u USERNAME**, **--username USERNAME**
: SMB username to connect with.

**-P PASSWORD**, **--password PASSWORD**
: Password for the SMB user.

**--port PORT**
: Port to connect over SMB.

**-s**, **--symlinks**
: Enable traversing symlinks.

**-r**, **--recursive**
: Add files and folders recursively.

# Generic_HTTP Plugin
The "generic_http" plugin is used for imaging HTTP directories.
"-l" is used to specify the link or link(s) to image from.
"-c" is used to specify the chunk size for the downloads. 
"-r" applies to this module if you want to image all the HTTP directories. 

**-l [LINK [LINK ...]]**, **--link [LINK [LINK ...]]**
: Create image from a link.

**-c [CHUNK_SIZE [CHUNK_SIZE ...]]**, **--chunk-size [CHUNK_SIZE [CHUNK_SIZE ...]]**
: Chunk size to download with. Default is 1024.

**-r**, **--recursive**
: Add files and folders recursively.

# EXAMPLES

**afflux -p disk_image -f /home -o home.aff4**
: Create an image ("home.aff4") of the "/home" directory on a Linux system.

**afflux -p android_adb -a 10.11.1.5:5001 --root -d / /dev- /proc- -o test.aff4 -v**
: Verbosely image an Android phone ("10.11.1.5") over the network to "test.aff4". Attempt to get root access, start imaging at "/" and ignore "/dev" and "/proc".

**afflux -p ios_ssh -a 10.11.1.7 -o iphone_ssh.aff4**
: Image a jailbroken iPhone ("10.11.1.7") via SSH.

**afflux -p generic_smb -a WINDEV2210EVAL -S \Users\User\Desktop\shared_folder -o test.aff4 -v -u User -P test**
: Image an SMB share on a Windows machine. 

# COPYRIGHT
Copyright 2020 Andrew Clark. License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>. This is free software: you are free to change and redistribute it. There is NO WARRANTY, to the extent permitted by law.