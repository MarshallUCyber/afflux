# Changelog

All notable changes to AFFLUX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-20

### Added
- Initial stable release of AFFLUX - AFF4 logical imager
- Support for multiple device types and protocols:
  - USB devices and drives
  - iOS devices (jailbroken and non-jailbroken via AFC)
  - Android devices (via ADB over USB and network)
  - SSH connections (generic and iOS-specific)
  - FTP servers
  - SMB network shares
  - HTTP downloads
  - Local disk imaging
- Complete plugin system with 9 plugins:
  - `android_adb` - Image Android devices via ADB
  - `apple_afc` - Image iOS devices via AFC protocol
  - `ios_ssh` - Image jailbroken iOS devices via SSH
  - `generic_ssh` - Image any device via SSH
  - `generic_ftp` - Image devices via FTP
  - `generic_smb` - Image SMB network shares
  - `generic_http` - Image files via HTTP
  - `disk_image` - Image local files and folders
  - `usb_drive` - Image USB drives
- Both CLI and GUI interfaces:
  - Command-line interface for scripting and automation
  - Graphical user interface with Qt5
  - Properly threaded GUI for responsive operation
  - Splash screen and custom styling (Breeze theme)
- AFF4 container features:
  - Create forensic images in AFF4 format
  - Optional ZIP container format support
  - Encrypted container support with password protection
  - Append mode to add to existing images
  - Metadata extraction and viewing
- Advanced imaging options:
  - Symlink traversal support
  - Recursive directory imaging
  - Selective directory exclusion (Android)
  - Root access support for Android devices
  - Device pairing and key management
  - Configurable timeout settings
- Cross-platform support:
  - Windows (with pre-built executables)
  - macOS Intel (with pre-built executables)
  - Linux (with pre-built executables)
- CASE ontology support for cyber investigation standards
- Comprehensive documentation including man page

### Fixed
- Fixed PyInstaller executable configurations for all platforms
- Fixed missing plugin inclusion (ios_ssh.py and generic_http.py)
- Fixed missing GUI module dependencies in executables
- Fixed missing hidden imports causing runtime errors
- Fixed splash screen configuration for macOS GUI
- Fixed platform-specific icon references
- Fixed wildcard plugin imports replaced with explicit references
- Zip functionality in GUI properly working
- Android keygen option added to GUI

### Changed
- Improved executable build reliability across platforms
- Enhanced GUI threading for better responsiveness
- Updated requirements and dependencies

### Documentation
- Comprehensive README with plugin documentation
- Usage examples for all major use cases
- Installation instructions for Windows, Linux, and macOS
- Man page documentation (afflux.1)
- Build instructions for creating executables

### Technical Details
- Built with Python 3
- Uses PyQt5 for GUI interface
- Leverages PyInstaller for cross-platform executables
- Implements AFF4 (Advanced Forensics File Format 4)
- Modular plugin architecture for extensibility

---

## Release Notes

This is the first stable release of AFFLUX, a versatile AFF4 logical imager designed for modern forensic imaging needs. AFFLUX enables forensic professionals to create logical images of devices where physical imaging may not be practical, including IoT devices, mobile devices, network shares, and cloud storage.

### Supported Devices and Protocols
- Mobile: iOS (AFC, SSH), Android (ADB)
- Network: SSH, FTP, SMB, HTTP
- Local: USB drives, disk files/folders

### Key Features
- **Multi-Protocol Support**: Image devices over USB, network, or local connections
- **Dual Interface**: Both CLI and GUI available
- **Forensically Sound**: Uses AFF4 format with encryption support
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Extensible**: Plugin-based architecture for easy customization

### Funding
This project was supported by funding from the United States Secret Service National Computer Forensics Institute (NCFI).

[1.0.0]: https://github.com/MarshallUCyber/afflux/releases/tag/v1.0.0
