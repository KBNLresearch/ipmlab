#! /usr/bin/env python3
"""
Script for automated imaging of poertable media such as
floppy discs and usb thumbdrives

Author: Johan van der Knijff
Research department,  KB / National Library of the Netherlands

"""

import sys
import os
import csv
import imp
import time
import xml.etree.ElementTree as ETree
import threading
import uuid
import logging
import platform
import queue
import tkinter as tk
from tkinter import filedialog as tkFileDialog
from tkinter import scrolledtext as ScrolledText
from tkinter import messagebox as tkMessageBox
from tkinter import ttk
from . import config
from .kbapi import sru
from .socketserver import server
from . import pmworker

__version__ = '0.2.0rc3'
config.version = __version__

class carrierEntry(tk.Frame):

    """This class defines the graphical user interface + associated functions
    for associated actions
    """

    def __init__(self, parent, *args, **kwargs):
        """Initiate class"""
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        # Logging stuff
        self.logger = logging.getLogger()
        # Create a logging handler using a queue
        self.log_queue = queue.Queue(-1)
        self.queue_handler = QueueHandler(self.log_queue)
        config.readyToStart = False
        self.catidOld = ""
        self.titleOld = ""
        self.volumeNoOld = ""
        self.carrierNumber = 0
        self.t1 = None
        self.t2 = None
        self.build_gui()

    def on_quit(self, event=None):
        """Wait until the medium that is currently being pocessed has
        finished, and quit (batch can be resumed by opening it in the File dialog)
        """
        config.quitFlag = True
        self.bQuit.config(state='disabled')
        if config.batchIsOpen:
            msg = 'User pressed Quit, quitting after current medium has been processed'
            tkMessageBox.showinfo("Info", msg)

        msg = 'User pressed Quit, click OK to close ipmlab'

        if not config.readyToStart:
            # User hasn't yet created or opened a batch
            time.sleep(2)
            tkMessageBox.showinfo("Quit", msg)
            os._exit(0)
        else:
            # User has created or opened a batch
            # Wait until processingMedium flag is reset to False
            while config.processingMedium:
                time.sleep(2)
            # Wait 1 more second to avoid race condition
            time.sleep(2)

            handlers = self.logger.handlers[:]

            for handler in handlers:
                handler.close()
                self.logger.removeHandler(handler)

            msg = 'User pressed Quit, click OK to close ipmlab'
            tkMessageBox.showinfo("Quit", msg)
            os._exit(0)


    def on_create(self, event=None):
        """Create new batch in rootDir"""

        # Create unique batch identifier (UUID, based on host ID and current time)
        # this ensures that if the software is run in parallel on different machines
        # the batch identifiers will always be unique
        batchID = str(uuid.uuid1())

        # Construct batch name
        batchName = config.prefixBatch + '-' + batchID
        config.batchFolder = os.path.join(config.rootDir, batchName)
        try:
            os.makedirs(config.batchFolder)
        except IOError:
            msg = 'Cannot create batch folder ' + config.batchFolder
            tkMessageBox.showerror("Error", msg)

        # Write Ipmlab version to file in batch
        versionFile = os.path.join(config.batchFolder, 'version.txt')
        with open(versionFile, "w") as vf:
            vf.write(config.version + '\n')

        # Define batch manifest (CSV file with minimal metadata on each carrier)
        config.batchManifest = os.path.join(config.batchFolder, 'manifest.csv')

        # Write header row if batch manifest doesn't exist already
        if not os.path.isfile(config.batchManifest):
            headerBatchManifest = (['jobID',
                                    'PPN',
                                    'volumeNo',
                                    'title',
                                    'success',
                                    'readErrors'])

        # Open batch manifest in append mode
        bm = open(config.batchManifest, "a", encoding="utf-8")

        # Create CSV writer object
        csvBm = csv.writer(bm, lineterminator='\n')

        # Write header to batch manifest and close file
        csvBm.writerow(headerBatchManifest)
        bm.close()

        # Set up logging
        successLogger = True

        try:
            self.setupLogger()
            # Start polling log messages from the queue
            self.after(100, self.poll_log_queue)
        except OSError:
            # Something went wrong while trying to write to lof file
            msg = ('error trying to write log file')
            tkMessageBox.showerror("ERROR", msg)
            successLogger = False

        if successLogger:
            # Notify user
            msg = 'Created batch ' + batchName
            tkMessageBox.showinfo("Created batch", msg)
            logging.info(''.join(['batchFolder set to ', config.batchFolder]))

            # Update state of buttons / widgets
            self.bNew.config(state='disabled')
            self.bOpen.config(state='disabled')
            self.bFinalise.config(state='normal')
            if config.enablePPNLookup:
                self.catid_entry.config(state='normal')
                self.usepreviousPPN_button.config(state='normal')
            else:
                self.title_entry.config(state='normal')
                self.usepreviousTitle_button.config(state='normal')
            self.volumeNo_entry.config(state='normal')
            self.volumeNo_entry.delete(0, tk.END)
            self.volumeNo_entry.insert(tk.END, "1")
            self.submit_button.config(state='normal')

            # Flag that is True if batch is open
            config.batchIsOpen = True
            # Set readyToStart flag to True,
            config.readyToStart = True


    def on_open(self, event=None):
        """Open existing batch"""

        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = config.rootDir
        options['mustexist'] = True
        options['parent'] = self.root
        options['title'] = 'Select batch directory'
        config.batchFolder = tkFileDialog.askdirectory(**self.dir_opt)
        config.batchManifest = os.path.join(config.batchFolder, 'manifest.csv')

        # Set up logging
        successLogger = True

        try:
            self.setupLogger()
            # Start polling log messages from the queue
            self.after(100, self.poll_log_queue)
        except OSError:
            # Something went wrong while trying to write to lof file
            msg = ('error trying to write log file')
            tkMessageBox.showerror("ERROR", msg)
            successLogger = False

        if successLogger:
            logging.info(''.join(['*** Opening existing batch ', config.batchFolder, ' ***']))

            if config.batchFolder != '':

                # Update state of buttons /widgets, taking into account whether batch was
                # finalized by user
                self.bNew.config(state='disabled')
                self.bOpen.config(state='disabled')
                self.submit_button.config(state='normal')
                self.bFinalise.config(state='normal')
                if config.enablePPNLookup:
                    self.catid_entry.config(state='normal')
                    self.usepreviousPPN_button.config(state='normal')
                else:
                    self.title_entry.config(state='normal')
                    self.usepreviousTitle_button.config(state='normal')
                self.volumeNo_entry.config(state='normal')
                self.volumeNo_entry.delete(0, tk.END)
                self.volumeNo_entry.insert(tk.END, "1")

                # Flag that is True if batch is open
                config.batchIsOpen = True
                # Set readyToStart flag to True
                config.readyToStart = True

    def on_finalise(self, event=None):
        """Finalise batch after user pressed finalise button"""
        msg = ("This will finalise the current batch.\n After finalising no further "
               "media can be added. Are you sure you want to do this?")
        if tkMessageBox.askyesno("Confirm", msg):
            self.bFinalise.config(state='disabled')
            self.submit_button.config(state='disabled')
            if config.enablePPNLookup:
                self.catid_entry.config(state='disabled')
                self.usepreviousPPN_button.config(state='disabled')
            else:
                self.title_entry.config(state='disabled')
                self.usepreviousTitle_button.config(state='disabled')
            self.volumeNo_entry.delete(0, tk.END)
            self.volumeNo_entry.config(state='disabled')

            # Wait until processingMedium flag is reset to False
            while config.processingMedium:
                time.sleep(2)
            
            config.readyToStart = False
            config.finishedBatch = True

            handlers = self.logger.handlers[:]
            for handler in handlers:
                handler.close()
                self.logger.removeHandler(handler)
            # Notify user
            msg = 'Finished processing this batch'
            tkMessageBox.showinfo("Finished", msg)
            # Reset the GUI
            self.reset_gui()

    def on_usepreviousPPN(self, event=None):
        """Add previously entered PPN to entry field"""
        if self.catidOld == "":
            msg = "Previous PPN is not defined"
            tkMessageBox.showerror("PPN not defined", msg)
        else:
            self.catid_entry.delete(0, tk.END)
            self.catid_entry.insert(tk.END, self.catidOld)
            if self.volumeNoOld != "":
                # Increase volume number value
                volumeNoNew = str(int(self.volumeNoOld) + 1)
                self.volumeNo_entry.delete(0, tk.END)
                self.volumeNo_entry.insert(tk.END, volumeNoNew)

    def on_usepreviousTitle(self, event=None):
        """Add previously entered title to title field"""
        if self.titleOld == "":
            msg = "Previous title is not defined"
            tkMessageBox.showerror("Tile not defined", msg)
        else:
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(tk.END, self.titleOld)
            if self.volumeNoOld != "":
                volumeNoNew = str(int(self.volumeNoOld) + 1)
                self.volumeNo_entry.delete(0, tk.END)
                self.volumeNo_entry.insert(tk.END, volumeNoNew)

    def on_submit(self, event=None):
        """Process one record and add it to the queue after user pressed submit button"""

        config.processingMedium = True
        mediumLoaded = False

        # Fetch entered values (strip any leading / tralue whitespace characters)
        if config.enablePPNLookup:
            catid = self.catid_entry.get().strip()
            self.catidOld = catid
        else:
            catid = ""
            title = self.title_entry.get().strip()
            self.titleOld = title
        volumeNo = self.volumeNo_entry.get().strip()
        self.volumeNoOld = volumeNo

        if config.enablePPNLookup:
            # Check for empty string
            if str(catid) == '':
                noGGCRecords = 0
            else:
                # Lookup catalog identifier
                sruSearchString = 'OaiPmhIdentifier="GGC:AC:' + str(catid) + '"'
                response = sru.search(sruSearchString, "GGC")

                if not response:
                    noGGCRecords = 0
                else:
                    noGGCRecords = response.sru.nr_of_records
        else:
            noGGCRecords = 1

        if not config.batchIsOpen:
            msg = "You must first create a batch or open an existing batch"
            tkMessageBox.showerror("Not ready", msg)
        elif not representsInt(volumeNo):
            msg = "Volume number must be integer value"
            tkMessageBox.showerror("Type mismatch", msg)
        elif int(volumeNo) < 1:
            msg = "Volume number must be greater than or equal to 1"
            tkMessageBox.showerror("Value error", msg)
        elif noGGCRecords == 0:
            # No matching record found
            msg = ("Search for PPN=" + str(catid) + " returned " +
                   "no matching record in catalog!")
            tkMessageBox.showerror("PPN not found", msg)
        else:
            if config.enablePPNLookup:
                # Matching record found. Display title and ask for confirmation
                record = next(response.records)

                # Title can be in either in:
                # 1. title element
                # 2. title element with maintitle attribute
                # 3. title element with intermediatetitle attribute (3 in combination with 2)

                titlesMain = record.titlesMain
                titlesIntermediate = record.titlesIntermediate
                titles = record.titles

                if titlesMain != []:
                    title = titlesMain[0]
                    if titlesIntermediate != []:
                        title = title + ", " + titlesIntermediate[0]
                else:
                    title = titles[0]

            msg = "Found title:\n\n'" + title + "'.\n\n Is this correct?"
            if tkMessageBox.askyesno("Confirm", msg):
                msg = ("Please load medium ('" + title + "', volume " + str(volumeNo) +
                       ") and press 'OK'")
                tkMessageBox.showinfo("Load medium", msg)

                if platform.system() == "Windows":
                    while not mediumLoaded:
                        try:
                            _ = os.listdir(config.inDevice + ":\\")
                            mediumLoaded = True
                        except(PermissionError, OSError):
                            msg = ("No medium found, please load medium and press 'OK'")
                            tkMessageBox.showinfo("Load medium", msg)

                elif platform.system() == "Linux":
                    while not mediumLoaded:
                        try:
                            fd= os.open(config.inDevice , os.O_RDONLY)
                            os.close(fd)
                            mediumLoaded = True
                        except(PermissionError, OSError):
                            msg = ("No medium found, please load medium and press 'OK'")
                            tkMessageBox.showinfo("Load medium", msg)

                # Create unique identifier for this job (UUID, based on host ID and current time)
                jobID = str(uuid.uuid1())

                # Update carrierNumber (only used to indicate order of all media in batch in widget)
                self.carrierNumber += 1

                # Set up dictionary that holds carrier data
                carrierData = {}
                carrierData['jobID'] = jobID
                carrierData['PPN'] = catid
                carrierData['title'] = title
                carrierData['volumeNo'] = volumeNo

                # Display PPN/Title + Volume number in treeview widget
                self.tv.insert('', 0, text=str(self.carrierNumber), values=(catid, title, volumeNo))

                if config.enablePPNLookup:
                    self.catid_entry.config(state='disabled')
                    self.usepreviousPPN_button.config(state='disabled')
                else:
                    self.title_entry.config(state='disabled')
                    self.usepreviousTitle_button.config(state='disabled')

                self.volumeNo_entry.config(state='disabled')
                self.submit_button.config(state='disabled')
                
                # Process carrier in separate thread
                self.t1 = threading.Thread(target=pmworker.processMedium, args=[carrierData])
                self.t1.start()
            
            else:
                # Clear entry fields
                if config.enablePPNLookup:
                    self.catid_entry.delete(0, tk.END)
                else:
                    self.title_entry.delete(0, tk.END)
                
                self.volumeNo_entry.delete(0, tk.END)


    def setupLogger(self):
        """Set up logging-related settings"""
        logFile = os.path.join(config.batchFolder, 'batch.log')

        logging.basicConfig(handlers=[logging.FileHandler(logFile, 'a', 'utf-8')],
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Add the handler to logger
        self.logger = logging.getLogger()
        # This sets the console output format (slightly different from basicConfig!)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        self.logger.addHandler(self.queue_handler)


    def display(self, record):
        """Display log record in scrolledText widget"""
        msg = self.queue_handler.format(record)
        self.st.configure(state='normal')
        self.st.insert(tk.END, msg + '\n', record.levelname)
        self.st.configure(state='disabled')
        # Autoscroll to the bottom
        self.st.yview(tk.END)


    def poll_log_queue(self):
        """Check every 100ms if there is a new message in the queue to display"""
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.after(100, self.poll_log_queue)


    def build_gui(self):
        """Build the GUI"""

        # Read configuration file
        configFileDefinedFlag, configFileExistsFlag, configFileOpenFlag, configFileParsedFlag = getConfiguration()

        self.root.title('ipmlab v.' + config.version)
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')

        # Batch toolbar
        self.bNew = tk.Button(self,
                              text="New",
                              height=2,
                              width=4,
                              underline=0,
                              command=self.on_create)
        self.bNew.grid(column=0, row=1, sticky='ew')
        self.bOpen = tk.Button(self,
                               text="Open",
                               height=2,
                               width=4,
                               underline=0,
                               command=self.on_open)
        self.bOpen.grid(column=1, row=1, sticky='ew')
        self.bFinalise = tk.Button(self,
                                   text="Finalize",
                                   height=2,
                                   width=4,
                                   underline=0,
                                   command=self.on_finalise)
        self.bFinalise.grid(column=2, row=1, sticky='ew')
        self.bQuit = tk.Button(self,
                               text="Quit",
                               height=2,
                               width=4,
                               underline=0,
                               command=self.on_quit)
        self.bQuit.grid(column=3, row=1, sticky='ew')

        # Disable finalise button on startup
        self.bFinalise.config(state='disabled')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=2, columnspan=4, sticky='ew')

        # Entry elements for each carrier

        if config.enablePPNLookup:
            # Catalog ID (PPN)
            tk.Label(self, text='PPN').grid(column=0, row=3, sticky='w')
            self.catid_entry = tk.Entry(self, width=20, state='disabled')

            # Pressing this button adds previously entered PPN to entry field
            self.usepreviousPPN_button = tk.Button(self,
                               text='Use previous',
                               height=1,
                               width=2,
                               underline=0,
                               state='disabled',
                               command=self.on_usepreviousPPN)
            self.usepreviousPPN_button.grid(column=2, row=3, sticky='ew')

            self.catid_entry.grid(column=1, row=3, sticky='w')
        else:
            # PPN lookup disabled, so present Title entry field
            tk.Label(self, text='Title').grid(column=0, row=3, sticky='w')
            self.title_entry = tk.Entry(self, width=45, state='disabled')

            # Pressing this button adds previously entered title to entry field
            self.usepreviousTitle_button = tk.Button(self,
                               text='Use previous',
                               height=1,
                               width=2,
                               underline=0,
                               state='disabled',
                               command=self.on_usepreviousTitle)
            self.usepreviousTitle_button.grid(column=3, row=3, sticky='ew')
            self.title_entry.grid(column=1, row=3, sticky='w', columnspan=3)

        # Volume number
        tk.Label(self, text='Volume number').grid(column=0, row=4, sticky='w')
        self.volumeNo_entry = tk.Entry(self, width=5, state='disabled')
        
        self.volumeNo_entry.grid(column=1, row=4, sticky='w')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=5, columnspan=4, sticky='ew')

        self.submit_button = tk.Button(self,
                                       text='Submit',
                                       height=2,
                                       width=4,
                                       underline=0,
                                       state='disabled',
                                       command=self.on_submit)
        self.submit_button.grid(column=1, row=6, sticky='ew')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=7, columnspan=4, sticky='ew')

        # Treeview widget displays info on entered carriers
        self.tv = ttk.Treeview(self, height=10,
                               columns=('PPN', 'Title', 'VolumeNo'))
        self.tv.heading('#0', text='Queue #')
        self.tv.heading('#1', text='PPN')
        self.tv.heading('#2', text='Title')
        self.tv.heading('#3', text='Volume #')
        self.tv.column('#0', stretch=tk.YES, width=5)
        self.tv.column('#1', stretch=tk.YES, width=10)
        self.tv.column('#2', stretch=tk.YES, width=250)
        self.tv.column('#3', stretch=tk.YES, width=5)
        self.tv.grid(column=0, row=8, sticky='ew', columnspan=4)

        # ScrolledText widget displays logging info
        self.st = ScrolledText.ScrolledText(self, state='disabled', height=15)
        self.st.configure(font='TkFixedFont')
        self.st.grid(column=0, row=10, sticky='ew', columnspan=4)

        # Define bindings for keyboard shortcuts: buttons
        self.root.bind_all('<Control-Key-n>', self.on_create)
        self.root.bind_all('<Control-Key-o>', self.on_open)
        self.root.bind_all('<Control-Key-f>', self.on_finalise)
        self.root.bind_all('<Control-Key-q>', self.on_quit)
        self.root.bind_all('<Control-Key-s>', self.on_submit)

        # TODO keyboard shortcuts for Radiobox selections: couldn't find ANY info on how to do this!

        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)

        # Display message and exit if config file is either undefined, doesn't exist, cannot
        # be opened or cannot be parsed
        
        if not configFileDefinedFlag:
            msg = "configuration file is undefined"
            errorExit(msg)
        if not configFileExistsFlag:
            msg = "configuration file doesn't exist"
            errorExit(msg)
        if not configFileOpenFlag:
            msg = "configuration file cannot be opened"
            errorExit(msg)
        if not configFileParsedFlag:
            msg = "unable to parse configuration file"
            errorExit(msg)

        # Check if all files and directories exist, and exit if not
        if config.imagingApplication == "aaru":
            if not os.path.isfile(config.aaruBin):
                msg = "Aaru binary " + config.aaruBin + " does not exist"
                errorExit(msg)
        elif config.imagingApplication == "ddrescue":
                if not os.path.isfile(config.ddrescueBin):
                    msg = "Ddrescue binary " + config.ddrescueBin + " does not exist"
                    errorExit(msg)
        else:
            msg = config.imagingApplication + " is not a recognized imagingApplication value"
            errorExit(msg)

        if not os.path.isdir(config.rootDir):
            msg = "root directory " + config.rootDir + " does not exist"
            errorExit(msg)            

    def reset_carrier(self):
        """Reset the carrier entry fields"""
        # Reset and ere-enable entry fields, and set focus on PPN / Title field

        if config.enablePPNLookup:
            self.usepreviousPPN_button.config(state='normal')
            self.catid_entry.config(state='normal')
            self.catid_entry.delete(0, tk.END)
            self.catid_entry.focus_set()
        else:
            self.title_entry.config(state='normal')
            self.usepreviousTitle_button.config(state='normal')
            self.title_entry.delete(0, tk.END)
            self.title_entry.focus_set()

        self.volumeNo_entry.config(state='normal')
        self.submit_button.config(state='normal')
        self.volumeNo_entry.delete(0, tk.END)
        self.volumeNo_entry.insert(tk.END, "1")

    def reset_gui(self):
        """Reset the GUI"""
        # Reset carrierNumber
        self.carrierNumber = 0
        # Clear items in treeview widget
        tvItems = self.tv.get_children()
        for item in tvItems:
           self.tv.delete(item)
        # Clear contents of ScrolledText widget
        # Only works if state is 'normal'
        self.st.config(state='normal')
        self.st.delete(1.0, tk.END)
        self.st.config(state='disabled')
        # Logging stuff
        self.logger = logging.getLogger()
        # Create a logging handler using a queue
        self.log_queue = queue.Queue(-1)
        self.queue_handler = QueueHandler(self.log_queue)
        config.readyToStart = False
        self.catidOld = ""
        self.titleOld = ""
        self.volumeNoOld = ""

        # Update state of buttons / widgets
        self.bNew.config(state='normal')
        self.bOpen.config(state='normal')
        self.bFinalise.config(state='disabled')
        self.bQuit.config(state='normal')
        self.submit_button.config(state='disabled')
        if config.enablePPNLookup:
            self.catid_entry.config(state='disabled')
            self.usepreviousPPN_button.config(state='disabled')
        else:
            self.title_entry.config(state='disabled')
            self.usepreviousTitle_button.config(state='disabled')
        self.volumeNo_entry.config(state='disabled')

    def handleSocketRequests(self, q):
        """ Update contents of PPN and Title widgets on incoming requests from socket interface
        """
        try:
            message = q.get_nowait()
            if config.enablePPNLookup:
                try:
                    catid = message
                    self.catid_entry.delete(0, tk.END)
                    self.catid_entry.insert(tk.END, catid)
                    if catid == self.catidOld and catid != "":
                        # Increase volume number value if existing catid
                        volumeNoNew = str(int(self.volumeNoOld) + 1)
                        self.volumeNo_entry.delete(0, tk.END)
                        self.volumeNo_entry.insert(tk.END, volumeNoNew)
                except:
                    # TODO: catch more specific errors here?
                    pass
            else:
                try:
                    title = message
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.insert(tk.END, title)
                    if title == self.titleOld and title != "":
                        # Increase volume number value if existing catid
                        volumeNoNew = str(int(self.volumeNoOld) + 1)
                        self.volumeNo_entry.delete(0, tk.END)
                        self.volumeNo_entry.insert(tk.END, volumeNoNew)
                except:
                    # TODO: catch more specific errors here?
                    pass
        except queue.Empty:
            pass

