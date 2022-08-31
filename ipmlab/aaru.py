#! /usr/bin/env python3
"""Wrapper module for Aaru"""

import os
import platform
import subprocess as sub
from . import config

def extractData(writeDirectory, imageFileBaseName):
    """Extract data to disk image"""

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')

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

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = p.returncode
  
    return dictOut
