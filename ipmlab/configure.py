#! /usr/bin/env python3

"""Import platform-specific configuration script"""

import platform
import sys
if platform.system() == "Linux":
    from .configure_linux import main
else:
    sys.stderr.write("ERROR: unsupported platform (only Linux is currently supported!\n")
    sys.exit(1)

if __name__ == '__main__':
    main()
