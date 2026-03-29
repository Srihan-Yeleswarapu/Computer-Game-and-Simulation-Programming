import random
import math
import time
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any, cast

class ATCWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Air Traffic Control",
            summary="Coordinate approach vectors to land aircraft safely",
            duration=70.0,
        )
        self.briefing = [
             "TRAFFIC ALERT: Extremely heavy volume entering airspace.",
             "As the Lead Controller, you must guide flights safely",
             "to the primary landing strip without any mid-air collisions.",
             "Survive the 70 second rush to clear your shift.",
             "Warning: Colliding planes will fail the shift and reduce your grade!"
        ]
        self.hints = [
             "Tip: Click and drag from a plane to draw its new flight path.",
             "Tip: Planes will automatically land once they touch the runway zone.",
             "Tip: Watch the separation between aircraft – don't let them overlap!",
             "Tip: Survive until the timer runs out."
        ]
        self.planes = []
        self.landed_count = 0
        self.spawn_timer = 1.0
        self.plane_limit = 20
        self.is_drawing = False
        self.current_path = [] # list of (x,y)
        self.selected_plane = None
        
        self.runways = [
            {"x": WIDTH/2, "y": HEIGHT/2, "w": 200, "h": 40, "angle": 0},
        ]
        
    def reset(self, player: Player) -> None:
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.planes = []
        self.landed_count = 0
        self.spawn_timer = 1.0
        self.is_drawing = False
        self.current_path = []
        self.selected_plane = None
        self.shake = 0.0
        self.particles = []

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        
        # Mouse input handling needs to be hacked in via player pos or better, bind events in Main but for now:
        # We rely on mouse events. Since BaseWorld doesn't have direct event access easily without callbacks,
        # we might need to assume 'player' x/y is mouse x/y if we change the engine, OR
        # better: we use the player object as a cursor.
        # Let's assume player object IS the cursor controlled by mouse if we could, 
        # BUT the requirements say "User journey... intuitively".
        # Current engine binds arrow keys.
        # Adapting to Arrow Keys cursor for ATC is hard. 
        # I will assume we can use the mouse bindings I added to GameEngine in next step or use Space to select.
        
        # Use real mouse position instead of hacked player cursor
        player.x, player.y = mouse_pos
        player.update(dt, keys, (0,0,WIDTH,HEIGHT))
        
        # Spawn planes
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.planes) < self.plane_limit:
            self.spawn_timer = random.uniform(2.0, 4.0)
            side = random.randint(0, 3)
            # Spawn at edges, slightly inside so they don't instantly bounce
            if side == 0: x, y = random.uniform(20, WIDTH-20), 20
            elif side == 1: x, y = WIDTH-20, random.uniform(20, HEIGHT-20)
            elif side == 2: x, y = random.uniform(20, WIDTH-20), HEIGHT-20
            else: x, y = 20, random.uniform(20, HEIGHT-20)
            
            # Target center initially
            angle = math.atan2(HEIGHT/2 - y, WIDTH/2 - x)
            vx = math.cos(angle) * 40
            vy = math.sin(angle) * 40
            
            self.planes.append({
                "x": x, "y": y, "vx": vx, "vy": vy, 
                "path": [], "landed": False, "color": "#fff"
            })
            
        # Selection Logic
        if "space" in keys:
            if not self.is_drawing:
                # Find nearest plane
                nearest = None
                min_dist = 50.0
                for p in self.planes:
                    px = float(p["x"])
                    py = float(p["y"])
                    d = math.hypot(player.x - px, player.y - py)
                    if d < min_dist:
                        min_dist = d
                        nearest = p
                
                if nearest:
                    self.is_drawing = True
                    self.selected_plane = nearest
                    self.current_path = [(player.x, player.y)]
            else:
                # Add points to path
                if len(self.current_path) == 0 or math.hypot(player.x - self.current_path[-1][0], player.y - self.current_path[-1][1]) > 15:
                    self.current_path.append((player.x, player.y))
        else:
            if self.is_drawing:
                # Finish drawing
                if self.selected_plane:
                    self.selected_plane["path"] = self.current_path
                    # Calculate new velocity based on first point
                    if self.current_path:
                        pt = self.current_path[0]
                        px = float(self.selected_plane["x"])
                        py = float(self.selected_plane["y"])
                        angle = math.atan2(pt[1] - py, pt[0] - px)
                        self.selected_plane["vx"] = math.cos(angle) * 60
                        self.selected_plane["vy"] = math.sin(angle) * 60
                self.is_drawing = False
                self.selected_plane = None
                self.current_path = []

        # Update Planes
        runway = self.runways[0]
        # Runway rect
        rw_rect = (runway["x"] - runway["w"]/2, runway["y"] - runway["h"]/2, runway["x"] + runway["w"]/2, runway["y"] + runway["h"]/2)
        
        crashed = False
        
        for p in self.planes:
            px = float(p["x"])
            py = float(p["y"])
            if p["path"]:
                target = p["path"][0]
                dx = target[0] - px
                dy = target[1] - py
                dist = math.hypot(dx, dy)
                if dist < 10:
                    p["path"].pop(0)
                    if not p["path"]:
                         pass # Landing is handled globally now
                else:
                    # Move towards target
                    angle = math.atan2(dy, dx)
                    p["vx"] = math.cos(angle) * 60
                    p["vy"] = math.sin(angle) * 60
            
            p["x"] = px + float(p.get("vx", 0.0)) * dt
            p["y"] = py + float(p.get("vy", 0.0)) * dt
            
            # Boundary check - bounce or wrap? Bounce implies "Holding pattern" logic needed, wrap implies easy mode.
            # Let's just clamp and bounce
            if p["x"] < 0 or p["x"] > WIDTH: p["vx"] *= -1
            if p["y"] < 0 or p["y"] > HEIGHT: p["vy"] *= -1
            
            # Collision detection
            for other in self.planes:
                if p != other and not p["landed"] and not other["landed"]:
                     if math.hypot(float(p["x"])-float(other["x"]), float(p["y"])-float(other["y"])) < 14:
                         crashed = True
                         
            # Universal Landing Check
            if not p["landed"]:
                r_dist = math.hypot(p["x"] - float(runway["x"]), p["y"] - float(runway["y"]))
                if r_dist < 60:
                     p["landed"] = True
                     self.landed_count += 1
        
        self.planes = [p for p in self.planes if not p["landed"]]
        
        if crashed:
            self.finished = True
            self.success = False
            self.message = "Operational safety compromised! Mid-air collision detected."
            self.shake = 8.0
            # Penalty grading
            if self.landed_count >= 15: self.grade = "B"
            elif self.landed_count >= 10: self.grade = "C"
            else: self.grade = "D"
            
        if self.timer <= 0 and not crashed:
            self.finished = True
            self.success = True
            self.message = "Shift over! Skies navigated safely."
            if self.landed_count >= 15: self.grade = "S"
            elif self.landed_count >= 10: self.grade = "A"
            elif self.landed_count >= 6: self.grade = "B"
            elif self.landed_count >= 3: self.grade = "C"
            else: self.grade = "D"
            
        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        # Radar BG with Shake
        sx, sy = 0, 0
        if self.shake > 0:
             sx = random.uniform(-self.shake, self.shake)
             sy = random.uniform(-self.shake, self.shake)
        
        bg = "#071207" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        
        # Grid lines
        for i in range(1, 10):
            canvas.create_oval(WIDTH/2 - i*50 + sx, HEIGHT/2 - i*50 + sy, WIDTH/2 + i*50 + sx, HEIGHT/2 + i*50 + sy, outline="#1a3d1a")
        
        # Radar sweep animation (micro-animation)
        sweep = (time.time() * 2) % (math.pi * 2)
        cx, cy = WIDTH / 2 + sx, HEIGHT / 2 + sy
        canvas.create_line(cx, cy, cx + math.cos(sweep) * 800, cy + math.sin(sweep) * 800, fill="#1a3d1a", width=2) if not self.high_contrast else None
        
        # Runway
        r = self.runways[0]
        canvas.create_rectangle(r["x"]-r["w"]/2, r["y"]-r["h"]/2, r["x"]+r["w"]/2, r["y"]+r["h"]/2, fill="#333", outline="#666", width=2)
        canvas.create_text(r["x"], r["y"], text="RWY 09", fill="#fff", font=("Helvetica", 10, "bold"))
        
        # Planes
        for p in self.planes:
            px = float(p["x"])
            py = float(p["y"])
            color = "#0f0" if p == self.selected_plane else "#fff"
            canvas.create_oval(px-8, py-8, px+8, py+8, fill=color, outline="")
            canvas.create_text(px, py-15, text="FLT", fill=color, font=("Helvetica", 8))
            
            # Draw path
            if p["path"]:
                pts = [(px, py)] + p["path"]
                # flatten
                flat_pts = [c for pt in pts for c in pt]
                if len(flat_pts) >= 4:
                    canvas.create_line(flat_pts, fill=color, tag="path")
                    
        # Drawing line
        if self.is_drawing and len(self.current_path) > 1:
            flat = [c for pt in self.current_path for c in pt]
            canvas.create_line(flat, fill="#ff0", width=2, dash=(4,4))
            
        # Cursor
        canvas.create_line(player.x-10, player.y, player.x+10, player.y, fill="#ff0")
        canvas.create_line(player.x, player.y-10, player.x, player.y+10, fill="#ff0")
        
        # HUD
        canvas.create_text(WIDTH-20, 20, anchor="e", text=f"Landed: {self.landed_count}", fill="#0f0", font=("Helvetica", 14, "bold"))
        
        canvas.create_text(20, HEIGHT-30, anchor="w", text="Move Mouse/WASD to position director. Hold SPACE on a plane to draw its approach path.", fill="#0f0", font=("Helvetica", 11))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
