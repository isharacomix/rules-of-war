# This file tests our grid object. The grid is, for the most part, a passive
# storer of data. This test will usually make sure that the grid loads its
# JSON dictionary and runs its side effect functions correctly. To work, it
# needs a dummy Rules file, which we define here.

import unittest

from graphics import gfx
from core import grid

# This is basic interface that has all the features that TestGrid
# expects. This is where the ducktyping of python comes in super
# handy!
class DummyRules(object):
    def make_unit(self,rules):
        return grid.Unit("Test","t")
    def make_cell(self,rules):
        return grid.Cell("Test",".","w")
    def make_team(self,rules):
        return grid.Team("Test","w")
        
# Test the grid.
class TestGrid(unittest.TestCase):
    def setUp(self):
        gfx.gfx.clear_buffer()
        gdict = {}
        gdict["name"] = "Hello World"
        gdict["w"] = 30
        gdict["h"] = 15
        gdict["cells"] = []
        for x in range(30):
            for y in range(15):
                cell = {}
                cell["x"] = x
                cell["y"] = y
                if x==y:
                    cell["name"] = "City"
                else:
                    cell["name"] = "Grass"
                gdict["cells"].append(cell)
        unit1 = {}
        unit1["name"] = "Artillery"
        unit1["team"] = 0
        unit2 = {}
        unit2["name"] = "Infantry"
        unit2["team"] = 1
        gdict["cells"][4]["unit"] = unit1
        gdict["cells"][40]["unit"] = unit2
        team1 = {"name":"Red","color":"r"}
        team2 = {"name":"Blue","color":"b"}
        gdict["teams"] = [team1,team2]

        self.G = grid.Grid(gdict,DummyRules())

        
    # This test makes sure that the variables that we loaded from
    # the JSON dictionary were stored correctly.
    def test_variables(self):
        self.assertEqual(len(self.G.grid),15*30)

    # Test the unit_at getter. Returns None for illegal cells.
    def test_unit_at(self):
        self.assertEqual(self.G.unit_at(0,0), None)
        self.assertEqual(self.G.unit_at(-8,-1), None)
        self.assertEqual(self.G.unit_at(0,4).name, "Test")

    # Test the tile_at getter. Returns None for illegal cells.
    def test_tile_at(self):
        self.assertEqual(self.G.tile_at(-1,-1), None)
        self.assertEqual(self.G.tile_at(0,4).unit.name, "Test")

    # Test the "all tiles" helper.
    def test_all_tiles(self):
        l = self.G.all_tiles()
        self.assertEqual(len(l),15*30)
        total = 0
        for x in l:
            if x.unit:
                total += 1
        self.assertEqual(total, 2)
        m = self.G.all_tiles_xy()
        self.assertEqual(len(m),15*30)
        self.assertEqual(sorted(m)[4],(0,4))

    # Test the distance measurer.
    def test_dist(self):
        a = (1,4)
        b = (4,4)
        c = (4,1)
        d = (1,1)
        self.assertEqual(self.G.dist(a,b),3)
        self.assertEqual(self.G.dist(a,c),6)
        self.assertEqual(self.G.dist(a,d),3)
        self.assertEqual(self.G.dist(b,a),3)
        self.assertEqual(self.G.dist(c,a),6)
        self.assertEqual(self.G.dist(d,a),3)

    # Test the range generator. This returns all cells between
    # near and far.
    def test_range(self):
        r1 = set(self.G.get_range((5,5),2))
        r2 = set(self.G.get_range((5,5),2,3))

        a1 = set([(5,7),(5,3),(7,5),(3,5),(6,6),(4,4),(6,4),(4,6)])
        self.assertEqual(a1,r1)
        a2 = set([(5,8),(6,7),(7,6),(8,5),(7,4),(6,3),(5,2),(4,3),(3,4),(2,5),
                  (3,6),(4,7)]).union(a1)
        self.assertEqual(a2,r2)

    # Test moving a unit.
    def test_move_unit(self):
        u = self.G.unit_at(0,4)
        self.G.move_unit((0,4),(0,8))
        self.assertEqual(self.G.unit_at(0,4),None)
        self.assertEqual(self.G.unit_at(0,8),u)
        #TODO test exceptions

    # Test removing a unit from the grid.
    def test_remove_unit(self):
        u = self.G.unit_at(0,4)
        self.G.remove_unit(0,4)
        self.assertEqual(self.G.unit_at(0,4),None)
        self.assertTrue(u not in self.G.units)

    # Test team switching and deactivating.
    def test_teams(self):
        t = self.G.current_team()
        self.G.end_turn()
        self.assertNotEqual(t,self.G.current_team())
        self.G.end_turn()
        self.assertEqual(t,self.G.current_team())
        self.assertEqual(self.G.day,2)
        t.active = False
        self.G.end_turn()
        self.assertNotEqual(t,self.G.current_team())
        self.G.end_turn()
        self.assertNotEqual(t,self.G.current_team())
