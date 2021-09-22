import os
import sys
import ctypes
from urllib import request, error
import string
from ctypes import windll
import tkinter
from tkinter.font import Font
import time
import re
import win32file
import shutil
from sys import exit


def install_cros_tools():
    print(os.popen("bash -c \"sudo apt update\"").read())
    print(os.popen("bash -c \"sudo apt install -y pv tar cgpt\"").read())


def ps_check_feature(feature):
    """Checks whether a Windows optional feature exists.
    Returns True if the component is installed. Otherwise returns False.
    Requires admin permissions."""
    _ = os.popen("powershell \"Get-WindowsOptionalFeature -FeatureName {} -Online\"".format(feature)).read().replace(
        " ", "")
    if "State:Disabled" in _:
        return False
    elif "State:Enabled" in _:
        return True
    else:
        return False


def is_wsl_framework_installed():
    """Checks if the WSL framework (excluding distros) is installed."""
    return ps_check_feature("Microsoft-Windows-Subsystem-Linux") and ps_check_feature(
        "VirtualMachinePlatform") and shutil.which("bash") and shutil.which("wsl")


def download_brunch():
    """
    Checks if brunch has already been downloaded, using the .txt file. Otherwise downloads the file.
    After that unpacks the file.
    :return:
    """
    # this file's structure is close to a dictionary. The simplest approach is to change the case of the booleans and
    # replace null with None.
    # this approach breaks any filenames with "true", "null", or "false".
    # although almost no one will use such filenames, any files with these substrings will break.
    # NEED TO find a better approach to make Python accept this dictionary.
    brunch_conf = os.popen("curl https://api.github.com/repos/sebanc/brunch/releases/latest").read(). \
        replace("false", "False").replace("null", "None").replace('true', "True")
    brunch_config = eval(brunch_conf)
    to_download = brunch_config["assets"][0]["browser_download_url"]
    file_to_download = os.path.basename(to_download)
    if not os.path.exists(f".\\TEMP\\{file_to_download}.downloaded"):  # a stub file
        download_url(to_download, ".\\TEMP")
        with open(f".\\TEMP\\{file_to_download}.downloaded", "w") as file:
            print(file=file)
    else:
        print(f'{file_to_download} has already been downloaded')
    shutil.unpack_archive(f".\\TEMP\\{file_to_download}", f'.\\TEMP\\Brunch', "gztar")


def download_recovery(recovery_name, recovery_list):
    """
    Using the recovery list provided, downloads a Chrome OS recovery image. If it already exists with a stub, skips.
    After that, unpacks the file. Filename will be returned to pass into the install command.
    :param recovery_name:
    :param recovery_list:
    :return:
    """
    to_download = recovery_list[recovery_name]
    file_to_download = os.path.basename(to_download)
    if not os.path.exists(f".\\TEMP\\{file_to_download}.downloaded"):
        download_url(to_download, ".\\TEMP")
        with open(f".\\TEMP\\{file_to_download}.downloaded", "w") as file:
            print(file=file)
    else:
        print(f'{file_to_download} has already been downloaded')
    shutil.unpack_archive(f".\\TEMP\\{file_to_download}", f'.\\TEMP\\ChromeOS', "zip")
    return file_to_download  # this will be used later


def suggest_recoveries_intel_core(cpu_gen):
    """Given the CPU generation of a Intel Core i*-**** chip, suggests the Chrome OS recovery."""
    if cpu_gen <= 10:
        return ["rammus", "hatch", "octopus", "nami", "hana", "fizz", "coral", "samus"]
    else:
        return ["volteer"]


def suggest_recoveries_intel_other():
    return ["rammus", "hatch", "octopus", "nami", "hana", "fizz", "coral", "volteer", "samus"]


def suggest_recoveries_amd_ryzen():
    return ["zork"]


def suggest_recoveries_amd_other():
    return ["grunt"]


