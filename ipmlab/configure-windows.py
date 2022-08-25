#! /usr/bin/env python3
"""Post-install / configuration for Ipmlab on Windows"""

import os
import sys
import imp
import site
from shutil import copyfile
import threading
import logging
import platform
if platform.system() == "Windows":
    import pythoncom
    from win32com.client import Dispatch
import tkinter as tk
import tkinter.scrolledtext as ScrolledText
import tkinter.messagebox as tkMessageBox


def errorExit(error):
    """Show error message in messagebox and then exit after userv presses OK"""
    tkMessageBox.showerror("Error", error)
    os._exit(0)


def get_reg(name, path):
    """Read variable from Windows Registry"""
    import winreg
    # From http://stackoverflow.com/a/35286642
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                      winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, name)
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return None


def post_install():
    """Install config file to user dir +
    Create a Desktop shortcut to the installed software
    """
    # This is needed to avoid 'CoInitialize has not been called'
    # error with Dispatch. See: https://stackoverflow.com/a/26753031
    pythoncom.CoInitialize()

    # Package name
    packageName = 'ipmlab'

    # Scripts directory (location of launcher script)
    scriptsDir = os.path.split(sys.argv[0])[0]

    logging.info("Scripts directory: " + scriptsDir)

    # Package directory (parent of scriptsDir)
    packageDir = os.path.abspath(os.path.join(scriptsDir, os.pardir))

    logging.info("Package directory: " + packageDir)

    # Part 1: install config file

    # Locate Windows user directory
    userDir = os.path.expanduser('~')
    # Config directory
    configDirUser = os.path.join(userDir, packageName)
    logging.info("User configuration directory: " + configDirUser)

    # Create config directory if it doesn't exist

    if not os.path.isdir(configDirUser):
        logging.info("Creating user configuration directory ...")
        try:
            os.makedirs(configDirUser)
            logging.info("Done!")
        except IOError:
            msg = 'could not create configuration directory'
            errorExit(msg)

    # Config file name
    configFileUser = os.path.join(configDirUser, 'config.xml')

    if not os.path.isfile(configFileUser):
        # No config file in user dir, so copy it from location in package.
        # Location is /ipmlab/conf/config.xml in 'site-packages' directory
        # if installed with pip)

        logging.info("Copying configuration file to user directory ...")

        # Locate global site-packages dir (this returns multiple entries)
        sitePackageDirsGlobal = site.getsitepackages()

        # Assumptions: site package dir is called 'site-packages' and is
        # unique (?)
        for directory in sitePackageDirsGlobal:
            if 'site-packages' in directory:
                sitePackageDirGlobal = directory
        
        try:
            logging.info("Global site package directory: " + sitePackageDirGlobal)
        except:
            pass

        # Locate user site-packages dir
        sitePackageDirUser = site.getusersitepackages()
        logging.info("User site package directory: " + sitePackageDirUser)

        # Determine which site package dir to use
        # Convert to lowercase because result of site.getsitepackages()
        # sometimes results in lowercase output (observed with Python 3.7 on Windows 10) 
        if packageDir.lower() in sitePackageDirGlobal.lower():
            sitePackageDir = sitePackageDirGlobal
        elif packageDir.lower() in sitePackageDirUser.lower():
            sitePackageDir = sitePackageDirUser
        else:
            msg = 'could not establish package dir to use'
            errorExit(msg)

        logging.info("Site package directory: " + sitePackageDir)

        # Construct path to config file
        configFilePackage = os.path.join(sitePackageDir, packageName,
                                         'conf', 'config-win.xml')

        if os.path.isfile(configFilePackage):
            try:
                copyfile(configFilePackage, configFileUser)
                logging.info("Done!")
            except IOError:
                msg = 'could not copy configuration file to ' + configFileUser
                errorExit(msg)
        # This should never happen but who knows ...
        else:
            msg = 'no configuration file found in package'
            errorExit(msg)

    # Part 2: create Desktop shortcut

    logging.info("Creating desktop shortcut ...")

    try:

        # Target of shortcut
        target = os.path.join(scriptsDir, packageName + '.exe')
        logging.info("Target of shortcut: " + target)
        # Name of link file
        linkName = packageName + '.lnk'
        # User profile folder
        profileFolder = os.getenv('USERPROFILE')
        # Desktop folder
        desktopFolder = os.path.join(profileFolder, "Desktop")
        logging.info("Desktop directory: " + desktopFolder)
        # Path to location of link file
        pathLink = os.path.join(desktopFolder, linkName)
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(pathLink)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = scriptsDir
        shortcut.IconLocation = target
        shortcut.save()
        logging.info("Done!")
    except Exception:
        msg = 'Failed to create desktop shortcut'
        errorExit(msg)

    msg = 'Ipmlab configuration completed successfully, click OK to exit!'
    tkMessageBox.showinfo("Info", msg)
    os._exit(0)


class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget
    Adapted from Moshe Kaplan:
    https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    """

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


class myGUI(tk.Frame):

    """This class defines the graphical user interface"""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.build_gui()

    def build_gui(self):
        # Build GUI
        self.root.title('Ipmlab Configuration Tool')
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')

        # Add text widget to display logging info
        st = ScrolledText.ScrolledText(self, state='disabled')
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=1, sticky='w', columnspan=4)

        # Create textLogger
        text_handler = TextHandler(st)

        # Logging configuration
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Add the handler to logger
        logger = logging.getLogger()
        logger.addHandler(text_handler)


def main():
    """Main function"""
    root = tk.Tk()
    myGUI(root)

    t1 = threading.Thread(target=post_install, args=[])
    t1.start()

    root.mainloop()
    t1.join()


if __name__ == "__main__":
    main()
