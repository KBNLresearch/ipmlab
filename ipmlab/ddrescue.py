#! /usr/bin/env python3
"""Wrapper module for ddrescue"""

import os
import time
import logging
import subprocess as sub
from . import config

def getNoReadErrors(rescueLine):
    """parse ddrescue output line for values of readErrors, return number
    of read errors"""
    lineItems = rescueLine.split(",")

    for item in lineItems:
        # Note that 'errors' item was renamed to 'read errors' between ddrescue 1.19 and 1.22
        # This should work in either case
        if "errors:" in item:
            reEntry = item.split(":")
            noReadErrors = int(reEntry[1].strip())

    return noReadErrors


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
    noReadErrors = 0

    # Arguments
    args = [config.ddrescueBin]
    args.append('-b')
    args.append(str(config.blockSize))
    args.append('-r' + str(config.retries))
    args.append('-v')
    args.append(config.inDevice)
    args.append(imageFile)
    args.append(mapFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    # Unmount input device
    sub.run(['umount', config.inDevice], shell=False)

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
                        noReadErrors = getNoReadErrors(tidy_line)

                # Reset line.
                line = ""

        # Parse any remaining lines afterwards.
        if line != "":
            tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")
            if "errors:" in tidy_line:
                # Parse this line for value of read errors
                noReadErrors = getNoReadErrors(tidy_line)

            logging.info(tidy_line)

        p.wait()

        exitStatus = p.returncode

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99

    # Set readErrors flag
    readErrors = noReadErrors != 0

    # All results to dictionary
    dictOut = {}
    dictOut["imageFile"] = imageFile
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = exitStatus
    dictOut["readErrors"] = readErrors
  
    return dictOut
