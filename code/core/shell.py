# The Shell is where it all starts. A Shell is an abstract and thin package in
# which all of the elements of the game are stored. It is responsible for
# creating the world, parsing and writing to save files, and turning on/off
# graphics.

from graphics import gfx, draw

from . import game, grid, widgets

import sys
import traceback
import random

# A Shell represents a single instance of a game, including its maps,
# data, and everything else.
class Shell(object):
    def __init__(self):
        rdict = {}
        gdict = {}
        gdict["name"] = "Hello World"
        gdict["w"] = 30
        gdict["h"] = 15
        gdict["cells"] = []
        for x in range(30):
            for y in range(15):
                cell = {}
                cell["x"] = x
                cell["y"] = y
                if random.randint(0,10)==1:
                    cell["name"] = "Mountains"
                elif random.randint(0,10)==2:
                    cell["name"] = "City"
                else:
                    cell["name"] = "Grass"
                gdict["cells"].append(cell)
        unit1 = {}
        unit1["name"] = "Infantry"
        unit1["team"] = 0
        unit2 = {}
        unit2["name"] = "Infantry"
        unit2["team"] = 1
        gdict["cells"][4]["unit"] = unit1
        gdict["cells"][40]["unit"] = unit2
        team1 = {"name":"Red","color":"r"}
        team2 = {"name":"Blue","color":"b"}
        gdict["teams"] = [team1,team2]
        rdict["grid"] = gdict
        rdict["history"] = []
        rdict["rules"] = {}
        rdict["rules"]["units"] = {}
        rdict["rules"]["units"]["Infantry"] = {}
        irules = rdict["rules"]["units"]["Infantry"]
        irules["properties"] = ["capture"]
        irules["icon"] = "i"
        irules["move"] = 3
        irules["damage"] = { "Infantry":30 }
        irules["terrain"] = { "Grass":1, "Mountains":2, "City":1}
        rdict["rules"]["terrain"] = {"Grass":{},"Mountains":{},"Ocean":{},
                                     "City":{}}
        rdict["rules"]["terrain"]["Grass"]["icon"] = "."
        rdict["rules"]["terrain"]["Grass"]["color"] = "g"
        rdict["rules"]["terrain"]["Grass"]["defense"] = 1
        rdict["rules"]["terrain"]["Grass"]["properties"] = []
        rdict["rules"]["terrain"]["Mountains"]["icon"] = "^"
        rdict["rules"]["terrain"]["Mountains"]["color"] = "y"
        rdict["rules"]["terrain"]["Mountains"]["defense"] = 3
        rdict["rules"]["terrain"]["Mountains"]["properties"] = []
        rdict["rules"]["terrain"]["Ocean"]["icon"] = "~"
        rdict["rules"]["terrain"]["Ocean"]["color"] = "b"
        rdict["rules"]["terrain"]["Ocean"]["defense"] = 0
        rdict["rules"]["terrain"]["Ocean"]["properties"] = []
        rdict["rules"]["terrain"]["City"]["icon"] = "#"
        rdict["rules"]["terrain"]["City"]["color"] = "w"
        rdict["rules"]["terrain"]["City"]["defense"] = 3
        rdict["rules"]["terrain"]["City"]["cash"] = 1000
        rdict["rules"]["terrain"]["City"]["properties"] = ["capture"]
        
        rdict['history'].append([[(0,4),(1,4),"Wait"]])

        # The most basic item is the rules.
        r = game.Game(rdict)
        self.g = grid.Controller(76,20,r)

        self.menu = None
        #self.buff = widgets.Buffer(10,5)
        #self.buff.write("Hello, world!")
    
    
    def display(self):
        #gfx.clear()
        self.g.draw(2,2)
        if self.menu:
            self.menu.draw(1,20,"r")
        #self.buff.draw(1,19)

    
    # Runs an interactive session of our game with the player until either
    # the player stops playing or an error occurs. Here, we pass input to the
    # world until we are told we don't need to anymore. If an error occurs, we
    # turn off graphics, print the traceback, and kill the program.
    def run(self):
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

