from polished_code import *  # put the ok functions somewhere else

import os
from sys import exit
import ssd
import platform
import tkinter
from tkinter.font import Font
from os import path
from shutil import disk_usage
import traceback
import time

kernel_dict = {
    "4.19": "4.19",
    "5.4 (recommended)": "5.4",
    "5.10 (experimental)": "5.10"
}
basic_toggle_dict = {
    "console=": "Disable verbose output to console",
    "cros_debug": "Enable developer mode. Disable to use SafetyNet and Widevine L3 features. "
                  "Cannot be changed by Brunch manager."
}
basic_toggle_tracker = {"cros_debug": 1}  # select default enabled
parameter_dict = {"enable_updates": "Allow native Chrome OS updates, disable to improve build stability",
                  "pwa": "Enable updates with native Brunch manager",
                  "mount_internal_drives": "Mount all internal disks, uncheck to improve performance",
                  "ipts": "Enable touchscreen support for Surface devices",
                  "suspend_s3": "Enable S3 suspend instead of S0ix (useful for PCs)",
                  "goodix": "Improve goodix touchscreen support",
                  "invert_camera_order": "Use if your camera order is inverted",
                  "acpi_power_button": "Enable power button for some models",
                  "advanced_als": "Enable advanced automatic brightness modifications",
                  "internal_mic_fix": "Fix internal microphone on some devices",
                  "broadcom_wl": "Patches for the broadcom_wl module",
                  "iwlwifi_backport": "Patches for Intel wireless cards if they are not supported natively",
                  }
parameter_tracker = {"enable_updates": 1, "pwa": 1, "acpi_power_button": 1}
advanced_parameter_dict = {
    "enforce_hyperthreading": "Enable enforced hyperthreading, improves performance but reduces security",
    "i915.enable_fbc": "Enable Intel integrated GPU's FBC feature. Disable to use crouton for 5.4 kernel",
    "i915.enable_psr": "Enable Intel integrated GPU's PSR feature. Disable to use crouton for 5.4 kernel",
    "psmouse.elantech_smbus": "Fix some Elantech touchpads",
    "psmouse.synaptics_intertouch": "Enable multitouch gesture on some touchpads",
}
advanced_parameter_tracker = {"i915.enable_fbc": 1, "i915.enable_psr": 1}


def install_chrome_os():
    if installed_disk:
        disk_to_install = installed_disk
    else:
        try:
            disk_entry = disk_list[disk_list_box.curselection()[0]]
            disk_to_install = disk_dict[disk_entry]
            # print(recovery_name)
        except IndexError:
            _ = WindowError("Please select the drive to install.")
            _.mainloop()
            return None
    try:
        recovery_name = recoveries_list[recoveries_list_box.curselection()[0]]
    except IndexError:
        _ = WindowError("Please select the recovery build to use.")
        _.mainloop()
        return None
    native_brunch = native_settings_variable.get()
    if native_brunch:
        kernel = "5.4"  # filler for function, no effect
        print("Native Brunch manager enabled.")
    else:
        try:
            kernel_entry = kernel_list[kernel_listbox.curselection()[0]]
            kernel = kernel_dict[kernel_entry]
        except IndexError:
            _ = WindowError("Please select the kernel for the bootloader.")
            _.mainloop()
            return None
    try:
        install_size = int(size_entry.get())
    except ValueError:
        _ = WindowError("The installation size must be non-blank and an integer.")
        _.mainloop()
        return None
    if install_size < 16:
        _ = WindowError("The installation must be at least 16 GBs.")
        _.mainloop()
        return None
    inst_vol_free = int([i / 1024 ** 3 for i in disk_usage(path.realpath(f'{disk_to_install}:\\'))][2])
    if install_size + 7 > inst_vol_free:  # including downloaded files
        _ = WindowError("Not enough space for the installation. Try a smaller installation size.")
        _.mainloop()
        return None
    # print(disk_to_install)
    main_install_window.destroy()  # somehow this gets in the way with installing!
    if ssd_dict[disk_to_install] == "HDD":
        __ = WindowError("You are installing Google Chrome OS on a mechanical drive,"
                         " which is not designed to run Chrome OS.",
                         "The sign in UI will appear before the Android container and "
                         "some other components are loaded properly,"
                         " and signing in within the first 2 minutes will cause them to crash."
                         "Press 'Abort' to cancel the installation, or click 'Proceed' to continue anyway.",
                         yes_command="exit()",
                         yes_text="Abort", color="yellow", tx_color="black", no_text="Proceed")
        __.mainloop()
    test_hiberfilsys(disk_to_install)
    if unstable_variable.get():
        __ = WindowError("You're downloading unstable releases. Bugs may occur.",
                         yes_command="exit()",
                         yes_text="Abort", color="yellow", tx_color="black", no_text="Proceed")
        __.mainloop()
        download_brunch(unstable=True)
    else:
        download_brunch(unstable=False)
    image_name = download_recovery(recovery_name, all_recoveries)
    install_cros_tools()
    chromeos_dir_add = "bash -c \"sudo mkdir /mnt/{}/ChromeOS\"".format(disk_to_install.lower())
    os.popen(chromeos_dir_add)
    print("CREATING SYSTEM IMAGE NOW. DO NOT EXIT THE PROGRAM.")
    with open("install.log", "w") as f:
        print(os.popen("bash TEMP/Brunch/chromeos-install.sh -src TEMP/ChromeOS/{0} "
                       "-dst /mnt/{1}/ChromeOS/ChromeOS.img -s {2}".format(image_name.removesuffix(".zip"),
                                                                           disk_to_install.lower(),
                                                                           install_size)).read())
    install_grub2win()
    update_grub2win_config(disk_to_install, kernel, parameter_tracker, advanced_parameter_tracker, basic_toggle_tracker,
                           native_brunch)
    with open(f"{disk_to_install}:\\ChromeOS\\chromeos_installed", "w") as f:
        print(file=f)
    __ = WindowError("Google Chrome OS installed!", color="green", tx_color="white", no_text="Exit")
    __.mainloop()


