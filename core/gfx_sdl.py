# The SDL GFX module is a text-based curses-like library built on top of Pygame.
# This should be easier for windows users to utilize. We require both pygame and
# the optional Pygame font package.

import pygame
if pygame.font is None:
    raise Exception("Missing pygame.font module")

from core import log


# API:
#   start()
#   stop()
#   mode()
#   get_input()
#   clear()
#   draw(x,y,c,col)


# The "screen" used by Pygame. These private variables serve to do some of the
# optimization of Curses. The 'fakescreen' keeps track of cells that have not
# changed, and the dirty list shows all of the rectangles that should be
# updated on the screen.
_screen = None
_changes = {}
_sw, _sh, _tw, _th = 0,0,0,0


# The Start function creates a 24x80 tile surface attached to the window and
# programmatically generates a font tile for each color and boldness.
_tiles = None
_colors = { "x": (0,0,0),
            "r": (200,0,0),
            "g": (0,200,0),
            "y": (200,200,0),
            "b": (0,0,200),
            "m": (200,0,200),
            "c": (0,200,200),
            "w": (200,200,200),
    }
def start( screen_w=80, screen_h=24, tile_w=15, tile_h=30):
    global _screen, _tiles, _colors, _fakescreen, _dirty
    global _sw, _sh, _tw, _th
    if not _screen:
        pygame.init()
        pygame.key.set_repeat(500,100)
        _sw, _sh, _tw, _th = screen_w, screen_h, tile_w, tile_h
        _screen = pygame.display.set_mode((_sw*_tw, _sh*_th))
        _screen.fill((0,0,0))
        _changes = {}
        
        if _tiles is None:
            f = pygame.font.Font(None,_th-2)
            _tiles = {}
            for c in (" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"+
                      "1234567890-=\\[];',./`~!@#$%^&*()_+|{}:\"<>?"):
             for fg in "xrgybmcw":
              for bg in "xrgybmcw":
               for bold in [False,True]:
                f.set_bold(bold)
                fg_col = _colors[fg]
                bg_col = _colors[bg]
                if bold:
                    fg_col = fg_col[0]+50,fg_col[1]+50,fg_col[2]+50
                
                # Here we render the character and align it to our grid.
                s1 = f.render(c,True,fg_col,bg_col).convert()
                w,h = s1.get_size()
                w = min(w,_tw-2)
                s1 = pygame.transform.smoothscale(s1.convert(),(w,_th-2))
                s2 = pygame.Surface((_tw,_th))
                s2.fill(bg_col)
                s2.blit(s1, (_tw//2-(w//2),1) )
                
                # Store the surface in the tiles dictionary.
                _tiles[(c,fg,bg,bold)] = s2.convert()

# This turns off Pygame.
def stop():
    global _screen
    if _screen:
        pygame.quit()
        _screen = None

# Return the gfx mode. This mode is sdl, as opposed to curses.
def mode():
    return "sdl"

# Gets input from the user and translates it into python strings.
# Returns None if the user hasn't pressed anything. Ideally this would
# be intercepted by a keymapper object that doesn't rely on any literal
# key definitions. We only handle the first event in the events queue.
_keymap ={pygame.K_BACKSPACE: "backspace",
          pygame.K_UP:        "up",
          pygame.K_DOWN:      "down",
          pygame.K_LEFT:      "left",
          pygame.K_RIGHT:     "right",
          pygame.K_RETURN:    "enter",
          pygame.K_END:       "end",
          pygame.K_HOME:      "home",
          pygame.K_F1:        "f1",
          pygame.K_F2:        "f2",
          pygame.K_F3:        "f3",
          pygame.K_F4:        "f4",
          pygame.K_F5:        "f5",
          pygame.K_F6:        "f6",
          pygame.K_F7:        "f7",
          pygame.K_F8:        "f8",
          pygame.K_F9:        "f9",
          pygame.K_F10:       "f10",
          pygame.K_F11:       "f11",
          pygame.K_F12:       "f12",
          pygame.K_F13:       "f13",
          pygame.K_F14:       "f14",
          pygame.K_F15:       "f15",
          pygame.K_PAGEUP:    "page_up",
          pygame.K_PAGEDOWN:  "page_down",
          pygame.K_ESCAPE:    "escape",
          -1:                 None}
def get_input():
    global _screen, _keymap
    if _screen:
        events = pygame.event.get(pygame.KEYDOWN)
        quit = pygame.event.get(pygame.QUIT)
        others = pygame.event.get()
        
        if len(quit) > 0: return "escape"
        elif len(events) == 0: return None
        elif events[0].key in _keymap: return _keymap[events[0].key]
        else:
            try:
                return "%s"%events[0].unicode
            except:
                pass
    
    return None

# This redraws the screen and handles the framerate. Should be called once
# per game tick.
def refresh():
    global _screen, _changes, _tw, _th
    if _screen:
        pygame.time.wait(20)
        dirty = []
        
        cleared = False
        if "cleared" in _changes:
            cleared = _changes.pop("cleared")
        for x,y in _changes:
            c,col = _changes[(x,y)]
            target = pygame.Rect(x*_tw,y*_th,_tw,_th)
            bold = "!" in col
            fg = "w"
            bg = "x"
            for q in "xrgybmcw":
                if q in col: fg = q
            for q in "XRGYBMCW":
                if q in col: bg = q
            if "?" in col:
                fg,bg=bg,fg
            _screen.blit(_tiles[(c,fg,bg,bold)],target)
            dirty.append(target)
        if cleared:
            pygame.display.update()
        elif len(dirty) > 0:
            pygame.display.update(dirty)
        _changes = {}

# Clear the screen.
def clear():
    global _screen, _changes
    if _screen:
        _screen.fill((0,0,0))
        _changes = {"cleared": True}

# Draw a character at X,Y. Includes boundary checking. You can also
# include color codes. Lowercase letters are foreground, uppercase are
# background. Use an ! for bold and ? for reverse
def draw(x,y,c,col=""):
    global _screen, _changes
    if _screen:
        if _changes.get((x,y)) != (c,col):
            _changes[(x,y)] = (c,col)

