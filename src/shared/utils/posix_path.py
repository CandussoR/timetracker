import os
import pathlib
import platform

def get_abspath(str_path):
    if platform.system() == 'Windows':
        return pathlib.PureWindowsPath(os.path.abspath(str_path)).as_posix()
    else:
        return os.path.abspath(str_path)