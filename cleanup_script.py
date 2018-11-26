import os
import sys
import time

path = "\\devshare\devl\kdawkhar\\"
if os.path.isdir("path"):
    try:
        os.rmdir("path")
    except OSError:
        print("Unable to remove folder:")
else:
    try:
        if os.path.exists("path"):
            os.remove("path")
    except OSError:
        print("Unable to remove file")
