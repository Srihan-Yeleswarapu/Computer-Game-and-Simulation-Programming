import tkinter as tk
from typing import Set

from src.player import Player
from src.utils import ACCENT, DANGER, HEIGHT, Particle, SUCCESS, TEXT, WIDTH


class BaseWorld:
    def __init__(self, name: str, summary: str, duration: float) -> None:
        self.name = name
        self.summary = summary
        self.duration = duration
        self.timer = duration
        self.finished = False
        self.success = False
        self.message = ""
        self.auto_finish_on_timer = False
        self.briefing = ["This is your task.", "Complete it skillfully."]
        self.bounds: tuple[float, float, float, float] = (0.0, 0.0, WIDTH, HEIGHT)
        self.warning = ""
        self.hints = [
            "Tip: Use WASD or Arrow Keys to move.",
            "Tip: Watch the timer in the top right!",
            "Tip: Complete the objective to win.",
            "Tip: Press ESC to abort the mission.",
        ]
        self.grade = "-"
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.high_contrast = False
        self.particles: list[Particle] = []
        self.shake = 0.0
        self.keys: Set[str] = set()
        self._pressed: dict[str, bool] = {}

    def reset(self, player: Player) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def update(
        self,
        dt: float,
        canvas: tk.Canvas,
        player: Player,
        keys: set[str],
        mouse_pos: tuple[int, int],
    ) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def tick_timer(self, dt: float) -> None:
        if self.finished:
            return

        self.timer = max(0.0, self.timer - dt)
        if self.timer <= 0.0 and self.auto_finish_on_timer:
            self.finished = True
            self.success = False
            self.message = "Deadline reached! Performance evaluation required."

        self.hint_display_timer += dt
        if self.hint_display_timer > 3.0:
            self.hint_display_timer = 0.0
            self.current_hint_index = (self.current_hint_index + 1) % len(self.hints)

    def clear_input_state(self) -> None:
        self.keys.clear()
        self._pressed = {}

    def just_pressed(self, keys: set[str], key: str) -> bool:
        is_down = key in keys
        was_down = self._pressed.get(key, False)
        self._pressed[key] = is_down
        return is_down and not was_down

    def update_particles(self, dt: float) -> None:
        for particle in self.particles:
            particle.update(dt)
        self.particles = [particle for particle in self.particles if not particle.is_dead()]
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 20)

    def calculate_grade(self) -> str:
        if self.grade != "-":
            return self.grade
        if not self.success:
            return "-"

        ratio = self.timer / self.duration
        if ratio > 0.6:
            return "S"
        if ratio > 0.4:
            return "A"
        if ratio > 0.2:
            return "B"
        return "C"

    def draw_hud(self, canvas: tk.Canvas) -> None:
        bg_color = "#000000" if self.high_contrast else "#111111"
        canvas.create_rectangle(0, 0, WIDTH, 40, fill=bg_color, outline="")
        canvas.create_text(
            15,
            20,
            anchor="w",
            fill="#ffff00" if self.high_contrast else TEXT,
            font=("Helvetica", 14, "bold"),
            text=self.name,
        )

        if self.hints:
            hint_text = self.hints[self.current_hint_index]
            canvas.create_text(
                WIDTH / 2,
                HEIGHT - 20,
                anchor="center",
                fill="#ffff00" if self.high_contrast else ACCENT,
                font=("Helvetica", 11, "italic"),
                text=hint_text,
            )

        canvas.create_text(
            WIDTH - 15,
            20,
            anchor="e",
            fill="#ffffff" if self.high_contrast else TEXT,
            font=("Helvetica", 14, "bold"),
            text=f"Time: {self.timer:05.1f}s",
        )

    def draw_particles(self, canvas: tk.Canvas) -> None:
        for particle in self.particles:
            canvas.create_oval(
                particle.x,
                particle.y,
                particle.x + particle.size,
                particle.y + particle.size,
                fill=particle.color,
                outline="",
            )

    def draw_result(self, canvas: tk.Canvas) -> None:
        color = "#ffff00" if self.high_contrast else (SUCCESS if self.success else DANGER)
        panel_fill = "#000000" if self.high_contrast else "#172233"
        accent_fill = "#ffffff" if self.high_contrast else "#d8ecff"
        button_fill = "#ffff00" if self.high_contrast else "#8ff0a4"
        button_text = "#000000" if self.high_contrast else "#0d1b22"

        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000" if self.high_contrast else "#09111b", outline="")
        panel_top = 84
        panel_bottom = HEIGHT - 72
        canvas.create_rectangle(140, panel_top, WIDTH - 140, panel_bottom, fill=panel_fill, outline=color, width=3)
        canvas.create_text(
            WIDTH / 2,
            panel_top + 48,
            text="MISSION COMPLETE" if self.success else "MISSION REPORT",
            fill=color,
            font=("Helvetica", 22, "bold"),
        )

        rank_text = self.grade if self.grade != "-" else self.calculate_grade()
        rank_top = panel_top + 78
        canvas.create_rectangle(WIDTH / 2 - 54, rank_top, WIDTH / 2 + 54, rank_top + 66, fill="#0e1826", outline=color, width=2)
        canvas.create_text(WIDTH / 2, rank_top + 17, text="RANK", fill=accent_fill, font=("Helvetica", 10, "bold"))
        canvas.create_text(WIDTH / 2, rank_top + 47, text=rank_text, fill=color, font=("Helvetica", 26, "bold"))

        message = self.message or ("Objective complete." if self.success else "Objective failed.")
        canvas.create_text(
            WIDTH / 2,
            rank_top + 114,
            text=message,
            fill=accent_fill,
            font=("Helvetica", 13, "bold"),
            width=500,
            justify="center",
        )
        canvas.create_text(
            WIDTH / 2,
            rank_top + 168,
            text=f"Time Remaining: {self.timer:0.1f}s",
            fill="#bfd3e6" if not self.high_contrast else "#ffffff",
            font=("Helvetica", 12),
        )
        canvas.create_rectangle(WIDTH / 2 - 170, panel_bottom - 82, WIDTH / 2 + 170, panel_bottom - 34, fill=button_fill, outline="")
        canvas.create_text(
            WIDTH / 2,
            panel_bottom - 58,
            text="Press SPACE To Return To The Hub",
            fill=button_text,
            font=("Helvetica", 13, "bold"),
        )

    def draw_briefing(self, canvas: tk.Canvas) -> None:
        bg_fill = "#000000" if self.high_contrast else "#08111d"
        panel_fill = "#000000" if self.high_contrast else "#111d2d"
        outline = "#ffffff" if self.high_contrast else "#2e5d84"
        accent = "#ffff00" if self.high_contrast else ACCENT
        copy_fill = "#ffffff" if self.high_contrast else "#dce9f7"

        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg_fill, outline="")
        if not self.high_contrast:
            canvas.create_oval(-80, -40, 260, 280, fill="#12314d", outline="")
            canvas.create_oval(WIDTH - 320, HEIGHT - 280, WIDTH + 40, HEIGHT + 40, fill="#0d2942", outline="")

        panel_top = 54
        panel_bottom = HEIGHT - 58
        canvas.create_rectangle(94, panel_top, WIDTH - 94, panel_bottom, fill=panel_fill, outline=outline, width=2)
        canvas.create_text(WIDTH / 2, panel_top + 46, text="CAREER BRIEFING", fill=accent, font=("Helvetica", 13, "bold"))
        canvas.create_text(WIDTH / 2, panel_top + 90, text=self.name, fill=copy_fill, font=("Helvetica", 23, "bold"), width=560)
        canvas.create_text(
            WIDTH / 2,
            panel_top + 144,
            text=self.summary,
            fill="#9ec7e7" if not self.high_contrast else "#ffffff",
            font=("Helvetica", 12),
            width=500,
        )

        y = panel_top + 208
        for line in self.briefing:
            canvas.create_text(
                WIDTH / 2,
                y,
                text=line,
                fill=copy_fill,
                font=("Helvetica", 12),
                width=520,
                justify="center",
            )
            y += 36

        warning_y = min(y + 8, panel_bottom - 86)
        if self.warning:
            canvas.create_text(
                WIDTH / 2,
                warning_y,
                text=self.warning,
                fill="#ffd9a8" if not self.high_contrast else "#ffffff",
                font=("Helvetica", 11, "bold"),
                width=520,
                justify="center",
            )

        button_top = panel_bottom - 82
        button_bottom = panel_bottom - 30
        canvas.create_rectangle(WIDTH / 2 - 190, button_top, WIDTH / 2 + 190, button_bottom, fill=accent, outline="")
        canvas.create_text(
            WIDTH / 2,
            (button_top + button_bottom) / 2,
            text="Press SPACE To Begin The Mission",
            fill="#08111d" if not self.high_contrast else "#000000",
            font=("Helvetica", 13, "bold"),
        )
        canvas.create_text(
            WIDTH / 2,
            panel_bottom - 10,
            text="Esc will abort the run and return you to the hub.",
            fill="#9bbad6" if not self.high_contrast else "#ffffff",
            font=("Helvetica", 10),
        )
