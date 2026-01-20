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
        if self.state == "result" and event.keysym == "space":
            self.return_to_menu()

        # Global Escape
        if event.keysym == "Escape":
            if self.state == "world":
                 self.active_world.finished = True
                 self.active_world.success = False
                 self.active_world.message = "Mission Aborted."
                 self.state = "menu" 
                 self.active_world = None
                 self.message = "Mission Aborted."
            elif self.state == "result":
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
        self.active_world.reset(self.player)
        self.state = "world"
        self.message = ""

    def return_to_menu(self) -> None:
        if self.active_world:
             # Save completion if successful
             if self.state == "result" and self.active_world.success:
                 # Find key associated with world
                 for k, v in self.worlds.items():
                     if v == self.active_world:
                         self.save_system.mark_world_complete(k)
                         break

        self.state = "menu"
        self.active_world = None
        comp = len(self.save_system.data["completed_worlds"])
        self.message = f"{comp}/6 Professions Mastered | Pick a portal"

    def loop(self) -> None:
        now = time.time()
        dt = min(0.1, now - self.last_time)
        self.last_time = now
        
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "world" and self.active_world:
            self.active_world.update(dt, self.canvas, self.player, self.keys)
            if self.active_world.finished:
                self.state = "result"
        elif self.state == "result" and self.active_world:
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

    def run(self) -> None:
        self.last_time = time.time()
        self.loop()
        self.root.mainloop()
