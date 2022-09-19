# Cygwin setup

Download *setup-x86_64.exe* from:

<https://www.cygwin.com/install.html>

Run *setup-x86_64.exe* (needs admin rights).

Use default settings.

In *Select Packages* dialog, search for *ddrescue*, then press enter.

In the package widget, click on *All*, *Utils*. You'll see a *ddrescue* line.

In the *new* column, select the most recent (1.25-1) version of *ddrescue*. (The *Src?* column can remain unchecked).

Click through remaining install steps.

## Finding the device

In Cygwin terminal:

```
ls /dev/
```

Lists all devices.

On test VM this works when floppy drive is connected via write blocker:

```
C:\cygwin64\bin\ddrescue -b 512 -r4 -v /dev/sdb1 test.img test.map
```

And without write blocker:

```
C:\cygwin64\bin\ddrescue -b 512 -r4 -v /dev/fd1 test.img test.map
```

PROBLEM: Windows-specific code hat checks if medium is loaded only works with Window drive letters, not POSIX devices. Using the Linux-specific code instead (on the POSIX device) results in a "FileNotFoundError" (presumably because Python's os module doesn't expect POSIX devices under Windows). 


Mappings between POSIX devices and Windows mounts in Cygwin:

```
cat /proc/partitions
```

Result:

```
major minor  #blocks  name   win-mounts

    8     0  52428800 sda
    8     1    512000 sda1
    8     2  51381406 sda2   C:\
    8     3    531456 sda3
    8    16      1440 sdb
    8    17      1440 sdb1   E:\
```

So possible solution here:

- In Ipmlab config, just specify drive letter (as before)
- Then read and parse `/proc/partitions`. and derive POSIX device from that.