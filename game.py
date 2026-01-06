import math
import random
import time
import tkinter as tk


WIDTH, HEIGHT = 960, 600
BG = "#0f1326"
TEXT = "#f5f6f7"


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class Player:
    def __init__(self) -> None:
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.size = 22
        self.speed = 260.0
        self.vx = 0.0
        self.vy = 0.0
        self.accel = 12.0

    def reset(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

    def update(self, dt: float, keys: set[str], bounds: tuple[float, float, float, float]) -> None:
        dx = (1 if "Right" in keys or "d" in keys else 0) - (
            1 if "Left" in keys or "a" in keys else 0
        )
        dy = (1 if "Down" in keys or "s" in keys else 0) - (
            1 if "Up" in keys or "w" in keys else 0
        )
        if dx or dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
        target_vx = dx * self.speed
        target_vy = dy * self.speed
        smooth = clamp(self.accel * dt, 0.0, 1.0)
        self.vx = lerp(self.vx, target_vx, smooth)
        self.vy = lerp(self.vy, target_vy, smooth)
        self.x += self.vx * dt
        self.y += self.vy * dt
        x1, y1, x2, y2 = bounds
        self.x = clamp(self.x, x1 + self.size, x2 - self.size)
        self.y = clamp(self.y, y1 + self.size, y2 - self.size)

    def draw(self, canvas: tk.Canvas) -> None:
        canvas.create_oval(
            self.x - self.size - 4,
            self.y - self.size + 6,
            self.x + self.size + 4,
            self.y + self.size + 8,
            fill="#0a2235",
            outline="",
        )
        canvas.create_rectangle(
            self.x - self.size,
            self.y - self.size,
            self.x + self.size,
            self.y + self.size,
            fill="#61dafb",
            outline="#0d8db6",
            width=2,
        )


class BaseWorld:
    def __init__(self, name: str, summary: str, duration: float) -> None:
        self.name = name
        self.summary = summary
        self.duration = duration
        self.timer = duration
        self.finished = False
        self.success = False
        self.message = ""
        self.bounds: tuple[float, float, float, float] = (0.0, 0.0, WIDTH, HEIGHT)

    def reset(self, player: Player) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def tick_timer(self, dt: float) -> None:
        if self.finished:
            return
        self.timer = max(0.0, self.timer - dt)
        if self.timer <= 0.0:
            self.finished = True
            self.success = False
            self.message = "Time ran out!"

    def draw_hud(self, canvas: tk.Canvas) -> None:
        canvas.create_text(
            20,
            20,
            anchor="w",
            fill=TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"{self.name}   |   {self.summary}",
        )
        canvas.create_text(
            WIDTH - 20,
            20,
            anchor="e",
            fill=TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"Time: {self.timer:05.1f}s",
        )


class FireRescueWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Firefighter Rescue",
            summary="Navigate smoke, dodge flames, and carry survivors out",
            duration=48.0,
        )
        self.bounds = (80.0, 60.0, WIDTH - 40.0, HEIGHT - 60.0)
        self.survivors: list[dict[str, float | str]] = []
        self.flames: list[dict[str, float]] = []
        self.smoke: list[dict[str, float]] = []
        self.carrying: dict[str, float | str] | None = None
        self.saved = 0
        self.heat = 0.0
        self.spread_cap = 12

    def reset(self, player: Player) -> None:
        start_x = self.bounds[0] + 30
        player.reset(start_x, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.saved = 0
        self.heat = 0.0
        self.carrying = None
        self.survivors = [
            {
                "x": random.randint(int(self.bounds[0] + 140), int(self.bounds[2] - 80)),
                "y": random.randint(int(self.bounds[1] + 60), int(self.bounds[3] - 60)),
                "state": "trapped",
                "progress": 0.0,
            }
            for _ in range(5)
        ]
        self.flames = []
        for _ in range(7):
            self.flames.append(
                {
                    "x": random.randint(int(self.bounds[0] + 80), int(self.bounds[2] - 40)),
                    "y": random.randint(int(self.bounds[1] + 40), int(self.bounds[3] - 40)),
                    "dx": random.choice([-1, 1]) * random.uniform(60, 110),
                    "dy": random.choice([-1, 1]) * random.uniform(50, 100),
                    "r": random.randint(20, 30),
                    "spread": random.uniform(6.0, 11.0),
                }
            )
        self.smoke = [
            {
                "x": random.uniform(self.bounds[0], self.bounds[2]),
                "y": random.uniform(self.bounds[1], self.bounds[3]),
                "r": random.uniform(32, 55),
                "rise": random.uniform(6, 18),
            }
            for _ in range(10)
        ]

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        x1, y1, x2, y2 = self.bounds
        player.update(dt, keys, self.bounds)
        for flame in self.flames:
            flame["x"] += flame["dx"] * dt
            flame["y"] += flame["dy"] * dt
            if flame["x"] < x1 + 10 or flame["x"] > x2 - 20:
                flame["dx"] *= -1
            if flame["y"] < y1 + 10 or flame["y"] > y2 - 10:
                flame["dy"] *= -1
            flame["spread"] -= dt
            if flame["spread"] <= 0 and len(self.flames) < self.spread_cap:
                flame["spread"] = random.uniform(7.0, 11.0)
                new_r = clamp(flame["r"] + random.uniform(-4, 6), 14, 34)
                self.flames.append(
                    {
                        "x": clamp(flame["x"] + random.uniform(-30, 30), x1 + 20, x2 - 20),
                        "y": clamp(flame["y"] + random.uniform(-30, 30), y1 + 20, y2 - 20),
                        "dx": random.choice([-1, 1]) * random.uniform(70, 120),
                        "dy": random.choice([-1, 1]) * random.uniform(60, 110),
                        "r": new_r,
                        "spread": random.uniform(7.0, 11.0),
                    }
                )
        for puff in self.smoke:
            puff["y"] -= puff["rise"] * dt
            puff["x"] += math.sin(puff["y"] * 0.08) * 10 * dt
            if puff["y"] < y1 - 40:
                puff["y"] = y2 + random.uniform(10, 40)
                puff["x"] = random.uniform(x1, x2)
        # Survivor handling: pick up, carry, and evacuate to the door
        door_zone = (80, HEIGHT / 2 - 50, 220, HEIGHT / 2 + 50)
        if not self.carrying:
            for survivor in self.survivors:
                dist = math.hypot(player.x - survivor["x"], player.y - survivor["y"])
                if survivor["state"] == "trapped" and dist < player.size + 16:
                    survivor["state"] = "freeing"
                if survivor["state"] == "freeing":
                    survivor["progress"] = clamp(survivor.get("progress", 0.0) + dt * 1.4, 0.0, 1.0)
                    if survivor["progress"] >= 0.99:
                        survivor["state"] = "freed"
                elif survivor["state"] == "freed" and dist < player.size + 14:
                    survivor["state"] = "carried"
                    self.carrying = survivor
                    break
                else:
                    survivor["progress"] = clamp(survivor.get("progress", 0.0) - dt * 0.5, 0.0, 1.0)
        if self.carrying:
            self.carrying["x"] = lerp(self.carrying["x"], player.x + 14, clamp(dt * 8, 0, 1))
            self.carrying["y"] = lerp(self.carrying["y"], player.y - 28, clamp(dt * 8, 0, 1))
            if door_zone[0] <= player.x <= door_zone[2] and door_zone[1] <= player.y <= door_zone[3]:
                self.carrying["state"] = "saved"
                self.saved += 1
                self.carrying = None
        if door_zone[0] <= player.x <= door_zone[2] and door_zone[1] <= player.y <= door_zone[3]:
            for survivor in self.survivors:
                if survivor["state"] == "freed":
                    survivor["state"] = "saved"
                    self.saved += 1
        self.survivors = [s for s in self.survivors if s["state"] != "saved"]
        for flame in self.flames:
            if math.hypot(player.x - flame["x"], player.y - flame["y"]) < player.size + flame["r"]:
                self.heat += dt * 35
                self.timer = max(0.0, self.timer - dt * 3)
                if self.heat > 40:
                    player.reset(self.bounds[0] + 20, HEIGHT / 2)
                    self.heat = 0.0
        if self.saved >= 5:
            self.finished = True
            self.success = True
            self.message = "All survivors are safe! You cleared the building."
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        x1, y1, x2, y2 = self.bounds
        for i in range(6):
            shade = 20 + i * 6
            canvas.create_rectangle(
                0,
                i * (HEIGHT / 6),
                WIDTH,
                (i + 1) * (HEIGHT / 6),
                fill=f"#{shade:02x}{shade:02x}{(shade+12):02x}",
                outline="",
            )
        canvas.create_rectangle(x1 - 40, y1 - 30, x2 + 20, y2 + 20, fill="#1d2433", outline="#3a4a66", width=4)
        canvas.create_rectangle(x1, y1, x2, y2, fill="#2f3544", outline="#4d5569", width=3)
        for i in range(int((x2 - x1) // 40)):
            xi = x1 + i * 40
            canvas.create_line(xi, y1, xi, y2, fill="#3e4457", dash=(4, 6))
        for i in range(int((y2 - y1) // 40)):
            yi = y1 + i * 40
            canvas.create_line(x1, yi, x2, yi, fill="#3e4457", dash=(6, 6))
        canvas.create_rectangle(80, HEIGHT / 2 - 40, 200, HEIGHT / 2 + 40, fill="#c24747", outline="#d97e7e", width=3)
        canvas.create_polygon(200, HEIGHT / 2 - 30, 220, HEIGHT / 2, 200, HEIGHT / 2 + 30, fill="#ffd166", outline="#ffb703", width=3)
        canvas.create_text(120, HEIGHT / 2 - 55, anchor="w", fill="#ffdd99", font=("Helvetica", 13, "bold"), text="Crew door")
        for puff in self.smoke:
            canvas.create_oval(
                puff["x"] - puff["r"],
                puff["y"] - puff["r"],
                puff["x"] + puff["r"],
                puff["y"] + puff["r"],
                fill="#4f596d",
                outline="#6d768a",
                width=1,
            )
        for flame in self.flames:
            flicker = random.randint(-6, 6)
            r = flame["r"] + flicker * 0.15
            canvas.create_oval(
                flame["x"] - r,
                flame["y"] - r,
                flame["x"] + r,
                flame["y"] + r,
                fill="#ff5f45",
                outline="#ffbd45",
                width=2,
            )
            canvas.create_arc(
                flame["x"] - r,
                flame["y"] - r,
                flame["x"] + r,
                flame["y"] + r,
                start=200,
                extent=140,
                fill="",
                outline="#ffe0a3",
                style="arc",
                width=2,
            )
        for survivor in self.survivors:
            sx = survivor["x"]
            sy = survivor["y"]
            color = "#f7d08a" if survivor["state"] == "trapped" else "#9ef3b2" if survivor["state"] == "freed" else "#b6f5ff"
            outline = "#f0a202" if survivor["state"] == "trapped" else "#4ba25f" if survivor["state"] == "freed" else "#79c7ff"
            canvas.create_oval(sx - 14, sy - 14, sx + 14, sy + 14, fill=color, outline=outline, width=2)
            tag_text = "TRAPPED" if survivor["state"] == "trapped" else "FREE" if survivor["state"] == "freed" else "CARRY"
            canvas.create_text(sx, sy - 22, text=tag_text, fill="#e5ffe5", font=("Helvetica", 8, "bold"))
            if survivor["state"] in {"trapped", "freeing"}:
                bar = survivor.get("progress", 0.0)
                canvas.create_rectangle(sx - 16, sy + 16, sx + 16, sy + 22, outline="#ffe0a3", width=2)
                canvas.create_rectangle(sx - 14, sy + 18, sx - 14 + 28 * bar, sy + 20, fill="#ffd166", outline="")
        canvas.create_rectangle(x1 - 12, y1 - 12, x2 + 12, y2 + 12, outline="#6d788f", width=2)
        player.draw(canvas)
        bar = clamp(self.heat / 50.0, 0.0, 1.0)
        canvas.create_rectangle(30, HEIGHT - 60, 190, HEIGHT - 30, outline="#ffbd45", width=2)
        canvas.create_rectangle(32, HEIGHT - 58, 32 + 156 * bar, HEIGHT - 32, fill="#ff5f45", outline="")
        canvas.create_text(110, HEIGHT - 75, text="Heat exposure", fill=TEXT, font=("Helvetica", 10, "bold"))
        canvas.create_text(
            WIDTH - 20,
            HEIGHT - 40,
            anchor="e",
            fill=TEXT,
            font=("Helvetica", 12, "bold"),
            text=f"Survivors: {self.saved}/5",
        )
        canvas.create_text(
            20,
            HEIGHT - 40,
            anchor="w",
            fill=TEXT,
            font=("Helvetica", 11),
            text="Tip: free trapped survivors by staying near, then carry them to the red door. Flames drain your clock and spread.",
        )
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

    def draw_result(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(WIDTH / 2 - 240, HEIGHT / 2 - 80, WIDTH / 2 + 240, HEIGHT / 2 + 80, fill="#0f1f33", outline="#4b89ff", width=3)
        canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text=self.message, fill=TEXT, font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, HEIGHT / 2 + 30, text="Press SPACE to return to the career hub.", fill="#c7e3ff", font=("Helvetica", 12, "bold"))


class ChefRushWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Chef Rush",
            summary="Assemble dishes in the right order while dodging kitchen chaos",
            duration=55.0,
        )
        self.bounds = (110.0, 100.0, WIDTH - 110.0, HEIGHT - 90.0)
        self.stations: list[dict[str, float | str]] = []
        self.recipe: list[str] = []
        self.step = 0
        self.step_progress = 0.0
        self.spills: list[dict[str, float]] = []
        self.tickets: list[dict[str, float]] = []
        self.ticket_spawn = 9.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 90)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.step = 0
        self.step_progress = 0.0
        self.tickets = []
        self.ticket_spawn = 8.0
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
        for station in self.stations:
            if self.step < len(self.recipe) and station["name"] == self.recipe[self.step]:
                continue
            if math.hypot(player.x - station["x"], player.y - station["y"]) < player.size + 20:
                self.timer = max(0.0, self.timer - dt * 5)
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
        canvas.create_rectangle(x1 - 10, y1 - 10, x2 + 10, y2 + 10, outline="#6a7c88", width=2)
        player.draw(canvas)
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

    def draw_result(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(WIDTH / 2 - 240, HEIGHT / 2 - 80, WIDTH / 2 + 240, HEIGHT / 2 + 80, fill="#232b3a", outline="#ff9f1c", width=3)
        canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text=self.message, fill=TEXT, font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, HEIGHT / 2 + 30, text="Press SPACE to return to the career hub.", fill="#ffe0b2", font=("Helvetica", 12, "bold"))


class BugHuntWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Software Engineer",
            summary="Patch code nodes in sequence while dodging glitches",
            duration=50.0,
        )
        self.bounds = (120.0, 110.0, WIDTH - 120.0, HEIGHT - 110.0)
        self.nodes: list[dict[str, float | str | bool]] = []
        self.glitches: list[dict[str, float]] = []
        self.index = 0
        self.patch_progress = 0.0
        self.deploy_progress = 0.0
        self.deploy_point = {"x": WIDTH / 2, "y": HEIGHT - 120}
        self.leak = {"x": WIDTH / 2, "y": HEIGHT / 2 + 40, "r": 40.0}

    def reset(self, player: Player) -> None:
        player.reset(140, 140)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.index = 0
        self.patch_progress = 0.0
        self.deploy_progress = 0.0
        self.leak["r"] = 40.0
        self.nodes = [
            {"name": "Telemetry", "x": 200, "y": 200, "color": "#8be9fd"},
            {"name": "Physics", "x": WIDTH - 220, "y": 180, "color": "#bd93f9"},
            {"name": "AI", "x": WIDTH / 2, "y": HEIGHT / 2 - 60, "color": "#50fa7b"},
            {"name": "UI", "x": WIDTH / 2 - 180, "y": HEIGHT / 2 + 100, "color": "#ffb86c"},
            {"name": "Netcode", "x": WIDTH - 220, "y": HEIGHT - 160, "color": "#ff6e6e"},
        ]
        self.glitches = []
        for _ in range(5):
            self.glitches.append(
                {
                    "x": random.randint(180, WIDTH - 180),
                    "y": random.randint(140, HEIGHT - 140),
                    "dx": random.choice([-1, 1]) * random.uniform(80, 130),
                    "dy": random.choice([-1, 1]) * random.uniform(80, 130),
                    "r": random.randint(18, 28),
                }
            )

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        x1, y1, x2, y2 = self.bounds
        player.speed = 260.0
        player.update(dt, keys, self.bounds)
        self.leak["r"] = clamp(self.leak["r"] + dt * 12.0, 40.0, 180.0)
        leak_dist = math.hypot(player.x - self.leak["x"], player.y - self.leak["y"])
        if leak_dist < self.leak["r"]:
            player.speed = 180.0
            self.timer = max(0.0, self.timer - dt * 3)
        for glitch in self.glitches:
            glitch["x"] += glitch["dx"] * dt
            glitch["y"] += glitch["dy"] * dt
            if glitch["x"] < x1 + 20 or glitch["x"] > x2 - 20:
                glitch["dx"] *= -1
            if glitch["y"] < y1 + 20 or glitch["y"] > y2 - 20:
                glitch["dy"] *= -1
            if math.hypot(player.x - glitch["x"], player.y - glitch["y"]) < player.size + glitch["r"]:
                self.timer = max(0.0, self.timer - dt * 6)
                player.reset(140, 140)
                break
        if self.index < len(self.nodes):
            target = self.nodes[self.index]
            on_target = math.hypot(player.x - target["x"], player.y - target["y"]) < player.size + 18
            if on_target:
                self.patch_progress = clamp(self.patch_progress + dt * 1.6, 0.0, 1.0)
            else:
                self.patch_progress = clamp(self.patch_progress - dt * 0.9, 0.0, 1.0)
            if self.patch_progress >= 0.99:
                self.index += 1
                self.patch_progress = 0.0
                self.timer = min(self.duration + 3, self.timer + 2.8)
        else:
            # Deploy build to prod
            deploy_dist = math.hypot(player.x - self.deploy_point["x"], player.y - self.deploy_point["y"])
            if deploy_dist < player.size + 26:
                self.deploy_progress = clamp(self.deploy_progress + dt * 1.5, 0.0, 1.0)
            else:
                self.deploy_progress = clamp(self.deploy_progress - dt * 1.0, 0.0, 1.0)
            if self.deploy_progress >= 0.99:
                self.finished = True
                self.success = True
                self.message = "Build is green and deployed. QA is happy!"
        for i, node in enumerate(self.nodes):
            if i == self.index:
                continue
            if math.hypot(player.x - node["x"], player.y - node["y"]) < player.size + 18:
                self.timer = max(0.0, self.timer - dt * 4)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        x1, y1, x2, y2 = self.bounds
        for i in range(6):
            shade = 12 + i * 8
            canvas.create_rectangle(
                0,
                i * (HEIGHT / 6),
                WIDTH,
                (i + 1) * (HEIGHT / 6),
                fill=f"#{shade:02x}{(shade+10):02x}{(shade+28):02x}",
                outline="",
            )
        canvas.create_rectangle(x1 - 30, y1 - 30, x2 + 30, y2 + 30, fill="#101828", outline="#2d3952", width=4)
        canvas.create_rectangle(x1, y1, x2, y2, fill="#121c2d", outline="#3b4c6b", width=3)
        for line_y in range(int(y1), int(y2), 28):
            canvas.create_line(x1, line_y, x2, line_y, fill="#1f2f48", dash=(4, 6))
        for line_x in range(int(x1), int(x2), 34):
            canvas.create_line(line_x, y1, line_x, y2, fill="#1f2f48", dash=(6, 6))
        canvas.create_oval(
            self.leak["x"] - self.leak["r"],
            self.leak["y"] - self.leak["r"],
            self.leak["x"] + self.leak["r"],
            self.leak["y"] + self.leak["r"],
            outline="#5ad1ff",
            width=3,
            fill="#102638",
        )
        canvas.create_text(
            WIDTH / 2,
            60,
            text="Late-night sprint. Fix nodes in order before QA wakes up.",
            fill="#cbe2ff",
            font=("Helvetica", 13, "bold"),
        )
        for i, node in enumerate(self.nodes):
            if i > 0:
                prev = self.nodes[i - 1]
                canvas.create_line(prev["x"], prev["y"], node["x"], node["y"], fill="#2dd8ff", width=4, dash=(4, 3))
                canvas.create_line(prev["x"], prev["y"], node["x"], node["y"], fill="#0a1826", width=1)
        for i, node in enumerate(self.nodes):
            glow = 8 if i == self.index else 4
            canvas.create_oval(
                node["x"] - 26,
                node["y"] - 26,
                node["x"] + 26,
                node["y"] + 26,
                fill="",
                outline=node["color"],
                width=glow,
            )
            canvas.create_oval(
                node["x"] - 20,
                node["y"] - 20,
                node["x"] + 20,
                node["y"] + 20,
                fill=node["color"],
                outline="#0b101e",
                width=3,
            )
            canvas.create_text(node["x"], node["y"] - 32, text=node["name"], fill=TEXT, font=("Helvetica", 10, "bold"))
            if i == self.index:
                canvas.create_rectangle(node["x"] - 22, node["y"] + 26, node["x"] + 22, node["y"] + 36, outline="#fefefe", width=2)
                canvas.create_rectangle(node["x"] - 20, node["y"] + 28, node["x"] - 20 + 40 * self.patch_progress, node["y"] + 34, fill="#50fa7b", outline="")
        scan_y = (time.time() * 70) % (y2 - y1) + y1
        canvas.create_rectangle(x1, scan_y, x2, scan_y + 12, fill="#1f5fff", outline="", stipple="gray25")
        for glitch in self.glitches:
            canvas.create_rectangle(
                glitch["x"] - glitch["r"] - 3,
                glitch["y"] - glitch["r"] - 3,
                glitch["x"] + glitch["r"] + 3,
                glitch["y"] + glitch["r"] + 3,
                fill="#1a0b18",
                outline="",
            )
        for glitch in self.glitches:
            canvas.create_rectangle(
                glitch["x"] - glitch["r"],
                glitch["y"] - glitch["r"],
                glitch["x"] + glitch["r"],
                glitch["y"] + glitch["r"],
                fill="#ff3366",
                outline="#ffd1e0",
                width=2,
            )
        canvas.create_rectangle(x1 - 10, y1 - 10, x2 + 10, y2 + 10, outline="#5e6d8c", width=2)
        # Deploy console appears after all nodes are patched
        if self.index >= len(self.nodes):
            cx = self.deploy_point["x"]
            cy = self.deploy_point["y"]
            canvas.create_rectangle(cx - 60, cy - 30, cx + 60, cy + 30, fill="#0c1828", outline="#4ad1ff", width=3)
            canvas.create_text(cx, cy - 10, text="DEPLOY", fill="#b7e9ff", font=("Helvetica", 11, "bold"))
            canvas.create_rectangle(cx - 50, cy + 10, cx + 50, cy + 20, outline="#b7e9ff", width=2)
            canvas.create_rectangle(cx - 48, cy + 12, cx - 48 + 96 * self.deploy_progress, cy + 18, fill="#50fa7b", outline="")
            canvas.create_text(cx, cy + 34, text="Hold to ship build", fill="#d8e7ff", font=("Helvetica", 9, "bold"))
        player.draw(canvas)
        pending = self.nodes[self.index]["name"] if self.index < len(self.nodes) else "Complete"
        canvas.create_text(
            WIDTH / 2,
            HEIGHT - 50,
            text=f"Next bug: {pending}",
            fill="#e7f3ff",
            font=("Helvetica", 12, "bold"),
        )
        canvas.create_text(20, HEIGHT - 80, anchor="w", text="Hold on glowing nodes to patch them in order, dodge glitches, avoid the memory leak pool, then deploy at the console.", fill=TEXT, font=("Helvetica", 11))
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

    def draw_result(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(WIDTH / 2 - 240, HEIGHT / 2 - 80, WIDTH / 2 + 240, HEIGHT / 2 + 80, fill="#222b3b", outline="#50fa7b", width=3)
        canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text=self.message, fill=TEXT, font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, HEIGHT / 2 + 30, text="Press SPACE to return to the career hub.", fill="#d0ffe2", font=("Helvetica", 12, "bold"))


class CareerGame:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Career Worlds")
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.player = Player()
        self.worlds: dict[str, BaseWorld] = {
            "1": FireRescueWorld(),
            "2": ChefRushWorld(),
            "3": BugHuntWorld(),
        }
        self.active_world: BaseWorld | None = None
        self.state = "menu"
        self.message = "Use WASD or arrow keys. Press 1, 2, or 3 to enter a career world."
        self.keys: set[str] = set()
        self.last_time = time.time()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_click)

    def on_key_press(self, event: tk.Event) -> None:
        self.keys.add(event.keysym)
        if self.state == "menu" and event.keysym in self.worlds:
            self.start_world(event.keysym)
        if self.state == "result" and event.keysym == "space":
            self.return_to_menu()

    def on_key_release(self, event: tk.Event) -> None:
        self.keys.discard(event.keysym)

    def on_click(self, event: tk.Event) -> None:
        if self.state != "menu":
            return
        if 140 <= event.y <= 240:
            self.start_world("1")
        elif 280 <= event.y <= 380:
            self.start_world("2")
        elif 420 <= event.y <= 520:
            self.start_world("3")

    def start_world(self, key: str) -> None:
        self.active_world = self.worlds[key]
        self.active_world.reset(self.player)
        self.state = "world"
        self.message = ""

    def return_to_menu(self) -> None:
        self.state = "menu"
        self.active_world = None
        self.message = "Pick another portal. Finish all three to master the hub!"

    def loop(self) -> None:
        now = time.time()
        dt = min(0.1, now - self.last_time)
        self.last_time = now
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "world" and self.active_world:
            self.active_world.update(dt, self.canvas, self.player, self.keys)
            if self.active_world.finished:
                self.state = "result"
        elif self.state == "result" and self.active_world:
            self.active_world.draw(self.canvas, self.player)
        self.root.after(16, self.loop)

    def draw_menu(self) -> None:
        self.canvas.delete("all")
        for i in range(8):
            shade = 18 + i * 5
            self.canvas.create_rectangle(
                0,
                i * (HEIGHT / 8),
                WIDTH,
                (i + 1) * (HEIGHT / 8),
                fill=f"#{shade:02x}{(shade+10):02x}{(shade+18):02x}",
                outline="",
            )
        for i in range(12):
            offset = (time.time() * 20 + i * 80) % (WIDTH + 200) - 200
            self.canvas.create_oval(offset, 60 + i * 28, offset + 120, 160 + i * 28, outline="#0f4c75", width=2)
        self.canvas.create_text(WIDTH / 2, 70, text="Career Worlds Hub", fill="#8ce1ff", font=("Helvetica", 26, "bold"))
        self.canvas.create_text(WIDTH / 2, 110, text="Jump into a mini-world and try the job for yourself.", fill="#d8e7ff", font=("Helvetica", 14))
        portals = [
            ("1", "Firefighter", "Rescue survivors and dodge fire", "#23486e"),
            ("2", "Chef", "Finish the dinner rush in order", "#25563f"),
            ("3", "Software Engineer", "Patch bugs before the build breaks", "#50346e"),
        ]
        y = 160
        for key, title, desc, color in portals:
            self.canvas.create_rectangle(170, y - 6, WIDTH - 170, y + 86, fill="#0b1220", outline="", width=0)
            self.canvas.create_rectangle(180, y, WIDTH - 180, y + 80, fill=color, outline="#f2f4ff", width=3)
            self.canvas.create_text(210, y + 20, anchor="w", text=f"[{key}] {title}", fill="#f9fbff", font=("Helvetica", 18, "bold"))
            self.canvas.create_text(210, y + 50, anchor="w", text=desc, fill="#d8e7ff", font=("Helvetica", 12))
            self.canvas.create_text(WIDTH - 200, y + 40, text="Click or press key", fill="#bfe3ff", font=("Helvetica", 10, "bold"))
            y += 120
        self.canvas.create_text(WIDTH / 2, HEIGHT - 60, text=self.message, fill="#b9c7e6", font=("Helvetica", 12, "bold"))
        self.canvas.create_text(WIDTH / 2, HEIGHT - 30, text="Controls: Arrow keys / WASD to move. Space returns to the hub after a job.", fill="#7fb6ff", font=("Helvetica", 11))

    def run(self) -> None:
        self.last_time = time.time()
        self.loop()
        self.root.mainloop()


if __name__ == "__main__":
    CareerGame().run()
