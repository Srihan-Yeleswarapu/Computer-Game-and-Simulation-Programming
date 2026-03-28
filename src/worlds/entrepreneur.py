import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class EntrepreneurWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Entrepreneur",
            summary="Build a startup while managing limited resources",
            duration=90.0,
        )
        self.briefing = [
             "STARTUP CHALLENGE: Your business must grow quickly!",
             "As the Entrepreneur, you must allocate resources wisely",
             "while balancing risk and growth opportunities.",
             "Invest strategically to maximize profits.",
             "Warning: Poor decisions may cause your startup to fail!"
        ]
        self.hints = [
             "Tip: Collect capital (golden coins) falling from above.",
             "Tip: Deliver capital to blinking Opportunity Zones.",
             "Tip: More expensive zones yield higher returns.",
             "Tip: Balance your investments!"
        ]
        self.capital = 0
        self.funds: list[dict[str, Any]] = []
        self.zones: list[dict[str, Any]] = []
        self.profit = 0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 100)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        
        self.capital = 0
        self.funds = []
        self.zones = [
            {"x": WIDTH/4, "y": HEIGHT/2, "req": 5, "current": 0, "reward": 15},
            {"x": WIDTH/2, "y": HEIGHT/3, "req": 10, "current": 0, "reward": 35},
            {"x": WIDTH*3/4, "y": HEIGHT/2, "req": 3, "current": 0, "reward": 8},
        ]
        self.profit = 0
        player.speed = 350.0

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Spawn funds
        if random.random() < 0.6 * dt:
            self.funds.append({"x": random.uniform(50, WIDTH-50), "y": -20})
            
        new_funds = []
        for f in self.funds:
            f["y"] += 150.0 * dt
            if abs(player.x - f["x"]) < 20 and abs(player.y - f["y"]) < 20:
                self.capital += 1
            elif f["y"] < HEIGHT + 20:
                new_funds.append(f)
        self.funds = new_funds
        
        # Interact with zones
        for z in self.zones:
            if abs(player.x - z["x"]) < 40 and abs(player.y - z["y"]) < 40:
                if self.capital > 0 and z["current"] < z["req"]:
                    self.capital -= 1
                    z["current"] += 1
                    
            if z["current"] >= z["req"]:
                self.profit += z["reward"]
                # Respawn zone with new reqs
                z["x"] = random.uniform(80, WIDTH-80)
                z["y"] = random.uniform(HEIGHT/4, HEIGHT - 120)
                z["req"] = random.randint(3, 15)
                z["current"] = 0
                z["reward"] = int(z["req"] * random.uniform(1.5, 3.5))

        if self.timer <= 0:
            if self.profit >= 50:
                self.finished = True
                self.success = True
                self.message = "Startup Acquired! You've built a successful unicorn."
                if self.profit > 200: self.grade = "S"
                elif self.profit > 150: self.grade = "A"
                elif self.profit > 100: self.grade = "B"
                else: self.grade = "C"
            else:
                self.finished = True
                self.success = False
                self.message = "Bankrupt! You didn't generate enough profit."

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#f3a683" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)

        for z in self.zones:
             color = "#f78fb3"
             canvas.create_rectangle(z["x"]-40, z["y"]-40, z["x"]+40, z["y"]+40, fill=color, outline="#3dc1d3", width=2)
             canvas.create_text(z["x"], z["y"]-15, text="OPPORTUNITY", fill="#3dc1d3", font=("Helvetica", 8, "bold"))
             canvas.create_text(z["x"], z["y"]+5, text=f"Need: {z['current']}/{z['req']}", fill="#303952", font=("Helvetica", 10))
             canvas.create_text(z["x"], z["y"]+25, text=f"ROI: +${z['reward']}", fill="#27ae60", font=("Helvetica", 10, "bold"))

        for f in self.funds:
             canvas.create_oval(f["x"]-10, f["y"]-10, f["x"]+10, f["y"]+10, fill="#f1c40f", outline="#f39c12", width=2)
             canvas.create_text(f["x"], f["y"], text="$", fill="#d35400", font=("Helvetica", 10, "bold"))

        player.draw(canvas)
        
        # HUD
        canvas.create_rectangle(20, 60, 200, 110, fill="#303952")
        canvas.create_text(110, 75, text=f"Capital: ${self.capital}", fill="#f1c40f", font=("Helvetica", 14, "bold"))
        canvas.create_text(110, 95, text=f"Profit: ${self.profit}", fill="#2ecc71", font=("Helvetica", 14, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
