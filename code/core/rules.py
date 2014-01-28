# A rules object handles all of the actual game play elements. The rules
# are what give meaning to the pieces in a Grid, and is controlled (usually)
# by a Controller that provides piecewise input.

from . import grid, widgets, storage, log
from graphics import draw

import copy, json


# Global strings. Stored to avoid mistyping.
CTRL_COORD = "coord"
CTRL_MENU = "menu"
CTRL_UNDO = "undo"
CTRL_EDITOR = "editor"
CTRL_QUIT = "quit"

# Custom Cell subclass. Contains information such as terrain defensive bonus.
class Cell(grid.Cell):
    def __init__(self, name, rules):
        super(Cell, self).__init__(name, rules["icon"], rules["color"])
        self.defense = rules["defense"]
        self.properties = list(rules.get("properties",[]))
        self.hp = 100
        self.cash = rules.get("cash",0)
        self.build = dict(rules.get("build",{}))
        self.description = rules.get("description","")
        self.repair = dict(rules.get("repair",{}))

    # Create a rulebook section for this terrain.
    def rulebook(self):
        report = []
        report.append(self.name+"\n"+("-"*len(self.name)))
        if self.description:
            report.append(self.description+"\n ")
        report.append("Icon on map: %s"%self.icon)
        report.append("Defensive cover: %d"%self.defense)

        if "capture" in self.properties:
            report.append("Can be captured")
            report.append("Produces $%d per turn"%self.cash)
        if "build" in self.properties:
            report.append("Can produce units:")
            for b in self.build:
                report.append("    %s costs $%d"%(b,self.build[b]))
        if "hq" in self.properties:
            report.append("This team loses if this property is captured")
        if "repair" in self.properties:
            report.append("Repairs the following units at start of a day:")
            for b in self.repair:
                report.append("    %s (+%d%%)"%(b,self.repair[b]))

        return report


# Custom Team subclass. Contains information such as resources.
class Team(grid.Team):
    def __init__(self, name, color):
        super(Team, self).__init__(name, color)
        self.cash = 0

# Custom Unit subclass. Contains information such as HP, readiness, and
# a custom drawing method.
class Unit(grid.Unit):
    def __init__(self, name, rules):
        super(Unit, self).__init__(name, rules["icon"])
        self.hp = 100
        self.ready = True
        self.move = rules["move"]
        self.anim = 0.0
        self.damage = dict(rules["damage"])
        self.properties = list(rules.get("properties",[]))
        self.terrain = dict(rules["terrain"])
        self.rng = tuple(rules.get("range",[1,1]))
        self.description = rules.get("description","")
        self.capacity = rules.get("capacity",0)
        self.carry = list(rules.get("carry",[]))

    # Create a rulebook section for this unit.
    def rulebook(self):
        report = []
        report.append(self.name+"\n"+("-"*len(self.name)))
        if self.description:
            report.append(self.description+"\n ")
        report.append("Icon on map: %s"%self.icon)
        report.append("Movement Range: %d"%self.move)
        for t in self.terrain:
            report.append("    %d over %s"%(self.terrain[t],t))
        if "nocover" in self.properties:
            report.append("This unit does not receive defensive cover")
        if "indirect" in self.properties:
            report.append("Indirect attack unit")
        if self.rng[0] != self.rng[1]:
            report.append("Firing Range: %d-%d"%self.rng)
        else:
            report.append("Firing Range: %d"%self.rng[0])
        for u in self.damage:
            report.append("    vs %s -%d%%"%(u, self.damage[u]))
        if "capture" in self.properties:
            report.append("Can capture properties")
        if "carry" in self.properties:
            a = "Can carry up to %d of the following units:"%self.capacity
            report.append(a)
            for u in self.carry:
                report.append("    %s"%u)

        return report

    # Simulate an attack from this unit on a target including unit
    # bonuses and terrain effects.
    def simulate(self, target, terrain, hp=None):
        if not hp: hp = self.hp
        if "nocover" in self.properties: terrain = 0
        if target in self.damage:
            base = self.damage[target]
            cover = 1.0 - (.1*terrain.defense)
            return int(base*.01*hp*cover)
        return None

    # This returns False if out of range and true if in range.
    def in_range(self, dist):
        return (dist >= self.rng[0] and dist <= self.rng[1])

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


