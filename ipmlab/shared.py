#! /usr/bin/env python
"""Shared functions module for Iromlab"""

import os
import subprocess as sub
import string
from random import choice


def launchSubProcess(args):
    """Launch subprocess and return exit code, stdout and stderr"""
    try:
        # Execute command line; stdout + stderr redirected to objects
        # 'output' and 'errors'.
        # Setting shell=True avoids console window poppong up with pythonw
        #p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
        p = sub.run(args)
        # output, errors = p.communicate()

        # Decode to Latin-1
        #outputAsString = output.decode('latin-1')
        #errorsAsString = errors.decode('latin-1')
        outputAsString = ""
        errorsAsString = ""

        exitStatus = p.returncode

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        ## TEST
        raise
        ## TEST

        exitStatus = -99
        outputAsString = ""
        errorsAsString = ""

    return(exitStatus, outputAsString, errorsAsString)


def randomString(length):
    """Generate text string with random characters (a-z;A-Z;0-9)"""
    return ''.join(choice(string.ascii_letters + string.digits) for i in range(length))


def index_startswith_substring(the_list, substring):
    """What is this? What is it used for?"""
    for i, s in enumerate(the_list):
        if s.startswith(substring):
            return i
    return -1


class cd:
    """Context manager for changing the current working directory"""
    # Source: http://stackoverflow.com/a/13197763
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
