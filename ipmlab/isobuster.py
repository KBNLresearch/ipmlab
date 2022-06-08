#! /usr/bin/env python
"""Wrapper module for Isobuster"""

import os
import io
import time
from . import config
from . import shared


def extractData(writeDirectory):
    """Extract data to disk image"""

    # Temporary name for image file; base name
    imageFileTemp = os.path.join(writeDirectory, "disc.img")
    logFile = os.path.join(writeDirectory, "isobuster.log")
    reportFile = os.path.join(writeDirectory, "isobuster-report-<%FN>.xml")
    
    # Format string that defines DFXML output report
    reportFormatString = config.reportFormatString

    args = [config.isoBusterExe]
    args.append("".join(["/d:", config.driveLetter, ":"]))
    args.append("".join(["/ei:", imageFileTemp]))
    args.append("/et:u")
    args.append("/ep:oea")
    args.append("/ep:npc")
    args.append("/c")
    args.append("/m")
    args.append("/nosplash")
    args.append("/s:1")
    args.append("".join(["/l:", logFile]))
    args.append("".join(["/tree:all:", reportFile, '?', reportFormatString]))

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    status, out, err = shared.launchSubProcess(args)

    # For some reason sometimes a FileNotFoundError occurs on the log file, so
    # we'll wait until it is actually available
    logFileExists = False
    while not logFileExists:
        time.sleep(2)
        logFileExists = os.path.isfile(logFile)

    # Open and read log file
    with io.open(logFile, "r", encoding="cp1252") as fLog:
        log = fLog.read()
    fLog.close()

    # Rewrite as UTF-8
    with io.open(logFile, "w", encoding="utf-8") as fLog:
        fLog.write(log)
    fLog.close()

    # TODO, remove volumeLabel later
    volumeLabel = ''

    if volumeLabel != '':
        # Rename image file using volumeLabel as a base name
        # Any spaces in volumeLabel are replaced with dashes
        try:
            imageFile = os.path.join(writeDirectory, volumeLabel.replace(' ', '-') + '.img')
            os.rename(imageFileTemp, imageFile)
        except:
            pass

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log
    dictOut["volumeIdentifier"] = volumeLabel

    return dictOut
