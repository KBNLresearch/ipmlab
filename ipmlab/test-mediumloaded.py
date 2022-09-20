import os
import subprocess as sub

def getPosixDevice(driveName):
    """
    Returns POSIX device name of Windows drive (Cygwin)
    May return None if drive is empty! 
    """
    ddrescueBin = os.path.normpath("C:/cygwin64/bin/ddrescue.exe")
    catBin = os.path.join(os.path.dirname(ddrescueBin), "cat.exe")

    devPosix = None

    args = [catBin]
    args.append('/proc/partitions')

    p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    out, err = p.communicate()
    outString = out.decode("utf-8")
    partList = outString.split("\n")

    pLine = 0

    for line in partList:
        items = line.strip().split()
        if pLine > 1 and len(items) == 5:
            devName = items[3]
            winMount = items[4].strip(":/\\")
            if winMount == driveName:
                devPosix = devName
        pLine += 1
    
    return devPosix

devTest = getPosixDevice("E")
print(devTest)
