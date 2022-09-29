#! /usr/bin/env python3
import io
import subprocess as sub

# Aaru binary
#aaruBin = "/usr/local/bin/aaru"
aaruBin = "/home/johan/Aaru-alpha/aaru-6.0.0-alpha3_linux_amd64/aaru"

# Input device
inDevice = "/dev/sdd"

# Image file name
imageFile = 'test-aaru.img'

# File names for aaru stdout/stderr
aarOut = 'test-aaru.stdout'
aarErr = 'test-aaru.stderr'

# List with Aaru commmand line arguments
args = [aaruBin]
args.append("media")
args.append("dump")
args.append("--encoding")
args.append("utf-8")
args.append("--metadata")
args.append("-d")
args.append(inDevice)
args.append(imageFile)

# Unmount input device
p1 = sub.Popen(['umount', inDevice], stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
output, errors = p1.communicate()

# Run Aaru as subprocess
p2 = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
output, errors = p2.communicate()

# Write stdout/stderr to file
with io.open(aarOut, "w", encoding="utf-8") as fOut:
    fOut.write(output.decode("utf-8"))
with io.open(aarErr, "w", encoding="utf-8") as fErr:
    fErr.write(errors.decode("utf-8"))

print("aaru return code: " + str(p2.returncode))