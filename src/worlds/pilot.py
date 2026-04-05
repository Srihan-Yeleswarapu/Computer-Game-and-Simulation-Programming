import random
import math
import time
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class PilotWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Pilot",
            summary="Safely navigate aircraft through turbulent weather conditions",
            duration=60.0,
        )
        self.briefing = [
             "URGENT MISSION: Severe turbulence is approaching!",
             "As the Pilot, you must navigate your aircraft safely",
             "while maintaining hull integrity avoiding storm clouds.",
             "Collect fuel to keep flying.",
             "Warning: Losing hull integrity will result in mission failure!"
        ]
        self.hints = [
             "Tip: Adjust position to avoid dark turbulence zones.",
             "Tip: Collect green fuel pickups.",
             "Tip: Use WASD to steer the aircraft.",
             "Tip: Stay alert, storms move fast."
        ]
        self.hull = 100.0
        self.fuel = 100.0
        self.clouds: list[dict[str, Any]] = []
        self.fuels: list[dict[str, Any]] = []
        self.scroll_speed = 300.0
        
    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 100)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.hull = 100.0
        self.fuel = 100.0
        self.clouds = []
        self.fuels = []
        self.shake = 0.0
        self.particles = []
        player.speed = 500.0

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        # tick_timer handled by engine
        player.update(dt, keys, self.bounds)
        self.fuel -= dt * 5  # Balanced drainrate
        
        # Spawn clouds
        if random.random() < 0.05 + dt:
            w = random.uniform(80, 200)
            self.clouds.append({"x": random.uniform(0, WIDTH), "y": -100, "w": w, "h": w*0.6, "bad": random.random() < 0.35})
            
        # Spawn fuel
        if random.random() < 0.007 + dt * 0.01:
            self.fuels.append({"x": random.uniform(20, WIDTH-20), "y": -20})
            
        new_clouds = []
        in_bad_cloud = False
        in_cloud = False
        
        for c in self.clouds:
            c["y"] += self.scroll_speed * dt
            
            # Collision with player
            if player.x > c["x"] - c["w"]/2 and player.x < c["x"] + c["w"]/2 and player.y > c["y"] - c["h"]/2 and player.y < c["y"] + c["h"]/2:
                if c["bad"]:
                    self.hull -= dt * 80
                    self.shake = 5.0
                    in_bad_cloud = True
                else:
                    in_cloud = True
                    
            if c["y"] < HEIGHT + 200:
                new_clouds.append(c)
        self.clouds = new_clouds
        
        if in_bad_cloud:
            player.speed = 150.0
        elif in_cloud:
            player.speed = 280.0
        else:
            player.speed = 400.0
        
        new_fuels = []
        for f in self.fuels:
            f["y"] += self.scroll_speed * dt
            if abs(player.x - f["x"]) < 30 and abs(player.y - f["y"]) < 30:
                self.fuel = min(100.0, self.fuel + 15.0)
            elif f["y"] < HEIGHT + 50:
                new_fuels.append(f)
        self.fuels = new_fuels
        
        if self.hull <= 0:
            self.finished = True
            self.success = False
            self.message = "Hull compromised! Aircraft went down."
            
        if self.fuel <= 0:
            self.finished = True
            self.success = False
            self.message = "Out of fuel! Aircraft went down."
            
        if self.timer <= 0 and self.hull > 0 and self.fuel > 0:
            self.finished = True
            self.success = True
            score = self.hull + self.fuel
            if score >= 150: self.grade = "S"
            elif score >= 100: self.grade = "A"
            elif score >= 50: self.grade = "B"
            else: self.grade = "C"
            self.message = "Mission Accomplished! Destination reached."
            
            
        self.update_particles(dt)
        self.draw(canvas, player)


    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#4b7bec" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Ground effect or lines
        for i in range(5):
            ly = (time.time() * self.scroll_speed + i * HEIGHT/5) % HEIGHT
            canvas.create_line(0, ly, WIDTH, ly, fill="#5588ff", width=1)
            
        # Draw clouds
        for c in self.clouds:
            color = "#a5b1c2" if not c["bad"] else "#2c3e50"
            if self.high_contrast: color = "#222222" if c["bad"] else "#dddddd"
            canvas.create_oval(c["x"] - c["w"]/2 + sx, c["y"] - c["h"]/2 + sy, c["x"] + c["w"]/2 + sx, c["y"] + c["h"]/2 + sy, fill=color, outline="")
            
        # Draw fuels
        for f in self.fuels:
            canvas.create_rectangle(f["x"] - 12 + sx, f["y"] - 15 + sy, f["x"] + 12 + sx, f["y"] + 15 + sy, fill="#20bf6b", outline="#fff", width=2)
            canvas.create_text(f["x"] + sx, f["y"] + sy, text="F", fill="#fff", font=("Helvetica", 10, "bold"))
            
        # Draw player
        px, py = player.x + sx, player.y + sy
        # Fuselage
        canvas.create_polygon(px, py-20, px-8, py+10, px+8, py+10, fill="#fff", outline="#222")
        # Wings
        canvas.create_polygon(px-25, py+5, px+25, py+5, px, py-5, fill="#d1d8e0", outline="#222")
        # Tail
        canvas.create_polygon(px-10, py+15, px+10, py+15, px, py+5, fill="#d1d8e0", outline="#222")
        
        # HUD for hull and fuel
        canvas.create_rectangle(20, 60, 220, 80, fill="#111", outline="#555", width=2)
        canvas.create_rectangle(22, 62, 22 + 196 * max(0.0, self.hull) / 100.0, 78, fill="#eb3b5a", outline="")
        canvas.create_text(120, 70, text="HULL", fill="#fff", font=("Helvetica", 9, "bold"))
        
        canvas.create_rectangle(20, 90, 220, 110, fill="#111", outline="#555", width=2)
        canvas.create_rectangle(22, 92, 22 + 196 * max(0.0, self.fuel) / 100.0, 108, fill="#20bf6b", outline="")
        canvas.create_text(120, 100, text="FUEL", fill="#fff", font=("Helvetica", 9, "bold"))
        
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
