# A grid is the arena upon which a battle takes place. The entire map should
# be self-contained. Players interact with the map by taking "actions" that
# are interpreted by an instance of the rules class containing the game logic.

from graphics import draw

from . import widgets, log


# The Grid is a game-agnostic representation of the world's entities. It
# provides an API to game rulesets to create, delete, and move entities
# around, but essentially has no functionality other than changing its
# configuration. The grid should be initialized with a configuration
# Dictionary containing the following keys and values.
#   name: the name of the map!
#   cells: (list) cells with x,y positions
#   teams: (list) the teams in the map
#   allies: (list) the teams that are allied in a list of lists of ints
#   variables: (dictionary) a dictionary of user-defined variables
#
# Danger: Do not store 'rules' in a variable. Should fall out of scope.
class Grid(object):
    def __init__(self, data, rules):
        self.name = data["name"]
        self.grid = {}
        self.teams = []
        self.units = []
        self.variables = data.get("variables",{})
        self.day = 1
        self.turn = 0

        # Load the teams first, since cells and units reference them.
        # Then set up the alliances.
        for t in data["teams"]:
            this = rules.make_team( t )
            this.variables = t.get("variables",{})
            self.teams.append(this)
        for alist in data.get("allies",[]):
            for a in alist:
                for b in alist:
                    self.teams[a].allies.append( self.teams[b] )

        # Load the terrain cells. The units are embedded in these elements
        # of the dictionary. Note that when units are loaded in other units
        # we, have to recursively dig them out.
        #   x: (int) x position
        #   y: (int) y position
        #   name: (string) the name of the terrain
        #   unit: the unit on this terrain, if one
        #   team: (int) the team that owns the terrain, if any
        #   variables: (dict) User-defined variables
        # There may be other values in this cell that will be parsed by
        # the factory of the rules.
        for c in data["cells"]:
            this = rules.make_cell(c)
            self.grid[(c["x"],c["y"])] = this
            this.variables = c.get("variables",{})
            if "team" in c:
                this.team = self.teams[c["team"]]
            if "unit" in c:
                def _process_units(unit):
                    u = rules.make_unit(unit)
                    u.team = self.teams[unit["team"]]
                    u.variables = unit.get("variables",{})
                    self.units.append(u)
                    for u in unit.get("carrying",[]):
                        u.carrying.append(_process_units(u))
                    return u
                this.unit = _process_units(c["unit"])

    # Export a dictionary of the cells and units in the grid. Usually used
    # to save a map!
    def export(self):
        report = {}
        report["name"] = self.name
        report["allies"] = []
        report["cells"] = []
        report["teams"] = []
        report["variables"] = dict(self.variables)
        for t in self.teams:
            team = {}
            team["name"] = t.name
            team["color"] = t.color
            team["variables"] = dict(t.variables)
            report["teams"].append(team)
        for c in self.grid:
            cell = {}
            cell["x"],cell["y"] = c
            cd = self.grid[c]
            cell["name"] = cd.name
            cell["variables"] = dict(cd.variables)
            if cd.team:
                cell["team"] = self.teams.index(cd.team)
            if cd.unit:
                cell["unit"] = {}
                cell["unit"]["name"] = cd.unit.name
                cell["unit"]["team"] = self.teams.index(cd.unit.team)
                cell["unit"]["variables"] = dict(cd.unit.variables)
            report["cells"].append(cell)
        return report
                
    # This returns all of the tiles.
    def all_tiles(self):
        return self.grid.values()

    def all_tiles_xy(self):
        return self.grid.keys()

    # Get the tile at x,y. Returns None if out of range.
    def tile_at(self, x, y):
        return self.grid.get((x,y),None)

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
                report.append((x+(r-i),y+i    ))
                report.append((x-i    ,y+(r-i)))
                report.append((x-(r-i),y-i    ))
                report.append((x+i    ,y-(r-i)))
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

    # Remove a unit from the game. This will not only remove the
    # unit, but all units that it is carrying.
    def remove_unit(self, x, y):
        tile = self.tile_at(x,y)
        unit = tile.unit
        if unit in self.units:
            self.units.remove(tile.unit)
        for u in unit.carrying:
            if u in self.units:
                self.units.remove(u)
        tile.unit = None

    # Return the team currently performing its turn.
    def current_team(self):
        return self.teams[self.turn]

    # End the turn and proceed to the next team, so long as there is
    # at least one active team left.
    def end_turn(self):
        if len([t for t in self.teams if t.active]) == 0:
            self.day += 1
        else:
            flag = True
            while flag or not self.teams[self.turn].active:
                flag = False
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

    # Draw this unit on the screen.
    def draw(self, x, y, col=""):
        draw.char(x, y, self.icon, self.team.color+"!"+col)

    # Returns true if the two units (or cells) are allied.
    def allied(self, other):
        return other.team is self.team or other.team in self.team.allies


