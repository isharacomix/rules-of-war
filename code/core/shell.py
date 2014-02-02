# The Shell is where it all starts. A Shell is an abstract and thin package in
# which all of the elements of the game are stored. It is responsible for
# turning on and off graphics and then creating an instance of the main menu.
# The main menu will tell the shell when it's time to start a game, at which
# point, the shell starts passing input to the game instead.

from graphics import gfx, draw, sprites

from . import storage, session

import sys
import os
import traceback
import random
import unittest
import json

# A Shell represents a single instance of a game session with the human player.
# The shell can also initiate the game's unit tests.
class Shell(object):
    def __init__(self, *args):
        self.mode = "play"
        self.graphics = "ascii"
        
        if "--test" in args:
            self.mode = "test"
        if "--sdl" in args:
            self.graphics = "sdl"

        self.menu = None
        self.game = session.Session(json.loads(storage.read_data("maps","Intro.json")))
    
    # Runs an interactive session of our game with the player until either
    # the player stops playing or an error occurs. If a game or the main
    # menu are running, we pass input to them.
    def run(self):
        if self.mode == "test":
            gfx.start("testing")
            start = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "..","tests")
            suite = unittest.TestLoader().discover(start)
            unittest.TextTestRunner().run(suite)
            return

        # First, we try to start the graphics. If FOR ANY REASON the graphics
        # don't start, try the fallback mode. If FOR ANY REASON that fails,
        # we give up.
        try:
            gfx.start(self.graphics)
        except:
            if self.graphics == "sdl":
                self.graphics = "ascii"
            else:
                self.graphics = "sdl"
        try:
            gfx.start(self.graphics)
        except:
            print("Can't run in %d mode."%self.graphics)
            return
        gfx.clear()

        # This is the main loop. We wrap the entire thing in a try catch block
        # If FOR ANY REASON the program raises an exception, we give up, safely
        # shut down the graphics mode, and then print the error to the user in
        try:
            self.menu = sprites.Sprite(0,0,10,10)
            self.menu.fill(" ")
            self.a = sprites.Sprite(1,1,1,1)
            self.a.putc("a",0,0)
            self.menu.add_sprite(self.a)
            gfx.refresh()
            while self.menu or self.game:
                c = gfx.get_input()
                res = None
                if c == "o": self.a.move(1,0)
                if c == "i": self.a.move(-1,0)

                # If the game is running, pass input to the game. Otherwise,
                # pass input to the menu.
                if self.game:
                    res = self.game.handle_input(c)
                    self.game.render(0,0)
                    
                    if res == "quit":
                        self.game = None
                elif self.menu:
                    res = self.menu.handle_input(c)
                    self.menu.render(0,0)
                    
                    if res == "quit":
                        self.menu = None
                    elif res:
                        pass # TODO start a game yo

                gfx.refresh()
            gfx.stop()
        except:
            gfx.stop()  
            print(traceback.format_exc())
            sys.exit(-1)
        

