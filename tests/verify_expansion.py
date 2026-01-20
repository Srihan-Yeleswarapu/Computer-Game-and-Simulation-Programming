import unittest
import tkinter as tk
from src.player import Player
from src.worlds.marine import MarineWorld
from src.worlds.architect import ArchitectWorld
from src.worlds.doctor import DoctorWorld
from src.worlds.atc import ATCWorld
from src.save_system import SaveSystem

class TestExpansion(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.player = Player()
        self.keys = set()
    
    def tearDown(self):
        self.root.destroy()
        
    def test_marine_world(self):
        world = MarineWorld()
        world.reset(self.player)
        world.update(0.1, self.canvas, self.player, self.keys)
        self.assertFalse(world.finished)
        
    def test_architect_world(self):
        world = ArchitectWorld()
        world.reset(self.player)
        # Test building
        self.keys.add("1")
        self.keys.add("space")
        world.update(0.1, self.canvas, self.player, self.keys)
        self.assertFalse(world.finished)
        
    def test_doctor_world(self):
        world = DoctorWorld()
        world.reset(self.player)
        world.update(0.1, self.canvas, self.player, self.keys)
        self.assertFalse(world.finished)
        
    def test_atc_world(self):
        world = ATCWorld()
        world.reset(self.player)
        world.update(0.1, self.canvas, self.player, self.keys)
        self.assertFalse(world.finished)
        
    def test_save_system(self):
        save = SaveSystem()
        # Test rank bounds
        self.assertTrue(0 <= save.data["rank_index"] <= 11)
        rank_name = save.get_rank()
        self.assertIsInstance(rank_name, str)

if __name__ == '__main__':
    unittest.main()
