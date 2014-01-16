# The GFX module is a wrapper around both gfx_ascii and gfx_sdl (and
# conceivably more experimental gfx libraries). It provides an interface to
# the underlying grid-based drawing system where the game doesn't need to
# think about primitive drawing functions.


# Try to import ASCII
ascii_available = False
try:
    from . import gfx_ascii
    ascii_available = True
except: pass


# Try to import SDL
sdl_available = False
try:
    from . import gfx_sdl
    sdl_available = True
except: pass


# Try to import testing
testing_available = False
try:
    from . import gfx_testing
    testing_available = True
except: pass



# API that needs to be implemented by subsystems.
#   start()
#   stop()
#   mode()
#   get_input()
#   refresh()
#   clear()
#   draw(x,y,c,col)
gfx = None
old_mode = "None"


# Start graphics. This either draws a window or sets a terminal screen. Once
# the graphics have been started, future calls to start will use the old mode.
def start(mode=None):
    global gfx, old_mode, ascii_available, sdl_available
    
    if mode is None:
        mode = old_mode
    
    if gfx and mode == old_mode: return
    elif gfx: gfx.stop()
    
    if mode == "ascii" and ascii_available: gfx = gfx_ascii
    elif mode == "sdl" and sdl_available: gfx = gfx_sdl
    elif mode == "testing" and testing_available: gfx = gfx_testing
    old_mode = mode

    if gfx:
        gfx.start()
    else:
        raise Exception("Graphics mode %s not available."%mode)

# Stop graphics. This turns off the display associated with the graphics mode.
def stop():
    global gfx
    if gfx:
        report = gfx.stop()
        gfx = None
        return report

# Returns the mode of the graphics currently running.
def mode():
    global gfx
    if gfx: return gfx.mode()
    else: return "None"

# Retrieves a single unit of input as a python string. If no input, returns
# None.
def get_input():
    global gfx
    if gfx: return gfx.get_input()

# Draws the screen and controls the framerate. Should be called exactly once
# per frame.
def refresh():
    global gfx
    if gfx: return gfx.refresh()

# Clears the screen.
def clear():
    global gfx
    if gfx: return gfx.clear()

# Draws the character 'c' at x,y with the color code provided.
#   Capital: Background
#   Lowercase: Foreground
#     x = black
#     r = red
#     g = green
#     y = yellow
#     b = blue
#     m = magenta
#     c = cyan
#     w = white
#   !: Bold
#   ?: Inverted
def draw(x,y,c,col=""):
    global gfx
    if gfx: return gfx.draw(x,y,c,col)

