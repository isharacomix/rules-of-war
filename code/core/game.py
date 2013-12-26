# The Game is where it all starts. A Game is an abstract and thin package in
# which all of the elements of the game are stored. It is responsible for
# creating the world, parsing and writing to save files, and turning on/off
# graphics.

from graphics import gfx


import sys
import traceback


# A Game represents a single instance of a game, including its maps,
# data, and everything else.
class Game(object):
    def __init__(self):
        pass
    
    
    def display_title(self):
        title = [(1,"This is an engine"),
                 (2,"One day it will be a game.")]
        
        for y,t in title:
            x = 40-len(t)//2
            q = y==1
            
            for c in t:
                gfx.draw(x,y,c,'g'+("!" if q else ""))
                x+= 1
    
    # Runs an interactive session of our game with the player until either
    # the player stops playing or an error occurs. Here, we pass input to the
    # world until we are told we don't need to anymore. If an error occurs, we
    # turn off graphics, print the traceback, and kill the program.
    def play(self):
        gfx.start("ascii")

        
        try:
            c = -1
            gfx.clear()
            while c != "enter":
                self.display_title()
                c = gfx.get_input()
                gfx.refresh()
        except:
            gfx.stop()  
            print(traceback.format_exc())
            sys.exit(-1)
        
        gfx.stop()

