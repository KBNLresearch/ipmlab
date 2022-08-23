#! /usr/bin/env python
"""Wrapper module for Aaru"""

import os
import io
import time
from . import config
from . import shared


def extractData(writeDirectory, imageFileBaseName):
    """Extract data to disk image"""

    # TODO read from config
    config.aaruBin =  "W:\aaru-5.3.1_windows_x64\aaru.exe"

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')

    # W:\aaru-5.3.1_windows_x64\aaru m dump E: W:\test-aaru\bullsh.img

    args = [config.aaruBin]
    args.append("m")
    args.append("dump")
    args.append("".join([config.driveLetter, ":"]))
    args.append(imageFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    status, out, err = shared.launchSubProcess(args)

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
  
    return dictOut
