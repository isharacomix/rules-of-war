# The Game is where it all starts. A Game is an abstract and thin package in
# which all of the elements of the game are stored. It is responsible for
# creating the world, parsing and writing to save files, and turning on/off
# graphics.

from graphics import gfx, draw

from . import grid, widgets

import sys
import traceback


# A Game represents a single instance of a game, including its maps,
# data, and everything else.
class Game(object):
    def __init__(self):
        g = grid.Grid(30,10)
        self.g = grid.GridView(10,5,g)
        self.menu = widgets.Menu(["One","Two","Three","Four"])
        self.buff = widgets.Buffer(30,5)
    
    
    def display_title(self):
        gfx.clear()
        draw.string(1,1,"This is an engine","g!")
        draw.string(1,2,"One day it will be a game.","g")
        self.g.draw(3,3)
        if self.menu:
            self.menu.draw(6,6,"r")
        self.buff.draw(1,10)
    
    # Runs an interactive session of our game with the player until either
    # the player stops playing or an error occurs. Here, we pass input to the
    # world until we are told we don't need to anymore. If an error occurs, we
    # turn off graphics, print the traceback, and kill the program.
    def play(self):
        gfx.start("ascii")

        
        try:
            c = -1
            gfx.clear()
            while c != "q":
                self.display_title()
                c = gfx.get_input()
                if self.menu:
                    q = self.menu.handle_input(c)
                    if q:
                        self.menu = None
                        self.buff.write((q+" jjj a ok ")*30,"c")
                else:
                    self.g.handle_input(c)
                    if c: self.buff.write(c)

                gfx.refresh()
        except:
            gfx.stop()  
            print(traceback.format_exc())
            sys.exit(-1)
        
        gfx.stop()

