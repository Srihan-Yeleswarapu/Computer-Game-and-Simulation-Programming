import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class ElectricianWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Electrician",
            summary="Restore power by repairing faulty circuits",
            duration=90.0,
        )
        self.briefing = [
             "POWER OUTAGE: The system is down!",
             "As the Electrician, you must repair the circuit network",
             "and restore electricity safely.",
             "Identify faulty connections and reroute power.",
             "Warning: Incorrect wiring may overload the system!"
        ]
        self.hints = [
             "Tip: Trace power flow carefully.",
             "Tip: Stand in the red broken gaps to connect the circuit.",
             "Tip: Avoid overloading circuits.",
             "Tip: Charge all terminals to restore full power."
        ]
        self.nodes: list[dict[str, Any]] = []
        self.gaps: list[dict[str, Any]] = []
        self.power_level = 0.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        self.power_level = 0.0
        
        # Build circuit
        self.nodes = [
            {"x": 100, "y": HEIGHT/2, "type": "source", "active": True},
            {"x": 300, "y": HEIGHT/2 - 100, "type": "relay", "active": False},
            {"x": 300, "y": HEIGHT/2 + 100, "type": "relay", "active": False},
            {"x": 500, "y": HEIGHT/2 - 100, "type": "house", "active": False, "charge": 0},
            {"x": 500, "y": HEIGHT/2 + 100, "type": "house", "active": False, "charge": 0},
            {"x": 500, "y": HEIGHT/2, "type": "house", "active": False, "charge": 0},
            {"x": 700, "y": HEIGHT/2 - 50, "type": "house", "active": False, "charge": 0},
            {"x": 700, "y": HEIGHT/2 + 50, "type": "house", "active": False, "charge": 0},
        ]
        
        self.gaps = [
            {"n1": 0, "n2": 1, "x": 200, "y": HEIGHT/2 - 50, "active": False, "req_time": 3.0, "time": 0},
            {"n1": 0, "n2": 2, "x": 200, "y": HEIGHT/2 + 50, "active": False, "req_time": 3.0, "time": 0},
            {"n1": 1, "n2": 3, "x": 400, "y": HEIGHT/2 - 100, "active": False, "req_time": 2.0, "time": 0},
            {"n1": 2, "n2": 4, "x": 400, "y": HEIGHT/2 + 100, "active": False, "req_time": 2.0, "time": 0},
            {"n1": 1, "n2": 5, "x": 400, "y": HEIGHT/2 - 50, "active": False, "req_time": 4.0, "time": 0},
            {"n1": 2, "n2": 5, "x": 400, "y": HEIGHT/2 + 50, "active": False, "req_time": 4.0, "time": 0},
            {"n1": 3, "n2": 6, "x": 600, "y": HEIGHT/2 - 75, "active": False, "req_time": 1.5, "time": 0},
            {"n1": 4, "n2": 7, "x": 600, "y": HEIGHT/2 + 75, "active": False, "req_time": 1.5, "time": 0},
        ]

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Reset node states (except source and completed charges)
        for i, n in enumerate(self.nodes):
            if n["type"] == "relay":
                n["active"] = False
        
        houses_complete = 0
        houses_total = sum(1 for n in self.nodes if n["type"] == "house")
        
        # Player bridging gaps
        for g in self.gaps:
             if not g["active"]:
                 if abs(player.x - g["x"]) < 25 and abs(player.y - g["y"]) < 25:
                       g["time"] += dt
                       if g["time"] >= g["req_time"]:
                            g["active"] = True
                            self.shake = 2.0
                 else:
                       g["time"] = max(0.0, g["time"] - dt)
        
        # Power flow propagation
        # Since it's a DAG left-to-right, we can do multiple passes
        for _ in range(3):
            for g in self.gaps:
                n1 = self.nodes[g["n1"]]
                n2 = self.nodes[g["n2"]]
                if n1["active"] and g["active"]:
                    if n2["type"] == "relay":
                        n2["active"] = True
                    elif n2["type"] == "house":
                        n2["active"] = True
                        n2["charge"] = min(100.0, float(n2.get("charge", 0)) + 25.0 * dt)
                        
        # Check completion
        power = 0.0
        for n in self.nodes:
            if n["type"] == "house":
                power += n.get("charge", 0) / 100.0
                if n.get("charge", 0) >= 100.0:
                    houses_complete += 1
                    
        self.power_level = (power / houses_total) * 100.0
        
        if self.power_level >= 99.9:
            self.finished = True
            self.success = True
            self.message = "City powered up! All sectors fully restored."
            if self.timer > 45: self.grade = "S"
            elif self.timer > 30: self.grade = "A"
            elif self.timer > 15: self.grade = "B"
            else: self.grade = "C"
            
        if self.timer <= 0:
            self.finished = True
            self.success = self.power_level >= 40.0
            if self.success:
                self.message = f"Shift Over! Power restored to {int(self.power_level)}% of the city."
                self.grade = self.calculate_grade()
            else:
                self.message = "Blackout! Total failure to secure the power grid."

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#2f3640" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Draw connections
        for g in self.gaps:
             n1 = self.nodes[g["n1"]]
             n2 = self.nodes[g["n2"]]
             color = "#fbc531" if g["active"] and n1["active"] else ("#718093" if g["active"] else "#2f3640")
             if self.high_contrast: color = "#ffff00" if g["active"] and n1["active"] else "#555"
             
             canvas.create_line(n1["x"]+sx, n1["y"]+sy, n2["x"]+sx, n2["y"]+sy, fill=color, width=4)
             
             # Gap marker
             if not g["active"]:
                  canvas.create_rectangle(g["x"]-15+sx, g["y"]-15+sy, g["x"]+15+sx, g["y"]+15+sy, outline="#e84118", width=2, dash=(4,4))
                  # Progress bar for gap
                  if g["time"] > 0:
                       canvas.create_rectangle(g["x"]-15+sx, g["y"]+20+sy, g["x"]-15 + 30*(g["time"]/g["req_time"])+sx, g["y"]+24+sy, fill="#00a8ff", outline="")

        # Draw nodes
        for n in self.nodes:
             if n["type"] == "source":
                  canvas.create_rectangle(n["x"]-25+sx, n["y"]-25+sy, n["x"]+25+sx, n["y"]+25+sy, fill="#e1b12c", outline="#fbc531", width=3)
                  canvas.create_text(n["x"]+sx, n["y"]+sy, text="PWR", fill="#fff", font=("Helvetica", 10, "bold"))
             elif n["type"] == "relay":
                  color = "#4cd137" if n["active"] else "#7f8fa6"
                  canvas.create_oval(n["x"]-20+sx, n["y"]-20+sy, n["x"]+20+sx, n["y"]+20+sy, fill=color, outline="#353b48")
                  canvas.create_text(n["x"]+sx, n["y"]+sy, text="R", fill="#fff", font=("Helvetica", 10))
             elif n["type"] == "house":
                  color = "#fbc531" if n.get("charge", 0) >= 100 else ("#00a8ff" if n.get("charge", 0) > 0 else "#2f3640")
                  canvas.create_polygon(n["x"]+sx, n["y"]-20+sy, n["x"]-20+sx, n["y"]+sy, n["x"]+20+sx, n["y"]+sy, fill=color, outline="#fff")
                  canvas.create_rectangle(n["x"]-15+sx, n["y"]+sy, n["x"]+15+sx, n["y"]+20+sy, fill=color, outline="#fff")
                  canvas.create_text(n["x"]+sx, n["y"]+10+sy, text=f"{int(n.get('charge', 0))}%", fill="#fff", font=("Helvetica", 8))

        # HUD specific
        canvas.create_rectangle(WIDTH/2 - 150, 60, WIDTH/2 + 150, 80, fill="#353b48", outline="#fff")
        canvas.create_rectangle(WIDTH/2 - 148, 62, WIDTH/2 - 148 + 296 * (self.power_level/100.0), 78, fill="#fbc531", outline="")
        canvas.create_text(WIDTH/2, 70, text=f"CITY POWER GRID: {int(self.power_level)}%", fill="#2f3640", font=("Helvetica", 11, "bold"))

        player.draw(canvas)
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
