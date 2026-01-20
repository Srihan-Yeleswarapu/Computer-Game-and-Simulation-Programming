import random
import math
import time
import tkinter as tk
from ..utils import WIDTH, HEIGHT, TEXT, clamp
from ..player import Player
from .base import BaseWorld

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
        self.warning = ""

    def reset(self, player: Player) -> None:
        player.reset(140, 140)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.index = 0
        self.patch_progress = 0.0
        self.deploy_progress = 0.0
        self.warning = ""
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
        self.leak["r"] = clamp(self.leak["r"] + dt * 4.0, 40.0, 130.0)
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
        self.warning = ""
        for i, node in enumerate(self.nodes):
            if i == self.index:
                continue
            if math.hypot(player.x - node["x"], player.y - node["y"]) < player.size + 18:
                self.timer = max(0.0, self.timer - dt * 0.5)
                self.warning = "Wrong Node!"
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
        if self.warning:
            canvas.create_text(WIDTH / 2, HEIGHT / 2 + 80, text=self.warning, fill="#ff4d4d", font=("Helvetica", 16, "bold"))
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
