# Ipmlab Setup Guide

Before trying to set up Ipmlab, check if the following requirements are met:

* The installation platform is Linux-based (e.g. Unbuntu or Linux Mint). 
* Python 3.8 (or more recent) is installed on the target platform. Older 3.x versions *may* (but are not guaranteed to) work.

Getting Ipmlab up running requires a number of installation and configuration steps:

1. Update the package index
1. Add user to "disk" group
1. Disable automatic mounting of removable media
1. Install Tkinter if it is not installed already
1. Install pip if it is not installed already
1. Install Sleuthkit
1. Install either ddrescue, or the [Aaru Data Preservation Suite](https://www.aaru.app/) software (and configure it), or both (note: Aaru is not working as of yet!).
1. Install Ipmlab
1. Configure Ipmlab

Each step is described in detail below.

## Update package index

As we'll be installing a few Debian packages, it's a good idea to first update the package index, to ensure the most recent versions of all packages are installed: 

```bash
sudo apt-get update
```

## Add user to disk group

For Linux, in order to have access to block devices as a non-root user, you must add your user name to the disk group. You can do this with the command below:

```bash
sudo adduser $USER disk
```

The user is now added to the 'disk' system group. Now log out, and then log in again for the changes to take effect.

## Disable automatic mounting of removable media

In order to minimise any risks of accidental write actions to e.g. floppy disks that are processed with Ipmlab, it is strongly suggested to disable automatic mounting of removable media. The exact command depends on the Linux desktop you're using. For the [MATE](https://mate-desktop.org/) desktop use this:

```bash
gsettings set org.mate.media-handling automount false
```

For a [GNOME](https://www.gnome.org/) desktop use this command:

```bash
gsettings set org.gnome.desktop.media-handling automount false
```

And for the [Cinnamon](https://projects.linuxmint.com/cinnamon/) desktop:

```bash
gsettings set org.cinnamon.desktop.media-handling automount-open false
```

You can use the below command to verify the automount setting (MATE):

```bash
gsettings get org.mate.media-handling automount
```

Or, for GNOME:

```bash
gsettings get org.gnome.desktop.media-handling automount
```

And finally for Cinnamon:

```bash
gsettings get org.cinnamon.desktop.media-handling automount-open 
```

If all goes well, this will result in:

```
false
```

Please be aware that disabling the automount feature does not provide tamper-proof write blocking! It only works at the level of the operating system's default file manager, and it won't keep a user from manually mounting a device. Also, the *gsettings* command only works at the user level. This means that for someone who logs in with a different user name, the default automount setting applies (which means automount will be enabled).

If possible, use a forensic write blocker if more robust write-blocking is needed, but note that these devices [may not always work as expected](https://github.com/KBNLresearch/ipmlab/issues/26) for USB adapter devices (such as USB 3.5" floppy drives).

## Install Tkinter

You may need to install Tkinter, if it is not installed already. You can install it using the OS's package manager (there is no PyInstaller package for Tkinter). If you're using *apt* this should work:

```bash
sudo apt install python3-tk
```

## Install pip

You need Pip to install Python packages. Use this command to install it:

```bash
sudo apt install python3-pip

```

## Install Sleuthkit

We need Sleuthkit for extracting Dfxml metadata. To install, use:

```bash
sudo apt install sleuthkit
```

## Install Ddrescue

Install ddrescue using this command:

```bash
sudo apt install gddrescue
```

## Install Aaru

Not supported yet, coming soon!

<!--

Download the latest stable release from:

<https://github.com/aaru-dps/Aaru/releases/latest>

For 64-bit Windows you'll most likely need the *aaru-x.y.z_windows_x64.zip* package. To install, simply unpack the contents of the ZIP file to any location you like.

For 64-bit Ubuntu/linux Mint you'll most likely want to use the *aaru_x.y.z_amd64.deb* file. Install it with your favourite package manager (or just double-click on it). 

Then, run the main Aaru application without any arguments from the Windows command prompt or the Linux terminal. For example (Windows):

```
W:\aaru-5.3.1_windows_x64\aaru.exe
```

Or on Linux:

```
aaru
```

This results in some screen output like this:

```
Creating main database
Adding USB vendors
Added 3410 usb vendors
Adding USB products
Added 19812 usb products
Adding CompactDisc read offsets
Added 4630 CompactDisc read offsets
Adding known devices
Added 354 known devices
Saving changes...
```

This will create the Aaru main database. After this, Aaru prompts you for some input on how to handle encrypted and copy-protected media, and
the sharing of device reports and usage stats. Answer these questions according to your own preferences.
-->

## Install Ipmlab

The recommended way to install Ipmlab is to use *pip3*, as this will automatically install any Python packages that are used by Ipmlab (with the exception of dfxml_python, which was explained above).

For a single-user installation, install using:

```bash
pip3 install --user ipmlab
```

For a global installation (this allows all users on the machine to use Ipmlab), use this (this might require sudo privilege):

```bash
pip3 install ipmlab
```

## Configuration

Before Ipmlab is ready for use you need to configure it. 

If you installed Ipmlab as a global install, just enter:

```bash
ipmlab-configure
```

For a user install, you may need to enter the full path to the configuration script:

```bash
~/.local/bin/ipmlab-configure
```

The output should look something like this:

```
2022-11-15 16:37:53,460 - INFO - Scripts directory: /home/johan/.local/bin
2022-11-15 16:37:53,460 - INFO - Package directory: /home/johan/.local
2022-11-15 16:37:53,460 - INFO - Home directory: /home/johan
2022-11-15 16:37:53,460 - INFO - Applications directory: /home/johan/.local/share/applications/
2022-11-15 16:37:53,460 - INFO - Configuration directory: /home/johan/.config/ipmlab
2022-11-15 16:37:53,461 - INFO - Copying configuration file ...
2022-11-15 16:37:53,461 - INFO - Global site package directory: 
2022-11-15 16:37:53,461 - INFO - User site package directory: /home/johan/.local/lib/python3.8/site-packages
2022-11-15 16:37:53,461 - INFO - Site package directory: /home/johan/.local/lib/python3.8/site-packages
2022-11-15 16:37:53,461 - INFO - copied configuration file!
2022-11-15 16:37:53,461 - INFO - creating desktop file /home/johan/.local/share/applications/ipmlab.desktop
Ipmlab configuration completed successfully!
```

## Editing the configuration file

The automatically generated configuration file needs some further manual editing, which is explained in the sections below.

### Configuration file location

If you did a user install, the configuration file is located at:

```
~/.config/ipmlab/config.xml
```

For a global install, you can find it here:

```
/etc/ipmlab/config.xml
```

### Configuration variables

Now open the configuration file *config.xml* in a text editor, or, alternatively, use a dedicated XML editor. Carefully go through all the variables (which are defined as XML elements), and modify them if necessary. Here is an explanation of all variables.

#### inDevice

This defines the path to the device you want to use for imaging. You need to use a device path such as:

```xml
<inDevice>/dev/sdd</inDevice>
```

If you're not sure about the device path to use, do this:

1. Make sure the floppy drive is connected to your machine, with a floppy inserted.
2. Then issue the following command to get info about all available storage devices:

```bash
sudo lshw -short -class disk
```

Example output:

```
H/W path       Device     Class          Description
====================================================
/0/13/0.0.0    /dev/sda   disk           1TB TOSHIBA DT01ACA1
/0/14/0.0.0    /dev/sdb   disk           250GB WDC WDS250G2B0A
/0/15/0.0.0    /dev/sdc   disk           5TB Expansion HDD
/0/16/0.0.0    /dev/sdd   disk           1474KB USB-FDU
```

In the list of output devices, look for a device with a small (typically 1474 or 737 KB) storage capacity. In the example above `/dev/sdd` is the floppy drive.

#### rootDir

This defines the root directory where Ipmlab will write its data. Ipmlab output is organised into *batches*, and each batch is written to *rootDir*. Make sure to pick an existing directory with plenty of space. 

Example:

```xml
<rootDir>/home/johan/test/ipmlab-test</rootDir>
```

#### prefixBatch

This is a text prefix that is added to the automatically-generated batch names:

```xml
<prefixBatch>kb</prefixBatch>
```

#### socketHost

Defines the host address that is used if the socket API is enabled (see below). Use 127.0.0.1 for localhost:

```xml
<socketHost>127.0.0.1</socketHost>
```

#### socketPort

Defines the port that is used if the socket API is enabled (see below):

```xml
<socketPort>65432</socketPort>
```

#### enablePPNLookup

Flag that controls whether PPN lookup is enabled. If set to *True*, the Ipmlab interface contains a widget for entering a *PPN* identifier. After submitting, Ipmlab then performs a lookup on the PPN in the KB catalogue, and automatically extracts the title of the corresponding entry (which is then added to the batch manifest). If set to *False*, the Ipmlab interface contains a widget in which an operator can manually enter a *Title* string; the entered value is written to the batch manifest. In this case no PPN lookup is performed, and the PPN-value in the batch manifest will be a zero-length string.

Allowed values:

```xml
<enablePPNLookup>True</enablePPNLookup>
```

and:

```xml
<enablePPNLookup>False</enablePPNLookup>
```

#### enableSocketAPI

This is a flag that -if set to *True*- enables Ipmlab to pick up Title and PPN info from a client application through a socket interface (disabled by default):

```xml
<enableSocketAPI>False</enableSocketAPI>
```

#### fiwalkBin

This points to the location of Fiwalk binary:

```xml
<fiwalkBin>/usr/bin/fiwalk</fiwalkBin>
```

#### imagingApplication

This sets the application that is used for imaging. Allowed values are "aaru" and "ddrescue":

```xml
<imagingApplication>ddrescue</imagingApplication>
```

#### aaruBin

This points to the location of Aaru binary:

```xml
<aaruBin>/usr/bin/aaru</aaruBin>
```

#### ddrescueBin

This points to the location of ddrescue binary:

```xml
<ddrescueBin>/usr/bin/ddrescue</ddrescueBin>
```

#### blockSize

This defines the block size used by ddrescue:

```xml
<blockSize>512</blockSize>
```

#### retries

This sets the maximum number of times ddrescue will try to read an unreadable sector:

```xml
<retries>4</retries>
```
