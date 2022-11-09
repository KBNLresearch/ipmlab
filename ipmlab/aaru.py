#! /usr/bin/env python3
"""Wrapper module for Aaru"""

import os
import io
import platform
import time
import logging
import subprocess as sub
from . import config

def extractData(writeDirectory, imageFileBaseName):
    """Extract data to disk image"""

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')

    # Error log file name
    errorLogFile = os.path.join(writeDirectory, imageFileBaseName + '.error.log')

    # This flag defines how subprocesses are executed 
    shellFlag = False

    args = [config.aaruBin]
    args.append("media")
    args.append("dump")
    args.append("--encoding")
    args.append("utf-8")
    args.append("--metadata")
    if platform.system() == "Windows":
        args.append("".join([config.inDevice, ":"]))
        shellFlag = True
    elif platform.system() == "Linux":
        args.append(config.inDevice)
    args.append(imageFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    if platform.system() == "Linux":
        # Unmount input device
        logging.info("unmounting input device")
        p1 = sub.Popen(['umount', config.inDevice], stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
        out, errors = p1.communicate()
 
    # Run Aaru as subprocess
    logging.info("running Aaru")
    p2 = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=shellFlag)
    out, errors = p2.communicate()    

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
    dictOut["imageFile"] = imageFile
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = p2.returncode
    dictOut["readErrors"] = readErrors
  
    return dictOut
