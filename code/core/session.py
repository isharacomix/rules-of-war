# A session is an interactive match of Rules of War between 2 or more teams.
# A session consists of multiple TEAMS each playing on a single MAP governed by
# set of RULES. The RULES and MAP are usually provided in the form of a JSON
# data file.

from . import grid, rules, widgets

from graphics import sprites, draw

import copy

# In theory, the game engine should be able to handle multiple sessions
# simultaneously. The session should be provided with a Dict generated from the
# JSON of a map in the following format.
#   rules: a dict containing the unit and terrain definitions
#   grid: a dict containing all of the tiles and other map variables (w,h,etc)
#   players: a list of the players, mapped to the teams in the grid
#   history: (optional) list of moves that have been played so far
class Session(object):
    def __init__(self, data):
        self.data = data
        self.grid = grid.Grid(data["grid"], data["rules"])
        self.w = 60
        self.h = 23

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
            t.name = "---"
            self.grid.purge(t,True)
        
        # Create the state machine widgets. These contain the ability to
        # undo actions and whatnot.
        self.grid.end_turn()
        self.action = rules.Begin()
        self.startover = copy.deepcopy(self.grid)
        self.checkpoint = copy.deepcopy(self.grid)
        self.inputs = []
        replay = data.pop("history",[])
        self.data["history"] = []
        self.history = []
        self.tab = 0
        
        # Create the canvases that contain all of the sprites.
        self.canvas = sprites.Sprite(0,0,80,24)
        self.grid_container = sprites.Sprite(0,0,self.w,self.h)
        self.grid_canvas = sprites.Sprite(0,0,self.grid.w,self.grid.h)
        self.canvas.add_sprite(self.grid_container)
        self.grid_container.add_sprite(self.grid_canvas)
        self.canvas.fill(' ')
        self.grid_container.fill(' ')
        self.grid_canvas.fill(' ')
        self.grid_canvas.add_sprite(self.grid.sprite)
        self.cursor_sprite = sprites.Sprite(0,0,1,1,100)
        self.grid_canvas.add_sprite(self.cursor_sprite)
        self.highlight = sprites.Sprite(0,0,1,1)
        self.cursor_sprite.putc(None,0,0,None,None,False,True)
        self.highlight.hide()        

        # These are other elements, such as the menu, cursor,
        # animation timer, etc.
        self.cursor = 0,0
        self.scroll = 0,0
        self.animation = 0.0
        self.menu = None
        self.notifications = []
        self.speed = 0.05


        
    # This exports our data as a dictionary to be JSONified. If history is
    # included, it's like saving a snapshot of the game to be continued later.
    # If griddata is included, it's like using the current snapshot as a new
    # map.
    def export(self, history=True, griddata=False):
        return {}
    
    # This function takes the character that was most recently entered by the
    # player and handles it. Even if no player is playing, this function
    # essentially serves as the step function for the AI.
    def handle_input(self, c):
        cx,cy = self.cursor
        sx,sy = self.scroll

        for n,loc in self.grid.info():
            self.notifications.append(n)
            self.grid_canvas.add_sprite(n.sprite)
            ns = n.sprite
            x,y = 0,0
            if loc == "center": x,y = (sx+self.w//2-ns.w//2,
                                       sy+self.h//2-ns.h//2)
            elif loc == "ul": x,y = cx-ns.w,cy-ns.h
            elif loc == "ur": x,y = cx+1,cy-ns.h
            elif loc == "bl": x,y = cx-ns.w,cy+1
            elif loc == "br": x,y = cx+1,cy+1
            n.sprite.move_to(x,y)
                
        
        # If control belongs to the human, then we process all inputs that way.
        # If control does not belong to the human, then the control simply
        # allows the player to move the map around.
        result = None
        info = {}
        if self.grid.current_team().control == "human":
            result = None
            if self.action.form == rules.FORM_COORD:
                if c == "left": cx -=1
                if c == "right": cx +=1
                if c == "up": cy -= 1
                if c == "down": cy += 1
                if c == "\t":
                    self.tab += 1
                    tabbables = [u for u in self.grid.units if u.ready
                                 and u.team is self.grid.current_team()
                                 and u.x is not None and u.y is not None]
                    if len(tabbables):
                        self.tab %= len(tabbables)
                        u = tabbables[self.tab]
                        cx,cy = u.x,u.y
                if (self.cursor != (cx,cy)):
                    if (cx < 0): cx = 0
                    if (cy < 0): cy = 0
                    if (cx >= self.grid.w): cx = self.grid.w-1
                    if (cy >= self.grid.w): cy = self.grid.h-1
                    self.cursor = cx,cy
                    info = self.action.info(self.cursor, self.grid)
                    while ( cx-sx < 0 ): sx -= 10
                    while ( cy-sy < 0 ): sy -= 5
                    while ( cx-sx > self.w): sx += 10
                    while ( cy-sy > self.h): sy += 5
                    if ((sx,sy) != self.scroll):
                        self.scroll = sx,sy
                        self.grid_canvas.move_to(-sx,-sy)
                if c == "enter":
                    result = self.action.perform(self.cursor, self.grid)
                    self.inputs.append(self.cursor)
                self.cursor_sprite.move_to(cx,cy)
            elif self.action.form == rules.FORM_MENU:
                if c:
                    val = self.menu.handle_input(c)
                    if val:
                        self.inputs.append(val)
                        result = self.action.perform(val, self.grid)
                        self.menu = None
                    else:
                        info = self.action.info(self.menu.info(), self.grid)

                    
        # If we got a result from performing an action, we will be given
        # either an order or a new action to perform. The orders tell us that
        # the action was complete and that we either need to commit it or
        # undo our mess.
        if result:
            if result == rules.ACT_COMMIT:
                self.history.append((copy.deepcopy(self.checkpoint),
                                     self.inputs))
                self.checkpoint = copy.deepcopy(self.grid)
                self.action = rules.Begin()
            elif result == rules.ACT_TRASH:
                self.grid.sprite.kill()
                self.inputs = []
                self.grid = copy.deepcopy(self.checkpoint)
                self.grid_canvas.add_sprite(self.grid.sprite)
                self.grid.info()
                self.action = rules.Begin()
            elif result == rules.ACT_UNDO:
                self.grid.sprite.kill()
                cp = None
                if len(self.history) > 0:
                    cp, acts = self.history.pop()
                else:
                    cp = self.checkpoint
                self.grid = copy.deepcopy(cp)
                self.checkpoint = copy.deepcopy(cp)
                self.grid_canvas.add_sprite(self.grid.sprite)
                self.grid.info()
                self.action = rules.Begin()
            elif result == rules.ACT_RESTART:
                self.history = []
                self.inputs = []
                self.grid.sprite.kill()
                self.grid = copy.deepcopy(self.startover)
                self.checkpoint = copy.deepcopy(self.startover)
                self.grid_canvas.add_sprite(self.grid.sprite)
                self.action = rules.Begin()
            elif result == rules.ACT_END:
                history = []
                self.data["history"].append(history)
                for (cp,acts) in self.history:
                    history.append(acts)
                self.history = []
                self.grid.end_turn()
                self.startover = copy.deepcopy(self.grid)
                self.checkpoint = copy.deepcopy(self.grid)
                self.action = rules.Begin()
            else:
                self.action = result
            
            # Set up various UI candy.
            if self.action.form == rules.FORM_COORD:
                self.highlight.kill()
                self.highlight = sprites.Sprite(0,0,self.grid.w,self.grid.h,50)
                c = None
                for (x,y) in self.action.choices:
                    t1,u1 = self.grid.get_at(x,y)
                    t2,u2 = self.grid.get_at(cx,cy)
                    if u1: c = u1.team.color
                    elif t1 and t1.team: c = t1.team.color
                    elif u2: c = u2.team.color
                    else: c = self.grid.current_team().color
                    self.highlight.putc(None,x,y,c,None,False,True)
                self.grid_canvas.add_sprite(self.highlight)
                self.animation = 0.0
            elif self.action.form == rules.FORM_MENU:
                self.menu = widgets.Menu(self.action.choices)
                self.menu.sprite.move_to(cx+1,cy)
                self.grid_canvas.add_sprite(self.menu.sprite)

    # The session has multiple sprites that need to be rendered, from the
    # view of the grid to the mutliple popups that need to appear.
    def render(self, x, y):
        self.animation += self.speed
        if self.animation >= 1.0:
            self.animation = 0.0
            if self.highlight and self.highlight.visible:
                self.highlight.hide()
            elif self.highlight and not self.highlight.visible:
                self.highlight.show()
                for u in self.grid.units:
                    u.cycle_anim()
        notifications = self.notifications
        self.notifications = []
        for n in notifications:
            n.update()
            if n.alive:
                self.notifications.append(n)
        self.canvas.render(0,0)



    

