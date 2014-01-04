# A grid is the arena upon which a battle takes place. The entire map should
# be self-contained. Players interact with the map by taking "actions".

from graphics import draw

from . import widgets


# need a comment here
class Grid(object):
    def __init__(self, w, h):
        self.grid = []
        self.w, self.h = w,h
        for y in range(h):
            row = []
            for x in range(w):
                row.append(Cell())
            self.grid.append(row)

        self.teams = [Team("One","r"),Team("Two","b")]
        self.add_unit( Unit(), self.teams[1], 6, 6 )


    # Get the tile at x,y. Returns None if out of range.
    def get(self, x, y):
        if (x < 0 or x >= self.w or y < 0 or y >= self.h):
            return None
        return self.grid[y][x]
    

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
        report = set()
        def _floodfill((a,b),r):
            t = self.get(a,b)
            if t and (not t.unit or t.unit.team == unit.team):
                report.add((a,b))
                if r > 0:
                    _floodfill((a-1,b),r-1)
                    _floodfill((a+1,b),r-1)
                    _floodfill((a,b-1),r-1)
                    _floodfill((a,b+1),r-1)
        _floodfill((x,y),unit.move)
        
        return [(x,y) for (x,y) in report if not self.get(x,y).unit]

    # Moves a unit from the old tile to the new tile.
    def move_unit(self, old, new):
        ox,oy = old
        x,y = new
        tile = self.get(ox,oy)
        unit = tile.unit
        tile.unit = None
        tile = self.get(x,y)
        tile.unit = unit

    # Add a unit to the game. Throws an exception if the tile
    # does not exist or if the tile is occupied.
    def add_unit(self, unit, team, x, y):
        tile = self.get(x,y)
        if tile.unit:
            raise Exception("Tried to add unit to occupied tile %d,%d"%(x,y))
        tile.unit = unit
        unit.team = team
        team.units.append(unit)
        

# A grid is made up of Cells. The cells all have properties
# that make up what would be called their 'terrain'.
class Cell(object):
    def __init__(self):
        self.c = "."
        self.col = "g"
        self.unit = None
        self.team = None

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


# Units 
class Unit(object):
    def __init__(self):
        self.c = "@"
        self.team = None
        self.anim = 0.0
        
        self.hp = 100
        self.ready = True
        self.move = 3

    # Get the actions that this unit is currently capable of.
    def get_actions(self):
        return ["move","attack"]

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


# 
class Team(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.resources = 0
        self.units = []


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

        self.move_range = []
        self.selected = None

        self.menu = None

    # This function handles input passed from gfx.get_input.
    def handle_input(self, c):
        if self.menu:
            q = self.menu[0].handle_input(c)
            if q:
                self.menu = None
        else:
            cx,cy = self.cursor
            if c == "up": self.cursor = cx,cy-1
            if c == "down": self.cursor = cx,cy+1
            if c == "left": self.cursor = cx-1,cy
            if c == "right": self.cursor = cx+1,cy
            if c == "enter":
                tile = self.world.get(cx,cy)
                if self.selected:
                    if (cx,cy) in self.move_range:
                        self.world.move_unit(self.selected,(cx,cy))
                    self.selected = None
                    self.move_range = []
                elif tile.unit:
                    self.move_range = self.world.get_move_range(cx,cy)
                    self.selected = cx,cy
                    #actions = tile.unit.get_actions()
                    #if actions and len(actions) > 0:
                    #    self.menu = widgets.Menu(actions),cx,cy
                #else:
                #    self.menu = widgets.Menu(["End Turn","Back"]),cx,cy
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
                if (_x,_y) in self.move_range: cur += "?"

                if ( tile and (tx-x >= 0) and (ty-y >= 0) and
                     (not w or tx < x+w) and (not h or ty < y+h)):
                    tile.draw(tx,ty,cur)

        if self.menu:
            m,mx,my = self.menu
            m.draw(mx+x-cx+2, my+y-cy)
