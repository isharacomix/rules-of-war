# The Rules contain the Action objects that serve as a sort of state machine
# for what can be done. Each action should, upon taking input, pass back a
# new action. Each action can also contain a sprite that should be killed
# after "perform" and modified during "update".

from . import entities


FORM_COORD = "coord"
FORM_MENU = "menu"

ACT_COMMIT = "commit"
ACT_TRASH = "trash"
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

    # The INFO function provides popups and other contextual information of
    # what would happen if the action was taken. This is used to help create
    # interface candy.
    def info(self, act, grid):
        return {}


# The BEGIN action is the first action and expects COORD. If the coord is a
# unit, we display its movement range. If the coord is a terrain that can
# produce, we begin production. If anything else, we display the GAME MENU.
class Begin(Action):
    def __init__(self):
        self.choices = []
        self.form = FORM_COORD

    def perform(self, act, grid):
        x,y = act
        t,u = grid.get_at(x,y)
        if u:
            return Move(x,y,grid)
        elif t.can_build and t.team is grid.current_team():
            return Build(x,y,grid)
        else:
            return Main_Menu()
        

# MAIN MENU follows BEGIN and expects MENU.
# This is the menu created if the user clicks outside of the field.
# This allows the user to end their turn, undo, moves, etc.
class Main_Menu(Action):
    def __init__(self):
        self.choices = ["Close","Surrender","End Turn"]
        self.form = FORM_MENU

    def perform(self, act, grid):
        if act not in self.choices:
            raise Exception("Illegal input: %s"%str(act))

        if act == "Close":
            return ACT_TRASH
        if act == "Surrender":
            grid.purge( grid.current_team() )
            grid.current_team().active = False
            # TODO announce that team has lost
            return ACT_COMMIT
        if act == "End Turn":
            return ACT_END

        raise Exception("Reached end of action without return.")

# BUILD follows BEGIN and expects MENU.
class Build(Action):
    def __init__(self, x, y, grid):
        self.choices = []
        self.start = x,y
        tile = grid.tile_at(x,y)
        for b,v in sorted(tile.builds.items(), key=lambda x:x[1]):
            if v <= grid.current_team().cash:
                self.choices.append("%s $%d"%(b,v))
        self.choices.append("Cancel")
        self.form = FORM_MENU

    # This builds the unit and disables it. It can move on the next turn.
    def perform(self, act, grid):
        if act not in self.choices:
            raise Exception("Illegal input: %s"%str(act))
        if act == "Cancel":
            return ACT_TRASH

        name,price = act.rsplit(None,1)
        unit = entities.Unit(name, grid.rules["units"][name])
        x,y = self.start
        grid.current_team().cash -= int(price[1:])
        grid.add_unit(unit,grid.current_team(),x,y)
        unit.done()
        return ACT_COMMIT
        
# MOVE follows BEGIN and expects COORD.
# If the selected unit is on the active team and is ready, then we permit
# it to move.
class Move(Action):
    def __init__(self, x,y,grid):
        self.start = x,y
        unit = grid.unit_at(x,y)
        self.choices = grid.get_move_range(unit)
        self.form = FORM_COORD
    
    # This performs the movement. After moving, we have to figure out if the
    # unit can do anything else.
    def perform(self, act, grid):
        if act not in self.choices:
            return ACT_TRASH
    
        ox,oy = self.start
        x,y = act
        t1,u1 = grid.get_at(ox,oy)
        t2,u2 = grid.get_at(x,y)
        
        # We just undo whenever we try to move a unit that isn't ready and
        # isn't ours.
        if u1.team is not grid.current_team() or not u1.ready:
            return ACT_TRASH
        
        # Before moving, we check to see if the tile is occupied. If it
        # is, we allow movement if the landing unit can either carry the
        # mover or the mover and landing unit can be joined.
        if (u2 and u2.unit == u1.unit):
            grid.remove_unit(u1)
            u2.hp = min(u1.hp+u2.hp,100)
            u2.fuel = min(u1.fuel+u2.fuel,u2.max_fuel)
            u2.ammo = min(u1.ammo+u2.ammo,u2.max_ammo)
            u2.done()
            return ACT_COMMIT
        if (u2 and u2.can_carry and u1.unit in u2.carries and
           len(u2.carrying) < u2.capacity):
            grid.load_unit(u1,u2)
            return ACT_COMMIT

        grid.move_unit(u1,x,y)
        return Unit_Act(x,y,grid)


# UNIT ACT follows MOVE and expects MENU.
#  If a unit is in range, there is ammo, etc, allow attack.
#  If the unit and current terrain are capturable, allow capture.
class Unit_Act(Action):
    def __init__(self,x,y,grid):
        self.form = FORM_MENU
        self.choices = []
        self.start = x,y
        t,u = grid.get_at(x,y)

        if t.can_capture and u and u.can_capture:
            self.choices.append("Capture")

        self.choices.append("Wait")
        self.choices.append("Cancel")

    #
    def perform(self, act, grid):
        if act not in self.choices:
            raise Exception("Illegal input: %s"%str(act))
        x,y = self.start
        t,u = grid.get_at(x,y)

        if act == "Capture":
            old_hp = t.hp
            new_hp = max(old_hp-u.hp,0)

            t.hp = new_hp
            if t.hp == 0:
                t.team = u.team
                t.hp = 100
                grid.change_tile(t,x,y)
            u.done()
            return ACT_COMMIT

        #if act == "Attack":
            #return Attack(x,y,grid)

        if act == "Wait":
            u.done()
            return ACT_COMMIT

        if act == "Cancel":
            return ACT_TRASH

# ACTION follows UNIT ACT when target in range. Expects COORD.
# The provided coord should be one that contains an enemy unit.
#class Attack(Action):
