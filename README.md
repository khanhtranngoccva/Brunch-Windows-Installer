# Brunch-Windows-Installer
Installs the Brunch framework to run Chrome OS on a Windows device, without having to manually install WSL or a bootloader.

Please note that this installer can only run on Windows 10 and up with UEFI boot mode and supporting WSL. Secure Boot must be disabled to run the software.

(Sure there are ways to install GRUB without having to turn this off, but all of this can't be run on NTFS, which means that partitioning is a must in all these cases.)

(Learn more about the problem here https://github.com/pbatard/uefi-ntfs)


This installer will not affect any partitions or data.

Due to the nature of the installer (read below), please disable Windows Defender before executing.


This installer does the following:
1. Examines system compatibility with Brunch.
2. Prompts the user, then installs the WSL framework if it is not installed and reboots if the user agrees.
3. Installs Debian WSL if it is not installed, then set this distro as default.
4. Suggests recoveries based on CPU.
5. Launches a GUI interface. The user can choose boot parameters, kernel, installation size and builds.
6. Installs all prerequisites and builds the Chrome OS system image using downloaded files from GitHub and Google's servers.
7. Installs Grub2Win and automatically adds an entry to the user section.

After installation, the user can relaunch this installer to:
1. Reinstall using specified parameters on the same disk, options to swap builds available.
2. Update the framework settings.
3. Uninstalls the Chrome OS image. (the user can remove Grub2Win with Windows' program manager)

Possible bugs: For users, none at the moment, report bugs on https://t.me/chromeosforpc.

Intel Core m3 CPUs are not yet added into the compatibility check.
Fixed in source code, but not yet compiled.

For contributors, the function stops when an error window is called. I had a workaround for the time being, but this may not be sustainable.

TODO: WSL distro checker may break. Please add a better algorithm. If you want to contribute, please ask me on Telegram. ;)
