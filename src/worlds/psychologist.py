import math
import random
import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import HEIGHT, TEXT, WIDTH, clamp
from src.worlds.base import BaseWorld


class PsychologistWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Psychologist",
            summary="Triage clients, identify what they need, and use the right intervention to de-escalate the room.",
            duration=90.0,
        )
        self.briefing = [
            "CLINIC OVERLOAD: Four clients arrive with different emotional needs.",
            "Move between rooms, read each client's presentation, and choose the right support approach.",
            "Use grounding for panic, breathing for acute physiological arousal, reflection for grief or overwhelm,",
            "and reframing for distorted self-talk. Wrong interventions damage trust and raise distress.",
        ]
        self.hints = [
            "Tip: Match the intervention to the client's cue words, not just the distress meter.",
            "Tip: Rapport improves when you stay with the right client and use the right approach.",
            "Tip: Mismatched interventions can escalate distress instead of reducing it.",
            "Tip: Stabilize each client's session progress before moving on.",
        ]
        self.interventions = [
            {"key": "1", "name": "Grounding", "focus": "panic", "color": "#4cc9f0"},
            {"key": "2", "name": "Breathing", "focus": "activation", "color": "#90be6d"},
            {"key": "3", "name": "Reflection", "focus": "overwhelm", "color": "#f9c74f"},
            {"key": "4", "name": "Reframing", "focus": "negative_thoughts", "color": "#f9844a"},
        ]
        self.client_templates = [
            {
                "name": "Mia",
                "presenting_issue": "panic spike before an exam",
                "cue": "I cannot slow my body down.",
                "focus": "activation",
                "secondary_focus": "panic",
                "notes": "shaky breathing, racing heart, can't sit still",
            },
            {
                "name": "Jordan",
                "presenting_issue": "grief after a family loss",
                "cue": "Everything feels too heavy to say out loud.",
                "focus": "overwhelm",
                "secondary_focus": "negative_thoughts",
                "notes": "withdrawn posture, quiet voice, tearful pauses",
            },
            {
                "name": "Alex",
                "presenting_issue": "catastrophic self-talk after rejection",
                "cue": "This proves I fail at everything.",
                "focus": "negative_thoughts",
                "secondary_focus": "overwhelm",
                "notes": "spiraling thoughts, harsh self-judgment",
            },
            {
                "name": "Noah",
                "presenting_issue": "acute panic after a crowded commute",
                "cue": "I feel trapped and the room keeps closing in.",
                "focus": "panic",
                "secondary_focus": "activation",
                "notes": "scanning exits, tense shoulders, hypervigilance",
            },
            {
                "name": "Sofia",
                "presenting_issue": "burnout and emotional flooding",
                "cue": "I have too many things in my head at once.",
                "focus": "overwhelm",
                "secondary_focus": "activation",
                "notes": "mental overload, difficulty sequencing tasks",
            },
            {
                "name": "Ethan",
                "presenting_issue": "performance anxiety before a presentation",
                "cue": "My chest is tight and I think I am going to freeze.",
                "focus": "activation",
                "secondary_focus": "negative_thoughts",
                "notes": "rapid speech, clenched hands, fear of embarrassment",
            },
        ]
        self.room_positions = [
            (WIDTH * 0.25, HEIGHT * 0.27),
            (WIDTH * 0.75, HEIGHT * 0.27),
            (WIDTH * 0.25, HEIGHT * 0.66),
            (WIDTH * 0.75, HEIGHT * 0.66),
        ]
        self.patients: list[dict[str, Any]] = []
        self.active_patient = -1
        self.locked_patient = -1
        self.selected_intervention = 0
        self.completed_sessions = 0
        self.session_goal = 4
        self.global_risk = 0.0
        self.message_timer = 0.0
        self.bounds = (28.0, 58.0, WIDTH - 28.0, HEIGHT - 28.0)

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = "Assess the room, then choose the right intervention."
        self.message_timer = 3.0
        self.shake = 0.0
        self.particles = []
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.active_patient = -1
        self.locked_patient = -1
        self.selected_intervention = 0
        self.completed_sessions = 0
        self.global_risk = 0.0

        templates = random.sample(self.client_templates, 4)
        base_distress = [34.0, 48.0, 56.0, 42.0]
        base_rates = [1.15, 2, 2.1, 1.7]
        self.patients = []
        for index, template in enumerate(templates):
            x, y = self.room_positions[index]
            self.patients.append(
                {
                    "x": x,
                    "y": y,
                    "name": template["name"],
                    "issue": template["presenting_issue"],
                    "cue": template["cue"],
                    "notes": template["notes"],
                    "focus": template["focus"],
                    "secondary_focus": template["secondary_focus"],
                    "distress": base_distress[index] + random.uniform(-6.0, 10.0),
                    "baseline_rate": base_rates[index] + random.uniform(-0.35, 0.45),
                    "rapport": 45.0 + random.uniform(-8.0, 8.0),
                    "progress": 0.0,
                    "speaking": template["cue"],
                    "bubble_timer": 3.5,
                    "cooldown": 0.0,
                    "resolved": False,
                    "escalated": False,
                }
            )

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        self.message_timer = max(0.0, self.message_timer - dt)

        if self.just_pressed(keys, "1"):
            self.selected_intervention = 0
        elif self.just_pressed(keys, "2"):
            self.selected_intervention = 1
        elif self.just_pressed(keys, "3"):
            self.selected_intervention = 2
        elif self.just_pressed(keys, "4"):
            self.selected_intervention = 3

        failed = False
        space_down = "space" in keys
        if not space_down:
            self.locked_patient = -1

        nearest_patient = -1
        best_dist = 9999.0
        for index, patient in enumerate(self.patients):
            if patient["resolved"]:
                continue
            dist = math.hypot(player.x - float(patient["x"]), player.y - float(patient["y"]))
            if dist < 125 and dist < best_dist:
                best_dist = dist
                nearest_patient = index

        if space_down:
            if self.locked_patient == -1:
                self.locked_patient = nearest_patient
            self.active_patient = self.locked_patient
        else:
            self.active_patient = nearest_patient

        for index, patient in enumerate(self.patients):
            if patient["resolved"]:
                continue

            patient["bubble_timer"] = max(0.0, float(patient["bubble_timer"]) - dt)
            patient["cooldown"] = max(0.0, float(patient["cooldown"]) - dt)
            if patient["bubble_timer"] <= 0:
                patient["speaking"] = random.choice(
                    [
                        str(patient["cue"]),
                        f"Need: {patient['issue']}",
                        f"Observe: {patient['notes']}",
                    ]
                )
                patient["bubble_timer"] = random.uniform(2.6, 4.3)

            intervention = self.interventions[self.selected_intervention]
            treating_here = index == self.active_patient and "space" in keys
            match_focus = intervention["focus"] == patient["focus"]
            secondary_match = intervention["focus"] == patient["secondary_focus"]

            if not (treating_here and (match_focus or secondary_match)):
                distress_rate = float(patient["baseline_rate"])
                if float(patient["rapport"]) < 30:
                    distress_rate += 1.0
                if float(patient["distress"]) > 75:
                    distress_rate += 0.8
                patient["distress"] = clamp(float(patient["distress"]) + distress_rate * dt, 0.0, 100.0)

            if not treating_here and random.random() < 0.09 * dt and float(patient["distress"]) < 88:
                patient["distress"] = clamp(float(patient["distress"]) + random.uniform(5.0, 9.0), 0.0, 100.0)
                patient["speaking"] = random.choice(
                    [
                        "I am losing control.",
                        "I cannot organize my thoughts.",
                        "Nothing I do is enough.",
                        "My body will not settle down.",
                    ]
                )
                patient["bubble_timer"] = 2.6
                self.shake = max(self.shake, 1.4)

            if index == self.active_patient and "space" in keys:
                effectiveness = 0.0
                if match_focus:
                    effectiveness = 1.0
                elif secondary_match:
                    effectiveness = 0.55
                else:
                    effectiveness = -0.35

                if effectiveness > 0:
                    patient["rapport"] = clamp(float(patient["rapport"]) + 14.0 * dt * effectiveness, 0.0, 100.0)
                    patient["progress"] = clamp(float(patient["progress"]) + 23.0 * dt * effectiveness, 0.0, 100.0)
                    patient["distress"] = clamp(float(patient["distress"]) - 20.0 * dt * effectiveness, 0.0, 100.0)
                    patient["speaking"] = f"{intervention['name']} is helping..."
                    patient["bubble_timer"] = 0.8
                else:
                    patient["rapport"] = clamp(float(patient["rapport"]) + 16.0 * dt * effectiveness, 0.0, 100.0)
                    patient["progress"] = clamp(float(patient["progress"]) + 10.0 * dt * effectiveness, 0.0, 100.0)
                    patient["distress"] = clamp(float(patient["distress"]) + 9.0 * dt * abs(effectiveness), 0.0, 100.0)
                    patient["speaking"] = f"{intervention['name']} does not fit right now."
                    patient["bubble_timer"] = 1.0
                    self.shake = max(self.shake, 1.0)

            if float(patient["progress"]) >= 100.0 and not patient["resolved"]:
                patient["resolved"] = True
                patient["distress"] = max(8.0, float(patient["distress"]) - 10.0)
                self.completed_sessions += 1
                self.message = f"{patient['name']} stabilized with a full intervention plan."
                self.message_timer = 2.6

            if float(patient["distress"]) >= 100.0:
                failed = True
                patient["escalated"] = True

        unresolved = [p for p in self.patients if not p["resolved"]]
        if unresolved:
            self.global_risk = sum(float(p["distress"]) for p in unresolved) / len(unresolved)
        else:
            self.global_risk = 0.0

        if failed:
            self.finished = True
            self.success = False
            self.message = "Clinic escalation: a client decompensated before the room could be stabilized."
            self.grade = "C"
        elif self.completed_sessions >= 4:
            self.finished = True
            self.success = True
            avg_rapport = sum(float(p["rapport"]) for p in self.patients) / len(self.patients)
            avg_distress = sum(float(p["distress"]) for p in self.patients) / len(self.patients)
            self.message = f"Shift complete. All 4 clients stabilized."
            
            if avg_rapport >= 78 and avg_distress <= 20:
                self.grade = "S"
            elif avg_rapport >= 66 and avg_distress <= 30:
                self.grade = "A"
            else:
                self.grade = "B"
        elif self.timer <= 0:
            self.finished = True
            self.success = self.completed_sessions >= 2
            if self.success:
                self.message = f"Shift Over! {self.completed_sessions}/4 clients stabilized."
                if self.completed_sessions == 3:
                    self.grade = "B"
                else:
                    self.grade = "C"
            else:
                self.message = f"Shift failed! Only {self.completed_sessions}/4 clients stabilized (Need 2+)."
                self.grade = "F"

        self.update_particles(dt)
        self.draw(canvas, player)

    def get_patient_color(self, distress: float) -> str:
        if distress >= 80:
            return "#d62828"
        if distress >= 55:
            return "#f77f00"
        if distress >= 30:
            return "#fcbf49"
        return "#52b788"

    def draw_intervention_bar(self, canvas: tk.Canvas) -> None:
        panel_y = HEIGHT - 96
        canvas.create_rectangle(18, panel_y, WIDTH - 18, HEIGHT - 18, fill="#18212d", outline="#30506c", width=2)
        canvas.create_text(34, panel_y + 16, anchor="w", text="Interventions", fill="#b8d8f1", font=("Helvetica", 11, "bold"))

        for index, intervention in enumerate(self.interventions):
            x1 = 190 + index * 182
            x2 = x1 + 164
            selected = index == self.selected_intervention
            fill = intervention["color"] if selected else "#0f1823"
            text_fill = "#0a1018" if selected else "#edf6ff"
            outline = "#ffffff" if selected else "#31506a"
            canvas.create_rectangle(x1, panel_y + 10, x2, panel_y + 58, fill=fill, outline=outline, width=2 if selected else 1)
            canvas.create_text((x1 + x2) / 2, panel_y + 25, text=f"[{intervention['key']}] {intervention['name']}", fill=text_fill, font=("Helvetica", 10, "bold"))
            canvas.create_text((x1 + x2) / 2, panel_y + 43, text=f"Best for {intervention['focus'].replace('_', ' ')}", fill=text_fill, font=("Helvetica", 8))

    def draw_patient_room(self, canvas: tk.Canvas, patient: dict[str, Any], index: int, is_active: bool, player: Player) -> None:
        room_w = WIDTH / 2 - 40
        room_h = 180
        room_col = index % 2
        room_row = index // 2
        x1 = 20 + room_col * (room_w + 40)
        y1 = 100 + room_row * (room_h + 20)
        x2 = x1 + room_w
        y2 = y1 + room_h

        distress = float(patient["distress"])
        color = self.get_patient_color(distress)
        room_fill = "#ffffff" if not self.high_contrast else "#050505"
        border = "#78c6ff" if is_active else "#c7d8e8"
        if patient["resolved"]:
            border = "#52b788"

        canvas.create_rectangle(x1, y1, x2, y2, fill=room_fill, outline=border, width=4 if is_active else 2)
        
        # Name and Distress State
        canvas.create_text(x1 + 20, y1 + 30, anchor="nw", text=patient["name"], fill="#1d3557", font=("Helvetica", 24, "bold"))
        
        # Distress color thing (The "Icon")
        icon_x, icon_y = x1 + room_w - 80, y1 + 60
        canvas.create_rectangle(icon_x - 30, icon_y - 30, icon_x + 30, icon_y + 30, fill=color, outline="#2f3e46", width=3)
        canvas.create_text(icon_x, icon_y, text=f"{int(distress)}", fill="#fff", font=("Helvetica", 14, "bold"))
        canvas.create_text(icon_x, icon_y + 40, text="DISTRESS", fill="#1d3557", font=("Helvetica", 10, "bold"))

        # The Fix: Show exactly which number to press
        correct_key = "?"
        for inter in self.interventions:
            if inter["focus"] == patient["focus"]:
                correct_key = inter["key"]
                break
        
        canvas.create_text(x1 + 20, y1 + 80, anchor="nw", text=f"PRESS [{correct_key}] TO STABILIZE", fill="#1d3557", font=("Helvetica", 14, "bold"))

        # Progress bar (Stabilize)
        bar_w = room_w - 40
        canvas.create_rectangle(x1 + 20, y2 - 40, x1 + 20 + bar_w, y2 - 20, fill="#dce7f3", outline="")
        canvas.create_rectangle(x1 + 20, y2 - 40, x1 + 20 + bar_w * (float(patient["progress"]) / 100.0), y2 - 20, fill="#52b788", outline="")
        canvas.create_text(x1 + 20 + bar_w / 2, y2 - 30, text="SESSION PROGRESS", fill="#1d3557", font=("Helvetica", 9, "bold"))

        if is_active and not patient["resolved"]:
            canvas.create_line(player.x, player.y, icon_x, icon_y, fill="#5fa8ff", width=2, dash=(4, 2))
        elif patient["resolved"]:
            canvas.create_text(x2 - 20, y1 + 20, anchor="ne", text="STABILIZED", fill="#2a9d8f", font=("Helvetica", 12, "bold"))

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#eef4f8" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg, outline="")
        canvas.create_rectangle(0, 40, WIDTH, 84, fill="#dde9f3", outline="")

        for index, patient in enumerate(self.patients):
            self.draw_patient_room(canvas, patient, index, index == self.active_patient, player)

        canvas.create_rectangle(0, 0, WIDTH, 40, fill="#122033", outline="")
        canvas.create_text(16, 20, anchor="w", text="Psychology Intake Wing", fill="#f2f7fb", font=("Helvetica", 15, "bold"))
        canvas.create_text(WIDTH / 2, 20, text=f"Stabilized: {self.completed_sessions}/{self.session_goal}", fill="#d9ecff", font=("Helvetica", 12, "bold"))
        canvas.create_text(WIDTH - 170, 20, anchor="e", text=f"Time: {self.timer:05.1f}s", fill="#f2f7fb", font=("Helvetica", 12, "bold"))
        canvas.create_text(WIDTH - 18, 20, anchor="e", text=f"Unit Risk: {int(self.global_risk)}", fill="#ffcf99", font=("Helvetica", 12, "bold"))

        canvas.create_text(20, 50, anchor="nw", text="Match the client's cue to the right intervention.", fill="#26445f", font=("Helvetica", 10, "bold"))
        canvas.create_text(20, 66, anchor="nw", text="1 Grounding  2 Breathing  3 Reflection  4 Reframing", fill="#45657f", font=("Helvetica", 8, "bold"))
        if self.message and self.message_timer > 0:
            canvas.create_rectangle(360, 46, WIDTH - 20, 78, fill="#17314b", outline="#3b6d96")
            canvas.create_text((360 + WIDTH - 20) / 2, 62, text=self.message, fill="#eef7ff", font=("Helvetica", 9, "bold"), width=WIDTH - 410)

        self.draw_intervention_bar(canvas)
        canvas.create_text(WIDTH / 2, HEIGHT - 110, text=self.hints[self.current_hint_index], fill="#4f6d86", font=("Helvetica", 8, "italic"))
        player.draw(canvas)

        if self.finished:
            self.draw_result(canvas)
