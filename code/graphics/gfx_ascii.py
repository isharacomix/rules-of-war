# The ASCII GFX module handles curses for us so that we don't have to do it
# ourselves. It's not object-oriented, so we should only ever have one game
# object trying to use it at a time. It uses a singleton screen object that
# represents the terminal window. If curses is unavailable, importing this
# module will fail, so you need to catch that when you import it.

import curses


# The "screen" used by Curses. When "None", curses is off, and all curses
# commands silently (safely) fail. This way, we can run games in non-interactive
# mode.
_screen = None


# This function turns on everything required by Curses. It puts the terminal in
# raw mode, turns of echoing, scrolling, etc. It also initializes the colors.
# This can safely be called more than once.
def start():
    global _screen
    if not _screen:
        _screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.nonl()
        _screen.keypad(1)
        _screen.timeout(0)
        _screen.scrollok(False)
        curses.start_color()
        
        i = 1
        for a in range(8):
            for b in range(8):
                curses.init_pair(i, b, a)
                i += 1

# This turns off curses and makes it safe to kill the program. You can call
# stop more than once safely. You should also be able to call start again after
# calling stop.
def stop():
    global _screen
    if _screen:
        _screen.timeout(-1)
        _screen.keypad(0)
        _screen.scrollok(True)
        curses.nocbreak()
        curses.curs_set(1)
        curses.nl()
        curses.echo()
        curses.endwin()
        _screen = None

# Return the gfx mode. This mode is curses, as opposed to SDL.
def mode():
    return "curses"

# Gets input from the user and translates it into python strings.
# Returns None if the user hasn't pressed anything. Ideally this would
# be intercepted by a keymapper object that doesn't rely on any literal
# key definitions.
_keymap ={curses.KEY_BACKSPACE: "backspace",
          curses.KEY_UP:        "up",
          curses.KEY_DOWN:      "down",
          curses.KEY_LEFT:      "left",
          curses.KEY_RIGHT:     "right",
          curses.KEY_ENTER:     "enter",
          curses.KEY_END:       "end",
          curses.KEY_HOME:      "home",
          curses.KEY_F1:        "f1",
          curses.KEY_F2:        "f2",
          curses.KEY_F3:        "f3",
          curses.KEY_F4:        "f4",
          curses.KEY_F5:        "f5",
          curses.KEY_F6:        "f6",
          curses.KEY_F7:        "f7",
          curses.KEY_F8:        "f8",
          curses.KEY_F9:        "f9",
          curses.KEY_F10:       "f10",
          curses.KEY_F11:       "f11",
          curses.KEY_F12:       "f12",
          curses.KEY_F13:       "f13",
          curses.KEY_F14:       "f14",
          curses.KEY_F15:       "f15",
          curses.KEY_RESIZE:    "resize",
          curses.KEY_PPAGE:     "page_up",
          curses.KEY_NPAGE:     "page_down",
          -1:                   None}
def get_input():
    global _screen, _keymap
    if _screen:
        c = _screen.getch()
        #curses.flushinp()
        if c == 27: return "escape"
        elif c == 10 or c == 13: return "enter"
        elif c > 0 and c < 256: return "%c"%c
        elif c in _keymap: return _keymap[c]
    return None

# In curses, refresh just controls the framerate.
def refresh():
    if _screen:
        curses.napms(20)

# Clear the screen. This uses Curses' optimized erase routine, so it's not
# necessarily inefficient.
def clear():
    global _screen
    if _screen:
        _screen.erase()

# This function returns the curses color pair for the provided color
# represented as a pair of characters. This is a private function.
#   x = black
#   r = red
#   g = green
#   y = yellow
#   b = blue
#   m = magenta
#   c = cyan
#   w = white
def _color(fg="w", bg="b"):
    fg = fg.lower()
    bg = bg.lower()
    
    if fg not in "xrgybmcw": fg = "w"
    if bg not in "xrgybmcw": bg = "x"
    
    i = "xrgybmcw".index(fg)
    j = "xrgybmcw".index(bg)
    
    if (fg,bg) == ("w","x"):
        return curses.color_pair(0)
    return curses.color_pair(1 + j*8 + i)

# Draw a character at X,Y. Includes boundary checking. You can also
# include color codes. Lowercase letters are foreground, uppercase are
# background. Use an ! for bold and ? for reverse
def draw(x,y,c,col=""):
    global _screen
    if _screen:
        h,w = _screen.getmaxyx()
        if x >= 0 and x < w and y >= 0 and y < h and (x,y)!=(w-1,h-1):
            mod = 0
            if "!" in col: mod |= curses.A_BOLD
            if "?" in col: mod |= curses.A_REVERSE
            if curses.has_colors():
                fg = "w"
                bg = "x"
                for q in "xrgybmcw":
                    if q in col: fg = q
                for q in "XRGYBMCW":
                    if q in col: bg = q
                mod |= _color(fg,bg)
            
            _screen.addch(y,x,c,mod)

