import win32api
import struct
import win32file

info = win32api.GetVolumeInformation('A:\\')

"""Returns tuple described here:
http://timgolden.me.uk/pywin32-docs/win32api__GetVolumeInformation_meth.html

Description of tuple items here:

https://docs.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationa

 
 But nothing related to media type.

"""

print(info)


dType = win32file.GetDriveType('A:')

print(dType)

# Below code adapted from:
# https://mail.python.org/pipermail/python-list/2003-January/196146.html
# CreateFile function documented here:
# http://timgolden.me.uk/pywin32-docs/win32file__CreateFile_meth.html

hDisk = win32file.CreateFile(r'\\.\A:',
                              0,
                              win32file.FILE_SHARE_READ,
                              None,
                              win32file.OPEN_EXISTING,
                              0,
                              None)

#IOCTL_DISK_GET_DRIVE_GEOMETRY=b'0x70000'
IOCTL_DISK_GET_DRIVE_GEOMETRY = int(458752)
info = win32file.DeviceIoControl(hDisk,
                                 IOCTL_DISK_GET_DRIVE_GEOMETRY,
                                 b'0',24)
# Values = (cylinders[high],cylinders[low],media_type,
#           tracks_per_cylinder,sectors_per_track,bytes_per_sector)
values = struct.unpack('6L',info)
print(values)
mediaType = values[2]
print("Media type: " + str(mediaType))
## TODO: what doe this value mean, and can it be mapped to:
## https://docs.microsoft.com/en-us/windows/win32/api/winioctl/ne-winioctl-media_type
# 
# YES, Pywin32 enumerations here:
#
# https://github.com/SublimeText/Pywin32/blob/753322f9ac4b943c2c04ddd88605e68bc742dbb4/lib/x32/win32/lib/winioctlcon.py#L642
#
# This seems to match the '2' value for a 1.44 MB 3.5" floppy
