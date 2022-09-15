#! /usr/bin/env python3
import platform
import subprocess as sub

# Aaru binary
aaruBin = "/usr/local/bin/aaru"

# Input device
inDevice = "/dev/sdd"

# Image file name
imageFile = 'test-aaru.img'

# List with Aaru commmand line arguments
args = [aaruBin]
args.append("media")
args.append("dump")
args.append("--encoding")
args.append("utf-8")
args.append("--metadata")
if platform.system() == "Windows":
    args.append("".join([inDevice, ":"]))
elif platform.system() == "Linux":
    args.append(inDevice)
args.append(imageFile)

if platform.system() == "Linux":
    # Unmount input device
    sub.run(['umount', inDevice], shell=False)

""" Original code
# Run Aaru as subprocess
p = sub.Popen(args, shell=False)

# RESULT: Works OK from console, but when double-clicked Aaru fails
"""

""" TEST 4: as original code, but stdout, stderr redirected to null device"""
# Run Aaru as subprocess
p = sub.Popen(args, stderr=sub.DEVNULL, stdout=sub.DEVNULL, shell=False)

# RESULT: Works OK from console, but when double-clicked Aaru fails
