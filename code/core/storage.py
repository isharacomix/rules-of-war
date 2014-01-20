# The storage module is a platform-independent way of saving and loading
# files to certain locations.

import os

# This reads the text from a file from the home directory. Each arg is a
# folder in the filename, and will be joined as appropriate. Returns None if
# the file does not exist.
def read(*args):
    home = os.path.join(os.path.expanduser("~"),".rule-of-war")
    target = os.path.join(home, *args)
    if not os.path.exists(target):
        return None
    try:
        f = open(target,"r")
        s = f.read()
        f.close()
        return s
    except:
        return None

# This saves a file to the home directory, overwriting if appropriate.
# Returns False if something goes wrong.
def save(data, *args):
    home = os.path.join(os.path.expanduser("~"),".rule-of-war")
    targetdir = os.path.join(home, *(args[:-1]))
    target = os.path.join(home, *args)
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)
    try:
        f = open(target,"w")
        f.write(data)
        f.close()
        return True
    except:
        return False


# This reads a file from the provided data directory.
def read_data(*args):
    data = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "..","..","data")
    target = os.path.join(data, *args)
    if not os.path.exists(target):
        return None
    try:
        f = open(target,"r")
        s = f.read()
        f.close()
        return s
    except:
        return None
