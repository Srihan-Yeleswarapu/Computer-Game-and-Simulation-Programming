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
import audioop  # raw audio processing helpers
import os
import wave
import tempfile

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
        
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_click)

    def on_key_press(self, event: tk.Event) -> None:
        self.keys.add(event.keysym)
        if self.state == "menu":
            if event.keysym in self.worlds:
                self.start_world(event.keysym)
            if event.keysym.lower() == "h":
                self.high_contrast = not self.high_contrast
                self.draw_menu()

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
        
        if self.high_contrast:
            # High Contrast Mode (Black BG, Yellow/White Text)
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000")
            
            # Header
            self.canvas.create_text(WIDTH / 2, 60, text="Career Worlds Hub", fill="#FFFF00", font=("Helvetica", 28, "bold"))
            self.canvas.create_text(WIDTH / 2, 90, text="High Contrast Mode Enabled (Press 'H' to toggle)", fill="#FFFFFF", font=("Helvetica", 14))
            
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
                outline = "#00FF00" if completed else "#FFFFFF" # Bright Green vs White
                
                self.canvas.create_rectangle(x, y, x+180, y+100, fill="#000000", outline=outline, width=5)
                self.canvas.create_text(x+90, y+50, text=f"[{key}]\n{title}", fill="#FFFFFF", font=("Helvetica", 14, "bold"), justify="center")

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
            self.canvas.create_text(WIDTH / 2, 90, text="Jump into a mini-world and try the job for yourself. (Press 'H' for High Contrast)", fill="#d8e7ff", font=("Helvetica", 14))
            
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
        def start_music(self):
            # Start background music if supported.
            if self._music_started:
                return
            try:
                import winsound
            except ImportError:
                return
    
            # Load and loop the background track if available.
            music_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "backgroundMusic.m4a")
            )
            if not os.path.exists(music_path):
                return
    
            faded_path = self.create_faded_wav(music_path, fade_seconds=6, volume_scale=0.5)
            if not faded_path:
                return
            self._music_temp_path = faded_path
            self._music_started = True
            winsound.PlaySound(self._music_temp_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)

    def stop_music(self):
        # Stop playback and clean up temp files.
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except ImportError:
            pass
        if self._music_temp_path and os.path.exists(self._music_temp_path):
            try:
                os.remove(self._music_temp_path)
            except OSError:
                pass
        self._music_temp_path = None
        self._music_started = False

    def create_faded_wav(self, input_path: str, fade_seconds: int = 3, volume_scale: float = 1.0):
        # Read a wav file and apply fade-in/out for smoother looping.
        try:
            with wave.open(input_path, "rb") as wf:
                params = wf.getparams()
                frames = wf.readframes(wf.getnframes())
        except (wave.Error, FileNotFoundError):
            return None

        # Apply a fade-in/out and optional volume scaling to avoid harsh loops.
        frame_bytes = params.sampwidth * params.nchannels
        if frame_bytes <= 0:
            return None

        total_frames = params.nframes
        fade_frames = int(params.framerate * fade_seconds)
        fade_frames = min(fade_frames, max(0, total_frames // 2))
        if fade_frames <= 0:
            return input_path

        # Convert frames to a mutable bytearray for processing.
        data = bytearray(frames)
        volume_scale = max(0.0, min(volume_scale, 1.0))

        # Fade in.
        for i in range(fade_frames):
            scale = (i / fade_frames) * volume_scale
            start = i * frame_bytes
            end = start + frame_bytes
            data[start:end] = audioop.mul(data[start:end], params.sampwidth, scale)

        # Fade out.
        for i in range(fade_frames):
            scale = ((fade_frames - i) / fade_frames) * volume_scale
            start = (total_frames - fade_frames + i) * frame_bytes
            end = start + frame_bytes
            data[start:end] = audioop.mul(data[start:end], params.sampwidth, scale)

        # Apply mid-section scaling if requested.
        if volume_scale < 1.0:
            mid_start = fade_frames * frame_bytes
            mid_end = (total_frames - fade_frames) * frame_bytes
            if mid_end > mid_start:
                data[mid_start:mid_end] = audioop.mul(
                    data[mid_start:mid_end], params.sampwidth, volume_scale
                )

        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
            os.close(temp_fd)
            # Write the processed audio to a temp file.
            with wave.open(temp_path, "wb") as wf:
                wf.setparams(params)
                wf.writeframes(bytes(data))
            return temp_path
        except OSError:
            return None
            
    def run(self) -> None:
        self.last_time = time.time()
        self.loop()
        self.root.mainloop()
