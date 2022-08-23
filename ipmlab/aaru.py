#! /usr/bin/env python
"""Wrapper module for Aaru"""

import os
import io
import time
import subprocess as sub
from . import config

def extractData(writeDirectory, imageFileBaseName):
    """Extract data to disk image"""

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')

    args = [config.aaruBin]
    args.append("m")
    args.append("dump")
    args.append("".join([config.driveLetter, ":"]))
    args.append(imageFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    # Run Aaru as subprocess
    p = sub.run(args, shell=True)

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = p.returncode
  
    return dictOut