def update_grub2win_config(disk, kern, p_tracker, ap_tracker, bt_tracker):
    """
    Updates the grub2win configuration for Chrome OS. The tracker's values must be IntVars.
    :param disk: Disk to use
    :param kern: Linux kernel version
    :param p_tracker: Dictionary containing all the parameters in IntVar
    :param ap_tracker: Similar
    :param bt_tracker: Similar
    :return:
    """
    # STEP 1: Generates the menu entry and headers
    parameters = {k: v.get() for k, v in p_tracker.items()}
    advanced_parameters = {k: v.get() for k, v in ap_tracker.items()}
    basic_toggles = {k: v.get() for k, v in bt_tracker.items()}
    disk_long_uuid = win32file.GetVolumeNameForVolumeMountPoint("{}:\\".format(disk))
    # print(disk_long_uuid)
    img_uuid = re.split("[{}]", disk_long_uuid)[1].upper()
    # print(parameters)
    # print(advanced_parameters)
    # print(basic_toggles)
    parameters_string = ",".join(k for k in parameters if parameters[k] == 1)
    advanced_parameters_string = " ".join(f'{k}={v}' for k, v in advanced_parameters.items())
    basic_toggles_string = " ".join(k for k in basic_toggles if basic_toggles[k] == 1)
    grub_lines = [
        f'img_uuid={img_uuid}',
        "img_path=/ChromeOS/ChromeOS.img",
        "search --no-floppy --set=root --file $img_path",
        "loopback loop $img_path",
        f"linux (loop,7)/kernel-{kern} boot=local noresume noswap loglevel=7 disablevmx=off \\",
        f'cros_secure {basic_toggles_string} {advanced_parameters_string} options={parameters_string} '
        f'loop.max_part=16 img_uuid=$img_uuid img_path=$img_path',
        'initrd (loop,7)/lib/firmware/amd-ucode.img (loop,7)/lib/firmware/intel-ucode.img (loop,7)/initramfs.img',
    ]
    grub_output = "\n".join(grub_lines)
    grub_redirect = """menuentry 'Google Chrome OS'  --class custom  --class icon-android {
    source $prefix/ChromeOS/chromeos.cfg
    }"""
    new_user_section = """# start-grub2win-user-section   ********************************************************
#
{}
#
# end-grub2win-user-section     ********************************************************""".format(grub_redirect)
    user_section_start_full_syntax = "# start-grub2win-user-section   **********************************************" \
                                     "**********\n#"
    user_section_start = "# start-grub2win-user-section"
    user_section_end = "# end-grub2win-user-section"
    # STEP 2: Add a temporary entry to grub.cfg if not existing
    with open("C:\\grub2\\grub.cfg", "r") as grub_file:
        grub_file_temp = grub_file.read()
    if grub_redirect in grub_file_temp:
        grub_file_new = grub_file_temp  # no changes
    elif user_section_end in grub_file_temp and user_section_start in grub_file_temp:
        grub_file_new = grub_file_temp.replace(user_section_start_full_syntax,
                                               user_section_start_full_syntax + "\n\n" + grub_redirect + "\n\n")
    else:
        grub_file_new = grub_file_temp + "\n\n" + new_user_section + "\n\n"
    while "\n\n" in grub_file_new:
        grub_file_new = grub_file_new.replace("\n\n", "\n")  # replaces empty newlines
    with open("C:\\grub2\\grub.cfg", "w") as grub_file:
        print(grub_file_new, file=grub_file)
    # STEP 3: Add a permanent entry to the usersection.cfg file if not existing
    if not os.path.exists("C:\\grub2\\userfiles\\usersection.cfg"):
        with open("C:\\grub2\\userfiles\\usersection.cfg", "w") as usercfg_file:
            print(file=usercfg_file)
    with open("C:\\grub2\\userfiles\\usersection.cfg", "r") as usercfg_file:
        usercfg_file_temp = usercfg_file.read()
    if grub_redirect in usercfg_file_temp:
        usercfg_file_new = usercfg_file_temp
    else:
        usercfg_file_new = usercfg_file_temp + "\n\n" + grub_redirect + "\n\n"
    while "\n\n" in usercfg_file_new:
        usercfg_file_new = usercfg_file_new.replace("\n\n", "\n")  # replaces empty newlines
    with open("C:\\grub2\\userfiles\\usersection.cfg", "w") as usercfg_file:
        print(usercfg_file_new, file=usercfg_file)
    # STEP 4: add/overwrite boot instructions.
    os.makedirs("C:\\grub2\\ChromeOS", exist_ok=True)
    with open("C:\\grub2\\ChromeOS\\chromeos.cfg", "w") as chromeos_cfg:
        print(grub_output, file=chromeos_cfg)


