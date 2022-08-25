#! /usr/bin/env python3

"""Wrapper script, ensures that relative imports work correctly in a PyInstaller build"""

import platform
if platform.system() == "Windows":
    from ipmlab.configure-windows import main
elif platform.system() == "Linux":
    from ipmlab.configure-linux import main

if __name__ == '__main__':
    main()
