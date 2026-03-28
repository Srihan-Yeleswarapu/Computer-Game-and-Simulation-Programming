import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class PsychologistWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Psychologist",
            summary="Help patients manage stress during a crisis",
            duration=90.0,
        )
        self.briefing = [
             "CRISIS ALERT: Patients are experiencing high stress levels!",
             "As the Psychologist, you must help patients stabilize",
             "their emotions and maintain mental well-being.",
             "Balance multiple patients and provide effective solutions.",
             "Warning: If stress levels rise too high, it will be a failure!"
        ]
        self.hints = [
             "Tip: Prioritize patients with highest stress levels.",
             "Tip: Use calming techniques to reduce stress quickly.",
             "Tip: Balance time between multiple patients.",
             "Tip: Monitor emotional stability indicators carefully."
        ]
        self.patients: list[dict[str, Any]] = []
        self.active_patient = -1

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        
        self.patients = [
            {"x": WIDTH/4, "y": HEIGHT/4, "stress": 20.0, "rate": 2.5},
            {"x": WIDTH*3/4, "y": HEIGHT/4, "stress": 30.0, "rate": 3.0},
            {"x": WIDTH/4, "y": HEIGHT*3/4, "stress": 10.0, "rate": 4.0},
            {"x": WIDTH*3/4, "y": HEIGHT*3/4, "stress": 40.0, "rate": 2.0},
        ]

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Increase stress
        failed = False
        self.active_patient = -1
        
        for i, p in enumerate(self.patients):
            dist = math.hypot(player.x - p["x"], player.y - p["y"])
            if dist < 60:
                self.active_patient = i
                
            if i == self.active_patient and "space" in keys:
                # Therapy in progress
                p["stress"] = max(0.0, p["stress"] - dt * 25.0)
            else:
                p["stress"] += p["rate"] * dt
                
            if p["stress"] >= 100.0:
                failed = True
                
        if failed:
            self.finished = True
            self.success = False
            self.message = "Crisis escalation! Stress levels reached maximum capacity."
            
        if self.timer <= 0:
            self.finished = True
            self.success = True
            self.message = "Shift complete. Patients are stabilized."
            avg_stress = sum(p["stress"] for p in self.patients) / len(self.patients)
            if avg_stress < 20: self.grade = "S"
            elif avg_stress < 40: self.grade = "A"
            elif avg_stress < 60: self.grade = "B"
            else: self.grade = "C"

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#f5f6fa" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)
        
        # Draw rooms
        canvas.create_rectangle(50, 50, WIDTH/2 - 20, HEIGHT/2 - 20, outline="#dcdde1", width=2)
        canvas.create_rectangle(WIDTH/2 + 20, 50, WIDTH - 50, HEIGHT/2 - 20, outline="#dcdde1", width=2)
        canvas.create_rectangle(50, HEIGHT/2 + 20, WIDTH/2 - 20, HEIGHT - 50, outline="#dcdde1", width=2)
        canvas.create_rectangle(WIDTH/2 + 20, HEIGHT/2 + 20, WIDTH - 50, HEIGHT - 50, outline="#dcdde1", width=2)

        for i, p in enumerate(self.patients):
            color = "#e84118" if p["stress"] > 75 else ("#fbc531" if p["stress"] > 40 else "#4cd137")
            canvas.create_oval(p["x"]-20, p["y"]-20, p["x"]+20, p["y"]+20, fill=color, outline="#2f3640", width=2)
            
            # Stress bar
            canvas.create_rectangle(p["x"]-25, p["y"]-35, p["x"]+25, p["y"]-25, fill="#353b48")
            canvas.create_rectangle(p["x"]-24, p["y"]-34, p["x"]-24 + 48*(p["stress"]/100.0), p["y"]-26, fill=color)
            canvas.create_text(p["x"], p["y"]-45, text=f"Stress: {int(p['stress'])}%", fill="#2f3640" if not self.high_contrast else "#fff", font=("Avenir", 10, "bold"))
            
            if i == self.active_patient and "space" in self.keys:
                 canvas.create_line(player.x, player.y, p["x"], p["y"], fill="#4bcffa", width=3, dash=(4,4))
                 
        player.draw(canvas)

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
