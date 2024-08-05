# AFFLUX

Afflux is an [AFF4](https://www2.aff4.org/) (Advanced Forensics File Format 4) logical imager designed to create forensic images of modern devices when a physical image may not be practical or possible. It is a versatile tool written in [Python](https://www.python.org/), allowing digital forensics professionals to easily modify and scale the tool to suit their specific needs and applications. Afflux offers both command-line interface (CLI) and graphical user interface (GUI) options, making it suitable for a wide range of digital forensic investigations. It may be useful for imaging devices and data sources that use various communication protocols, such as IoT devices, mobile devices, ICS systems, network shares, and even DVRs, where traditional physical imaging methods may not be feasible.

## Key Features:
- [x] USB Support
- [x] iOS Support
- [x] Android Support
- [x] SSH support
- [x] Hard drive support
- [x] FTP support
- [x] SMB support
- [X] HTTP (limited)
- [X] Apple Watches
- [X] Properly threaded GUI
- [ ] ~~Android Watches~~ (coming soon)

## Plugins

Afflux currently includes six (6) default plugins. 
Plugins are stored in `/plugins` and can be listed with `python3 afflux.py -p list`.

```
[+] Plugins:

android_adb 	| Image an Android device via ADB over USB or over network. Supports root filesystems.
apple_afc 	| Image a device that support AFC. Supports jailbroken and non-jailbroken devices.
disk_image 	| Image a file or folder on the local disk.
generic_ftp 	| Image a device via network FTP
generic_http 	| Image a file or folder via http.
generic_smb 	| Image a device via network SMB
generic_ssh 	| Image a device via network SSH
ios_ssh 	| Image a jailbroken device via SSH over network or USB.
usb_drive 	| Image a local USB device or mounted drive.
```

## Afflux Options

Afflux supports several optional arguments, no matter which plugin is selected. 
These are shown with `python3 afflux.py -h` and are also shown with each plugin's `-h` argument.

```
optional arguments:
  -h, --help            print help output.
  -v, --verbose         enable verbose output.
  -t PATH, --temp PATH  directory to create any temporary files.
  -A, --append          append to an existing AFF4 image specified with `-o`.
  -e PASSWORD, --container_password PASSWORD
                        password to create an encrypted AFF4 container.
  -o OUTPUT_FILE, --output OUTPUT_FILE
                        output AFF4 file name.
  --overwrite           overwrite AFF4 file if it already exists.
  -m AFF4_IMAGE, --meta AFF4_IMAGE
                        print the AFF4 image's metadata.
  -p PLUGIN_NAME, --plugin PLUGIN_NAME
                        specify a plugin to load, or use "list" to list all plugins.
  -z, --zip             write to a Zip container instead of AFF4.
  -x AFF4_IMAGE, --extract AFF4_IMAGE
                        extract all files and folders from an AFF4 image.
```

## Plugin Options

### Apple_AFC Plugin

The `apple_afc` plugin allows for creating logical images from Apple devices using the AFC protocol. 
The iPod Touch, iPhone, and Apple Watch are supported. 
`-i` is used to specify `AFC` for non-jailbroken devices or `AFC2` for jailbroken devices with `Apple File Conduit 2` installed.
`-c` is used to remove all previous pairing records and `-k` is used to initiate pairing before imaging.

```
  -i METHOD, --iOS METHOD
                        create an image from an iOS device using METHOD. Jailbroken methods: AFC, AFC2. Unjailbroken method: AFC.
  -c, --clear           clear any pairing records made by Afflux.
  -k, --pair            pair or re-pair the device before imaging.
```

### iOS_SSH Plugin

The `ios_ssh` plugin is used to image a Jailbroken device via SSH protocol. 
`-a` is used to specify the devices IP address to connect to or `-l` is used for a device connected via USB.
`-R` is used to specify the root password if it is known, default is `alpine`. 
`-s` is used to enable traversing symlinks.

```
  -a IP, --address IP   IP address to connect to.
  -d REMOTE DIR, --directory REMOTE DIR
                        Remote directory to begin imaging.
  -l, --local           SSH to iOS device via network address instead of USB tunneling.
  -R ROOT_PASSWORD, --root-password ROOT_PASSWORD
                        root password for jailbroken device if using SSH. 
                        Defaults to 'alpine'.
  -s, --symlinks        follow and image any symlinks.
```

### Android_ADB Plugin

The `android_adb` plugin allows for imaging an Android device over the ADB protocol. 
`-a` is used to specify the `IP:PORT` of the device if it is on the network or `USB` if it is connected via USB. 
`-d` is used to specify the directory to image. 
Default directory is `/`.
Directories that should be ignored can be specified here by placing a `-` after the directory to ignore. 
For example, to image `/` and ignore `/proc` you would use `-d / /proc-`.
`-s` is used to enable the imaging to traverse symlinks. 
And `-k` is used to pair or repair the device.

```
  -a USB/IP:PORT, --android USB/IP:PORT
                        create an image from a connected Android device using ADB. Method can be USB or via IP.
  -d [DIRECTORY [DIRECTORY ...]], --directory [DIRECTORY [DIRECTORY ...]]
                        Directory to image on the device.
  -s, --symlinks        follow and image any symlinks.
  --root                check and acquire root privileges if possible.
  -k, --keygen          regenerate pairing keys for the device.
  --timeout TIMEOUT     ADB timeout.
```

### Generic_SSH

The `generic_ssh` plugin is used for imaging any device that supports a network SSH connection. 
`-a` is used to specify the IP address.
`-u` is used to specify the username.
`-P` is the user's password.
`-q` can specify the port. 
The default is `22`.
`-s` will enable symlink traversal and `-d` is used to specify a directory to image. 

```
  -a IP, --address IP   IP address to connect to.
  -u USERNAME, --username USERNAME
                        SSH username to connect with.
  -P PASSWORD, --password PASSWORD
                        password for the SSH user.
  --port PORT  port to connect over SSH.
  -s, --symlinks        follow and image any symlinks.
  -r, --recursive       add files and folders recursively.
  -d REMOTE DIR, --directory REMOTE DIR
                        Remote directory to begin imaging.
```

### Generic_FTP

The `generic_ftp` plugin is used for imaging any device that supports a network FTP connection. 
`-a` is used to specify the hostname or IP address.
`-u` is used to specify the username.
`-P` is the user's password.
`-q` can specify the port. 
The default is `21`.
`-s` will enable symlink traversal and `-d` is used to specify a directory to image. 

```
  -a IP, --address IP   IP address  or server name to connect to.
  -u USERNAME, --username USERNAME
                        FTP username to connect with.
  -P PASSWORD, --password PASSWORD
                        password for the FTP user.
  --port PORT  port to connect over FTP.
  -s, --symlinks        follow and image any symlinks.
  -r, --recursive       add files and folders recursively.
  -d REMOTE DIR, --directory REMOTE DIR
                        Remote directory to begin imaging.
  --timeout TIMEOUT     FTP connection timeout.
```

### USB_Drive

The `usb_drive` image is used for imaging a USB drive.
Simply add the flash drive name with `-u`.

```
  -u USB NAME, --usb USB NAME
                        create image from a connected USB device.
  -s, --symlinks        follow and image any symlinks.
```

### Disk_Image

The `disk_image` plugin is used to image files or folders on a disk. 
`-f` is used to specify a folder.
`-F` is used to specify a file. 
And again, `-s` is used enable symlink traversal. 

```
  -f [FOLDER [FOLDER ...]], --folder [FOLDER [FOLDER ...]]
                        create image from a local folder.
  -F [FILE [FILE ...]], --file [FILE [FILE ...]]
                        create image from a local file or files.
  -s, --symlinks        follow and image any symlinks.
```

### Generic_SMB

The `generic_smb` plugin is used for imaging SMB shares across systems.
`-a` is used to specify the hostname/address for the share.
`-u` is the username and `-P` is the password. 
The port can also be specified to a non-standard SMB port with `-p`.
Symlinks can also be traversed with `-s`. 
`-S` is used to specify the share directory to image. 

```
  -a HOSTNAME, --address HOSTNAME
                        IP address  or server name to connect to.
  -S SHARE, --share SHARE
                        SMB share for imaging.
  -u USERNAME, --username USERNAME
                        SMB username to connect with.
  -P PASSWORD, --password PASSWORD
                        password for the SMB user.
  --port PORT           port to connect over SMB.
  -s, --symlinks        Enable traversing symlinks.
  -r, --recursive       add files and folders recursively.
```

### Generic_HTTP

The `generic_http` plugin is used for imaging HTTP directories.
`-l` is used to specify the link or link(s) to image from.
`-c` is used to specify the chunk size for the downloads. 
`-r` applies to this module if you want to image all the HTTP directories. 

```
  -l [LINK [LINK ...]], --link [LINK [LINK ...]]
                        create image from a link.
  -c [CHUNK_SIZE [CHUNK_SIZE ...]], --chunk-size [CHUNK_SIZE [CHUNK_SIZE ...]]
                        chunk size to download with. Default is 1024.
  -r, --recursive       add files and folders recursively.
```

## Usage Examples

Verbosely image an Android device (`10.11.1.5`) over the network to `test.aff4`. 
Attempt to get root access, start imaging at `/` and ignore `/dev` and `/proc`. 

```
python3 afflux.py -p android_adb -a 10.11.1.5:5001 --root -d / /dev- /proc- -o test.aff4 -v
```

Create an image (`home.aff4`) of the `/home` directory on a Linux system.

```
python3 afflux.py -p disk_image -f /home -o home.aff4
```

Image a jailbroken iPhone (`10.11.1.7`) via SSH.

```
python3 afflux.py -p ios_ssh -a 10.11.1.7 -o iphone_ssh.aff4
```

Image an SMB share on a Windows machine. 

```
python3 afflux.py -p generic_smb -a WINDEV2210EVAL -S \Users\User\Desktop\shared_folder -o test.aff4 -v -u User -P test
```
Verbosely image the sdcard `/sdcard` within an Android device `(via ADB)` to `test.aff4` using the afflux standalone windows executable.
```
afflux_windows.exe -p android_adb -a USB -d /sdcard -o test.aff4 -v
```
## Pre-built Executables

Portable pre-built executables can be found on the [Releases]([https://github.com/MarshallUCyber/afflux/releases/tag/Alpha])
page for Windows, Mac (Intel), and Linux.
`pyinstaller` is required to build the executables. 
If you want to build them yourself, build scripts can be found in the respective system folders: `/windows_executable`,
`mac_os_executable`, and `linux_executable`.

**Note**, if using the prebuilt executables on Linux, you may need to install `libffi` in order to run them. 

## Installing

If you want to not use the pre-built executables, there are some scripts for installing the dependencies.
First, you need to clone the repo with `git clone [REPO] --recursive`.

### Windows

If you have a different version of Python other than `3.11`, you'll need to download the appropriate snappy wheel
for your Python version from 
[here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-snappy).
Place it in the `windows_executable`, directory then, in `install_windows.bat` modify the filename on line `13` to fit 
your file. 
Then simply run `install_windows.bat`.

### Linux/MacOS

Install Python 3 and run `install_linux.sh`.

## GUI Modifications

The GUI is designed with `Qt Designer 5` and exists in the `gui/afflux.ui` file. 
If you change the layout, text, or colors of the GUI, run `pyuic5 gui/afflux.ui -o gui/afflux_gui_ui.py` to create the 
Python code.

## Building Executables

Ensure all the modules are installed with `pip install -r requirements.txt` on Linux/Mac or 
`pip install -r requirements_windows.txt` on Windows.
Then, run `pip install pyinstaller`. 
Build scripts are located in folders for respective systems: `windows_executable`, `linux_executable`, and
`mac_os_executable`.
Run the bash or batch script to build the GUI or command line tools.

## Building Man Page

Requires Pandoc. 

    pandoc afflux.1.md -s -t man -o afflux.1
    sudo mkdir /usr/local/man/man1
    sudo cp afflux.1 /usr/local/man/man1
    sudo gzip /usr/local/man/man1/afflux.1 -f
    sudo mandb

## About 

### About AFF4

AFF4 is an open, extensible file format for storing and sharing of digital evidence, arbitrary case-related information, and forensic workflow. It was introduced in the paper ["Extending the advanced forensic format to accommodate multiple data sources, logical evidence, arbitrary information and forensic workflow"](https://www.sciencedirect.com/science/article/pii/S1742287609000401) by Michael Cohen, Simson Garfinkel, and Bradley Schatz (Digital Investigation 6, 2009, S57–S68).

Key features of AFF4 include:

- Ability to store multiple heterogeneous data types, including data from multiple storage devices, network packets, memory images, extracted logical evidence, and forensic workflow.
- Improved separation between the underlying storage mechanism and forensic software that uses the evidence.
- Support for storing evidence in a single file, multiple files, a relational database, or an object management system.
- Backwards compatibility with the earlier AFF format.

AFF4 introduces several key concepts:

- **AFF4 Objects**: The basic building blocks, identified by unique URNs.
- **Relations**: Factual statements describing relationships between AFF4 Objects or their properties.
- **Volumes**: Responsible for providing storage to AFF4 segments.
- **Streams**: Provide the ability to seek and read data, and implement abstracted storage.
- **Segments**: Single units of data written to a volume.
- **References**: Allow objects to refer to other objects using URIs or URLs.
- **Universal Resolver**: Collects and resolves attributes for different AFF4 Objects.

### CASE Support

Afflux supports the [Cyber-investigation Analysis Standard Expression (CASE)](https://https://caseontology.org/) Ontology standard. CASE is a community-developed evolving standard that provides a structured (ontology-based) specification for representing information commonly analyzed and exchanged by people and systems during investigations involving digital evidence. The power of CASE is that it provides a common language to support automated normalization, combination and validation of varied information sources to facilitate analysis and exploration of investigative questions (who, when, how long, where). In addition to representing tool results, CASE ensures that analysis results can be traced back to their source(s), keeping track of when, where and who used which tools to perform investigative actions on data sources.

## Funding

Afflux was supported by funding from the [United States Secret Service National Computer Forensics Institute (NCFI)](https://ncfi.usss.gov)
