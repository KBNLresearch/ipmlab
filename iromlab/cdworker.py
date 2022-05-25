#! /usr/bin/env python
"""This module contains iromlab's cdWorker code, i.e. the code that monitors
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
from . import cdinfo
from . import isobuster
from . import dbpoweramp
from . import verifyaudio
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

    logging.info(''.join(['### Job identifier: ', jobID]))
    logging.info(''.join(['PPN: ', carrierData['PPN']]))
    logging.info(''.join(['Title: ', carrierData['title']]))
    logging.info(''.join(['Volume number: ', carrierData['volumeNo']]))

    # Initialise reject and success status
    reject = False
    success = True

    # Create output folder for this disc
    dirDisc = os.path.join(config.batchFolder, jobID)
    logging.info(''.join(['disc directory: ', dirDisc]))
    if not os.path.exists(dirDisc):
        os.makedirs(dirDisc)

    # Get disc info
    logging.info('*** Running cd-info ***')
    carrierInfo = cdinfo.getCarrierInfo(dirDisc)
    logging.info(''.join(['cd-info command: ', carrierInfo['cmdStr']]))
    logging.info(''.join(['cd-info-status: ', str(carrierInfo['status'])]))
    logging.info(''.join(['cdExtra: ', str(carrierInfo['cdExtra'])]))
    logging.info(''.join(['containsAudio: ', str(carrierInfo['containsAudio'])]))
    logging.info(''.join(['containsData: ', str(carrierInfo['containsData'])]))
    logging.info(''.join(['mixedMode: ', str(carrierInfo['mixedMode'])]))
    logging.info(''.join(['cdInteractive: ', str(carrierInfo['cdInteractive'])]))
    logging.info(''.join(['multiSession: ', str(carrierInfo['multiSession'])]))

    # Assumptions in below workflow:
    # 1. Audio tracks are always part of 1st session
    # 2. If disc is of CD-Extra type, there's one data track on the 2nd session
    if carrierInfo["containsAudio"]:
        logging.info('*** Ripping audio ***')
        # Rip audio using dBpoweramp console ripper
        resultdBpoweramp = dbpoweramp.consoleRipper(dirDisc)
        statusdBpoweramp = str(resultdBpoweramp["status"])
        logdBpoweramp = resultdBpoweramp["log"]
        # secureExtractionLog = resultdBpoweramp["secureExtractionLog"]

        if statusdBpoweramp != "0":
            success = False
            reject = True
            logging.error("dBpoweramp exited with error(s)")

        logging.info(''.join(['dBpoweramp command: ', resultdBpoweramp['cmdStr']]))
        logging.info(''.join(['dBpoweramp-status: ', str(resultdBpoweramp['status'])]))
        logging.info("dBpoweramp log:\n" + logdBpoweramp)

        # Verify that created audio files are not corrupt (using shntool / flac)
        logging.info('*** Verifying audio ***')
        audioHasErrors, audioErrorsList = verifyaudio.verifyCD(dirDisc, config.audioFormat)
        logging.info(''.join(['audioHasErrors: ', str(audioHasErrors)]))

        if audioHasErrors:
            success = False
            reject = True
            logging.error("Verification of audio files resulted in error(s)")

        # TODO perhaps indent this block if we only want this in case of actual errors?
        logging.info("Output of audio verification:")
        for audioFile in audioErrorsList:
            for item in audioFile:
                logging.info(item)

        if carrierInfo["containsData"]:
            if carrierInfo["cdExtra"]:
                logging.info('*** Extracting data session of cdExtra to ISO ***')
                # Create ISO file from data on 2nd session
                dataTrackLSNStart = int(carrierInfo['dataTrackLSNStart'])
                resultIsoBuster = isobuster.extractData(dirDisc, 2, dataTrackLSNStart)
            elif carrierInfo["mixedMode"]:
                logging.info('*** Extracting data session of mixedMode disc to ISO ***')
                dataTrackLSNStart = int(carrierInfo['dataTrackLSNStart'])
                resultIsoBuster = isobuster.extractData(dirDisc, 1, dataTrackLSNStart)

            statusIsoBuster = resultIsoBuster["log"].strip()
            isolyzerSuccess = resultIsoBuster['isolyzerSuccess']
            imageTruncated = resultIsoBuster['imageTruncated']

            if statusIsoBuster != "0":
                success = False
                reject = True
                logging.error("Isobuster exited with error(s)")

            elif not isolyzerSuccess:
                success = False
                reject = True
                logging.error("Isolyzer exited with error(s)")

            elif imageTruncated:
                success = False
                reject = True
                logging.error("Isolyzer detected truncated ISO image")

            logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
            logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
            logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
            logging.info(''.join(['volumeIdentifier: ',
                                    str(resultIsoBuster['volumeIdentifier'])]))
            logging.info(''.join(['isolyzerSuccess: ', str(isolyzerSuccess)]))
            logging.info(''.join(['imageTruncated: ', str(imageTruncated)]))

    elif carrierInfo["containsData"] and not carrierInfo["cdInteractive"]:
        logging.info('*** Extracting data session to ISO ***')
        # Create ISO image of first session
        resultIsoBuster = isobuster.extractData(dirDisc, 1, 0)

        statusIsoBuster = resultIsoBuster["log"].strip()
        isolyzerSuccess = resultIsoBuster['isolyzerSuccess']
        imageTruncated = resultIsoBuster['imageTruncated']

        if statusIsoBuster != "0":
            success = False
            reject = True
            logging.error("Isobuster exited with error(s)")

        elif not isolyzerSuccess:
            success = False
            reject = True
            logging.error("Isolyzer exited with error(s)")

        elif imageTruncated:
            success = False
            reject = True
            logging.error("Isolyzer detected truncated ISO image")

        logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
        logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
        logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
        logging.info(''.join(['volumeIdentifier: ', str(resultIsoBuster['volumeIdentifier'])]))
        logging.info(''.join(['isolyzerSuccess: ', str(isolyzerSuccess)]))
        logging.info(''.join(['imageTruncated: ', str(imageTruncated)]))

    elif carrierInfo["cdInteractive"]:
        logging.info('*** Extracting data from CD Interactive to raw image file ***')
        resultIsoBuster = isobuster.extractCdiData(dirDisc)
        statusIsoBuster = resultIsoBuster["log"].strip()

        if statusIsoBuster != "0":
            success = False
            reject = True
            logging.error("Isobuster exited with error(s)")

        logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
        logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
        logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
    
    else:
        # We end up here if cd-info wasn't able to identify the disc
        success = False
        reject = True
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
        reject = True
        logging.error("Writing of checksum file resulted in an error")

    # Create comma-delimited batch manifest entry for this carrier

    # VolumeIdentifier only defined for ISOs, not for pure audio CDs and CD Interactive!
    if carrierInfo["containsData"]:
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
                         str(carrierInfo['containsAudio']),
                         str(carrierInfo['containsData']),
                         str(carrierInfo['cdExtra']),
                         str(carrierInfo['mixedMode']),
                         str(carrierInfo['cdInteractive'])])

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