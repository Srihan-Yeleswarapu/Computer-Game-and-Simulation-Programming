import unittest

from src.player import Player
from src.worlds.architect import ArchitectWorld


class MockCanvas:
    def create_rectangle(self, *args, **kwargs):
        pass

    def create_oval(self, *args, **kwargs):
        pass

    def create_text(self, *args, **kwargs):
        pass

    def create_line(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass


class TestArchitectWorld(unittest.TestCase):
    def test_complete_program_passes_review(self) -> None:
        canvas = MockCanvas()
        player = Player()
        world = ArchitectWorld()
        world.reset(player)
        world.tutorial_timer = 0.0

        program = [
            (4, 7, "Lobby"),
            (5, 7, "Core"),
            (4, 6, "Reading Room"),
            (5, 6, "Reading Room"),
            (6, 6, "Reading Room"),
            (1, 7, "Archive"),
            (4, 5, "Roof Garden"),
        ]
        color_map = {room["name"]: room["color"] for room in world.room_types}
        cost_map = {room["name"]: room["cost"] for room in world.room_types}
        short_map = {room["name"]: room["short"] for room in world.room_types}
        world.blocks = [
            {
                "gx": gx,
                "gy": gy,
                "type": room_name,
                "color": color_map[room_name],
                "cost": cost_map[room_name],
                "short": short_map[room_name],
            }
            for gx, gy, room_name in program
        ]
        world.budget = world.budget_limit - sum(cost_map[room_name] for _, _, room_name in program)

        world.phase = "review"
        world.review_timer = 0.0
        world.update(0.1, canvas, player, set(), (0, 0))

        self.assertTrue(world.finished)
        self.assertTrue(world.success)
        self.assertGreaterEqual(world.review_score, 70.0)


if __name__ == "__main__":
    unittest.main()
