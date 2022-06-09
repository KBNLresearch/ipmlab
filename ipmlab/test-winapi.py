import sys
import struct
import win32api
import win32file
import winioctlcon


def getDrives():
    """
    Helper function that returns
    list of all available logical drives
    """

    drives = win32api.GetLogicalDriveStrings()
    # Var drives is one string with weird 3-byte separator
    sepB = b'\x3a\x5c\x00'
    # Separator string
    sepS = sepB.decode('UTF-8')
    drives = drives.split(sepS)[:-1]

    return drives


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
        sys.stderr.write("Error, cannot access device for drive " + drive)
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


def main():
    """
    Get media type for lidt of logical Windows drive. First we
    get the drive geometry, then we use that to get
    the actual media type
    """
    
    myDrives = ["A", "C", "D", "E"]

    for drive in myDrives:
        geometry = getDriveGeometry(drive)
        mediaType = getMediaType(geometry)
        print("Media Type for drive " + drive + ": is " + mediaType)

main()