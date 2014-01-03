# This module contains high-level drawing routines that utilize the basic
# drawing functionality of the GFX module. The GFX module should be
# initialized before attempting to use this module.

from . import gfx


# This draws an individual character to the screen at the given X,Y position.
# it is essentially a wrapper around the GFX draw function.
def char(x,y,c,col=""):
    gfx.draw(x,y,c,col)


# This draws a string to the screen starting at the given X,Y position. If
# the string runs over the edge of the screen, it is truncated. All characters
# in the string have the same col.
#  TODO: make something fancier like markup or something...
def string(x,y,s,col=""):
    for c in s:
        gfx.draw(x,y,c,col)
        x += 1


# This fills a rectangle from x,y to x+w,y+h with the character c in the given
# style. If the character isn't given, space is used (so it basically clears
# the area).
def fill(x,y,w,h,c=" ",col=""):
    i = x
    while i < x+w:
        j = y
        while j < y+h:
            gfx.draw(i,j,c,col)
            j += 1
        i += 1


# This draws a border around the box defined by x,y,w,h.
def border(x,y,w,h,border="     ",col=""):
    i = x
    top,bottom,left,right,corner = border
    for i in range(x,x+w):
        gfx.draw(i,y-1,top,col)
        gfx.draw(i,y+h,bottom,col)
    for j in range(y,y+h):
        gfx.draw(x-1,j,left,col)
        gfx.draw(x+w,j,right,col)
    gfx.draw(x-1,y-1,corner,col)    
    gfx.draw(x-1,y+h,corner,col)
    gfx.draw(x+w,y+h,corner,col)
    gfx.draw(x+w,y-1,corner,col)
        
