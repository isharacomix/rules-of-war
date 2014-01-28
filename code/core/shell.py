# The Shell is where it all starts. A Shell is an abstract and thin package in
# which all of the elements of the game are stored. It is responsible for
# creating the world, parsing and writing to save files, and turning on/off
# graphics.

from graphics import gfx, draw

from . import rules, grid, widgets, storage, landing

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

        self.g = None
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

        

        self.menu = None
        self.m = None
        #self.buff = widgets.Buffer(10,5)
        #self.buff.write("Hello, world!")
    
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
        
        over = False
        try:
            gfx.clear()
            while not over:
                c = gfx.get_input()
                q = None
                if self.g:
                    q = self.g.handle_input(c)
                    self.g.draw(1,1)

                    if q == "quit":
                        self.g = None
                elif self.m:
                    q = self.m.handle_input(c)
                    self.m.draw(1,1)

                    if q == "quit":
                        over = True
                        self.m = None
                    elif q:
                        mode,data = q
                        r = rules.Rules(data, mode == "edit")
                        self.g = grid.Controller(78,22,r)
                        self.m = None
                elif self.m is None:
                    self.m = landing.Landing(78,22)

                gfx.refresh()
        except:
            gfx.stop()  
            print(traceback.format_exc())
            sys.exit(-1)
        
        gfx.stop()

