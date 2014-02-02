# The sprite engine makes it possible to draw things efficiently. The way
# sprites work is that a sprite contains a list of subsprites. When you call
# the "render" method, all of the subsprites.

from . import gfx, draw

from core import log

# This is a glyph that is stored in the system. A glyph is a character with
# color information, etc.
class Glyph(object):
    def __init__(self, icon=None, fg=None, bg=None, bold=False, invert=False):
        self.icon = icon
        self.fg = fg
        self.bg = bg
        self.bold = bold
        self.invert = invert

    # This mixes in another glyph into this one.
    def mix(self, other):
        newglyph = Glyph(self.icon, self.fg, self.bg, self.bold, self.invert)
        if other:
            if other.icon is not None: newglyph.icon = other.icon
            if other.fg is not None: newglyph.fg = other.fg
            if other.bg is not None: newglyph.bg = other.bg
            if other.bold is not None: newglyph.bold = other.bold
            if other.invert is not None: newglyph.invert = other.bold
        return newglyph
    
    # Returns the color string needed for gfx.draw()
    def color(self):
        s = ""
        if self.fg: s += self.fg.lower()
        if self.bg: s += self.bg.upper()
        if self.bold: s += "!"
        if self.invert: s += "?"
        return s

# Sprites are drawables that are smart enough to know when to spend time drawing
# and when to not. Sprites can contain subsprites in layers allowing them to
# serve as sprite managers.
class Sprite(object):
    def __init__(self, x, y, w, h, layer=0):
        self.reset(x, y, w, h, layer)

    # Sprites handle input and 
    def handle_input(self, c):
        pass

    # Resize deletes the image and changes the dimensions.
    def reset(self, x, y, w, h, layer=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.oldx = self.x
        self.oldy = self.y
        if layer is not None:
            self.layer = layer
        self.sprites = []
        self.surface = []
        for i in range(h):
            newarray = []
            for j in range(w):
                newarray.append(None)
            self.surface.append(newarray)
        self.dirty = True
        self.moved = True
        self.alive = True
        self.visible = True

    # This renders a sprite on the actual terminal screen starting at x,y.
    # This will pass back up a dictionary of transparent cells to the parent
    # to be drawn over.
    def render(self, x, y, bounds=None, update=None):
        if not bounds:
            bounds = ( x+self.x, y+self.y, x+self.x+self.w, y+self.y+self.h )
        
        # If any of the sprites have moved, figure out which cells need to be
        # redrawn.
        if not update:
            update = []
        if self.dirty:
            for i in range(self.w):
                for j in range(self.h):
                    update.append((i,j))
        else:
            for s in [s for s in self.sprites if s.moved or not s.alive]:
                for i in range(s.oldx,s.oldx+s.w):
                    for j in range(s.oldy,s.oldy+s.h):
                        update.append((i,j))
        
        # Now redraw the cells. This is usually a NOP since update is usually
        # empty.
        for (i,j) in update:
            dx = i+x+self.x
            dy = j+y+self.y
            if (dx >= bounds[0] and dy >= bounds[1] and i < self.w and i >= 0 and
                     j < self.h and dx < bounds[2] and dy < bounds[3] and j >= 0):
                glyph = self.surface[j][i]
                if glyph:
                    gfx.draw(dx,dy,glyph.icon,glyph.color())
        
        # Set all the sprites as no longer having been moved.
        for s in self.sprites:
            if s.visible:
                s.render(x+self.x,y+self.y, bounds, [(i-s.x,j-s.y) for (i,j) in update])
            s.moved = False
            s.dirty = False
        
        # Set this sprite as no longer dirty.
        self.dirty = False
        self.sprites = [s for s in self.sprites if s.alive]

    # This puts a character at x,y on the sprite. Returns True if it works,
    # False if the x,y was out of bounds.
    def putc(self, c, x, y, fg=None, bg=None, bold=False, invert=False):
        g = Glyph(c,fg,bg,bold,invert)
        if x >= 0 and x < self.w and y >= 0 and y < self.h:
            self.surface[y][x] = g
            self.dirty = True
            return True
        return False

    # This fills all of the glyphs with the same character.
    def fill(self, c, fg=None, bg=None, bold=False, invert=False):
        for i in range(self.w):
            for j in range(self.h):
                self.putc(c, i, j, fg, bg, bold, invert)
        self.dirty = True

    # This recolors a sprite.
    def colorize(self, fg=None, bg=None, bold=None, invert=None):
        if fg is not None:
            for g in self.surface:
                g.fg = fg
        if bg is not None:
            for g in self.surface:
                g.bg = bg
        if bold is not None:
            for g in self.surface:
                g.bold = bold
        if invert is not None:
            for g in self.surface:
                g.invert = invert
        self.dirty = True

    # This moves the sprite.
    def move(self, dx, dy, absolute=False):
        self.oldx = self.x
        self.oldy = self.y
        if absolute:
            self.x,self.y = dx,dy
        else:
            self.x += dx
            self.y += dy
        self.moved = True
        self.dirty = True
    def move_to(self, dx, dy):
        self.move(dx,dy,True)

    # This adds a sprite to the sprite manager. A sprite remains until its
    # "alive" is set to False.
    def add_sprite(self, sprite):
        self.sprites.append(sprite)
        self.sprites.sort(key=lambda s:s.layer)
        self.dirty = True
    
    # This sets a sprite and all of its subsprites as dead. They will be removed
    # from their managers in the next update.
    def kill(self):
        self.alive = False
        for s in self.sprites:
            s.kill()
        self.moved = True
        self.dirty = True
            
    # This hides a sprite.
    def hide(self):
        self.visible = False
        self.moved = True
        self.dirty = True

    # This shows a sprite.
    def show(self):
        self.visible = True
        self.moved = True
        self.dirty = True

