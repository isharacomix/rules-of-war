# Entities are TILES, OBJECTS, and TEAMS.

from graphics import sprites, draw

# A Team is one "side" of a session in a game of RoW. Teams control Tiles and
# Units, and may be allied with other teams. When a team is set to be inactive,
# that is the indication that it has lost the game and will not longer act.
class Team(object):
    def __init__(self, data):
        self.name = data["name"]
        self.color = data["color"]
        self.cash = 0
        self.active = True
        self.allies = []
        self.control = "human"

    # Returns True if this team is allied with the other team.
    def is_allied(self, other):
        if other in self.allies or other is self:
            return True
        return False

# A Tile is a location on the grid that can hold up to one unit.
class Tile(object):
    def __init__(self, terrain, data):
        self.terrain = terrain
        self.icon = data["icon"]
        self.color = data["color"]
        self.cover = data["cover"]
        self.income = data.get("income",0)
        self.hp = 100
        self.team = None
        self.unit = None

        # Set the flag properties for the terrain. A terrain with
        # "capture" can be captured by opponents. Terrain that are
        # marked hq cause the game to be lost by a team if it is
        # captured. A terrain can build if its build dictionary is
        # not empty, and can repair if its repair array is not empty.
        self.can_capture = data.get("capture",False)
        self.is_hq = data.get("hq",False)

        # This highlights the interactions between units and tiles.
        self.build = data.get("build",{})
        self.repair = data.get("repair",{})

    # Returns True if this unit is allied with the other team, tile, or unit.
    def is_allied(self, other):
        if not self.team:
            return False
        if self.team.is_allied(other) or self.team.is_allied(other.team):
            return True
        return False


# Units are the entities on a grid that can be moved about by the player.
# Units have the most programming about them, since they do battle and such.
# UNits are also the only objects to be associated with sprites since they have
# animation.
class Unit(object):
    def __init__(self, unit, data):
        self.unit = unit
        self.icon = data["icon"]
        self.move = data["move"]
        self.rang = data["range"]
        self.max_ammo = data.get("ammo",0)
        self.max_fuel = data["fuel"]
        self.capacity = data.get("capacity",0)
        self.capture = data.get("capture",0)
        self.x = None
        self.y = None
        self.hp = 100
        self.team = None
        self.ready = True
        self.carrying = []
        self.ammo = self.max_ammo
        self.fuel = self.max_fuel

        # Set the animation variables.
        self.anim = self.icon
        self.frame = 0
        self.sprite = sprites.Sprite(0,0,1,1)

        # Read the flag variables. Indirect units may not counter
        # and units with "nocover" do not receive terrain bonuses.
        self.is_indirect = data.get("indirect",False)
        self.no_cover = data.get("nocover",False)
        
        # These are some larger arrays.
        self.primary = data.get("primary",{})
        self.secondary = data.get("secondary",{})
        self.carry = data.get("carry",[])
        self.terrain = data["terrain"]

    # Recursively get all the units that this unit is carrying.
    def get_carrying(self):
        report = []
        for c in self.carrying:
            report.append( c.get_carrying() )
        return report

    # Simulate the damage of this unit attacking the target. Note that 0 damage
    # means that the unit simply can't scratch the target, while None means it
    # can't attack it period. Returns True if the primary weapon was used.
    def simulate(self, target, cover, hp=None):
        if target.no_cover: cover = 0
        if hp is None: hp = self.hp
        if target.unit in self.primary and self.ammo > 0:
            base = self.primary[target.unit]
            return int(base*.01*hp*(1.0-(.01*cover))),True
        elif target.unit in self.secondary:
            base = self.secondary[target.unit]
            return int(base*.01*hp*(1.0-(.01*cover))),False
        return None,None

    # This returns False if out of range and true if in range.
    def in_range(self, dist):
        return (dist >= self.rang[0] and dist <= self.rang[1])

    # This function adds one frame to the animation cycle for the unit.
    def cycle_anim(self):
        self.frame += 1
        frames = [self.icon]
        
        if (self.hp < 90):
            frames.append( str((self.hp//10)+1)  )
        
        self.frame %= len(frames)
        self.anim = frames[self.frame]
        
        # This isn't ideal, but it seems to be the only way to mix a char
        # without recoloring.
        self.sprite.mixc(self.anim,0,0,None,None,None,None)
        #self.sprite.blit(draw.char(0,0,self.anim,None,None,None,None),0,0,True)

    # Returns True if this unit is allied with the other team, tile, or unit.
    def is_allied(self, other):
        if not self.team:
            return False
        if self.team.is_allied(other) or self.team.is_allied(other.team):
            return True
        return False

    # Mark the unit as done (not ready and grayed out).
    def done(self):
        self.ready = False
        self.sprite.colorize(fg="x")


