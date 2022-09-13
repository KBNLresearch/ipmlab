# Ipmlab Setup Guide

Before trying to set up Ipmlab, check if the following requirements are met:

* The installation platform is either Microsoft Windows (tested with Windows 10), or Linux-based (e.g. Unbuntu or Linux Mint). 
* Python 3.8 (or more recent) is installed on the target platform. Older 3.x versions *may* (but are not guaranteed to) work.

Getting Ipmlab up running requires a number of installation and configuration steps:

1. Add user to "disk" group (Linux only)
2. Install the [Aaru Data Preservation Suite](https://www.aaru.app/) software and configure it.
3. Install Ipmlab
4. Configure Ipmlab

Each step is described in detail below.

## Add user to disk group (Linux only)

For Linux, in order to have access to block devices as a non-root user, you must add your user name to the disk group. You can do this with the command below:

```
sudo adduser $USER disk
```

The user is now added to the 'disk' system group. Now log out, and then log in again for the changes to take effect.

## Aaru installation and configuration

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

## Ipmlab installation

The recommended way to install Ipmlab is to use *pip*. Installing with *pip* will also automatically install any Python packages that are used by Ipmlab. On Windows systems the *pip* executable is located in the *Scripts* directory which is located under Python's top-level installation folder (e.g. *C:\Python38\Scripts*). To install Ipmlab, follow the steps in either the *Global install* or *User install* subsections below.

### Global install

Follow the steps below for a global installation (this allows all users on the machine to use Ipmlab):

1. Launch a Command Prompt window or Linux terminal. Depending on your system settings, in Windows you may need Administrator privilege (right-click on the *Command Prompt* icon and the choose *Run as Administrator*).

2. For Windows, type:

   `%path-to-pip%\pip install ipmlab`

   Here, replace %path-to-pip% with the actual file bpath on your system. For example:

   `C:\Python38\Scripts\pip install ipmlab`

   For Linux, just use this:

   `pip install ipmlab`

### User install

For a single-user installation, follow these steps:

1. Launch a Command Prompt window window or Linux terminal (no admin rights required).
2. For Windows, type:

   `%path-to-pip%\pip install --user ipmlab`

   For Linux, just use this:

   `pip install --user ipmlab`

The above steps will install Ipmlab and all required libraries.

## Configuration

Before Ipmlab is ready for use you need to configure it. 

### Windows

As a first step, locate the *ipmlab-configure.exe* application. In case of a global install you can find it directly under the *Scripts* directory of the *Python* installation folder:

![](./img/ipmlab-configure-location.png)

If you did a user install, it will be somewhere in your Windows user profile (see below). The exact location depends on your local Windows configuration. As an example, in my case it is located in the folder *C:\Users\jkn010\AppData\Roaming\Python\Python38\Scripts*.

Run the configuration application by double-clicking on it. The application will create a configuration directory in your Windows user directory, copy a default configuration file to it, and create a shortcut to the main Ipmlab application on the Windows Desktop [^1]. If all goes well the following window appears:

![](./img/ipmlab-configure-1.png)

Click on the *OK* button on the messagebox to close the configuration application:

![](./img/ipmlab-configure-2.png)

#### If the configuration tool fails

If running the configuration tool doesn't have any effect (i.e. nothing happens, and no window appears, the most likely cause is a bug in the Python pywin32 module that is used by Ipmlab. A workaround can be found [here](https://github.com/KBNLresearch/iromlab/issues/100#issuecomment-594656069). (I ran into this issue myself while trying to do a user install of Iromlab under Windows 10.)

### Linux

in Linux, you can run the configuration tool from the terminal. For a global install just enter:

```
ipmlab-configure
```

For a user install you may need to enter the full path:

```
~/.local/bin/ipmlab-configure
```

Afterwards, click on the *OK* button on the messagebox to close the configuration application.

## Editing the configuration file

The automatically generated configuration file needs some further manual editing, which is explained in the sections below.

### Configuration file location

#### Windows

In Windows the configuration file is located in the User Profile directory[^2]. To find it, open a Command Prompt window and type:

```
set USERPROFILE
```

The output will be something like this:

```
USERPROFILE=C:\Users\jkn010
```

If you open this location on your machine with Window Explorer, you will find that it contains a folder named *ipmlab*:   

![](./img/userDir.png)

You will find the configuration file *config.xml* inside this folder.


#### Linux

If you did a global install, the configuration file in located at:

```
/etc/ipmlab/config.xml
```

For a user install, you can find it here:

```
~/.config/ipmlab/config.xml
```

### Configuration variables

Now open the configuration file *config.xml* in a text editor (e.g. Notepad), or, alternatively, use a dedicated XML editor. Carefully go through all the variables (which are defined as XML elements), and modify them if necessary. Here is an explanation of all variables.

#### inDevice

This defines the path to the device you want to use for imaging. Under Windows, this is a logical drive letter.  E.g. for a floppy drive this is typically *A*. If the floppy drive is connected to a write blocker it will show up under a different drive letter (e.g. *E*). In the latter case the entry in the configuration file looks like this:

```xml
<inDevice>E</inDevice>
```

(Note: do *not* add a colon to the drive letter).

In Linux you must specify *inDevice* using a device path such as:

```xml
<inDevice>/dev/sdd</inDevice>
```

If you're not sure about the device path, use the following command to get info about all available hardware devices:

```bash
sudo lshw
```

#### rootDir

This defines the root directory where Ipmlab will write its data. Ipmlab output is organised into *batches*, and each batch is written to *rootDir*. Make sure to pick an existing directory with plenty of space. 

Example:

```xml
<rootDir>E:\floppyImages</rootDir>
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
<socketPort>65432</socketPor
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

#### aaruBin

Location of Aaru binary (installation instructions for Aaru can be found [here](./setupAaru.md)). Example (Windows):

```xml
<aaruBin>W:\aaru-5.3.1_windows_x64\aaru.exe</aaruBin>
```

Or for Linux:

```xml
<aaruBin>/usr/local/bin/aaru</aaruBin>
```


[^1]: This will *not* overwrite any pre-existing configuration files.

[^2]: To be more precise: the profile of the user that installed Ipmlab (in case of multiple user profiles)

