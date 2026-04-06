import math
import random
import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import HEIGHT, WIDTH, clamp
from src.worlds.base import BaseWorld


class SoftwareDeveloperWorld(BaseWorld):
    INCIDENT_RADIUS = 56.0
    STATION_RADIUS = 70.0

    def __init__(self) -> None:
        super().__init__(
            name="Software Developer",
            summary="Triage production incidents, implement fixes, and ship a stable release.",
            duration=95.0,
        )
        self.briefing = [
            "RELEASE NIGHT: Production services are unstable and the sprint board is stacked with urgent tickets.",
            "Each ticket must move through a workflow: investigate the incident, then implement the fix.",
            "Stand at the highlighted location and hold the matching key to complete the current step.",
            "Open incidents and random pings drain focus quickly if you ignore them.",
            "Clear the sprint board, then deploy from the console before the shift ends.",
        ]
        self.hints = [
            "Investigate at the service node with SPACE, then code at the desk with C.",
            "Focus on high-priority tickets sequentially; avoid jumping around.",
            "Aging tickets and unresolved pings drain your focus.",
            "After all tickets are implemented, deploy the release at the console with E.",
        ]
        self.bounds = (40.0, 64.0, WIDTH - 40.0, HEIGHT - 48.0)
        self.service_positions = [
            (120.0, 220.0), # Auth (Top Left)
            (480.0, 210.0), # Billing (Top Center)
            (840.0, 220.0), # Search (Top Right)
        ]
        self.tickets: list[dict[str, Any]] = []
        self.workstations = {
            "desk": {"x": 150.0, "y": 480.0, "label": "IDE DESK", "key": "c"},
            "deploy": {"x": 810.0, "y": 480.0, "label": "DEPLOY", "key": "e"},
        }
        self.pings = [
            {"x": 100.0, "y": 280.0, "timer": 0.0},
            {"x": 300.0, "y": 240.0, "timer": 0.0},
            {"x": 500.0, "y": 260.0, "timer": 0.0},
            {"x": 700.0, "y": 240.0, "timer": 0.0},
            {"x": 860.0, "y": 280.0, "timer": 0.0},
            {"x": 480.0, "y": 400.0, "timer": 0.0},
            {"x": 300.0, "y": 520.0, "timer": 0.0},
            {"x": 660.0, "y": 520.0, "timer": 0.0},
            {"x": 480.0, "y": 560.0, "timer": 0.0},
            {"x": 300.0, "y": 180.0, "timer": 0.0},
            {"x": 660.0, "y": 180.0, "timer": 0.0},
            {"x": 100.0, "y": 180.0, "timer": 0.0}, # Top Left Corner
            {"x": 860.0, "y": 180.0, "timer": 0.0}, # Top Right Corner
            {"x": 100.0, "y": 560.0, "timer": 0.0}, # Bottom Left Corner
            {"x": 860.0, "y": 560.0, "timer": 0.0}, # Bottom Right Corner
            {"x": 480.0, "y": 180.0, "timer": 0.0}, # Center Top
            {"x": 200.0, "y": 380.0, "timer": 0.0}, # Left Mid
            {"x": 760.0, "y": 380.0, "timer": 0.0}, # Right Mid
            {"x": 50.0, "y": 320.0, "timer": 0.0},  # Edges
            {"x": 910.0, "y": 320.0, "timer": 0.0}, # Edges
            {"x": 400.0, "y": 480.0, "timer": 0.0}, # Filling gaps
            {"x": 560.0, "y": 480.0, "timer": 0.0}, # Filling gaps
        ]

        self.focus = 100.0
        self.completed_tickets = 0
        self.current_ticket_index = 0
        self.deploy_progress = 0.0
        self.message_timer = 0.0
        self.ping_spawn_timer = 5.0
        self.context_switch_penalty = 0.0
        self.last_action = ""

    def build_ticket_queue(self) -> list[dict[str, Any]]:
        templates = [
            {"name": "Auth token refresh", "service": "Auth API", "severity": "P1", "triage_time": 1.1, "code_time": 2.3},
            {"name": "Billing retry loop", "service": "Billing Worker", "severity": "P1", "triage_time": 1.0, "code_time": 2.1},
            {"name": "Search cache eviction", "service": "Search API", "severity": "P2", "triage_time": 1.2, "code_time": 2.0},
        ]
        queue: list[dict[str, Any]] = []
        for index, template in enumerate(templates):
            x, y = self.service_positions[index]
            queue.append(
                {
                    "name": template["name"],
                    "service": template["service"],
                    "severity": template["severity"],
                    "triage_time": template["triage_time"],
                    "code_time": template["code_time"],
                    "x": x,
                    "y": y,
                    "stage": "incident",
                    "progress": 0.0,
                    "age": 0.0,
                }
            )
        return queue

    def reset(self, player: Player) -> None:
        player.reset(110.0, 480.0)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.grade = "-"
        self.message = "Work the queue in order: investigate, code, then deploy."
        self.message_timer = 3.0
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.shake = 0.0
        self.particles = []
        self.focus = 100.0
        self.completed_tickets = 0
        self.current_ticket_index = 0
        self.deploy_progress = 0.0
        self.ping_spawn_timer = 4.0
        self.context_switch_penalty = 0.0
        self.last_action = ""
        self.tickets = self.build_ticket_queue()
        for ping in self.pings:
            ping["timer"] = 0.0

    def active_ticket(self) -> dict[str, Any] | None:
        if 0 <= self.current_ticket_index < len(self.tickets):
            return self.tickets[self.current_ticket_index]
        return None

    def near(self, player: Player, x: float, y: float, radius: float) -> bool:
        return math.hypot(player.x - x, player.y - y) <= radius

    def decay_focus_and_health(self, dt: float) -> None:
        open_incidents = 0
        for index, ticket in enumerate(self.tickets):
            if ticket["stage"] != "done":
                ticket["age"] += dt
            if ticket["stage"] == "incident":
                open_incidents += 1
            if index < self.current_ticket_index and ticket["stage"] != "done":
                self.focus = clamp(self.focus - dt * 5.0, 0.0, 100.0)
                self.message = "Skipped priority work; focus is waning."
                self.message_timer = 0.5

        age_pressure = sum(max(0.0, ticket["age"] - 4.0) for ticket in self.tickets if ticket["stage"] != "done")
        ping_pressure = sum(1 for ping in self.pings if ping["timer"] > 0.0)
        self.focus = clamp(self.focus - dt * (open_incidents * 0.35 + ping_pressure * 1.0 + self.context_switch_penalty * 0.55 + age_pressure * 0.02), 0.0, 100.0)
        self.context_switch_penalty = max(0.0, self.context_switch_penalty - dt * 0.8)

    def update_pings(self, dt: float, player: Player, keys: set[str]) -> None:
        self.ping_spawn_timer -= dt
        inactive = [ping for ping in self.pings if ping["timer"] <= 0.0]
        if self.ping_spawn_timer <= 0.0 and inactive:
            ping = random.choice(inactive)
            ping["timer"] = random.uniform(6.0, 9.0)
            self.ping_spawn_timer = random.uniform(1.8, 3.2)

        q_pressed = "q" in keys or "Q" in keys
        for ping in self.pings:
            if ping["timer"] <= 0.0:
                continue
            ping["timer"] = max(0.0, ping["timer"] - dt)
            if self.near(player, float(ping["x"]), float(ping["y"]), 52.0) and q_pressed:
                ping["timer"] = 0.0
                self.focus = clamp(self.focus + 12.0, 0.0, 100.0)
                self.message = "Q key: Inbox cleared! Focus restored."
                self.message_timer = 1.4
                self.shake = 1.5
            elif ping["timer"] <= 0.0:
                self.focus = clamp(self.focus - 8.0, 0.0, 100.0)
                self.message = "A ping escalated! Focus lost."
                self.message_timer = 1.5

    def work_ticket(self, dt: float, player: Player, keys: set[str]) -> None:
        ticket = self.active_ticket()
        if not ticket:
            return

        target_key = ""
        target_x = 0.0
        target_y = 0.0
        target_radius = self.STATION_RADIUS
        required_time = 1.0
        next_stage = ""
        action_name = ""

        if ticket["stage"] == "incident":
            target_key = "space"
            target_x = float(ticket["x"])
            target_y = float(ticket["y"])
            target_radius = self.INCIDENT_RADIUS
            required_time = float(ticket["triage_time"])
            next_stage = "coding"
            action_name = "triage"
        elif ticket["stage"] == "coding":
            target_key = "c"
            target_x = float(self.workstations["desk"]["x"])
            target_y = float(self.workstations["desk"]["y"])
            required_time = float(ticket["code_time"])
            next_stage = "done"
            action_name = "code"
        else:
            return

        engaged = self.near(player, target_x, target_y, target_radius) and target_key in keys
        if engaged:
            if self.last_action and self.last_action != action_name:
                self.context_switch_penalty = min(8.0, self.context_switch_penalty + 2.2)
            self.last_action = action_name
            speed_scale = 1.0 + max(0.0, self.focus - 50.0) / 120.0
            ticket["progress"] = clamp(float(ticket["progress"]) + dt / required_time * 100.0 * speed_scale, 0.0, 100.0)
            self.message = f"{action_name.title()} {ticket['service']}..."
            self.message_timer = 0.5
            if ticket["progress"] >= 100.0:
                ticket["stage"] = next_stage
                ticket["progress"] = 0.0
                ticket["age"] = 0.0
                self.focus = clamp(self.focus - 4.0, 0.0, 100.0)
                if next_stage == "coding":
                    self.message = f"Incident understood. Move to the desk and press C to implement {ticket['name']}."
                else:
                    self.completed_tickets += 1
                    self.current_ticket_index += 1
                    self.focus = clamp(self.focus + 3.0, 0.0, 100.0)
                    self.message = f"{ticket['service']} is merged. Next ticket is up."
                self.message_timer = 2.0
        else:
            ticket["progress"] = clamp(float(ticket["progress"]) - dt * 18.0, 0.0, 100.0)

    def handle_deploy(self, dt: float, player: Player, keys: set[str]) -> None:
        if self.current_ticket_index < len(self.tickets):
            self.deploy_progress = 0.0
            return
        deploy_station = self.workstations["deploy"]
        can_deploy = self.near(player, float(deploy_station["x"]), float(deploy_station["y"]), self.STATION_RADIUS) and "e" in keys
        if not can_deploy:
            self.deploy_progress = clamp(self.deploy_progress - dt * 25.0, 0.0, 100.0)
            return
        self.deploy_progress = clamp(self.deploy_progress + dt * 60.0, 0.0, 100.0)
        self.message = "Running final checks and deploying release..."
        self.message_timer = 0.4
        if self.deploy_progress >= 100.0:
            self.finished = True
            complete = self.completed_tickets >= len(self.tickets)
            self.success = complete and self.focus >= 30.0
            if self.success:
                self.message = "Release shipped smoothly. The sprint board is empty."
                self.grade = self.calculate_grade()
            else:
                self.grade = "C"
                self.message = "The build shipped but focus or completion was lacking."

    def evaluate_failure(self) -> None:
        if self.focus <= 0.0:
            self.finished = True
            self.success = False
            self.grade = "F"
            self.message = "Context switching and constant pings burned out the whole shift."
        elif self.timer <= 0.0:
            self.finished = True
            reviewed = sum(1 for ticket in self.tickets if ticket["stage"] == "done")
            self.success = reviewed == len(self.tickets) and self.focus >= 25.0
            if self.success:
                self.message = f"Shift ended with {reviewed}/{len(self.tickets)} tickets merged."
                self.grade = self.calculate_grade()
            else:
                self.grade = "F"
                self.message = "The release train missed the window."

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        player.update(dt, keys, self.bounds)
        self.decay_focus_and_health(dt)
        self.update_pings(dt, player, keys)
        self.work_ticket(dt, player, keys)
        self.handle_deploy(dt, player, keys)
        self.evaluate_failure()
        self.update_particles(dt)
        self.draw(canvas, player)

    def draw_ticket_card(self, canvas: tk.Canvas, index: int, ticket: dict[str, Any]) -> None:
        x = 32 + index * 180
        y = 64
        active = index == self.current_ticket_index
        done = ticket["stage"] == "done"
        fill = "#102030"
        if done:
            fill = "#16372d"
        elif active:
            fill = "#20344d"
        outline = "#f8f8f2" if active else "#35526c"
        canvas.create_rectangle(x, y, x + 160, y + 92, fill=fill, outline=outline, width=2 if active else 1)
        canvas.create_text(x + 10, y + 14, anchor="w", text=f"{ticket['severity']}  {ticket['service']}", fill="#8cd3ff", font=("Courier", 10, "bold"))
        canvas.create_text(x + 10, y + 38, anchor="w", text=ticket["name"], fill="#ffffff", font=("Courier", 9), width=138)
        stage_label = {
            "incident": "Investigate",
            "coding": "Implement",
            "done": "Merged",
        }[str(ticket["stage"])]
        canvas.create_text(x + 10, y + 70, anchor="w", text=stage_label, fill="#ffd166" if not done else "#9df1b5", font=("Courier", 10, "bold"))
        if not done:
            canvas.create_rectangle(x + 10, y + 78, x + 150, y + 86, fill="#0a111a", outline="")
            canvas.create_rectangle(x + 10, y + 78, x + 10 + 140 * (float(ticket["progress"]) / 100.0), y + 86, fill="#5fb6ff", outline="")

    def draw_station(self, canvas: tk.Canvas, station: dict[str, Any], active: bool) -> None:
        x = float(station["x"])
        y = float(station["y"])
        fill = "#28445e" if active else "#17293a"
        outline = "#ffffff" if active else "#3f627d"
        canvas.create_rectangle(x - 64, y - 42, x + 64, y + 42, fill=fill, outline=outline, width=3 if active else 1)
        canvas.create_text(x, y - 8, text=str(station["label"]), fill="#ffffff", font=("Courier", 12, "bold"))
        canvas.create_text(x, y + 16, text=f"HOLD {str(station['key']).upper()}", fill="#a9d6ff", font=("Courier", 10))

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")

        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#0a0f18", outline="")
        canvas.create_rectangle(18, 52, WIDTH - 18, HEIGHT - 18, fill="#0f1622", outline="#20384d", width=2)
        for x in range(30, WIDTH, 48):
            canvas.create_line(x, 52, x, HEIGHT - 18, fill="#121f2c")
        for y in range(52, HEIGHT, 36):
            canvas.create_line(18, y, WIDTH - 18, y, fill="#101b27")

        active_t = self.active_ticket()
        for index, ticket in enumerate(self.tickets):
            self.draw_ticket_card(canvas, index, ticket)
            tx, ty = float(ticket["x"]), float(ticket["y"])
            color = "#ff5d73" if ticket["stage"] == "incident" else "#f6c85f" if ticket["stage"] == "coding" else "#4bd18b"
            radius = 34 if index == self.current_ticket_index else 28
            outline = "#ffffff" if index == self.current_ticket_index else "#1f2b36"
            canvas.create_oval(tx - radius, ty - radius, tx + radius, ty + radius, fill=color, outline=outline, width=3 if index == self.current_ticket_index else 1)
            canvas.create_text(tx, ty - 4, text=str(ticket["service"]), fill="#ffffff", font=("Courier", 9, "bold"))
            canvas.create_text(tx, ty + 14, text=str(ticket["severity"]), fill="#08111b", font=("Courier", 11, "bold"))
            if ticket["stage"] != "done":
                canvas.create_rectangle(tx - 28, ty + 40, tx + 28, ty + 48, fill="#0b121a", outline="")
                canvas.create_rectangle(tx - 28, ty + 40, tx - 28 + 56 * (float(ticket["progress"]) / 100.0), ty + 48, fill="#ffffff", outline="")

        desk_active = active_t is not None and active_t["stage"] == "coding"
        deploy_active = active_t is None
        self.draw_station(canvas, self.workstations["desk"], desk_active)
        self.draw_station(canvas, self.workstations["deploy"], deploy_active)

        if active_t is None:
            bx, by = 380, 500
            canvas.create_rectangle(bx, by, bx + 200, by + 10, fill="#09111b", outline="#20384d")
            canvas.create_rectangle(bx, by, bx + 200 * (self.deploy_progress / 100.0), by + 10, fill="#4bd18b", outline="")

        for ping in self.pings:
            if ping["timer"] <= 0.0:
                continue
            px, py = float(ping["x"]), float(ping["y"])
            pulse = 6.0 * math.sin(ping["timer"] * 7.0)
            canvas.create_oval(px - 22 - pulse, py - 22 - pulse, px + 22 + pulse, py + 22 + pulse, fill="#ff8c42", outline="#fff2d8", width=2)
            canvas.create_text(px, py - 4, text="PING", fill="#08111b", font=("Courier", 10, "bold"))
            canvas.create_text(px, py + 12, text="Q", fill="#08111b", font=("Courier", 12, "bold"))

        canvas.create_rectangle(32, 520, 292, 540, fill="#0a111a", outline="")
        canvas.create_rectangle(34, 522, 34 + 256 * (self.focus / 100.0), 538, fill="#8ce99a" if self.focus > 35 else "#ffb703", outline="")
        canvas.create_text(162, 506, text=f"FOCUS {int(self.focus)}%", fill="#ffffff", font=("Courier", 12, "bold"))

        canvas.create_text(770, 36, text=f"Tickets merged: {self.completed_tickets}/{len(self.tickets)}", fill="#d2e9ff", font=("Courier", 12, "bold"))

        if self.message_timer > 0.0 and self.message:
            canvas.create_rectangle(206, HEIGHT - 78, WIDTH - 206, HEIGHT - 48, fill="#132234", outline="#2f5675")
            canvas.create_text(WIDTH / 2, HEIGHT - 63, text=self.message, fill="#ffffff", font=("Courier", 10, "bold"), width=520)

        player.draw(canvas)

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
