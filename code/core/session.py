# A session is an interactive match of Rules of War between 2 or more teams.
# A session consists of multiple TEAMS each playing on a single MAP governed by
# set of RULES. The RULES and MAP are usually provided in the form of a JSON
# data file.

from . import grid

from graphics import sprites

# In theory, the game engine should be able to handle multiple sessions
# simultaneously. The session should be provided with a Dict generated from the
# JSON of a map in the following format.
#   rules: a dict containing the unit and terrain definitions
#   grid: a dict containing all of the tiles and other map variables (w,h,etc)
#   players: a list of the players, mapped to the teams in the grid
#   history: (optional) list of moves that have been played so far
class Session(object):
    def __init__(self, data):
        self.grid = grid.Grid(data["grid"], data["rules"])

        # Load the players. If a team does not have a respective player,
        # destroy that team.
        for t in self.grid.teams:
            t.active = False
        for p in data["players"]:
            pdata = data["players"][p]
            pteam = self.grid.teams[pdata["team"]]
            pteam.active = True
            pteam.name = p
        for t in [t for t in self.grid.teams if not t.active]:
            self.grid.purge(t,True)
        
        # Create the grid sprite.
        self.cursor = 0,0
        self.grid_sprite = sprites.Sprite(0,0,60,24)
        self.grid_sprite.fill(' ')
        self.grid_sprite.add_sprite(self.grid.sprite)
        self.cursor_sprite = sprites.Sprite(0,0,1,1,100)
        self.cursor_sprite.putc(None,0,0,"w","X",False,True)
        self.grid_sprite.add_sprite(self.cursor_sprite)
        self.action = None

    # This function takes the character that was most recently entered by the
    # player and handles it. Even if no player is playing, this function
    # essentially serves as the step function for the AI.
    def handle_input(self, c):
        cx,cy = self.cursor
        if c == "left"  : cx -=1
        if c == "right"  : cx +=1
        if c == "up":    cy -= 1
        if c == "down":  cy += 1
        if (self.cursor != (cx,cy)):
            self.cursor = cx,cy
            self.cursor_sprite.move_to(cx,cy)

    # The session has multiple sprites that need to be rendered, from the
    # view of the grid to the mutliple popups that need to appear.
    def render(self, x, y):
        self.grid_sprite.render(0,0)

