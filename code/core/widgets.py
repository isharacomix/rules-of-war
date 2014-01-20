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

    def write(self, msg):
        current = ""
        report = []
        for s in msg.split("\n"):
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
                current = ""
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


# This is a data editor. A list of fields are provided, and two dictionaries.
# The first dictionary contains the preset data for each field. The types
# are what kinds of data go in that field (string, int, boolean).
class Editor(object):
    def __init__(self, fields, data, types):
        self.data = ""
        self.fields = fields
        self.data = data
        self.types = types
        self.current = 0
        self.width = 0
        self.margin = 0
        for f in self.fields:
            l1 = len(f)+1
            l2 = 7
            if types[f].startswith("str"):
                l2 = int(types[f].split()[1])+1
            if l1 > self.margin:
                self.margin = l1
            if l2 > self.width:
                self.width = l2

    def handle_input(self, c):
        edit = self.data[self.fields[self.current]]
        editt = self.types[self.fields[self.current]]

        if c == "enter":
            return self.data
        elif c == "up":
            self.current = (self.current-1)%len(self.fields)
        elif c == "down":
            self.current = (self.current+1)%len(self.fields)
        elif c == "backspace" and len(edit) > 0:
            edit = edit[:-1]
        elif c and len(c) == 1:
            if editt == "int":
                if len(edit) < 6 and c in "0123456789":
                    edit += c
            if editt.startswith("str"):
                maxlen = int(editt.split()[1])
                if len(edit) < maxlen:
                    if c.lower() in "abcdefghijklmnopqrstuvwxyz 0123456789-_":
                        edit += c

        self.data[self.fields[self.current]] = edit
        return None

    def draw(self, x, y, col=""):
        w = self.width+self.margin
        m = self.margin
        draw.border(x,y, w, len(self.fields),"--||+")
        draw.fill(x, y, w, len(self.fields))
        for i in range(len(self.fields)):
            this = (i == self.current)
            draw.string(x,y+i,self.fields[i], col+("?" if this else ""))
            draw.string(x+m,y+i, self.data[self.fields[i]], col)
            if this:
                draw.char(x+m+len(self.data[self.fields[i]]),y+i," ",col+"?")
        


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
            self.write("%d%%"%self.start)
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

    # This adds a string 'msg' to the buffer and rescrolls to the
    # end. Word-wraps the text if necessary.
    def write(self, msg, col="w"):
        current = ""
        report = []
        for s in msg.split("\n"):
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
                current = ""
        report.reverse()
        self.text = report + self.text
        self.where = 0

    # Clear the buffer.
    def clear(self):
        self.text = []
        self.where = 0

    # Positive numbers scroll to newer elements, and negative
    # numbers scroll to older ones. "None" will scroll to the
    # end.
    def scroll(self, where):
        if len(self.text) < self.h:
            return
        self.where -= where
        self.where = min(max(self.where,0),len(self.text)-self.h)

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
        if len(self.text) < self.h:
            i -= (self.h - len(self.text))
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

        # Move the camera to keep the cursor visible.
        cx, cy = self.viewport
        if x < cx: self.viewport = cx-self.w/2,cy
        if y < cy: self.viewport = cx,cy-self.h/2
        if x >= cx+self.w: self.viewport = cx+self.w/2,cy
        if y >= cy+self.h: self.viewport = cx,cy+self.h/2

        # If we press enter, send that information to the caller.
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
                tile = self.grid.tile_at(_x,_y)

                # Apply multiple levels of inverted color when tiles
                # are highlighted by the interface.
                cur = col
                if self.blink_anim < 1.0 and (_x,_y) in self.blink: cur += "?"
                if self.cursor == (_x,_y): cur += "w?"
                
                if ( tile and (tx-x >= 0) and (ty-y >= 0) and
                     (not w or tx < x+w) and (not h or ty < y+h)):
                    if tile.unit:
                        tile.unit.draw(tx,ty,cur)
                    else:
                        tile.draw(tx,ty,cur)
                elif self.cursor == (_x,_y):
                    draw.char(tx,ty," ",cur)


# Rulebooks are really big text buffers designed for providing information
# dumps to the player. Rulebooks are made up of pages, and the pages can be
# changed using left/right.
class Rulebook(object):
    def __init__(self, w, h, pages, start=0):
        self.w = w
        self.h = h
        self.buffers = []
        self.page = start
        for text in pages:
            b = Buffer(w,h-2)
            for line in text:
                col = ""
                if type(line) == tuple:
                    line,col = line
                b.write(line,col)
            self.buffers.append(b)
            b.scroll(-10000)

    # The buffer does usually handle input, but when it does,
    # up and down scroll it. This handle-input never returns
    # anything other than None.
    def handle_input(self, c):
        if c == "up": self.buffers[self.page].scroll(-1)
        if c == "down": self.buffers[self.page].scroll(1)
        if c == "left": self.page = (self.page-1)%len(self.buffers)
        if c == "right": self.page = (self.page+1)%len(self.buffers)
        return None

    # This draws the buffer with its current width and height such
    # that it starts with the top-left x,y of the terminal. You can
    # override the colors (gray out) by providing a col parameter.
    def draw(self, x, y, col=""):
        self.buffers[self.page].draw(x,y,col)
        pageno = "Page %d/%d"%(self.page+1,len(self.buffers))
        draw.border(x,y+self.h-1,self.w,1,"--||+")
        draw.fill(x,y+self.h-1,self.w,1)
        draw.string(x,y+self.h-1,pageno,col+"?")