def is_admin():
    """
    Checks if the user has admin permissions
    :return: admin true/false
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        return False


def download_url(url, root, filename=None):
    """Download a file from a url and place it in root.
    Args:
        url (str): URL to download file from
        root (str): Directory to place downloaded file in
        filename (str, optional): Name to save the file under. If None, use the basename of the URL
    """

    root = os.path.expanduser(root)
    if not filename:
        filename = os.path.basename(url)
    fpath = os.path.join(root, filename)

    os.makedirs(root, exist_ok=True)

    try:
        print('Downloading ' + url + ' to ' + fpath)
        request.urlretrieve(url, fpath)
    except (error.URLError, IOError):
        if url[:5] == 'https':
            url = url.replace('https:', 'http:')
            print('Failed download. Trying https -> http instead.'
                  ' Downloading ' + url + ' to ' + fpath)
            request.urlretrieve(url, fpath)


def get_cpu():
    """
    Returns CPU name of the PC
    :return:
    """
    cpu_name = os.popen("wmic cpu get name").readlines()[2]
    return cpu_name


def get_admin_permission():
    """checks if the program has admin permissions, otherwise it requests admin permission once, then exits"""
    if is_admin():
        pass
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        exit()


def get_drives():
    """
    Returns the name of all Windows disk drives
    :return:
    """
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives


def install_wsl():
    """Installs WSL and its dependencies, then reboots. Requires admin permission."""
    if is_admin():
        print(os.popen(
            "dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart").read())
        print(os.popen("dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart").read())
        os.popen("shutdown.exe /r /t 0")


def get_recoveries():
    download_url("https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.conf", ".\\TEMP")
    with open(".\\TEMP\\recovery.conf") as recovery_file:
        lines = recovery_file.read()
        lines = re.split("\n\n", lines)
        result = {}
        # print(lines)
        for entry in lines:
            variables = entry.split("\n")
            filename = None
            url_name = None
            for variable in variables:
                if "file=" in variable:
                    filename = re.split("_", variable.strip("file="))[2]
                if "url=" in variable:
                    url_name = variable.strip("url=")
            if filename and url_name:
                result[filename] = url_name
    return result


def strip_suffix_intel_cpu(model):
    """Returns the Intel CPU generation along with its suffix.
    In case there is no lettered suffix, returns the CPU gen only."""
    if model.isnumeric():
        return model, ""
    ___ = 0
    for _, __ in enumerate(reversed(model)):
        # print(_, __)
        if __.isalpha():
            ___ = 1
        if __.isnumeric() and ___ == 1:
            return model[:-_], model[-_:]


def get_cpu_generation_intel(cpu_name):
    """Gets Intel CPU suffix and generation."""
    cpu_model = cpu_name.split()[2].split("-")[1]
    cpu_gen, suffix = strip_suffix_intel_cpu(cpu_model)
    cpu_gen = cpu_gen[:-3]
    return cpu_gen, suffix


class WindowError(tkinter.Tk):
    """
    A window displaying errors. May not be polished yet. Especially the quit() and destroy() not working properly.
    """

    def __init__(self, *messages, color="red", tx_color="white", yes_command="", yes_text="OK", no_text="Dismiss"):
        """
        Creates the windows. Mainloop needed after initializing
        :param messages: All the messages. Separate the strings to make a line break
        :param color: Background color
        :param tx_color: Text color
        :param yes_command: Executes this command in a string.
        :param yes_text: The label of the button.
        """
        super().__init__()
        self.title("Install Chrome OS")
        self.geometry("640x240")
        self.minsize(height=240, width=640)
        self.maxsize(height=240, width=640)
        self.config(padx=8, pady=8, background=color)
        row_weight = 10000, 1
        for _, __ in enumerate(row_weight):
            self.rowconfigure(_, weight=__)
        column_weight = 100, 1
        for _, __ in enumerate(column_weight):
            self.columnconfigure(_, weight=__)
        error_frame = tkinter.Frame(self, background=color)
        error_frame.grid(row=0, column=0, sticky="new", columnspan=2)
        for message in messages:
            tkinter.Label(error_frame, text=message, font=Font(family="Arial", size=12), background=color,
                          fg=tx_color, wraplength=600, justify="left").pack(side="top", anchor="nw")
        if yes_command:
            button_accept = tkinter.Button(self, relief="raised", text=yes_text, command=self.accept_button_function)
            self.yes_command = yes_command
            button_accept.grid(row=1, column=0, sticky="e")
        button_exit = tkinter.Button(self, relief="raised", text=no_text, command=self.destroy)
        button_exit.grid(row=1, column=1, sticky="e")

    def accept_button_function(self):
        # self.quit()
        self.destroy()
        exec(f'{self.yes_command}')


def wsl_get_distro():
    """
    Returns the output of "wsl.exe --list"
    :return:
    """
    __ = os.popen("wsl --list").readlines()
    result = (_.replace("\x00", "") for _ in __)
    result = "".join(_ for _ in result if _ != "\n" and _ != "")
    return result.casefold()


def is_linux_enabled(distro):
    """
    Checks if WSL distro is installed. If not, tries to install distro.
     If WSL isn't present, prompts to install WSL and its prerequisites.
    :param distro:
    :return: TRUE if the specified WSL distro has already been installed.
    LINUX_INSTALLED if WSL is present but the distro is not.
    WSL_NOT_INSTALLED if WSL is not present.
    """
    if not is_wsl_framework_installed():
        _ = WindowError("WSL is not installed. To install Google Chrome OS, please install WSL first.",
                        "Please save your work before clicking install. The machine will reboot.",
                        yes_text="Install WSL",
                        yes_command="install_wsl()")
        _.mainloop()
        exit()
    wsl_list_header = "windows subsystem for linux distributions"
    wsl_no_distributions = "no installed distributions"
    result = wsl_get_distro()
    if distro in result and wsl_list_header in result:  # checks if distro has been installed. Done
        os.popen("wsl -s {}".format(distro))
        return "TRUE"
    elif wsl_no_distributions in result or distro not in result and wsl_list_header in result:
        # checks if there is no distribution, or the distribution is not present
        print("An instance of {} is being installed on your device. Please wait.".format(distro))
        os.popen("wsl --install -d {}".format(distro)).readlines()
        # execution of the last line stops, but installation hasn't been completed. therefore must check again.
        while True:  # check again for the presence of the OS before exiting
            time.sleep(2)
            result = wsl_get_distro()
            # print(result)
            if distro in result and wsl_list_header in result:
                os.popen("wsl -s {}".format(distro))
                break
        return "LINUX_INSTALLED"


def test_systemdrive(_):
    """Detect if the partition is the Windows system partition,
    then warns the user that the program will disable hibernation.
    If the user choose not to disable hibernation, quits the program."""
    if f'{_}:' == os.getenv("systemdrive"):
        __ = WindowError("Warning!",
                         "You chose to install on the Windows partition."
                         " Fast Startup can render the system image read only and cause errors to the programs. "
                         "Click \"Dismiss\" to continue and disable hibernation on Windows,"
                         " otherwise click \"Exit\" to abort the install.",
                         yes_text="Exit", yes_command="exit()", color="yellow", tx_color="black")
        __.mainloop()
        if is_admin():
            os.popen("powercfg /h off")
        else:
            sys.exit()


def install_grub2win():
    """Installs grub2win in the background to C:. The update code updates the grub2win's usersection"""
    if not os.path.exists("C:\\grub2\\g2bootmgr") or not os.path.exists("C:\\grub2\\winsource"):
        if not os.path.exists("grub2win.zip"):
            _ = WindowError(
                "The installation cannot complete successfully. Grub2Win bootloader .zip archive is missing.",
                "You can remove the installation .img file, or install Grub2Win manually.")
            _.mainloop()
            exit()
        else:
            shutil.unpack_archive("grub2win.zip", ".\\TEMP", "zip")
            print(os.popen(".\\TEMP\\install\\winsource\\grub2win.exe AutoInstall Quiet").read())
