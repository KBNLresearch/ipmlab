#! /usr/bin/env python3
"""Post-install / configuration for Ipmlab on Linux"""

import os
import sys
import io
import site
from shutil import copyfile
import logging


def errorExit(msg):
    """Show error message and exit"""
    sys.stderr.write("Error: " + msg + "\n")
    sys.exit(1)


def writeDesktopFiles(applicationsDir):
    """Creates desktop file in /usr/share/applications"""

    # Needed to change file permissions
    sudoUID = os.environ.get('SUDO_UID')
    sudoGID = os.environ.get('SUDO_GID')

    # Full path to config and launcher scripts
    pathName = os.path.abspath(os.path.dirname(sys.argv[0]))

    """
    # Locate icon file in package
    iconFile = os.path.join(packageDir, 'icons', 'omimgr.png')
    if not os.path.isfile(iconFile):
        msg = 'cannot find icon file'
        errorExit(msg)
    """

    fApplications = os.path.join(applicationsDir, 'ipmlab.desktop')

    # List of desktop file lines
    desktopList = []
    desktopList.append('[Desktop Entry]')
    desktopList.append('Type=Application')
    desktopList.append('Encoding=UTF-8')
    desktopList.append('Name=ipmlab')
    desktopList.append('Comment=Image Portable Media Like A Boss')
    desktopList.append('Exec=' + os.path.join(pathName, 'ipmlab'))
    #desktopList.append('Icon=' + iconFile)
    desktopList.append('Terminal=false')
    desktopList.append('Categories=Utility;System;GTK')

    # Write desktop file to applications directory
    try:
        logging.info('creating desktop file ' + fApplications)
        with io.open(fApplications, 'w', encoding='utf-8') as fA:
            for line in desktopList:
                fA.write(line + '\n')
    except:
        msg = 'Failed to create ' + fApplications
        errorExit(msg)


def post_install():
    """Install config file + pre-packaged tools to user dir +
    Create a Desktop shortcut to the installed software

    Creates the following items:
    - configuration directory ipmlab in ~/.config/ or /etc/
    - configuration file in configuration directory
    - desktop file in  ~/.local/share/applications/ or /usr/share/applications
    """

    # Get evironment variables
    sudoUser = os.environ.get('SUDO_USER')

    # Package name
    packageName = 'ipmlab'

    # Scripts directory (location of launcher script)
    scriptsDir = os.path.split(sys.argv[0])[0]

    logging.info("Scripts directory: " + scriptsDir)

    # Package directory (parent of scriptsDir)
    packageDir = os.path.abspath(os.path.join(scriptsDir, os.pardir))

    logging.info("Package directory: " + packageDir)

    # Current home directory
    try:
        # If executed as root, return normal user's home directory
        homeDir = os.path.normpath('/home/'+ sudoUser)
    except TypeError:
        # sudoUser doesn't exist if not executed as root
        homeDir = os.path.normpath(os.path.expanduser("~"))

    logging.info("Home directory: " + homeDir)

    # Get locations of configRootDir and applicationsDir,
    # depending of install type (which is inferred from packageDir)

    if packageDir.startswith(homeDir):
        # Local install: store everything in user's home dir
        globalInstall = False
        configRootDir = os.path.join(homeDir, '.config/')
        applicationsDir = os.path.join(homeDir, '.local/share/applications/')
    else:
        # Global install
        globalInstall = True
        configRootDir = os.path.normpath('/etc/')
        applicationsDir = os.path.normpath('/usr/share/applications')

    logging.info("Applications directory: " + applicationsDir)

    """
    # Desktop directory
    desktopDir = os.path.join(homeDir, 'Desktop/')

    logging.info("Desktop directory: " + desktopDir)
    """

    # Create applicationsDir and configRootDir if they don't exist already
    if not os.path.isdir(configRootDir):
        os.mkdir(configRootDir)
    if not os.path.isdir(applicationsDir):
        os.mkdir(applicationsDir)

    # For a global installation this script must be run as root
    if globalInstall and sudoUser is None:
        msg = 'this script must be run as root for a global installation'
        errorExit(msg)

    # Check if directories exist and that they are writable
    if not os.access(configRootDir, os.W_OK | os.X_OK):
        msg = 'cannot write to ' + configRootDir
        errorExit(msg)

    if not os.access(applicationsDir, os.W_OK | os.X_OK):
        msg = 'cannot write to ' + applicationsDir
        errorExit(msg)

    """
    if not os.access(desktopDir, os.W_OK | os.X_OK):
        msg = 'cannot write to ' + desktopDir
        errorExit(msg)
    """

    # Create configuration directory if it doesn't already exist
    configDir = os.path.join(configRootDir, packageName)

    logging.info("Configuration directory: " + configDir)

    if not os.path.isdir(configDir):
        os.mkdir(configDir)

    # Path to configuration file
    fConfig = os.path.join(configDir, 'config.xml')

    if not os.path.isfile(fConfig):
        # No existing config file at destination, so copy from package.
        # Location is /ipmlab/conf/config.xml in 'site-packages' directory
        # if installed with pip)

        logging.info("Copying configuration file ...")

        # Locate global site-packages dir (this returns multiple entries)
        sitePackageDirsGlobal = site.getsitepackages()

        sitePackageDirGlobal = ""

        # Assumptions: site package dir is called 'site-packages' and is
        # unique (?)
        for directory in sitePackageDirsGlobal:
            if 'site-packages' in directory:
                sitePackageDirGlobal = directory
        
        try:
            logging.info("Global site package directory: " + sitePackageDirGlobal)
        except:
            msg = "Could not establish global site package directory"
            errorExit(msg)

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
                                         'conf', 'config-linux.xml')

        if os.path.isfile(configFilePackage):
            try:
                copyfile(configFilePackage, fConfig)
                logging.info("copied configuration file!")
            except IOError:
                msg = 'could not copy configuration file to ' + fConfig
                errorExit(msg)
        # This should never happen but who knows ...
        else:
            msg = 'no configuration file found in package'
            errorExit(msg)

    writeDesktopFiles(applicationsDir)

    sys.stdout.write('Ipmlab configuration completed successfully!\n')
    sys.exit(0)


def main():
    """Main function"""

    # Logging configuration
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    post_install()


if __name__ == "__main__":
    main()
