# The Game is where it all starts. A Game is an abstract and thin package in
# which all of the elements of the game are stored. It is responsible for
# creating the world, parsing and writing to save files, and turning on/off
# graphics.

from graphics import gfx, draw

from . import rules, grid, widgets

import sys
import traceback


# A Game represents a single instance of a game, including its maps,
# data, and everything else.
class Game(object):
    def __init__(self):
        rdict = {}
        gdict = {}
        gdict["w"] = 30
        gdict["h"] = 15
        gdict["cells"] = []
        for x in range(30):
            for y in range(15):
                cell = {}
                cell["x"] = x
                cell["y"] = y
                cell["name"] = "grass"
                gdict["cells"].append(cell)
        unit1 = {}
        unit1["icon"] = "i"
        unit1["name"] = "Infantry"
        unit1["team"] = 0
        unit2 = {}
        unit2["icon"] = "L"
        unit2["name"] = "Artillery"
        unit2["team"] = 1
        gdict["cells"][4]["unit"] = unit1
        gdict["cells"][40]["unit"] = unit2
        team1 = {"name":"Red","color":"r"}
        team2 = {"name":"Blue","color":"b"}
        gdict["teams"] = [team1,team2]
        rdict["grid"] = gdict

        # The most basic item is the rules.
        r = rules.Rules(rdict)
        self.g = grid.Controller(70,18,r)

        self.menu = None
        self.buff = widgets.Buffer(10,5)
        self.buff.write("Hello, world!")
    
    
    def display(self):
        #gfx.clear()
        self.g.draw(1,1)
        if self.menu:
            self.menu.draw(1,20,"r")
        self.buff.draw(1,19)

    
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