def update_bootloader_button():
    native_brunch = native_settings_variable.get()
    if native_brunch:
        kernel = "5.4"  # filler
        print("Native Brunch manager enabled.")
    else:
        try:
            kernel_entry = kernel_list[kernel_listbox.curselection()[0]]
            kernel = kernel_dict[kernel_entry]
        except IndexError:
            _ = WindowError("Please select the kernel for the bootloader.")
            _.mainloop()
            return None
    disk_to_install = installed_disk
    install_grub2win()
    update_grub2win_config(disk_to_install, kernel, parameter_tracker, advanced_parameter_tracker,
                           basic_toggle_tracker, native_brunch)
    __ = WindowError("Bootloader updated!", color="green", tx_color="white")
    __.mainloop()


def uninstall_chrome_os_button():
    if os.path.exists(f"{installed_disk}:\\ChromeOS\\ChromeOS.img"):
        os.remove(f"{installed_disk}:\\ChromeOS\\ChromeOS.img")
    if os.path.exists(f"{installed_disk}:\\ChromeOS\\chromeos_installed"):
        os.remove(f"{installed_disk}:\\ChromeOS\\chromeos_installed")
    if os.path.exists("C:\\grub2\\grub.cfg"):
        with open("C:\\grub2\\grub.cfg") as f:
            grub_file_temp = f.read()
            grub_file_new = grub_file_temp.replace(
                "source $prefix/ChromeOS/chromeos.cfg", "\n")
        with open("C:\\grub2\\grub.cfg", "w") as f:
            print(grub_file_new, file=f)
    if os.path.exists("C:\\grub2\\userfiles\\usersection.cfg"):
        with open("C:\\grub2\\userfiles\\usersection.cfg") as f:
            grub_file_temp = f.read()
            grub_file_new = grub_file_temp.replace(
                "source $prefix/ChromeOS/chromeos.cfg", "\n")
        with open("C:\\grub2\\userfiles\\usersection.cfg", "w") as f:
            print(grub_file_new, file=f)
    main_install_window.destroy()
    _ = WindowError("Chrome OS has been uninstalled. You can now exit.", color="green", tx_color="white",
                    no_text="Exit")
    _.mainloop()
    exit()


