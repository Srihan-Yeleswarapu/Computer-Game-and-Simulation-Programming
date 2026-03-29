import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp, lerp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any, cast

class MarineWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Marine Biologist",
            summary="Dive, scan fish, and collect specimens while avoiding predators",
            duration=62.0,
        )
        self.briefing = [
             "RESEARCH MISSION: Deep-sea specimens are needed for a critical study.",
             "Scan rare fish and collect bioluminescent samples.",
             "Watch your Oxygen! Drains faster as you go deeper.",
             "BEWARE: Great White Sharks roam these waters!",
             "Look for hidden discoveries on the ocean floor."
        ]
        self.hints = [
             "Tip: Hold SPACE near a fish to scan it.",
             "Tip: Avoid RED sharks; they will bite your oxygen tank!",
             "Tip: Touch glowing discoveries for a research bonus.",
             "Tip: Scan 3 fish and collect 3 samples to complete the mission."
        ]
        self.bounds = (40.0, 40.0, WIDTH - 40.0, HEIGHT - 40.0)
        self.fish: list[dict[str, Any]] = []
        self.sharks: list[dict[str, Any]] = []
        self.samples: list[dict[str, Any]] = []
        self.discoveries: list[dict[str, Any]] = []
        self.bubbles: list[dict[str, Any]] = []
        self.oxygen = 100.0
        self.scanned_count = 0
        self.collected_count = 0
        
        self.scan_target: dict | None = None
        self.scan_timer = 0.0
        self.discovery_msg = ""
        self.msg_timer = 0.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, 80)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.oxygen = 100.0
        self.scanned_count = 0
        self.collected_count = 0
        self.scan_timer = 0.0
        self.discovery_msg = ""
        self.msg_timer = 0.0
        self.shake = 0.0
        
        # Populate
        self.fish = []
        species = [{"name": "Tang", "c": "#1e90ff"}, {"name": "Turtle", "c": "#32cd32"}, {"name": "Jelly", "c": "#e6e6fa"}]
        for _ in range(6):
            s = random.choice(species)
            self.fish.append({
                "x": random.uniform(100, WIDTH-100), "y": random.uniform(200, HEIGHT-150),
                "dx": random.choice([-1, 1]) * random.uniform(50, 90), "dy": random.uniform(-20, 20),
                "color": s["c"], "scanned": False, "w": 40
            })
        
        self.sharks = []
        for _ in range(2):
            self.sharks.append({
                "x": random.uniform(100, WIDTH-100), "y": random.uniform(300, HEIGHT-100),
                "dx": random.choice([-1, 1]) * 120, "dy": 0, "w": 60
            })

        self.samples = []
        for _ in range(3):
            self.samples.append({"x": random.uniform(100, WIDTH-100), "y": HEIGHT-70, "collected": False})
            
        self.discoveries = [
            {"x": 150, "y": HEIGHT-65, "name": "Sunken Anchor", "found": False, "msg": "An old pirate anchor!"},
            {"x": WIDTH-200, "y": HEIGHT-65, "name": "Giant Clam", "found": False, "msg": "Look at the size of that pearl!"}
        ]

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        
        # tick_timer handled by engine
        if self.tutorial_timer > 0:
            self.draw(canvas, player)
            return
            
        player.update(dt, keys, self.bounds)
        
        # Buoyancy
        if "Down" not in keys and "s" not in keys: player.vy -= 80 * dt
        player.vx = clamp(player.vx, -200, 200)
        player.vy = clamp(player.vy, -200, 200)

        # Oxygen
        depth_factor = 1.0 + (player.y / HEIGHT)
        self.oxygen = max(0.0, self.oxygen - dt * 2.0 * depth_factor)
        
        # Fish & Sharks
        x1, y1, x2, y2 = self.bounds
        for f in self.fish:
            f["x"] += f["dx"] * dt
            if f["x"] < x1 or f["x"] > x2: f["dx"] *= -1
        
        for s in self.sharks:
            s["x"] += s["dx"] * dt
            if s["x"] < x1 or s["x"] > x2: s["dx"] *= -1
            
            # Shark Bite Logic
            dist = math.hypot(player.x - s["x"], player.y - s["y"])
            if dist < 50:
                 # Check for recent bite to prevent instant death
                 if not s.get("bite_cooldown", 0) > 0:
                      self.oxygen = max(0.0, self.oxygen - 15.0) # BIG HIT
                      self.shake = 8.0
                      s["bite_cooldown"] = 2.0 # Wait 2s before biting again
            
            if s.get("bite_cooldown", 0) > 0:
                 s["bite_cooldown"] -= dt

        # Scanning
        self.scan_target = None
        for f in self.fish:
            if math.hypot(player.x - f["x"], player.y - f["y"]) < 80 and not f["scanned"]:
                self.scan_target = f
                if "space" in keys:
                    self.scan_timer += dt
                    if self.scan_timer > 1.2:
                        f["scanned"] = True
                        self.scanned_count += 1
                        self.scan_timer = 0
                break
        else: self.scan_timer = 0

        # Samples
        for s in self.samples:
            if not s["collected"] and math.hypot(player.x - s["x"], player.y - s["y"]) < 40:
                s["collected"] = True
                self.collected_count += 1
        
        # Discoveries
        for d in self.discoveries:
            if not d["found"] and math.hypot(player.x - d["x"], player.y - d["y"]) < 50:
                d["found"] = True
                self.discovery_msg = d["msg"]
                self.msg_timer = 3.0
                self.oxygen = min(100.0, self.oxygen + 15.0)

        if self.msg_timer > 0: self.msg_timer -= dt

        if self.collected_count >= 3 and self.scanned_count >= 3:
            self.finished = True
            self.success = True
            if self.oxygen > 60: self.grade = "S"
            elif self.oxygen > 40: self.grade = "A"
            else: self.grade = "B"
            self.message = "Mission Success! Marine data uploaded."

        if self.timer <= 0:
             self.finished = True
             self.success = self.collected_count + self.scanned_count >= 2
             if self.success:
                 self.message = f"Shift Over! Data uploaded: {self.scanned_count} scans & {self.collected_count} samples."
                 self.grade = self.calculate_grade()
             else:
                 self.message = "Expedition failure! Too little data collected before blackout."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        # Water
        for i in range(5):
             shade = 180 - i*30
             canvas.create_rectangle(0, i*(HEIGHT/5), WIDTH, (i+1)*(HEIGHT/5), fill=f"#00{shade:02x}ff", outline="")
        canvas.create_rectangle(0, HEIGHT-60, WIDTH, HEIGHT, fill="#d2b48c") # Seabed

        for d in self.discoveries:
             color = "#f1c40f" if not d["found"] else "#7f8c8d"
             canvas.create_text(d["x"], d["y"], text="?", fill=color, font=("Arial", 20, "bold"))
        
        for s in self.samples:
            if not s["collected"]:
                 canvas.create_oval(s["x"]-10, s["y"]-10, s["x"]+10, s["y"]+10, fill="#9b59b6", outline="#fff")
        
        for f in self.fish:
             canvas.create_oval(f["x"]-f["w"]/2, f["y"]-10, f["x"]+f["w"]/2, f["y"]+10, fill=f["color"])
             if f["scanned"]: canvas.create_text(f["x"], f["y"]-20, text="SCAN", fill="#2ecc71", font=("Arial", 8, "bold"))

        for s in self.sharks:
             sx_p, sy_p = s["x"], s["y"]
             # Shark Body
             canvas.create_oval(sx_p-s["w"]/2, sy_p-20, sx_p+s["w"]/2, sy_p+20, fill="#ff4757", outline="#000")
             # Tail
             tail_dir = -1 if s["dx"] > 0 else 1
             canvas.create_polygon(sx_p + tail_dir*s["w"]/2, sy_p, sx_p + tail_dir*(s["w"]/2+20), sy_p-15, sx_p + tail_dir*(s["w"]/2+20), sy_p+15, fill="#ff4757", outline="#000")
             # Dorsal Fin
             canvas.create_polygon(sx_p-10, sy_p-15, sx_p+10, sy_p-15, sx_p, sy_p-40, fill="#ff4757", outline="#000")

        player.draw(canvas)
        
        # Scanning Progress Bar
        if self.scan_target and "space" in self.keys:
             canvas.create_rectangle(player.x-30, player.y+35, player.x+30, player.y+42, fill="#333", outline="#fff")
             canvas.create_rectangle(player.x-28, player.y+37, player.x-28 + 56 * (self.scan_timer/1.2), player.y+40, fill="#2ecc71", outline="")
             canvas.create_text(player.x, player.y+50, text="SCANNING...", fill="#fff", font=("Arial", 8, "bold"))

        # Discovery Bubble
        if self.msg_timer > 0:
             canvas.create_rectangle(player.x-60, player.y-90, player.x+60, player.y-50, fill="#fff", outline="#000")
             canvas.create_text(player.x, player.y-70, text=self.discovery_msg, fill="#000", font=("Arial", 8))

        # HUD
        canvas.create_rectangle(20, HEIGHT-40, 220, HEIGHT-20, outline="#fff")
        canvas.create_rectangle(22, HEIGHT-38, 22+196*(self.oxygen/100), HEIGHT-22, fill="#0af")
        canvas.create_text(WIDTH-100, 80, text=f"Scans: {self.scanned_count}/3", fill="#fff", font=("Arial", 12, "bold"))
        canvas.create_text(WIDTH-100, 105, text=f"Samples: {self.collected_count}/3", fill="#fff", font=("Arial", 12, "bold"))

        if self.finished: self.draw_result(canvas)
        self.draw_hud(canvas)
