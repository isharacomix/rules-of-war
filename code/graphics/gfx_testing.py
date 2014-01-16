# The testing graphics module is a wrapper around graphics that allows us
# to simulate things like drawing and keypresses. In addition to the
# required interface, it also provides methods for adding input to a buffer
# to be returned to the caller.


# The "screen" used by Curses. When "None", curses is off, and all curses
# commands silently (safely) fail. This way, we can run games in
# non-interactive mode.
_screen = None
_buffer = []

# This function turns "on" graphics.
def start():
    global _screen
    if not _screen:
        _screen = True

# This function turns "off" graphics.
def stop():
    global _screen
    if _screen:
        _screen = None


# Return the gfx mode.
def mode():
    return "testing"


# Returns the next character in the buffer.
def get_input():
    global _screen, _buffer
    if _screen:
        if len(_buffer) > 0:
            return _buffer.pop(0)
    return None

# Dummy method.
def refresh():
    pass

# Dummy method.
def clear():
    pass

# Dummy method.
def draw(x,y,c,col=""):
    pass


# This clears the buffer of input. This should be done in setup(). You need
# to call it like "gfx.gfx.clear_buffer()"
def clear_buffer():
    global _buffer
    _buffer = []


# This adds input to the buffer. You can add input one at time or in a list.
# You need to call it like "gfx.gfx.add_to_buffer()"
def add_to_buffer(c):
    global _buffer
    if type(c) is list:
        _buffer += c
    elif type(c) is str:
        _buffer.append(c)
        

