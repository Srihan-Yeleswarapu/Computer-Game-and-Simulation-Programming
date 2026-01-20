import unittest
from unittest.mock import MagicMock
import sys
import os
import math

# Add parent directory to path to import game
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import FireRescueWorld, ChefRushWorld, BugHuntWorld, Player, WIDTH, HEIGHT

class MockCanvas:
    def create_rectangle(self, *args, **kwargs): pass
    def create_oval(self, *args, **kwargs): pass
    def create_text(self, *args, **kwargs): pass
    def create_line(self, *args, **kwargs): pass
    def create_polygon(self, *args, **kwargs): pass
    def create_arc(self, *args, **kwargs): pass
    def delete(self, *args, **kwargs): pass

class TestGameWinnable(unittest.TestCase):
    def setUp(self):
        self.canvas = MockCanvas()
        self.player = Player()

    def test_fire_rescue_winnable(self):
        print("\nTesting FireRescueWorld...")
        world = FireRescueWorld()
        world.reset(self.player)
        world.flames = [] # Remove RNG hazards
        
        # Verify bounds allow access to door (x=80..220)
        # Old bounds started at 220, making x<220 unreachable.
        # Check if player can set x to 100
        self.player.x = 100
        self.player.y = HEIGHT / 2
        # Update with no keys to trigger bounds check
        world.update(0.1, self.canvas, self.player, set())
        
        print(f"Player X after update at door: {self.player.x}")
        self.assertTrue(self.player.x < 220, "Player should be able to reach the rescue door area")

        # Simulate saving 5 survivors
        for i in range(5):
            # 1. Teleport to a survivor
            if not world.survivors: break
            target = world.survivors[0]
            self.player.x = target["x"]
            self.player.y = target["y"]
            
            # 2. Wait for pickup (1.0 progress / 1.4 rate ~= 0.8s)
            for _ in range(10): # 1 second
                world.update(0.1, self.canvas, self.player, set())
                if world.carrying: break
            
            self.assertIsNotNone(world.carrying, f"Failed to pick up survivor {i+1}")
            
            # 3. Teleport to door
            self.player.x = 150 # In door zone
            self.player.y = HEIGHT / 2
            
            # 4. Update to drop off
            world.update(0.1, self.canvas, self.player, set())
            
        self.assertTrue(world.finished, "World should be finished")
        self.assertTrue(world.success, "World should be won")
        print("FireRescueWorld Passed!")

    def test_chef_rush_winnable(self):
        print("\nTesting ChefRushWorld...")
        world = ChefRushWorld()
        world.reset(self.player)
        world.spills = [] # Remove RNG hazards
        
        recipe_len = len(world.recipe)
        for i in range(recipe_len):
            target_name = world.recipe[world.step]
            target_station = next(s for s in world.stations if s["name"] == target_name)
            
            # Teleport to station
            self.player.x = target_station["x"]
            self.player.y = target_station["y"]
            
            # Wait for progress
            start_timer = world.timer
            for _ in range(15): # 1.5s
                world.update(0.1, self.canvas, self.player, set())
                if world.step > i: break
            
            # Check we advanced
            self.assertEqual(world.step, i + 1, f"Failed to complete step {i}")
            
            # Check penalty isn't huge (should be minimal drain)
            # timer might increase on success, so this check is soft
            self.assertTrue(world.timer > 0, "Timer shouldn't run out")

        self.assertTrue(world.finished, "World should be finished")
        self.assertTrue(world.success, "World should be won")
        print("ChefRushWorld Passed!")

    def test_bug_hunt_winnable(self):
        print("\nTesting BugHuntWorld...")
        world = BugHuntWorld()
        world.reset(self.player)
        world.glitches = [] # Remove RNG hazards
        
        node_len = len(world.nodes)
        for i in range(node_len):
            target = world.nodes[world.index]
            self.player.x = target["x"]
            self.player.y = target["y"]
            
            for _ in range(10):
                world.update(0.1, self.canvas, self.player, set())
                if world.index > i: break
            
            self.assertEqual(world.index, i + 1, f"Failed to patch node {i}")
            
        # Deploy
        self.player.x = world.deploy_point["x"]
        self.player.y = world.deploy_point["y"]
        for _ in range(10):
            world.update(0.1, self.canvas, self.player, set())
            
        self.assertTrue(world.finished, "World should be finished")
        self.assertTrue(world.success, "World should be won")
        print("BugHuntWorld Passed!")

if __name__ == "__main__":
    unittest.main()