# The Rules serve two purposes. Firstly, it is a factory that produces
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
class Rules(object):
    def __init__(self, data, edit=False):
        self.data = data
        self.edit = edit

        # Create the grid with what's left.
        self.alerts = []
        self.grid = grid.Grid(data["grid"], self)
        if not self.edit:
            for t in self.grid.teams:
                t.active = False
            for p in data["players"]:
                t = self.grid.teams[data["players"][p]["team"]]
                t.name = p
                t.color = data["players"][p]["color"]
                t.active = True
            for t in self.grid.teams:
                if not t.active:
                    t.name = "Absent"
                    self.defeated(t)
                while not self.grid.current_team().active and self.grid.day==1:
                    self.grid.end_turn()
        self.checkpoint = copy.deepcopy(self.grid)
        self.restartpoint = copy.deepcopy(self.grid)

        # The history contains all actions for this player turn.
        self.history = []

        # These are the state variables
        self.action = []
        self.state = "play"
        if edit:
            self.data["history"] = []
            self.state = "edit"

        self.choices = []
        self.winners = None
        self.done = False

        # other
        self.alerts = []
        self.start = True

        # Replay turn history.
        replay = self.data.pop("history",[])
        self.data["history"] = []
        for turn in replay:
            for action in turn:
                for step in action:
                    self.process(step)
            self.end_turn()
        self.alerts = []
        self.last_edit = None

    # Return a JSON string that can be saved to a file. The current
    # turn in progress will be lost.
    def export(self, griddata=False):
        data = dict(self.data)
        if griddata:
            data["grid"] = self.grid.export()
        return json.dumps(data, indent=4)

    # This function produces a Unit object based on the unit code.
    def make_unit(self, data):
        name = data["name"]
        u = Unit(name, self.data["rules"]["units"][name])
        return u

    # This function produces a Cell object based on the terrain code.
    def make_cell(self, data):
        name = data["name"]
        c = Cell(name, self.data["rules"]["terrain"][name])
        return c

    # This function produces a team.
    def make_team(self, data):
        t = Team(data["name"],data["color"])
        return t


    # The rulebook has three pages. An overview, a page for units, and
    # a page for terrain.
    def make_rulebook(self):
        overview = [("Overview\n========","w!")]
        overview.append(" ")
        overview.append("One day I'll put the rules here.")

        
        quick = [("Quick Reference\n===============","w!")]

        # The third section has all of the units, listed in order.
        # We create temporary unit objects that are responsible for
        # writing their own sections.
        units = [("Unit Intel\n==========","w!")]
        quick.append(" ")
        quick.append("Units\n----------------------")
        for uni in self.data["rules"]["units"]:
            U = self.make_unit({"name":uni})
            units += [" "]+U.rulebook()+[" "]
            quick.append("%20s %s"%(U.name, U.icon))

        # The fourth part is just like the second, except for terrain.
        terrain = [("Terrain Intel\n=============","w!")]
        quick.append(" ")
        quick.append("Terrain\n----------------------")
        for ter in self.data["rules"]["terrain"]:
            T = self.make_cell({"name":ter})
            terrain += [" "]+T.rulebook()+[" "]
            quick.append("%20s %s"%(T.name, T.icon))

        return [overview,quick,units,terrain]

    



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
        def _floodfill(pos,r,top=False):
            a,b = pos
            t = self.grid.tile_at(a,b)
            if t and (not t.unit or t.unit.allied(unit)):
                if not top:
                    r -= unit.terrain.get(t.name,r)
                if (a,b) not in report and t.name in unit.terrain:
                    report.append((a,b))
                if r > 0:
                    _floodfill((a-1,b),r)
                    _floodfill((a+1,b),r)
                    _floodfill((a,b-1),r)
                    _floodfill((a,b+1),r)
        _floodfill((x,y),unit.move,True)
        
        return [(x,y) for (x,y) in report if (not self.grid.unit_at(x,y) or
                                              self.grid.unit_at(x,y) and
                                              self.grid.unit_at(x,y).team is
                                              unit.team)]





    # This is the attack action. This is what actually has side effects.
    def action_attack(self, atk_pos, def_pos):
        ax,ay = atk_pos
        dx,dy = def_pos
        atk_unit = self.grid.unit_at(ax,ay)
        def_unit = self.grid.unit_at(dx,dy)
        dist = self.grid.dist((ax,ay),(dx,dy))

        if not atk_unit: raise Exception("Attack square is empty.")
        if not def_unit: raise Exception("Defend square is empty.")

        # This is the basic attack formula.
        a_terrain = self.grid.tile_at(ax,ay)
        d_terrain = self.grid.tile_at(dx,dy)
        def_unit.hp -= atk_unit.simulate(def_unit.name, d_terrain)

        counter = True
        if def_unit.hp <= 0: counter = False
        if "indirect" in def_unit.properties: counter = False
        if not def_unit.in_range(dist): counter = False

        if counter:
            atk_unit.hp -= def_unit.simulate(atk_unit.name, a_terrain)

        # Remove destroyed units from grid and prevent HP from falling into
        # the negatives.
        if atk_unit.hp <= 0:
            atk_unit.hp = 0
            a_terrain.hp = 100
            self.grid.remove_unit(ax,ay)
        if def_unit.hp <= 0:
            def_unit.hp = 0
            d_terrain.hp = 100
            self.grid.remove_unit(dx,dy)

        # Check and see if the last unit died.
        a_alive = False
        d_alive = False
        for (tx,ty) in self.grid.all_tiles_xy():
            u = self.grid.unit_at(tx,ty)
            if u and u.team is atk_unit.team: a_alive = True
            if u and u.team is def_unit.team: d_alive = True 
        if not a_alive: self.defeated(atk_unit.team)
        if not d_alive: self.defeated(def_unit.team)

    # 
    def pump_info(self, x, y):
        if self.start and not self.edit:
            self.start_turn()
        report = self.alerts
        self.alerts = []
        
        # Info 1 is global team information.
        info1 = [ ("Day %d"%self.grid.day,"w!")]
        if self.edit:
            info1 = [("Map Editing","w!")]
        for t in self.grid.teams:
            money = "$%d"%t.cash
            if t.cash >= 10000:
                money = "$%dK"%(t.cash/1000)
            if t.cash >= 1000000:
                money = "$RICH"
            space = " "*(14-len(t.name[:8])-len(money))
            col = t.color
            if not t.active:
                col = "x!"
            info1.append( ("%s%s%s"%(t.name[:8], space, money), col) )

        # If attack is in the action, we need to get the estimated
        # damage to show the player.
        dmg1, dmg2 = "",""
        if "Attack" in self.action and (x,y) in self.choices:
            ax,ay = self.action[1]
            atk_unit = self.grid.unit_at(ax,ay)
            def_unit = self.grid.unit_at(x,y)
            if atk_unit and def_unit:
                a_terrain = self.grid.tile_at(ax,ay)
                d_terrain = self.grid.tile_at(x,y)
                dist = self.grid.dist((ax,ay),(x,y))
                est = atk_unit.simulate(def_unit.name,d_terrain)
                dmg1 = "-%d%%"%est
                if est > def_unit.hp:
                    est = def_unit.hp
                dmg2 = "-%d%%"%(def_unit.simulate(atk_unit.name,a_terrain,
                                                  atk_unit.hp-est))

                counter = True
                if "indirect" in def_unit.properties: counter = False
                if not def_unit.in_range(dist): counter = False
                if not counter: dmg2 = "-0%"

        # Info 2 is for the intel on the hovering tile.
        info2 = []
        t = self.grid.tile_at(x,y)
        tcol = "w"
        if t:
            if t.team:
                tcol = t.team.color
            info2 += [ (t.name,tcol),
                       ("DEF +%d"%t.defense,tcol)]
            u = t.unit
            if u:
                ucol = u.team.color
                if t.hp < 100:
                    info2 += [("Capturing: %d%%"%t.hp,ucol)]
                info2 += [ (" ",""),
                           (u.name,ucol+"!"),
                           ("HP %d%% %s"%(u.hp,dmg1),ucol) ]
            
        

        # Info 3 is for the unit that is currently selected.
        info3 = []
        if len(self.action) > 0 and not self.edit:
            x,y = self.action[0]
            if len(self.action) > 1:
                x,y = self.action[1]
            t = self.grid.tile_at(x,y)
            u = self.grid.unit_at(x,y)
            if u:
                col = u.team.color
                info3 = [(u.name,col+"!"),
                         ("DEF +%d"%t.defense,col),
                         ("HP %d%% %s"%(u.hp,dmg2),col)]
            

        return report, info1, info2, info3

    # This sets the state back to start while also restoring the previous
    # checkpoint of the world. When the controller gets CTRL_UNDO, it is
    # supposed to set its camera's grid to the new one.
    def start_over(self):
        self.action = []
        self.state = "play"
        self.choices = []
        self.grid = copy.deepcopy(self.checkpoint)
        return CTRL_UNDO

    # When a move is completed and we return to the start state, we
    # change the checkpoint and save the move in our history.
    def commit(self):
        self.history.append((self.checkpoint,self.action))
        self.action = []
        self.state = "play"
        self.choices = []
        self.checkpoint = copy.deepcopy(self.grid)
        return self.transition("play")

    # When we undo, we go back to a previous spot in the history.
    def undo(self, total=False):
        if len(self.history) > 0:
            if total:
                cp = self.restartcopy
                self.history = []
                self.start = True
            else:
                cp,action = self.history.pop()
            self.grid = cp
            self.checkpoint = copy.deepcopy(cp)
        self.action = []
        self.state = "play"
        self.choices = []
        return CTRL_UNDO

    #
    def start_turn(self):
        self.restartcopy = copy.deepcopy(self.grid)
        t = self.grid.current_team()

        # Give the player their money.
        for tile in self.grid.all_tiles():
            if tile.team is t:
                u = tile.unit
                if u and u.team is t and u.hp < 100 and u.name in tile.repair:
                    u.hp = min(100,u.hp+tile.repair[u.name])
                else:
                    t.cash += tile.cash

        # Make the turn-start alert.
        m1 = "%s: Day %d"%(self.grid.name, self.grid.day)
        m2 = "%s - move out!"%t.name
        w = max(len(m1),len(m2))+1
        a = widgets.Alert(w,2,m1+"\n"+m2,t.color)
        a.time = 50
        self.alerts.append((a,"c"))

        self.checkpoint = copy.deepcopy(self.grid)
        self.start = False

    # Mark the team as defeated. This destroys all of their units, sets their
    # funds to zero, and marks them as inactive, unable to take future turns.
    # Properties are still left intact - capturing the enemy HQ will reward
    # you by giving you all of the properties belonging to the team.
    def defeated(self, team):
        team.active = False
        for (tx,ty) in self.grid.all_tiles_xy():
            u = self.grid.unit_at(tx,ty)
            if u and u.team == team:
                self.grid.remove_unit(tx,ty)
        self.grid.units = [u for u in self.grid.units if u.team is not team]

        m = "%s has been defeated!"%(team.name)
        a = widgets.Alert(len(m)+1,1,m,team.color)
        a.time = 50
        self.alerts.append((a,"c"))

    # When we end the turn, we flush the history buffer and save a new
    # checkpoint.
    def end_turn(self):
        if self.state != None and self.action != []:
            raise Exception("Can't end right now")

        self.start = True
        for u in self.grid.units:
            u.ready = True
        self.data["history"].append([acts for (cp,acts) in self.history])
        self.grid.end_turn()
        self.history = []
        self.action = []
        self.choices = []
        self.checkpoint = copy.deepcopy(self.grid)

        # Finally, figure out if we've won. If we have, then put the map in
        # "finished" mode and allow the player to leave. The game is only
        # won when the final player ends their turn.
        winner = True
        for at in [t for t in self.grid.teams if t.active]:
            for ot in [t for t in self.grid.teams if t.active]:
                if not at.allied(ot):
                    winner = False
        if winner:
            self.winners = [t for t in self.grid.teams if t.active]
            #self.state = "over"

        return self.transition("play")

    # This sets the new state and returns the appropriate code
    # to the caller for what kind of input should come next.
    def transition(self, new_state):
        self.state = new_state
        if   self.state == "play"     : return CTRL_COORD
        elif self.state == "main menu": return CTRL_MENU
        elif self.state == "moving"   : return CTRL_COORD
        elif self.state == "unload"   : return CTRL_MENU
        elif self.state == "unload drop": return CTRL_COORD
        elif self.state == "action"   : return CTRL_MENU
        elif self.state == "attacking": return CTRL_COORD
        elif self.state == "building" : return CTRL_MENU

        elif self.state == "edit"     : return CTRL_COORD
        elif self.state == "edit menu": return CTRL_MENU
        elif self.state == "edit unit": return CTRL_MENU
        elif self.state == "edit terrain": return CTRL_MENU
        elif self.state == "unit team": return CTRL_MENU
        elif self.state == "draw terrain": return CTRL_COORD
        elif self.state == "terrain team": return CTRL_MENU
        elif self.state == "save map": return CTRL_EDITOR
        elif self.state == "rule unit": return CTRL_MENU
        elif self.state == "rule terrain": return CTRL_MENU
        elif self.state == "page unit": return CTRL_EDITOR
        elif self.state == "page terrain": return CTRL_EDITOR
        elif self.state == "edit teams": return CTRL_MENU

        elif self.state == "quit": return CTRL_QUIT

        else: raise Exception("No such state.")

    # This processes input of two types: coordinates and strings.
    # A string is the input from a menu, such as "attack" or "wait".
    # A coordinate is an x,y location on the grid.
    # Has one of four return values:
    #     None: Tell the controller to do nothing
    #     menu: Tell the controller to render a menu
    #     coord: Tell the controller to give it a coord
    #     undo: Tell the controller to reload the grid
    def process(self, c):
        if   self.state == "play"     : return self.process_play(c)
        elif self.state == "main menu": return self.process_main_menu(c)
        elif self.state == "moving"   : return self.process_moving(c)
        elif self.state == "action"   : return self.process_action(c)
        elif self.state == "attacking": return self.process_attacking(c)
        elif self.state == "building" : return self.process_building(c)
        elif self.state == "unload"   : return self.process_unload(c)
        elif self.state == "unload drop": return self.process_unload_drop(c)

        elif self.state == "edit"     : return self.process_edit(c)
        elif self.state == "edit menu": return self.process_edit_menu(c)
        elif self.state == "edit unit": return self.process_edit_unit(c)
        elif self.state == "edit terrain": return self.process_edit_terrain(c)
        elif self.state == "unit team": return self.process_unit_team(c)
        elif self.state == "terrain team": return self.process_terrain_team(c)
        elif self.state == "draw terrain": return self.process_draw_terrain(c)
        elif self.state == "save map": return self.process_save_map(c)
        elif self.state == "rule unit": return self.process_rule_unit(c)
        elif self.state == "rule terrain": return self.process_rule_terrain(c)
        elif self.state == "page unit": return self.process_page_unit(c)
        elif self.state == "page terrain": return self.process_page_terrain(c)
        elif self.state == "edit teams": return self.process_edit_teams(c)


    # State    : Play (expected input, tuple)
    # Expected : Tuple (unit or friendly factory)
    # Next step: If unit: coordinates of range of unit
    #            If factory: list of possible buildables
    def process_play(self, coord):
        if type(coord) not in (tuple,list):
            raise Exception("Expected tuple!")
        x,y = coord
        t = self.grid.tile_at(x,y)
        u = self.grid.unit_at(x,y)
        team = self.grid.current_team()

        # If no unit, check for terrain
        self.action.append((x,y))
        if t and not u and "build" in t.properties and t.team is team:
            self.choices = []
            for b in t.build:
                p = t.build[b]
                if p <= team.cash:
                    self.choices.append("%s $%d"%(b,p))
            self.choices.append("Cancel")
            return self.transition("building")

        # Even if the unit isn't ours (or isn't ready) we still enter the
        # "move" state so that we can see its movement range. Actually
        # moving the unit will be stopped at the process_moving step.
        if u:
            self.choices = []
            for (qx,qy) in self.get_move_range(x,y):
                unit = self.grid.unit_at(qx,qy)
                keep = True
                if unit:
                    keep = False
                    if unit is u: keep = True
                    if unit.name == u.name: keep = True
                    if ("carry" in unit.properties and u.name in unit.carry
                        and len(unit.carrying) < unit.capacity):
                        keep = True
                if keep:
                    self.choices.append((qx,qy))
            return self.transition("moving")

        # Whatever else happens, main menu.
        self.choices = ["Back","End Turn","Surrender","Undo","Start Over"]
        return self.transition("main menu")


    # State    : Moving (expected input, tuple)
    # Expected : Tuple in range
    # Next step: If in range, move
    #            If out of range, cancel
    def process_moving(self, coord):
        if type(coord) not in (tuple,list):
            raise Exception("Expected tuple!")
        x,y = coord
        ox,oy = self.action[0]
        u = self.grid.unit_at(ox,oy)
        team = self.grid.current_team()
        utarg = self.grid.unit_at(x,y)
        
        # If coord was in range, move the unit and return possible actions.
        if (x,y) in self.choices and u.team is team and u.ready:
            self.action.append((x,y))

            # Join units with the same name.
            if (utarg and utarg.team is team and 
               utarg.name == u.name and utarg is not u):
                self.grid.remove_unit(ox,oy)
                start_hp = utarg.hp
                utarg.hp = min(100, utarg.hp+u.hp)
                a = widgets.HPAlert(6,1,utarg.team.color,start_hp,utarg.hp,0)
                a.time = (utarg.hp - start_hp) + 50
                self.alerts += [(a,"tr")]
                utarg.ready = False
                return self.commit()
            if (utarg and utarg is not u and "carry" in utarg.properties):
                self.grid.tile_at(ox,oy).unit = None
                utarg.carrying.append(u)
                return self.commit()

            self.choices = []

            moved = (x,y)!=(ox,oy)
            if moved:
                t = self.grid.tile_at(ox,oy)
                t.hp = 100

            # Determine if a target is in range.
            attackable = False
            for px,py in self.grid.get_range((x,y),u.rng[0],u.rng[1]):
                a = self.grid.unit_at(px,py)
                if a and not a.allied(u):
                    attackable = True
            if "indirect" in u.properties and moved:
                attackable = False
            if attackable:
                self.choices.append("Attack")

            # If the cell you are on is capturable, add that option to
            # the list.
            t = self.grid.tile_at(x,y)
            if ("capture" in t.properties and "capture" in u.properties
                and not team.allied(t.team)):
                self.choices.append("Capture")
            if (len(u.carrying) > 0):
                self.choices.append("Unload")

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
            return self.start_over()
        
        # End my turn.
        if opt == "End Turn":
            self.action = []
            return self.end_turn()

        if opt == "Undo":
            return self.undo()

        if opt == "Start Over":
            return self.undo(True)

        if opt == "Surrender":
            self.defeated(self.grid.current_team())
            self.action.append(opt)
            return self.commit()


    # State: main menu (expected, menu option)
    def process_building(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")

        # Leave the menu.
        if opt == "Cancel":
            return self.start_over()
        
        else:
            x,y = self.action[0]
            team = self.grid.current_team()
            unit, cost = opt.rsplit(None,1)
            u = self.make_unit({"name":unit})
            self.grid.add_unit(u, team, x, y)
            team.cash -= int(cost[1:])
            u.ready = False
            self.action.append(opt)
            return self.commit()

    # 
    def process_action(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")

        if opt == "Unload":
            self.choices = []

            x,y = self.action[1]
            me = self.grid.unit_at(x,y)
            i = 0
            for u in me.carrying:
                self.choices.append("%d %s %d%%"%(i, u.name, u.hp))
                i+=1
            self.choices.append("Done")
            self.action.append(opt)
            return self.transition("unload")

        if opt == "Attack":
            self.choices = []

            x,y = self.action[-1]
            u = self.grid.unit_at(x,y)

            # Get possible targets.
            for px,py in self.grid.get_range((x,y),u.rng[0],u.rng[1]):
                a = self.grid.unit_at(px,py)
                if a and not a.allied(u):
                    self.choices.append((px,py))

            self.action.append(opt)
            return self.transition("attacking")

        if opt == "Capture":
            self.choices = []

            x,y = self.action[-1]
            t = self.grid.tile_at(x,y)
            unit = t.unit
            unit.ready = False

            # Capturing.
            start_hp = t.hp
            t.hp -= int(unit.hp*.5)
            if t.hp <= 0:
                t.hp = 0
            col = t.team.color if t.team else "w"
            a = widgets.HPAlert(6,1,col,start_hp,t.hp,0)
            a.time = (start_hp - t.hp) + 50
            self.alerts += [(a,"tr")]
            if t.hp == 0:
                t.hp = 100
                old = t.team
                t.team = unit.team
                if "hq" in t.properties:
                    t.properties.remove("hq")
                    if old:
                        if old.active:
                            self.defeated(old)
                        for tt in self.grid.all_tiles():
                            if tt.team is old:
                                tt.team = unit.team
            
            self.action.append(opt)
            return self.commit()

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
    def process_unload(self, opt):
        if opt not in self.choices:
            raise Exception("Nope.")

        x,y = self.action[1]
        t = self.grid.tile_at(x,y)
        unit = t.unit
        if opt == "Done":
            self.action.append(opt)
            self.choices = []
            unit.ready = False
            return self.commit()
        else:
            self.action.append(opt)
            u = unit.carrying[int(opt.split()[0])]
            self.choices = []
            for (tx,ty) in [(x-1,y),(x,y+1),(x+1,y),(x,y-1)]:
                t = self.grid.tile_at(tx,ty)
                if t and t.name in u.terrain and not t.unit:
                    self.choices.append((tx,ty))
            if len(self.choices) == 0:
                return self.transition("unload")
            else:
                self.action.append(opt)
                return self.transition("unload drop")

            

    #
    def process_unload_drop(self, coord):
        if type(coord) not in (tuple,list):
            raise Exception("Expected tuple!")

        x,y = self.action[1]
        unit = self.grid.unit_at(x,y)
        dropper = int(self.action[-1].split()[0])
        if coord in self.choices:
            self.action.append(coord)
            t = self.grid.tile_at(*coord)
            t.unit = unit.carrying.pop(dropper)
            t.unit.ready = False
        else:
            self.action.pop()

        self.choices = []
        x,y = self.action[1]
        me = self.grid.unit_at(x,y)
        i = 0
        for u in me.carrying:
            self.choices.append("%d %s %d%%"%(i, u.name, u.hp))
            i += 1
        self.choices.append("Done")
        return self.transition("unload")


    #
    def process_attacking(self, coord):
        if type(coord) not in (tuple,list):
            raise Exception("Expected tuple!")
        x,y = coord

        if coord in self.choices:
            ox,oy = self.action[-2]
            self.action.append((ox,oy))
            a, d = self.grid.unit_at(ox,oy), self.grid.unit_at(x,y)
            
            start_hp = d.hp, a.hp
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
            self.alerts += [(a1,"tr"),(a2,"bl")]
            a.ready = False

            return self.commit()



        else:
            return self.start_over()






    # This is the root state for the editor. We put the editor states
    # in the same system as the rules so that we can take advantage of
    # the "make" constructors.
    def process_edit(self, coord):
        if type(coord) not in (tuple,list):
            raise Exception("Expected tuple!")
        x,y = coord
        u = self.grid.unit_at(x,y)
        self.action = [(x,y)]
        
        self.choices = ["Repeat","Place Unit", "Place Terrain","Edit Teams",
                        "Unit Rules", "Terrain Rules","Save Map",
                        "Quit to Main Menu","Back"]

        return self.transition("edit menu")

    # 
    def process_edit_menu(self,opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        self.choices = []
        x,y = self.action[0]

        if opt == "Repeat":
            if not self.last_edit:
                self.action = []
                return self.transition("edit")
            kind,thing,team = self.last_edit
            if kind == "terrain":
                self.action.append(thing)
                if team:
                    self.action.append(team)
                self.choices = [(x,y)]
                return self.transition("draw terrain")
            elif kind == "unit":
                self.action.append(thing)
                self.choices = [team]
                return self.process_unit_team(team)
            
        if opt == "Place Unit":
            self.choices = ["(None)"]
            for u in self.data["rules"]["units"]:
                self.choices.append(u)
            return self.transition("edit unit")
        
        if opt == "Place Terrain":
            self.choices = ["(None)"]
            for u in self.data["rules"]["terrain"]:
                self.choices.append(u)
            return self.transition("edit terrain")

        if opt == "Edit Teams":
            self.choices = ["Red","Blue","Green","Yellow","Cyan",
                            "Magenta","Done"]
            for x,y in self.grid.all_tiles_xy():
                if self.grid.unit_at(x,y):
                    self.grid.remove_unit(x,y)
                t = self.grid.tile_at(x,y)
                t.team = None
            self.grid.teams = []
            return self.transition("edit teams")

        if opt == "Unit Rules":
            self.choices = []
            for u in self.data["rules"]["units"]:
                self.choices.append(u)
            self.choices.append("(New Unit)")
            return self.transition("rule unit")

        if opt == "Terrain Rules":
            self.choices = []
            for u in self.data["rules"]["terrain"]:
                self.choices.append(u)
            self.choices.append("(New Terrain)")
            return self.transition("rule terrain")

        if opt == "Save Map":
            for t in self.grid.teams[:]:
                kill = True
                for c in self.grid.all_tiles():
                    if c.unit and c.unit.team is t: kill = False
                    if c.team is t and "hq" in c.properties: kill = False
                if kill:
                    self.grid.teams.remove(t)
            self.choices = {"Map Name": {"data":"","type":"str 15"}}
            return self.transition("save map")

        if opt == "Quit to Main Menu":
            return self.transition("quit")

        if opt == "Back":
            return self.transition("edit")

        

    # 
    def process_edit_teams(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        self.choices.remove(opt)
        
        if opt == "Done" and len(self.grid.teams) == 0:
            self.choices.append(opt)
            return self.transition("edit teams")
        elif opt == "Done" and len(self.grid.teams) > 0:
            return self.transition("edit")
        else:
            t = self.make_team({"name":opt, "color":opt[0].lower()})
            self.grid.teams.append(t)
            return self.transition("edit teams")
    

    # 
    def process_edit_unit(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        self.choices = []
        x,y = self.action[0]
        u = self.grid.unit_at(x,y)
        self.action.append(opt)

        if opt == "(None)":
            if u:
                self.grid.remove_unit(x,y)
            self.action = []
            return self.transition("edit")

        # Before moving forward, we need to know the team.
        self.choices = []
        for t in self.grid.teams:
            self.choices.append(t.name)
        return self.transition("unit team")

    # 
    def process_unit_team(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        self.choices = []
        x,y = self.action[0]
        t = self.grid.tile_at(x,y)
        self.action.append(opt)

        if t:
            if t.unit:
                self.grid.remove_unit(x,y)
            u = self.make_unit({"name": self.action[1]})
            team = None
            for q in self.grid.teams:
                if q.name == opt:
                    team = q
            self.grid.add_unit(u, team, x, y)
            self.last_edit = "unit",self.action[1],opt

        return self.transition("edit")

    # Editing terrain is slightly different. After picking the type of
    # terrain you want, you pick another coordinate, and a box is filled
    # between the two endpoints.
    def process_edit_terrain(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        self.choices = []
        x,y = self.action[0]
        u = self.grid.unit_at(x,y)
        self.action.append(opt)
        self.choices = [(x,y)]

        if opt == "(None)":
            return self.transition("draw terrain")

        t = self.make_cell({"name":opt})
        if "capture" in t.properties:
            self.choices = ["(None)"]
            for t in self.grid.teams:
                self.choices.append(t.name)
            return self.transition("terrain team")
        return self.transition("draw terrain")

    # If the tile in question is capturable, then we need to pick the
    # team.
    def process_terrain_team(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        x,y = self.action[0]
        self.choices = [(x,y)]
        x,y = self.action[0]
        self.action.append(opt)
        return self.transition("draw terrain")

    # Now, pick the endpoint.
    def process_draw_terrain(self, coord):
        if type(coord) not in (tuple,list):
            raise Exception("Expected tuple!")
        ex,ey = coord
        ox,oy = self.action[0]

        if ex < ox:
            ex,ox = ox,ex
        if ey < oy:
            ey,oy = oy,ey

        # Now fill!
        for x in range(ox,ex+1):
            for y in range(oy,ey+1):
                t = self.grid.tile_at(x,y)
                if self.action[1] == "(None)":
                    u = self.grid.unit_at(x,y)
                    if u:
                        self.grid.remove_unit(x,y)
                    self.grid.grid.pop((x,y),None)
                    self.last_edit = "terrain","(None)",None
                else:
                    tile = self.make_cell({"name":self.action[1]})
                    self.last_edit = "terrain",self.action[1],None
                    if len(self.action) > 2:
                        team = None
                        for q in self.grid.teams:
                            if q.name == self.action[2]:
                                team = q
                        tile.team = team
                        self.last_edit="terrain",self.action[1],self.action[2]
                    if t:
                        tile.unit = t.unit
                    self.grid.grid[(x,y)] = tile
                    

        self.choices = []
        return self.transition("edit")
                        
    #
    def process_save_map(self, opt):
        if "Map Name" not in opt:
            raise Exception("Not there!")
        newname = opt["Map Name"]
        if len(newname) > 15:
            raise Exception("Too long.")

        self.choices = []
        if len(opt) != 0:
            self.grid.name = newname
            data = self.export(True)
            newname = newname.replace(" ","_")
            storage.save(data, "maps","%s.json"%newname)

        self.action = []
        return self.transition("edit")


    def process_rule_unit(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        self.action.append(opt)

        u = None
        if opt != "(New Unit)":
            u = self.make_unit({"name":opt})

        props = u.properties if u else []
        defaults = {}
        defaults["Name"] = u.name if u else ""
        defaults["Icon"] = u.icon if u else ""
        defaults["Move"] = str(u.move) if u else ""
        defaults["Is Indirect?"] = "Yes" if "indirect" in props else "No"
        defaults["Range (from)"] = str(u.rng[0]) if u else "1"
        defaults["Range (to)"] = str(u.rng[1]) if u else "1"
        defaults["Can Carry?"] = "Yes" if "carry" in props else "No"
        defaults["Capacity"] = str(u.capacity) if u else ""
        defaults["No Cover?"] = "Yes" if "nocover" in props else "No"
        defaults["Can Capture?"] = "Yes" if "capture" in props else "No"
        self.choices = { "Name": {"data": defaults["Name"],
                                  "type": "str 12",
                                  "ordering": 1 },
                         "Icon": {"data": defaults["Icon"],
                                  "type": "str 1",
                                  "ordering": 2},
                         "Move": {"data": defaults["Move"],
                                  "type": "int",
                                  "ordering": 3 },
                         "Is Indirect?": {"data": defaults["Is Indirect?"],
                                          "type": "bool",
                                          "ordering": 4},
                         "Range (from)": {"data": defaults["Range (from)"],
                                          "type": "int",
                                          "ordering": 5 },
                         "Range (to)": {"data": defaults["Range (to)"],
                                        "type": "int",
                                        "ordering": 6 },
                         "Can Carry?": {"data": defaults["Can Carry?"],
                                        "type": "bool",
                                        "ordering": 7},
                         "Capacity": {"data": defaults["Capacity"],
                                      "type": "int",
                                      "ordering": 8},
                         "No Cover?": {"data": defaults["No Cover?"],
                                       "type": "bool",
                                       "ordering": 9},
                         "Can Capture?": {"data": defaults["Can Capture?"],
                                          "type": "bool",
                                          "ordering": 10}
                       }
        return self.transition("page unit")

    # The first page contains flags and base properties.
    # The second contains movement.
    # The third contains damage.
    def process_page_unit(self, data):
        u = None
        oldname = self.action[1]
        if oldname != "(New Unit)":
            u = self.make_unit({"name":oldname})

        if len(self.action) == 2:
            self.action.append(1)

            if not u:
                self.data["rules"]["units"][data["Name"]] = {}
            elif oldname != data["Name"]:
                x = self.data["rules"]["units"].pop(self.action[1])
                self.data["rules"]["units"][data["Name"]] = x
                for t in self.grid.all_tiles_xy():
                    q = self.grid.unit_at(t[0],t[1])
                    if q and q.name == oldname:
                        self.grid.remove_unit(t[0],t[1])
                for t in self.data["rules"]["units"]:
                    if oldname in self.data["rules"]["units"][t]["damage"]:
                        self.data["rules"]["units"][t]["damage"].pop(oldname)
                for t in self.data["rules"]["terrain"]:
                    if "build" in self.data["rules"]["terrain"][t]:
                     if oldname in self.data["rules"]["terrain"][t]["build"]:
                      self.data["rules"]["terrain"][t]["build"].pop(oldname)
                    if "repair" in self.data["rules"]["terrain"][t]:
                     if oldname in self.data["rules"]["terrain"][t]["repair"]:
                      self.data["rules"]["terrain"][t]["repair"].pop(oldname)

            ed = self.data["rules"]["units"][data["Name"]]

            ed["icon"] = data["Icon"] if data["Icon"] else "?"
            ed["move"] = int(data["Move"]) if data["Move"] else 0
            lo = int(data["Range (from)"]) if data["Range (from)"] else 0
            hi = int(data["Range (to)"]) if data["Range (to)"] else 0
            ed["range"] = [lo,hi]
            ed["capacity"] = int(data["Capacity"]) if data["Capacity"] else 0
            ed["properties"] = []
            if data["Is Indirect?"] == "Yes":
                ed["properties"].append("indirect")
            if data["Can Carry?"] == "Yes" :
                ed["properties"].append("carry")
            if data["No Cover?"] == "Yes":
                ed["properties"].append("nocover")
            if data["Can Capture?"] == "Yes":
                ed["properties"].append("capture")
            if not u:
                ed["terrain"] = {}
                ed["damage"] = {}

            self.action[1] = data["Name"]

            self.choices = {}
            for t in self.data["rules"]["terrain"]:
                s = ""
                if t in ed["terrain"]:
                    s = str(ed["terrain"][t])
                self.choices[t] = {"data": s,
                                   "type": "int"}

            return self.transition("page unit")
        elif len(self.action) == 3:
            self.action.append(2)

            ed = self.data["rules"]["units"][self.action[1]]
            ed["terrain"] = {}
            for d in data:
                if data[d]:
                    ed["terrain"][d] = int(data[d])
            
            self.choices = {}
            for t in self.data["rules"]["units"]:
                s = ""
                if t in ed["damage"]:
                    s = str(ed["damage"][t])
                self.choices[t] = {"data": s,
                                   "type": "int"}

            return self.transition("page unit")
        elif len(self.action) == 4:

            ed = self.data["rules"]["units"][self.action[1]]
            ed["damage"] = {}
            for d in data:
                if data[d]:
                    ed["damage"][d] = int(data[d])
            self.choices = {}
            self.action = []

        return self.transition("edit")

    def process_rule_terrain(self, opt):
        if opt not in self.choices:
            raise Exception("Invalid option.")
        self.action.append(opt)
        self.choices = {}

        t = None
        if opt != "(New Terrain)":
            t = self.make_cell({"name":opt})

        props = t.properties if t else []
        defaults = {}
        defaults["Name"] = t.name if t else ""
        defaults["Icon"] = t.icon if t else ""
        defaults["Color"] = t.color if t else ""
        defaults["Cash"] = str(t.cash) if t else ""
        defaults["Capture?"] = "Yes" if "capture" in props else "No"
        defaults["HQ?"] = "Yes" if "hq" in props else "No"
        defaults["Build?"] = "Yes" if "build" in props else "No"
        defaults["Repair?"] = "Yes" if "repair" in props else "No"
        self.choices = { "Name": {"data": defaults["Name"],
                                  "type": "str 12",
                                  "ordering": 1 },
                         "Icon": {"data": defaults["Icon"],
                                  "type": "str 1",
                                  "ordering": 2},
                         "Color": {"data": defaults["Color"],
                                  "type": "str 1",
                                  "ordering": 3 },
                         "Cash": {"data": defaults["Cash"],
                                  "type": "int",
                                  "ordering": 4 },
                         "Capture?": {"data": defaults["Capture?"],
                                      "type": "bool",
                                      "ordering": 7},
                         "HQ?": {"data": defaults["HQ?"],
                                 "type": "bool",
                                 "ordering": 9},
                         "Build?": {"data": defaults["Build?"],
                                    "type": "bool",
                                    "ordering": 10},
                         "Repair?": {"data": defaults["Repair?"],
                                     "type": "bool",
                                     "ordering": 11}
                       }
        return self.transition("page terrain")




    def process_page_terrain(self, data):
        t = None
        oldname = self.action[1]
        if oldname != "(New Terrain)":
            t = self.make_cell({"name":oldname})

        if len(self.action) == 2:
            self.action.append(1)

            if not t:
                self.data["rules"]["terrain"][data["Name"]] = {}
            elif oldname != data["Name"]:
                x = self.data["rules"]["terrain"].pop(oldname)
                self.data["rules"]["terrain"][data["Name"]] = x
                for t in self.grid.all_tiles_xy():
                    q = self.grid.tile_at(t[0],t[1])
                    if q and q.name == oldname:
                        if self.grid.unit_at(t[0],t[1]):
                            self.grid.remove_unit(t[0],t[1])
                        self.grid.grid.pop((t[0],t[1]))
                for t in self.data["rules"]["units"]:
                    if oldname in self.data["rules"]["units"][t]["terrain"]:
                        self.data["rules"]["units"][t]["terrain"].pop(oldname)


            ed = self.data["rules"]["terrain"][data["Name"]]

            ed["icon"] = data["Icon"] if data["Icon"] else "?"
            ed["color"] = data["Color"]
            ed["cash"] = int(data["Cash"]) if data["Cash"] else 0
            if data["Capture?"] == "Yes":
                ed["properties"].append("capture")
            if data["HQ?"] == "Yes" :
                ed["properties"].append("hq")
            if data["Build?"] == "Yes":
                ed["properties"].append("build")
            if data["Repair?"] == "Yes":
                ed["properties"].append("repair")
            if not t:
                ed["build"] = {}
                ed["repair"] = {}

            self.action[1] = data["Name"]

            self.choices = {}
            for t in self.data["rules"]["units"]:
                s = ""
                if t in ed["build"]:
                    s = str(ed["build"][t])
                self.choices[t] = {"data": s,
                                   "type": "int"}

            return self.transition("page terrain")

        if len(self.action) == 3:
            self.action.append(2)

            ed = self.data["rules"]["terrain"][oldname]
            ed["build"] = {}
            for d in data:
                if data[d]:
                    ed["build"][d] = int(data[d])
            
            self.choices = {}            
            for t in self.data["rules"]["units"]:
                s = ""
                if t in ed["repair"]:
                    s = str(ed["repair"][t])
                self.choices[t] = {"data": s,
                                   "type": "int"}

            return self.transition("page terrain")
        if len(self.action) == 4:
            ed = self.data["rules"]["terrain"][oldname]
            ed["repair"] = {}
            for d in data:
                if data[d]:
                    ed["repair"][d] = int(data[d])
            
            self.choices = {}            
            self.action = []

            # I'm not even trying anymore. ;_;

        return self.transition("edit")


        

