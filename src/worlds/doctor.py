import random
import math
import time
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class DoctorWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Doctor",
            summary="Diagnose and treat emergency room patients",
            duration=90.0,
        )
        self.briefing = [
             "EMERGENCY CALL: Mass casualty incident!",
             "As the ER Doctor, you must triage and treat patients.",
             "Identify their symptoms and bring the correct tool.",
             "- High Temp -> Ice Pack",
             "- Fracture -> X-Ray",
             "- Bleeding -> Bandage"
        ]
        self.hints = [
             "Tip: Touch a supply table and hold SPACE to pick up a tool.",
             "Tip: Touch the patient and hold SPACE to treat them.",
             "Tip: Don't let a patient's health drop to zero!",
             "Tip: Treat as many patients as possible."
        ]
        self.held_item = ""
        self.patients: list[dict[str, Any]] = []
        self.beds = [
            {"x": WIDTH/4, "y": HEIGHT/2},
            {"x": WIDTH/2, "y": HEIGHT/2},
            {"x": WIDTH*3/4, "y": HEIGHT/2},
        ]
        self.tables = [
            {"name": "Ice Pack", "type": "ice", "color": "#00d2d3", "x": WIDTH/4, "y": HEIGHT-80},
            {"name": "X-Ray", "type": "xray", "color": "#feca57", "x": WIDTH/2, "y": HEIGHT-80},
            {"name": "Bandage", "type": "bandage", "color": "#ff9f43", "x": WIDTH*3/4, "y": HEIGHT-80},
        ]
        self.tools_map = {
            "fever": "ice",
            "fracture": "xray",
            "bleeding": "bandage"
        }
        self.score = 0
        self.treatment_progress = 0.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 4)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        
        self.held_item = ""
        self.patients = []
        self.score = 0
        self.treatment_progress = 0.0

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Spawn patients in empty beds
        occupied = [p["bed"] for p in self.patients]
        for i, bed in enumerate(self.beds):
            if i not in occupied and random.random() < 0.4 * dt:
                symptom = random.choice(list(self.tools_map.keys()))
                self.patients.append({
                    "bed": i,
                    "x": bed["x"],
                    "y": bed["y"],
                    "symptom": symptom,
                    "health": 100.0,
                    "rate": random.uniform(2.5, 4.5)
                })

        interacting = False
        
        # Table interaction
        for t in self.tables:
            if math.hypot(player.x - t["x"], player.y - t["y"]) < 40 and "space" in keys:
                 self.held_item = t["type"]
                 interacting = True

        new_patients = []
        patient_died = False
        
        for p in self.patients:
            if interacting: break
            
            p["health"] -= dt * p["rate"]
            
            # Treat interaction
            if math.hypot(player.x - p["x"], player.y - p["y"]) < 40 and "space" in keys:
                 if self.held_item == self.tools_map[p["symptom"]]:
                     self.treatment_progress += dt * 80.0
                     if self.treatment_progress >= 100.0:
                         self.score += 1
                         self.treatment_progress = 0.0
                         self.held_item = "" # Consume item
                         p["health"] = 0 # Mark for removal
                 else:
                     # Wrong item
                     self.shake = 2.0
                     p["health"] -= dt * 5.0 # Penalty
            else:
                 self.treatment_progress = max(0.0, self.treatment_progress - dt * 100.0)
                 
            if p["health"] <= 0:
                 if self.treatment_progress < 100: 
                      patient_died = True
                 # If it hit 0 because of treatment, it just gets removed (cured)
            else:
                 new_patients.append(p)
                 
        if not ("space" in keys):
             self.treatment_progress = 0.0

        if patient_died:
             self.finished = True
             self.success = False
             self.message = "Malpractice! A patient's health reached zero."
             return
             
        self.patients = new_patients
        
        if self.timer <= 0:
            self.finished = True
            self.success = True
            self.message = f"Shift over! You saved {self.score} patients."
            if self.score > 12: self.grade = "S"
            elif self.score > 8: self.grade = "A"
            elif self.score > 4: self.grade = "B"
            else: self.grade = "C"

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#e0f7fa" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Floor pattern
        if not self.high_contrast:
            for i in range(0, WIDTH, 40):
                for j in range(0, HEIGHT, 40):
                    if (i//40 + j//40) % 2 == 0:
                        canvas.create_rectangle(i+sx, j+sy, i+40+sx, j+40+sy, fill="#b2ebf2", outline="")

        # Beds
        for b in self.beds:
             canvas.create_rectangle(b["x"]-30+sx, b["y"]-20+sy, b["x"]+30+sx, b["y"]+20+sy, fill="#fff", outline="#95a5a6", width=2)
             canvas.create_rectangle(b["x"]-25+sx, b["y"]-15+sy, b["x"]-5+sx, b["y"]+15+sy, fill="#ecf0f1", outline="#bdc3c7")

        # Patients
        for p in self.patients:
             # Patient body
             canvas.create_oval(p["x"]-15+sx, p["y"]-15+sy, p["x"]+15+sx, p["y"]+15+sy, fill="#ffdd59", outline="#d1ccc0")
             # Symptom Icon
             sym_colors = {"fever": "#ff5252", "fracture": "#ffb142", "bleeding": "#8c7ae6"}
             canvas.create_rectangle(p["x"]-10+sx, p["y"]-25+sy, p["x"]+10+sx, p["y"]-15+sy, fill=sym_colors[p["symptom"]], outline="")
             
             # Health bar
             canvas.create_rectangle(p["x"]-20+sx, p["y"]-35+sy, p["x"]+20+sx, p["y"]-28+sy, fill="#2c3e50")
             canvas.create_rectangle(p["x"]-19+sx, p["y"]-34+sy, p["x"]-19 + 38 * max(0.0, p["health"]/100.0) + sx, p["y"]-29+sy, fill="#ff5252")
             
             # Treatment progress bar if active
             if self.treatment_progress > 0 and math.hypot(player.x - p["x"], player.y - p["y"]) < 40 and "space" in self.keys and self.held_item == self.tools_map[p["symptom"]]:
                  canvas.create_rectangle(p["x"]-20+sx, p["y"]+25+sy, p["x"]+20+sx, p["y"]+30+sy, fill="#34495e")
                  canvas.create_rectangle(p["x"]-20+sx, p["y"]+25+sy, p["x"]-20 + 40*(self.treatment_progress/100.0) + sx, p["y"]+30+sy, fill="#2ecc71")

        # Tables
        for t in self.tables:
             canvas.create_rectangle(t["x"]-25+sx, t["y"]-25+sy, t["x"]+25+sx, t["y"]+25+sy, fill="#ecf0f1", outline="#bdc3c7", width=3)
             canvas.create_oval(t["x"]-15+sx, t["y"]-15+sy, t["x"]+15+sx, t["y"]+15+sy, fill=t["color"], outline="")
             canvas.create_text(t["x"]+sx, t["y"]+35+sy, text=t["name"], fill="#2f3640" if not self.high_contrast else "#fff", font=("Helvetica", 9, "bold"))
             
        player.draw(canvas)
        
        # Show held item over player head
        if self.held_item:
             held_colors = {"ice": "#00d2d3", "xray": "#feca57", "bandage": "#ff9f43"}
             canvas.create_oval(player.x-10+sx, player.y-30+sy, player.x+10+sx, player.y-10+sy, fill=held_colors[self.held_item], outline="#fff", width=2)
             
        # HUD specific
        canvas.create_rectangle(20, 60, 180, 100, fill="#2c3e50", outline="#ecf0f1", width=2)
        canvas.create_text(100, 80, text=f"Patients Saved: {self.score}", fill="#2ecc71", font=("Helvetica", 11, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
