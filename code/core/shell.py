# The Shell is where it all starts. A Shell is an abstract and thin package in
# which all of the elements of the game are stored. It is responsible for
# creating the world, parsing and writing to save files, and turning on/off
# graphics.

from graphics import gfx, draw

from . import rules, grid, widgets, storage

import sys
import os
import traceback
import random
import unittest
import json

# A Shell represents a single instance of a game, including its maps,
# data, and everything else.
class Shell(object):
    def __init__(self, *args):


        self.mode = "play"
        self.graphics = "ascii"
        if "--test" in args:
            self.mode = "test"
        if "--sdl" in args:
            self.graphics = "sdl"

        # IN THE FUTURE ALL OF THIS WILL NOT EXIST
        qdata = storage.read_data("maps","default.json")
        qdict = json.loads(qdata)
        qdict["players"] = {"Ishara":{"team":1,"color":"b"},
                            "Ramen":{"team":0,"color":"r"}
                           }
        r = rules.Rules(qdict)#,True)
        self.g = grid.Controller(78,22,r)

        self.menu = None
        #self.buff = widgets.Buffer(10,5)
        #self.buff.write("Hello, world!")
    
    
    def display(self):
        self.g.draw(1,1)
        if self.menu:
            self.menu.draw(1,20,"r")

    
    # Runs an interactive session of our game with the player until either
    # the player stops playing or an error occurs. Here, we pass input to the
    # world until we are told we don't need to anymore. If an error occurs, we
    # turn off graphics, print the traceback, and kill the program.
    def run(self):
        if self.mode == "test":
            gfx.start("testing")
            start = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "..","tests")
            suite = unittest.TestLoader().discover(start)
            unittest.TextTestRunner().run(suite)
            return

        try:
            gfx.start(self.graphics)
        except:
            print("Can't run in %d mode."%self.graphics)
            return
        
        try:
            c = -1
            gfx.clear()
            while c != "q" and not self.g.world.winners:
                self.display()
                c = gfx.get_input()
                if self.menu:
                    q = self.menu.handle_input(c)
                    if q:
                        self.menu = None
                else:
                    self.g.handle_input(c)

                gfx.refresh()
        except:
            gfx.stop()  
            print(traceback.format_exc())
            sys.exit(-1)
        
        gfx.stop()

