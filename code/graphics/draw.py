# This module contains fancy actions that create new sprite objects that can
# be drawn on the screen or blitted to another sprite.

from . import sprites


# This gives you a sprite that is a single character.
def char(x,y,c,fg="w",bg="X",bold=False,invert=False,layer=0):
    report = sprites.Sprite(x,y,1,1,layer)
    report.putc(c,0,0,fg,bg,bold,invert)
    return report


# This creates a sprite for a string.
def string(x,y,s,fg="w",bg="X",bold=False,invert=False,layer=0):
    report = sprites.Sprite(x,y,len(s),1,layer)
    i = 0
    for c in s:
        report.putc(c,i,0,fg,bg,bold,invert)
        i += 1
    return report


# This fills a rectangle from x,y to x+w,y+h with the character c in the given
# style. If the character isn't given, space is used (so it basically clears
# the area).
def fill(x,y,w,h,c=" ",fg="w",bg="X",bold=False,invert=False,layer=0):
    report = sprites.Sprite(x,y,w,h,layer)
    report.fill(c,fg,bg,bold,invert)
    return report


# This draws a border around the box defined by x,y,w,h.
def border(x,y,w,h,code="--||+ ",fg="w",bg="X",bold=False,invert=False,layer=0):
    report = sprites.Sprite(x,y,w,h,layer)
    top,bottom,left,right,corner,fill = code
    report.fill(fill,fg,bg,bold,invert)
    for i in range(w):
        report.putc(top,i,0,fg,bg,bold,invert)
        report.putc(bottom,i,h-1,fg,bg,bold,invert)
    for j in range(h):
        report.putc(left,0,j,fg,bg,bold,invert)
        report.putc(right,w-1,j,fg,bg,bold,invert)
    report.putc(corner,0,0,fg,bg,bold,invert)
    report.putc(corner,0,h-1,fg,bg,bold,invert)
    report.putc(corner,w-1,0,fg,bg,bold,invert)
    report.putc(corner,w-1,h-1,fg,bg,bold,invert)
    return report
        
