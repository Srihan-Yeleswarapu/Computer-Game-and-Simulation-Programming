import unittest

from src.player import Player
from src.worlds.doctor import DoctorWorld


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


class TestDoctorWorld(unittest.TestCase):
    def test_patient_can_be_cured_with_correct_treatment(self) -> None:
        canvas = MockCanvas()
        player = Player()
        world = DoctorWorld()
        world.reset(player)
        world.tutorial_timer = 0.0
        world.spawn_patients = lambda: None

        patient = world.create_patient(0, "fever")
        patient["stability"] = 90.0
        patient["drain_rate"] = 0.0
        world.patients = [patient]

        tool = next(tool for tool in world.tool_catalog if tool["type"] == "antipyretic")
        player.x = tool["x"]
        player.y = tool["y"]
        world.update(0.1, canvas, player, {"space"}, (0, 0))
        self.assertEqual(world.held_item, "antipyretic")

        player.x = patient["x"]
        player.y = patient["y"]
        for _ in range(20):
            world.update(0.1, canvas, player, {"space"}, (0, 0))

        self.assertEqual(world.saved_patients, 1)
        self.assertEqual(world.held_item, "")
        self.assertTrue(all(p["status"] == "cured" for p in world.patients) or not world.patients)


if __name__ == "__main__":
    unittest.main()
