import tkinter as tk
import time
from .utils import WIDTH, HEIGHT, BG
from .player import Player
from .worlds.base import BaseWorld
from .worlds.fire_rescue import FireRescueWorld
from .worlds.chef_rush import ChefRushWorld
from .worlds.bug_hunt import BugHuntWorld
from .worlds.marine import MarineWorld
from .worlds.architect import ArchitectWorld
from .worlds.doctor import DoctorWorld

from .save_system import SaveSystem

# We will import new worlds here later

class GameEngine:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Career Worlds")
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.player = Player()
        self.save_system = SaveSystem()
        
        self.worlds: dict[str, BaseWorld] = {
            "1": FireRescueWorld(),
            "2": ChefRushWorld(),
            "3": BugHuntWorld(),
            "4": MarineWorld(),
            "5": ArchitectWorld(),
            "6": DoctorWorld(),

        }
        
        self.active_world: BaseWorld | None = None
        self.state = "menu"
        self.message = "Use WASD or arrow keys. Press keys to enter a career world."
        self.keys: set[str] = set()
        self.last_time = time.time()
        
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_click)

    def on_key_press(self, event: tk.Event) -> None:
        self.keys.add(event.keysym)
        if self.state == "menu":
            if event.keysym in self.worlds:
                self.start_world(event.keysym)
            elif event.keysym == "m":
                self.start_military_mission()
        if "result" in self.state and event.keysym == "space":
            self.return_to_menu()
        if self.state == "endgame" and event.keysym == "space":
             pass # Exit or reset?

        # Global Escape
        if event.keysym == "Escape":
            if self.state == "world" or self.state == "military":
                 self.active_world.finished = True
                 self.active_world.success = False
                 self.active_world.message = "Mission Aborted."
                 # Let the loop handle the transition to result screen naturally or:
                 self.state = "menu" 
                 self.active_world = None
                 self.message = "Mission Aborted."
            elif "result" in self.state or self.state == "endgame":
                 self.return_to_menu()

    def on_key_release(self, event: tk.Event) -> None:
        self.keys.discard(event.keysym)

    def on_click(self, event: tk.Event) -> None:
        if self.state != "menu":
            return
            
        keys = ["1", "2", "3", "4", "5", "6"]
        start_x = 100
        start_y = 160
        gap_x = 200
        gap_y = 120
        
        for i, key in enumerate(keys):
            if key not in self.worlds: continue
            
            col = i % 4
            row = i // 4
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            
            if x <= event.x <= x + 180 and y <= event.y <= y + 100:
                self.start_world(key)
                return

    def start_world(self, key: str) -> None:
        self.active_world = self.worlds[key]
        self.active_world.reset(self.player) # Default difficulty 0
        self.state = "world"
        self.message = ""

    def start_military_mission(self) -> None:
        if not self.save_system.data["military_unlocked"]:
            self.message = "LOCKED. Complete 6 career professions first."
            return
            
        rank = self.save_system.get_rank()
        if "Master" in rank:
            self.state = "endgame"
            return
            
        # Select random world for mission
        import random
        key = random.choice(list(self.worlds.keys()))
        self.start_world(key)
        self.active_world.name = f"MISSION: {self.active_world.name}"
        
        # Difficulty Scaling based on Rank Index
        rank_idx = self.save_system.data["rank_index"]
        self.active_world.reset(self.player, difficulty=rank_idx)
        
        # Additional Duration constraint is now handled inside world.reset usually, 
        # but we can keep the global 0.8x multiplier as an extra challenge if desired.
        # Let's rely on the per-world scaling for now, or keep it slight.
        self.active_world.duration *= 0.9 
        self.active_world.timer = self.active_world.duration
        
        self.state = "military"

    def return_to_menu(self) -> None:
        if self.active_world:
             # Career Mode Result
             if self.state == "result_career" and self.active_world.success:
                 # Find key associated with world
                 for k, v in self.worlds.items():
                     if v == self.active_world:
                         self.save_system.mark_world_complete(k)
                         break
             
             # Boss Level Mode Result
             if self.state == "result_boss":
                 if self.active_world.success:
                     # Log Mission
                     duration = self.active_world.duration - self.active_world.timer
                     self.save_system.log_mission(self.active_world.name, duration, True)
                     
                     promoted = self.save_system.promote()
                     if promoted:
                         self.message = f"PROMOTED! New Rank: {self.save_system.get_rank()}"
                     else:
                        self.state = "endgame" # Master reached
                 else:
                     duration = self.active_world.duration - self.active_world.timer
                     self.save_system.log_mission(self.active_world.name, duration, False)
                     self.save_system.demote_reset()
                     self.message = "BOSS MISSION FAILED. Rank Reset to Noob."

        self.state = "menu"
        self.active_world = None
        if self.state != "endgame":
             r = self.save_system.get_rank()
             self.message = f"Rank: {r} | Pick a portal"

    def loop(self) -> None:
        now = time.time()
        dt = min(0.1, now - self.last_time)
        self.last_time = now
        
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "endgame":
            self.draw_endgame()
        elif (self.state == "world" or self.state == "military") and self.active_world:
            self.active_world.update(dt, self.canvas, self.player, self.keys)
            if self.active_world.finished:
                # Transition to specific result state to preserve mode context
                if self.state == "military":
                    self.state = "result_boss"
                else:
                    self.state = "result_career"
        elif "result" in self.state and self.active_world:
            self.active_world.draw(self.canvas, self.player)
            
        self.root.after(16, self.loop)

    def draw_menu(self) -> None:
        self.canvas.delete("all")
        # Background
        for i in range(8):
            shade = 18 + i * 5
            self.canvas.create_rectangle(
                0, i * (HEIGHT / 8), WIDTH, (i + 1) * (HEIGHT / 8),
                fill=f"#{shade:02x}{(shade+10):02x}{(shade+18):02x}", outline=""
            )
        
        # Header
        self.canvas.create_text(WIDTH / 2, 60, text="Career Worlds Hub", fill="#8ce1ff", font=("Helvetica", 28, "bold"))
        self.canvas.create_text(WIDTH / 2, 90, text="Jump into a mini-world and try the job for yourself.", fill="#d8e7ff", font=("Helvetica", 14))
        
        # Boss Level Status
        rank = self.save_system.get_rank()
        if self.save_system.data["military_unlocked"]:
            color = "#ffd700"
            txt = f"BOSS LEVEL ACTIVE - {rank} - Press 'M' for Mission"
        else:
            color = "#777"
            comp = len(self.save_system.data["completed_worlds"])
            txt = f"Boss Level Locked ({comp}/6 Professions Mastered)"
            
        self.canvas.create_text(WIDTH/2, 120, text=txt, fill=color, font=("Helvetica", 12, "bold"))
        
        # Portals List Compact
        portals = [
            ("1", "Firefighter", "#23486e"), ("2", "Chef", "#25563f"),
            ("3", "Engineer", "#50346e"), ("4", "Marine Bio", "#008b8b"),
            ("5", "Architect", "#cd853f"), ("6", "Doctor", "#ff69b4")
        ]
        
        # Grid layout for portals 4x2
        start_x = 100
        start_y = 160
        gap_x = 200
        gap_y = 120
        
        for i, (key, title, color) in enumerate(portals):
            col = i % 4
            row = i // 4
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            
            completed = key in self.save_system.data["completed_worlds"]
            outline = "#0f0" if completed else "#666"
            
            self.canvas.create_rectangle(x, y, x+180, y+100, fill=color, outline=outline, width=3)
            self.canvas.create_text(x+90, y+50, text=f"[{key}]\n{title}", fill="#fff", font=("Helvetica", 12, "bold"), justify="center")

        # Footer
        self.canvas.create_text(WIDTH / 2, HEIGHT - 40, text=self.message, fill="#b9c7e6", font=("Helvetica", 12, "bold"))

    def draw_endgame(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(0,0,WIDTH,HEIGHT, fill="#000")
        
        self.canvas.create_text(WIDTH/2, 50, text="HALL OF MASTERS", fill="#ffd700", font=("Helvetica", 32, "bold"))
        self.canvas.create_text(WIDTH/2, 100, text="CONGRATULATIONS.", fill="#fff", font=("Helvetica", 18))
        self.canvas.create_text(WIDTH/2, 140, text="You have mastered every profession and reached:", fill="#aaa", font=("Helvetica", 14))
        self.canvas.create_text(WIDTH/2, 180, text="MASTER RANK", fill="#ffd700", font=("Helvetica", 28, "bold"))
        
        # Mission Report
        history = self.save_system.data.get("military_history", [])
        start_y = 240
        self.canvas.create_text(WIDTH/2, 220, text="--- MISSION REPORT ---", fill="#0f0", font=("Helvetica", 14, "bold"))
        
        # Display last 10 entries to avoid overflow
        for i, entry in enumerate(history[-10:]):
            txt = f"{entry['rank']} | {entry['world']} | {entry['time']}s | {entry['outcome']}"
            self.canvas.create_text(WIDTH/2, start_y + i*25, text=txt, fill="#b9c7e6", font=("Courier", 12))
            
        # Footer
        self.canvas.create_text(WIDTH / 2, HEIGHT - 60, text="Press ESC to return to menu", fill="#777", font=("Helvetica", 12, "bold"))

    def run(self) -> None:
        self.last_time = time.time()
        self.loop()
        self.root.mainloop()
