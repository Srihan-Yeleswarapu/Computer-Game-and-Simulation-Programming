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
            summary="Complete a game build before release deadline",
            duration=90.0,
        )
        self.briefing = [
             "DEADLINE ALERT: Game launch is approaching!",
             "As the Game Developer, you must finish development",
             "while balancing Code, Art, and Testing.",
             "Neglecting any area creates Crash Bugs!",
             "Warning: Too many bugs will delay release!"
        ]
        self.hints = [
             "Tip: Balance your time between Code, Art, and Test stations.",
             "Tip: Refill a station's progress by standing on it.",
             "Tip: Avoid crash bugs if they spawn.",
             "Tip: Keep all bars above zero to succeed."
        ]
        self.stations: list[dict[str, Any]] = []
        self.bugs: list[dict[str, Any]] = []
        self.global_progress = 0.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        
        self.stations = [
            {"name": "Code", "x": WIDTH/2, "y": HEIGHT/4, "progress": 100.0, "color": "#ff4757", "rate": 5.0},
            {"name": "Art", "x": WIDTH/4, "y": HEIGHT*3/4, "progress": 100.0, "color": "#1e90ff", "rate": 4.0},
            {"name": "Test", "x": WIDTH*3/4, "y": HEIGHT*3/4, "progress": 100.0, "color": "#2ed573", "rate": 6.0},
        ]
        self.bugs = []
        self.global_progress = 0.0

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Update stations
        active_station = -1
        for i, s in enumerate(self.stations):
            dist = math.hypot(player.x - s["x"], player.y - s["y"])
            if dist < 50:
                 s["progress"] = min(100.0, s["progress"] + dt * 25.0)
                 active_station = i
            else:
                 s["progress"] -= dt * s["rate"]
                 
            if s["progress"] <= 0:
                 s["progress"] = 50.0 # reset a bit to avoid instant re-spawn
                 self.bugs.append({"x": s["x"], "y": s["y"], "speed": random.uniform(80, 120)})
                 self.shake = 3.0
                 
        # Update bugs
        new_bugs = []
        for b in self.bugs:
            angle = math.atan2(player.y - b["y"], player.x - b["x"])
            b["x"] += math.cos(angle) * b["speed"] * dt
            b["y"] += math.sin(angle) * b["speed"] * dt
            
            if math.hypot(player.x - b["x"], player.y - b["y"]) < 20: # hit player
                self.global_progress -= 15.0
                self.shake = 5.0
            else:
                new_bugs.append(b)
        self.bugs = new_bugs
        
        # Global Progress increases automatically if there are no bugs and stations are healthy
        avg_health = sum(s["progress"] for s in self.stations) / len(self.stations)
        if len(self.bugs) == 0 and avg_health > 20: # Must be somewhat healthy to progress
            self.global_progress += dt * 1.5

        if self.global_progress >= 100.0:
            self.finished = True
            self.success = True
            self.message = "Game Gone Gold! Release was a massive success."
            if self.timer > 40: self.grade = "S"
            elif self.timer > 20: self.grade = "A"
            elif self.timer > 0: self.grade = "B"
            else: self.grade = "C"
            
        if self.timer <= 0:
            self.finished = True
            self.success = False
            self.message = "Missed the deadline! Publisher canceled the project."

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#dfe4ea" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Draw stations
        for s in self.stations:
            canvas.create_rectangle(s["x"]-40+sx, s["y"]-40+sy, s["x"]+40+sx, s["y"]+40+sy, fill="#fff", outline=s["color"], width=3)
            canvas.create_text(s["x"]+sx, s["y"]-15+sy, text=s["name"], fill="#2f3542", font=("Helvetica", 10, "bold"))
            
            # Progress bar
            canvas.create_rectangle(s["x"]-30+sx, s["y"]+10+sy, s["x"]+30+sx, s["y"]+20+sy, fill="#a4b0be", outline="")
            canvas.create_rectangle(s["x"]-30+sx, s["y"]+10+sy, s["x"]-30 + 60 * max(0.0, s["progress"])/100.0 + sx, s["y"]+20+sy, fill=s["color"], outline="")
            
        # Draw bugs
        for b in self.bugs:
            canvas.create_oval(b["x"]-8+sx, b["y"]-8+sy, b["x"]+8+sx, b["y"]+8+sy, fill="#ff4757", outline="#2f3542")
            canvas.create_text(b["x"]+sx, b["y"]-15+sy, text="BUG", fill="#ff4757", font=("Helvetica", 8, "bold"))

        player.draw(canvas)
        
        # Draw global progress
        gp = max(0.0, self.global_progress)
        canvas.create_rectangle(WIDTH/2 - 150, 60, WIDTH/2 + 150, 80, fill="#2f3542", outline="#fff")
        canvas.create_rectangle(WIDTH/2 - 148, 62, WIDTH/2 - 148 + 296 * (gp/100.0), 78, fill="#2ed573", outline="")
        canvas.create_text(WIDTH/2, 70, text=f"GAME BUILD PROGRESS: {int(gp)}%", fill="#fff" if gp < 50 else "#2f3542", font=("Helvetica", 11, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
