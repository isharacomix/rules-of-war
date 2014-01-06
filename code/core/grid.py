# A grid is the arena upon which a battle takes place. The entire map should
# be self-contained. Players interact with the map by taking "actions".

from graphics import draw

from . import widgets

import copy


# The Grid is a game-agnostic representation of the world's entities. It
# provides an API to game rulesets to create, delete, and move entities
# around, but essentially has no functionality other than changing its
# configuration. The grid should be initialized with a configuration
# Dictionary containing the following keys and values.
#   w: (int) width
#   h: (int) height
#   cells: (list) exactly w*h cells
#   teams: (list) the teams in the map
#   allies: (list) the teams that are allied in a list of lists of ints
#   variables: (dictionary) a dictionary of user-defined variables
class Grid(object):
    def __init__(self, config):
        self.grid = []
        self.w, self.h = config["w"], config["h"]
        for y in range(self.h):
            row = []
            for x in range(self.w):
                row.append(None)
            self.grid.append(row)
        self.teams = []
        self.units = []
        self.variables = config.get("variables",{})
        self.day = 0
        self.turn = 0

        # Load the teams first, since cells and units reference them.
        # Then set up the alliances.
        for t in config["teams"]:
            this = Team( t["name"], t["color"] )
            this.variables = t.get("variables",{})
            self.teams.append(this)
        for alist in config.get("allies",[]):
            for a in alist:
                for b in alist:
                    self.teams[a].allies.append( self.teams[b] )

        # Load the terrain cells. The units are embedded in these elements
        # of the dictionary. Note that when units are loaded in other units
        # we, have to recursively dig them out.
        #   x: (int) x position
        #   y: (int) y position
        #   terrain: (string) the name of the terrain
        #   unit: the unit on this terrain, if one
        #   team: (int) the team that owns the terrain, if any
        #   variables: (dict) User-defined variables
        for c in config["cells"]:
            this = Cell(c["terrain"])
            self.grid[c["y"]][c["x"]] = this
            this.variables = c.get("variables",{})
            if "owner" in c:
                this.team = self.teams[c["team"]]
            if "unit" in c:
                def _process_units(unit):
                    u = Unit(unit["type"],self.teams[unit["team"]])
                    u.variables = unit.get("variables",{})
                    self.units.append(u)
                    for u in unit.get("carrying",[]):
                        _process_units(u)
                    return u
                this.unit = _process_units(c["unit"])


                

    # Get the tile at x,y. Returns None if out of range.
    def get(self, x, y):
        if (x < 0 or x >= self.w or y < 0 or y >= self.h):
            return None
        return self.grid[y][x]
    
    # Get the unit at x,y.
    def unit_at(self, x, y):
        tile = self.get(x,y)
        if tile: return tile.unit
        else: return None

    # Return the actions that the given unit can take if it were
    # at x,y.
    def actions(self, unit, x, y):
        acts = []
        a1 = self.unit_at(x-1,y)
        a2 = self.unit_at(x+1,y)
        a3 = self.unit_at(x,y-1)
        a4 = self.unit_at(x,y+1)
        attackable = False
        if a1 and not a1.allied(unit): attackable = True
        if a2 and not a2.allied(unit): attackable = True
        if a3 and not a3.allied(unit): attackable = True
        if a4 and not a4.allied(unit): attackable = True
        if attackable: acts.append("Attack")
        return acts+["Wait","Back"]

    # Get movement range of the unit at x,y. Returns nothing
    # if the tile is empty or does not exist. All of the positions
    # returned are guaranteed to be tiles that the unit could
    # stop moving on.
    def get_move_range(self, x, y):
        tile = self.get(x,y)
        if not tile or not tile.unit:
            return []
        unit = tile.unit

        # Use the naive flood-fill algorithm to get neighboring
        # tiles. TODO: handle allied units
        report = []
        def _floodfill((a,b),r):
            t = self.get(a,b)
            if t and (not t.unit or t.unit.allied(unit)):
                if (a,b) not in report:
                    report.append((a,b))
                if r > 0:
                    _floodfill((a-1,b),r-1)
                    _floodfill((a+1,b),r-1)
                    _floodfill((a,b-1),r-1)
                    _floodfill((a,b+1),r-1)
        _floodfill((x,y),unit.move)
        
        return [(x,y) for (x,y) in report if (not self.unit_at(x,y) or
                                              self.unit_at(x,y) is unit)]

    # Moves a unit from the old tile to the new tile. Will
    # throw exception if move is illegal. CHECK FIRST.
    def move_unit(self, old, new):
        ox,oy = old
        x,y = new
        tile = self.get(ox,oy)
        unit = tile.unit
        tile.unit = None
        tile = self.get(x,y)
        tile.unit = unit

    # Launch an attack from the attack coordinates to the defend
    # coordinates. Will throw exception if move is illegal.
    # CHECK FIRST.
    def launch_attack(self, attacker, defender):
        ax,ay = attacker
        dx,dy = defender
        atk_unit = self.get(ax,ay).unit
        def_unit = self.get(dx,dy).unit
        atk_unit.attack(def_unit)
        if def_unit.hp >= 0: #and can counter
            def_unit.attack(atk_unit)
        
        # Destroy dead units.
        if def_unit.hp <= 0: self.remove_unit(dx,dy)
        if atk_unit.hp <= 0: self.remove_unit(ax,ay)


    # Add a unit to the game. Throws an exception if the tile
    # does not exist or if the tile is occupied.
    # This should be the ONLY WAY units are added to the game.
    def add_unit(self, unit, team, x, y):
        tile = self.get(x,y)
        if tile.unit:
            raise Exception("Tried to add unit to occupied tile %d,%d"%(x,y))
        tile.unit = unit
        unit.team = team
        self.units.append(unit)

    #
    def remove_unit(self, x, y):
        tile = self.get(x,y)
        if tile.unit in self.units:
            self.units.remove(tile.unit)
        tile.unit = None

    #
    def current_team(self):
        return self.teams[self.turn]

    #
    def end_turn(self):
        current_team = self.teams[self.turn]
        for u in self.units:
            u.ready = True
        self.turn += 1
        if self.turn >= len(self.teams):
            self.turn = 0
            self.day += 1
        

