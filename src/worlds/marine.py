import random
import math
import tkinter as tk
from ..utils import WIDTH, HEIGHT, TEXT, clamp, lerp
from ..player import Player
from .base import BaseWorld

class MarineWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Marine Biologist",
            summary="Dive, scan fish, and collect samples before O2 runs out",
            duration=60.0,
        )
        self.bounds = (40.0, 40.0, WIDTH - 40.0, HEIGHT - 40.0)
        self.fish: list[dict[str, float | str | bool]] = []
        self.samples: list[dict[str, float | bool]] = []
        self.bubbles: list[dict[str, float]] = []
        self.oxygen = 100.0
        self.scanned_count = 0
        self.collected_count = 0
        
        # Scanner tool
        self.scanner_active = False
        self.scan_target: dict | None = None
        self.scan_timer = 0.0

    def reset(self, player: Player, difficulty: int = 0) -> None:
        player.reset(WIDTH / 2, 80) # Start near surface
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.oxygen = 100.0
        self.oxygen_drain = 1.5 + (difficulty * 0.15) # Scaled drain
        self.scanned_count = 0
        self.collected_count = 0
        self.scanner_active = False
        self.scan_target = None
        self.scan_timer = 0.0
        
        # Populate world
        self.fish = []
        species = [
            {"name": "Clownfish", "color": "#ff7f50", "speed": 60},
            {"name": "Blue Tang", "color": "#1e90ff", "speed": 80},
            {"name": "Sea Turtle", "color": "#32cd32", "speed": 40},
            {"name": "Jellyfish", "color": "#e6e6fa", "speed": 20},
            {"name": "Manta Ray", "color": "#708090", "speed": 50},
        ]
        for _ in range(8):
            s = random.choice(species)
            self.fish.append({
                "x": random.uniform(100, WIDTH - 100),
                "y": random.uniform(200, HEIGHT - 100),
                "dx": random.choice([-1, 1]) * s["speed"],
                "dy": random.uniform(-20, 20),
                "type": s["name"],
                "color": s["color"],
                "scanned": False,
                "w": random.randint(30, 50)
            })
            
        self.samples = []
        for _ in range(3):
            self.samples.append({
                "x": random.uniform(100, WIDTH - 100),
                "y": HEIGHT - 60, # On the seabed
                "collected": False
            })
            
        self.bubbles = []
    
    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        if self.timer <= 0: return # Timer managed by base
        
        # Custom physics for swimming (gravity + buoyancy)
        # Player naturally floats up slowly if not moving down
        # Movement has inertia
        
        # Keys input handled by player.update, but we tweak physics after
        player.update(dt, keys, self.bounds)
        
        # Add "buoyancy" if not pressing down
        if "Down" not in keys and "s" not in keys:
             player.vy -= 100 * dt 
        
        # Clamp speed for water resistance
        player.vx = clamp(player.vx, -180, 180)
        player.vy = clamp(player.vy, -180, 180)
        
        # Oxygen drain
        self.oxygen = max(0.0, self.oxygen - dt * self.oxygen_drain)
        if self.oxygen <= 0:
            self.finished = True
            self.success = False
            self.message = "Oxygen depletion! Emergency surface."
            return

        # Fish movement
        x1, y1, x2, y2 = self.bounds
        for f in self.fish:
            f["x"] += f["dx"] * dt
            f["y"] += f["dy"] * dt
            if f["x"] < x1 or f["x"] > x2:
                f["dx"] *= -1
            if f["y"] < y1 + 100 or f["y"] > y2: # Stay deep
                f["dy"] *= -1
                
        # Scanner Logic (Hold Space to scan nearby fish)
        # Assuming Space is added to keys in main engine update (need to check)
        # Use "e" or "space" for interaction? Let's assume Space for now.
        
        closest_fish = None
        min_dist = 100.0
        
        for f in self.fish:
            d = math.hypot(player.x - f["x"], player.y - f["y"])
            if d < min_dist:
                min_dist = d
                closest_fish = f
        
        if closest_fish and min_dist < 80:
            self.scan_target = closest_fish
            if "space" in keys and not closest_fish["scanned"]:
                self.scan_timer += dt
                if self.scan_timer > 1.5:
                    closest_fish["scanned"] = True
                    self.scanned_count += 1
                    self.scan_timer = 0.0
                    self.scan_target = None
            else:
                self.scan_timer = max(0.0, self.scan_timer - dt * 2)
        else:
            self.scan_target = None
            self.scan_timer = 0.0

        # Sample Collection (Touch to collect)
        for s in self.samples:
            if not s["collected"]:
                if math.hypot(player.x - s["x"], player.y - s["y"]) < player.size + 20:
                    s["collected"] = True
                    self.collected_count += 1
                    
        # Bubbles Update
        if random.random() < 0.05:
            self.bubbles.append({"x": player.x, "y": player.y, "r": random.randint(2,6), "speed": random.randint(50, 100)})
        
        for b in self.bubbles:
            b["y"] -= b["speed"] * dt
            b["x"] += math.sin(b["y"] * 0.05) * 50 * dt
        self.bubbles = [b for b in self.bubbles if b["y"] > 0]

        # Win Condition
        if self.collected_count >= 3 and self.scanned_count >= 3:
            self.finished = True
            self.success = True
            self.message = "Research complete! The reef data is secured."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        # Water Gradient Background
        for i in range(10):
            shade = 255 - i * 20
            color = f"#00{shade:02x}ff" # Blueish
            h = HEIGHT / 10
            canvas.create_rectangle(0, i*h, WIDTH, (i+1)*h, fill=color, outline="")

        # Seabed
        canvas.create_rectangle(0, HEIGHT-60, WIDTH, HEIGHT, fill="#e0d2a4", outline="")
        
        # Samples
        for s in self.samples:
            if not s["collected"]:
                canvas.create_oval(s["x"]-10, s["y"]-10, s["x"]+10, s["y"]+10, fill="#8a2be2", outline="#fff")
                canvas.create_text(s["x"], s["y"]-20, text="SAMPLE", fill="#fff", font=("Helvetica", 8, "bold"))

        # Fish
        for f in self.fish:
            color = f["color"]
            w = f["w"]
            # Simple fish shape
            canvas.create_oval(f["x"]-w/2, f["y"]-10, f["x"]+w/2, f["y"]+10, fill=color, outline="")
            # Tail
            tail_x = f["x"] - w/2 if f["dx"] > 0 else f["x"] + w/2
            canvas.create_polygon(tail_x, f["y"], tail_x + ( -10 if f["dx"]>0 else 10), f["y"]-10, tail_x + ( -10 if f["dx"]>0 else 10), f["y"]+10, fill=color)
            
            if f["scanned"]:
                canvas.create_text(f["x"], f["y"]-20, text="SCANNED", fill="#0f0", font=("Helvetica", 8, "bold"))
            elif self.scan_target == f:
                 canvas.create_oval(f["x"]-w/2-5, f["y"]-15, f["x"]+w/2+5, f["y"]+15, outline="#fff", width=2, dash=(4,4))
                 
        # Bubbles
        for b in self.bubbles:
            canvas.create_oval(b["x"]-b["r"], b["y"]-b["r"], b["x"]+b["r"], b["y"]+b["r"], outline="#fff", width=1)
            
        # Player (Diver look?)
        # Base player draw is simple circle, maybe we add a scuba tank
        player.draw(canvas)
        canvas.create_rectangle(player.x-6, player.y-player.size-10, player.x+6, player.y-player.size, fill="#aaa", outline="#000") # Tank?

        # HUD - Oxygen
        bar_w = 200
        canvas.create_rectangle(20, HEIGHT - 50, 20 + bar_w, HEIGHT - 30, outline="#fff", width=2)
        canvas.create_rectangle(22, HEIGHT - 48, 22 + (bar_w-4) * (self.oxygen/100), HEIGHT - 32, fill="#0af", outline="")
        canvas.create_text(20 + bar_w/2, HEIGHT - 40, text=f"OXYGEN: {int(self.oxygen)}%", fill="#fff", font=("Helvetica", 10, "bold"))
        
        # HUD - Objectives
        canvas.create_text(WIDTH-20, HEIGHT-60, anchor="e", text=f"Samples: {self.collected_count}/3", fill="#fff", font=("Helvetica", 12, "bold"))
        canvas.create_text(WIDTH-20, HEIGHT-40, anchor="e", text=f"Scans: {self.scanned_count}/3", fill="#fff", font=("Helvetica", 12, "bold"))
        
        # Instructions
        if self.scan_target and not self.scan_target["scanned"]:
            pct = self.scan_timer / 1.5
            canvas.create_text(player.x, player.y - 50, text="Hold SPACE to Scan", fill="#ff0", font=("Helvetica", 10, "bold"))
            canvas.create_rectangle(player.x - 30, player.y - 45, player.x + 30, player.y - 40, outline="#fff")
            canvas.create_rectangle(player.x - 29, player.y - 44, player.x - 29 + 58 * pct, player.y - 41, fill="#0f0", outline="")

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
