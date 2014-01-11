# A grid is the arena upon which a battle takes place. The entire map should
# be self-contained. Players interact with the map by taking "actions" that
# are interpreted by an instance of the rules class containing the game logic.

from graphics import draw

from . import widgets


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
#
# Danger: Do not store 'rules' in a variable. Should fall out of scope.
class Grid(object):
    def __init__(self, config, rules):
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
            this = rules.make_team( t )
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
            this = rules.make_cell(c)
            self.grid[c["y"]][c["x"]] = this
            this.variables = c.get("variables",{})
            if "team" in c:
                this.team = self.teams[c["team"]]
            if "unit" in c:
                def _process_units(unit):
                    u = rules.make_unit(unit)
                    u.team = self.teams[unit["team"]]
                    self.units.append(u)
                    for u in unit.get("carrying",[]):
                        _process_units(u)
                    return u
                this.unit = _process_units(c["unit"])
                
    # Get the tile at x,y. Returns None if out of range.
    def tile_at(self, x, y):
        if (x < 0 or x >= self.w or y < 0 or y >= self.h):
            return None
        return self.grid[y][x]

    # Get the unit at x,y.
    def unit_at(self, x, y):
        tile = self.tile_at(x,y)
        if tile: return tile.unit
        else: return None

    # Get a range of coordinates, usually for an attack range. Coordinates
    # may not actually be cells.
    def get_range(self, center, start, end=None):
        if end is None:
            end = start

        report = []
        x,y = center
        for r in range(start,end+1):
            for i in range(r):
                report.append((x+i,y+(r-i)))
                report.append((x+i,y-(r-i)))
                report.append((x+(r-i),y+i))
                report.append((x-(r-i),y+i))
        return report

    # Return distance (zero norm) between two points.
    def dist(self, start, end):
        x1,y1 = start
        x2,y2 = end
        dx = x1-x2
        dy = y1-y2
        if (dx < 0): dx *= -1
        if (dy < 0): dy *= -1
        return dx+dy


    # Moves a unit from the old tile to the new tile. Will
    # throw exception if move is illegal. CHECK FIRST.
    def move_unit(self, old, new):
        ox,oy = old
        x,y = new
        tile = self.tile_at(ox,oy)
        unit = tile.unit
        tile.unit = None
        tile = self.tile_at(x,y)
        tile.unit = unit

    # Add a unit to the game. Throws an exception if the tile
    # does not exist or if the tile is occupied.
    # This should be the ONLY WAY units are added to the game.
    def add_unit(self, unit, team, x, y):
        tile = self.tile_at(x,y)
        if tile.unit:
            raise Exception("Tried to add unit to occupied tile %d,%d"%(x,y))
        tile.unit = unit
        unit.team = team
        self.units.append(unit)

    #
    def remove_unit(self, x, y):
        tile = self.tile_at(x,y)
        if tile.unit in self.units:
            self.units.remove(tile.unit)
        tile.unit = None

    #
    def current_team(self):
        return self.teams[self.turn]

    #
    def end_turn(self):
        current_team = self.teams[self.turn]
        self.turn += 1
        if self.turn >= len(self.teams):
            self.turn = 0
            self.day += 1
        

# A grid is made up of Cells. The cells all have properties that make up
# what would be called their 'terrain'.
class Cell(object):
    def __init__(self, name, icon, color):
        self.name = name
        self.icon = icon
        self.color = color
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
                col += self.team.color +"!"
            draw.char(x, y, self.icon, self.color+col)


# Units are the pieces that move about the game board. Units belong to a
# team and can be moved about by taking actions.
class Unit(object):
    def __init__(self, name, icon):
        self.name = name
        self.icon = icon
        self.team = None
        self.carrying = []
        self.variables = {}

    def draw(self, x, y, col=""):
        draw.char(x, y, self.icon, self.team.color+"!"+col)

    def allied(self, unit):
        return unit.team == self.team or unit.team in self.team.allies


#
class Team(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.allies = []
        self.active = True
        self.variables = {}

    def allied(self, team):
        return team == self or team in self.allies






# The controller of the grid. It takes a rules object and passes
# control back and forth between it. It doesn't usually need a
# direct copy of the grid, except for its camera.
class Controller(object):
    def __init__(self, w, h, rules):
        self.world = rules
        self.w = w
        self.h = h
        self.cam = widgets.Camera(w,h,self.world.grid)

        self.alerts = []
        self.menu = None

    # This function handles input passed from gfx.get_input.
    def handle_input(self, c):
        cx,cy = self.cam.cursor
        r = None

        # If we have a menu, it capture the input. Otherwise, the camera
        # does.
        if self.menu:
            q = self.menu[0].handle_input(c)
            if q:
                r = self.world.process(q)
                self.menu = None
        else:
            pos = self.cam.handle_input(c)
            if pos:
                r = self.world.process(pos)

        # If the rules were processed, figure out if we need to display
        # a menu or highlight tiles.
        if r:
            self.cam.blink = []
            if r == "coord":
                self.cam.blink = self.world.choices
            if r == "menu":
                self.menu = widgets.Menu(self.world.choices),cx,cy
            if r == "undo":
                self.cam.grid = self.world.grid

        # This returns nothing.
        self.alerts += self.world.pop_alerts()
        return None

    # Draw the grid to the terminal using the gfx library. Specify the
    # x,y and w,h of the viewport in the terminal, and the cx,cy of the
    # top-left of the map (including outside of the map).
    def draw(self, x, y, col=None):
        self.cam.draw(x,y)
        cx,cy = self.cam.viewport

        if self.menu:
            m,mx,my = self.menu
            m.draw(mx+x-cx+2, my+y-cy)

        # Display all alerts on the screen until their timers
        # expire.
        for a in self.alerts:
            m,mx,my = a
            m.time -= 1
            m.draw(mx+x-cx, my+y-cy)
        self.alerts = [a for a in self.alerts if a[0].time > 0]
