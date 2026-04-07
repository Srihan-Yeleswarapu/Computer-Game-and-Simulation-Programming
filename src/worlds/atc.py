import random
import math
import time
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, SUCCESS, DANGER
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
        self.spawn_timer = 0.4
        self.plane_limit = 35
        self.is_drawing = False
        self.current_path = [] # list of (x,y)
        self.selected_plane = None
        self.collision_radius = 22.0
        self.landing_radius = 42.0
        
        self.runways = [
            {"x": WIDTH/2, "y": HEIGHT/2, "w": 320, "h": 60, "angle": 0},
        ]
        
    def reset(self, player: Player) -> None:
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.planes = []
        self.landed_count = 0
        self.spawn_timer = 0.4
        self.is_drawing = False
        self.current_path = []
        self.selected_plane = None
        self.shake = 0.0
        self.particles = []

    def calculate_grade(self) -> str:
        if not self.success:
            return "F"
        if self.landed_count >= 24:
            return "S"
        if self.landed_count >= 21:
            return "A"
        if self.landed_count >= 19:
            return "B"
        return "C"

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        if not self.planes:
            return ("Wait for aircraft to enter the controlled airspace.", None)

        if self.is_drawing and self.selected_plane is not None:
            return ("Keep holding SPACE and drag a safe route. Release SPACE to assign it to this aircraft.", (float(self.selected_plane["x"]), float(self.selected_plane["y"])))
            
        danger_plane = None
        for i, p1 in enumerate(self.planes):
            for p2 in self.planes[i+1:]:
                if math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"]) < self.collision_radius * 2.5:
                    danger_plane = p1
                    break
            if danger_plane: break
            
        if danger_plane:
            return ("Collision warning: move the cursor onto this plane, hold SPACE, drag a new route, then release.", (float(danger_plane["x"]), float(danger_plane["y"])))
            
        runway = self.runways[0]
        far_plane = max(self.planes, key=lambda p: math.hypot(p["x"] - runway["x"], p["y"] - runway["y"]))
        
        return ("Move the cursor onto this plane, hold SPACE, and draw a path into the runway box.", (float(far_plane["x"]), float(far_plane["y"])))

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.x, player.y = mouse_pos
        player.update(dt, keys, (0,0,WIDTH,HEIGHT))
        
        # Spawn planes
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.planes) < self.plane_limit:
            self.spawn_timer = random.uniform(0.4, 1.1)
            side = random.randint(0, 3)
            if side == 0: x, y = random.uniform(20, WIDTH-20), 20
            elif side == 1: x, y = WIDTH-20, random.uniform(20, HEIGHT-20)
            elif side == 2: x, y = random.uniform(20, WIDTH-20), HEIGHT-20
            else: x, y = 20, random.uniform(20, HEIGHT-20)
            
            target_x = WIDTH / 2 + random.uniform(-155, 155)
            target_y = HEIGHT / 2 + random.uniform(-115, 115)
            angle = math.atan2(target_y - y, target_x - x) + random.uniform(-0.13, 0.13)
            speed = random.uniform(55, 80)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            self.planes.append({
                "x": x, "y": y, "vx": vx, "vy": vy, 
                "path": [], "landed": False, "color": "#fff", "speed": speed
            })
            
        # Selection Logic
        if "space" in keys:
            if not self.is_drawing:
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
                    self.current_path = [(player.x, player.y)]
            else:
                if len(self.current_path) == 0 or math.hypot(player.x - self.current_path[-1][0], player.y - self.current_path[-1][1]) > 15:
                    self.current_path.append((player.x, player.y))
        else:
            if self.is_drawing:
                if self.selected_plane:
                    self.selected_plane["path"] = self.current_path
                    if self.current_path:
                        pt = self.current_path[0]
                        angle = math.atan2(pt[1] - self.selected_plane["y"], pt[0] - self.selected_plane["x"])
                        speed = float(self.selected_plane.get("speed", 105.0))
                        self.selected_plane["vx"] = math.cos(angle) * speed
                        self.selected_plane["vy"] = math.sin(angle) * speed
                self.is_drawing = False
                self.selected_plane = None
                self.current_path = []

        # Update Planes
        runway = self.runways[0]
        rw_rect = (runway["x"] - runway["w"]/2, runway["y"] - runway["h"]/2, runway["x"] + runway["w"]/2, runway["y"] + runway["h"]/2)
        crashed = False
        
        active_planes = []
        for p in self.planes:
            if p["path"]:
                target = p["path"][0]
                dx, dy = target[0] - p["x"], target[1] - p["y"]
                dist = math.hypot(dx, dy)
                if dist < 10:
                    p["path"].pop(0)
                else:
                    angle = math.atan2(dy, dx)
                    speed = float(p.get("speed", 105.0))
                    p["vx"] = math.cos(angle) * speed
                    p["vy"] = math.sin(angle) * speed
            
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            
            if p["x"] < 0 or p["x"] > WIDTH:
                p["vx"] *= -1
                p["x"] = max(0.0, min(WIDTH, p["x"]))
            if p["y"] < 0 or p["y"] > HEIGHT:
                p["vy"] *= -1
                p["y"] = max(0.0, min(HEIGHT, p["y"]))

            rx1, ry1, rx2, ry2 = rw_rect
            if rx1 <= p["x"] <= rx2 and ry1 <= p["y"] <= ry2:
                self.landed_count += 1
                continue
            active_planes.append(p)

        # Collision detection
        for i, p1 in enumerate(active_planes):
            for p2 in active_planes[i+1:]:
                if math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"]) < self.collision_radius:
                    crashed = True
                    break
            if crashed: break
            
        self.planes = active_planes
        
        if crashed:
            self.finished = True
            self.success = False
            self.message = "Operational safety compromised! Mid-air collision detected."
            self.shake = 8.0
            self.grade = "F"
            
        if self.timer <= 0 and not crashed:
            self.finished = True
            self.success = self.landed_count >= 19
            if self.success:
                self.message = f"Shift over! Successfully landed {self.landed_count} aircraft."
                self.grade = self.calculate_grade()
            else:
                self.message = f"Shift failure! Only {self.landed_count} planes landed safely."
                self.grade = "F"
            
        self.update_particles(dt)
        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0
        sy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0
        bg = "#071207" if not self.high_contrast else "#000000"
        canvas.create_rectangle(sx, sy, WIDTH+sx, HEIGHT+sy, fill=bg)
        for i in range(1, 10):
            canvas.create_oval(WIDTH/2 - i*50 + sx, HEIGHT/2 - i*50 + sy, WIDTH/2 + i*50 + sx, HEIGHT/2 + i*50 + sy, outline="#1a3d1a")
        sweep = (time.time() * 2) % (math.pi * 2)
        cx, cy = WIDTH / 2 + sx, HEIGHT / 2 + sy
        canvas.create_line(cx, cy, cx + math.cos(sweep) * 800, cy + math.sin(sweep) * 800, fill="#1a3d1a", width=2)
        r = self.runways[0]
        canvas.create_rectangle(r["x"]-r["w"]/2, r["y"]-r["h"]/2, r["x"]+r["w"]/2, r["y"]+r["h"]/2, fill="#333", outline="#666", width=2)
        canvas.create_text(r["x"], r["y"], text="RWY 09", fill="#fff", font=("Helvetica", 10, "bold"))
        for p in self.planes:
            color = "#0f0" if p == self.selected_plane else "#fff"
            canvas.create_oval(p["x"]-8, p["y"]-8, p["x"]+8, p["y"]+8, fill=color, outline="")
            canvas.create_text(p["x"], p["y"]-15, text="FLT", fill=color, font=("Helvetica", 8))
            if p["path"]:
                pts = [(p["x"], p["y"])] + p["path"]
                flat_pts = [c for pt in pts for c in pt]
                if len(flat_pts) >= 4:
                    canvas.create_line(flat_pts, fill=color, tag="path")
        if self.is_drawing and len(self.current_path) > 1:
            flat = [c for pt in self.current_path for c in pt]
            canvas.create_line(flat, fill="#ff0", width=2, dash=(4,4))
        canvas.create_line(player.x-10, player.y, player.x+10, player.y, fill="#ff0")
        canvas.create_line(player.x, player.y-10, player.x, player.y+10, fill="#ff0")
        canvas.create_text(WIDTH-20, 60, anchor="e", text=f"Landed: {self.landed_count} / 19", fill="#0f0", font=("Helvetica", 14, "bold"))
        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
