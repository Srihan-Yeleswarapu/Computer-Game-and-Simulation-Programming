import math
import os
import time
import tkinter as tk
from typing import Any

import pygame

from src.player import Player
from src.save_system import SaveSystem
from src.utils import BG, HEIGHT, WIDTH
from src.worlds.ai_engineer import AIEngineerWorld
from src.worlds.architect import ArchitectWorld
from src.worlds.atc import ATCWorld
from src.worlds.base import BaseWorld
from src.worlds.bug_hunt import BugHuntWorld
from src.worlds.chef_rush import ChefRushWorld
from src.worlds.cybersecurity_analyst import CybersecurityAnalystWorld
from src.worlds.data_scientist import DataScientistWorld
from src.worlds.doctor import DoctorWorld
from src.worlds.electrician import ElectricianWorld
from src.worlds.entrepreneur import TycoonWorld
from src.worlds.fire_rescue import FireRescueWorld
from src.worlds.game_developer import GameDeveloperWorld
from src.worlds.marine import MarineWorld
from src.worlds.pilot import PilotWorld
from src.worlds.psychologist import PsychologistWorld
from src.worlds.robotics_engineer import RoboticsEngineerWorld
from src.worlds.software_developer import SoftwareDeveloperWorld


class GameEngine:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Career Worlds")
        self.root.configure(bg="#04111f")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH,
            height=HEIGHT,
            bg=BG,
            highlightthickness=0,
        )
        self.canvas.pack(expand=True)

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
            "8": PilotWorld(),
            "9": SoftwareDeveloperWorld(),
            "0": PsychologistWorld(),
            "q": TycoonWorld(),
            "w": ElectricianWorld(),
            "e": GameDeveloperWorld(),
            "r": DataScientistWorld(),
            "t": AIEngineerWorld(),
            "y": CybersecurityAnalystWorld(),
            "u": RoboticsEngineerWorld(),
        }
        self.world_order = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "q", "w", "e", "r", "t", "y", "u"]
        self.menu_columns = 4
        self.selected_world_index = 0
        self.menu_card_bounds: dict[str, tuple[float, float, float, float]] = {}

        self.active_world: BaseWorld | None = None
        self.state = "title"
        self.message = "Select a profession and jump straight into the challenge."
        self.keys: set[str] = set()
        self.last_time = time.time()
        self.high_contrast = bool(self.save_system.get_setting("high_contrast", False))
        self.debug_mode = False
        self.fps = 0.0
        self.mouse_x = 0
        self.mouse_y = 0
        self.music_on = bool(self.save_system.get_setting("music_on", True))

        self.logo_img: tk.PhotoImage | None = None
        self.logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png"))
        if not os.path.exists(self.logo_path):
            self.logo_path = os.path.join(os.getcwd(), "assets", "logo.png")
        try:
            self.logo_img = tk.PhotoImage(file=self.logo_path)
        except Exception:
            self.logo_img = None

        try:
            pygame.mixer.init()
        except pygame.error as error:
            print(f"Audio unavailable: {error}")
            self.music_on = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.root.after(16, self.loop)

    def on_mouse_move(self, event: tk.Event) -> None:
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.state != "menu":
            return

        hovered = self.get_menu_key_at(event.x, event.y)
        if hovered and hovered in self.world_order:
            self.selected_world_index = self.world_order.index(hovered)

    def on_key_press(self, event: tk.Event) -> None:
        self.keys.add(event.keysym)

        try:
            state = int(event.state)
            is_alt = (state & 131072 != 0) or (state & 4 != 0) or (state & 0x20000 != 0)
            if event.keysym.lower() == "s" and is_alt:
                self.music_on = not self.music_on
                self.save_system.set_setting("music_on", self.music_on)
                if self.music_on:
                    self.start_music()
                else:
                    self.stop_music()
                return
        except (ValueError, TypeError):
            pass

        lower_key = event.keysym.lower()
        if self.state == "title" and event.keysym in {"space", "Return"}:
            self.state = "menu"
            self.message = "Browse with arrow keys or hover cards, then press Enter."
        elif self.state == "menu":
            if lower_key in self.worlds:
                self.selected_world_index = self.world_order.index(lower_key)
                self.start_world(lower_key)
                return

            if event.keysym in {"Left", "Right", "Up", "Down"}:
                self.move_menu_selection(event.keysym)
            elif event.keysym in {"Return", "space"}:
                self.start_world(self.get_selected_key())
                return
            elif lower_key == "h":
                self.high_contrast = not self.high_contrast
                self.save_system.set_setting("high_contrast", self.high_contrast)
            elif event.keysym in {"?", "slash"}:
                self.state = "help"
            elif event.keysym == "F3":
                self.debug_mode = not self.debug_mode
        elif self.state == "briefing" and event.keysym in {"space", "Return"}:
            self.state = "world"
        elif self.state == "result" and event.keysym in {"space", "Return"}:
            self.return_to_menu()
        elif self.state == "victory" and event.keysym in {"space", "Return"}:
            self.state = "menu"

        if event.keysym == "Escape":
            if self.state == "world" and self.active_world:
                self.active_world.finished = True
                self.active_world.success = False
                self.active_world.message = "Mission Aborted."
                self.state = "menu"
                self.active_world = None
                self.message = "Mission aborted. Pick another profession when ready."
            elif self.state == "result":
                self.return_to_menu()
            elif self.state == "help":
                self.state = "menu"
                self.message = "Browse with arrow keys or hover cards, then press Enter."

    def on_key_release(self, event: tk.Event) -> None:
        self.keys.discard(event.keysym)

    def on_click(self, event: tk.Event) -> None:
        if self.state != "menu":
            return

        key = self.get_menu_key_at(event.x, event.y)
        if key is None:
            return

        self.selected_world_index = self.world_order.index(key)
        self.start_world(key)

    def get_selected_key(self) -> str:
        return self.world_order[self.selected_world_index]

    def move_menu_selection(self, direction: str) -> None:
        index = self.selected_world_index
        rows = math.ceil(len(self.world_order) / self.menu_columns)
        row = index // self.menu_columns
        col = index % self.menu_columns

        if direction == "Left":
            col = (col - 1) % self.menu_columns
        elif direction == "Right":
            col = (col + 1) % self.menu_columns
        elif direction == "Up":
            row = (row - 1) % rows
        elif direction == "Down":
            row = (row + 1) % rows

        new_index = row * self.menu_columns + col
        while new_index >= len(self.world_order):
            row = (row - 1) % rows
            new_index = row * self.menu_columns + col
        self.selected_world_index = new_index

    def get_menu_key_at(self, x: float, y: float) -> str | None:
        for key, bounds in self.menu_card_bounds.items():
            x1, y1, x2, y2 = bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return key
        return None

    def start_world(self, key: str) -> None:
        self.active_world = self.worlds[key]
        self.active_world.reset(self.player)
        self.active_world.high_contrast = self.high_contrast
        self.state = "briefing"
        self.message = ""

    def return_to_menu(self) -> None:
        if self.active_world and self.state == "result" and self.active_world.success:
            for key, world in self.worlds.items():
                if world == self.active_world:
                    self.save_system.mark_world_complete(key, self.active_world.grade, self.active_world.name)
                    self.selected_world_index = self.world_order.index(key)
                    break

        self.state = "menu"
        self.active_world = None
        comp_count = self.save_system.get_completed_world_count()
        if comp_count >= len(self.world_order):
            all_b_or_higher = True
            ranks = {"S": 5, "A": 4, "B": 3, "C": 2, "-": 1}
            for world_id in self.worlds:
                if ranks.get(self.save_system.get_grade(world_id, "-"), 0) < 3:
                    all_b_or_higher = False
                    break
            if all_b_or_higher:
                self.state = "victory"

        self.message = f"{comp_count}/{len(self.world_order)} professions mastered"

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
            self.active_world.tick_timer(dt)
            try:
                self.active_world.update(
                    dt,
                    self.canvas,
                    self.player,
                    self.keys,
                    (self.mouse_x, self.mouse_y),
                )
            except Exception as error:
                print(f"CRASH in {self.active_world.name}: {error}")
                self.return_to_menu()
                return

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

        self.root.after(16, self.loop)

    def draw_title(self) -> None:
        self.canvas.delete("all")
        for i in range(7):
            blend = i / 6
            red = int(4 + 28 * blend)
            green = int(17 + 55 * blend)
            blue = int(31 + 82 * blend)
            self.canvas.create_rectangle(
                0,
                i * HEIGHT / 7,
                WIDTH,
                (i + 1) * HEIGHT / 7,
                fill=f"#{red:02x}{green:02x}{blue:02x}",
                outline="",
            )

        pulse = (math.sin(time.time() * 1.8) + 1.0) / 2.0
        orb_radius = 90 + pulse * 24
        self.canvas.create_oval(
            WIDTH - 270 - orb_radius,
            150 - orb_radius,
            WIDTH - 270 + orb_radius,
            150 + orb_radius,
            fill="#13314f",
            outline="",
        )
        self.canvas.create_oval(70, 340, 310, 580, fill="#102844", outline="")
        panel_top = 64
        panel_bottom = HEIGHT - 58
        self.canvas.create_rectangle(70, panel_top, WIDTH - 70, panel_bottom, fill="#08111d", outline="#3ca8d8", width=2)
        self.canvas.create_rectangle(94, panel_top + 24, WIDTH - 94, panel_bottom - 24, fill="", outline="#163b5f", width=1)

        if self.logo_img:
            self.canvas.create_image(WIDTH / 2, 144, image=self.logo_img)
        else:
            self.canvas.create_text(WIDTH / 2, 132, text="CAREER WORLDS", fill="#8ce1ff", font=("Helvetica", 34, "bold"))

        self.canvas.create_text(
            WIDTH / 2,
            214,
            text="Arcade career trials with instant retries and persistent ranks",
            fill="#dbeeff",
            font=("Helvetica", 16, "bold"),
        )
        self.canvas.create_text(
            WIDTH / 2,
            248,
            text="Master 17 professions, improve your grades, and move between worlds without menu friction.",
            fill="#93b9d8",
            font=("Helvetica", 12),
            width=580,
        )
        self.draw_title_chip(220, 318, "Move", "WASD / Arrows")
        self.draw_title_chip(480, 318, "Launch", "Enter / Space")
        self.draw_title_chip(740, 318, "Abort", "Esc")

        completed = self.save_system.get_completed_world_count()
        self.canvas.create_rectangle(188, 366, WIDTH - 188, 406, fill="#0d1d31", outline="#21486b", width=1)
        self.canvas.create_rectangle(
            194,
            372,
            194 + ((WIDTH - 388) * completed / len(self.world_order)),
            400,
            fill="#4dd0e1",
            outline="",
        )
        self.canvas.create_text(
            WIDTH / 2,
            386,
            text=f"Overall Progress  {completed}/{len(self.world_order)}",
            fill="#ffffff",
            font=("Helvetica", 12, "bold"),
        )

        cta_fill = "#f7c96a" if pulse > 0.45 else "#ffe2a3"
        self.canvas.create_rectangle(WIDTH / 2 - 170, 442, WIDTH / 2 + 170, 490, fill=cta_fill, outline="")
        self.canvas.create_text(
            WIDTH / 2,
            466,
            text="PRESS SPACE TO ENTER THE HUB",
            fill="#12202f",
            font=("Helvetica", 14, "bold"),
        )
        self.canvas.create_text(
            WIDTH / 2,
            panel_bottom - 18,
            text="Direct selection keys still work in the hub for fast restarts.",
            fill="#9ab9d4",
            font=("Helvetica", 10),
        )

        if self.save_system.integrity_error:
            self.canvas.create_text(
                WIDTH / 2,
                panel_bottom + 2,
                text="Save file signature mismatch detected. Progress was reset.",
                fill="#ff6b6b",
                font=("Courier", 10),
            )

    def draw_title_chip(self, x: float, y: float, label: str, value: str) -> None:
        self.canvas.create_rectangle(x - 92, y - 26, x + 92, y + 26, fill="#10253c", outline="#27577f", width=1)
        self.canvas.create_text(x, y - 8, text=label, fill="#79d8ff", font=("Helvetica", 10, "bold"))
        self.canvas.create_text(x, y + 10, text=value, fill="#eef7ff", font=("Helvetica", 11))

    def draw_debug(self) -> None:
        debug_text = f"FPS: {self.fps:02.1f}\nState: {self.state}\nPos: {self.player.x:01f}, {self.player.y:01f}"
        self.canvas.create_text(10, HEIGHT - 10, anchor="sw", text=debug_text, fill="#00ff88", font=("Consolas", 10))

    def draw_victory(self) -> None:
        self.canvas.delete("all")
        for i in range(6):
            shade = 18 + i * 8
            self.canvas.create_rectangle(
                0,
                i * HEIGHT / 6,
                WIDTH,
                (i + 1) * HEIGHT / 6,
                fill=f"#{shade:02x}{shade:02x}{(shade + 20):02x}",
                outline="",
            )
        panel_top = 72
        panel_bottom = HEIGHT - 62
        self.canvas.create_rectangle(110, panel_top, WIDTH - 110, panel_bottom, fill="#111726", outline="#ffb86c", width=3)
        self.canvas.create_text(WIDTH / 2, panel_top + 64, text="CAREER MASTER", fill="#ffcf7d", font=("Helvetica", 32, "bold"))
        self.canvas.create_text(WIDTH / 2, panel_top + 112, text="Every profession cleared with a B rank or higher.", fill="#f5f7fb", font=("Helvetica", 14, "bold"))
        self.canvas.create_text(
            WIDTH / 2,
            panel_top + 184,
            text="You built enough consistency across every challenge to complete the full career tour.",
            fill="#b7c8dc",
            font=("Helvetica", 13),
            width=540,
        )
        self.canvas.create_rectangle(225, panel_bottom - 92, WIDTH - 225, panel_bottom - 38, fill="#172338", outline="#364a6a")
        self.canvas.create_text(WIDTH / 2, panel_bottom - 65, text="Press SPACE to return to the hub", fill="#8ff0a4", font=("Helvetica", 14, "bold"))

    def draw_menu(self) -> None:
        self.canvas.delete("all")
        self.menu_card_bounds.clear()

        if self.high_contrast:
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", outline="")
            header_fill = "#ffff00"
            sub_fill = "#ffffff"
            panel_fill = "#000000"
            panel_outline = "#ffffff"
            accent_fill = "#ffff00"
        else:
            for i in range(10):
                blend = i / 9
                red = int(8 + 15 * blend)
                green = int(18 + 36 * blend)
                blue = int(32 + 55 * blend)
                self.canvas.create_rectangle(
                    0,
                    i * HEIGHT / 10,
                    WIDTH,
                    (i + 1) * HEIGHT / 10,
                    fill=f"#{red:02x}{green:02x}{blue:02x}",
                    outline="",
                )
            self.canvas.create_oval(-120, -40, 220, 300, fill="#12385b", outline="")
            self.canvas.create_oval(WIDTH - 260, HEIGHT - 250, WIDTH + 70, HEIGHT + 60, fill="#0b2945", outline="")
            header_fill = "#dff6ff"
            sub_fill = "#8ecae6"
            panel_fill = "#0a1421"
            panel_outline = "#1f4d75"
            accent_fill = "#4dd0e1"

        self.canvas.create_text(48, 40, anchor="w", text="Career Worlds Hub", fill=header_fill, font=("Helvetica", 28, "bold"))
        self.canvas.create_text(
            48,
            72,
            anchor="w",
            text="Keyboard-first selection, hover details, and quick re-entry into any world.",
            fill=sub_fill,
            font=("Helvetica", 12),
        )

        progress = self.save_system.get_completed_world_count()
        progress_ratio = progress / len(self.world_order)
        self.canvas.create_text(48, 112, anchor="w", text=self.message, fill=header_fill, font=("Helvetica", 12, "bold"))
        self.canvas.create_rectangle(48, 126, 390, 144, fill=panel_fill, outline=panel_outline)
        self.canvas.create_rectangle(50, 128, 50 + 338 * progress_ratio, 142, fill=accent_fill, outline="")
        self.canvas.create_text(402, 135, anchor="w", text=f"{int(progress_ratio * 100)}% cleared", fill=sub_fill, font=("Helvetica", 11))

        controls = [("Arrows", "move focus"), ("Enter", "launch"), ("H", "contrast"), ("?", "help"), ("Alt+S", "music")]
        for index, (control, label) in enumerate(controls):
            x1 = 530 + index * 82
            x2 = x1 + 74
            self.canvas.create_rectangle(x1, 34, x2, 60, fill=panel_fill, outline=panel_outline, width=1)
            self.canvas.create_text((x1 + x2) / 2, 44, text=control, fill=header_fill, font=("Helvetica", 8, "bold"))
            self.canvas.create_text((x1 + x2) / 2, 53, text=label, fill=sub_fill, font=("Helvetica", 7))

        grid_x = 44
        grid_y = 182
        card_w = 138
        card_h = 60
        gap_x = 14
        gap_y = 8
        for index, key in enumerate(self.world_order):
            row = index // self.menu_columns
            col = index % self.menu_columns
            x1 = grid_x + col * (card_w + gap_x)
            y1 = grid_y + row * (card_h + gap_y)
            x2 = x1 + card_w
            y2 = y1 + card_h
            self.menu_card_bounds[key] = (x1, y1, x2, y2)

            world = self.worlds[key]
            grade = self.save_system.get_grade(key)
            is_selected = index == self.selected_world_index
            is_hovered = x1 <= self.mouse_x <= x2 and y1 <= self.mouse_y <= y2
            self.draw_world_card(x1, y1, x2, y2, key, world, grade, is_selected, is_hovered)

        self.draw_selected_world_panel(panel_fill, panel_outline, header_fill, sub_fill, accent_fill)
        self.canvas.create_text(
            WIDTH / 2,
            HEIGHT - 14,
            text="Completed cards retain your best grade. Direct hotkeys still work: 1-0, Q-U.",
            fill=sub_fill,
            font=("Helvetica", 10),
        )

    def draw_world_card(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        key: str,
        world: BaseWorld,
        grade: str | None,
        is_selected: bool,
        is_hovered: bool,
    ) -> None:
        if self.high_contrast:
            fill = "#000000"
            text_fill = "#ffffff"
            muted = "#ffff00"
        else:
            fill = "#152434" if is_selected else "#0d1826"
            if is_hovered and not is_selected:
                fill = "#122234"
            text_fill = "#eef7ff"
            muted = "#8fb4cf"

        grade_color = self.get_grade_color(grade)
        outline = "#ffffff" if self.high_contrast and is_selected else grade_color
        width = 3 if is_selected else 1
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)
        if is_selected and not self.high_contrast:
            self.canvas.create_rectangle(x1 + 4, y1 + 4, x2 - 4, y2 - 4, outline="#65d6ff", width=1)

        self.canvas.create_text(x1 + 12, y1 + 13, anchor="nw", text=f"[{key.upper()}]", fill=muted, font=("Helvetica", 10, "bold"))
        self.canvas.create_text(
            x1 + 12,
            y1 + 24,
            anchor="nw",
            text=world.name,
            fill=text_fill,
            font=("Helvetica", 9, "bold"),
            width=x2 - x1 - 24,
        )
        self.canvas.create_text(
            x1 + 12,
            y2 - 12,
            anchor="w",
            text=f"Best Rank  {grade or '-'}",
            fill=grade_color if not self.high_contrast else "#ffffff",
            font=("Helvetica", 9, "bold"),
        )

    def draw_selected_world_panel(
        self,
        panel_fill: str,
        panel_outline: str,
        header_fill: str,
        sub_fill: str,
        accent_fill: str,
    ) -> None:
        key = self.get_selected_key()
        world = self.worlds[key]
        grade = self.save_system.get_grade(key)
        completed = world.name in self.save_system.get_completed_worlds()

        x1, y1, x2, y2 = 640, 102, 920, 542
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=panel_fill, outline=panel_outline, width=2)
        self.canvas.create_text(x1 + 20, y1 + 24, anchor="w", text="Selected World", fill=sub_fill, font=("Helvetica", 10, "bold"))
        self.canvas.create_text(x1 + 20, y1 + 52, anchor="w", text=world.name, fill=header_fill, font=("Helvetica", 18, "bold"), width=220)

        badge_fill = "#1b3d24" if completed and not self.high_contrast else panel_fill
        badge_outline = "#7cf29a" if completed and not self.high_contrast else panel_outline
        self.canvas.create_rectangle(x1 + 20, y1 + 110, x1 + 118, y1 + 140, fill=badge_fill, outline=badge_outline)
        self.canvas.create_text(
            x1 + 69,
            y1 + 125,
            text="Cleared" if completed else "Uncleared",
            fill=accent_fill if not completed else "#7cf29a",
            font=("Helvetica", 10, "bold"),
        )
        self.canvas.create_text(x1 + 145, y1 + 125, anchor="w", text=f"Best Rank: {grade or '-'}", fill=header_fill, font=("Helvetica", 11, "bold"))
        self.canvas.create_text(
            x1 + 20,
            y1 + 168,
            anchor="nw",
            text=world.summary,
            fill=header_fill if self.high_contrast else "#d7e7f5",
            font=("Helvetica", 11),
            width=230,
        )

        hints = [
            f"Shortcut: {key.upper()}",
            "Enter or Space launches this world",
            "Esc backs out of a run instantly",
            "Hover any card to update this panel",
        ]
        panel_y = y1 + 258
        self.canvas.create_text(x1 + 20, panel_y, anchor="w", text="Quick Actions", fill=sub_fill, font=("Helvetica", 10, "bold"))
        for hint in hints:
            panel_y += 24
            self.canvas.create_text(x1 + 20, panel_y, anchor="w", text=f"- {hint}", fill=header_fill, font=("Helvetica", 10), width=225)

        self.canvas.create_rectangle(x1 + 20, y2 - 64, x2 - 20, y2 - 20, fill=accent_fill, outline="")
        self.canvas.create_text((x1 + x2) / 2, y2 - 42, text="Press Enter To Start", fill="#08111d", font=("Helvetica", 13, "bold"))

    def get_grade_color(self, grade: str | None) -> str:
        palette = {"S": "#7cf29a", "A": "#67d7ff", "B": "#f5d76e", "C": "#ff9e57", "-": "#4d657d"}
        if self.high_contrast:
            return "#ffffff"
        return palette.get(grade or "-", "#4d657d")

    def draw_help(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#07111b", outline="")
        panel_top = 30
        panel_bottom = HEIGHT - 34
        self.canvas.create_rectangle(42, panel_top, WIDTH - 42, panel_bottom, fill="#0d1724", outline="#2a587d", width=2)
        self.canvas.create_text(WIDTH / 2, panel_top + 38, text="How To Navigate Career Worlds", fill="#dff6ff", font=("Helvetica", 24, "bold"))
        self.canvas.create_text(
            WIDTH / 2,
            panel_top + 68,
            text="Everything important is reachable by keyboard, with the mouse only adding faster browsing.",
            fill="#8ecae6",
            font=("Helvetica", 11),
        )

        left_x1, left_x2 = 82, 440
        right_x1, right_x2 = 510, 878
        self.canvas.create_rectangle(left_x1, 130, left_x2, 454, fill="#101d2c", outline="#284f74")
        self.canvas.create_rectangle(right_x1, 130, right_x2, 454, fill="#101d2c", outline="#284f74")

        self.canvas.create_text(left_x1 + 18, 158, anchor="w", text="Controls", fill="#7cd7ff", font=("Helvetica", 16, "bold"))
        controls = [
            "WASD / Arrows: move in worlds",
            "Arrow keys in hub: move focus",
            "Enter / Space: start selected world",
            "Esc: abort run or leave help",
            "H: toggle high contrast in hub",
            "Alt+S: toggle music",
            "1-0 and Q-U: instant world shortcuts",
            "F3: debug overlay",
        ]
        y = 192
        for line in controls:
            self.canvas.create_text(left_x1 + 18, y, anchor="w", text=f"- {line}", fill="#eef7ff", font=("Helvetica", 12), width=320)
            y += 28

        self.canvas.create_text(right_x1 + 18, 158, anchor="w", text="Flow", fill="#7cd7ff", font=("Helvetica", 16, "bold"))
        flow = [
            "1. Start from the title screen.",
            "2. Pick a profession from the hub.",
            "3. Read the briefing and press Space.",
            "4. Finish the mini-game before time runs out.",
            "5. Return to the hub and improve your best rank.",
            "6. Reach a B or higher in every world to unlock the final victory screen.",
        ]
        y = 192
        for line in flow:
            self.canvas.create_text(right_x1 + 18, y, anchor="w", text=line, fill="#eef7ff", font=("Helvetica", 12), width=320)
            y += 34

        self.canvas.create_rectangle(220, panel_bottom - 56, WIDTH - 220, panel_bottom - 10, fill="#4dd0e1", outline="")
        self.canvas.create_text(WIDTH / 2, panel_bottom - 33, text="Press ESC To Return To The Hub", fill="#07111b", font=("Helvetica", 13, "bold"))

    def start_music(self) -> None:
        try:
            music_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backgroundMusic.wav"))
            if not os.path.exists(music_path):
                print(f"Music file not found: {music_path}")
                return
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)
        except Exception as error:
            print(f"Error playing music: {error}")

    def stop_music(self) -> None:
        try:
            pygame.mixer.music.stop()
        except Exception as error:
            print(f"Error stopping music: {error}")

    def on_closing(self) -> None:
        self.save_system.set_setting("high_contrast", self.high_contrast, save_immediately=False)
        self.save_system.set_setting("music_on", self.music_on, save_immediately=False)
        self.save_system.save()
        self.stop_music()
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.last_time = time.time()
        if self.music_on:
            self.start_music()
        self.loop()
        self.root.mainloop()
