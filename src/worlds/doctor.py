import random
import math
import tkinter as tk
from ..utils import WIDTH, HEIGHT, TEXT
from ..player import Player
from .base import BaseWorld

class DoctorWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Doctor",
            summary="Diagnose patients and perform treatments",
            duration=60.0,
        )
        self.patients = []
        self.current_patient = 0
        self.health_score = 100
        self.diagnosis_stage = True
        self.selected_treatment = ""
        self.feedback = ""
        
        self.symptoms_db = [
            {"sym": "High Fever, Cough", "diag": "Flu", "treat": "Antivirals"},
            {"sym": "Broken Bone, Pain", "diag": "Fracture", "treat": "Cast"},
            {"sym": "Deep Cut, Bleeding", "diag": "Laceration", "treat": "Stitches"},
            {"sym": "Chest Pain, Nausea", "diag": "Heart Attack", "treat": "CPR/Defib"},
        ]

    def reset(self, player: Player, difficulty: int = 0) -> None:
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.health_score = 100
        self.current_patient = 0
        self.diagnosis_stage = True
        self.selected_treatment = ""
        self.feedback = ""
        
        # Difficulty Scaling
        num_patients = 3 + int(difficulty / 3) # 3 to 6
        
        # Generate patients
        self.patients = []
        for _ in range(num_patients):
            case = random.choice(self.symptoms_db)
            self.patients.append({
                "name": f"Patient {random.randint(100, 999)}",
                "symptoms": case["sym"],
                "diagnosis": case["diag"],
                "treatment": case["treat"],
                "status": "waiting"
            })

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        
        # Simple Logic: 1, 2, 3, 4 keys to select treatment option
        # No movement needed for player really, it's a UI mini-game
        
        if self.current_patient < len(self.patients):
            if "1" in keys: self.selected_treatment = "Antivirals"
            if "2" in keys: self.selected_treatment = "Cast"
            if "3" in keys: self.selected_treatment = "Stitches"
            if "4" in keys: self.selected_treatment = "CPR/Defib"
            
            if "space" in keys and self.selected_treatment:
                # Check correctness
                patient = self.patients[self.current_patient]
                if self.selected_treatment == patient["treatment"]:
                    self.feedback = "Correct treatment applied!"
                    patient["status"] = "cured"
                    self.current_patient += 1
                    self.selected_treatment = ""
                else:
                    self.feedback = "Wrong treatment! Patient health dropped."
                    self.health_score -= 20
                    self.timer -= 5
                
                # Debounce hack
                keys.discard("space")
        else:
            if self.health_score > 0:
                self.finished = True
                self.success = True
                self.message = "Shift complete. Patients are stable."
            else:
                self.finished = True
                self.success = False
                self.message = "Critical failure. Too many mistakes."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        # Hospital BG
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#e6f7ff", outline="")
        
        # HUD
        canvas.create_text(20, 20, anchor="w", text=f"Hospital Rating: {self.health_score}%", font=("Helvetica", 16, "bold"), fill="#d00")
        
        if self.current_patient < len(self.patients):
            p = self.patients[self.current_patient]
            
            # Patient Info Card
            canvas.create_rectangle(WIDTH/2 - 200, 100, WIDTH/2 + 200, 300, fill="#fff", outline="#aaa", width=2)
            canvas.create_text(WIDTH/2, 130, text=p["name"], font=("Helvetica", 18, "bold"), fill="#000")
            canvas.create_text(WIDTH/2, 170, text=f"Symptoms: {p['symptoms']}", font=("Helvetica", 14), fill="#333")
            
            # Options
            canvas.create_text(WIDTH/2, 350, text="Select Treatment (Press 1-4, then SPACE):", font=("Helvetica", 12, "bold"), fill="#000")
            
            options = ["1: Antivirals (Flu)", "2: Cast (Fracture)", "3: Stitches (Cut)", "4: CPR/Defib (Heart)"]
            y = 380
            for opt in options:
                color = "#000"
                if self.selected_treatment and opt.startswith(self.selected_treatment[0]): # simplistic match for highlight
                     pass # handled below logic is a bit decoupled
                
                # Better highlight logic
                key = opt.split(":")[0]
                is_selected = False
                if self.selected_treatment == "Antivirals" and key == "1": is_selected = True
                elif self.selected_treatment == "Cast" and key == "2": is_selected = True
                elif self.selected_treatment == "Stitches" and key == "3": is_selected = True
                elif self.selected_treatment == "CPR/Defib" and key == "4": is_selected = True
                
                bg = "#ff0" if is_selected else "#fff"
                canvas.create_rectangle(WIDTH/2 - 150, y, WIDTH/2 + 150, y+30, fill=bg, outline="#777")
                canvas.create_text(WIDTH/2, y+15, text=opt, font=("Helvetica", 11), fill="#000")
                y += 40
            
            if self.feedback:
                color = "#0a0" if "Correct" in self.feedback else "#d00"
                canvas.create_text(WIDTH/2, 550, text=self.feedback, font=("Helvetica", 14, "bold"), fill=color)

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
