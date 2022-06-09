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


def getDriveGeometry(drive):
    """
    Get drive geometry parameters from logical Windows drive
    Adapted from:
    
    https://mail.python.org/pipermail/python-list/2003-January/196146.html
    
    CreateFile function documented here:
    
    http://timgolden.me.uk/pywin32-docs/win32file__CreateFile_meth.html

    Function returns a tuple with the following 6 integer values:

    - cylinders[high]
    - cylinders[low]
    - media_type
    - tracks_per_cylinder
    - sectors_per_track
    - bytes_per_sector
    """

    # Low-level device name of device assigned to drive
    driveDevice =  "\\\\.\\" + drive + ":"

    # Create a handle to access the device
    try:
        handle = win32file.CreateFile(driveDevice,
                                    0,
                                    win32file.FILE_SHARE_READ,
                                    None,
                                    win32file.OPEN_EXISTING,
                                    0,
                                    None)

        # Get drive geometry info, result to 24 byte bytes object
        # (which contains 6 unsigned long integer values)
        geometryBytes = win32file.DeviceIoControl(handle,
                                                  winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY,
                                                  None,
                                                  24)

        # Unpack bytes object into a tuple
        geometryValues = struct.unpack('6L',geometryBytes)

    except BaseException as e:
        # We end up here if the device handle cannot be created
        geometryValues = None,None,None,None,None,None

    return geometryValues


def getMediaType(driveGeometry):
    """
    Return media type code from driveGeometry

    Codes are documented here:

    https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ne-winioctl-media_type

    Worth noting that even more media types can be detected using the STORAGE_MEDIA_TYPE
    enumeration:

    https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ne-winioctl-storage_media_type

    These should be available via IOCTL_STORAGE_GET_MEDIA_TYPES:

    https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-ioctl_storage_get_media_types

    But I can't quite get this to work (also can't find any Python examples)
    """

    # Below dictionary maps Windows media type codes against the driveGeometry output codes.
    # 
    # Based on:
    #
    # https://github.com/SublimeText/Pywin32/blob/master/lib/x64/win32/lib/winioctlcon.py
    #

    mediaTypes = {
        0: "Unknown",
        1: "F5_1Pt2_512",
        2: "F3_1Pt44_512",
        3: "F3_2Pt88_512",
        4: "F3_20Pt8_512",
        5: "F3_720_512",
        6: "F5_360_512",
        7: "F5_320_512",
        8: "F5_320_1024",
        9: "F5_180_512",
        10: "F5_160_512",
        11: "RemovableMedia",
        12: "FixedMedia",
        13: "F3_120M_512",
        14: "F3_640_512",
        15: "F5_640_512",
        16: "F5_720_512",
        17: "F3_1Pt2_512",
        18: "F3_1Pt23_1024",
        19: "F5_1Pt23_1024",
        20: "F3_128Mb_512",
        21: "F3_230Mb_512",
        22: "F8_256_128",
        23: "F3_200Mb_512",
        24: "F3_240M_512",
        25: "F3_32M_512"
    }

    # Media code is third item in drive geometry tuple
    mediaCode = driveGeometry[2]
    # Get corresponding media type
    try:
        mediaType = mediaTypes[mediaCode]
    except KeyError:
        mediaType = "Unknown"

    return mediaType


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

    logging.info('*** Establishing medium type ***')
    mediaGeometry = getDriveGeometry(config.driveLetter)
    mediaType = getMediaType(mediaGeometry)

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