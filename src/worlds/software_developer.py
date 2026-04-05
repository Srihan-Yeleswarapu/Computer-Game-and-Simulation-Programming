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
            summary="Triage production incidents, implement fixes, get review approval, and ship a stable release.",
            duration=65.0,
        )
        self.briefing = [
            "RELEASE NIGHT: Production services are unstable and the sprint board is stacked with urgent tickets.",
            "Each ticket must move through a realistic workflow: investigate the incident, implement the fix, then request review.",
            "Stand at the highlighted location and hold the matching key to complete the current step.",
            "Open incidents, stale review queues, and random pings all chip away at release health if you ignore them.",
            "Clear the sprint board, then deploy from the release console before the shift ends.",
        ]
        self.hints = [
            "Investigate at the service node with SPACE, then code at the desk with C.",
            "Take reviewed work to the PR station and hold R to merge it cleanly.",
            "Aging tickets and unresolved pings drain release health and developer focus.",
            "After all tickets are reviewed, deploy the release at the console with E.",
        ]
        self.bounds = (40.0, 64.0, WIDTH - 40.0, HEIGHT - 48.0)
        self.service_positions = [
            (150.0, 170.0),
            (335.0, 150.0),
            (520.0, 182.0),
            (705.0, 150.0),
            (810.0, 250.0),
        ]
        self.tickets: list[dict[str, Any]] = []
        self.workstations = {
            "desk": {"x": 320.0, "y": 410.0, "label": "IDE DESK", "key": "c"},
            "review": {"x": 625.0, "y": 410.0, "label": "PR REVIEW", "key": "r"},
            "deploy": {"x": 810.0, "y": 500.0, "label": "DEPLOY", "key": "e"},
        }
        self.pings = [
            {"x": 185.0, "y": 500.0, "timer": 0.0},
            {"x": 130.0, "y": 350.0, "timer": 0.0},
            {"x": 840.0, "y": 355.0, "timer": 0.0},
        ]
        self.release_health = 100.0
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
            {"name": "Auth token refresh", "service": "Auth API", "severity": "P1", "triage_time": 1.1, "code_time": 2.3, "review_time": 1.3},
            {"name": "Billing retry loop", "service": "Billing Worker", "severity": "P1", "triage_time": 1.0, "code_time": 2.1, "review_time": 1.2},
            {"name": "Search cache eviction", "service": "Search API", "severity": "P2", "triage_time": 1.2, "code_time": 2.0, "review_time": 1.4},
            {"name": "Notification webhook lag", "service": "Notifications", "severity": "P2", "triage_time": 1.0, "code_time": 2.2, "review_time": 1.3},
            {"name": "Analytics event dedupe", "service": "Analytics", "severity": "P3", "triage_time": 1.1, "code_time": 1.9, "review_time": 1.1},
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
                    "review_time": template["review_time"],
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
        self.message = "Work the queue in order: investigate, code, review, then deploy."
        self.message_timer = 3.0
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.shake = 0.0
        self.particles = []
        self.release_health = 100.0
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
        blocked_reviews = 0
        for index, ticket in enumerate(self.tickets):
            if ticket["stage"] != "done":
                ticket["age"] += dt
            if ticket["stage"] == "incident":
                open_incidents += 1
            elif ticket["stage"] == "review":
                blocked_reviews += 1
            if index < self.current_ticket_index and ticket["stage"] != "done":
                self.release_health = clamp(self.release_health - dt * 8.0, 0.0, 100.0)
                self.focus = clamp(self.focus - dt * 6.5, 0.0, 100.0)
                self.message = "You skipped priority work. Release health is dropping."
                self.message_timer = 0.5

        age_pressure = sum(max(0.0, ticket["age"] - 4.0) for ticket in self.tickets if ticket["stage"] != "done")
        ping_pressure = sum(1 for ping in self.pings if ping["timer"] > 0.0)
        self.release_health = clamp(self.release_health - dt * (open_incidents * 0.45 + blocked_reviews * 0.3 + age_pressure * 0.03 + ping_pressure * 0.9), 0.0, 100.0)
        self.focus = clamp(self.focus - dt * (blocked_reviews * 0.25 + ping_pressure * 1.15 + self.context_switch_penalty * 0.55), 0.0, 100.0)
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
            if self.near(player, float(ping["x"]), float(ping["y"]), 46.0) and "q" in keys:
                ping["timer"] = 0.0
                self.focus = clamp(self.focus + 10.0, 0.0, 100.0)
                self.message = "Inbox cleared. You bought yourself some focus."
                self.message_timer = 1.4
            elif ping["timer"] <= 0.0:
                self.release_health = clamp(self.release_health - 5.0, 0.0, 100.0)
                self.message = "A ping escalated because nobody answered it."
                self.message_timer = 1.5

    def work_ticket(self, dt: float, player: Player, keys: set[str]) -> None:
        ticket = self.active_ticket()
        if ticket is None:
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
            next_stage = "review"
            action_name = "code"
        elif ticket["stage"] == "review":
            target_key = "r"
            target_x = float(self.workstations["review"]["x"])
            target_y = float(self.workstations["review"]["y"])
            required_time = float(ticket["review_time"])
            next_stage = "done"
            action_name = "review"
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
                elif next_stage == "review":
                    self.message = f"Fix ready. Take it to review and hold R for approval."
                else:
                    self.completed_tickets += 1
                    self.current_ticket_index += 1
                    self.release_health = clamp(self.release_health + 6.0, 0.0, 100.0)
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
            self.success = self.release_health >= 35.0
            if self.success:
                self.message = "Release shipped cleanly. Incidents are stable and the sprint board is empty."
                if self.release_health >= 82.0 and self.focus >= 65.0 and self.timer >= 18.0:
                    self.grade = "S"
                elif self.release_health >= 68.0 and self.timer >= 10.0:
                    self.grade = "A"
                else:
                    self.grade = "B"
            else:
                self.grade = "C"
                self.message = "The build shipped, but the release health was already in bad shape."

    def evaluate_failure(self) -> None:
        if self.release_health <= 0.0:
            self.finished = True
            self.success = False
            self.grade = "F"
            self.message = "Production spiraled before you could stabilize the release."
        elif self.focus <= 0.0:
            self.finished = True
            self.success = False
            self.grade = "F"
            self.message = "Context switching and constant pings burned out the whole shift."
        elif self.timer <= 0.0:
            self.finished = True
            reviewed = sum(1 for ticket in self.tickets if ticket["stage"] == "done")
            self.success = reviewed >= 4 and self.release_health >= 45.0
            if self.success:
                self.message = f"Shift ended with {reviewed}/{len(self.tickets)} tickets merged and the release still standing."
                self.grade = "B" if reviewed == len(self.tickets) else "C"
            else:
                self.grade = "F"
                self.message = "The release train missed the window."

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
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
            "review": "Review",
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

        active_ticket = self.active_ticket()
        for index, ticket in enumerate(self.tickets):
            self.draw_ticket_card(canvas, index, ticket)
            color = "#ff5d73" if ticket["stage"] == "incident" else "#f6c85f" if ticket["stage"] == "coding" else "#6bc5ff" if ticket["stage"] == "review" else "#4bd18b"
            radius = 34 if index == self.current_ticket_index else 28
            outline = "#ffffff" if index == self.current_ticket_index else "#1f2b36"
            canvas.create_oval(float(ticket["x"]) - radius, float(ticket["y"]) - radius, float(ticket["x"]) + radius, float(ticket["y"]) + radius, fill=color, outline=outline, width=3 if index == self.current_ticket_index else 1)
            canvas.create_text(float(ticket["x"]), float(ticket["y"]) - 4, text=str(ticket["service"]), fill="#ffffff", font=("Courier", 9, "bold"))
            canvas.create_text(float(ticket["x"]), float(ticket["y"]) + 14, text=str(ticket["severity"]), fill="#08111b", font=("Courier", 11, "bold"))
            if ticket["stage"] != "done":
                canvas.create_rectangle(float(ticket["x"]) - 28, float(ticket["y"]) + 40, float(ticket["x"]) + 28, float(ticket["y"]) + 48, fill="#0b121a", outline="")
                canvas.create_rectangle(float(ticket["x"]) - 28, float(ticket["y"]) + 40, float(ticket["x"]) - 28 + 56 * (float(ticket["progress"]) / 100.0), float(ticket["y"]) + 48, fill="#ffffff", outline="")

        desk_active = active_ticket is not None and active_ticket["stage"] == "coding"
        review_active = active_ticket is not None and active_ticket["stage"] == "review"
        deploy_active = active_ticket is None
        self.draw_station(canvas, self.workstations["desk"], desk_active)
        self.draw_station(canvas, self.workstations["review"], review_active)
        self.draw_station(canvas, self.workstations["deploy"], deploy_active)

        if active_ticket is None:
            canvas.create_rectangle(730, 548, 890, 558, fill="#09111b", outline="")
            canvas.create_rectangle(730, 548, 730 + 160 * (self.deploy_progress / 100.0), 558, fill="#4bd18b", outline="")

        for ping in self.pings:
            if ping["timer"] <= 0.0:
                continue
            pulse = 6.0 * math.sin(ping["timer"] * 7.0)
            canvas.create_oval(float(ping["x"]) - 22 - pulse, float(ping["y"]) - 22 - pulse, float(ping["x"]) + 22 + pulse, float(ping["y"]) + 22 + pulse, fill="#ff8c42", outline="#fff2d8", width=2)
            canvas.create_text(float(ping["x"]), float(ping["y"]) - 4, text="PING", fill="#08111b", font=("Courier", 10, "bold"))
            canvas.create_text(float(ping["x"]), float(ping["y"]) + 12, text="Q", fill="#08111b", font=("Courier", 12, "bold"))

        canvas.create_rectangle(32, 520, 292, 540, fill="#0a111a", outline="")
        canvas.create_rectangle(34, 522, 34 + 256 * (self.release_health / 100.0), 538, fill="#5fb6ff" if self.release_health > 35 else "#ff5d73", outline="")
        canvas.create_text(162, 506, text=f"RELEASE HEALTH {int(self.release_health)}%", fill="#ffffff", font=("Courier", 12, "bold"))

        canvas.create_rectangle(332, 520, 592, 540, fill="#0a111a", outline="")
        canvas.create_rectangle(334, 522, 334 + 256 * (self.focus / 100.0), 538, fill="#8ce99a" if self.focus > 35 else "#ffb703", outline="")
        canvas.create_text(462, 506, text=f"FOCUS {int(self.focus)}%", fill="#ffffff", font=("Courier", 12, "bold"))

        canvas.create_text(770, 36, text=f"Tickets merged: {self.completed_tickets}/{len(self.tickets)}", fill="#d2e9ff", font=("Courier", 12, "bold"))

        if self.message_timer > 0.0 and self.message:
            canvas.create_rectangle(206, HEIGHT - 78, WIDTH - 206, HEIGHT - 48, fill="#132234", outline="#2f5675")
            canvas.create_text(WIDTH / 2, HEIGHT - 63, text=self.message, fill="#ffffff", font=("Courier", 10, "bold"), width=520)

        player.draw(canvas)

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
