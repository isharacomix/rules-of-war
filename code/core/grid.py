# A grid is the arena upon which a battle takes place. The entire map should
# be self-contained. Players interact with the map by taking "actions".

from graphics import gfx, draw


#
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
    

    # Draw the grid to the terminal using the gfx library. Specify the
    # x,y and w,h of the viewport in the terminal, and the cx,cy of the
    # top-left of the map (including outside of the map).
    def draw(self, x, y, w, h, cx=0, cy=0):
        draw.fill(x,y,w,h)
        
        for _x in range(cx,cx+w):
            for _y in range(cy,cy+h):
                tx,ty = _x+x-cx, _y+y-cy
                tile = self.get(_x,_y)

                if ( tile and (tx-x >= 0) and (ty-y >= 0) and
                     (not w or tx < x+w) and (not h or ty < y+h)):
                    draw.char(tx,ty,tile)
