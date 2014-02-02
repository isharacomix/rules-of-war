# The Grid is the "map" of the field. We use "grid" instead of "map" in order
# to avoid using the reserved keyword function "map". A grid is made up of
# TILES and UNITS. A tile has a terrain and may contain zero or one UNITS.

from . import entities

# The grid is made up 
class Grid(class):
    def __init__(self, data, rules):
        self.w = 0
        self.h = 0

        # TODO create the grid from data
        self.tiles = []
        self.units = []
        self.teams = []
        self.winners = []

        self.day = 1
        self.turn = 0

    # Get the tile and unit at X,Y
    def get_at(self, x, y):
        if x >= 0 and x < self.w and y >= 0 and y < self.h:
            t = self.tiles[y][x]
            if t: return t, t.unit
        return None, None

    # Get all tile objects.
    def all_tiles(self):
        report = []
        for x in range(self.w):
            for y in range(self.h):
                t,u = self.get_at(x,y)
                if t: report.append(t)
        return report

    # Get an iterable range of all legal tile coordinates.
    def all_tiles_xy(self):
        report = []
        for x in range(self.w):
            for y in range(self.h):
                t,u = self.get_at(x,y)
                if t: report.append((x,y))
        return report

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

    # Return the current team.
    def current_team(self):
        return self.teams[self.turn]

    # This ends the turn and passes play to the next player. All units are set
    # to acive. If a player has won the game at this point, set the winner
    # variable.
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
        for u in self.units:
            u.ready = True

        # Determine the winning team.
        winner = True
        for at in [t for t in self.teams if t.active]:
            for ot in [t for t in self.teams if t.active]:
                if not at.allied(ot):
                    winner = False
        if winner:
            self.winners = [t for t in self.grid.teams if t.active]

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

    # TODO MAY NEED TO BE FIXED ITS POSSIBLE SO POSSIBLE
    def export(self):
        report = {}
        report["name"] = self.name
        report["allies"] = []
        report["cells"] = []
        report["teams"] = []
        for t in self.teams:
            team = {}
            team["name"] = t.name
            team["color"] = t.color
            report["teams"].append(team)
        for c in self.grid:
            cell = {}
            cell["x"],cell["y"] = c
            cd = self.grid[c]
            cell["name"] = cd.name
            if cd.team:
                cell["team"] = self.teams.index(cd.team)
            if cd.unit:
                cell["unit"] = {}
                cell["unit"]["name"] = cd.unit.name
                cell["unit"]["team"] = self.teams.index(cd.unit.team)
                # TODO fix carrying!
            report["cells"].append(cell)
        return report

