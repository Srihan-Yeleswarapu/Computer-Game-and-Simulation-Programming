import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp, lerp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any, cast

class FireRescueWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Firefighter Rescue",
            summary="Navigate smoke, dodge flames, and carry survivors out",
            duration=55.0,
        )
        self.briefing = [
             "RESCUE 5 survivors and bring them to the CREW DOOR.",
             "STAND NEAR survivors to free them, then carry them.",
             "WATCH OUT for flames—they drain your time on contact!"
        ]
        self.hints = [
             "Tip: Stay low! Use WASD to navigate the floor plan.",
             "Tip: Touch a survivor to pick them up, then head to the yellow door.",
             "Tip: Only one survivor can be carried at a time.",
             "Tip: Speed is life! But watch out for the fire's growth."
        ]
        self.DOOR_ZONE = (80, HEIGHT / 2 - 40, 220, HEIGHT / 2 + 40)
        # Fix applied: bounds starting at 60.0 to allow door access
        self.bounds = (60.0, 60.0, WIDTH - 40.0, HEIGHT - 60.0)
        self.survivors: list[dict[str, Any]] = []
        self.flames: list[dict[str, Any]] = []
        self.smoke: list[dict[str, Any]] = []
        self.carrying: dict[str, Any] | None = None
        self.saved = 0
        self.heat = 0.0
        self.spread_cap = 12

    def reset(self, player: Player) -> None:
        start_x = self.bounds[0] + 20
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
                "x": random.randint(320, 860),
                "y": random.randint(100, HEIGHT - 100),
                "state": "trapped",
                "progress": 0.0,
            }
            for _ in range(5)
        ]
        self.flames = []
        for _ in range(7):
            self.flames.append(
                {
                    "x": random.randint(240, WIDTH - 40),
                    "y": random.randint(80, HEIGHT - 80),
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

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        if self.carrying:
            dx1, dy1, dx2, dy2 = self.DOOR_ZONE
            return ("Carry the survivor to the yellow Crew Door on the left.", ((dx1 + dx2) / 2, (dy1 + dy2) / 2))
            
        if not self.survivors:
            return ("All survivors cleared! Wait for the building to stabilize.", None)
            
        # Target the nearest survivor
        survivor = min(self.survivors, key=lambda s: math.hypot(player.x - float(s["x"]), player.y - float(s["y"])))
        target_pos = (float(survivor["x"]), float(survivor["y"]))
        
        if survivor["state"] == "trapped":
            return ("Stand near the trapped survivor to free them.", target_pos)
        if survivor["state"] == "freeing":
            return ("Stay close! Freeing the survivor from the debris...", target_pos)
        if survivor["state"] == "freed":
            return ("Touch the freed survivor to pick them up.", target_pos)
            
        return ("Navigate through the smoke and locate survivors.", None)

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.update_particles(dt)
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
        if not self.carrying:
            for survivor in self.survivors:
                dist = math.hypot(player.x - survivor["x"], player.y - survivor["y"])
                if survivor["state"] == "trapped" and dist < player.size + 16:
                    survivor["state"] = "freeing"
                if survivor["state"] == "freeing":
                    progress = float(survivor.get("progress", 0.0))
                    survivor["progress"] = clamp(progress + dt * 1.4, 0.0, 1.0)
                    if survivor["progress"] >= 0.99:
                        survivor["state"] = "freed"
                elif survivor["state"] == "freed" and dist < player.size + 14:
                    survivor["state"] = "carried"
                    self.carrying = survivor
                    break
                else:
                    progress = float(survivor.get("progress", 0.0))
                    survivor["progress"] = clamp(progress - dt * 0.5, 0.0, 1.0)
        carrying = self.carrying
        if carrying is not None:
            carrying["x"] = lerp(float(carrying["x"]), player.x + 14, clamp(dt * 8, 0, 1))
            carrying["y"] = lerp(float(carrying["y"]), player.y - 28, clamp(dt * 8, 0, 1))
            if self.DOOR_ZONE[0] <= player.x <= self.DOOR_ZONE[2] and self.DOOR_ZONE[1] <= player.y <= self.DOOR_ZONE[3]:
                carrying["state"] = "saved"
                self.saved += 1
                self.carrying = None
        self.survivors = [s for s in self.survivors if s["state"] != "saved"]
        for flame in self.flames:
            if math.hypot(player.x - flame["x"], player.y - flame["y"]) < player.size + flame["r"]:
                self.heat += dt * 35
                self.shake = 4.0
                self.timer = max(0.0, self.timer - dt * 3)
                if self.heat > 40:
                    player.reset(self.bounds[0] + 20, HEIGHT / 2)
                    self.heat = 0.0
        if self.timer <= 0:
            self.finished = True
            self.success = self.saved >= 2
            if self.success:
                self.message = f"Shift Over! {self.saved}/5 survivors rescued from the fire."
                if self.saved == 5: self.grade = "S"
                elif self.saved == 4: self.grade = "A"
                elif self.saved == 3: self.grade = "B"
                else: self.grade = "C"
            else:
                self.message = f"Fire out of control! Only {self.saved}/5 survivors evacuated."
                self.grade = "F"
            
        if self.saved >= 5:
            self.finished = True
            self.success = True
            self.grade = "S"
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
        
        dx1, dy1, dx2, dy2 = self.DOOR_ZONE
        canvas.create_rectangle(dx1, dy1, dx2, dy2, fill="#c24747", outline="#d97e7e", width=3)
        canvas.create_polygon(dx2, dy1 + 10, dx2 + 20, (dy1 + dy2)/2, dx2, dy2 - 10, fill="#ffd166", outline="#ffb703", width=3)
        canvas.create_text(dx1 + 40, dy1 - 15, anchor="w", fill="#ffdd99", font=("Helvetica", 13, "bold"), text="Crew door")
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
            tag_text = str(survivor["state"]).upper()
            if tag_text == "FREEING": tag_text = "FREEING..."
            elif tag_text == "FREED": tag_text = "FREE"
            canvas.create_text(sx, sy - 22, text=tag_text, fill="#e5ffe5", font=("Helvetica", 8, "bold"))
            if survivor["state"] in {"trapped", "freeing"}:
                bar = float(survivor.get("progress", 0.0))
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
        # canvas.create_text(
        #     20,
        #     HEIGHT - 40,
        #     anchor="w",
        #     fill=TEXT,
        #     font=("Helvetica", 11),
        #     text="Tip: free trapped survivors by staying near, then carry them to the red door. Flames drain your clock and spread.",
        # )
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
