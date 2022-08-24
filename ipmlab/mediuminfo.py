#!/usr/bin/env python3

import sys
import struct
import platform
if platform.system() == "Windows":
    import win32api
    import win32file
    import winioctlcon

"""
Functions that retrieve media and device info on a logical
Windows drive, using Python's Windows API wrapper interface.
"""

def createFileHandle(drive):
    """
    Creates file handle for a logical Windows drive
    """

    # Low-level device name of device assigned to logical drive
    driveDevice =  "\\\\.\\" + drive + ":"

    # Create a file handle
    try:
        handle = win32file.CreateFile(driveDevice,
                                      0,
                                      win32file.FILE_SHARE_READ,
                                      None,
                                      win32file.OPEN_EXISTING,
                                      0,
                                      None)
    except:
        # Report error message if device handle cannot be created
        handle = None
        sys.stderr.write("Error, cannot access device for drive " + drive + "\n")

    return handle


def getMediaType(drive, handle):
    """
    Returns Media Type from disk geometry.

    Media types are documented here:

    https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ne-winioctl-media_type
    """

    # Initialise output variables 
    mediaType = None

    # Get media type using IOCTL_DISK_GET_DRIVE_GEOMETRY method
    try:
        diskGeometry = win32file.DeviceIoControl(handle,
                                                 winioctlcon.IOCTL_DISK_GET_DRIVE_GEOMETRY,
                                                 None,
                                                 24)

        # Extract media type from diskGeometry structure (documented here:
        # https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-disk_geometry
        # )

        offset = 8
        mediaTypeCode = struct.unpack("<I", diskGeometry[offset:offset + 4])[0]
        # Lookup corresponding media type string
        mediaType = lookupMediaType(mediaTypeCode)

    except:
        pass

    return mediaType


def getDeviceInfo(drive, handle):
    """
    
    Returns a tuple with the following items:

    - Device type string
    - A list with the media types that are supported by the device

    Media types are documented here:

    https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ne-winioctl-media_type

    and here:

    https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ne-winioctl-storage_media_type
    """

    # Initialise output variables 
    deviceType = None
    supportedMediaTypes = []

    # Get media info using IOCTL_STORAGE_GET_MEDIA_TYPES_EX method
    try:
        getMediaTypes = win32file.DeviceIoControl(handle,
                                               winioctlcon.IOCTL_STORAGE_GET_MEDIA_TYPES_EX,
                                               None,
                                               2048)

        # GET_MEDIA_TYPES structure documented here:
        # https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-get_media_types
        #

        # Device type
        deviceCode = struct.unpack("<I", getMediaTypes[0:4])[0]
        deviceType = lookupDeviceType(deviceCode)

        # Number of DEVICE_MEDIA_INFO structures to read
        mediaInfoCount = struct.unpack("<I", getMediaTypes[4:8])[0]

        # Remaining bytes are one or more 32-byte DEVICE_MEDIA_INFO structures.
        # documented here:
        #
        # https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-device_media_info
        #
        # This describes a union of 3 possible structures. Two of them  (DiskInfo, RemovableDiskInfo)
        # are identical, only TapeInfo is different (with MediaType at 0 offset instead of 8)

        offset = 8

        # Loop over DEVICE_MEDIA_INFO structures
        for _ in range(mediaInfoCount):
            if deviceCode in [31, 32]:
                # Tape device, mediaTypeCode is first item
                mediaTypeCode = struct.unpack("<I", getMediaTypes[offset:offset + 4])[0]
                offset +=8
            else:
                # Not a tape device, so skip 8 byte cylinders value
                offset += 8
                mediaTypeCode = struct.unpack("<I", getMediaTypes[offset:offset + 4])[0]

            # Lookup corresponding supported media type string and add to output list
            mediaType = lookupMediaType(mediaTypeCode)
            supportedMediaTypes.append(mediaType)
            # Skip to position of next DEVICE_MEDIA_INFO structure
            offset += 24

    except:
        pass


    return deviceType, supportedMediaTypes


