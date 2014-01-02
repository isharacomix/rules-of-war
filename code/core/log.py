# A simple global logging library to help with debugging. The log()
# function will log any strings automatically to the file as long as the
# logger has been 'toggled' on. 

import time


# The Logfile uses the following two global variables to manage logs.
logfile = None      # A python file object.
is_logging = False  # True if we are currently logging.

# This function writes to the logfile if we are currently logging. If a file
# has not been opened yet, open one with a timestamp of the time it was
# created in the name.
def log(s):
    global logfile
    global is_logging
    if is_logging:
        if not logfile:
            logfile = open("log_%d"%time.time(),"w")
        logfile.write(s+"\n")

# This toggles logging on or off, depending on the value of the flag. One
# trick you can use to prevent logging in production is to use a global DEBUG
# variable and use it for the value of the toggle command. This will prevent
# logs when DEBUG is false.
def toggle(flag):
    global is_logging
    is_logging = True if flag else False

