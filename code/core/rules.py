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
        elif len(t.build) > 0 and t.team is grid.current_team():
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
        for b,v in sorted(tile.build.items(), key=lambda x:x[1]):
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

        # Calculate movement range. TODO, calc fuel cost as well.
        report = []
        def _floodfill(pos,r,top=False):
            a,b = pos
            t,u = grid.get_at(a,b)
            if t and (not u or u.is_allied(unit)):
                if not top:
                    r -= unit.terrain.get(t.terrain,r)
                if (a,b) not in report and t.terrain in unit.terrain:
                    report.append((a,b))
                if r > 0:
                    _floodfill((a-1,b),r)
                    _floodfill((a+1,b),r)
                    _floodfill((a,b-1),r)
                    _floodfill((a,b+1),r)
        _floodfill((x,y),unit.move,True)

        # Now filter the results. We have to do something more complex
        # than a list comprehension.
        self.choices = []
        for (a,b) in report:
            add = True
            t,u = grid.get_at(a,b)
            if not t: add = False
            elif u is unit: add = True
            elif u and u.team is not unit.team: add = False
            elif u and u.team is unit.team and u.unit == unit.unit: add = True
            elif u and u.team is unit.team and unit.unit in u.carry: add = True
 
            if add:
                self.choices.append((a,b))

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
        if (u2 and u2.unit == u1.unit and u1 is not u2):
            grid.remove_unit(u1)
            u2.hp = min(u1.hp+u2.hp,100)
            u2.fuel = min(u1.fuel+u2.fuel,u2.max_fuel)
            u2.ammo = min(u1.ammo+u2.ammo,u2.max_ammo)
            u2.done()
            return ACT_COMMIT
        if (u2 and u2.capacity > 0 and u1.unit in u2.carry and
           len(u2.carrying) < u2.capacity and u1 is not u2):
            grid.load_unit(u1,u2)
            return ACT_COMMIT

        grid.move_unit(u1,x,y)
        t1.hp = 100
        moved = False
        if (ox,oy) != (x,y):
            moved = True
        return Unit_Act(x,y,grid,moved)


# UNIT ACT follows MOVE and expects MENU.
#  If a unit is in range, there is ammo, etc, allow attack.
#  If the unit and current terrain are capturable, allow capture.
class Unit_Act(Action):
    def __init__(self,x,y,grid,moved):
        self.form = FORM_MENU
        self.choices = []
        self.start = x,y
        t,u = grid.get_at(x,y)

        # Determine if we can attack anything.
        lo,hi = u.rang
        if (lo>0 and hi>0 and (not u.is_indirect or
                (u.is_indirect and not moved))):
            can_attack = False
            for (a,b) in grid.get_range(x,y,lo,hi):
                targ = grid.unit_at(a,b)
                if (targ and not u.is_allied(targ) 
                         and (targ.unit in u.secondary or 
                         (targ.unit in u.primary and u.ammo > 0))):
                    can_attack = True
            if can_attack:
                    self.choices.append("Attack")

        # If we're carrying anything, try to unload it.
        if u and len(u.carrying) > 0:
            self.choices.append("Unload")

        # Can we capture this tile?
        if t.can_capture and u and u.capture > 0:
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
            new_hp = max(old_hp-int(u.hp*u.capture*.01),0)

            t.hp = new_hp
            if t.hp == 0:
                if t.is_hq and t.team:
                    grid.purge(t.team)
                    t.team.active = False
                    #message t.team loses
                    t.is_hq = False
                    for (tx,ty) in grid.all_tiles_xy():
                        ot = grid.tile_at(tx,ty)
                        if ot.team is t.team:
                            ot.team = u.team
                            ot.is_hq = False
                            ot.hp = 100
                            grid.change_tile(ot,tx,ty)
                t.team = u.team
                t.hp = 100
                grid.change_tile(t,x,y)
            u.done()
            return ACT_COMMIT

        if act == "Unload":
            return Unload(x,y,grid)

        if act == "Attack":
            return Attack(x,y,grid)

        if act == "Wait":
            u.done()
            return ACT_COMMIT

        if act == "Cancel":
            return ACT_TRASH

