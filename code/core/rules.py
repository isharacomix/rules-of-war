# A rules object handles all of the actual game play elements. The rules
# are what give meaning to the pieces in a Grid, and is controlled (usually)
# by a Controller that provides piecewise input.

from . import widgets

import copy


# Constants sent to the controller after processing.
CTRL_COORD = 1
CTRL_MENU = 2
CTRL_UNDO = 3


#
class Rules(object):
    def __init__(self, grid):
        self.grid = grid
        self.checkpoint = copy.deepcopy(grid)

        # The history contains all actions for this player turn.
        self.history = []

        # These are the state variables
        self.action = []
        self.state = None
        self.choices = []

        # other
        self.alerts = []

    # This is the attack action. This is what actually has side effects.
    def action_attack(self, atk_pos, def_pos):
        pass

    # 
    def pop_alerts(self):
        report = self.alerts
        self.alerts = []
        return report

    # This sets the state back to start while also restoring the previous
    # checkpoint of the world. When the controller gets CTRL_UNDO, it is
    # supposed to set its camera's grid to the new one.
    def start_over(self):
        self.action = []
        self.state = None
        self.choices = []
        self.grid = copy.deepcopy(self.checkpoint)
        return CTRL_UNDO

    # When a move is completed and we return to the start state, we
    # change the checkpoint and save the move in our history.
    def commit(self):
        self.history.append((self.checkpoint,self.action))
        self.action = []
        self.state = None
        self.choices = []
        self.checkpoint = copy.deepcopy(self.grid)
        return self.transition(None)

    # When we undo, we go back to a previous spot in the history.
    def undo(self):
        cp,action = self.history.pop()
        self.grid = cp
        self.action = []
        self.state = None
        self.choices = []
        return CTRL_UNDO

    # When we end the turn, we flush the history buffer and save a new
    # checkpoint.
    def end_turn(self):
        self.history = []
        self.action = []
        self.state = None
        self.choices = []
        self.checkpoint = copy.deepcopy(self.grid)
        return self.transition(None)

    # This sets the new state and returns the appropriate code
    # to the caller for what kind of input should come next.
    def transition(self, new_state):
        self.state = new_state
        if   self.state == None       : return CTRL_COORD
        elif self.state == "main menu": return CTRL_MENU
        elif self.state == "moving"   : return CTRL_COORD
        elif self.state == "action"   : return CTRL_MENU
        elif self.state == "attacking": return CTRL_COORD

    # This processes input of two types: coordinates and strings.
    # A string is the input from a menu, such as "attack" or "wait".
    # A coordinate is an x,y location on the grid.
    # Has one of four return values:
    #     None: Tell the controller to do nothing
    #     menu: Tell the controller to render a menu
    #     coord: Tell the controller to give it a coord
    #     undo: Tell the controller to reload the grid
    def process(self, c):
        if   self.state == None       : return self.process_none(c)
        elif self.state == "main menu": return self.process_main_menu(c)
        elif self.state == "moving"   : return self.process_moving(c)
        elif self.state == "action"   : return self.process_action(c)
        elif self.state == "attacking": return self.process_attacking(c)

    # State    : None (expected input, tuple)
    # Expected : Tuple (unit or friendly factory)
    # Next step: If unit: coordinates of range of unit
    #            If factory: list of possible buildables
    def process_none(self, coord):
        if type(coord) is not tuple:
            raise Exception("Expected tuple!")
        x,y = coord
        u = self.grid.unit_at(x,y)
        team = self.grid.current_team()

        # If no unit, check for terrain
        if not u:
            self.state = "main menu"
            self.choices = ["Back","End Turn"]
            return self.transition("main menu")

        # If unit is not friendly, return nothing.
        if u and u.team is not team:
            return self.transition(None)

        # If unit is friendly, but not ready, return nothing.
        if u and u.team is team and not u.ready:
            return self.transition(None)

        # If unit is friendly and ready, switch to moving state and
        # give the controller the list of valid move locations.
        if u and u.team is team and u.ready:
            self.action.append((x,y))
            self.choices = self.grid.get_move_range(x,y)
            return self.transition("moving")

        raise Exception("Shouldn't get here.")

    # State    : Moving (expected input, tuple)
    # Expected : Tuple in range
    # Next step: If in range, move
    #            If out of range, cancel
    def process_moving(self, coord):
        if type(coord) is not tuple:
            raise Exception("Expected tuple!")
        x,y = coord
        ox,oy = self.action[0]
        u = self.grid.unit_at(ox,oy)
        team = self.grid.current_team()
        
        # If coord was in range, move the unit and return possible actions.
        if (x,y) in self.choices:
            self.action.append((x,y))
            self.choices = []

            a1 = self.grid.unit_at(x-1,y)
            a2 = self.grid.unit_at(x+1,y)
            a3 = self.grid.unit_at(x,y-1)
            a4 = self.grid.unit_at(x,y+1)
            attackable = False
            if a1 and not a1.allied(u): attackable = True
            if a2 and not a2.allied(u): attackable = True
            if a3 and not a3.allied(u): attackable = True
            if a4 and not a4.allied(u): attackable = True
            if attackable: self.choices.append("Attack")

            self.grid.move_unit((ox,oy),(x,y))
            self.choices += ["Wait","Cancel"]
            return self.transition("action")

        # If the coord was out of range, undo everything.
        return self.start_over()

    # State: main menu (expected, menu option)
    def process_main_menu(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")

        # Leave the menu.
        if opt == "Back":
            return self.transition(None)
        
        # End my turn.
        if opt == "End Turn":
            self.grid.end_turn()
            return self.end_turn()

    # 
    def process_action(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")

        if opt == "Attack":
            self.choices = []

            x,y = self.action[-1]
            u = self.grid.unit_at(x,y)

            a1 = self.grid.unit_at(x-1,y)
            a2 = self.grid.unit_at(x+1,y)
            a3 = self.grid.unit_at(x,y-1)
            a4 = self.grid.unit_at(x,y+1)
            attackable = False
            if a1 and not a1.allied(u): self.choices.append((x-1,y))
            if a2 and not a2.allied(u): self.choices.append((x+1,y))
            if a3 and not a3.allied(u): self.choices.append((x,y-1))
            if a4 and not a4.allied(u): self.choices.append((x,y+1))

            self.action.append(opt)
            return self.transition("attacking")

        # Wait.
        if opt == "Wait":
            x,y = self.action[-1]
            unit = self.grid.unit_at(x,y)
            unit.ready = False
            self.action.append(opt)
            return self.commit()

        if opt == "Cancel":
            return self.start_over()

    #
    def process_attacking(self, coord):
        if type(coord) is not tuple:
            raise Exception("Expected tuple!")
        x,y = coord

        if coord in self.choices:
            ox,oy = self.action[-2]
            self.action.append((ox,oy))
            a, d = self.grid.unit_at(ox,oy), self.grid.unit_at(x,y)
            
            start_hp = d.hp, a.hp
            #self.action_attack((ox,oy),(x,y))
            self.grid.launch_attack((ox,oy),(x,y))
            end_hp = d.hp, a.hp

            # Build the animation.
            t1 = start_hp[0]-end_hp[0]
            t2 = start_hp[1]-end_hp[1]
            a1 = widgets.HPAlert(6,1,d.team.color,start_hp[0],end_hp[0],0)
            a2 = widgets.HPAlert(6,1,a.team.color,start_hp[1],end_hp[1],t1)
            x1,y1 = x,y
            x2,y2 = ox,oy
            a1.time = t1+t2+50
            a2.time = t1+t2+50
            self.alerts += [(a1,x1+2,y1+2),(a2,x2-4,y2-2)]
            a.ready = False

            return self.commit()



        else:
            return self.start_over()
