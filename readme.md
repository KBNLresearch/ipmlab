# Ipmlab

## What it does

Ipmlab (Image Portable Media Like A Boss ) provides a simple and straightforward way to save the content of offline portable media from the KB collection. It supports a variety of carrier types, such as DOS/Windows formatted 3.5" floppy disks, USB thumb drives and hard drives.

For extracting the content these media, Ipmlab wraps around either [Ddrescue](https://www.gnu.org/software/ddrescue/) or [Aaru](https://www.aaru.app/) (in progress).

The media images are saved in a simple batch structure. Each batch contains a batch manifest, which is a comma-delimited text file with basic information about each carriers, such as:

- An identifier that links to a record in the KB catalogue.
- A volume number (because carriers may span multiple volumes).
- A True/False flag that indicates the status of ipmlab's imaging process.

## Using Ipmlab outside the KB

By default, Ipmlab expects each carrier to be associated with a record in the KB catalogue by means of an identifier (PPN). This identifier is then used to fetch title information from the KB catalogue using a HTTP request. This effectively constrains the use of Ipmlab to materials in the KB collection. To overcome this constraint, you can disable the PPN lookup by setting the value of *enablePPNLookup* in the configuration file to *False*. More details can be found in the [setup and configuration documentation](./doc/setupGuide.md#enableppnlookup). If *enablePPNLookup* is disabled, the *PPN* data entry widget in Ipmlab's data entry GUI is replaced with a *Title* widget, which can be used for entering a free text description of each carrier. See also the section about [Processing media that are not part of the KB collection](./doc/userGuide.md#processing-media-that-are-not-part-of-the-kb-collection) in the User Guide.

Moreover, it would be fairly straightforward to replace the PPN lookup by some alternative identifier that is linked to another catalogue/database (especially if it can be queried using HTTP-requests).

## Platform

Linux only (e.g. Ubuntu, Linux Mint, etc.).

## Wrapped software

Ipmlab wraps around either:

- [Ddrescue](https://www.gnu.org/software/ddrescue/), or
- [Aaru Data Preservation Suite](https://www.aaru.app/) (work in progress, see also [here](https://github.com/KBNLresearch/ipmlab/issues/23))

It also has a dependency on [dfxml_python](https://github.com/dfxml-working-group/dfxml_python), which must be installed separately because no PyPi package exists.

## Documentation

* [Setup Guide](./doc/setupGuide.md) - covers installation, setup and configuration.
* [User Guide](./doc/userGuide.md) - explains how to use Ipmlab.

## Contributors

Written by Johan van der Knijff, except *sru.py* which was adapted from the [KB Python API](https://github.com/KBNLresearch/KB-python-API) which is written by Willem Jan Faber, and the socket server code which  was adapted from an example in [Python Socket Communication](https://medium.com/python-pandemonium/python-socket-communication-e10b39225a4c) by Rodgers Ouma Mc'Alila.

## License

Ipmlab is released under the  Apache License 2.0. The KB Python API is released under the GNU GENERAL PUBLIC LICENSE.
