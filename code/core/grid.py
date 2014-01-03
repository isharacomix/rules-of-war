# A grid is the arena upon which a battle takes place. The entire map should
# be self-contained. Players interact with the map by taking "actions".

from graphics import draw

from . import widgets


# need a comment here
class Grid(object):
    def __init__(self, w, h):
        self.grid = []
        self.w, self.h = w,h
        for y in range(w):
            row = []
            for x in range(h):
                row.append(("%d"%x)[-1])
            self.grid.append(row)


    # Get the tile at x,y. Returns None if out of range.
    def get(self, x, y):
        if (x < 0 or x >= self.w or y < 0 or y >= self.h):
            return None
        return self.grid[y][x]
    


# The view object of the grid.
class GridView(object):
    def __init__(self, w, h, grid):
        self.world = grid
        self.w = w
        self.h = h
        self.cx = 0
        self.cy = 0
        self.cursor = 0,0

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
                self.menu = widgets.Menu(["Move","Attack"]),cx,cy
        return None

    # Draw the grid to the terminal using the gfx library. Specify the
    # x,y and w,h of the viewport in the terminal, and the cx,cy of the
    # top-left of the map (including outside of the map).
    def draw(self, x, y, col=None):
        w,h = self.w,self.h
        cx,cy = self.cx,self.cy
        
        draw.border(x,y,w,h,"--||+")
        draw.fill(x,y,w,h)
        
        for _x in range(cx,cx+w):
            for _y in range(cy,cy+h):
                tx,ty = _x+x-cx, _y+y-cy
                tile = self.world.get(_x,_y)
                cur = "g?" if self.cursor == (_x,_y) else "g"

                if ( tile and (tx-x >= 0) and (ty-y >= 0) and
                     (not w or tx < x+w) and (not h or ty < y+h)):
                    draw.char(tx,ty,tile, cur)

        if self.menu:
            m,mx,my = self.menu
            m.draw(mx+x-cx+2, my+y-cy)
