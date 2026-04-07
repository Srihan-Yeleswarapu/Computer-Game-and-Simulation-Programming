import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp, Particle
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class CybersecurityAnalystWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Cybersecurity Analyst",
            summary="Defend systems from cyber attacks",
            duration=90.0,
        )
        self.briefing = [
             "SECURITY ALERT: Cyber attack detected!",
             "As the Cybersecurity Analyst, you must defend",
             "the central server from incoming threats.",
             "Intercept malicious packets with your firewall.",
             "Warning: Too many breaches will compromise the system!"
        ]
        self.hints = [
             "Tip: Move your character to act as a firewall.",
             "Tip: Intercept the red threat packets before they hit the center.",
             "Tip: You are faster than the packets, prioritize targets.",
             "Tip: Protect the server integrity."
        ]
        self.attacks: list[dict[str, Any]] = []
        self.integrity = 100.0
        self.server_x = WIDTH / 2
        self.server_y = HEIGHT / 2

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2 - 50)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.shake = 0.0
        self.particles = []
        
        self.attacks = []
        self.integrity = 100.0

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        if not self.attacks:
            return ("Shield the CORE from upcoming malicious packets.", (self.server_x, self.server_y))
            
        threat = min(self.attacks, key=lambda a: math.hypot(self.server_x - a["x"], self.server_y - a["y"]))
        target_pos = (float(threat["x"]), float(threat["y"]))
        if math.hypot(player.x - target_pos[0], player.y - target_pos[1]) < player.size + 15:
            return ("Keep overlapping this red threat packet to intercept it before it reaches the CORE.", target_pos)
        
        return ("Move into this red threat packet now to block it before it reaches the CORE.", target_pos)

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        
        # Spawn attacks
        if random.random() < 1.2 * dt:
            side = random.randint(0, 3)
            if side == 0: x, y = random.uniform(0, WIDTH), -20
            elif side == 1: x, y = WIDTH+20, random.uniform(0, HEIGHT)
            elif side == 2: x, y = random.uniform(0, WIDTH), HEIGHT+20
            else: x, y = -20, random.uniform(0, HEIGHT)
            
            speed = random.uniform(50.0, 90.0)
            self.attacks.append({"x": x, "y": y, "speed": speed})

        new_attacks = []
        for a in self.attacks:
            angle = math.atan2(self.server_y - a["y"], self.server_x - a["x"])
            a["x"] += math.cos(angle) * a["speed"] * dt
            a["y"] += math.sin(angle) * a["speed"] * dt
            
            # Distance from server
            dist_server = math.hypot(self.server_x - a["x"], self.server_y - a["y"])
            # Distance from player (firewall)
            dist_player = math.hypot(player.x - a["x"], player.y - a["y"])
            
            if dist_player < player.size + 15: # Intercepted!
                 self.particles.append(Particle(a["x"], a["y"], "#00a8ff", 0, 0, 0.5, 5.0))
            elif dist_server < 30: # Hit server!
                 self.integrity -= 10.0
                 self.shake = 5.0
            else:
                 new_attacks.append(a)
                 
        self.attacks = new_attacks
        
        if self.integrity <= 0:
            self.finished = True
            self.success = False
            self.message = "System compromised! Too many breaches."
            
        if self.timer <= 0 and self.integrity > 0:
            self.finished = True
            self.success = True
            self.message = "Attack averted! System secured."
            if self.integrity > 80: self.grade = "S"
            elif self.integrity > 50: self.grade = "A"
            elif self.integrity > 20: self.grade = "B"
            else: self.grade = "C"

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
             
        bg = "#111" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Grid lines tracking to center
        canvas.create_line(0+sx, 0+sy, WIDTH+sx, HEIGHT+sy, fill="#222", dash=(4,4))
        canvas.create_line(WIDTH+sx, 0+sy, 0+sx, HEIGHT+sy, fill="#222", dash=(4,4))
        
        # Server
        canvas.create_rectangle(self.server_x-30+sx, self.server_y-30+sy, self.server_x+30+sx, self.server_y+30+sy, fill="#273c75", outline="#4cd137", width=3)
        canvas.create_text(self.server_x+sx, self.server_y+sy, text="CORE", fill="#4cd137", font=("Courier", 12, "bold"))
        
        # Attacks
        for a in self.attacks:
             canvas.create_polygon(a["x"]-10+sx, a["y"]+sy, a["x"]+sx, a["y"]-10+sy, a["x"]+10+sx, a["y"]+sy, a["x"]+sx, a["y"]+10+sy, fill="#e84118", outline="#fff")
             
        # Particles
        for p in self.particles:
             canvas.create_oval(p.x-p.size+sx, p.y-p.size+sy, p.x+p.size+sx, p.y+p.size+sy, fill=p.color, outline="")
             
        # Player (Firewall)
        canvas.create_oval(player.x-25+sx, player.y-25+sy, player.x+25+sx, player.y+25+sy, fill="", outline="#00a8ff", width=4, dash=(4,4))
        player.draw(canvas)

        # HUD specific
        canvas.create_rectangle(WIDTH/2 - 150, 60, WIDTH/2 + 150, 80, fill="#2f3542", outline="#fff")
        canvas.create_rectangle(WIDTH/2 - 148, 62, WIDTH/2 - 148 + 296 * (self.integrity/100.0), 78, fill="#4cd137", outline="")
        canvas.create_text(WIDTH/2, 70, text=f"SYSTEM INTEGRITY: {int(self.integrity)}%", fill="#1e272e", font=("Courier", 11, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
