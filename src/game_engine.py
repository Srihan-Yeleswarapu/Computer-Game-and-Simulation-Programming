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
import os
import pygame

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
        self.high_contrast = False
        self.mouse_x = 0
        self.mouse_y = 0
        
        self.descriptions = {
            "1": "Navigate a burning building, dodge flames, and carry survivors to safety.",
            "2": "Prepare raw ingredients and serve orders quickly in a chaotic kitchen.",
            "3": "Patch code nodes in sequence while dodging glitches.",
            "4": "Clean up the ocean and protect marine life.",
            "5": "Design and build structures according to blueprints.",
            "6": "Diagnose patients and administer treatments in a hospital."
        }
        
        pygame.mixer.init()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def on_mouse_move(self, event: tk.Event) -> None:
        self.mouse_x = event.x
        self.mouse_y = event.y

    def on_key_press(self, event: tk.Event) -> None:
        self.keys.add(event.keysym)
        if self.state == "menu":
            if event.keysym in self.worlds:
                self.start_world(event.keysym)
            if event.keysym.lower() == "h":
                self.high_contrast = not self.high_contrast
                self.draw_menu()
            if event.keysym == "?" or event.keysym == "slash":
                self.state = "help"

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
            elif self.state == "help":
                 self.state = "menu"
                 self.message = "Use WASD or arrow keys. Press keys to enter a career world."

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
                         self.save_system.mark_world_complete(k, self.active_world.grade)
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
        elif self.state == "help":
            self.draw_help()
            
        self.root.after(16, self.loop)

    def draw_menu(self) -> None:
        self.canvas.delete("all")
        
        if self.high_contrast:
            # High Contrast Mode (Black BG, Yellow/White Text)
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000")
            
            # Header
            self.canvas.create_text(WIDTH / 2, 60, text="Career Worlds Hub", fill="#FFFF00", font=("Helvetica", 28, "bold"))
            self.canvas.create_text(WIDTH / 2, 90, text="High Contrast Mode Enabled (Press 'H' to toggle | Press '?' for Help)", fill="#FFFFFF", font=("Helvetica", 14))
            
            portals = [
                ("1", "Firefighter"), ("2", "Chef"),
                ("3", "Engineer"), ("4", "Marine Bio"),
                ("5", "Architect"), ("6", "Doctor")
            ]
            
            # Grid layout for portals 4x2
            start_x = 100
            start_y = 160
            gap_x = 200
            gap_y = 120
            
            for i, (key, title) in enumerate(portals):
                col = i % 4
                row = i // 4
                x = start_x + col * gap_x
                y = start_y + row * gap_y
                
                completed = key in self.save_system.data["completed_worlds"]
                grade = self.save_system.data.get("world_grades", {}).get(key, "-")
                outline = "#00FF00" if completed else "#FFFFFF" # Bright Green vs White
                
                self.canvas.create_rectangle(x, y, x+180, y+100, fill="#000000", outline=outline, width=5)
                
                label = f"[{key}]\n{title}"
                if completed: label += f"\nRank: {grade}"
                
                self.canvas.create_text(x+90, y+50, text=label, fill="#FFFFFF", font=("Helvetica", 14, "bold"), justify="center")

            # Footer
            self.canvas.create_text(WIDTH / 2, HEIGHT - 40, text=self.message, fill="#FFFF00", font=("Helvetica", 14, "bold"))

        else:
            # Standard Aesthetic Mode
            # Background
            for i in range(8):
                shade = 18 + i * 5
                self.canvas.create_rectangle(
                    0, i * (HEIGHT / 8), WIDTH, (i + 1) * (HEIGHT / 8),
                    fill=f"#{shade:02x}{(shade+10):02x}{(shade+18):02x}", outline=""
                )
            
            # Header
            self.canvas.create_text(WIDTH / 2, 60, text="Career Worlds Hub", fill="#8ce1ff", font=("Helvetica", 28, "bold"))
            self.canvas.create_text(WIDTH / 2, 90, text="Jump into a mini-world and try the job for yourself. (Press 'H' for High Contrast | '?' for Help)", fill="#d8e7ff", font=("Helvetica", 14))
            
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
                grade = self.save_system.data.get("world_grades", {}).get(key, "-")
                outline = "#0f0" if completed else "#666"
                
                self.canvas.create_rectangle(x, y, x+180, y+100, fill=color, outline=outline, width=3)
                self.canvas.create_text(x+90, y+50, text=f"[{key}]\n{title}", fill="#fff", font=("Helvetica", 12, "bold"), justify="center")
                
                if completed:
                     # Draw Grade Badge
                     badges = {"S": "#ffd700", "A": "#c0c0c0", "B": "#cd7f32", "C": "#a0522d"}
                     badge_col = badges.get(grade, "#fff")
                     self.canvas.create_oval(x+140, y+60, x+170, y+90, fill=badge_col, outline="#fff", width=2)
                     self.canvas.create_text(x+155, y+75, text=grade, fill="#000", font=("Helvetica", 12, "bold"))

            # Footer
            self.canvas.create_text(WIDTH / 2, HEIGHT - 40, text=self.message, fill="#b9c7e6", font=("Helvetica", 12, "bold"))

            # Tooltip Logic
            self.draw_tooltips(portals, start_x, start_y, gap_x, gap_y)

    def draw_tooltips(self, portals, start_x, start_y, gap_x, gap_y):
        for i, (key, title, *_) in enumerate(portals):
            col = i % 4
            row = i // 4
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            
            if x <= self.mouse_x <= x + 180 and y <= self.mouse_y <= y + 100:
                desc = self.descriptions.get(key, "Explore this career.")
                # Draw tooltip box
                tx = self.mouse_x + 10
                ty = self.mouse_y + 10
                self.canvas.create_rectangle(tx, ty, tx + 300, ty + 60, fill="#111", outline="#fff", width=2)
                self.canvas.create_text(tx + 150, ty + 30, text=desc, fill="#fff", font=("Helvetica", 10), width=280)

    def draw_help(self) -> None:
        self.canvas.delete("all")
        # Background
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#1a1a2e")
        
        # Title
        self.canvas.create_text(WIDTH / 2, 80, text="How to Play", fill="#e94560", font=("Helvetica", 32, "bold"))
        
        # Content
        lines = [
            "Welcome to Career Worlds!",
            "",
            "Controls:",
            "- WASD or Arrow Keys: Move your character",
            "- SPACE: Interact (depends on career)",
            "- ESC: Return to Menu / Abort Mission",
            "- H: Toggle High Contrast Mode",
            "",
            "Objective:",
            "Choose a career portal from the main hub.",
            "Complete the mini-game task before time runs out.",
            "Master all 6 professions to win!",
            "",
            "Press ESC to return to the hub."
        ]
        
        start_y = 160
        for line in lines:
            self.canvas.create_text(WIDTH / 2, start_y, text=line, fill="#fff", font=("Helvetica", 16))
            start_y += 35
    def start_music(self):
        try:
            music_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "backgroundMusic.wav")
            )
            
            if not os.path.exists(music_path):
                print(f"Music file not found: {music_path}")
                return
            
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)
            print(f"Playing music: {music_path}")
        except Exception as e:
            print(f"Error playing music: {e}")

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
            print("Music stopped")
        except Exception as e:
            print(f"Error stopping music: {e}")

    def on_closing(self):
        self.stop_music()
        pygame.mixer.quit()
        self.root.destroy()
            
    def run(self) -> None:
        self.last_time = time.time()
        self.start_music()
        self.loop()
        self.root.mainloop()
