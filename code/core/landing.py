# The landing is the "main menu" of the game. Here you are able to select
# maps to begin playing!

from graphics import draw

from . import rules, grid, storage, widgets

import json


class Landing(object):
    def __init__(self, w, h):
        self.w = w
        self.h = h

        self.state = "home"
        self.options = []
        self.cursor = 0
        self.built_in = storage.list_datafiles("maps")
        self.user_defined = storage.list_files("maps")
        self.map_selection = None
        self.menu = None


    # Here we handle input based on our current state.
    def handle_input(self, c):
        if self.menu:
            q = self.menu.handle_input(c)
            if q: self.menu = None
            if q == "Edit":
                return "edit",json.loads(self.map_selection)
            if q == "Play":
                self.state = "setup"
            if q == "Back":
                self.map_selection = None
        elif self.state == "home":
            if c == "up": self.cursor -= 1
            elif c == "down": self.cursor += 1
            elif c == "q": return "quit"
            elif c == "enter":
                data = ""
                if self.cursor >= len(self.built_in):
                    i = self.cursor - len(self.built_in)
                    data = storage.read("maps",self.user_defined[i])
                else:
                    i = self.cursor
                    data = storage.read_data("maps",self.built_in[i])
                self.map_selection = data
                self.menu = widgets.Menu(["Play","Edit","Back"])
        elif self.state == "setup":
            pass

    # Here we draw our current state.
    def draw(self, x, y):
        draw.fill(0,0,self.w,self.h)
        if self.state == "home":
            draw.string(1,1,"Welcome to Rules of War!")
            draw.string(1,3,"Please select a map!")

            # Todo... correctly scroll.
            i = 0
            draw.string(40,1,"Built-in Maps","!")
            for m in self.built_in:
                col = ""
                if i == self.cursor: col = "?"
                draw.string(40,2+i,m,col)
                i += 1
            draw.string(40,3+i,"User-generated maps","!")
            for m in self.user_defined:
                col = ""
                if i == self.cursor: col = "?"
                draw.string(40,4+i,m,col)
                i += 1

        elif self.state == "setup":
            pass

        if self.menu:
            self.menu.draw(48,2+self.cursor)

        
