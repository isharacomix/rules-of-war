# The storage module is a platform-independent way of saving and loading
# files to certain locations. This module is global and functional. It contains
# NO state information.
#
# There are two data stores. The local data stored in the user's home directory
# and the global data stored in /data/ in the game's runtime location. The data
# directory must be two sublevels above this file. Information should never
# be saved in data... only in home.

import os

GAME_DIR = ".rules-of-war"

# This reads the text from a file in the home directory. Each arg is a
# folder in the filename, and will be joined as appropriate. Returns None if
# the file does not exist.
def read(*args):
    home = os.path.join(os.path.expanduser("~"),GAME_DIR)
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

# This returns a list of filenames under the provided directory.
def list_files(*args):
    home = os.path.join(os.path.expanduser("~"),GAME_DIR)
    target = os.path.join(home, *args)
    if not os.path.exists(target):
        return []
    return [ f for f in os.listdir(target)
             if os.path.isfile(os.path.join(target,f)) ]

# This saves a file to the home directory, overwriting if appropriate.
# Returns False if something goes wrong.
def save(data, *args):
    home = os.path.join(os.path.expanduser("~"),GAME_DIR)
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

# This returns a list of filenames under the provided data directory. These
# files should be considered READ ONLY.
def list_datafiles(*args):
    data = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "..","..","data")
    target = os.path.join(data, *args)
    if not os.path.exists(target):
        return []
    return [ f for f in os.listdir(target) 
             if os.path.isfile(os.path.join(target,f)) ]