def lookupDeviceType(deviceCode):
    """
    Return device type string from device code.

    Based on:

    https://github.com/mhammond/pywin32/blob/main/win32/Lib/winioctlcon.py

    (Converted original hex to decimal values)
    """
    deviceTypes = {
    1: "FILE_DEVICE_BEEP",
    2: "FILE_DEVICE_CD_ROM",
    3: "FILE_DEVICE_CD_ROM_FILE_SYSTEM",
    4: "FILE_DEVICE_CONTROLLER",
    5: "FILE_DEVICE_DATALINK",
    6: "FILE_DEVICE_DFS",
    7: "FILE_DEVICE_DISK",
    8: "FILE_DEVICE_DISK_FILE_SYSTEM",
    9: "FILE_DEVICE_FILE_SYSTEM",
    10: "FILE_DEVICE_INPORT_PORT",
    11: "FILE_DEVICE_KEYBOARD",
    12: "FILE_DEVICE_MAILSLOT",
    13: "FILE_DEVICE_MIDI_IN",
    14: "FILE_DEVICE_MIDI_OUT",
    15: "FILE_DEVICE_MOUSE",
    16: "FILE_DEVICE_MULTI_UNC_PROVIDER",
    17: "FILE_DEVICE_NAMED_PIPE",
    18: "FILE_DEVICE_NETWORK",
    19: "FILE_DEVICE_NETWORK_BROWSER",
    20: "FILE_DEVICE_NETWORK_FILE_SYSTEM",
    21: "FILE_DEVICE_NULL",
    22: "FILE_DEVICE_PARALLEL_PORT",
    23: "FILE_DEVICE_PHYSICAL_NETCARD",
    24: "FILE_DEVICE_PRINTER",
    25: "FILE_DEVICE_SCANNER",
    26: "FILE_DEVICE_SERIAL_MOUSE_PORT",
    27: "FILE_DEVICE_SERIAL_PORT",
    28: "FILE_DEVICE_SCREEN",
    29: "FILE_DEVICE_SOUND",
    30: "FILE_DEVICE_STREAMS",
    31: "FILE_DEVICE_TAPE",
    32: "FILE_DEVICE_TAPE_FILE_SYSTEM",
    33: "FILE_DEVICE_TRANSPORT",
    34: "FILE_DEVICE_UNKNOWN",
    35: "FILE_DEVICE_VIDEO",
    36: "FILE_DEVICE_VIRTUAL_DISK",
    37: "FILE_DEVICE_WAVE_IN",
    38: "FILE_DEVICE_WAVE_OUT",
    39: "FILE_DEVICE_8042_PORT",
    40: "FILE_DEVICE_NETWORK_REDIRECTOR",
    41: "FILE_DEVICE_BATTERY",
    42: "FILE_DEVICE_BUS_EXTENDER",
    43: "FILE_DEVICE_MODEM",
    44: "FILE_DEVICE_VDM",
    45: "FILE_DEVICE_MASS_STORAGE",
    46: "FILE_DEVICE_SMB",
    47: "FILE_DEVICE_KS",
    48: "FILE_DEVICE_CHANGER",
    49: "FILE_DEVICE_SMARTCARD",
    50: "FILE_DEVICE_ACPI",
    51: "FILE_DEVICE_DVD",
    52: "FILE_DEVICE_FULLSCREEN_VIDEO",
    53: "FILE_DEVICE_DFS_FILE_SYSTEM",
    54: "FILE_DEVICE_DFS_VOLUME",
    55: "FILE_DEVICE_SERENUM",
    56: "FILE_DEVICE_TERMSRV",
    57: "FILE_DEVICE_KSEC",
    58: "FILE_DEVICE_FIPS",
    59: "FILE_DEVICE_INFINIBAND",
    }

    try:
        deviceType = deviceTypes[deviceCode]
    except KeyError:
        deviceType = "Unknown"
    return deviceType


def lookupMediaType(mediaTypeCode):
    """
    Return media type string from mediaType code.

    Below dictionary maps Windows media type codes against the MEDIA_TYPE and STORAGE_MEDIA_TYPE
    output codes.
  
    Based on:

    https://github.com/mhammond/pywin32/blob/main/win32/Lib/winioctlcon.py
    """
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
        25: "F3_32M_512",
        32: "DDS_4mm",
        33: "MiniQic",
        34: "Travan",
        35: "QIC",
        36: "MP_8mm",
        37: "AME_8mm",
        38: "AIT1_8mm",
        39: "DLT",
        40: "NCTP",
        41: "IBM_3480",
        42: "IBM_3490E",
        43: "IBM_Magstar_3590",
        44: "IBM_Magstar_MP",
        45: "STK_DATA_D3",
        46: "SONY_DTF",
        47: "DV_6mm",
        48: "DMI",
        49: "SONY_D2",
        50: "CLEANER_CARTRIDGE",
        51: "CD_ROM",
        52: "CD_R",
        53: "CD_RW",
        54: "DVD_ROM",
        55: "DVD_R",
        56: "DVD_RW",
        57: "MO_3_RW",
        58: "MO_5_WO",
        59: "MO_5_RW",
        60: "MO_5_LIMDOW",
        61: "PC_5_WO",
        62: "PC_5_RW",
        63: "PD_5_RW",
        64: "ABL_5_WO",
        65: "PINNACLE_APEX_5_RW",
        66: "SONY_12_WO",
        67: "PHILIPS_12_WO",
        68: "HITACHI_12_WO",
        69: "CYGNET_12_WO",
        70: "KODAK_14_WO",
        71: "MO_NFR_525",
        72: "NIKON_12_RW",
        73: "IOMEGA_ZIP",
        74: "IOMEGA_JAZ",
        75: "SYQUEST_EZ135",
        76: "SYQUEST_EZFLYER",
        77: "SYQUEST_SYJET",
        78: "AVATAR_F2",
        79: "MP2_8mm",
        80: "DST_S",
        81: "DST_M",
        82: "DST_L",
        83: "VXATape_1",
        84: "VXATape_2",
        85: "STK_9840",
        86: "LTO_Ultrium",
        87: "LTO_Accelis",
        88: "DVD_RAM",
        89: "AIT_8mm",
        90: "ADR_1",
        91: "ADR_2",
        92: "STK_9940"
    }

    try:
        mediaType = mediaTypes[mediaTypeCode]
    except KeyError:
        mediaType = "Unknown"
    return mediaType