class QueueHandler(logging.Handler):
    """Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    Taken from https://github.com/beenje/tkinter-logging-text-widget/blob/master/main.py
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


def representsInt(s):
    """Return True if s is an integer, False otherwise"""
    # Source: http://stackoverflow.com/a/1267145
    try:
        int(s)
        return True
    except ValueError:
        return False


def errorExit(error):
    """Show error message in messagebox and then exit after userv presses OK"""
    tkMessageBox.showerror("Error", error)
    sys.exit()


def main_is_frozen():
    """Return True if application is frozen (Py2Exe), and False otherwise"""
    return (hasattr(sys, "frozen") or  # new py2exe
            hasattr(sys, "importers") or  # old py2exe
            imp.is_frozen("__main__"))  # tools/freeze


def get_main_dir():
    """Return application (installation) directory"""
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])


def findElementTextOld(elt, elementPath):
    """Returns element text if it exists, errorExit if it doesn't exist"""
    elementText = elt.findtext(elementPath)
    if elementText is None:
        msg = 'no element found at ' + elementPath
        errorExit(msg)
    else:
        return elementText

def findElementText(elt, elementPath):
    """Returns element text if it exists, errorExit if it doesn't exist"""
    elementText = elt.findtext(elementPath)
    if elementText is None:
        elementText = ""
    return elementText

