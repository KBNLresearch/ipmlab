#! /usr/bin/env python3

import os
import io
import platform
import subprocess as sub

"""Extract data to disk image"""

# Aaru binary
aaruBin = "/usr/local/bin/aaru"

# Input device
inDevice = "/dev/sdd"

# Image file name
imageFile = 'test-aaru.img'

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

# Run Aaru as subprocess
p = sub.run(args, shell=False)
