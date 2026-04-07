import math
import random
import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import HEIGHT, WIDTH, clamp
from src.worlds.base import BaseWorld


class SoftwareDeveloperWorld(BaseWorld):
    INCIDENT_RADIUS = 56.0
    STATION_RADIUS = 68.0
    PING_RADIUS = 40.0

    def __init__(self) -> None:
        super().__init__(
            name="Software Developer",
            summary="Balance incident triage, implementation, review, and interruptions to ship a stable release.",
            duration=105.0,
        )
        self.briefing = [
            "Stabilize the release by moving tickets from incident to code to review to deploy.",
            "Select a ticket with 1, 2, 3, or 4, then work the matching stage at the correct station.",
            "Urgent incidents and ignored pings drain release health, so route your time deliberately.",
        ]
        self.hints = [
            "Select tickets with 1-4. You are no longer forced down a single path.",
            "SPACE investigates at a service node, C codes at the IDE desk, R reviews at the PR table.",
            "Q clears live pings for a focus boost, but ignoring incidents hurts release health.",
            "After every ticket is merged, hold E at Deploy to ship the release.",
        ]

        self.bounds = (298.0, 118.0, 748.0, HEIGHT - 72.0)
        self.service_positions = [
            (372.0, 176.0),
            (548.0, 164.0),
            (680.0, 248.0),
            (430.0, 314.0),
        ]
        self.workstations = {
            "desk": {"x": 388.0, "y": 438.0, "label": "IDE DESK", "key": "c"},
            "review": {"x": 540.0, "y": 438.0, "label": "PR REVIEW", "key": "r"},
            "deploy": {"x": 684.0, "y": 438.0, "label": "DEPLOY", "key": "e"},
        }
        self.pings = [
            {"x": 328.0, "y": 254.0, "timer": 0.0},
            {"x": 706.0, "y": 154.0, "timer": 0.0},
            {"x": 710.0, "y": 344.0, "timer": 0.0},
        ]

        self.tickets: list[dict[str, Any]] = []
        self.selected_ticket_index = 0
        self.completed_tickets = 0
        self.deploy_progress = 0.0
        self.focus = 100.0
        self.release_health = 100.0
        self.message_timer = 0.0
        self.ping_spawn_timer = 4.5
        self.context_switch_penalty = 0.0
        self.last_action = ""

    def build_ticket_queue(self) -> list[dict[str, Any]]:
        templates = [
            {"name": "Auth token refresh", "service": "Auth API", "severity": "P1", "triage_time": 1.1, "code_time": 2.2, "review_time": 1.2},
            {"name": "Billing retry loop", "service": "Billing Worker", "severity": "P1", "triage_time": 1.0, "code_time": 2.0, "review_time": 1.1},
            {"name": "Search cache eviction", "service": "Search API", "severity": "P2", "triage_time": 1.2, "code_time": 1.9, "review_time": 1.3},
            {"name": "Analytics event dedupe", "service": "Analytics", "severity": "P3", "triage_time": 0.9, "code_time": 1.7, "review_time": 1.0},
        ]
        tickets: list[dict[str, Any]] = []
        for index, template in enumerate(templates):
            x, y = self.service_positions[index]
            tickets.append(
                {
                    "name": template["name"],
                    "service": template["service"],
                    "severity": template["severity"],
                    "triage_time": template["triage_time"],
                    "code_time": template["code_time"],
                    "review_time": template["review_time"],
                    "x": x,
                    "y": y,
                    "stage": "incident",
                    "progress": 0.0,
                    "age": 0.0,
                }
            )
        return tickets

    def reset(self, player: Player) -> None:
        player.reset(332.0, 486.0)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.grade = "-"
        self.message = "Choose a ticket, then balance incidents, coding, review, and pings."
        self.message_timer = 3.0
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.focus = 100.0
        self.release_health = 100.0
        self.completed_tickets = 0
        self.selected_ticket_index = 0
        self.deploy_progress = 0.0
        self.ping_spawn_timer = 4.5
        self.context_switch_penalty = 0.0
        self.last_action = ""
        self.tickets = self.build_ticket_queue()
        for ping in self.pings:
            ping["timer"] = 0.0

    def near(self, player: Player, x: float, y: float, radius: float) -> bool:
        return math.hypot(player.x - x, player.y - y) <= radius

    def selected_ticket(self) -> dict[str, Any] | None:
        if 0 <= self.selected_ticket_index < len(self.tickets):
            return self.tickets[self.selected_ticket_index]
        return None

    def choose_ticket(self, keys: set[str]) -> None:
        for index in range(min(4, len(self.tickets))):
            if str(index + 1) in keys:
                if self.selected_ticket_index != index:
                    self.selected_ticket_index = index
                    ticket = self.tickets[index]
                    self.message = f"Selected {ticket['service']}."
                    self.message_timer = 0.9

    def update_pressure(self, dt: float) -> None:
        open_incidents = 0
        blocked_reviews = 0
        total_age_pressure = 0.0

        for ticket in self.tickets:
            if ticket["stage"] != "done":
                ticket["age"] += dt
                total_age_pressure += max(0.0, float(ticket["age"]) - 4.0)
            if ticket["stage"] == "incident":
                open_incidents += 1
            elif ticket["stage"] == "review":
                blocked_reviews += 1

        severity_pressure = 0.0
        for ticket in self.tickets:
            if ticket["stage"] == "done":
                continue
            if ticket["severity"] == "P1":
                severity_pressure += 1.0
            elif ticket["severity"] == "P2":
                severity_pressure += 0.5
            else:
                severity_pressure += 0.25

        live_pings = sum(1 for ping in self.pings if ping["timer"] > 0.0)
        self.release_health = clamp(
            self.release_health - dt * (open_incidents * 0.55 + blocked_reviews * 0.28 + severity_pressure * 0.24 + total_age_pressure * 0.035 + live_pings * 0.95),
            0.0,
            100.0,
        )
        self.focus = clamp(
            self.focus - dt * (blocked_reviews * 0.22 + self.context_switch_penalty * 0.8 + live_pings * 0.85),
            0.0,
            100.0,
        )
        self.context_switch_penalty = max(0.0, self.context_switch_penalty - dt * 0.8)

    def update_pings(self, dt: float, player: Player, keys: set[str]) -> None:
        self.ping_spawn_timer -= dt
        inactive = [ping for ping in self.pings if ping["timer"] <= 0.0]
        if self.ping_spawn_timer <= 0.0 and inactive:
            ping = random.choice(inactive)
            ping["timer"] = random.uniform(5.0, 8.0)
            self.ping_spawn_timer = random.uniform(4.0, 6.5)

        for ping in self.pings:
            if ping["timer"] <= 0.0:
                continue
            ping["timer"] = max(0.0, ping["timer"] - dt)
            if self.near(player, float(ping["x"]), float(ping["y"]), self.PING_RADIUS) and "q" in keys:
                ping["timer"] = 0.0
                self.focus = clamp(self.focus + 10.0, 0.0, 100.0)
                self.message = "Inbox cleared. Focus recovered."
                self.message_timer = 1.2
            elif ping["timer"] <= 0.0:
                self.release_health = clamp(self.release_health - 5.0, 0.0, 100.0)
                self.message = "A ping escalated into release noise."
                self.message_timer = 1.2

    def work_selected_ticket(self, dt: float, player: Player, keys: set[str]) -> None:
        ticket = self.selected_ticket()
        if ticket is None or ticket["stage"] == "done":
            return

        action_name = ""
        target_key = ""
        target_x = 0.0
        target_y = 0.0
        target_radius = self.STATION_RADIUS
        required_time = 1.0
        next_stage = ""

        if ticket["stage"] == "incident":
            action_name = "triage"
            target_key = "space"
            target_x = float(ticket["x"])
            target_y = float(ticket["y"])
            target_radius = self.INCIDENT_RADIUS
            required_time = float(ticket["triage_time"])
            next_stage = "coding"
        elif ticket["stage"] == "coding":
            action_name = "code"
            target_key = "c"
            target_x = float(self.workstations["desk"]["x"])
            target_y = float(self.workstations["desk"]["y"])
            required_time = float(ticket["code_time"])
            next_stage = "review"
        elif ticket["stage"] == "review":
            action_name = "review"
            target_key = "r"
            target_x = float(self.workstations["review"]["x"])
            target_y = float(self.workstations["review"]["y"])
            required_time = float(ticket["review_time"])
            next_stage = "done"

        engaged = self.near(player, target_x, target_y, target_radius) and target_key in keys
        if not engaged:
            ticket["progress"] = clamp(float(ticket["progress"]) - dt * 15.0, 0.0, 100.0)
            return

        if self.last_action and self.last_action != action_name:
            self.context_switch_penalty = min(8.0, self.context_switch_penalty + 2.0)
        self.last_action = action_name

        speed_scale = 0.88 + max(0.0, self.focus) / 120.0
        ticket["progress"] = clamp(float(ticket["progress"]) + dt / required_time * 100.0 * speed_scale, 0.0, 100.0)
        self.message = f"{action_name.title()} {ticket['service']}..."
        self.message_timer = 0.4

        if ticket["progress"] < 100.0:
            return

        ticket["stage"] = next_stage
        ticket["progress"] = 0.0
        ticket["age"] = 0.0
        self.focus = clamp(self.focus - 3.0, 0.0, 100.0)

        if next_stage == "coding":
            self.message = f"{ticket['service']} understood. Take it to the IDE desk."
        elif next_stage == "review":
            self.message = f"{ticket['service']} implemented. Move to PR review."
        else:
            self.completed_tickets += 1
            self.release_health = clamp(self.release_health + 7.0, 0.0, 100.0)
            self.focus = clamp(self.focus + 4.0, 0.0, 100.0)
            self.message = f"{ticket['service']} merged cleanly."
        self.message_timer = 1.6

    def handle_deploy(self, dt: float, player: Player, keys: set[str]) -> None:
        if self.completed_tickets < len(self.tickets):
            self.deploy_progress = 0.0
            return

        station = self.workstations["deploy"]
        can_deploy = self.near(player, float(station["x"]), float(station["y"]), self.STATION_RADIUS) and "e" in keys
        if not can_deploy:
            self.deploy_progress = clamp(self.deploy_progress - dt * 22.0, 0.0, 100.0)
            return

        self.deploy_progress = clamp(self.deploy_progress + dt * 56.0, 0.0, 100.0)
        self.message = "Running checks and deploying release..."
        self.message_timer = 0.4

        if self.deploy_progress < 100.0:
            return

        self.finished = True
        self.success = self.release_health >= 35.0 and self.focus >= 20.0
        if self.success:
            self.message = "Release shipped cleanly. The board is clear and stable."
            if self.release_health >= 82.0 and self.focus >= 65.0 and self.timer >= 20.0:
                self.grade = "S"
            elif self.release_health >= 68.0 and self.focus >= 50.0:
                self.grade = "A"
            else:
                self.grade = "B"
        else:
            self.grade = "C"
            self.message = "The release shipped, but the system was already strained."

    def evaluate_failure(self) -> None:
        if self.release_health <= 0.0:
            self.finished = True
            self.success = False
            self.grade = "F"
            self.message = "Too many unresolved issues stacked up. Release health collapsed."
        elif self.focus <= 0.0:
            self.finished = True
            self.success = False
            self.grade = "F"
            self.message = "The constant interruptions burned through your focus."
        elif self.timer <= 0.0:
            self.finished = True
            self.success = self.completed_tickets == len(self.tickets) and self.release_health >= 45.0
            if self.success:
                self.grade = "B"
                self.message = "The release window closed, but you shipped just in time."
            else:
                self.grade = "F"
                self.message = "The release window closed before the board was stabilized."

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        if self.pings:
            return ("Priority Alert! Press Q to clear pending system messages.", (player.x, player.y - 40))
        
        if self.selected_ticket_index == -1:
            return ("Check the Terminal for new JIRA tickets.", (140, 110))
            
        ticket = self.tickets[self.selected_ticket_index]
        if ticket["stage"] == "incident":
            return (f"Urgent: Resolve incident {ticket['id']} at the {ticket['node']} node.", (float(ticket["x"]), float(ticket["y"])))
        
        if ticket["stage"] == "coding":
            desk = self.workstations["desk"]
            return (f"Go to the IDE desk to work on {ticket['id']}.", (desk[0], desk[1]))
            
        if ticket["stage"] == "review":
            review = self.workstations["review"]
            return (f"Submit code reviews at the PR station for {ticket['id']}.", (review[0], review[1]))
            
        if self.completed_tickets >= len(self.tickets):
            deploy = self.workstations["deploy"]
            return ("All tickets merged. Head to DEPLOY to finish the release.", (deploy[0], deploy[1]))
            
        return ("Follow the ticket workflow: Code -> Review -> Merge.", None)

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        self.choose_ticket(keys)
        player.update(dt, keys, self.bounds)
        self.update_pressure(dt)
        self.update_pings(dt, player, keys)
        self.work_selected_ticket(dt, player, keys)
        self.handle_deploy(dt, player, keys)
        self.evaluate_failure()
        self.update_particles(dt)
        self.draw(canvas, player)

    def draw_ticket_card(self, canvas: tk.Canvas, index: int, ticket: dict[str, Any]) -> None:
        x = 28
        y = 92 + index * 82
        is_selected = index == self.selected_ticket_index
        done = ticket["stage"] == "done"
        fill = "#101b2a"
        if done:
            fill = "#143126"
        elif is_selected:
            fill = "#1d3550"
        outline = "#f8f8f2" if is_selected else "#35526c"
        canvas.create_rectangle(x, y, x + 244, y + 70, fill=fill, outline=outline, width=2 if is_selected else 1)
        canvas.create_text(x + 12, y + 14, anchor="w", text=f"[{index + 1}]  {ticket['severity']}  {ticket['service']}", fill="#8cd3ff", font=("Helvetica", 10, "bold"))
        canvas.create_text(x + 12, y + 34, anchor="w", text=ticket["name"], fill="#ffffff", font=("Helvetica", 10, "bold"), width=194)
        stage_label = {
            "incident": "Investigate",
            "coding": "Implement",
            "review": "Review",
            "done": "Merged",
        }[str(ticket["stage"])]
        canvas.create_text(x + 12, y + 56, anchor="w", text=stage_label, fill="#ffd166" if not done else "#9df1b5", font=("Helvetica", 10, "bold"))
        if not done:
            canvas.create_rectangle(x + 112, y + 52, x + 228, y + 60, fill="#0a111a", outline="")
            canvas.create_rectangle(x + 112, y + 52, x + 112 + 116 * (float(ticket["progress"]) / 100.0), y + 60, fill="#5fb6ff", outline="")
        canvas.create_text(x + 228, y + 14, anchor="e", text=("Done" if done else f"Age {ticket['age']:0.0f}s"), fill="#9fc0da", font=("Helvetica", 9))

    def draw_station(self, canvas: tk.Canvas, station: dict[str, Any], active: bool) -> None:
        x = float(station["x"])
        y = float(station["y"])
        fill = "#28445e" if active else "#17293a"
        outline = "#ffffff" if active else "#3f627d"
        canvas.create_rectangle(x - 56, y - 34, x + 56, y + 34, fill=fill, outline=outline, width=3 if active else 1)
        canvas.create_text(x, y - 7, text=str(station["label"]), fill="#ffffff", font=("Helvetica", 11, "bold"))
        canvas.create_text(x, y + 14, text=f"HOLD {str(station['key']).upper()}", fill="#a9d6ff", font=("Helvetica", 9, "bold"))

    def draw_metric_bar(self, canvas: tk.Canvas, x: float, y: float, width: float, value: float, label: str, fill: str) -> None:
        canvas.create_text(x, y - 10, anchor="w", text=f"{label}  {int(value)}%", fill="#e7f2fb", font=("Helvetica", 10, "bold"))
        canvas.create_rectangle(x, y, x + width, y + 14, fill="#09111a", outline="#29445c")
        canvas.create_rectangle(x + 2, y + 2, x + 2 + (width - 4) * (value / 100.0), y + 12, fill=fill, outline="")

    def draw_side_panel(self, canvas: tk.Canvas, ticket: dict[str, Any] | None) -> None:
        x1, y1, x2, y2 = 766, 92, 930, 438
        canvas.create_rectangle(x1, y1, x2, y2, fill="#101b2a", outline="#29445c", width=2)
        canvas.create_text(x1 + 14, y1 + 18, anchor="w", text="Release Board", fill="#8cd3ff", font=("Helvetica", 11, "bold"))

        self.draw_metric_bar(canvas, x1 + 14, y1 + 46, x2 - x1 - 28, self.release_health, "Release", "#5fb6ff" if self.release_health > 35 else "#ff5d73")
        self.draw_metric_bar(canvas, x1 + 14, y1 + 88, x2 - x1 - 28, self.focus, "Focus", "#8ce99a" if self.focus > 35 else "#ffb703")
        canvas.create_text(x1 + 14, y1 + 132, anchor="w", text=f"Merged {self.completed_tickets}/{len(self.tickets)}", fill="#ffffff", font=("Helvetica", 11, "bold"))

        canvas.create_text(x1 + 14, y1 + 166, anchor="w", text="Selected Ticket", fill="#8cd3ff", font=("Helvetica", 10, "bold"))
        if ticket is not None:
            stage_text = {
                "incident": "Go to the service node and hold SPACE.",
                "coding": "Go to the IDE desk and hold C.",
                "review": "Go to PR review and hold R.",
                "done": "This ticket is complete.",
            }[str(ticket["stage"])]
            canvas.create_text(x1 + 14, y1 + 192, anchor="nw", text=ticket["name"], fill="#ffffff", font=("Helvetica", 12, "bold"), width=x2 - x1 - 28)
            canvas.create_text(
                x1 + 14,
                y1 + 236,
                anchor="nw",
                text=f"{ticket['severity']}  |  {ticket['service']}\n\n{stage_text}",
                fill="#d8e9f7",
                font=("Helvetica", 10),
                width=x2 - x1 - 28,
            )
            canvas.create_text(x1 + 14, y1 + 304, anchor="w", text=f"Progress {int(ticket['progress'])}%", fill="#ffd166", font=("Helvetica", 10, "bold"))

        canvas.create_text(x1 + 14, y1 + 334, anchor="w", text="Workflow", fill="#8cd3ff", font=("Helvetica", 10, "bold"))
        canvas.create_text(
            x1 + 14,
            y1 + 356,
            anchor="nw",
            text="1-4 select ticket\nSPACE investigate\nC code\nR review\nQ clear ping\nE deploy",
            fill="#d8e9f7",
            font=("Helvetica", 9),
            width=x2 - x1 - 28,
        )

        if self.completed_tickets == len(self.tickets):
            canvas.create_rectangle(x1 + 14, y2 - 28, x2 - 14, y2 - 14, fill="#09111a", outline="#29445c")
            canvas.create_rectangle(x1 + 16, y2 - 26, x1 + 16 + (x2 - x1 - 32) * (self.deploy_progress / 100.0), y2 - 16, fill="#4bd18b", outline="")

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")

        for i in range(7):
            blend = i / 6
            red = int(8 + 10 * blend)
            green = int(14 + 18 * blend)
            blue = int(24 + 30 * blend)
            canvas.create_rectangle(0, i * HEIGHT / 7, WIDTH, (i + 1) * HEIGHT / 7, fill=f"#{red:02x}{green:02x}{blue:02x}", outline="")

        canvas.create_rectangle(18, 52, WIDTH - 18, HEIGHT - 18, fill="#0f1622", outline="#20384d", width=2)
        canvas.create_rectangle(22, 84, 278, HEIGHT - 44, fill="#0e1825", outline="#29445c", width=2)
        canvas.create_rectangle(292, 84, 752, HEIGHT - 44, fill="#0d1520", outline="#29445c", width=2)
        canvas.create_rectangle(766, 84, 934, HEIGHT - 44, fill="#0e1825", outline="#29445c", width=2)

        for x in range(312, 734, 46):
            canvas.create_line(x, 104, x, HEIGHT - 64, fill="#132130")
        for y in range(104, HEIGHT - 62, 34):
            canvas.create_line(312, y, 732, y, fill="#12202d")

        canvas.create_text(38, 68, anchor="w", text="Sprint Queue", fill="#d2e9ff", font=("Helvetica", 13, "bold"))
        canvas.create_text(312, 68, anchor="w", text="Incident Floor", fill="#d2e9ff", font=("Helvetica", 13, "bold"))

        selected = self.selected_ticket()
        for index, ticket in enumerate(self.tickets):
            self.draw_ticket_card(canvas, index, ticket)
            tx = float(ticket["x"])
            ty = float(ticket["y"])
            color = "#ff5d73" if ticket["stage"] == "incident" else "#f6c85f" if ticket["stage"] == "coding" else "#6bc5ff" if ticket["stage"] == "review" else "#4bd18b"
            radius = 32 if index == self.selected_ticket_index else 26
            outline = "#ffffff" if index == self.selected_ticket_index else "#1f2b36"
            canvas.create_oval(tx - radius, ty - radius, tx + radius, ty + radius, fill=color, outline=outline, width=3 if index == self.selected_ticket_index else 1)
            canvas.create_text(tx, ty - 3, text=str(ticket["severity"]), fill="#08111b", font=("Helvetica", 11, "bold"))
            canvas.create_text(tx, ty + 40, text=str(ticket["service"]), fill="#dbeeff", font=("Helvetica", 9, "bold"), width=112)
            if ticket["stage"] != "done":
                canvas.create_rectangle(tx - 28, ty + 52, tx + 28, ty + 60, fill="#0b121a", outline="")
                canvas.create_rectangle(tx - 28, ty + 52, tx - 28 + 56 * (float(ticket["progress"]) / 100.0), ty + 60, fill="#ffffff", outline="")

        self.draw_station(canvas, self.workstations["desk"], selected is not None and selected["stage"] == "coding")
        self.draw_station(canvas, self.workstations["review"], selected is not None and selected["stage"] == "review")
        self.draw_station(canvas, self.workstations["deploy"], self.completed_tickets == len(self.tickets))

        for ping in self.pings:
            if ping["timer"] <= 0.0:
                continue
            pulse = 4.0 * math.sin(float(ping["timer"]) * 7.0)
            px = float(ping["x"])
            py = float(ping["y"])
            canvas.create_oval(px - 20 - pulse, py - 20 - pulse, px + 20 + pulse, py + 20 + pulse, fill="#ff8c42", outline="#fff2d8", width=2)
            canvas.create_text(px, py - 4, text="PING", fill="#08111b", font=("Helvetica", 9, "bold"))
            canvas.create_text(px, py + 11, text="Q", fill="#08111b", font=("Helvetica", 11, "bold"))

        self.draw_side_panel(canvas, selected)

        if self.message_timer > 0.0 and self.message:
            canvas.create_rectangle(308, HEIGHT - 74, 744, HEIGHT - 46, fill="#132234", outline="#2f5675")
            canvas.create_text(WIDTH / 2, HEIGHT - 60, text=self.message, fill="#ffffff", font=("Helvetica", 10, "bold"), width=392)

        player.draw(canvas)

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
