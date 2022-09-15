#! /usr/bin/env python3
import time
import io
import threading
import platform
import logging
import subprocess as sub
import tkinter as tk
import tkinter.scrolledtext as ScrolledText


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    
    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

class myGUI(tk.Frame):

    # This class defines the graphical user interface 
    
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.build_gui()
        
    def build_gui(self):                    
        # Build GUI
        self.root.title('TEST')
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')
        
        # Add text widget to display logging info
        st = ScrolledText.ScrolledText(self, state='disabled')
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=1, sticky='w', columnspan=4)

        # Create textLogger
        text_handler = TextHandler(st)
        
        # Logging configuration
        logging.basicConfig(filename='test.log',
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s')        
        
        # Add the handler to logger
        logger = logging.getLogger()        
        logger.addHandler(text_handler)


def dump():
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

    """Test 1: stdout + stderr to file:
    with open('ipmlab.outerr', "w") as outfile:
        sub.run(args, stderr=sub.STDOUT, stdout=outfile)

    # RESULT: Works OK from console, but when double-clicked throws:
    #  "Unhandled exception: System.Reflection.TargetInvocationException: Exception has been thrown by the target of an invocation."
    """

    """Test 2: stdout + stderr to GUI:
    p = sub.Popen(args, stderr=sub.STDOUT, stdout=sub.PIPE, shell=False)
    for line in io.TextIOWrapper(p.stdout, encoding="utf-8"):
        logging.info(line)

    # RESULT: Works OK from console, but when double-clicked throws:
    #  "Unhandled exception: System.Reflection.TargetInvocationException: Exception has been thrown by the target of an invocation."
    """

    """Test 3: as above, but shell=True
    p = sub.Popen(args, stderr=sub.STDOUT, stdout=sub.PIPE, shell=True)
    for line in io.TextIOWrapper(p.stdout, encoding="utf-8"):
        logging.info(line)

    # RESULT: from console results in "required command was not provided" (arguments not passed to Aaru), nothing happens,
    # same on double-click.
    """

    """ TEST 4: as original code, but stdout, stderr redirected to null device"""
    # Run Aaru as subprocess
    p = sub.Popen(args, stderr=sub.DEVNULL, stdout=sub.DEVNULL, shell=False)

    # RESULT: Works OK from console, but when double-clicked Aaru fails



def main():
    
    root = tk.Tk()
    myGUI(root)
    
    t1 = threading.Thread(target=dump, args=[])
    t1.start()
        
    root.mainloop()
    t1.join()
    
main()