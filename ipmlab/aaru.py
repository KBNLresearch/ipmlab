#! /usr/bin/env python3
"""Wrapper module for Aaru"""

import os
import io
import platform
import time
import subprocess as sub
from . import config

def extractData(writeDirectory, imageFileBaseName):
    """Extract data to disk image"""

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')

    # Error log file name
    errorLogFile = os.path.join(writeDirectory, imageFileBaseName + '.error.log')

    args = [config.aaruBin]
    args.append("media")
    args.append("dump")
    args.append("--encoding")
    args.append("utf-8")
    args.append("--metadata")
    if platform.system() == "Windows":
        args.append("".join([config.inDevice, ":"]))
    elif platform.system() == "Linux":
        args.append(config.inDevice)
    args.append(imageFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    if platform.system() == "Linux":
        # Unmount input device
        sub.run(['umount', config.inDevice], shell=False)

    # Run Aaru as subprocess
    p = sub.run(args, shell=False)

    errorLogExists = False
    while not errorLogExists:
        time.sleep(2)
        errorLogExists = os.path.isfile(errorLogFile)

    # Read error log
    with io.open(errorLogFile, "r", encoding="utf-8") as eLog:
        eLogList = eLog.read().splitlines()
    eLog.close()

    eLogDelim = "######################################################"

    try:
        if eLogList[1].strip() == eLogDelim and eLogList[2].strip() == eLogDelim:
            readErrors = False
        else:
            readErrors = True
    except:
        readErrors = True

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = p.returncode
    dictOut["readErrors"] = readErrors
  
    return dictOut
