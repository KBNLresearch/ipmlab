#! /usr/bin/env python3
"""Wrapper module for fiwalk"""

import os
import time
import subprocess as sub
from . import config

def runFiwalk(writeDirectory, imageFileBaseName):
    """Run fiwalk on disk image and write result to dfxml"""

    # Image file name
    imageFile = os.path.join(writeDirectory, imageFileBaseName + '.img')

    # Dfxml output file
    outFile = os.path.join(writeDirectory, 'dfxml.xml')

    # Arguments
    args = [config.fiwalkBin]
    args.append('-X')
    args.append(outFile)
    args.append(imageFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    # Run fiwalk as subprocess
    try:        
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
        out, errors = p.communicate()
        # Wait until output file has been written (do we really need this here?)
        outFileExists = False
        while not outFileExists:
            time.sleep(2)
            outFileExists = os.path.isfile(outFile)
        exitStatus = p.returncode
    except Exception:
        exitStatus = -99

    # All results to dictionary
    dictOut = {}
    dictOut["imageFile"] = imageFile
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = exitStatus
  
    return dictOut