# ACTION follows UNIT ACT when target in range. Expects COORD.
# The provided coord should be one that contains an enemy unit.
class Attack(Action):
    def __init__(self, x, y, grid):
        self.start = x,y
        self.form = FORM_COORD
        self.choices = []

        u = grid.unit_at(x,y)
        lo,hi = u.rang
        for (a,b) in grid.get_range(x,y,lo,hi):
            targ = grid.unit_at(a,b)
            if (targ and not u.is_allied(targ) 
                     and (targ.unit in u.secondary or 
                     (targ.unit in u.primary and u.ammo > 0))):
                self.choices.append((a,b))

    # 
    def perform(self, act, grid):
        if act in self.choices:
            ax,ay = self.start
            dx,dy = act
            atk_t,atk_u = grid.get_at(ax,ay)
            def_t,def_u = grid.get_at(dx,dy)
            d = grid.dist((ax,ay),(dx,dy))
            start_ahp, start_dhp = atk_u.hp, def_u.hp

            # Calculate damage.
            a_dmg,prim = atk_u.simulate(def_u, def_t.cover)
            if a_dmg: def_u.hp = max(0,def_u.hp-a_dmg)
            if prim: atk_u.ammo -= 1

            # Only counter if hp > 0 and not indirect.
            if def_u.hp > 0 and not def_u.is_indirect and def_u.in_range(d):
                d_dmg,prim = def_u.simulate(atk_u, atk_t.cover)
                if d_dmg: atk_u.hp = max(0,atk_u.hp-d_dmg)
                if prim: def_u.ammo -= 1

            # draw hp countdown from start_ahp to atk_u.hp
            # draw hp countdown from start_dhp to def_u.hp

            # Remove dead units (and all carriees) from grid.
            if atk_u.hp > 0:
                atk_u.done()
            else:
                grid.remove_unit(atk_u)
                atk_t.hp = 100
            if def_u.hp <= 0:
                grid.remove_unit(def_u)
                def_t.hp = 100

            ateam = 0
            dteam = 0
            for u in grid.units:
                if u.team is atk_u.team: ateam += 1
                if u.team is def_u.team: dteam += 1
            for (score,team) in ((ateam,atk_u.team),(dteam,def_u.team)):
                if score == 0:
                    team.active = False
                    #print messagfe

            return ACT_COMMIT
        else:
            return ACT_TRASH


# UNLOAD follows UNIT ACT when carrying units. A unit can unload
# when it's carrying - even if it isn't supposed to load in the
# first place.
class Unload(Action):
    def __init__(self, x, y, grid, already=None):
        self.start = x,y
        self.form = FORM_MENU
        self.choices = []
        self.already = []
        if already:
            self.already += already

        u = grid.unit_at(x,y)
        for i,c in enumerate(u.carrying):
            if i not in self.already:
                self.choices.append("%d: %s (%d%%)"%(i,c.unit,c.hp))
        self.choices.append("Done")

    # This performs the unload. But the user now has to pick a
    # destination for the unit.
    def perform(self, act, grid):
        if act not in self.choices:
            raise Exception("Illegal input: %s"%str(act))
        
        x,y = self.start
        u = grid.unit_at(x,y)
        if act == "Done":
            u.done()
            return ACT_COMMIT
        else:
            i = int(act.split(":",1)[0])
            return Unload_Placement(x,y,grid,i,self.already)

class Unload_Placement(Action):
    def __init__(self, x, y, grid, i, already):
        u = grid.unit_at(x,y)
        self.target = i
        self.already = already+[i]
        unit = u.carrying[i]
        self.choices = []
        self.form = FORM_COORD
        self.start = x,y
        for (a,b) in grid.get_range(x,y,1):
            t,u = grid.get_at(a,b)
            if not u or (t and unit.terrain.get(t.terrain,0) > 0):
                self.choices.append((a,b))

    def perform(self, act, grid):
        x,y = self.start
        if act in self.choices:
            u = grid.unit_at(x,y) # there's no reason to keep typing this
            dx,dy = act
            grid.unload_unit(u, self.target, dx, dy)
            grid.unit_at(dx,dy).done()
        return Unload(x, y, grid, self.already)
        
        