def getConfiguration():
    """ Read configuration file, make all config variables available via
    config.py and check that all file paths / executables exist.
    This assumes an non-frozen script (no Py2Exe!)
    """

    configFileDefinedFlag = False
    configFileExistsFlag = False
    configFileOpenFlag = False
    configFileParsedFlag = False


    if platform.system() == "Windows":
        # Locate Windows profile directory
        userDir = os.environ['USERPROFILE']
        # Locate package directory
        packageDir = os.path.dirname(os.path.abspath(__file__))
        # Config directory
        configDirUser = os.path.join(userDir, 'ipmlab')
        configFileUser = os.path.join(configDirUser, 'config.xml')
        configFileDefinedFlag = True
    elif platform.system() == "Linux":
        packageDir = os.path.dirname(os.path.abspath(__file__))
        homeDir = os.path.normpath(os.path.expanduser("~"))
        if packageDir.startswith(homeDir):
            configFileUser = os.path.join(homeDir, '.config/ipmlab/config.xml')
        else:
            configFileUser = os.path.normpath('/etc/ipmlab/config.xml')
        configFileDefinedFlag = True

    # Check if user config file exists and exit if not
    if os.path.isfile(configFileUser):
        configFileExistsFlag = True

    # Read contents to bytes object
    if configFileExistsFlag:
        try:
            fConfig = open(configFileUser, "rb")
            configBytes = fConfig.read()
            fConfig.close()
            configFileOpenFlag = True
        except IOError:
            pass

    # Parse XML tree
    if configFileOpenFlag:
        try:
            root = ETree.fromstring(configBytes)
            configFileParsedFlag = True
        except Exception:
            pass

    if configFileParsedFlag:

        # Create empty element object & add config contents to it
        # A bit silly but allows use of findElementText in etpatch

        configElt = ETree.Element("bogus")
        configElt.append(root)

        config.inDevice = findElementText(configElt, './config/inDevice')
        config.rootDir = findElementText(configElt, './config/rootDir')
        config.prefixBatch = findElementText(configElt, './config/prefixBatch')
        config.imagingApplication = findElementText(configElt, './config/imagingApplication')
        config.aaruBin = findElementText(configElt, './config/aaruBin')
        config.ddrescueBin = findElementText(configElt, './config/ddrescueBin')
        config.blockSize = findElementText(configElt, './config/blockSize')
        config.retries = findElementText(configElt, './config/retries')
    
        # For below configuration variables, use default value if value cannot be
        # read from config file (this ensures v1 will work with old config files)
        try:
            config.socketHost = findElementText(configElt, './config/socketHost')
        except:
            pass
        try:
            config.socketPort = findElementText(configElt, './config/socketPort')
        except:
            pass
        try:
            if findElementText(configElt, './config/enablePPNLookup') == "True":
                config.enablePPNLookup = True
            else:
                config.enablePPNLookup = False
        except:
            pass
        try:
            if findElementText(configElt, './config/enableSocketAPI') == "True":
                config.enableSocketAPI = True
            else:
                config.enableSocketAPI = False
        except:
            pass

        # Normalise all file paths
        config.rootDir = os.path.normpath(config.rootDir)
        config.aaruBin = os.path.normpath(config.aaruBin)
        config.ddrescueBin = os.path.normpath(config.ddrescueBin)

    return configFileDefinedFlag, configFileExistsFlag, configFileOpenFlag, configFileParsedFlag


def main():
    """Main function"""
    config.version = __version__
    root = tk.Tk()
    myCarrierEntry = carrierEntry(root)
    # This ensures application quits normally if user closes window
    root.protocol('WM_DELETE_WINDOW', myCarrierEntry.on_quit)
    # Start socket API as separate thread
    if config.enableSocketAPI:
        q = queue.Queue()
        myServer = server()
        myCarrierEntry.t2 = threading.Thread(target=server.start,
                                             args=[myServer,
                                             config.socketHost,
                                             config.socketPort,
                                             q])
        myCarrierEntry.t2.start()

    while True:
        if config.enableSocketAPI:
            myCarrierEntry.handleSocketRequests(q)
        root.update_idletasks()
        root.update()
        time.sleep(0.1)
        if config.finishedMedium:
            myCarrierEntry.t1.join()
            # Prompt operator to remove medium
            msg = ("Please remove the medium, then press 'OK'")
            tkMessageBox.showinfo("Remove medium", msg)
            myCarrierEntry.reset_carrier()
            config.processingMedium = False
            config.finishedMedium = False


if __name__ == "__main__":
    main()
