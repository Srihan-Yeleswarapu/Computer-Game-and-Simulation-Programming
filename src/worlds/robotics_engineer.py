import random
import math
import time
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class RoboticsEngineerWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Robotics Engineer",
            summary="Build and stabilize a functioning robot",
            duration=90.0,
        )
        self.briefing = [
             "ROBOT TEST: Prototype is unstable!",
             "As the Robotics Engineer, you must assemble",
             "a robot that functions properly.",
             "Retrieve parts matching the blueprint requirements.",
             "Warning: Incorrect parts will destabilize the robot!"
        ]
        self.hints = [
             "Tip: Check the requested part in the center blueprint.",
             "Tip: Wait for the correct part to drop onto the belts.",
             "Tip: Touch the parts to collect them.",
             "Tip: Build 2 successful robots to win."
        ]
        self.parts = ["ARM", "LEG", "CHASSIS", "SENSOR", "CORE"]
        self.colors = ["#ff4757", "#2ed573", "#1e90ff", "#ffa502", "#9b59b6"]
        self.active_parts: list[dict[str, Any]] = []
        self.current_req = ""
        self.robots_built = 0
        self.robot_stability = 100.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2 + 100)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        
        self.active_parts = []
        self.current_req = random.choice(self.parts)
        self.robots_built = 0
        self.robot_stability = 100.0
        player.speed = 450.0

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        matching_parts = [p for p in self.active_parts if p["type"] == self.current_req]
        if matching_parts:
            target = min(matching_parts, key=lambda p: math.hypot(player.x - p["x"], player.y - p["y"]))
            target_pos = (float(target["x"]), float(target["y"]))
            if math.hypot(player.x - target_pos[0], player.y - target_pos[1]) < 30:
                return (f"Touch this {self.current_req} part now to collect it.", target_pos)
            return (f"Move to the {target['side']} belt and collect this {self.current_req} part.", target_pos)
            
        wrong_parts = [p for p in self.active_parts if p["type"] != self.current_req]
        if wrong_parts:
            closest_wrong = min(wrong_parts, key=lambda p: math.hypot(player.x - p["x"], player.y - p["y"]))
            if math.hypot(player.x - closest_wrong["x"], player.y - closest_wrong["y"]) < 100:
                return (f"Do not touch this {closest_wrong['type']}. Wait for a {self.current_req} part instead.", (float(closest_wrong["x"]), float(closest_wrong["y"])))
                
        return (f"No {self.current_req} is in reach yet. Stay centered and watch both belts.", (WIDTH / 2, HEIGHT / 2))

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        player.update(dt, keys, self.bounds)
        
        # Spawn parts on left and right belts
        if random.random() < 2.5 * dt:
            typ = random.choice(self.parts)
            side = random.choice(["left", "right"])
            x = 50 if side == "left" else WIDTH - 50
            y = -40
            
            # Prevent overlap
            overlap = False
            for p in self.active_parts:
                if p["side"] == side and abs(p["y"] - y) < 60:
                    overlap = True
                    break
            
            if not overlap:
                self.active_parts.append({"x": x, "y": y, "type": typ, "speed": 100.0, "side": side})

        new_parts = []
        for p in self.active_parts:
            p["y"] += p["speed"] * dt
            
            # Collection
            if math.hypot(player.x - p["x"], player.y - p["y"]) < 30:
                 if p["type"] == self.current_req:
                      self.robot_stability = min(100.0, self.robot_stability + 10.0)
                      self.current_req = random.choice(self.parts)
                      self.robots_built += 0.34 # 3 parts per robot completion for better pacing
                 else:
                      self.robot_stability -= 25.0
                      self.shake = 4.0
            elif p["y"] < HEIGHT + 20:
                 new_parts.append(p)
                 
        self.active_parts = new_parts
        
        if self.robot_stability <= 0:
            self.finished = True
            self.success = False
            self.message = "Critical Failure! The prototype exploded."
            
        if self.robots_built >= 3.0:
            self.finished = True
            self.success = True
            self.message = "Assembly complete! 2 functional prototypes built."
            self.grade = self.calculate_grade()
            
        if self.timer <= 0:
            self.finished = True
            self.success = self.robots_built >= 1.0
            if self.success:
                self.message = f"Shift Over! Factory produced {int(self.robots_built)} functional prototypes."
                self.grade = self.calculate_grade()
            else:
                self.message = "Deadline missed! The assembly line failed to produce a working unit."

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#f5f6fa" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Conveyor belts
        for y_line in range(int((time.time() * 100) % 40), int(HEIGHT), 40):
             # Left belt
             canvas.create_line(30+sx, y_line+sy, 70+sx, y_line+sy, fill="#bdc3c7", width=3)
             # Right belt
             canvas.create_line(WIDTH-70+sx, y_line+sy, WIDTH-30+sx, y_line+sy, fill="#bdc3c7", width=3)
             
        canvas.create_rectangle(25+sx, 0+sy, 75+sx, HEIGHT+sy, outline="#7f8c8d", width=2)
        canvas.create_rectangle(WIDTH-75+sx, 0+sy, WIDTH-25+sx, HEIGHT+sy, outline="#7f8c8d", width=2)
        
        # Blueprint Station
        canvas.create_rectangle(WIDTH/2-80+sx, HEIGHT/2-60+sy, WIDTH/2+80+sx, HEIGHT/2+40+sy, fill="#192a56", outline="#4cd137", width=3)
        canvas.create_text(WIDTH/2+sx, HEIGHT/2-40+sy, text="REQUESTED PART", fill="#4cd137", font=("Helvetica", 10, "bold"))
        req_idx = self.parts.index(self.current_req)
        req_color = self.colors[req_idx]
        canvas.create_text(WIDTH/2+sx, HEIGHT/2-5+sy, text=self.current_req, fill=req_color, font=("Helvetica", 18, "bold"))
        
        # Draw parts
        for p in self.active_parts:
             idx = self.parts.index(p["type"])
             color = self.colors[idx]
             canvas.create_rectangle(p["x"]-20+sx, p["y"]-20+sy, p["x"]+20+sx, p["y"]+20+sy, fill=color, outline="#2c3e50")
             canvas.create_text(p["x"]+sx, p["y"]+sy, text=p["type"][:3], fill="#fff", font=("Helvetica", 8, "bold"))
             
        player.draw(canvas)
        
        # HUD
        canvas.create_rectangle(WIDTH/2 - 150, 60, WIDTH/2 + 150, 80, fill="#2f3542", outline="#fff")
        canvas.create_rectangle(WIDTH/2 - 148, 62, WIDTH/2 - 148 + 296 * max(0.0, self.robot_stability)/100.0, 78, fill="#e84118", outline="")
        canvas.create_text(WIDTH/2, 70, text=f"STABILITY: {int(self.robot_stability)}%", fill="#f5f6fa", font=("Helvetica", 11, "bold"))
        
        canvas.create_text(WIDTH/2, 100, text=f"ROBOTS BUILT: {int(self.robots_built)}/3", fill="#192a56", font=("Helvetica", 14, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
