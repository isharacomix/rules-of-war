# Widgets are GUI elements that can be interacted with and drawn on the
# screen. When a widget is created, its sprite should be added to the
# appropriate sprite for rendering.

from graphics import draw

# Menus are the prime example of a widget. They capture input - pressing
# an arrow key moves the highlighted line of text, and pressing enter
# will cause the interaction to return the string of the menu. Keyboard
# shortcuts will automatically be assigned based on the first letter of
# an option.
class Menu(object):
    def __init__(self, items):
        h = len(items)
        w = 0
        for s in items:
            w = max(len(s),w)

        # Set up the window.
        self.sprite = draw.border(0,0,w+2,h+2)
        self.sprite.layer = 200
        i = 1
        for s in items:
            self.sprite.blit(draw.string(0,0,s),1,i)
            i += 1
        self.cursor = draw.fill(1,1,w,1,None,None,None,True,True)
        self.sprite.add_sprite(self.cursor)
        self.index = 0
        self.items = items

    # This method takes the return value of gfx.get_input and handles
    # it. If a menu item is selected via Enter or keyboard shortcut,
    # that option is returned.
    def handle_input(self, c):
        i = self.index
        if c == "up": i -= 1
        if c == "down": i += 1
        if i != self.index:
            i = i%len(self.items)
            self.cursor.move_to(1,i+1)
            self.index = i
        if c == "enter":
            report = self.items[self.index]
            self.sprite.kill()
            return report
        return None

    # This function just reports what value is being hovered over.
    # This can be used for tooltips.
    def info(self):
        return self.items[self.index]
