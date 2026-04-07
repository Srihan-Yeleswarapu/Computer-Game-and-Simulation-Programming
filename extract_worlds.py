import os
import sys

# Add the current directory to sys.path so we can import src
sys.path.append(os.getcwd())

import tkinter as tk
# Mock tk to avoid opening windows during extraction
class MockCanvas:
    def __init__(self, *args, **kwargs): pass
    def delete(self, *args, **kwargs): pass
    def create_rectangle(self, *args, **kwargs): pass
    def create_text(self, *args, **kwargs): pass
    def create_oval(self, *args, **kwargs): pass
    def create_line(self, *args, **kwargs): pass
    def create_image(self, *args, **kwargs): pass
    def pack(self, *args, **kwargs): pass
    def bind(self, *args, **kwargs): pass

tk.Canvas = MockCanvas
def mock_tk():
    class MockTk:
        def __init__(self, *args, **kwargs): pass
        def title(self, *args, **kwargs): pass
        def configure(self, *args, **kwargs): pass
        def resizable(self, *args, **kwargs): pass
        def protocol(self, *args, **kwargs): pass
        def bind(self, *args, **kwargs): pass
        def after(self, *args, **kwargs): pass
        def mainloop(self, *args, **kwargs): pass
        def destroy(self, *args, **kwargs): pass
    return MockTk()

tk.Tk = mock_tk

from src.worlds.fire_rescue import FireRescueWorld
from src.worlds.chef_rush import ChefRushWorld
from src.worlds.bug_hunt import BugHuntWorld
from src.worlds.marine import MarineWorld
from src.worlds.architect import ArchitectWorld
from src.worlds.doctor import DoctorWorld
from src.worlds.atc import ATCWorld
from src.worlds.pilot import PilotWorld
from src.worlds.software_developer import SoftwareDeveloperWorld
from src.worlds.psychologist import PsychologistWorld
from src.worlds.entrepreneur_rework import TycoonWorld
from src.worlds.electrician import ElectricianWorld
from src.worlds.game_developer import GameDeveloperWorld
from src.worlds.data_scientist import DataScientistWorld
from src.worlds.ai_engineer import AIEngineerWorld
from src.worlds.cybersecurity_analyst import CybersecurityAnalystWorld
from src.worlds.robotics_engineer import RoboticsEngineerWorld

worlds = {
    "1": FireRescueWorld(),
    "2": ChefRushWorld(),
    "3": BugHuntWorld(),
    "4": MarineWorld(),
    "5": ArchitectWorld(),
    "6": DoctorWorld(),
    "7": ATCWorld(),
    "8": PilotWorld(),
    "9": SoftwareDeveloperWorld(),
    "0": PsychologistWorld(),
    "q": TycoonWorld(),
    "w": ElectricianWorld(),
    "e": GameDeveloperWorld(),
    "r": DataScientistWorld(),
    "t": AIEngineerWorld(),
    "y": CybersecurityAnalystWorld(),
    "u": RoboticsEngineerWorld(),
}

print("# Career Worlds Summary")
for key, world in worlds.items():
    print(f"## [{key.upper()}] {world.name}")
    print(f"**Summary**: {world.summary}")
    print(f"**Duration**: {world.duration} seconds")
    print("**Briefing**:")
    for line in world.briefing:
        print(f"- {line}")
    print("")
