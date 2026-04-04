from __future__ import annotations

import tkinter as tk

from src.utils import TEXT, WIDTH, clamp


def draw_bar(
    canvas: tk.Canvas,
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    value: float,
    label: str,
    fill: str,
    outline: str = "#0b1220",
    back: str = "#111827",
) -> None:
    value = clamp(value, 0.0, 100.0)
    canvas.create_rectangle(x, y, x + w, y + h, fill=back, outline=outline, width=2)
    canvas.create_rectangle(x + 2, y + 2, x + 2 + (w - 4) * (value / 100.0), y + h - 2, fill=fill, outline="")
    canvas.create_text(x + 10, y + h / 2, anchor="w", fill=TEXT, font=("Helvetica", 11, "bold"), text=f"{label}: {value:0.0f}")


def draw_toast(canvas: tk.Canvas, *, text: str, timer: float) -> None:
    if timer <= 0.0:
        return
    alpha = clamp(timer / 2.2, 0.0, 1.0)
    # Tkinter doesn't support alpha fill, so fake it with stipple.
    stipple = "gray25" if alpha < 0.6 else "gray12"
    w = min(680, max(320, 14 * len(text)))
    x1 = (WIDTH - w) / 2
    x2 = x1 + w
    y1 = 52
    y2 = 96
    canvas.create_rectangle(x1, y1, x2, y2, fill="#0b1220", outline="#5fb6ff", width=2, stipple=stipple)
    canvas.create_text(WIDTH / 2, (y1 + y2) / 2, fill="#e7f3ff", font=("Helvetica", 13, "bold"), text=text)


def draw_panic_banner(canvas: tk.Canvas, *, active: bool, intensity: float) -> None:
    if not active:
        return
    pulse = 0.55 + 0.45 * clamp(intensity, 0.0, 1.0)
    canvas.create_rectangle(0, 40, WIDTH, 44, fill="#ff2f2f", outline="", stipple="gray12" if pulse < 0.75 else "gray25")
    canvas.create_text(
        WIDTH / 2,
        62,
        fill="#ffdddd",
        font=("Helvetica", 16, "bold"),
        text="PANIC MODE: STABILIZE THE BUILD",
    )

