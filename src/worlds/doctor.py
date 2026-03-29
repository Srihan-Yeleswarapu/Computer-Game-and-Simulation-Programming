import math
import random
import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import HEIGHT, TEXT, WIDTH, clamp
from src.worlds.base import BaseWorld


class DoctorWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Doctor",
            summary="Read patient charts, grab the right treatment, and stabilize the ER.",
            duration=60.0,
        )
        self.case_types = [
            {
                "id": "fever",
                "condition": "High Fever",
                "symptoms": "Temp 103F, chills, flushed skin",
                "tool": "antipyretic",
                "tool_name": "Antipyretic",
                "color": "#ff6b6b",
            },
            {
                "id": "cut",
                "condition": "Deep Cut",
                "symptoms": "Heavy bleeding, open wound on forearm",
                "tool": "bandage",
                "tool_name": "Pressure Bandage",
                "color": "#ff9f43",
            },
            {
                "id": "fracture",
                "condition": "Broken Arm",
                "symptoms": "Severe pain, swelling, arm deformity",
                "tool": "cast",
                "tool_name": "Quick Cast",
                "color": "#feca57",
            },
            {
                "id": "asthma",
                "condition": "Asthma Attack",
                "symptoms": "Wheezing, chest tightness, shallow breathing",
                "tool": "inhaler",
                "tool_name": "Rescue Inhaler",
                "color": "#48dbfb",
            },
            {
                "id": "dehydration",
                "condition": "Dehydration",
                "symptoms": "Dizziness, dry lips, weak pulse",
                "tool": "iv",
                "tool_name": "IV Fluids",
                "color": "#1dd1a1",
            },
        ]
        self.case_by_id = {case["id"]: case for case in self.case_types}
        self.tool_catalog = [
            {"name": "Antipyretic", "type": "antipyretic", "color": "#ff6b6b", "x": 130.0, "y": HEIGHT - 85.0},
            {"name": "Pressure Bandage", "type": "bandage", "color": "#ff9f43", "x": 290.0, "y": HEIGHT - 85.0},
            {"name": "Quick Cast", "type": "cast", "color": "#feca57", "x": 450.0, "y": HEIGHT - 85.0},
            {"name": "Rescue Inhaler", "type": "inhaler", "color": "#48dbfb", "x": 610.0, "y": HEIGHT - 85.0},
            {"name": "IV Fluids", "type": "iv", "color": "#1dd1a1", "x": 770.0, "y": HEIGHT - 85.0},
        ]
        self.briefing = [
            "ER SURGE: Multiple patients are arriving at once.",
            "Read each bedside chart to see the exact condition and symptoms.",
            "Pick up the matching treatment from the supply stations, then hold SPACE at the bed to cure them.",
            "Wrong treatments waste precious time and hurt the patient's stability.",
        ]
        self.hints = [
            "Tip: Charts show the patient's condition, symptoms, and needed treatment.",
            "Tip: Hold SPACE on a supply station to pick up one treatment.",
            "Tip: Use the correct treatment on the matching patient to fill the cure bar.",
            "Tip: If a patient's stability hits zero, the mission fails immediately.",
        ]
        self.held_item = ""
        self.message = ""
        self.patients: list[dict[str, Any]] = []
        self.patient_counter = 0
        self.saved_patients = 0
        self.active_patient_id: int | None = None
        self.beds = [
            {"x": WIDTH * 0.18, "y": HEIGHT * 0.31},
            {"x": WIDTH * 0.5, "y": HEIGHT * 0.31},
            {"x": WIDTH * 0.82, "y": HEIGHT * 0.31},
            {"x": WIDTH * 0.33, "y": HEIGHT * 0.62},
            {"x": WIDTH * 0.67, "y": HEIGHT * 0.62},
        ]
        self.bounds = (30.0, 55.0, WIDTH - 30.0, HEIGHT - 35.0)

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 170.0)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        self.tutorial_timer = 4.0
        self.hint_display_timer = 0.0
        self.current_hint_index = 0

        self.held_item = ""
        self.patients = []
        self.patient_counter = 0
        self.saved_patients = 0
        self.active_patient_id = None

    def create_patient(self, bed_index: int, case_id: str | None = None) -> dict[str, Any]:
        case = self.case_by_id[case_id] if case_id else random.choice(self.case_types)
        bed = self.beds[bed_index]
        self.patient_counter += 1
        return {
            "id": self.patient_counter,
            "bed": bed_index,
            "x": bed["x"],
            "y": bed["y"],
            "condition": case["condition"],
            "symptoms": case["symptoms"],
            "tool": case["tool"],
            "tool_name": case["tool_name"],
            "color": case["color"],
            "stability": random.uniform(78.0, 96.0),
            "drain_rate": random.uniform(3.0, 5.0),
            "cure_progress": 0.0,
            "status": "waiting",
            "discharge_timer": 0.0,
        }

    def spawn_patients(self) -> None:
        occupied_beds = {patient["bed"] for patient in self.patients}
        minimum_opening = 2 if self.timer > 20.0 else 3
        if len(self.patients) >= minimum_opening:
            return

        for bed_index in range(len(self.beds)):
            if bed_index in occupied_beds:
                continue
            spawn_rate = 0.9 if len(self.patients) < 2 else 0.45
            if random.random() < spawn_rate:
                self.patients.append(self.create_patient(bed_index))
                occupied_beds.add(bed_index)

    def handle_supply_pickup(self, player: Player, keys: set[str]) -> bool:
        if "space" not in keys:
            return False
        for tool in self.tool_catalog:
            if math.hypot(player.x - tool["x"], player.y - tool["y"]) < 50.0:
                self.held_item = tool["type"]
                self.message = f"Picked up {tool['name']}."
                self.active_patient_id = None
                return True
        return False

    def handle_patient_treatment(self, dt: float, player: Player, keys: set[str]) -> bool:
        if "space" not in keys:
            self.active_patient_id = None
            return False

        treated_any = False
        for patient in self.patients:
            if patient["status"] != "waiting":
                continue
            if math.hypot(player.x - patient["x"], player.y - patient["y"]) >= 100.0:
                if self.active_patient_id == patient["id"]:
                    patient["cure_progress"] = 0.0
                continue

            treated_any = True
            self.active_patient_id = patient["id"]
            if self.held_item == patient["tool"]:
                patient["cure_progress"] = clamp(patient["cure_progress"] + dt * 75.0, 0.0, 100.0)
                patient["stability"] = clamp(patient["stability"] + dt * 22.0, 0.0, 100.0)
                self.message = f"Treating {patient['condition']} with {patient['tool_name']}..."
                if patient["cure_progress"] >= 100.0:
                    patient["status"] = "cured"
                    patient["discharge_timer"] = 1.1
                    patient["stability"] = 100.0
                    self.saved_patients += 1
                    self.held_item = ""
                    self.active_patient_id = None
                    self.message = f"{patient['condition']} stabilized and cured."
                return True

            patient["cure_progress"] = 0.0
            patient["stability"] = clamp(patient["stability"] - dt * 12.0, 0.0, 100.0)
            self.shake = 2.0
            self.message = f"Wrong treatment. {patient['condition']} needs {patient['tool_name']}."
            return True

        if not treated_any:
            self.active_patient_id = None
        return treated_any

    def update_patients(self, dt: float) -> bool:
        survivors: list[dict[str, Any]] = []
        for patient in self.patients:
            if patient["status"] == "cured":
                patient["discharge_timer"] -= dt
                if patient["discharge_timer"] > 0.0:
                    survivors.append(patient)
                continue

            patient["stability"] = clamp(patient["stability"] - dt * patient["drain_rate"], 0.0, 100.0)
            if patient["stability"] <= 0.0:
                self.finished = True
                self.success = False
                self.message = f"Patient lost: {patient['condition']} was not treated in time."
                return False
            survivors.append(patient)

        self.patients = survivors
        return True

    def calculate_grade(self) -> str:
        if not self.success:
            return "-"
        if self.saved_patients >= 9:
            return "S"
        if self.saved_patients >= 5:
            return "A"
        if self.saved_patients >= 3:
            return "B"
        return "C"

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
        if self.finished:
            self.draw(canvas, player)
            return

        if self.timer <= 0:
            self.finished = True
            self.success = self.saved_patients >= 3
            if self.success:
                self.message = f"Shift complete. {self.saved_patients} patients cured."
                self.grade = self.calculate_grade()
            else:
                self.message = f"Shift over! Only {self.saved_patients} patients stabilized. ER integrity low."
            self.draw(canvas, player)
            return

        self.spawn_patients()
        used_supply = self.handle_supply_pickup(player, keys)
        if not used_supply:
            self.handle_patient_treatment(dt, player, keys)

        if not self.update_patients(dt):
            self.draw(canvas, player)
            return

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw_bed(self, canvas: tk.Canvas, bed: dict[str, float], sx: float, sy: float) -> None:
        bx = float(bed["x"])
        by = float(bed["y"])
        canvas.create_rectangle(bx - 70.0 + sx, by - 32.0 + sy, bx + 70.0 + sx, by + 32.0 + sy, fill="#f5f6fa", outline="#8395a7", width=2)
        canvas.create_rectangle(bx - 62.0 + sx, by - 26.0 + sy, bx - 20.0 + sx, by + 26.0 + sy, fill="#dfe6e9", outline="#ced6e0")
        canvas.create_rectangle(bx - 70.0 + sx, by - 36.0 + sy, bx + 70.0 + sx, by - 32.0 + sy, fill="#576574", outline="")

    def draw_patient(self, canvas: tk.Canvas, patient: dict[str, Any], player: Player, sx: float, sy: float) -> None:
        px = float(patient["x"])
        py = float(patient["y"])
        body_color = "#ffeaa7" if patient["status"] == "waiting" else "#55efc4"
        canvas.create_oval(px - 18.0 + sx, py - 18.0 + sy, px + 18.0 + sx, py + 18.0 + sy, fill=body_color, outline="#2d3436", width=2)
        canvas.create_rectangle(px - 55.0 + sx, py - 82.0 + sy, px + 55.0 + sx, py - 22.0 + sy, fill="#1f2937", outline=patient["color"], width=2)
        canvas.create_text(px + sx, py - 70.0 + sy, text=patient["condition"], fill="#ffffff", font=("Helvetica", 9, "bold"))
        canvas.create_text(px + sx, py - 53.0 + sy, text=patient["symptoms"], fill="#dfe6e9", font=("Helvetica", 7), width=100)
        canvas.create_text(px + sx, py - 31.0 + sy, text=f"Needs: {patient['tool_name']}", fill=patient["color"], font=("Helvetica", 7, "bold"))

        canvas.create_rectangle(px - 42.0 + sx, py + 30.0 + sy, px + 42.0 + sx, py + 40.0 + sy, fill="#2c3e50", outline="")
        stability_color = "#2ecc71" if patient["stability"] > 60.0 else "#f1c40f" if patient["stability"] > 30.0 else "#e74c3c"
        canvas.create_rectangle(
            px - 41.0 + sx,
            py + 31.0 + sy,
            px - 41.0 + sx + 82.0 * (patient["stability"] / 100.0),
            py + 39.0 + sy,
            fill=stability_color,
            outline="",
        )
        canvas.create_text(px + sx, py + 51.0 + sy, text=f"Stability {patient['stability']:.0f}", fill="#ffffff", font=("Helvetica", 7, "bold"))

        if patient["status"] == "cured":
            canvas.create_text(px + sx, py + 68.0 + sy, text="CURED", fill="#2ecc71", font=("Helvetica", 10, "bold"))
        elif patient["cure_progress"] > 0.0 and self.active_patient_id == patient["id"]:
            canvas.create_rectangle(px - 42.0 + sx, py + 60.0 + sy, px + 42.0 + sx, py + 69.0 + sy, fill="#34495e", outline="")
            canvas.create_rectangle(
                px - 41.0 + sx,
                py + 61.0 + sy,
                px - 41.0 + sx + 82.0 * (patient["cure_progress"] / 100.0),
                py + 68.0 + sy,
                fill="#5fdbff",
                outline="",
            )
            canvas.create_text(px + sx, py + 81.0 + sy, text="TREATING", fill="#5fdbff", font=("Helvetica", 8, "bold"))

        if math.hypot(player.x - patient["x"], player.y - patient["y"]) < 82.0 and patient["status"] == "waiting":
            canvas.create_text(px + sx, py + 95.0 + sy, text="Hold SPACE to treat", fill="#ffffff", font=("Helvetica", 8, "bold"))

    def draw_tool_station(self, canvas: tk.Canvas, tool: dict[str, Any], player: Player, sx: float, sy: float) -> None:
        tx = float(tool["x"])
        ty = float(tool["y"])
        outline = "#ffffff" if self.held_item == tool["type"] else tool["color"]
        canvas.create_rectangle(tx - 48.0 + sx, ty - 30.0 + sy, tx + 48.0 + sx, ty + 30.0 + sy, fill="#f5f6fa", outline=outline, width=3)
        canvas.create_oval(tx - 16.0 + sx, ty - 16.0 + sy, tx + 16.0 + sx, ty + 16.0 + sy, fill=tool["color"], outline="")
        canvas.create_text(tx + sx, ty + 44.0 + sy, text=tool["name"], fill="#102a43" if not self.high_contrast else "#ffffff", font=("Helvetica", 8, "bold"))
        if math.hypot(player.x - tool["x"], player.y - tool["y"]) < 50.0:
            canvas.create_text(tx + sx, ty - 44.0 + sy, text="Hold SPACE to pick up", fill="#ffffff", font=("Helvetica", 8, "bold"))

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0
        sy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0

        bg = "#dff2ff" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0.0 + sx, 0.0 + sy, WIDTH + sx, HEIGHT + sy, fill=bg, outline="")
        canvas.create_rectangle(20.0 + sx, 55.0 + sy, WIDTH - 20.0 + sx, HEIGHT - 140.0 + sy, fill="#c8e6f5" if not self.high_contrast else "#111111", outline="")
        canvas.create_rectangle(0.0 + sx, HEIGHT - 140.0 + sy, WIDTH + sx, HEIGHT + sy, fill="#9fb3c8" if not self.high_contrast else "#050505", outline="")

        for bed in self.beds:
            self.draw_bed(canvas, bed, sx, sy)
        for patient in self.patients:
            self.draw_patient(canvas, patient, player, sx, sy)
        for tool in self.tool_catalog:
            self.draw_tool_station(canvas, tool, player, sx, sy)

        player.draw(canvas)
        if self.held_item:
            held_tool = next(tool for tool in self.tool_catalog if tool["type"] == self.held_item)
            canvas.create_oval(player.x - 10.0 + sx, player.y - 34.0 + sy, player.x + 10.0 + sx, player.y - 14.0 + sy, fill=held_tool["color"], outline="#ffffff", width=2)

        canvas.create_rectangle(18.0, 50.0, 270.0, 118.0, fill="#1f2937", outline="#dfe6e9", width=2)
        canvas.create_text(35.0, 72.0, anchor="w", text=f"Patients Cured: {self.saved_patients}", fill="#55efc4", font=("Helvetica", 11, "bold"))
        held_name = "None"
        if self.held_item:
            held_name = next(tool["name"] for tool in self.tool_catalog if tool["type"] == self.held_item)
        canvas.create_text(35.0, 94.0, anchor="w", text=f"Held Treatment: {held_name}", fill="#ffffff", font=("Helvetica", 10, "bold"))

        if self.message:
            canvas.create_rectangle(280.0, 50.0, WIDTH - 20.0, 94.0, fill="#102a43", outline="#5fb6ff", width=2)
            canvas.create_text(WIDTH / 2, 72.0, text=self.message, fill=TEXT, font=("Helvetica", 10, "bold"), width=WIDTH - 340.0)

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
