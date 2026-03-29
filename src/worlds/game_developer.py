import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class GameDeveloperWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Game Developer",
            summary="Collect assets and deliver to the workstation to finish your game",
            duration=70.0,
        )
        self.briefing = [
             "DEV RUSH: The publisher wants an early alpha!",
             "Collect CODE, ART, and SOUND assets appearing around the office.",
             "Deliver them to your WORKSTATION in the center.",
             "Watch out for BUG spawns – squash them before they ruin the project!"
        ]
        self.hints = [
             "Tip: Yellow = Code, Blue = Art, Purple = Sound.",
             "Tip: Touch an asset to pick it up, then touch the PC to deposit.",
             "Tip: RED dots are BUGS. Touch them to squash!",
             "Tip: Finish the progress bar before the deadline."
        ]
        self.held_asset = ""
        self.progress = 0.0
        self.assets = []
        self.bugs = []
        self.spawn_timer = 1.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 100)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.progress = 0.0
        self.assets = []
        self.bugs = []
        self.held_asset = ""
        self.shake = 0.0
        self.particles = []

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)

        # Spawning
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(1.0, 2.0)
            if random.random() < 0.7:
                 # Asset
                 typ = random.choice(["CODE", "ART", "SOUND"])
                 col = {"CODE": "#f1c40f", "ART": "#3498db", "SOUND": "#9b59b6"}[typ]
                 self.assets.append({"x": random.uniform(50, WIDTH-50), "y": random.uniform(50, HEIGHT-150), "type": typ, "color": col})
            else:
                 # Bug
                 self.bugs.append({"x": random.uniform(80, WIDTH-80), "y": random.uniform(80, HEIGHT-180)})

        # Pickup
        new_assets = []
        for a in self.assets:
            if math.hypot(player.x - a["x"], player.y - a["y"]) < 40 and not self.held_asset:
                 self.held_asset = a["type"]
            else:
                 new_assets.append(a)
        self.assets = new_assets

        # Bug squash
        new_bugs = []
        for b in self.bugs:
            if math.hypot(player.x - b["x"], player.y - b["y"]) < 40:
                 self.shake = 2.0
                 self.progress = max(0.0, self.progress - 2.0)
            else:
                 new_bugs.append(b)
                 if random.random() < 0.1 * dt: # Bugs slowly drain progress
                      self.progress = max(0.0, self.progress - 1.0 * dt)
        self.bugs = new_bugs

        # Deliver to PC
        pc_x, pc_y = WIDTH/2, HEIGHT/2
        if math.hypot(player.x - pc_x, player.y - pc_y) < 60:
            if self.held_asset:
                 self.progress += 10.0
                 self.held_asset = ""

        if self.progress >= 100.0:
            self.finished = True
            self.success = True
            self.message = "Game Launched! Overwhelmingly Positive reviews."
            if self.timer > 30: self.grade = "S"
            elif self.timer > 15: self.grade = "A"
            else: self.grade = "B"

        if self.timer <= 0:
            self.finished = True
            self.success = False
            self.message = "Development Cancelled! Deadline missed."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#2f3542" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)

        # Workstation
        pc_x, pc_y = WIDTH/2, HEIGHT/2
        canvas.create_rectangle(pc_x-50, pc_y-40, pc_x+50, pc_y+40, fill="#57606f", outline="#2ed573", width=3)
        canvas.create_text(pc_x, pc_y, text="WORKSTATION", fill="#2ed573", font=("Arial", 10, "bold"))
        
        # Assets
        for a in self.assets:
             canvas.create_rectangle(a["x"]-15, a["y"]-15, a["x"]+15, a["y"]+15, fill=a["color"], outline="#fff")
             canvas.create_text(a["x"], a["y"], text=a["type"][0], fill="#fff", font=("Arial", 8, "bold"))

        # Bugs
        for b in self.bugs:
             canvas.create_oval(b["x"]-10, b["y"]-10, b["x"]+10, b["y"]+10, fill="#ff4757", outline="#fff")

        # Held asset
        if self.held_asset:
             canvas.create_text(player.x, player.y-40, text=f"HOLDING: {self.held_asset}", fill="#fff", font=("Arial", 9, "bold"))

        player.draw(canvas)
        
        # Progress Bar
        canvas.create_rectangle(WIDTH/2-150, 60, WIDTH/2+150, 85, fill="#111", outline="#fff")
        canvas.create_rectangle(WIDTH/2-148, 62, WIDTH/2-148+296*(self.progress/100.0), 83, fill="#2ed573")
        canvas.create_text(WIDTH/2, 72, text=f"BUILD PROGRESS: {int(self.progress)}%", fill="#fff", font=("Arial", 10, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

