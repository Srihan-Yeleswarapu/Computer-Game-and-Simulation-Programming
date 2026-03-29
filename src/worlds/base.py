import tkinter as tk
import random
from typing import Set
from src.utils import WIDTH, HEIGHT, TEXT, Particle, ACCENT, DANGER, SUCCESS
from src.player import Player

class BaseWorld:
    def __init__(self, name: str, summary: str, duration: float) -> None:
        self.name = name
        self.summary = summary
        self.duration = duration
        self.timer = duration
        self.finished = False
        self.success = False
        self.message = ""
        self.briefing = ["This is your task.", "Complete it skillfully."]
        self.bounds: tuple[float, float, float, float] = (0.0, 0.0, WIDTH, HEIGHT)
        self.warning = ""
        self.hints = [
            "Tip: Use WASD or Arrow Keys to move.",
            "Tip: Watch the timer in the top right!",
            "Tip: Complete the objective to win.",
            "Tip: Press ESC to abort the mission."
        ]
        self.grade = "-"
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.high_contrast = False
        self.particles: list[Particle] = []
        self.shake = 0.0
        self.keys: Set[str] = set()

    def reset(self, player: Player) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def tick_timer(self, dt: float) -> None:
        if self.finished:
            return
        self.timer = max(0.0, self.timer - dt)
        if self.timer <= 0.0:
            self.finished = True
            self.success = False
            self.message = "Time ran out!"
        
        # Cycle hints every 4 seconds
        self.hint_display_timer += dt
        if self.hint_display_timer > 4.0:
            self.hint_display_timer = 0.0
            self.current_hint_index = (self.current_hint_index + 1) % len(self.hints)

    def update_particles(self, dt: float):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead()]
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 20)

    def calculate_grade(self) -> str:
        # Override if world set a specific grade
        if self.grade != "-": return self.grade
        
        # Generic grading based on time remaining
        if not self.success: return "-"
        ratio = self.timer / self.duration
        if ratio > 0.6: return "S"
        if ratio > 0.4: return "A"
        if ratio > 0.2: return "B"
        return "C"

    def draw_hud(self, canvas: tk.Canvas) -> None:
        # HUD Background Bar (Compact)
        bg_color = "#000000" if self.high_contrast else "#111111"
        canvas.create_rectangle(0, 0, WIDTH, 40, fill=bg_color, outline="")

        # Title on the left
        canvas.create_text(
            15,
            20,
            anchor="w",
            fill="#ffff00" if self.high_contrast else TEXT,
            font=("Helvetica", 14, "bold"),
            text=self.name,
        )
        
        # Draw Hint at the Bottom
        if self.hints:
             hint_text = self.hints[self.current_hint_index]
             canvas.create_text(
                 WIDTH / 2,
                 HEIGHT - 20,
                 anchor="center",
                 fill="#ffff00" if self.high_contrast else ACCENT, 
                 font=("Helvetica", 11, "italic"),
                 text=hint_text
             )

        # Timer on the right
        canvas.create_text(
            WIDTH - 15,
            20,
            anchor="e",
            fill="#ffffff" if self.high_contrast else TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"Time: {self.timer:05.1f}s",
        )
    
    def draw_particles(self, canvas: tk.Canvas):
        for p in self.particles:
            canvas.create_oval(p.x, p.y, p.x+p.size, p.y+p.size, fill=p.color, outline="")

    def draw_result(self, canvas: tk.Canvas) -> None:
        color = SUCCESS if self.success else DANGER
        if self.high_contrast: color = "#ffff00"
        
        canvas.create_rectangle(WIDTH / 2 - 240, HEIGHT / 2 - 80, WIDTH / 2 + 240, HEIGHT / 2 + 80, fill="#000000" if self.high_contrast else "#222b3b", outline=color, width=3)
        
        msg = self.message
        if self.success and self.grade != "-":
            msg += f" | Rank: {self.grade}"
            
        canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text=msg, fill=TEXT, font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, HEIGHT / 2 + 30, text="Press SPACE to return to the hub.", fill="#ffffff" if self.high_contrast else "#d0ffe2", font=("Helvetica", 12, "bold"))

    def draw_briefing(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000" if self.high_contrast else "#0a0d1a")
        
        # Scenario Header
        canvas.create_text(WIDTH/2, 100, text=f"CARRIER BRIEFING: {self.name}", fill="#ffff00" if self.high_contrast else ACCENT, font=("Helvetica", 24, "bold"))
        
        # Mission Context
        y = 200
        for line in self.briefing:
            canvas.create_text(WIDTH/2, y, text=line, fill=TEXT, font=("Helvetica", 14), width=600, justify="center")
            y += 40
            
        canvas.create_text(WIDTH/2, HEIGHT - 100, text="Press SPACE to begin the mission", fill="#ffffff" if self.high_contrast else SUCCESS, font=("Helvetica", 12, "bold"))
