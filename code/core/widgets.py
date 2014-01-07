# This module contains "gui" widgets that are useful for games.
#
#

from graphics import draw


# A menu is a simple menu of selections. Created using a list of options,
# it intercepts input, returning None if nothing has been selected yet,
# or the text of the selected option. Handling something like "cancelling"
# should be done by the creator.
class Menu(object):
    def __init__(self, items):
        self.items = list(items)
        self.index = 0
        
        if len(self.items) == 0:
            raise Exception("Created a menu with no items.")

    # Pass the input from gfx.get_input to this function.
    def handle_input(self, c):
        if c == "up": self.index -= 1
        if c == "down": self.index += 1

        self.index %= len(self.items)

        if c == "enter": 
            return self.items[self.index]

        return None

    # Draw the window on the terminal with the top left corner
    # at x,y. Will draw off the side of the screen.
    def draw(self, x, y, col=""):
        w,h = 0,len(self.items)
        for s in self.items:
            w = max(w,len(s))

        draw.border(x,y,w,h,"--||+")
        draw.fill(x,y,w,h)
        for i,s in enumerate(self.items):
            draw.string(x,y+i,s,col+("?" if i==self.index else ""))


# An alert is just a window that contains text. Unlike a buffer, it doesn't
# scroll. Writing to it will overwrite the current message.
class Alert(object):
    def __init__(self, w, h, msg="", col=""):
        self.w = w
        self.h = h
        self.text = []
        self.col = col
        self.write(msg)

    def write(self, s):
        current = ""
        report = []
        for c in s:
            current += c
            if len(current) >= self.w:
                if " " in current.rstrip():
                    old,current = current.rstrip().rsplit(None,1)
                    report.append(old)
                else:
                    report.append(current)
                    current = ""
        if current:
            report.append(current)
        report.reverse()
        self.text = report

    def handle_input(self, c):
        return None

    def draw(self, x, y, col=""):
        draw.border(x,y,self.w,self.h,"--||+")
        draw.fill(x, y, self.w, self.h)
        w = 0
        i = y+self.h
        while i > y and w < len(self.text):
            i -= 1
            draw.string(x,i,self.text[w],self.col+col)
            w += 1


# The HPAlert is a special kind of alert that is used when a unit's HP
# is going down. The Alert starts at a certain HP and decreases until
# it reaches end. In order to facilitate animation, you can also put in
# a delay so that another unit's animation can finish before this one
# starts.
class HPAlert(Alert):
    def __init__(self, w, h, col="w", start=100, end=0, delay=0):
        super(HPAlert, self).__init__(w,h, "%d%%"%start,  col)
        #self.alert = widgets.Alert( 6,1,"%d%%"%start, col)
        self.start = start
        self.end = end
        self.delay = delay

    def draw(self, x, y, col=""):
        if self.delay > 0:
            self.delay -= 1
        elif self.start > self.end:
            self.start -= 1
            self.alert.write("%d%%"%self.start)
        super(HPAlert, self).draw(x,y,col)


# A buffer is just a window that contains text. You can add more text to it
# and it will automatically scroll to the newest. Each line in the buffer is
# a (text,color) tuple.
class Buffer(object):
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.where = 0
        self.text = []

    # This adds a string 's' to the buffer and rescrolls to the
    # end. Word-wraps the text if necessary.
    def write(self, s, col="w"):
        current = ""
        report = []
        for c in s:
            current += c
            if len(current) >= self.w:
                if " " in current.rstrip():
                    old,current = current.rstrip().rsplit(None,1)
                    report.append((old,col))
                else:
                    report.append((current,col))
                    current = ""
        if current:
            report.append((current,col))
        report.reverse()
        self.text = report + self.text
        self.where = 0

    # Positive numbers scroll to newer elements, and negative
    # numbers scroll to older ones. "None" will scroll to the
    # end.
    def scroll(self, where):
        self.where -= where
        if self.where < 0:
            self.where = 0

    # The buffer does usually handle input, but when it does,
    # up and down scroll it. This handle-input never returns
    # anything other than None.
    def handle_input(self, c):
        if c == "up": self.scroll(-1)
        if c == "down": self.scroll(1)
        return None

    # This draws the buffer with its current width and height such
    # that it starts with the top-left x,y of the terminal. You can
    # override the colors (gray out) by providing a col parameter.
    def draw(self, x, y, col=""):
        draw.border(x,y,self.w,self.h,"--||+")
        draw.fill(x, y, self.w, self.h)
        w = self.where
        i = y+self.h
        while i > y and w < len(self.text):
            i -= 1
            s,c = self.text[w]
            draw.string(x,i,s,c+col)
            w += 1


# A Camera is an interactable widget that serves as a representation of
# a Grid.
class Camera(object):
    def __init__(self, w, h, grid):
        self.w = w
        self.h = h
        self.grid = grid

        self.cursor = 0,0
        self.viewport = 0,0
        self.blink = []
        self.blink_anim = 0.0
        self.blink_anim_speed = 0.1

    # Returns the cursor when the player presses Enter. Moves the
    # cursor around when the arrow keys are pressed.
    def handle_input(self, c):
        x, y = self.cursor
        if c == "up": self.cursor = x, y-1
        if c == "down": self.cursor = x, y+1
        if c == "left": self.cursor = x-1, y
        if c == "right": self.cursor = x+1, y

        # move the camera now

        if c == "enter":
            self.blink_anim = 0.0
            return self.cursor
        return None

    # Draw the camera.
    def draw(self, x, y, col=""):
        w,h = self.w,self.h
        cx,cy = self.viewport

        # The blink animation.
        self.blink_anim += self.blink_anim_speed
        if self.blink_anim >= 2:
            self.blink_anim = 0.0
        
        draw.border(x,y,w,h,"--||+")
        draw.fill(x,y,w,h)
        
        # Draw all of the tiles.
        for _x in range(cx,cx+w):
            for _y in range(cy,cy+h):
                tx,ty = _x+x-cx, _y+y-cy
                tile = self.grid.get(_x,_y)

                # Apply multiple levels of inverted color when tiles
                # are highlighted by the interface.
                cur = col
                if self.blink_anim < 1.0 and (_x,_y) in self.blink: cur += "?"
                if self.cursor == (_x,_y): cur += "w?"
                
                if ( tile and (tx-x >= 0) and (ty-y >= 0) and
                     (not w or tx < x+w) and (not h or ty < y+h)):
                    tile.draw(tx,ty,cur)
