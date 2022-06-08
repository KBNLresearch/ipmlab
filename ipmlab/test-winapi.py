import win32api

info = win32api.GetVolumeInformation('A:\\')

print(info)