try:
    if __name__ == '__main__':
        get_admin_permission()
        print("Please do not close this window while installation of Chrome OS is running.")
        if not os.path.exists("grub2win.zip"):
            _ = WindowError("Grub2Win archive is missing. The installer will now quit.")
            _.mainloop()
            exit()
        cpu = get_cpu()
        # cpu = "Intel Celeron G4500"
        recoveries_list = []
        if os.name != "nt":
            _ = WindowError("This installer can only be run on Windows 10 and up.")
            _.mainloop()
            exit()
        elif int(platform.release()) < 10:
            _ = WindowError("This installer can only be run on Windows 10 and up.")
            _.mainloop()
            exit()
        if "intel" in cpu.casefold():
            if "core" in cpu.casefold():
                if "i3" not in cpu.casefold() and "i5" not in cpu.casefold() and "i7" not in cpu.casefold() \
                        and "i9" not in cpu.casefold() and "m3" not in cpu.casefold():  # core solo or core 2 duo
                    _ = WindowError("Compatibility check failed!",
                                    "Your Intel Core CPU is too old to run Chrome OS.",
                                    "https://github.com/sebanc/brunch/wiki/CPUs-&-Recoveries",
                                    "CPU name for debugging: {}".format(cpu))
                    _.mainloop()
                    exit()
                cpu_generation, cpu_suffix = get_cpu_generation_intel(cpu)
                print('Intel Core CPU detected. CPU generation: {}, CPU suffix: {}'.format(cpu_generation, cpu_suffix))
                cpu_generation = int(cpu_generation)
                if cpu_generation == 1:  # it doesn't support properly
                    _ = WindowError("Compatibility check failed!",
                                    "Your first-generation Intel Core CPU to run Chrome OS.",
                                    "https://github.com/sebanc/brunch/wiki/CPUs-&-Recoveries",
                                    "CPU name for debugging: {}".format(cpu))
                    _.mainloop()
                    exit()
                if cpu_suffix == "F":  # suffix F => no integrated GPU
                    _ = WindowError("Compatibility check failed!",
                                    "Your Intel Core CPU doesn't have an integrated graphics card,"
                                    " and Brunch doesn't support this at the moment.",
                                    "https://github.com/sebanc/brunch/wiki/CPUs-&-Recoveries",
                                    "Please try again later!", "CPU name for debugging: {}".format(cpu))
                    _.mainloop()
                    exit()
                recoveries_list = suggest_recoveries_intel_core(cpu_generation)
            else:
                _ = WindowError(
                    "Your CPU may or may not be able to run Chrome OS, depending on its age and model. "
                    "Proceed at your own risk.",
                    "Click \"Dismiss\" to proceed. ",
                    "Visit https://github.com/sebanc/brunch/wiki/CPUs-&-Recoveries for more details.",
                    "CPU name for debugging: {}".format(cpu), color="yellow", tx_color="black", yes_text="Exit",
                    yes_command="exit()")
                _.mainloop()
                recoveries_list = suggest_recoveries_intel_other()
        elif "amd" in cpu.casefold():
            if "ryzen" in cpu.casefold():
                recoveries_list = suggest_recoveries_amd_ryzen()
            else:
                _ = WindowError(
                    "Your CPU may or may not be able to run Chrome OS, depending on its age and model."
                    " Proceed at your own risk.",
                    "Click \"Dismiss\" to proceed.",
                    "Visit https://github.com/sebanc/brunch/wiki/CPUs-&-Recoveries for more details.",
                    "CPU name for debugging: {}".format(cpu), color="yellow", tx_color="black", yes_text="Exit",
                    yes_command="exit()")
                _.mainloop()
                recoveries_list = suggest_recoveries_amd_other()
        else:  # may never be reached, because Windows may not work with anything other than team blue or red :P
            _ = WindowError("Compatibility check failed!", "We can't detect your CPU, or your CPU is unsupported.",
                            "Visit https://github.com/sebanc/brunch/wiki/CPUs-&-Recoveries for more details.",
                            "CPU name for debugging: {}".format(cpu),
                            )
            _.mainloop()
            exit()
        print(f"Linux install status: {is_linux_enabled('debian')}")
        disk_dict = {}
        ssd_dict = {}
        installed_disk = None
        for vol_name in get_drives():
            # print(vol_name)
            vol_free = int([i / 1024 ** 3 for i in disk_usage(path.realpath(f'{vol_name}:\\'))][2])
            try:
                if ssd.is_ssd(f'{vol_name}:\\'):
                    disk_dict["SSD {} {} GBs free".format(f'{vol_name}:\\', vol_free)] = vol_name
                    ssd_dict[vol_name] = "SSD"
                else:
                    disk_dict["HDD {} {} GBs free".format(f'{vol_name}:\\', vol_free)] = vol_name
                    ssd_dict[vol_name] = "HDD"
                if os.path.exists(f"{vol_name}:\\ChromeOS\\chromeos_installed"):
                    installed_disk = vol_name
            except KeyError:  # in case it's not a physical drive
                pass
        all_recoveries = get_recoveries()
        main_install_window = tkinter.Tk()
        size = 1200, 600
        main_install_window.geometry("{}x{}".format(size[0], size[1]))
        main_install_window.title("Install Chrome OS")
        main_install_window.config(padx=8, pady=8)
        row_config = 1, 1, 10000, 1
        column_config = 1, 1, 1, 10000, 1
        for index, value in enumerate(row_config):
            main_install_window.rowconfigure(index, weight=value)
        for index, value in enumerate(column_config):
            main_install_window.columnconfigure(index, weight=value)

        # OUTER FRAMES
        parameter_checkbox_frame = tkinter.Frame(main_install_window)
        parameter_checkbox_frame.grid(row=1, column=0, sticky="nw")
        other_parameter_checkbox_frame = tkinter.Frame(main_install_window)
        other_parameter_checkbox_frame.grid(row=1, column=1, sticky="nw")
        installer_list_frame = tkinter.Frame(main_install_window)
        installer_list_frame.grid(row=1, column=2, sticky="nw")
        title_frame = tkinter.Frame(main_install_window)
        title_frame.grid(row=0, column=0, columnspan=5, sticky="new")
        title_frame_column_weight = 1, 10000, 1, 1
        for index, value in enumerate(title_frame_column_weight):
            title_frame.columnconfigure(index, weight=value)
        action_buttons_frame = tkinter.Frame(main_install_window)
        action_buttons_frame.grid(row=2, column=0, columnspan=5, sticky="wes")
        # INNER FRAMES
        title1 = tkinter.Label(title_frame, text="Install Chrome OS", font=Font(family="Google Sans", size=20),
                               fg="blue", wraplength=600, justify="left")
        title1.grid(row=0, column=0, sticky="nw")
        exit_button = tkinter.Button(title_frame, text="Exit", command=exit)
        exit_button.grid(row=0, column=4, sticky="ne")
        check_frame = tkinter.LabelFrame(parameter_checkbox_frame, text="Bootloader parameters")
        check_frame.grid(row=1, column=0, sticky="new")
        advanced_check_frame = tkinter.LabelFrame(other_parameter_checkbox_frame, text="Advanced bootloader parameters")
        advanced_check_frame.grid(row=2, column=0, sticky="new")
        basic_toggle_frame = tkinter.LabelFrame(other_parameter_checkbox_frame, text="Basic toggles (bootloader)")
        basic_toggle_frame.grid(row=3, column=0, sticky="new")
        misc_frame = tkinter.LabelFrame(other_parameter_checkbox_frame, text="Miscellaneous (bootloader)")
        misc_frame.grid(row=4, column=0, sticky="new")
        unstable_frame = tkinter.LabelFrame(other_parameter_checkbox_frame, text="Bleeding edge releases")
        unstable_frame.grid(row=5, column=0, sticky="new")
        native_settings_variable = tkinter.IntVar()
        native_settings_variable.set(0)
        unstable_variable = tkinter.IntVar()
        unstable_variable.set(0)
        recoveries_frame = tkinter.LabelFrame(installer_list_frame, text="Builds", padx=4, pady=4)
        recoveries_frame.grid(row=0, column=0, sticky="new")
        recoveries_list_var = tkinter.StringVar(value=recoveries_list)  # takes in a list as well
        recoveries_list_box = tkinter.Listbox(recoveries_frame, listvariable=recoveries_list_var, exportselection=False,
                                              height=len(recoveries_list))
        recoveries_list_box.grid(row=0, column=0, sticky="new")
        size_frame = tkinter.LabelFrame(installer_list_frame, text="Install size (in GBs)", padx=4, pady=4)
        size_frame.grid(row=3, column=0, sticky="new")
        size_entry = tkinter.Entry(size_frame)
        size_entry.grid(row=0, column=0, sticky="new")
        kernel_frame = tkinter.LabelFrame(installer_list_frame, text="Select kernel", padx=4, pady=4)
        kernel_frame.grid(row=2, column=0, sticky="new")
        kernel_list = list(kernel_dict)
        kernel_list_var = tkinter.StringVar(value=kernel_list)
        kernel_listbox = tkinter.Listbox(kernel_frame, listvariable=kernel_list_var, exportselection=False,
                                         height=len(kernel_list))
        kernel_listbox.grid(row=0, column=4, sticky="new")
        for key, item in parameter_dict.items():
            default_value = parameter_tracker.get(key, 0)
            parameter_tracker[key] = tkinter.IntVar(main_install_window, default_value)
            tkinter.Checkbutton(check_frame, text=item, variable=parameter_tracker[key]).pack(side="top", anchor="nw")
        for key, item in advanced_parameter_dict.items():
            default_value = advanced_parameter_tracker.get(key, 0)
            advanced_parameter_tracker[key] = tkinter.IntVar(main_install_window, default_value)
            tkinter.Checkbutton(advanced_check_frame, text=item, variable=advanced_parameter_tracker[key]).pack(
                side="top",
                anchor="nw")
        for key, item in basic_toggle_dict.items():
            default_value = basic_toggle_tracker.get(key, 0)
            basic_toggle_tracker[key] = tkinter.IntVar(main_install_window, default_value)
            tkinter.Checkbutton(basic_toggle_frame, text=item, variable=basic_toggle_tracker[key]).pack(side="top",
                                                                                                        anchor="nw")
        native_button = tkinter.Checkbutton(misc_frame,
                                            text="Use Brunch configuration manager instead of configuring through "
                                                 "this app (unstable builds only). ",
                                            variable=native_settings_variable)
        native_button.pack(side="top", anchor="nw")
        unstable_button = tkinter.Checkbutton(unstable_frame,
                                              text="Use unstable releases of Brunch",
                                              variable=unstable_variable)
        unstable_button.pack(side="top", anchor="nw")
        install_button_label = tkinter.StringVar()
        install_button = tkinter.Button(action_buttons_frame, textvariable=install_button_label,
                                        command=install_chrome_os,
                                        background="blue", fg="white")
        install_button.pack(side="right")
        if installed_disk:
            install_button_label.set("Reinstall Chrome OS")
            update_grub2win_button = tkinter.Button(action_buttons_frame, text="Update bootloader",
                                                    background="green", fg="white", command=update_bootloader_button)
            update_grub2win_button.pack(side="right")
            uninstall_button = tkinter.Button(action_buttons_frame, text="Uninstall",
                                              background="red", fg="white", command=uninstall_chrome_os_button)
            uninstall_button.pack(side="left")
            cpu_query = tkinter.Label(title_frame,
                                      text="Installed at {}:\\, CPU detected: {}".format(installed_disk, cpu),
                                      font=Font(family="Arial", size=12),
                                      fg="green", wraplength=600, justify="right")
            cpu_query.grid(row=0, column=3, sticky="ne")
        else:
            install_button_label.set("Install Chrome OS")
            disk_frame = tkinter.LabelFrame(installer_list_frame, text="Select disk", padx=4, pady=4)
            disk_frame.grid(row=1, column=0, sticky="new")
            disk_list = list(disk_dict)
            disk_list_box_var = tkinter.StringVar(value=disk_list)
            disk_list_box = tkinter.Listbox(disk_frame, listvariable=disk_list_box_var, exportselection=False,
                                            height=len(disk_list))
            disk_list_box.grid(row=0, column=0, sticky="new")
            cpu_query = tkinter.Label(title_frame, text="CPU detected: {}".format(cpu),
                                      font=Font(family="Arial", size=12),
                                      fg="green", wraplength=600, justify="right")
            cpu_query.grid(row=0, column=3, sticky="ne")
        main_install_window.update()
        main_install_window.attributes('-alpha', 0.95)
        min_width = parameter_checkbox_frame.winfo_width() + advanced_check_frame.winfo_width() + installer_list_frame \
            .winfo_width() + 16
        largest_option_frame = max([parameter_checkbox_frame.winfo_height(), advanced_check_frame.winfo_height(),
                                    installer_list_frame.winfo_height()])
        min_height = title_frame.winfo_height() + largest_option_frame + action_buttons_frame.winfo_height() + 16
        main_install_window.minsize(width=min_width, height=min_height)
        main_install_window.geometry(f'{min_width}x{min_height}')
        main_install_window.mainloop()
except Exception as e:
    with open("error.txt", "w") as error_file:
        error_file.write(str(time.strftime("%d %H %M %S", time.localtime())))
        error_file.write(str(e))
        error_file.write(traceback.format_exc())
