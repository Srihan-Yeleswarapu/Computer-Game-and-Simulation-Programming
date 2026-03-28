import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class SoftwareDeveloperWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Software Developer",
            summary="Fix system bugs before the application crashes",
            duration=90.0,
        )
        self.briefing = [
             "SYSTEM ALERT: Critical bugs are crashing the application!",
             "As the Software Developer, you must identify and fix errors",
             "while keeping the system running smoothly.",
             "Prioritize critical bugs and optimize performance.",
             "Warning: Too many unresolved bugs will cause a system failure!"
        ]
        self.hints = [
             "Tip: Focus on high-priority bugs (Red nodes) first.",
             "Tip: Use WASD to navigate the server grid.",
             "Tip: Hold SPACE over a bug to compile a fix.",
             "Tip: Keep the system stable while implementing fixes."
        ]
        self.servers: list[dict[str, Any]] = []
        self.stability = 100.0
        self.connections: list[tuple[int, int]] = []
        self.fixing_progress = 0.0
        self.active_server = -1

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.stability = 100.0
        self.servers = []
        self.connections = []
        self.fixing_progress = 0.0
        self.active_server = -1
        self.shake = 0.0
        self.particles = []
        
        # Create grid of servers
        cols, rows = 5, 3
        gap_x = (WIDTH - 200) / (cols - 1)
        gap_y = (HEIGHT - 200) / (rows - 1)
        start_x, start_y = 100, 100
        
        for r in range(rows):
            for c in range(cols):
                self.servers.append({
                    "x": start_x + c * gap_x,
                    "y": start_y + r * gap_y,
                    "bugged": random.random() < 0.2, # Initial bugs
                    "severity": random.uniform(2.0, 5.0),
                    "id": len(self.servers)
                })
                
        # Connect servers (horizontal and vertical)
        for r in range(rows):
            for c in range(cols):
                i = r * cols + c
                if c < cols - 1:
                    self.connections.append((i, i + 1))
                if r < rows - 1:
                    self.connections.append((i, i + cols))

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # New bugs spawn randomly over time
        if random.random() < 0.2 * dt:
            clean = [s for s in self.servers if not s["bugged"]]
            if clean:
                s = random.choice(clean)
                s["bugged"] = True
                s["severity"] = random.uniform(2.0, 5.0)
                
        # Bugs spread to connected nodes
        if random.random() < 0.1 * dt:
            bugged_ids = [s["id"] for s in self.servers if s["bugged"]]
            for c1, c2 in self.connections:
                if (c1 in bugged_ids) != (c2 in bugged_ids):
                    target = c2 if c1 in bugged_ids else c1
                    if random.random() < 0.5:
                        self.servers[target]["bugged"] = True
                        self.servers[target]["severity"] = 2.0
                        
        bug_count = 0
        self.active_server = -1
        
        for s in self.servers:
            if s["bugged"]:
                bug_count += 1
                self.stability -= dt * s["severity"] * 0.1
                
            # Check interaction
            if math.hypot(player.x - float(s["x"]), player.y - float(s["y"])) < player.size + 30:
                self.active_server = int(s["id"])
                
        if self.active_server != -1 and "space" in keys:
            target = self.servers[self.active_server]
            if target["bugged"]:
                self.fixing_progress += dt * 50.0 # Fix speed
                if self.fixing_progress >= 100.0:
                    target["bugged"] = False
                    self.fixing_progress = 0.0
                    self.stability = min(100.0, self.stability + 5.0)
            else:
                self.fixing_progress = 0.0
        else:
            self.fixing_progress = max(0.0, self.fixing_progress - dt * 100.0) # Decay if let go

        if bug_count > len(self.servers) * 0.7:
             self.shake = 4.0

        if self.stability <= 0:
            self.finished = True
            self.success = False
            self.message = "System Crash! Too many critical bugs."
            
        if self.timer <= 0:
            if self.stability > 0:
                self.finished = True
                self.success = True
                self.message = "Shift over! System is stable."
                if self.stability > 80: self.grade = "S"
                elif self.stability > 60: self.grade = "A"
                elif self.stability > 40: self.grade = "B"
                else: self.grade = "C"

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#1e272e" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Connections
        for c1, c2 in self.connections:
            s1 = self.servers[c1]
            s2 = self.servers[c2]
            color = "#ff3f34" if s1["bugged"] and s2["bugged"] else "#3c40c6"
            if self.high_contrast: color = "#ff0000" if s1["bugged"] and s2["bugged"] else "#fff"
            canvas.create_line(s1["x"]+sx, s1["y"]+sy, s2["x"]+sx, s2["y"]+sy, fill=color, width=3)
            
        # Servers
        for i, s in enumerate(self.servers):
            color = "#ff3f34" if s["bugged"] else "#0fbcf9"
            if self.high_contrast: color = "#ff0000" if s["bugged"] else "#00ff00"
            r = 25
            outline = "#fff" if i == self.active_server else ("#ffa801" if s["bugged"] and s["severity"] > 4.0 else "")
            width = 3 if outline else 0
            
            canvas.create_rectangle(s["x"]-r+sx, s["y"]-r+sy, s["x"]+r+sx, s["y"]+r+sy, fill=color, outline=outline, width=width)
            
            if s["bugged"]:
                canvas.create_text(s["x"]+sx, s["y"]+sy, text="BUG", fill="#fff", font=("Courier", 10, "bold"))
            else:
                canvas.create_text(s["x"]+sx, s["y"]+sy, text="OK", fill="#fff", font=("Courier", 10))
                
            # Progress bar for fix
            if i == self.active_server and s["bugged"]:
                canvas.create_rectangle(s["x"]-30+sx, s["y"]+30+sy, s["x"]+30+sx, s["y"]+38+sy, fill="#333", outline="#fff")
                canvas.create_rectangle(s["x"]-28+sx, s["y"]+32+sy, s["x"]-28 + 56 * (self.fixing_progress/100.0) + sx, s["y"]+36+sy, fill="#fff", outline="")
                
        # Stability UI
        canvas.create_rectangle(WIDTH/2 - 150, 60, WIDTH/2 + 150, 80, fill="#333")
        canvas.create_rectangle(WIDTH/2 - 148, 62, WIDTH/2 - 148 + 296 * max(0.0, self.stability)/100.0, 78, fill="#0fbcf9" if self.stability > 30 else "#ff3f34")
        canvas.create_text(WIDTH/2, 70, text=f"SYSTEM STABILITY: {int(self.stability)}%", fill="#fff", font=("Courier", 12, "bold"))
        
        # Player
        player.draw(canvas)
        # Extra highlight for player
        if "space" in self.keys and self.active_server != -1 and self.servers[self.active_server]["bugged"]:
             canvas.create_oval(player.x-player.size-5, player.y-player.size-5, player.x+player.size+5, player.y+player.size+5, outline="#fff", width=2, dash=(4,4))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
