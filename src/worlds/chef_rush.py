import random
import math
import time
import tkinter as tk
from ..utils import WIDTH, HEIGHT, TEXT, clamp
from ..player import Player
from .base import BaseWorld

class ChefRushWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Chef Rush",
            summary="Assemble dishes in the right order while dodging kitchen chaos",
            duration=30.0,
        )
        self.bounds = (110.0, 100.0, WIDTH - 110.0, HEIGHT - 90.0)
        self.stations: list[dict[str, float | str]] = []
        self.recipe: list[str] = []
        self.step = 0
        self.step_progress = 0.0
        self.spills: list[dict[str, float]] = []
        self.tickets: list[dict[str, float]] = []
        self.ticket_spawn = 9.0
        self.warning = ""

    def reset(self, player: Player, difficulty: int = 0) -> None:
        player.reset(WIDTH / 2, HEIGHT - 90)
        # Scaled Duration: Less time per level
        self.timer = max(15.0, self.duration - (difficulty * 2.0))
        self.finished = False
        self.success = False
        self.message = ""
        self.step = 0
        self.step_progress = 0.0
        self.tickets = []
        self.ticket_spawn = max(4.0, 8.0 - (difficulty * 0.3))
        self.warning = ""
        self.recipe = random.choice(
            [
                ["Knife Skills", "Sear Protein", "Deglaze", "Plate"],
                ["Chop Veggies", "Simmer Sauce", "Season", "Plating"],
                ["Prep Dough", "Bake", "Glaze", "Garnish"],
            ]
        )
        self.stations = [
            {"name": "Knife Skills", "x": 140, "y": 180, "color": "#ffc857"},
            {"name": "Sear Protein", "x": WIDTH - 160, "y": 200, "color": "#ff7f51"},
            {"name": "Deglaze", "x": WIDTH / 2, "y": 140, "color": "#6dd3ff"},
            {"name": "Plate", "x": WIDTH / 2, "y": 320, "color": "#8bcf88"},
            {"name": "Chop Veggies", "x": 150, "y": HEIGHT - 160, "color": "#7ae07a"},
            {"name": "Simmer Sauce", "x": WIDTH - 160, "y": HEIGHT - 150, "color": "#ff9f1c"},
            {"name": "Season", "x": WIDTH / 2 + 40, "y": 230, "color": "#d6cdea"},
            {"name": "Plating", "x": WIDTH / 2 - 30, "y": HEIGHT - 220, "color": "#f5f5dc"},
            {"name": "Prep Dough", "x": WIDTH / 2 - 120, "y": 110, "color": "#d9b08c"},
            {"name": "Bake", "x": WIDTH - 200, "y": 120, "color": "#ff7b72"},
            {"name": "Glaze", "x": 200, "y": 110, "color": "#9ed0ff"},
            {"name": "Garnish", "x": WIDTH / 2, "y": HEIGHT - 130, "color": "#a7e3a1"},
        ]
        self.spills = []
        for _ in range(4):
            self.spills.append(
                {
                    "x": random.randint(200, WIDTH - 200),
                    "y": random.randint(160, HEIGHT - 160),
                    "dx": random.choice([-1, 1]) * random.uniform(60, 120),
                    "dy": random.choice([-1, 1]) * random.uniform(60, 120),
                    "r": random.randint(24, 34),
                }
            )

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        x1, y1, x2, y2 = self.bounds
        player.update(dt, keys, self.bounds)
        for spill in self.spills:
            spill["x"] += spill["dx"] * dt
            spill["y"] += spill["dy"] * dt
            if spill["x"] < x1 + 20 or spill["x"] > x2 - 20:
                spill["dx"] *= -1
            if spill["y"] < y1 + 20 or spill["y"] > y2 - 20:
                spill["dy"] *= -1
            if math.hypot(player.x - spill["x"], player.y - spill["y"]) < player.size + spill["r"]:
                self.timer = max(0.0, self.timer - dt * 4)
                player.speed = 180.0
                break
        else:
            player.speed = 240.0
        if self.step < len(self.recipe):
            active_step = self.recipe[self.step]
            on_station = False
            for station in self.stations:
                if station["name"] != active_step:
                    continue
                if math.hypot(player.x - station["x"], player.y - station["y"]) < player.size + 26:
                    on_station = True
                    break
            if on_station:
                self.step_progress = clamp(self.step_progress + dt * 1.4, 0.0, 1.0)
            else:
                self.step_progress = clamp(self.step_progress - dt * 0.6, 0.0, 1.0)
            if self.step_progress >= 0.99:
                self.step += 1
                self.step_progress = 0.0
                player.speed = 240.0
                self.timer = min(self.duration + 4, self.timer + 3.0)
        self.warning = ""
        for station in self.stations:
            if self.step < len(self.recipe) and station["name"] == self.recipe[self.step]:
                continue
            if math.hypot(player.x - station["x"], player.y - station["y"]) < player.size + 10:
                self.timer = max(0.0, self.timer - dt * 1)
                self.warning = "Wrong Station!"
        if self.step >= len(self.recipe):
            self.finished = True
            self.success = True
            self.message = "Dish up! You finished every station in order."
        # Expedite tickets at the pass
        self.ticket_spawn -= dt
        if self.ticket_spawn <= 0:
            self.ticket_spawn = random.uniform(7.0, 11.0)
            self.tickets.append({"ttl": 7.5})
        window = (x2 - 170, y1 - 10, x2 - 30, y1 + 50)
        if self.tickets and window[0] <= player.x <= window[2] and window[1] <= player.y <= window[3]:
            self.tickets.pop(0)
            self.timer = min(self.duration + 5, self.timer + 4.0)
        remaining_tickets = []
        for ticket in self.tickets:
            ticket["ttl"] -= dt
            if ticket["ttl"] <= 0:
                self.timer = max(0.0, self.timer - 6.0)
            else:
                remaining_tickets.append(ticket)
        self.tickets = remaining_tickets
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        x1, y1, x2, y2 = self.bounds
        for i in range(6):
            shade = 22 + i * 6
            canvas.create_rectangle(
                0,
                i * (HEIGHT / 6),
                WIDTH,
                (i + 1) * (HEIGHT / 6),
                fill=f"#{shade:02x}{(shade+12):02x}{(shade+20):02x}",
                outline="",
            )
        canvas.create_rectangle(x1 - 30, y1 - 30, x2 + 30, y2 + 30, fill="#1f2a30", outline="#3e5560", width=4)
        canvas.create_rectangle(x1, y1, x2, y2, fill="#2f333b", outline="#54606b", width=3)
        tile = 36
        for xi in range(int(x1), int(x2), tile):
            for yi in range(int(y1), int(y2), tile):
                color = "#363b45" if (xi // tile + yi // tile) % 2 == 0 else "#2b2f38"
                canvas.create_rectangle(xi, yi, xi + tile, yi + tile, fill=color, outline="")
        canvas.create_rectangle(x1, y1 - 24, x2, y1, fill="#10151b", outline="#526673", width=2)
        canvas.create_text(WIDTH / 2, y1 - 12, text="Michelin-night prep. Keep the line moving!", fill="#ffd280", font=("Helvetica", 13, "bold"))
        window = (x2 - 170, y1 - 10, x2 - 30, y1 + 50)
        canvas.create_rectangle(window[0], window[1], window[2], window[3], fill="#0f1922", outline="#72c2ff", width=3)
        canvas.create_text(window[0] + 12, window[1] - 12, anchor="w", text="Pass / Expedite", fill="#b7e9ff", font=("Helvetica", 10, "bold"))
        canvas.create_rectangle(x1 + 10, y2 + 8, x2 - 10, y2 + 36, fill="#1a2228", outline="#475560", width=2)
        current_index = min(self.step, len(self.recipe) - 1)
        active_step = self.recipe[current_index] if self.recipe else ""
        canvas.create_text(
            (x1 + x2) / 2,
            y2 + 22,
            text=" -> ".join([step if i != current_index else f"[{step}]" for i, step in enumerate(self.recipe)]),
            fill="#fefefe",
            font=("Helvetica", 12, "bold"),
        )
        canvas.create_text(
            20,
            HEIGHT - 80,
            anchor="w",
            text="Hold on the highlighted station to finish prep; clear expedite tickets at the pass; wrong stations and spills drain your clock.",
            fill=TEXT,
            font=("Helvetica", 11),
        )
        for station in self.stations:
            outline = "#f8f8f0" if station["name"] == active_step else "#121212"
            canvas.create_oval(
                station["x"] - 32,
                station["y"] - 32,
                station["x"] + 32,
                station["y"] + 32,
                fill="#0f1218",
                outline="#1f242d",
                width=3,
            )
            canvas.create_oval(
                station["x"] - 26,
                station["y"] - 26,
                station["x"] + 26,
                station["y"] + 26,
                fill=station["color"],
                outline=outline,
                width=3,
            )
            if station["name"] == active_step:
                canvas.create_oval(
                    station["x"] - 40,
                    station["y"] - 40,
                    station["x"] + 40,
                    station["y"] + 40,
                    outline="#fefefe",
                    width=2,
                    dash=(4, 4),
                )
                steam_y = station["y"] - 50 + math.sin(time.time() * 3) * 4
                canvas.create_oval(station["x"] - 10, steam_y, station["x"] + 10, steam_y + 20, fill="#f0f8ff", outline="#c2d8ff", width=1)
            canvas.create_text(station["x"], station["y"] - 38, text=station["name"], fill=TEXT, font=("Helvetica", 9, "bold"))
            if station["name"] == active_step and self.step < len(self.recipe):
                bar = self.step_progress
                canvas.create_rectangle(station["x"] - 30, station["y"] + 34, station["x"] + 30, station["y"] + 44, outline="#fefefe", width=2)
                canvas.create_rectangle(station["x"] - 28, station["y"] + 36, station["x"] - 28 + 56 * bar, station["y"] + 42, fill="#ffd280", outline="")
        for spill in self.spills:
            canvas.create_oval(
                spill["x"] - spill["r"] - 3,
                spill["y"] - spill["r"] - 3,
                spill["x"] + spill["r"] + 3,
                spill["y"] + spill["r"] + 3,
                fill="#1c2b4a",
                outline="",
            )
            canvas.create_oval(
                spill["x"] - spill["r"],
                spill["y"] - spill["r"],
                spill["x"] + spill["r"],
                spill["y"] + spill["r"],
                fill="#4f73ff",
                outline="#98b6ff",
                width=2,
            )
        if self.tickets:
            canvas.create_text(window[2] - 10, window[1] + 18, anchor="e", text=f"Tickets: {len(self.tickets)}", fill="#e8f6ff", font=("Helvetica", 10, "bold"))
            ttl_bar = clamp(self.tickets[0]["ttl"] / 7.5, 0.0, 1.0)
            canvas.create_rectangle(window[0] + 10, window[3] + 8, window[2] - 10, window[3] + 16, outline="#72c2ff", width=2)
            canvas.create_rectangle(window[0] + 12, window[3] + 10, window[0] + 12 + (window[2] - window[0] - 24) * ttl_bar, window[3] + 14, fill="#ffd166", outline="")
        if self.warning:
            canvas.create_text(WIDTH / 2, HEIGHT / 2 + 60, text=self.warning, fill="#ff4d4d", font=("Helvetica", 16, "bold"))
        canvas.create_rectangle(x1 - 10, y1 - 10, x2 + 10, y2 + 10, outline="#6a7c88", width=2)
        player.draw(canvas)
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
