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

    def reset(self, player: Player, difficulty: int = 0) -> None:  # pragma: no cover - interface
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

    def draw_hud(self, canvas: tk.Canvas) -> None:
        canvas.create_text(
            20,
            20,
            anchor="w",
            fill=TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"{self.name}   |   {self.summary}",
        )
        canvas.create_text(
            WIDTH - 20,
            20,
            anchor="e",
            fill=TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"Time: {self.timer:05.1f}s",
        )
    
    def draw_result(self, canvas: tk.Canvas) -> None:
        # Default result screen if not overridden
        color = "#50fa7b" if self.success else "#ff5555"
        canvas.create_rectangle(WIDTH / 2 - 240, HEIGHT / 2 - 80, WIDTH / 2 + 240, HEIGHT / 2 + 80, fill="#222b3b", outline=color, width=3)
        canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text=self.message, fill=TEXT, font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, HEIGHT / 2 + 30, text="Press SPACE to return to the career hub.", fill="#d0ffe2", font=("Helvetica", 12, "bold"))
