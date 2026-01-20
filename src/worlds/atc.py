import random
import math
import tkinter as tk
from ..utils import WIDTH, HEIGHT, TEXT
from ..player import Player
from .base import BaseWorld

class ATCWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Air Traffic Controller",
            summary="Draw flight paths to land planes safely without crashes",
            duration=90.0,
        )
        self.planes = []
        self.landed_count = 0
        self.spawn_timer = 2.0
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
        self.spawn_timer = 2.0
        self.is_drawing = False
        self.current_path = []
        self.selected_plane = None

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:
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
        
        # Actually, let's stick to the requested "Path Drawing" - this implies Mouse.
        # Note: I haven't added mouse motion bindings to GameEngine yet. I need to do that.
        # For now, let's use the player as a cursor moved by WASD.
        # Hold SPACE to start drawing path for nearest plane.
        
        player.speed = 400.0 # Faster cursor
        player.update(dt, keys, (0,0,WIDTH,HEIGHT))
        
        # Spawn planes
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.planes) < 5:
            self.spawn_timer = random.uniform(3.0, 6.0)
            side = random.randint(0, 3)
            # Spawn at edges
            if side == 0: x, y = random.uniform(0, WIDTH), -20
            elif side == 1: x, y = WIDTH+20, random.uniform(0, HEIGHT)
            elif side == 2: x, y = random.uniform(0, WIDTH), HEIGHT+20
            else: x, y = -20, random.uniform(0, HEIGHT)
            
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
                    d = math.hypot(player.x - p["x"], player.y - p["y"])
                    if d < min_dist:
                        min_dist = d
                        nearest = p
                
                if nearest:
                    self.is_drawing = True
                    self.selected_plane = nearest
                    self.current_path = []
            else:
                # Add points to path
                if len(self.current_path) == 0 or math.hypot(player.x - self.current_path[-1][0], player.y - self.current_path[-1][1]) > 20:
                    self.current_path.append((player.x, player.y))
        else:
            if self.is_drawing:
                # Finish drawing
                if self.selected_plane:
                    self.selected_plane["path"] = self.current_path
                    # Calculate new velocity based on first point
                    if self.current_path:
                        pt = self.current_path[0]
                        angle = math.atan2(pt[1] - self.selected_plane["y"], pt[0] - self.selected_plane["x"])
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
            if p["path"]:
                target = p["path"][0]
                dx = target[0] - p["x"]
                dy = target[1] - p["y"]
                dist = math.hypot(dx, dy)
                if dist < 10:
                    p["path"].pop(0)
                    if not p["path"]:
                         # Check landing - forgiving radius
                         r_dist = math.hypot(p["x"] - runway["x"], p["y"] - runway["y"])
                         if r_dist < 80: # Generous landing zone
                             p["landed"] = True
                             self.landed_count += 1
                else:
                    # Move towards target
                    angle = math.atan2(dy, dx)
                    p["vx"] = math.cos(angle) * 60
                    p["vy"] = math.sin(angle) * 60
            
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            
            # Boundary check - bounce or wrap? Bounce implies "Holding pattern" logic needed, wrap implies easy mode.
            # Let's just clamp and bounce
            if p["x"] < 0 or p["x"] > WIDTH: p["vx"] *= -1
            if p["y"] < 0 or p["y"] > HEIGHT: p["vy"] *= -1
            
            # Collision detection
            for other in self.planes:
                if p != other and not p["landed"] and not other["landed"]:
                     if math.hypot(p["x"]-other["x"], p["y"]-other["y"]) < 20:
                         crashed = True
        
        self.planes = [p for p in self.planes if not p["landed"]]
        
        if crashed:
            self.finished = True
            self.success = False
            self.message = "CRASH DETECTED! Airspace unsafe."
            
        if self.landed_count >= 5:
            self.finished = True
            self.success = True
            self.message = "All flights landed safely. Good calm under pressure."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        # Radar BG
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#001a00", outline="")
        # Grid lines
        for i in range(10):
            canvas.create_oval(WIDTH/2 - i*50, HEIGHT/2 - i*50, WIDTH/2 + i*50, HEIGHT/2 + i*50, outline="#003300")
        
        # Runway
        r = self.runways[0]
        canvas.create_rectangle(r["x"]-r["w"]/2, r["y"]-r["h"]/2, r["x"]+r["w"]/2, r["y"]+r["h"]/2, fill="#333", outline="#666", width=2)
        canvas.create_text(r["x"], r["y"], text="RWY 09", fill="#fff", font=("Helvetica", 10, "bold"))
        
        # Planes
        for p in self.planes:
            color = "#0f0" if p == self.selected_plane else "#fff"
            canvas.create_oval(p["x"]-8, p["y"]-8, p["x"]+8, p["y"]+8, fill=color, outline="")
            canvas.create_text(p["x"], p["y"]-15, text="FLT", fill=color, font=("Helvetica", 8))
            
            # Draw path
            if p["path"]:
                pts = [(p["x"], p["y"])] + p["path"]
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
        canvas.create_text(WIDTH-20, 20, anchor="e", text=f"Landed: {self.landed_count}/5", fill="#0f0", font=("Helvetica", 14, "bold"))
        
        canvas.create_text(20, HEIGHT-30, anchor="w", text="WASD triggers cursor. Hold SPACE on a plane to draw landing path to RWY 09.", fill="#0f0", font=("Helvetica", 11))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
