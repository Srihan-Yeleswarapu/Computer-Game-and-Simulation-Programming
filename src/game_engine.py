import tkinter as tk
import time
import math
from typing import Any
from src.utils import WIDTH, HEIGHT, BG
from src.player import Player
from src.worlds.base import BaseWorld
from src.worlds.fire_rescue import FireRescueWorld
from src.worlds.chef_rush import ChefRushWorld
from src.worlds.bug_hunt import BugHuntWorld
from src.worlds.marine import MarineWorld
from src.worlds.architect import ArchitectWorld
from src.worlds.doctor import DoctorWorld
from src.worlds.atc import ATCWorld
import os
import pygame

from src.save_system import SaveSystem

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
            "7": ATCWorld(),
        }
        
        self.active_world: BaseWorld | None = None
        self.state = "title" # Start at title screen
        self.message = "Use WASD or arrow keys. Press keys to enter a career world."
        self.keys: set[str] = set()
        self.last_time = time.time()
        self.high_contrast = False
        self.debug_mode = False
        self.fps = 0.0
        self.mouse_x = 0
        self.mouse_y = 0
        self.logo_img: tk.PhotoImage | None = None
        self.logo_path = os.path.join(os.path.dirname(__file__), "..", "career_worlds_logo_1774679748475.png")
        try:
             self.logo_img = tk.PhotoImage(file=self.logo_path)
        except:
             pass
        
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
        if self.state == "title" and event.keysym == "space":
            self.state = "menu"
            
        elif self.state == "menu":
            if event.keysym in self.worlds:
                self.start_world(event.keysym)
            if event.keysym.lower() == "h":
                self.high_contrast = not self.high_contrast
                self.draw_menu()
            if event.keysym == "?" or event.keysym == "slash":
                self.state = "help"
            if event.keysym == "F3":
                self.debug_mode = not self.debug_mode
        
        elif self.state == "briefing" and event.keysym == "space":
            self.state = "world"

        elif self.state == "result" and event.keysym == "space":
            self.return_to_menu()
            
        elif self.state == "victory" and event.keysym == "space":
            self.state = "menu"

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
        self.active_world.high_contrast = self.high_contrast
        self.state = "briefing"
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
        comp_count = len(self.save_system.data["completed_worlds"])
        
        # Check for Grand Finale
        if comp_count >= 7:
             all_b_or_higher = True
             ranks = {"S": 5, "A": 4, "B": 3, "C": 2, "-": 1}
             for w_id in self.worlds:
                 if ranks.get(self.save_system.data["world_grades"].get(w_id, "-"), 0) < 3:
                     all_b_or_higher = False
                     break
             if all_b_or_higher:
                 self.state = "victory"

        self.message = f"{comp_count}/7 Professions Mastered | Pick a portal"

    def loop(self, *args: Any) -> None:
        now = time.time()
        raw_dt = now - self.last_time
        dt = min(0.1, raw_dt)
        self.last_time = now
        self.fps = 1.0 / max(0.001, raw_dt)
        
        if self.state == "title":
            self.draw_title()
        elif self.state == "menu":
            self.draw_menu()
        elif self.state == "briefing" and self.active_world:
            self.active_world.draw_briefing(self.canvas)
        elif self.state == "world" and self.active_world:
            self.active_world.update(dt, self.canvas, self.player, self.keys, (self.mouse_x, self.mouse_y))
            if self.active_world.finished:
                self.active_world.grade = self.active_world.calculate_grade()
                self.state = "result"
        elif self.state == "result" and self.active_world:
            self.active_world.draw(self.canvas, self.player)
        elif self.state == "help":
            self.draw_help()
        elif self.state == "victory":
            self.draw_victory()
            
        if self.debug_mode:
            self.draw_debug()
            
        self.logo_path = os.path.join(os.path.dirname(__file__), "..", "career_worlds_logo_1774679748475.png")
        self.logo_img = None # Placeholder load
        try:
             self.logo_img = tk.PhotoImage(file=self.logo_path)
        except:
             pass

    def draw_title(self) -> None:
        self.canvas.delete("all")
        if self.logo_img:
             self.canvas.create_image(WIDTH/2, HEIGHT/2 - 100, image=self.logo_img)
        else:
             self.canvas.create_text(WIDTH/2, HEIGHT/2 - 50, text="CAREER WORLDS", fill="#5fb6ff", font=("Helvetica", 48, "bold"))
        
        pulse = abs(math.sin(time.time() * 2)) * 50
        self.canvas.create_text(WIDTH/2, HEIGHT/2 + 50, text="PRESS SPACE TO START", fill="#ffffff", font=("Helvetica", 14, "bold"), stipple="" if pulse > 25 else "gray50")
        
        if self.save_system.integrity_error:
             self.canvas.create_text(WIDTH/2, HEIGHT-40, text="[!] Save file signature mismatch. Progress reset.", fill="#ff4444", font=("Courier", 10))
        
    def draw_debug(self) -> None:
        debug_text = f"FPS: {self.fps:02.1f}\nState: {self.state}\nPos: {self.player.x:01f}, {self.player.y:01f}"
        self.canvas.create_text(10, HEIGHT - 10, anchor="sw", text=debug_text, fill="#00ff00", font=("Consolas", 10))

    def draw_victory(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#1a1c2c")
        self.canvas.create_text(WIDTH/2, HEIGHT/2 - 60, text="🏆 CAREER MASTER 🏆", fill="#ffb86c", font=("Helvetica", 40, "bold"))
        self.canvas.create_text(WIDTH/2, HEIGHT/2, text="You have mastered every profession with excellence!", fill="#ffffff", font=("Helvetica", 16))
        self.canvas.create_text(WIDTH/2, HEIGHT/2 + 100, text="Press SPACE to return to Hub", fill="#50fa7b", font=("Helvetica", 12, "bold"))

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
                ("5", "Architect"), ("6", "Doctor"),
                ("7", "ATC")
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
                ("5", "Architect", "#cd853f"), ("6", "Doctor", "#ff69b4"),
                ("7", "ATC", "#2e8b57")
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
            self.canvas.create_text(WIDTH / 2, HEIGHT - 25, text=self.message, fill="#b9c7e6", font=("Helvetica", 12, "bold"))

            # Tooltip Logic
            self.draw_tooltips(portals, start_x, start_y, gap_x, gap_y)

    def draw_tooltips(self, portals, start_x, start_y, gap_x, gap_y):
        for i, (key, title, *_) in enumerate(portals):
            col = i % 4
            row = i // 4
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            
            if x <= self.mouse_x <= x + 180 and y <= self.mouse_y <= y + 100:
                world_obj = self.worlds.get(key)
                desc = world_obj.summary if world_obj else "Explore this career."
                # Draw tooltip box
                tx = self.mouse_x + 10
                ty = self.mouse_y + 10
                grade = self.save_system.data.get("world_grades", {}).get(key, "-")
                self.canvas.create_rectangle(tx, ty, tx + 240, ty + 80, fill="#111", outline="#fff", width=2)
                self.canvas.create_text(tx + 120, ty + 20, text=f"{title} Mastery", fill="#5fb6ff", font=("Helvetica", 11, "bold"))
                self.canvas.create_text(tx + 120, ty + 45, text=f"Best Grade: {grade}", fill="#fff", font=("Helvetica", 10))
                self.canvas.create_text(tx + 120, ty + 65, text=desc, fill="#aaa", font=("Helvetica", 9), width=220)

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
            
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)
                print(f"Playing music: {music_path}")
            except pygame.error as e:
                print(f"Pygame music error: {e}")
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
