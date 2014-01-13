# A game object handles all of the actual game play elements. The rules
# are what give meaning to the pieces in a Grid, and is controlled (usually)
# by a Controller that provides piecewise input.

from . import grid, widgets
from graphics import draw

import copy, json


# Global strings. Stored to avoid mistyping.
CTRL_COORD = "coord"
CTRL_MENU = "menu"
CTRL_UNDO = "undo"


# Custom Cell subclass. Contains information such as terrain defensive bonus.
class Cell(grid.Cell):
    def __init__(self, name, icon, color):
        super(Cell, self).__init__(name, icon, color)

# Custom Team subclass. Contains information such as resources.
class Team(grid.Team):
    def __init__(self, name, color):
        super(Team, self).__init__(name, color)
        self.resources = 0

# Custom Unit subclass. Contains information such as HP, readiness, and
# a custom drawing method.
class Unit(grid.Unit):
    def __init__(self, name, icon):
        super(Unit, self).__init__(name, icon)
        self.hp = 100
        self.ready = True
        self.move = 3
        self.anim = 0.0

    # This drawing method overrides the default method by handling
    # animations for when this unit is low on resources such as HP,
    # ammo, etc.
    def draw(self, x, y, col):
        self.anim += .02

        # Gray out units that can't act. Units are always bold.
        ready = "x" if not self.ready else ""
        color = self.team.color + ready + col + "!"

        # Build the animation for this unit based on values
        # that are running low (hp, fuel, etc).
        frames = [self.icon]
        if (self.hp < 90):
            frames.append( str((self.hp//10)+1)  )
        if int(self.anim) >= len(frames):
            self.anim = 0.0
        img = frames[int(self.anim)]
        
        # Draw the character.
        draw.char(x, y, img, color)


# The Game serve two purposes. Firstly, it is a factory that produces
# new objects according the needs of the game being played. Secondly, they
# serve as a state machine for performing legal actions and changing the
# state of the game grid.
#
# Required methods:
#   make_unit
#   make_team
#   make_cell
#   pop_alerts
#   process
class Game(object):
    def __init__(self, data):
        # TODO: load the rules definition (types of units and properties)
        self.data = data

        # Create the grid with what's left.
        self.grid = grid.Grid(data["grid"], self)
        self.checkpoint = copy.deepcopy(self.grid)

        # The history contains all actions for this player turn.
        self.history = []

        # These are the state variables
        self.action = []
        self.state = None
        self.choices = []

        # other
        self.alerts = []
        self.start = True

        # The first index is the attacker, the second is the defender.
        # This information should really be stored in the Unit object
        # itself. Ugh.
        self.matrix = {}
        self.matrix["i"] = {"i": 50, "T": 10, "M": 5, "H": 1, "L": 10}
        self.matrix["T"] = {"i": 70, "T": 40, "M": 20, "H": 10, "L": 40}
        self.matrix["M"] = {"i": 90, "T": 70, "M": 40, "H": 20, "L": 70}
        self.matrix["H"] = {"i": 100, "T": 90, "M": 60, "H": 30, "L": 90}
        self.matrix["L"] = {"i": 70, "T": 40, "M": 20, "H": 10, "L": 40}
        self.properties = {}
        self.properties["i"] = [] 
        self.properties["T"] = []
        self.properties["M"] = []
        self.properties["H"] = []
        self.properties["L"] = ["indirect"]

        # Replay turn history.
        replay = self.data.pop("history",[])
        self.data["history"] = []
        for turn in replay:
            for action in turn:
                for step in action:
                    self.process(step)
            self.end_turn()
        self.alerts = []



    # Return a JSON string that can be saved to a file. The current
    # turn in progress will be lost.
    def save(self):
        return json.dumps(self.data)

    # This function produces a Unit object based on the unit code.
    def make_unit(self, data):
        u = Unit(data["name"], data["icon"])
        return u

    # This function produces a Cell object based on the terrain code.
    def make_cell(self, data):
        c = Cell(data["name"],'.','g')
        return c

    # This function produces a team.
    def make_team(self, data):
        t = Team(data["name"],data["color"])
        return t


    # Get movement range of the unit at x,y. Returns nothing
    # if the tile is empty or does not exist. All of the positions
    # returned are guaranteed to be tiles that the unit could
    # stop moving on.
    def get_move_range(self, x, y):
        unit = self.grid.unit_at(x,y)
        if not unit:
            return []

        # Use the naive flood-fill algorithm to get neighboring
        # tiles. TODO: handle allied units
        report = []
        def _floodfill((a,b),r):
            t = self.grid.tile_at(a,b)
            if t and (not t.unit or t.unit.allied(unit)):
                if (a,b) not in report:
                    report.append((a,b))
                if r > 0:
                    _floodfill((a-1,b),r-1)
                    _floodfill((a+1,b),r-1)
                    _floodfill((a,b-1),r-1)
                    _floodfill((a,b+1),r-1)
        _floodfill((x,y),unit.move)
        
        return [(x,y) for (x,y) in report if (not self.grid.unit_at(x,y) or
                                              self.grid.unit_at(x,y) is unit)]



    # This is the attack action. This is what actually has side effects.
    def action_attack(self, atk_pos, def_pos):
        ax,ay = atk_pos
        dx,dy = def_pos
        atk_unit = self.grid.unit_at(ax,ay)
        def_unit = self.grid.unit_at(dx,dy)

        if not atk_unit: raise Exception("Attack square is empty.")
        if not def_unit: raise Exception("Defend square is empty.")

        # This is the basic attack formula.
        a = atk_unit.icon
        d = def_unit.icon
        def_unit.hp -= int(self.matrix[a][d]*(.01*atk_unit.hp))
        if def_unit.hp > 0:
            atk_unit.hp -= int(self.matrix[d][a]*(.01*def_unit.hp))

        # Remove destroyed units from grid and prevent HP from falling into
        # the negatives.
        if atk_unit.hp <= 0:
            atk_unit.hp = 0
            self.grid.remove_unit(ax,ay)
        if def_unit.hp <= 0:
            def_unit.hp = 0
            self.grid.remove_unit(dx,dy)

    # 
    def pump_info(self, x, y):
        if self.start:
            t = self.grid.current_team()
            m1 = "%s: Day %d"%(self.grid.name, self.grid.day)
            m2 = "%s Advance"%t.name
            w = max(len(m1),len(m2))+1
            a = widgets.Alert(w,2,m1+"\n"+m2,t.color)
            a.time = 50
            self.alerts.append((a,10,5))
            self.start = False
        report = self.alerts
        self.alerts = []
        
        # Info 1 is global team information.
        info1 = [ ("Day %d"%self.grid.day,"w!")]
        for t in self.grid.teams:
            info1.append( (t.name, t.color) )

        # If attack is in the action, we need to get the estimated
        # damage to show the player.
        dmg1, dmg2 = "",""
        if "Attack" in self.action and (x,y) in self.choices:
            ax,ay = self.action[1]
            atk_unit = self.grid.unit_at(ax,ay)
            def_unit = self.grid.unit_at(x,y)
            if atk_unit and def_unit:
                a = atk_unit.icon
                d = def_unit.icon
                est = self.matrix[a][d]*(.01*atk_unit.hp)
                if est > def_unit.hp:
                    est = def_unit.hp
                dmg1 = "-%d%%"%(self.matrix[a][d]*(.01*atk_unit.hp))
                dmg2 = "-%d%%"%(self.matrix[d][a]*(.01*(def_unit.hp-est)))

        # Info 2 is for the intel on the hovering tile.
        info2 = []
        t = self.grid.tile_at(x,y)
        tcol = "w"
        if t.team:
            tcol = t.team.color
        info2 += [ (t.name,tcol),
                   ("DEF +?",tcol)]
        u = t.unit
        if u:
            ucol = u.team.color
            info2 += [ (" ",""),
                       (u.name,ucol+"!"),
                       ("HP %d%% %s"%(u.hp,dmg1),ucol) ]
            
        

        # Info 3 is for the unit that is currently selected.
        info3 = []
        if len(self.action) > 0:
            x,y = self.action[0]
            if len(self.action) > 1:
                x,y = self.action[1]
            t = self.grid.tile_at(x,y)
            u = t.unit
            if u:
                col = u.team.color
                info3 = [(u.name,col+"!"),
                         ("DEF +?",col),
                         ("HP %d%% %s"%(u.hp,dmg2),col)]
            

        return report, info1, info2, info3

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
    def undo(self, total=False):
        if len(self.history) > 0:
            if total:
                cp,action = self.history[0]
                self.history = []
                self.start = True
            else:
                cp,action = self.history.pop()
            self.grid = cp
            self.checkpoint = copy.deepcopy(cp)
        self.action = []
        self.state = None
        self.choices = []
        return CTRL_UNDO

    # When we end the turn, we flush the history buffer and save a new
    # checkpoint.
    def end_turn(self):
        if self.state != None and self.action != []:
            raise Exception("Can't end right now")
        self.start = True
        self.grid.end_turn()
        for u in self.grid.units:
            u.ready = True
        self.data["history"].append([acts for (cp,acts) in self.history])
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
            self.choices = ["Back","End Turn","Undo","Start Over"]
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
            self.choices = self.get_move_range(x,y)
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

            # Determine if a target is in range.
            attackable = False
            for px,py in self.grid.get_range((x,y),1):
                a = self.grid.unit_at(px,py)
                if a and not a.allied(u):
                    attackable = True
            moved = (x,y) != (ox,oy)
            if "indirect" in self.properties[u.icon] and moved:
                attackable = False
            if attackable:
                self.choices.append("Attack")

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
            return self.end_turn()

        if opt == "Undo":
            return self.undo()

        if opt == "Start Over":
            return self.undo(True)

    # 
    def process_action(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")

        if opt == "Attack":
            self.choices = []

            x,y = self.action[-1]
            u = self.grid.unit_at(x,y)

            # Get possible targets.
            for px,py in self.grid.get_range((x,y),1):
                a = self.grid.unit_at(px,py)
                if a and not a.allied(u):
                    self.choices.append((px,py))

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
            self.action_attack((ox,oy),(x,y))
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
