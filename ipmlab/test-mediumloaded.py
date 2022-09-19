import os

inDevice = "/dev/sdb1"

try:
    fd= os.open(inDevice , os.O_RDONLY)
    os.close(fd)
except(PermissionError, OSError):
    raise