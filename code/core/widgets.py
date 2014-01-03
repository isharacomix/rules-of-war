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
    def draw(self, x, y, col="w"):
        w,h = 0,len(self.items)
        for s in self.items:
            w = max(w,len(s))

        draw.border(x,y,w,h,"--||+")
        draw.fill(x,y,w,h)
        for i,s in enumerate(self.items):
            draw.string(x,y+i,s,col+("?" if i==self.index else ""))


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
    def draw(self, x, y, col=None):
        draw.border(x,y,self.w,self.h,"--||+")
        draw.fill(x, y, self.w, self.h)
        w = self.where
        i = y+self.h
        while i > y and w < len(self.text):
            i -= 1
            s,c = self.text[w]
            if col: c = col
            draw.string(x,i,s,c)
            w += 1
