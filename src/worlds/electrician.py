import math
import random
import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import HEIGHT, WIDTH, clamp
from src.worlds.base import BaseWorld


class ElectricianWorld(BaseWorld):
    TOP_BAR_H = 42
    FOOTER_H = 28
    LOWER_PANEL_H = 130
    SIDE_PANEL_W = 250
    BOARD_LEFT = 18
    BOARD_TOP = 58
    BOARD_RIGHT = WIDTH - SIDE_PANEL_W - 18
    BOARD_BOTTOM = HEIGHT - LOWER_PANEL_H - FOOTER_H

    def __init__(self) -> None:
        super().__init__(
            name="Electrician",
            summary="Diagnose overloaded circuits, isolate the right panel, repair faults, and restore the building safely.",
            duration=105.0,
        )
        self.briefing = [
            "RESTORE power by repairing all circuit faults.",
            "ISOLATE circuits at the breaker panel (1-3) before repairing.",
            "HOLD R near a fault to repair it safely.",
            "ENERGIZE (E) at the main panel to restore the building."
        ]
        self.hints = [
            "Move with WASD or arrows. Stand near a fault and press SPACE to inspect it.",
            "Press 1, 2, or 3 at the breaker panel to toggle the matching circuit group.",
            "Hold R at a fault to repair it after isolating the correct group.",
            "Hold E at the main panel to re-energize repaired circuits and restore building load.",
        ]
        self.groups = [
            {"id": "lighting", "label": "Lighting", "color": "#ffd166"},
            {"id": "sockets", "label": "Sockets", "color": "#74c0fc"},
            {"id": "hvac", "label": "HVAC", "color": "#63e6be"},
        ]
        self.fault_templates = [
            {"name": "Lobby lighting short", "group": "lighting", "symptom": "Breaker trips when lobby lights surge.", "severity": 16.0, "repair_time": 2.8},
            {"name": "Kitchen receptacle fault", "group": "sockets", "symptom": "GFCI loop is arcing under appliance load.", "severity": 18.0, "repair_time": 3.2},
            {"name": "Roof condenser disconnect", "group": "hvac", "symptom": "Outdoor unit is drawing uneven current.", "severity": 20.0, "repair_time": 3.4},
            {"name": "Conference strip overload", "group": "sockets", "symptom": "Power strips are overheating on one branch.", "severity": 14.0, "repair_time": 2.5},
            {"name": "Hall emergency lights", "group": "lighting", "symptom": "Transfer path is flickering during test cycle.", "severity": 17.0, "repair_time": 2.9},
            {"name": "Air handler relay chatter", "group": "hvac", "symptom": "Control relay is cycling rapidly under demand.", "severity": 19.0, "repair_time": 3.5},
        ]
        self.breaker_panel = {"x": self.BOARD_LEFT + 78.0, "y": self.BOARD_BOTTOM - 66.0}
        self.main_panel = {"x": self.BOARD_RIGHT - 70.0, "y": self.BOARD_BOTTOM - 66.0}
        self.fault_positions = [
            (self.BOARD_LEFT + 180.0, self.BOARD_TOP + 72.0),
            (self.BOARD_LEFT + 390.0, self.BOARD_TOP + 54.0),
            (self.BOARD_LEFT + 570.0, self.BOARD_TOP + 84.0),
            (self.BOARD_LEFT + 230.0, self.BOARD_TOP + 210.0),
            (self.BOARD_LEFT + 455.0, self.BOARD_TOP + 214.0),
            (self.BOARD_LEFT + 650.0, self.BOARD_TOP + 205.0),
        ]
        self.bounds = (self.BOARD_LEFT, self.BOARD_TOP, self.BOARD_RIGHT, self.BOARD_BOTTOM)
        self.faults: list[dict[str, Any]] = []
        self.breaker_states: dict[str, bool] = {}
        self.power_by_group: dict[str, float] = {}
        self.system_health = 100.0
        self.restore_progress = 0.0
        self.inspected_fault = -1
        self.active_repair_fault = -1
        self.message_timer = 0.0

    def reset(self, player: Player) -> None:
        player.reset(self.BOARD_LEFT + 60.0, self.BOARD_BOTTOM - 42.0)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.grade = "-"
        self.message = "Inspect the faults, isolate the right circuit, and repair safely."
        self.message_timer = 3.0
        self.shake = 0.0
        self.particles = []
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.system_health = 100.0
        self.restore_progress = 0.0
        self.inspected_fault = -1
        self.active_repair_fault = -1
        self.breaker_states = {group["id"]: True for group in self.groups}
        self.power_by_group = {group["id"]: 100.0 for group in self.groups}
        templates = random.sample(self.fault_templates, 5)
        self.faults = []
        for index, template in enumerate(templates):
            x, y = self.fault_positions[index]
            self.faults.append(
                {
                    "name": template["name"],
                    "group": template["group"],
                    "symptom": template["symptom"],
                    "severity": template["severity"],
                    "repair_time": template["repair_time"],
                    "repair_progress": 0.0,
                    "state": "fault",
                    "x": x,
                    "y": y,
                }
            )

    def nearest_fault(self, player: Player, radius: float = 65.0) -> int:
        best_index = -1
        best_dist = radius
        for index, fault in enumerate(self.faults):
            dist = math.hypot(player.x - float(fault["x"]), player.y - float(fault["y"]))
            if dist < best_dist:
                best_dist = dist
                best_index = index
        return best_index

    def near_panel(self, player: Player, target: dict[str, float], radius: float = 70.0) -> bool:
        return math.hypot(player.x - target["x"], player.y - target["y"]) < radius

    def inspect_fault(self, player: Player, keys: set[str]) -> None:
        if not self.just_pressed(keys, "space"):
            return
        fault_index = self.nearest_fault(player)
        if fault_index >= 0:
            self.inspected_fault = fault_index
            self.message = f"Inspected: {self.faults[fault_index]['name']}."
            self.message_timer = 2.0

    def handle_breakers(self, player: Player, keys: set[str]) -> None:
        if not self.near_panel(player, self.breaker_panel):
            return
        for key, group in zip(("1", "2", "3"), self.groups):
            if self.just_pressed(keys, key):
                state = self.breaker_states[group["id"]]
                self.breaker_states[group["id"]] = not state
                status = "OPEN" if not state else "ISOLATED"
                self.message = f"{group['label']} breaker set to {status}."
                self.message_timer = 1.2

    def handle_repairs(self, dt: float, player: Player, keys: set[str]) -> None:
        if "r" not in keys:
            self.active_repair_fault = -1
            return
        fault_index = self.nearest_fault(player)
        if fault_index < 0:
            self.active_repair_fault = -1
            return
        fault = self.faults[fault_index]
        if fault["state"] != "fault":
            return
        self.active_repair_fault = fault_index
        isolated = not self.breaker_states[fault["group"]]
        if not isolated:
            self.system_health = clamp(self.system_health - dt * (12.0 + float(fault["severity"]) * 0.35), 0.0, 100.0)
            self.shake = max(self.shake, 1.5)
            self.message = f"Danger: {fault['name']} is still live. Isolate {fault['group']} first."
            self.message_timer = 0.6
            return
        fault["repair_progress"] = clamp(float(fault["repair_progress"]) + dt / float(fault["repair_time"]) * 100.0, 0.0, 100.0)
        self.message = f"Repairing {fault['name']}..."
        self.message_timer = 0.6
        if float(fault["repair_progress"]) >= 100.0:
            fault["state"] = "repaired"
            self.message = f"Repair complete: {fault['name']}."
            self.message_timer = 1.8

    def handle_restore(self, dt: float, player: Player, keys: set[str]) -> None:
        if "e" not in keys or not self.near_panel(player, self.main_panel):
            self.restore_progress = 0.0
            return
        repaired_groups = {fault["group"] for fault in self.faults if fault["state"] == "repaired"}
        if not repaired_groups:
            self.message = "No repaired circuits ready to re-energize."
            self.message_timer = 0.8
            return
        self.restore_progress = clamp(self.restore_progress + dt * 70.0, 0.0, 100.0)
        self.message = "Re-energizing repaired circuits..."
        self.message_timer = 0.6
        if self.restore_progress >= 100.0:
            for fault in self.faults:
                if fault["state"] == "repaired":
                    fault["state"] = "online"
            self.restore_progress = 0.0
            self.message = "All repaired circuits are NOW ONLINE."
            self.message_timer = 2.0

    def update_fault_effects(self, dt: float) -> None:
        overload = 0.0
        for fault in self.faults:
            if fault["state"] == "fault":
                self.power_by_group[fault["group"]] = clamp(self.power_by_group[fault["group"]] - dt * float(fault["severity"]) * 0.14, 0.0, 100.0)
                overload += float(fault["severity"]) * 0.05
            elif fault["state"] == "online":
                self.power_by_group[fault["group"]] = clamp(self.power_by_group[fault["group"]] + dt * 7.0, 0.0, 100.0)
        if overload > 0.0:
            self.system_health = clamp(self.system_health - dt * overload, 0.0, 100.0)

    def evaluate_outcome(self) -> None:
        online_count = sum(1 for fault in self.faults if fault["state"] == "online")
        if online_count == len(self.faults) and self.system_health >= 15.0:
            self.finished = True
            self.success = True
            self.message = "Building stabilized! All circuits re-energized successfully."
            # Grade based more on quality and speed
            if self.system_health >= 90.0:
                self.grade = "S"
            elif self.system_health >= 75.0 and self.timer >= 15.0:
                self.grade = "S"
            elif self.system_health >= 60.0 or self.timer >= 35.0:
                self.grade = "A"
            else:
                self.grade = "B"
        elif self.system_health <= 0.0:
            self.finished = True
            self.success = False
            self.grade = "F"
            self.message = "Critical fault escalation. The service panel failed under unsafe repair attempts."
        elif self.timer <= 0.0:
            self.finished = True
            restored_ratio = online_count / max(1, len(self.faults))
            self.success = restored_ratio >= 0.6 and self.system_health >= 25.0
            if self.success:
                self.message = f"Shift ended with {online_count}/{len(self.faults)} circuits restored."
                if restored_ratio >= 1.0:
                    self.grade = "A"
                elif restored_ratio >= 0.8:
                    self.grade = "B"
                else:
                    self.grade = "C"
            else:
                self.grade = "F"
                self.message = "Building failed safety inspections or was not fully restored."

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        unrepaired = [f for f in self.faults if f["state"] == "fault"]
        if not unrepaired:
            ready = any(f["state"] == "repaired" for f in self.faults)
            if ready:
                return ("Repairs done! Hold E at the Main Panel to energize the building.", (float(self.main_panel["x"]), float(self.main_panel["y"])))
            return ("All circuits stabilized. Monitor system health until end of shift.", None)
            
        # Target the nearest fault
        fault = min(unrepaired, key=lambda f: math.hypot(player.x - float(f["x"]), player.y - float(f["y"])))
        target_pos = (float(fault["x"]), float(fault["y"]))
        
        # Check if isolated
        if self.breaker_states[fault["group"]]:
            # Not isolated
            return (f"Isolate {fault['group'].title()} at the Breaker Panel before fixing {fault['name']}.", (float(self.breaker_panel["x"]), float(self.breaker_panel["y"])))
            
        return (f"Hold R to repair the isolated {fault['name']} safely.", target_pos)

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        player.update(dt, keys, self.bounds)
        self.inspect_fault(player, keys)
        self.handle_breakers(player, keys)
        self.handle_repairs(dt, player, keys)
        self.handle_restore(dt, player, keys)
        self.update_fault_effects(dt)
        self.evaluate_outcome()
        self.update_particles(dt)
        self.draw(canvas, player)

    def draw_background(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101821", outline="")
        canvas.create_rectangle(self.BOARD_LEFT, self.BOARD_TOP, self.BOARD_RIGHT, self.BOARD_BOTTOM, fill="#162431", outline="#2d4d67", width=2)
        canvas.create_rectangle(self.BOARD_RIGHT + 10, self.BOARD_TOP, WIDTH - 18, self.BOARD_BOTTOM, fill="#0d1822", outline="#2d4d67", width=2)
        canvas.create_rectangle(0, HEIGHT - self.LOWER_PANEL_H - self.FOOTER_H, WIDTH, HEIGHT - self.FOOTER_H, fill="#0b141d", outline="#2d4d67")

    def draw_top_bar(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, 0, WIDTH, self.TOP_BAR_H, fill="#08111b", outline="")
        canvas.create_text(14, 21, anchor="w", text="Electrician", fill="#eef7ff", font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, 21, text=f"System Health {int(self.system_health)}%", fill="#9bd1ff", font=("Helvetica", 11, "bold"))
        canvas.create_text(WIDTH - 16, 21, anchor="e", text=f"Time {self.timer:05.1f}s", fill="#eef7ff", font=("Helvetica", 12, "bold"))

    def draw_footer(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, HEIGHT - self.FOOTER_H, WIDTH, HEIGHT, fill="#08111b", outline="")
        canvas.create_text(WIDTH / 2, HEIGHT - self.FOOTER_H / 2, text=self.hints[self.current_hint_index], fill="#8ec7ec", font=("Helvetica", 10, "italic"), width=WIDTH - 80)

    def draw_fault_network(self, canvas: tk.Canvas) -> None:
        for fault in self.faults:
            panel_color = "#ff6b6b" if fault["state"] == "fault" else "#ffd166" if fault["state"] == "repaired" else "#63e6be"
            canvas.create_rectangle(fault["x"] - 30, fault["y"] - 20, fault["x"] + 30, fault["y"] + 20, fill=panel_color, outline="#ffffff", width=2)
            canvas.create_text(fault["x"], fault["y"] - 32, text=fault["group"].upper(), fill="#dcecff", font=("Helvetica", 8, "bold"))
            canvas.create_text(fault["x"], fault["y"], text="FAULT" if fault["state"] == "fault" else "READY" if fault["state"] == "repaired" else "ON", fill="#102030", font=("Helvetica", 9, "bold"))
            if fault["state"] == "fault":
                progress = float(fault["repair_progress"]) / 100.0
                canvas.create_rectangle(fault["x"] - 28, fault["y"] + 27, fault["x"] + 28, fault["y"] + 34, fill="#223546", outline="")
                canvas.create_rectangle(fault["x"] - 28, fault["y"] + 27, fault["x"] - 28 + 56 * progress, fault["y"] + 34, fill="#4dabf7", outline="")

        for group in self.groups:
            group_faults = [fault for fault in self.faults if fault["group"] == group["id"]]
            if not group_faults:
                continue
            source_x = self.breaker_panel["x"]
            source_y = self.breaker_panel["y"]
            for fault in group_faults:
                energized = self.breaker_states[group["id"]] and fault["state"] == "online"
                line_color = group["color"] if energized else "#3c4f60"
                canvas.create_line(source_x, source_y, fault["x"], fault["y"], fill=line_color, width=3, dash=(4, 3) if not energized else ())

        canvas.create_rectangle(self.breaker_panel["x"] - 38, self.breaker_panel["y"] - 52, self.breaker_panel["x"] + 38, self.breaker_panel["y"] + 52, fill="#1f3344", outline="#8ec7ec", width=2)
        canvas.create_text(self.breaker_panel["x"], self.breaker_panel["y"] - 64, text="Breaker Panel", fill="#dcecff", font=("Helvetica", 10, "bold"))
        for index, group in enumerate(self.groups):
            y = self.breaker_panel["y"] - 24 + index * 24
            state = self.breaker_states[group["id"]]
            fill = group["color"] if state else "#495866"
            canvas.create_rectangle(self.breaker_panel["x"] - 26, y - 8, self.breaker_panel["x"] + 26, y + 8, fill=fill, outline="#ffffff")
            canvas.create_text(self.breaker_panel["x"], y, text=f"[{index+1}] {group['label'][0]}", fill="#102030", font=("Helvetica", 8, "bold"))

        canvas.create_rectangle(self.main_panel["x"] - 42, self.main_panel["y"] - 44, self.main_panel["x"] + 42, self.main_panel["y"] + 44, fill="#243647", outline="#8ec7ec", width=2)
        canvas.create_text(self.main_panel["x"], self.main_panel["y"] - 54, text="Main Panel", fill="#dcecff", font=("Helvetica", 10, "bold"))
        canvas.create_text(self.main_panel["x"], self.main_panel["y"] - 6, text="Hold E", fill="#ffffff", font=("Helvetica", 9, "bold"))
        canvas.create_rectangle(self.main_panel["x"] - 28, self.main_panel["y"] + 10, self.main_panel["x"] + 28, self.main_panel["y"] + 20, fill="#162431", outline="")
        canvas.create_rectangle(self.main_panel["x"] - 28, self.main_panel["y"] + 10, self.main_panel["x"] - 28 + 56 * (self.restore_progress / 100.0), self.main_panel["y"] + 20, fill="#63e6be", outline="")

    def draw_status_panels(self, canvas: tk.Canvas) -> None:
        y1 = HEIGHT - self.LOWER_PANEL_H - self.FOOTER_H
        cards = [
            ("Lighting", f"{int(self.power_by_group['lighting'])}%", "#ffd166"),
            ("Sockets", f"{int(self.power_by_group['sockets'])}%", "#74c0fc"),
            ("HVAC", f"{int(self.power_by_group['hvac'])}%", "#63e6be"),
            ("Restored", f"{sum(1 for fault in self.faults if fault['state'] == 'online')}/{len(self.faults)}", "#f8f9fa"),
        ]
        for index, (label, value, color) in enumerate(cards):
            x1 = 18 + index * 180
            x2 = x1 + 164
            canvas.create_rectangle(x1, y1 + 14, x2, y1 + 60, fill="#122131", outline="#33526a")
            canvas.create_text(x1 + 12, y1 + 28, anchor="w", text=label, fill="#9bc0da", font=("Helvetica", 9, "bold"))
            canvas.create_text(x1 + 12, y1 + 47, anchor="w", text=value, fill=color, font=("Helvetica", 12, "bold"))
        canvas.create_rectangle(18, y1 + 72, WIDTH - 18, HEIGHT - self.FOOTER_H - 10, fill="#101a27", outline="#2d4d67")
        has_repaired = any(fault["state"] == "repaired" for fault in self.faults)
        if self.message_timer > 0.0:
            status = self.message
        elif has_repaired:
            status = ">> REPAIRS COMPLETE. RETURN TO MAIN PANEL TO RE-ENERGIZE <<"
        else:
            status = "Inspect, isolate, repair, then re-energize."
        canvas.create_text(30, y1 + 89, anchor="w", text=status, fill="#ffd166" if has_repaired else "#e5f3ff", font=("Helvetica", 10, "bold"), width=WIDTH - 70)

    def draw_sidebar(self, canvas: tk.Canvas) -> None:
        x1 = self.BOARD_RIGHT + 10
        x2 = WIDTH - 18
        y = self.BOARD_TOP + 12
        canvas.create_text(x1 + 14, y, anchor="nw", text="Inspection", fill="#eef7ff", font=("Helvetica", 12, "bold"))
        y += 28
        if 0 <= self.inspected_fault < len(self.faults):
            fault = self.faults[self.inspected_fault]
            details = [
                fault["name"],
                f"Group: {fault['group'].title()}",
                fault["symptom"],
                f"Repair State: {fault['state'].title()}",
                f"Repair Time: {fault['repair_time']:.1f}s",
            ]
        else:
            details = ["Inspect a fault with SPACE.", "The sidebar will show the fault group and symptoms.", "", "", ""]
        for line in details:
            canvas.create_text(x1 + 14, y, anchor="nw", text=line, fill="#dcecff", font=("Helvetica", 9), width=self.SIDE_PANEL_W - 28)
            y += 20
        y += 10
        canvas.create_text(x1 + 14, y, anchor="nw", text="Controls", fill="#ffd166", font=("Helvetica", 11, "bold"))
        y += 22
        controls = [
            "SPACE inspect fault",
            "1/2/3 toggle breakers",
            "Hold R repair fault",
            "Hold E restore service",
        ]
        for line in controls:
            canvas.create_text(x1 + 14, y, anchor="nw", text=line, fill="#dcecff", font=("Helvetica", 9), width=self.SIDE_PANEL_W - 28)
            y += 18
        y += 12
        canvas.create_text(x1 + 14, y, anchor="nw", text="Fault Queue", fill="#ffd166", font=("Helvetica", 11, "bold"))
        y += 22
        for fault in self.faults:
            label = f"{fault['name']} [{fault['state']}]"
            canvas.create_text(x1 + 14, y, anchor="nw", text=label, fill="#dcecff", font=("Helvetica", 9), width=self.SIDE_PANEL_W - 28)
            y += 18

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        self.draw_background(canvas)
        self.draw_top_bar(canvas)
        self.draw_fault_network(canvas)
        player.draw(canvas)
        self.draw_sidebar(canvas)
        self.draw_status_panels(canvas)
        self.draw_footer(canvas)
        if self.finished:
            self.draw_result(canvas)
