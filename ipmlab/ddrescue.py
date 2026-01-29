#! /usr/bin/env python3
"""Wrapper module for ddrescue"""

import os
import io 
import time
import logging
import subprocess as sub
from . import config

def getNoReadErrors(rescueLine):
    """parse ddrescue output line for values of readErrors, return number
    of read errors.
    TODO: do we really need this anymore, since we're now using the number
    of bad blocks from the map file as an indicator?"""

    lineItems = rescueLine.split(",")

    for item in lineItems:
        # Note that 'errors' item was renamed to 'read errors' between ddrescue 1.19 and 1.22
        # This should work in either case
        if "errors:" in item:
            reEntry = item.split(":")
            noReadErrors = int(reEntry[1].strip())

    return noReadErrors


def getNoBadBlocks(map):
    """Parse ddrescue map file data and count number of bad blocks
    This follows mapfile structure described here:
    https://www.gnu.org/software/ddrescue/manual/ddrescue_manual.html#Mapfile-structure
    """

    noBadBlocks = 0
    lineNo = 0
    for line in map:
        line = line.strip()
        if line.startswith('#'):
            # Line is a comment, skip
            pass
        elif lineNo == 0:
            # Line is a status line, skip but increase counter
            lineNo += 1
        else:
            # Line describes a data block
            blockItems = line.split()
            blockStatus = blockItems[2]
            if blockStatus != '+':
                noBadBlocks += 1
            lineNo += 1

    return noBadBlocks


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

    # Number of bad blocks
    noBadBlocks = 0

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

    try:
        with io.open(mapFile, "r", encoding="utf-8") as fMap:
            map = fMap.read().splitlines()
            noBadBlocks = getNoBadBlocks(map)
    except Exception:
        logging.error("error reading ddrescue map file")
        # Set noBadBlocks to ensure this will be flagged
        noBadBlocks = 99

    # Set readErrors and badBlocks flags
    readErrors = noReadErrors != 0
    badBlocks = noBadBlocks != 0

    # All results to dictionary
    dictOut = {}
    dictOut["imageFile"] = imageFile
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = exitStatus
    dictOut["readErrors"] = readErrors
    dictOut["badBlocks"] = badBlocks
  
    return dictOut
