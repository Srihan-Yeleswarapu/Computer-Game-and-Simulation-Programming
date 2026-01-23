import random
import math
import tkinter as tk
from ..utils import WIDTH, HEIGHT, TEXT, clamp
from ..player import Player
from .base import BaseWorld

class ArchitectWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Architect",
            summary="Design a stable Eco-Library that withstands the wind test",
            duration=90.0,
        )
        self.grid_size = 40
        self.grid_w = 12
        self.grid_h = 8
        self.offset_x = WIDTH // 2 - (self.grid_w * self.grid_size) // 2
        self.offset_y = HEIGHT // 2 - (self.grid_h * self.grid_size) // 2
        
        self.blocks = [] # (grid_x, grid_y, type)
        self.room_types = [
            {"name": "Lobby", "color": "#e1e1e1", "cost": 10},
            {"name": "Books", "color": "#8b4513", "cost": 15},
            {"name": "Eco-Roof", "color": "#7cfc00", "cost": 20},
            {"name": "Elevator", "color": "#708090", "cost": 25},
        ]
        self.selected_room = 0
        self.budget = 1000
        self.phase = "build" # build, test
        self.wind_force = 0.0
        self.wind_timer = 0.0
        self.stability = 100.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 80)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.blocks = []
        self.budget = 1000
        self.phase = "build"
        self.wind_force = 0.0
        self.stability = 100.0
        self.wind_timer = 0.0
        
        # Pre-place foundation
        for i in range(self.grid_w):
            self.blocks.append({"gx": i, "gy": self.grid_h, "type": "Foundation", "fixed": True})

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        x1, y1, x2, y2 = 0, 0, WIDTH, HEIGHT # Full screen movement
        player.update(dt, keys, (x1, y1, x2, y2))
        
        if self.phase == "build":
            self.tick_timer(dt)
            
            # Room selection (1-4 keys)
            if "1" in keys: self.selected_room = 0
            if "2" in keys: self.selected_room = 1
            if "3" in keys: self.selected_room = 2
            if "4" in keys: self.selected_room = 3
            
            # Place block (Space)
            # Find grid cell player is standing on
            gx = int((player.x - self.offset_x) // self.grid_size)
            gy = int((player.y - self.offset_y) // self.grid_size)
            
            if "space" in keys:
                if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
                    cost = self.room_types[self.selected_room]["cost"]
                    # Check overlap
                    occupied = any(b["gx"] == gx and b["gy"] == gy for b in self.blocks)
                    if not occupied and self.budget >= cost:
                        self.blocks.append({
                            "gx": gx,
                            "gy": gy,
                            "type": self.room_types[self.selected_room]["name"],
                            "color": self.room_types[self.selected_room]["color"],
                            "fixed": False
                        })
                        self.budget -= cost
                        # Key debounce logic needed ideally, but naive approach works with fast ticks
                        
            # Test Button
            if self.budget < 50 or "Return" in keys: # Enter to test
                self.phase = "test"
                self.wind_timer = 10.0 # Full 10‑second wind test
                
        elif self.phase == "test":
            self.wind_timer -= dt
            # Wind gusts
            base_wind = (10.0 - self.wind_timer) * 1.5  # Scale to keep wind magnitude reasonable
            gust = random.uniform(-10.0, 45.0)
            
            # INNOVATION: Simulated Earthquake in the final 3 seconds
            quake = 0.0
            if self.wind_timer < 3.0:
                 quake = math.sin(time.time() * 20) * 15.0
                 self.offset_x = WIDTH // 2 - (self.grid_w * self.grid_size) // 2 + quake
            
            self.wind_force = clamp(base_wind + gust, 0.0, 200.0)
            
            # Physics Simulation
            # 1. Connectivity Check (Gravity)
            connected = set()
            queue = [b for b in self.blocks if b.get("fixed")]
            for start in queue:
                connected.add((start["gx"], start["gy"]))
            
            # BFS for gravity
            q_bfs = list(connected)
            head = 0
            while head < len(q_bfs):
                curr = q_bfs[head]; head+=1
                cx, cy = curr
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = cx+dx, cy+dy
                    if (nx, ny) not in connected:
                        # Check if block exists there
                        found = False
                        for b in self.blocks:
                            if b["gx"] == nx and b["gy"] == ny:
                                found = True
                                break
                        if found:
                            connected.add((nx, ny))
                            q_bfs.append((nx, ny))

            # 2. Wind Stress & Shear Failure
            surviving = []
            failed_msg = ""
            
            for b in self.blocks:
                if (b["gx"], b["gy"]) not in connected:
                    # Gravity fall
                    continue
                
                if b.get("fixed"):
                    surviving.append(b)
                    continue

                # Wind Drag Calculation
                # Higher blocks get more wind
                height_factor = (self.grid_h - b["gy"]) / self.grid_h # 0 to 1
                drag = self.wind_force * (0.5 + height_factor * 1.5)
                
                # Material Strength
                mat_type = b["type"]
                strength = 60.0 # Default
                if mat_type == "Lobby": strength = 45.0
                elif mat_type == "Books": strength = 80.0 # Heavy
                elif mat_type == "Eco-Roof": strength = 20.0 # Fragile
                elif mat_type == "Elevator": strength = 120.0 # Strong core
                
                # Support Bonus (Neighbors reinforce)
                neighbors = 0
                for other in self.blocks:
                    if abs(other["gx"] - b["gx"]) + abs(other["gy"] - b["gy"]) == 1:
                        neighbors += 1
                
                strength += neighbors * 15.0
                
                # Failure Check
                # Stress accumulates over time? Or instant snap?
                # Let's use probabilistic snap based on (Drag / Strength)
                ratio = drag / (strength + 1.0)
                
                if ratio > 1.2: # Immediate break
                    pass
                elif ratio > 0.8 and random.random() < dt * 0.5: # Stress fracture
                    pass
                else:
                    surviving.append(b)
            
            if len(self.blocks) != len(surviving):
                self.stability -= (len(self.blocks) - len(surviving)) * 5.0
            
            self.blocks = surviving
            
            if self.wind_timer <= 0:
                # Validation
                count = len(self.blocks)
                has_roof = any(b["type"] == "Eco-Roof" for b in self.blocks)
                if self.stability > 0 and count > 10 and has_roof:
                     self.finished = True
                     self.success = True
                     
                     if self.stability >= 95: self.grade = "S"
                     elif self.stability >= 80: self.grade = "A"
                     elif self.stability >= 60: self.grade = "B"
                     else: self.grade = "C"
                     
                     self.message = f"Design Verified. Integrity: {int(self.stability)}%"
                else:
                     self.finished = True
                     self.success = False
                     reason = "Collapsed" if count <= 10 else "Missing Eco-Roof"
                     self.message = f"Test Failed: {reason}."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        # Background
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#87ceeb", outline="") # Sky
        canvas.create_rectangle(0, HEIGHT-100, WIDTH, HEIGHT, fill="#deb887", outline="") # Ground
        
        # Grid
        for i in range(self.grid_w + 1):
            x = self.offset_x + i * self.grid_size
            canvas.create_line(x, self.offset_y, x, self.offset_y + self.grid_h * self.grid_size, fill="#ccc")
        for i in range(self.grid_h + 1):
            y = self.offset_y + i * self.grid_size
            canvas.create_line(self.offset_x, y, self.offset_x + self.grid_w * self.grid_size, y, fill="#ccc")
            
        # Blocks
        for b in self.blocks:
            x = self.offset_x + b["gx"] * self.grid_size
            y = self.offset_y + b["gy"] * self.grid_size
            color = b.get("color", "#555")
            canvas.create_rectangle(x+2, y+2, x+self.grid_size-2, y+self.grid_size-2, fill=color, outline="#333", width=2)
            
        # Player
        if self.phase == "build":
            player.draw(canvas)
            # Highlight cursor
            gx = int((player.x - self.offset_x) // self.grid_size)
            gy = int((player.y - self.offset_y) // self.grid_size)
            if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
                x = self.offset_x + gx * self.grid_size
                y = self.offset_y + gy * self.grid_size
                canvas.create_rectangle(x, y, x+self.grid_size, y+self.grid_size, outline="#ff0", width=3)
                
        # HUD
        canvas.create_text(20, 20, anchor="w", text=f"Budget: ${self.budget}", font=("Helvetica", 16, "bold"), fill="#000")
        
        if self.phase == "build":
            canvas.create_text(WIDTH/2, 30, text="1: Lobby($10)  2: Books($15)  3: Eco-Roof($20)  4: Elevator($25)", font=("Helvetica", 12), fill="#000")
            canvas.create_text(WIDTH/2, 50, text=f"Selected: {self.room_types[self.selected_room]['name']} - Press SPACE to Build, ENTER to Test", font=("Helvetica", 12, "bold"), fill="#000")
        else:
            canvas.create_text(WIDTH/2, 50, text=f"WIND TEST: {int(self.wind_force)} mph", font=("Helvetica", 16, "bold"), fill="#d00")

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
