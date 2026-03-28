import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class AIEngineerWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="AI Engineer",
            summary="Train AI model to perform accurately",
            duration=90.0,
        )
        self.briefing = [
             "AI TRAINING ALERT: Model performance is low!",
             "As the AI Engineer, you must improve the model",
             "by leading it to high-quality training data.",
             "Avoid biased data, or the model will fail.",
             "Warning: Poor training will corrupt the AI!"
        ]
        self.hints = [
             "Tip: Lead the tracking AI node to Green data.",
             "Tip: Keep the AI away from Red biased data.",
             "Tip: The AI follows you!",
             "Tip: Maximize accuracy to deploy the model."
        ]
        self.ai_node = {"x": WIDTH/2, "y": 50, "speed": 100.0}
        self.data_points: list[dict[str, Any]] = []
        self.accuracy = 25.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 50)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        
        self.ai_node = {"x": WIDTH/2, "y": 50, "speed": 120.0}
        self.data_points = []
        self.accuracy = 25.0

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # AI follows player
        angle = math.atan2(player.y - self.ai_node["y"], player.x - self.ai_node["x"])
        self.ai_node["x"] += math.cos(angle) * self.ai_node["speed"] * dt
        self.ai_node["y"] += math.sin(angle) * self.ai_node["speed"] * dt
        
        # Spawn data
        if random.random() < 2.5 * dt:
            typ = random.choice(["valid", "bias"])
            self.data_points.append({"x": random.uniform(50, WIDTH-50), "y": random.uniform(50, HEIGHT-50), "type": typ})
            
        # Data expiry and AI consumption
        new_data = []
        for d in self.data_points:
            # Did AI eat it?
            if math.hypot(self.ai_node["x"] - d["x"], self.ai_node["y"] - d["y"]) < 25:
                 if d["type"] == "valid":
                      self.accuracy = min(100.0, self.accuracy + 4.0)
                 else:
                      self.accuracy = max(0.0, self.accuracy - 8.0)
                      self.shake = 3.0
            else:
                 new_data.append(d)
                 
        # limit data points
        if len(new_data) > 15:
             new_data.pop(0)
             
        self.data_points = new_data
        
        if self.accuracy >= 100.0:
            self.finished = True
            self.success = True
            self.message = "Model deployed! AI training successfully completed."
            if self.timer > 60: self.grade = "S"
            elif self.timer > 40: self.grade = "A"
            elif self.timer > 20: self.grade = "B"
            else: self.grade = "C"
            
        if self.timer <= 0:
            self.finished = True
            self.success = False
            self.message = "Failed! The AI model remained undertrained."

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#f1f2f6" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # AI visual tether to player
        canvas.create_line(player.x+sx, player.y+sy, self.ai_node["x"]+sx, self.ai_node["y"]+sy, fill="#a4b0be", dash=(4,4))
        
        for d in self.data_points:
             color = "#2ed573" if d["type"] == "valid" else "#ff4757"
             shape = canvas.create_oval if d["type"] == "valid" else canvas.create_rectangle
             shape(d["x"]-10+sx, d["y"]-10+sy, d["x"]+10+sx, d["y"]+10+sy, fill=color, outline="#2f3542")

        # Draw AI Node
        canvas.create_oval(self.ai_node["x"]-20+sx, self.ai_node["y"]-20+sy, self.ai_node["x"]+20+sx, self.ai_node["y"]+20+sy, fill="#1e90ff", outline="#7bed9f", width=3)
        canvas.create_text(self.ai_node["x"]+sx, self.ai_node["y"]+sy, text="AI", fill="#fff", font=("Helvetica", 10, "bold"))

        player.draw(canvas)

        # HUD specific
        canvas.create_rectangle(WIDTH/2 - 150, 60, WIDTH/2 + 150, 80, fill="#2f3542", outline="#fff")
        canvas.create_rectangle(WIDTH/2 - 148, 62, WIDTH/2 - 148 + 296 * (self.accuracy/100.0), 78, fill="#1e90ff", outline="")
        canvas.create_text(WIDTH/2, 70, text=f"AI ACCURACY: {int(self.accuracy)}%", fill="#1e272e" if self.accuracy > 50 else "#fff", font=("Helvetica", 11, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
