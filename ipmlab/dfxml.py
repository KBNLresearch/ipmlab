#! /usr/bin/env python
"""Get DFXML output using fiwalk and write it to file"""

import os
import io
from dfxml import fiwalk
import logging

def writeDfxml(imageFile, writeDirectory):
    """Generate DFXML metadata and write to file"""

    fileOut = os.path.join(writeDirectory, "dfxml.xml")

    try:
        with open(imageFile, "rb") as ifs:
            fwOutBuffer = fiwalk.fiwalk_xml_stream(imagefile=ifs)
            fwOut = fwOutBuffer.read().decode("utf-8")
    except:
        logging.error("Error extracting Dfxml metadata")
        success = False

    try:
        with io.open(fileOut, "wb") as fOut:
            fOut.write(fwOut)
        success = True
    except:
        logging.error("Could not write Dfxml metadata to file")
        success = False

    return success