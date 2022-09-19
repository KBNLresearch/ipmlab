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
