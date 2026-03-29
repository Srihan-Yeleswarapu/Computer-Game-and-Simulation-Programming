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
            summary="Code at your desk and squash bugs before they ruin the build!",
            duration=60.0,
        )
        self.briefing = [
             "CRUNCH TIME: The game needs to ship today!",
             "Sit at your WORKSTATION (center) to write code and increase progress.",
             "BUGS (red) will spawn around the office and crawl towards your code.",
             "If bugs reach your workstation, they will destroy your progress!",
             "Run over bugs to squash them, then get back to coding."
        ]
        self.hints = [
             "Tip: You only gain progress while touching the Workstation.",
             "Tip: Bugs destroy progress faster than you can write it.",
             "Tip: Balance coding and squashing to reach 100%!"
        ]
        self.progress = 0.0
        self.bugs = []
        self.spawn_timer = 1.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2 + 50)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.progress = 0.0
        self.bugs = []
        self.shake = 0.0
        self.particles = []

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)

        pc_x, pc_y = WIDTH/2, HEIGHT/2

        # Coding Progress
        at_desk = math.hypot(player.x - pc_x, player.y - pc_y) < 50
        if at_desk:
            self.progress += 2.5 * dt

        # Bug Spawning
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(0.8, 1.8)
            # Spawn at edges
            side = random.randint(0, 3)
            if side == 0: bx, by = random.uniform(20, WIDTH-20), 20
            elif side == 1: bx, by = WIDTH-20, random.uniform(20, HEIGHT-20)
            elif side == 2: bx, by = random.uniform(20, WIDTH-20), HEIGHT-20
            else: bx, by = 20, random.uniform(20, HEIGHT-20)
            self.bugs.append({"x": bx, "y": by, "speed": random.uniform(25, 45)})

        # Bug Logic
        new_bugs = []
        for b in self.bugs:
            # Check player squash
            if math.hypot(player.x - b["x"], player.y - b["y"]) < 30:
                 self.shake = 2.0
                 continue # Squashed!
            
            # Move towards PC
            angle = math.atan2(pc_y - b["y"], pc_x - b["x"])
            b["x"] += math.cos(angle) * b["speed"] * dt
            b["y"] += math.sin(angle) * b["speed"] * dt

            # Check PC hit
            if math.hypot(b["x"] - pc_x, b["y"] - pc_y) < 30:
                 self.progress = max(0.0, self.progress - 10.0 * dt)
                 self.shake = 1.0
            
            new_bugs.append(b)
        self.bugs = new_bugs

        if self.progress >= 100.0:
            self.finished = True
            self.success = True
            self.message = "Game Launched! Overwhelmingly Positive Reviews."
            if self.timer > 30: self.grade = "S"
            elif self.timer > 15: self.grade = "A"
            else: self.grade = "B"

        if self.timer <= 0:
            self.finished = True
            self.success = self.progress >= 50.0
            if self.success:
                self.message = f"Shift Over! Game launched in Early Access ({int(self.progress)}% complete)."
                self.grade = self.calculate_grade()
            else:
                self.message = f"Development Cancelled! Build too buggy to release."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        sx = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0
        sy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0

        bg = "#2f3542" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0+sx, 0+sy, WIDTH+sx, HEIGHT+sy, fill=bg)

        # Workstation
        pc_x, pc_y = WIDTH/2, HEIGHT/2
        canvas.create_rectangle(pc_x-40+sx, pc_y-40+sy, pc_x+40+sx, pc_y+40+sy, fill="#57606f", outline="#2ed573", width=3)
        canvas.create_text(pc_x+sx, pc_y-10+sy, text="DESK", fill="#2ed573", font=("Arial", 10, "bold"))
        
        is_coding = math.hypot(player.x - pc_x, player.y - pc_y) < 50
        if is_coding:
             canvas.create_text(pc_x+sx, pc_y+15+sy, text="CODING...", fill="#ffdd59", font=("Arial", 8, "bold"))

        # Bugs
        for b in self.bugs:
             canvas.create_oval(b["x"]-10+sx, b["y"]-10+sy, b["x"]+10+sx, b["y"]+10+sy, fill="#ff4757", outline="#fff")
             # Bug legs
             canvas.create_line(b["x"]-15+sx, b["y"]+sy, b["x"]+15+sx, b["y"]+sy, fill="#ff4757")
             canvas.create_line(b["x"]+sx, b["y"]-15+sy, b["x"]+sx, b["y"]+15+sy, fill="#ff4757")

        player.draw(canvas)
        
        # Progress Bar
        canvas.create_rectangle(WIDTH/2-150, 60, WIDTH/2+150, 85, fill="#111", outline="#fff")
        canvas.create_rectangle(WIDTH/2-148, 62, WIDTH/2-148+296*(self.progress/100.0), 83, fill="#2ed573")
        canvas.create_text(WIDTH/2, 72, text=f"BUILD PROGRESS: {int(self.progress)}%", fill="#fff", font=("Arial", 10, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

