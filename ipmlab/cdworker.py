#! /usr/bin/env python
"""This module contains ipmlab's cdWorker code, i.e. the code that monitors
the list of jobs (submitted from the GUI) and does the actual imaging and ripping
"""

import sys
import os
import shutil
import time
import glob
import csv
import hashlib
import logging
import platform
if platform.system() == "Windows":
    import pythoncom
    import wmi
import _thread as thread
from . import config
from . import isobuster
from . import mdo

def mediumLoaded(driveName):
    """Returns True if medium is loaded (also if blank/unredable), False if not"""

    # Use CoInitialize to avoid errors like this:
    # http://stackoverflow.com/questions/14428707/python-function-is-unable-to-run-in-new-thread
    pythoncom.CoInitialize()
    c = wmi.WMI()
    foundDriveName = False
    loaded = False
    for cdrom in c.Win32_CDROMDrive():
        if cdrom.Drive == driveName:
            foundDriveName = True
            loaded = cdrom.MediaLoaded

    return(foundDriveName, loaded)


def generate_file_md5(fileIn):
    """Generate MD5 hash of file"""

    # fileIn is read in chunks to ensure it will work with (very) large files as well
    # Adapted from: http://stackoverflow.com/a/1131255/1209004

    blocksize = 2**20
    m = hashlib.md5()
    with open(fileIn, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def generate_file_sha512(fileIn):
    """Generate sha512 hash of file"""

    # fileIn is read in chunks to ensure it will work with (very) large files as well
    # Adapted from: http://stackoverflow.com/a/1131255/1209004

    blocksize = 2**20
    m = hashlib.sha512()
    with open(fileIn, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def checksumDirectory(directory):
    """Calculate checksums for all files in directory"""

    # All files in directory
    allFiles = glob.glob(directory + "/*")

    # Dictionary for storing results
    checksums = {}

    for fName in allFiles:
        hashString = generate_file_sha512(fName)
        checksums[fName] = hashString

    # Write checksum file
    try:
        fChecksum = open(os.path.join(directory, "checksums.sha512"), "w", encoding="utf-8")
        for fName in checksums:
            lineOut = checksums[fName] + " " + os.path.basename(fName) + '\n'
            fChecksum.write(lineOut)
        fChecksum.close()
        wroteChecksums = True
    except IOError:
        wroteChecksums = False

    return wroteChecksums


def processDisc(carrierData):
    """Process one disc / job"""

    jobID = carrierData['jobID']
    PPN = carrierData['PPN']
    containsData = True # Dummy variable, TODO remove later

    logging.info(''.join(['### Job identifier: ', jobID]))
    logging.info(''.join(['PPN: ', carrierData['PPN']]))
    logging.info(''.join(['Title: ', carrierData['title']]))
    logging.info(''.join(['Volume number: ', carrierData['volumeNo']]))

    # Initialise success status
    success = True

    # Create output folder for this disc
    dirDisc = os.path.join(config.batchFolder, jobID)
    logging.info(''.join(['disc directory: ', dirDisc]))
    if not os.path.exists(dirDisc):
        os.makedirs(dirDisc)

    if containsData:
        # TODO, either remove conditional block or establish containsData on some sensible test
        logging.info('*** Extracting data ***')
        resultIsoBuster = isobuster.extractData(dirDisc)
        statusIsoBuster = resultIsoBuster["log"].strip()

        if statusIsoBuster != "0":
            success = False
            logging.error("Isobuster exited with error(s)")

        logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
        logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
        logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
        logging.info(''.join(['volumeIdentifier: ', str(resultIsoBuster['volumeIdentifier'])]))
    
    else:
        # We end up here if no data were detected
        success = False
        logging.error("Unable to identify disc type")

    if config.enablePPNLookup:
        # Fetch metadata from KBMDO and store as file
        logging.info('*** Writing metadata from KB-MDO to file ***')

        successMdoWrite = mdo.writeMDORecord(PPN, dirDisc)
        if not successMdoWrite:
            success = False
            reject = True
            logging.error("Could not write metadata from KB-MDO")

    # Generate checksum file
    logging.info('*** Computing checksums ***')
    successChecksum = checksumDirectory(dirDisc)

    if not successChecksum:
        success = False
        logging.error("Writing of checksum file resulted in an error")

    # Create comma-delimited batch manifest entry for this carrier

    # VolumeIdentifier only defined for ISOs, not for pure audio CDs and CD Interactive!
    if containsData:
        # TODO, either remove conditional block or establish containsData on some sensible test
        try:
            volumeID = resultIsoBuster['volumeIdentifier'].strip()
        except Exception:
            volumeID = ''
    else:
        volumeID = ''

    # Put all items for batch manifest entry in a list
    rowBatchManifest = ([jobID,
                         carrierData['PPN'],
                         carrierData['volumeNo'],
                         carrierData['title'],
                         volumeID,
                         str(success),
                         str(containsData)])

    # Open batch manifest in append mode
    bm = open(config.batchManifest, "a", encoding="utf-8")

    # Create CSV writer object
    csvBm = csv.writer(bm, lineterminator='\n')

    # Write row to batch manifest and close file
    csvBm.writerow(rowBatchManifest)
    bm.close()

    logging.info('*** Finished processing disc ***')

    # Set finishedDisc flag
    config.finishedDisc = True

    return success