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
            summary="Debug code modules and push features under pressure",
            duration=50.0,
        )
        self.briefing = [
             "SYSTEM ALERT: Legacy code is breaking in production!",
             "As the Lead Dev, you must fix bugs in the modules.",
             "Walk to a RED module and hold SPACE to debug it.",
             "Only 4 bugs can be active at once to prevent total crash.",
             "Fix enough modules to save the release!"
        ]
        self.hints = [
             "Tip: Focus on modules that have been red for a while.",
             "Tip: Debugging takes about 2.5 seconds per bug.",
             "Tip: Once fixed, a module stays safe for a few seconds.",
             "Tip: Keep the total bug count below the limit."
        ]
        self.modules: list[dict[str, Any]] = []
        for i in range(8):
             self.modules.append({
                  "x": 100 + (i % 4) * 200,
                  "y": 150 + (i // 4) * 200,
                  "status": "ok",
                  "progress": 0.0,
                  "cooldown": 0.0
             })
        self.fixed_count = 0
        self.max_bugs = 4
        self.bug_spawn_timer = 1.0
        self.stability = 100.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.stability = 100.0
        self.fixed_count = 0
        self.bug_spawn_timer = 1.0
        for m in self.modules:
            m["status"] = "ok"
            m["progress"] = 0.0
            m["cooldown"] = 0.0
        self.shake = 0.0
        self.particles = []

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Spawn bugs up to max_bugs
        active_bugs = sum(1 for m in self.modules if m["status"] == "bug")
        self.bug_spawn_timer -= dt
        if self.bug_spawn_timer <= 0 and active_bugs < self.max_bugs:
             candidate_indices = [i for i, m in enumerate(self.modules) if m["status"] == "ok" and m["cooldown"] <= 0]
             if candidate_indices:
                  idx = random.choice(candidate_indices)
                  self.modules[idx]["status"] = "bug"
                  self.modules[idx]["progress"] = 0.0
                  self.bug_spawn_timer = random.uniform(1.5, 3.0)

        # Update modules
        for m in self.modules:
             if m["cooldown"] > 0:
                  m["cooldown"] -= dt
                  
             if m["status"] == "bug":
                  self.stability -= dt * 0.5
                  dist = math.hypot(player.x - m["x"], player.y - m["y"])
                  if dist < 60 and "space" in keys:
                       m["progress"] += dt * 40.0 # 2.5 seconds to fix
                       if m["progress"] >= 100.0:
                            m["status"] = "ok"
                            m["progress"] = 0.0
                            m["cooldown"] = 3.0 # Wait 3s before bugging again
                            self.fixed_count += 1
                  else:
                       # Progress decays if you stop
                       m["progress"] = max(0.0, m["progress"] - dt * 15.0)

        if self.stability <= 0:
            self.finished = True
            self.success = False
            self.message = "System Crash! Too many critical bugs."
            
        if self.timer <= 0:
            self.finished = True
            self.success = self.fixed_count >= 4
            self.message = f"Shift Over! Fixed: {self.fixed_count} bugs"
            if self.fixed_count >= 10: self.grade = "S"
            elif self.fixed_count >= 7: self.grade = "A"
            elif self.fixed_count >= 4: self.grade = "B"
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
