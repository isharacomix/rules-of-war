# The Grid is the "map" of the field. We use "grid" instead of "map" in order
# to avoid using the reserved keyword function "map". A grid is made up of
# TILES and UNITS. A tile has a terrain and may contain zero or one UNITS.
# The grid also manages all of the sprites for the units.

# The grid needs to be a very stable data structure, as undoing moves relies on
# deep copies of the grid. Whenever a move is undo, a previous deepcopy is
# popped from the action stack. Sprites must follow the same rules.

from . import entities

from graphics import sprites

# The grid is made up 
class Grid(object):
    def __init__(self, data, rules):
        self.w = data["w"]
        self.h = data["h"]

        # Create the main sprite. This sprite will be added to the sprite
        # manager in the session object. When a deepcopy is made, this sprite
        # will be duplicated and the old one will be killed.
        self.sprite = sprites.Sprite(0,0,self.w,self.h)

        # Create the grid from data
        self.tiles = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                row.append(None)
            self.tiles.append(row)
        self.units = []
        self.teams = []
        self.winners = []
        
        # Load the teams first, since cells and units reference them.
        # Then set up the alliances.
        for t in data["teams"]:
            this = entities.Team(t)
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
        # We also make the sprite information for the units here. Note that
        # this code is duplicated from the load_unit and add_unit methods.
        for c in data["tiles"]:
            x,y = c["x"], c["y"]
            terrain = c["terrain"]
            this = entities.Tile(terrain,rules["terrain"][terrain])
            if "team" in c:
                this.team = self.teams[c["team"]]
            self.change_tile(this, x, y)
            if "unit" in c:
                def _process_units(udata):
                    name = udata["name"]
                    u = entities.Unit(name, rules["units"][name])
                    u.team = self.teams[udata["team"]]
                    u.x = x
                    u.y = y
                    self.units.append(u)
                    unit.sprite.putc(u.icon,0,0,u.team.color,"X",True,False)
                    unit.sprite.move_to(x,y)
                    self.sprite.add_sprite(unit.sprite)
                    self.units.append(u)
                    for uc in unit.get("carrying",[]):
                        carriee = _process_units(uc)
                        u.carrying.append(carriee)
                        carriee.x = None
                        carriee.y = None
                        carriee.sprite.hide()
                    return u
                this.unit = _process_units(c["unit"])

        self.day = 1
        self.turn = 0

    # Get the tile and unit at X,Y
    def get_at(self, x, y):
        if x >= 0 and x < self.w and y >= 0 and y < self.h:
            t = self.tiles[y][x]
            if t: return t, t.unit
        return None, None
    
    # Get the tile at X,Y
    def tile_at(self, x, y):
        tile, unit = get_at(x, y)
        return tile
        
    # Get the tile of a unit
    def utile(self, unit):
        if unit.x is None and unit.y is None:
            return None
        tile, test = get_at(unit.x, unit.y)
        if test is not unit:
            raise Exception("Unit mismatch at %d,%d"%(unit.x,unit.y))
        return tile
        
    # Get the unit at X,Y
    def unit_at(self, x, y):
        tile, unit = get_at(x, y)
        return unit

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
            u.colorize(u.team.color,"X",True,False)

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
    def move_unit(self, unit, x, y):
        tile = self.utile(unit)
        tile.unit = None
        tile = self.tile_at(x, y)
        if tile.unit:
            raise Exception("Tried to add unit to occupied tile %d,%d"%(x,y))
        tile.unit = unit
         
        unit.x = x
        unit.y = y
        unit.sprite.move_to(x,y)
       
    # This loads a unit into the other. 
    def load_unit(self, unit, carrier):
        tile = self.utile(unit)
        tile.unit = None
        carrier.carrying.append(unit)
        
        unit.x = None
        unit.y = None
        unit.sprite.hide()
        
    # This unloads a unit onto a tile
    def unload_unit(self, carrier, i, x, y):
        unit = carrier.carrying.pop(i)
        tile = self.tile_at(x, y)
        if tile.unit:
            raise Exception("Tried to add unit to occupied tile %d,%d"%(x,y))
        tile.unit = unit
        
        unit.x = x
        unit.y = y
        unit.sprite.show()
        unit.sprite.move_to(x,y)

    # Add a unit to the game. Throws an exception if the tile
    # does not exist or if the tile is occupied.
    # This should be the ONLY WAY units are added to the game.
    def add_unit(self, unit, team, x, y):
        tile = self.tile_at(x,y)
        if tile.unit:
            raise Exception("Tried to add unit to occupied tile %d,%d"%(x,y))
        tile.unit = unit
        unit.team = team
        unit.x = x
        unit.y = y
        
        self.units.append(unit)
        unit.sprite.putc(unit.icon,0,0,team.color,"X",True,False)
        unit.sprite.move_to(x,y)
        self.sprite.add_sprite(unit.sprite)

    # Remove a unit from the game. This will not only remove the
    # unit, but all units that it is carrying.
    def remove_unit(self, unit):
        tile = self.utile(unit)
        if tile:
            tile.unit = False
        
        if unit in self.units:
            self.units.remove(unit)
        for u in unit.get_carrying():
            if u in self.units:
                self.units.remove(u)
                u.sprite.kill()
        unit.sprite.kill()

    # This removes all entities from a team (done when the team is defeated).
    def purge(self, team, structures=False):
        for u in [u for u in self.units if u.team is team]:
            self.remove_unit(u)
        if structures:
            for (x,y) in self.all_tiles_xy():
                t = self.tile_at(x,y)
                if t.team is team:
                    t.team = None
                    self.change_tile(t,x,y)

    # Change a tile on the map.
    def change_tile(self, tile, x, y):
        if x >= 0 and x < self.w and y >= 0 and y < self.h:
            oldtile, unit = self.get_at(x,y)
            self.tiles[y][x] = tile
            tile.unit = unit
            if tile.team:
                self.sprite.putc(tile.icon,x,y,tile.team.color,"X",True,False)
            else:
                self.sprite.putc(tile.icon,x,y,tile.color,"X",False,False)
            self.sprite.dirty = True

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

