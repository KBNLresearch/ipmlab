#! /usr/bin/env python3
"""Wrapper module for ddrescue"""

import os
import io
import platform
import time
import logging
import subprocess as sub
from . import config

def getPosixDevice(driveName):
    """
    Returns POSIX device name of Windows drive (Cygwin)
    May return None if drive is empty! 
    """
    devPosix = None

    args = [config.catBin]
    args.append('/proc/partitions')

    p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    out, err = p.communicate()
    outString = out.decode("utf-8")
    partList = outString.split("\n")

    pLine = 0

    for line in partList:
        items = line.strip().split()
        if pLine > 1 and len(items) == 5:
            devName = items[3]
            winMount = items[4].strip(":/\\")
            if winMount == driveName:
                devPosix = "/dev/" + devName
        pLine += 1
    
    return devPosix


def getReadErrors(rescueLine):
    """parse ddrescue output line for values of readErrors"""
    lineItems = rescueLine.split(",")

    for item in lineItems:
        # Note that 'errors' item was renamed to 'read errors' between ddrescue 1.19 and 1.22
        # This should work in either case
        if "errors:" in item:
            reEntry = item.split(":")
            readErrors = int(reEntry[1].strip())

    return readErrors


def extractData(writeDirectory, imageFileBaseName):
    """Extract data to disk image"""

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')

    # Map file name
    mapFile = os.path.join(writeDirectory, imageFileBaseName + '.map')

    # Error log file name
    #errorLogFile = os.path.join(writeDirectory, imageFileBaseName + '.error.log')

    # This flag defines how subprocesses are executed 
    shellFlag = False

    # Number of read errors
    readErrors = 0

    # Arguments
    args = [config.ddrescueBin]
    args.append('-b')
    args.append(str(config.blockSize))
    args.append('-r' + str(config.retries))
    args.append('-v')
    if platform.system() == "Windows":
        # Derive Cygwin-specific POSIX device that corresponds to logical drive
        inDevCygwin = getPosixDevice(config.inDevice)
        args.append(inDevCygwin)
    elif platform.system() == "Linux":
        args.append(config.inDevice)
    args.append(imageFile)
    args.append(mapFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    if platform.system() == "Linux":
        # Unmount input device
        sub.run(['umount', config.inDevice], shell=False)
    elif platform.system() == "Windows":
        shellFlag = True

    # Run ddrescue as subprocess
    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=shellFlag, bufsize=1, universal_newlines=True)

        # Processing of output adapted from DDRescue-GUI by Hamish McIntyre-Bhatty:
        # https://git.launchpad.net/ddrescue-gui/tree/DDRescue_GUI.py

        line = ""
        char = " "

        # Give ddrescue plenty of time to start.
        time.sleep(2)

        # Grab information from ddrescue. (After ddrescue exits, attempt to keep reading chars until
        # the last attempt gave an empty string)
        while p.poll() is None or char != "":
            char = p.stdout.read(1)
            line += char

            # If this is the end of the line, process it, and send the results to the logger
            if char == "\n":
                tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")

                if tidy_line != "":

                    if "errors:" in tidy_line:
                        # Parse this line for value of read errors
                        readErrors = getReadErrors(tidy_line)

                # Reset line.
                line = ""

        # Parse any remaining lines afterwards.
        if line != "":
            tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")
            if "errors:" in tidy_line:
                # Parse this line for value of read errors
                readErrors = getReadErrors(tidy_line)

            logging.info(tidy_line)

        p.wait()

        exitStatus = p.returncode

    except Exception:
        raise
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = exitStatus
    dictOut["readErrors"] = readErrors
  
    return dictOut