# The game is played by teams. Each team commands an army of units and
# may also have other variables such as money, etc, governed by the
# subclass of the current set of rules.
class Team(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.allies = []
        self.active = True
        self.variables = {}

    # Returns true if the two teams are allied.
    def allied(self, team):
        return team is self or team in self.allies


# The controller of the grid. It takes a rules object and passes
# control back and forth between it. It doesn't usually need a
# direct copy of the grid, except for its camera.
class Controller(object):
    def __init__(self, w, h, rules):
        self.world = rules
        self.w = w
        self.h = h

        # The elements of the grid.
        self.cam = widgets.Camera(w-16,h,self.world.grid)
        self.buff1 = widgets.Buffer(15,7)
        self.buff2 = widgets.Buffer(15,7)
        self.buff3 = widgets.Buffer(15,4)

        self.alerts = []
        self.menu = None
        self.rulebook = None
        self.textentry = None

    # This function handles input passed from gfx.get_input.
    def handle_input(self, c):
        cx,cy = self.cam.cursor
        r = None

        #
        if c == "?":
            if self.rulebook:
                self.rulebook = None
            else:
                text = self.world.make_rulebook()
                self.rulebook = widgets.Rulebook(self.w,self.h,text)

        # If we have a menu, it capture the input. Otherwise, the camera
        # does.
        if self.rulebook:
            q = self.rulebook.handle_input(c)
        elif self.textentry:
            q = self.textentry[0].handle_input(c)
            if q:
                r = self.world.process(q)
                self.textentry = None
        elif self.menu:
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
            if r == "editor":
                fields = []
                data = {}
                types = {}
                for f in self.world.choices:
                    fields.append(f)
                    data[f] = self.world.choices[f]["data"]
                    types[f] = self.world.choices[f]["type"]
                fields.sort(key=lambda x:
                            self.world.choices[x].get("ordering",100))
                self.textentry = widgets.Editor(fields,data,types),cx,cy

        # Get intel from the world's information method.
        cx,cy = self.cam.cursor
        vx,vy = self.cam.viewport
        alerts, i1, i2, i3 = self.world.pump_info(cx,cy)
        for a,loc in alerts:
            if loc == "c": x,y = (vx+(self.cam.w//2)-(a.w//2),
                                  vy+(self.cam.h//2)-(a.h//2))
            elif loc == "tl": x,y = cx-a.w-1,cy-a.h-1
            elif loc == "tr": x,y = cx+2,cy-a.h-1
            elif loc == "bl": x,y = cx-a.w-1,cy+2
            elif loc == "br": x,y = cx+2,cy+2

            self.alerts.append((a,x,y))
        for (info,buff) in ((i1,self.buff1),(i2,self.buff2),(i3,self.buff3)):
            if info is not None:
                buff.clear()
                for s,c in info:
                    buff.write(s,c)
        return None

    # Draw the grid to the terminal using the gfx library. Specify the
    # x,y and w,h of the viewport in the terminal, and the cx,cy of the
    # top-left of the map (including outside of the map).
    def draw(self, x, y, col=None):
        if self.rulebook:
            self.rulebook.draw(x,y)
            return

        self.cam.draw(x,y)
        self.buff1.draw(x+(self.w-15),y)
        self.buff2.draw(x+(self.w-15),y+8)
        self.buff3.draw(x+(self.w-15),y+16)
        draw.fill(x+(self.w-15),y+21,16,self.h-20)
        cx,cy = self.cam.viewport

        # TODO, if it looks like the menu is going to run off any of
        # the sides, rearrange it on the fly.
        for item in [self.menu, self.textentry]+self.alerts:
            if item:
                m,mx,my = item
                dx = mx+x-cx
                dy = my+y-cy
                if item in self.alerts:
                    m.time-=1
                else:
                    dx += 2
                if dx < 0: dx = 0
                if dx > self.w-m.w: dx = self.w-m.w
                if dy < 0: dy = 0
                if dy > self.h-m.h+1: dy = self.h-m.h+1
                m.draw(dx, dy)

        self.alerts = [a for a in self.alerts if a[0].time > 0]
        
