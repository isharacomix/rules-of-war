# The Rules contain the Action objects that serve as a sort of state machine
# for what can be done. Each action should, upon taking input, pass back a
# new action. Each action can also contain a sprite that should be killed
# after "perform" and modified during "update".


ACT_COMMIT = "commit"
ACT_UNDO = "undo"
ACT_END = "end"
ACT_RESTART = "restart"


# An action is the base class of handling actions. Actions tell the session
# what the next input necessary is (such as any coord, a coord in a range of
# selections, or a menu item). The session is responsible for handling input
# appropriately in the context of the action. AI can also respond to actions.
class Action(object):
    def __init__(self):
        self.choices = []
        self.form = None

    # The PERFORM function takes the input (either a coord or a string) and
    # then processes it. This should only be done when the player presses
    # enter and confirms the action. The grid should be backed up before
    # performing. This will return an instance of the new action that the
    # session should handle.
    def perform(self, act, grid):
        return None

    # The UPDATE function provides popups and other contextual information of
    # what would happen if the action was taken. This is used to help create
    # interface candy.
    def update(self, act, grid):
        pass


# The BEGIN action is the first action and expects COORD. If the coord is a
# unit, we display its movement range. If the coord is a terrain that can
# produce, we begin production. If anything else, we display the GAME MENU.
class Begin(Action):
    def __init__(self):
        self.choices = []
        self.form = "coord"

    def perform(self, act, grid):
        x,y = act
        t,u = grid.get_at(x,y)
        if u:
            return Move(x,y)
        
        
# MOVE follows BEGIN and expects COORD.
# If the selected unit is on the active team and is ready,
# then the 
class Move(Action):
    def __init__(self, x, y):
        self.start = x,y
        self.choices = []
        self.form = "coord"
    
    def perform(self, act, grid):
        ox,oy = self.start
        x,y = act
        
        t1,u1 = grid.get_at(ox,oy)
        t2,u2 = grid.get_at(x,y)
        
        grid.move_unit(u1,x,y)
        return "commit"

