# Entities are TILES, OBJECTS, and TEAMS.


# A Team is one "side" of a session in a game of RoW. Teams control Tiles and
# Units, and may be allied with other teams. When a team is set to be inactive,
# that is the indication that it has lost the game and will not longer act.
class Team(object):
    def __init__(self, data):
        self.name = data["name"]
        self.cash = 0
        self.active = True
        self.allies = []

    # Returns True if this team is allied with the other team.
    def is_allied(self, other):
        if other in self.allies:


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

        # Set the flag properties for the terrain.
        self.can_build = "build" in data["properties"]
        self.can_capture = "capture" in data["properties"]
        self.can_repair = "repair" in data["properties"]
        self.is_hq = "hq" in data["properties"]

        # This highlights the interactions between units and tiles.
        self.builds = data.get("builds",{})
        self.repairs = data.get("repairs",{})

    # Returns True if this unit is allied with the other team, tile, or unit.
    def is_allied(self, other):
        if not self.team:
            return False
        if self.team.allied(other) or self.team.allied(other.team):
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
        self.movement = data["movement"]
        self.over = data["over"]
        self.range = data["range"]
        self.max_ammo = data.get("ammo",0)
        self.max_fuel = data["fuel"]
        self.capacity = data.get("capacity",0)
        self.hp = 100
        self.team = None
        self.ready = True
        self.carrying = []
        self.ammo = self.max_ammo
        self.fuel = self.max_fuel

        # Set the animation variables.
        self.anim = self.icon
        self.frame = 0

        # Read the flag variables.
        self.is_indirect = "indirect" in data["properties"]
        self.no_cover = "nocover" in data["properties"]
        self.can_carry = "carry" in data["properties"]
        self.can_capture = "capture" in data["properties"]
        
        self.primary = data.get("primary",{})
        self.secpndary = data.get("secondary",{})
        self.carries = data.get("carries",[])

    # This function adds one frame to the animation cycle for the unit.
    def cycle_anim(self):
        self.frame += 1
        frames = [self.icon]
        
        if (self.hp < 90):
            frames.append( str((self.hp//10)+1)  )
        
        self.frame %= len(frames)
        self.anim = frames[self.frame]

    # Returns True if this unit is allied with the other team, tile, or unit.
    def is_allied(self, other):
        if not self.team:
            return False
        if self.team.allied(other) or self.team.allied(other.team):
            return True
        return False


