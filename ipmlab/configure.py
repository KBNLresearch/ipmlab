#! /usr/bin/env python3

"""Import platform-specific configuration script"""

import platform
if platform.system() == "Windows":
    from .configure_windows import main
elif platform.system() == "Linux":
    from .configure_linux import main

if __name__ == '__main__':
    main()
