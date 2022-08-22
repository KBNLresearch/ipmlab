#! /usr/bin/env python
"""Wrapper module for Isobuster"""

import os
import io
import time
from . import config
from . import shared


def extractData(writeDirectory, imageFileBaseName):
    """Extract data to disk image"""

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')
    # Log file
    logFile = os.path.join(writeDirectory, "isobuster.log")
    #reportFile = os.path.join(writeDirectory, "isobuster-report-<%FN>.xml")
    reportFile = os.path.join(writeDirectory, "isobuster-report.xml")    

    # Format string that defines DFXML output report
    reportFormatString = config.reportFormatString

    args = [config.isoBusterExe]
    args.append("".join(["/d:", config.driveLetter, ":"]))
    args.append("".join(["/ei:", imageFile]))
    args.append("/et:u")
    args.append("/ep:oez")
    args.append("/ep:npc")
    args.append("/c")
    args.append("/m")
    args.append("/nosplash")
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

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log

    return dictOut
