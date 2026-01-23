import tkinter as tk
from ..utils import WIDTH, HEIGHT, TEXT
from ..player import Player

class BaseWorld:
    def __init__(self, name: str, summary: str, duration: float) -> None:
        self.name = name
        self.summary = summary
        self.duration = duration
        self.timer = duration
        self.finished = False
        self.success = False
        self.message = ""
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

    def reset(self, player: Player) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str]) -> None:  # pragma: no cover - interface
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

    def draw_hud(self, canvas: tk.Canvas) -> None:
        # HUD Background Bar for better contrast
        canvas.create_rectangle(0, 0, WIDTH, 50, fill="#000000", outline="", stipple="gray50") # Semi-transparent effect via stipple if alpha not supported

        canvas.create_text(
            20,
            25,
            anchor="w",
            fill=TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"{self.name}   |   {self.summary}",
        )
        
        # Draw Hint in Center
        # if self.hints:
        #      hint_text = self.hints[self.current_hint_index]
        #      canvas.create_text(
        #          WIDTH / 2,
        #          25,
        #          anchor="center",
        #          fill="#ffff00", 
        #          font=("Helvetica", 12, "italic"),
        #          text=hint_text
        #      )

        canvas.create_text(
            WIDTH - 20,
            25,
            anchor="e",
            fill=TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"Time: {self.timer:05.1f}s",
        )
    
    def draw_result(self, canvas: tk.Canvas) -> None:
        # Default result screen if not overridden
        color = "#50fa7b" if self.success else "#ff5555"
        canvas.create_rectangle(WIDTH / 2 - 240, HEIGHT / 2 - 80, WIDTH / 2 + 240, HEIGHT / 2 + 80, fill="#222b3b", outline=color, width=3)
        
        msg = self.message
        if self.success and self.grade != "-":
            msg += f" | Rank: {self.grade}"
            
        canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text=msg, fill=TEXT, font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, HEIGHT / 2 + 30, text="Press SPACE to return to the career hub.", fill="#d0ffe2", font=("Helvetica", 12, "bold"))