# A grid is made up of Cells. The cells all have properties that make up
# what would be called their 'terrain'.
class Cell(object):
    def __init__(self, terrain):
        self.name = terrain
        self.c = "."
        self.col = "g"
        self.unit = None
        self.team = None
        self.variables = {}

    # This function returns the character and color that
    # should be drawn. If there is a unit on this terrain,
    # the unit's draw will be prioritized.
    def draw(self, x, y, col=""):
        if self.unit:
            self.unit.draw(x, y, col)
        else:
            if self.team:
                col += self.team.color+"!"
            draw.char(x, y, self.c, self.col+col)

    # This function draws the terrain without drawing the
    # unit. Put into its own function to avoid messing up
    # the "drawable" interface.
    def draw_terrain(self, x, y, col=""):
        if self.team:
            col += self.team.color+"!"
        draw.char(x, y, self.c, self.col+col)


# Units are the pieces that move about the game board. Units belong to a
# team and can be moved about by taking actions.
class Unit(object):
    def __init__(self, name, team):
        self.name = name
        self.c = "@"
        self.team = team
        self.variables = {}

        self.anim = 0.0
        
        self.hp = 100
        self.ready = True
        self.move = 3

    # This function draws the unit at the desired location.
    def draw(self, x, y, col):
        self.anim += .02

        # Gray out units that can't act. Units are always bold.
        ready = "x" if not self.ready else ""
        color = self.team.color + ready + col + "!"

        # Build the animation for this unit based on values
        # that are running low (hp, fuel, etc).
        frames = [self.c]
        if (self.hp <= 90):
            frames.append( str((self.hp//10)+1)  )
        if int(self.anim) >= len(frames):
            self.anim = 0.0
        img = frames[int(self.anim)]
        
        # Draw the character.
        draw.char(x, y, img, color)

    def allied(self, unit):
        return unit.team == self.team or unit.team in self.team.allies

    #
    def attack(self, unit):
        damage = int(30 * 0.01 * self.hp)
        unit.hp -= damage
        if unit.hp < 0:
            unit.hp = 0

#
class Team(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.resources = 0
        self.allies = []
        self.active = True
        self.variables = {}

    def allied(self, team):
        return team == self or team in self.allies

# The view object of the grid.
class GridView(object):
    def __init__(self, w, h, grid):
        self.world = grid
        self.w = w
        self.h = h
        self.cx = 0
        self.cy = 0
        self.cursor = 0,0
        self.c_anim = 0.0

        self.highlight = []
        self.selected = None

        self.hp_animation = []

        self.alerts = []
        self.currently = None
        self.menu = None
        self.checkpoint = None

    # This function handles input passed from gfx.get_input.
    def handle_input(self, c):
        if self.menu:
            q = self.menu[0].handle_input(c)
            if q == "Attack":
                if self.cursor in self.highlight:
                    self.world.move_unit(self.selected,self.cursor)
                self.currently = "attacking"
                self.selected = self.cursor
                self.highlight = []
            if q == "Wait":
                if self.cursor in self.highlight:
                    self.world.move_unit(self.selected,self.cursor)
                    self.world.unit_at(*self.cursor).ready = False
                self.selected = None
                self.currently = None
                self.highlight = []
            if q == "End Turn":
                self.world.end_turn()
            if q:
                self.menu = None
        else:
            cx,cy = self.cursor
            if c == "up": self.cursor = cx,cy-1
            if c == "down": self.cursor = cx,cy+1
            if c == "left": self.cursor = cx-1,cy
            if c == "right": self.cursor = cx+1,cy
            if c == "w": self.checkpoint = copy.deepcopy(self.world)
            if c == "e": self.world = self.checkpoint
            if c == "enter":
                tile = self.world.get(cx,cy)
                unit = tile.unit if tile else None
                if self.currently == "attacking":
                    my_unit = self.world.unit_at(*self.selected)
                    if unit and not unit.allied(my_unit):
                        starting_hp = unit.hp, my_unit.hp
                        c1 = unit.team.color
                        c2 = my_unit.team.color
                        self.world.launch_attack(self.selected,self.cursor)
                        ending_hp = (unit.hp if unit else 0,
                                     my_unit.hp if my_unit else 0)
                        
                        # Ugly hacky hp animation for combats.
                        self.hp_animation = list(starting_hp)+list(ending_hp)
                        x1,y1 = self.cursor
                        x2,y2 = self.selected
                        a1 = widgets.Alert( 6,1,"%d%%"%starting_hp[0], c1)
                        a2 = widgets.Alert( 6,1,"%d%%"%starting_hp[1], c2)
                        self.alerts += [(a1,x1+2,y1+2),(a2,x2-4,y2-2)]
                        self.hp_animation += [a1,a2,50]
                        
                        if my_unit:
                            my_unit.ready = False
                        self.selected = None
                        self.currently = None
                elif self.currently == "moving":
                    my_unit = self.world.unit_at(*self.selected)
                    if (cx,cy) in self.highlight:
                        acts = self.world.actions(my_unit,cx,cy)
                        self.menu = widgets.Menu(acts),cx,cy
                    else:
                        self.selected = None
                        self.currently = None
                        self.highlight = []
                elif unit:
                    if unit.ready and unit.team == self.world.current_team():
                        self.highlight = self.world.get_move_range(cx,cy)
                        self.selected = cx,cy
                        self.currently = "moving"
                    #actions = tile.unit.get_actions()
                    #if actions and len(actions) > 0:
                    #    self.menu = widgets.Menu(actions),cx,cy
                else:
                    self.menu = widgets.Menu(["Back","End Turn"]),cx,cy
        return None

    # Draw the grid to the terminal using the gfx library. Specify the
    # x,y and w,h of the viewport in the terminal, and the cx,cy of the
    # top-left of the map (including outside of the map).
    def draw(self, x, y, col=None):
        w,h = self.w,self.h
        cx,cy = self.cx,self.cy

        self.c_anim += .05
        if self.c_anim >= 2:
            self.c_anim = 0.0
        
        draw.border(x,y,w,h,"--||+")
        draw.fill(x,y,w,h)
        
        for _x in range(cx,cx+w):
            for _y in range(cy,cy+h):
                tx,ty = _x+x-cx, _y+y-cy
                tile = self.world.get(_x,_y)

                # Apply multiple levels of inverted color when tiles
                # are highlighted by the interface.
                cur = ""
                if self.cursor == (_x,_y): cur += "?"
                if (_x,_y) in self.highlight: cur += "?"

                if ( tile and (tx-x >= 0) and (ty-y >= 0) and
                     (not w or tx < x+w) and (not h or ty < y+h)):
                    tile.draw(tx,ty,cur)

        if self.menu:
            m,mx,my = self.menu
            m.draw(mx+x-cx+2, my+y-cy)

        if self.hp_animation:
            hp1s,hp2s,hp1e,hp2e,a1,a2,t= self.hp_animation
            if hp1s > hp1e:
                hp1s -= 1
                a1.write( "%d%%"%hp1s)
                self.hp_animation = [hp1s,hp2s,hp1e,hp2e,a1,a2,t]
            elif hp2s > hp2e:
                hp2s -=1
                a2.write( "%d%%"%hp2s)
                self.hp_animation = [hp1s,hp2s,hp1e,hp2e,a1,a2,t]
            elif t > 0:
                t -= 1
                self.hp_animation = [hp1s,hp2s,hp1e,hp2e,a1,a2,t]
            else:
                hp_animation = None
                self.alerts = []

        for a in self.alerts:
            m,mx,my = a
            m.draw(mx+x-cx, my+y-cy)
