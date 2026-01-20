import math
import tkinter as tk
from .utils import WIDTH, HEIGHT, lerp, clamp

class Player:
    def __init__(self) -> None:
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.size = 22
        self.speed = 260.0
        self.vx = 0.0
        self.vy = 0.0
        self.accel = 12.0

    def reset(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

    def update(self, dt: float, keys: set[str], bounds: tuple[float, float, float, float]) -> None:
        dx = (1 if "Right" in keys or "d" in keys else 0) - (
            1 if "Left" in keys or "a" in keys else 0
        )
        dy = (1 if "Down" in keys or "s" in keys else 0) - (
            1 if "Up" in keys or "w" in keys else 0
        )
        if dx or dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
        target_vx = dx * self.speed
        target_vy = dy * self.speed
        smooth = clamp(self.accel * dt, 0.0, 1.0)
        self.vx = lerp(self.vx, target_vx, smooth)
        self.vy = lerp(self.vy, target_vy, smooth)
        self.x += self.vx * dt
        self.y += self.vy * dt
        x1, y1, x2, y2 = bounds
        self.x = clamp(self.x, x1 + self.size, x2 - self.size)
        self.y = clamp(self.y, y1 + self.size, y2 - self.size)

    def draw(self, canvas: tk.Canvas) -> None:
        canvas.create_oval(
            self.x - self.size - 4,
            self.y - self.size + 6,
            self.x + self.size + 4,
            self.y + self.size + 8,
            fill="#0a2235",
            outline="",
        )
        canvas.create_rectangle(
            self.x - self.size,
            self.y - self.size,
            self.x + self.size,
            self.y + self.size,
            fill="#61dafb",
            outline="#0d8db6",
            width=2,
        )
