import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class DataScientistWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Data Scientist",
            summary="Analyze data to predict system outcomes",
            duration=72.0,
        )
        self.briefing = [
            "TRAIN your AI model to 99.9% accuracy.",
            "CATCH valid data (Green) and bonus patterns (Yellow).",
            "AVOID red anomalies that corrupt your dataset.",
            "MOVE quickly to intercept data before it drops."
        ]
        self.hints = [
             "Tip: Catch Green data points for clean data.",
             "Tip: Avoid Red anomalies, they ruin your model.",
             "Tip: Look for meaningful patterns.",
             "Tip: Yellow data gives bonus model accuracy."
        ]
        self.data_points: list[dict[str, Any]] = []
        self.model_accuracy = 50.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 50)
        self.timer = 72.0
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        self.data_points = []
        self.model_accuracy = 50.0

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        if not self.data_points:
            return ("Collect falling Green data packets to train your model.", None)
            
        # Target the nearest good data
        good_data = [d for d in self.data_points if d["type"] in {"valid", "bonus"}]
        if good_data:
            target = min(good_data, key=lambda d: math.hypot(player.x - d["x"], player.y - d["y"]))
            return (f"Catch the {target['type'].upper()} data point falling from the top.", (float(target["x"]), float(target["y"])))
            
        anomalies = [d for d in self.data_points if d["type"] == "anomaly"]
        if anomalies:
            target = min(anomalies, key=lambda d: math.hypot(player.x - d["x"], player.y - d["y"]))
            return ("AVOID Red Anomalies! They instantly ruin model accuracy.", (float(target["x"]), float(target["y"])))
            
        return ("Maintain model confidence by catching valid datasets.", None)

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Drain accuracy slowly over time
        self.model_accuracy = max(0.0, self.model_accuracy - dt * 2.5)
        
        # Spawn data - 30% increase
        if random.random() < 1.3 * dt:
            typ = random.choice(["valid", "anomaly", "bonus"])
            if typ == "valid": color, speed = "#2ed573", 100
            elif typ == "anomaly": color, speed = "#ff4757", 150
            else: color, speed = "#ffa502", 80
            
            self.data_points.append({"x": random.uniform(50, WIDTH-50), "y": -20, "type": typ, "color": color, "speed": speed})
            
        new_data = []
        for d in self.data_points:
            d["y"] += d["speed"] * dt
            if abs(player.x - d["x"]) < 25 and abs(player.y - d["y"]) < 25:
                 if d["type"] == "valid":
                      self.model_accuracy = min(100.0, self.model_accuracy + 5.0)
                 elif d["type"] == "bonus":
                      self.model_accuracy = min(100.0, self.model_accuracy + 15.0)
                 else:
                      self.model_accuracy = max(0.0, self.model_accuracy - 20.0)
                      self.shake = 3.0
            elif d["y"] < HEIGHT + 20:
                 new_data.append(d)
        self.data_points = new_data
        
        if self.model_accuracy >= 99.9:
            self.finished = True
            self.success = True
            self.message = "Model deployed! 99.9% accuracy achieved."
            if self.timer >= 50:
                self.grade = "S"
            elif self.timer >= 30:
                self.grade = "A"
            elif self.timer >= 10:
                self.grade = "B"
            else:
                self.grade = "C"
            
        if self.timer <= 0:
            self.finished = True
            self.success = self.model_accuracy >= 50.0
            if self.success:
                self.message = f"Shift Over! Model partially trained ({int(self.model_accuracy)}% confidence)."
                self.grade = self.calculate_grade()
            else:
                self.message = f"Deadline missed! Model confidence too low ({int(self.model_accuracy)}%)."

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#1e272e" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Grid lines for "data" feel
        for i in range(10):
            canvas.create_line(0, i*(HEIGHT/10)+sy, WIDTH, i*(HEIGHT/10)+sy, fill="#2f3542", dash=(2,2))
            
        for d in self.data_points:
             canvas.create_polygon(d["x"]+sx, d["y"]-10+sy, d["x"]-10+sx, d["y"]+sy, d["x"]+sx, d["y"]+10+sy, d["x"]+10+sx, d["y"]+sy, fill=d["color"], outline="#fff")

        # HUD specific
        canvas.create_rectangle(WIDTH/2 - 150, 60, WIDTH/2 + 150, 80, fill="#2f3542", outline="#fff")
        canvas.create_rectangle(WIDTH/2 - 148, 62, WIDTH/2 - 148 + 296 * (self.model_accuracy/100.0), 78, fill="#2ed573", outline="")
        canvas.create_text(WIDTH/2, 70, text=f"MODEL CONFIDENCE: {int(self.model_accuracy)}%", fill="#1e272e", font=("Helvetica", 11, "bold"))

        player.draw(canvas)
        # Custom player bucket overlay
        canvas.create_arc(player.x-25+sx, player.y-25+sy, player.x+25+sx, player.y+25+sy, start=180, extent=180, style=tk.ARC, outline="#1e90ff", width=4)
        
        if self.finished:
            self.draw_result(canvas)
