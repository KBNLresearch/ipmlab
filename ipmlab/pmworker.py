#! /usr/bin/env python
"""This module contains the code that does the actual imaging
"""

import sys
import os
import struct
import win32api
import win32file
import winioctlcon
import glob
import csv
import hashlib
import logging
import platform
if platform.system() == "Windows":
    import pythoncom
    import wmi
from . import config
from . import isobuster
from . import mdo
from . import mediuminfo


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

def fixDfXMLFileNames(directory):
    """
    Replace whitespace characters in Isobuster dfxml file names
    with underscores
    """

    # All DFXML files in directory
    dfxmlFiles = glob.glob(directory + "/isobuster-report*.xml")

    for file in dfxmlFiles:
        nameOld = os.path.basename(file)
        nameNew = nameOld.replace(" ", "_")
        fileNew = os.path.join(directory, nameNew)
        os.rename(file, fileNew)


def processMedium(carrierData):
    """Process one medium/carrier"""

    jobID = carrierData['jobID']
    PPN = carrierData['PPN']

    logging.info(''.join(['### Job identifier: ', jobID]))
    logging.info(''.join(['PPN: ', carrierData['PPN']]))
    logging.info(''.join(['Title: ', carrierData['title']]))
    logging.info(''.join(['Volume number: ', carrierData['volumeNo']]))

    # Initialise success status
    success = True

    # Create output folder for this medium
    dirMedium = os.path.join(config.batchFolder, jobID)
    logging.info(''.join(['medium directory: ', dirMedium]))
    if not os.path.exists(dirMedium):
        os.makedirs(dirMedium)

    logging.info('*** Establishing media type and device type ***')
    drive = config.driveLetter
    driveHandle = mediuminfo.createFileHandle(drive)
    mediaType = mediuminfo.getMediaType(drive, driveHandle)
    deviceType = mediuminfo.getDeviceInfo(drive, driveHandle)[0]

    logging.info('*** Extracting data ***')
    resultIsoBuster = isobuster.extractData(dirMedium)
    statusIsoBuster = resultIsoBuster["log"].strip()

    if statusIsoBuster != "0":
        success = False
        logging.error("Isobuster exited with error(s)")

    logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
    logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
    logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
    logging.info(''.join(['volumeIdentifier: ', str(resultIsoBuster['volumeIdentifier'])]))

    # Replace any white space characters in Isobuster dfxml files with underscores
    fixDfXMLFileNames(dirMedium)

    if config.enablePPNLookup:
        # Fetch metadata from KBMDO and store as file
        logging.info('*** Writing metadata from KB-MDO to file ***')

        successMdoWrite = mdo.writeMDORecord(PPN, dirMedium)
        if not successMdoWrite:
            success = False
            reject = True
            logging.error("Could not write metadata from KB-MDO")

    # Generate checksum file
    logging.info('*** Computing checksums ***')
    successChecksum = checksumDirectory(dirMedium)

    if not successChecksum:
        success = False
        logging.error("Writing of checksum file resulted in an error")

    # Create comma-delimited batch manifest entry for this carrier

    # VolumeIdentifier only defined for ISOs, not for pure audio CDs and CD Interactive!
    try:
        volumeID = resultIsoBuster['volumeIdentifier'].strip()
    except Exception:
        volumeID = ''

    # Put all items for batch manifest entry in a list
    rowBatchManifest = ([jobID,
                         carrierData['PPN'],
                         carrierData['volumeNo'],
                         carrierData['title'],
                         volumeID,
                         mediaType,
                         deviceType,
                         str(success)])

    # Open batch manifest in append mode
    bm = open(config.batchManifest, "a", encoding="utf-8")

    # Create CSV writer object
    csvBm = csv.writer(bm, lineterminator='\n')

    # Write row to batch manifest and close file
    csvBm.writerow(rowBatchManifest)
    bm.close()

    logging.info('*** Finished processing medium ***')

    # Set finishedMedium flag
    config.finishedMedium = True

    return success