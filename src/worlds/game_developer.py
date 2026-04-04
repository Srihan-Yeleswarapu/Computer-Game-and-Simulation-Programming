from __future__ import annotations

import json
import math
import os
import random
import tkinter as tk

from src.player import Player
from src.utils import ACCENT, DANGER, HEIGHT, SUCCESS, TEXT, WIDTH, Particle, clamp
from src.worlds.base import BaseWorld

from src.game.abilities import AbilitySystem
from src.game.bugs import BugDifficultyScaler, BugManager
from src.game.chaos_events import ChaosEventManager
from src.game.complaints import ComplaintManager
from src.game.features import FeatureUnlockManager
from src.game.panic_mode import PanicModeManager
from src.game.systems import CoreSystems, Difficulty
from src.game.ui import draw_bar, draw_panic_banner, draw_toast


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROGRESS_FILE = os.path.join(PROJECT_ROOT, "game_dev_progress.json")


class GameDeveloperWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Game Developer",
            summary="Ship features under chaos. Bugs multiply, complaints swarm, motivation burns. Keep stability alive long enough to launch.",
            duration=120.0,
        )
        self.auto_finish_on_timer = False

        self.office_bounds = (88.0, 88.0, 872.0, 548.0)
        self.desk_pos = (250.0, 310.0)

        self.briefing = [
            "Hold SPACE to code. Coding is faster at the Dev Desk.",
            "Stomp red bugs by running through them. Too many bugs escalate into glitches and crash risk.",
            "Run into floating complaints to reply (no inbox walking). Too many unresolved complaints drain you fast.",
            "Abilities: Dash (Shift), Emergency Patch (E), Coffee Boost (C), Debug Burst (F - unlock later).",
            "Ship the unlock features, then survive the Launch Window.",
        ]
        self.warning = "If Stability hits 0: crash. If Motivation hits 0: burnout."
        self.hints = [
            "Tip: SPACE to code anywhere, but the desk is faster.",
            "Tip: Dash (Shift) lets you stomp a swarm without losing tempo.",
            "Tip: Coffee (C) is the safe way to keep speed and progress up.",
            "Tip: Complaints are targets. Run into them.",
            "Tip: 13+ bugs means crash risk. Do not let it sit.",
        ]

        self.meta = self._load_meta()
        self.systems = CoreSystems()
        self.difficulty = Difficulty()

        self.abilities = AbilitySystem()
        self.features = FeatureUnlockManager()
        self.bugs = BugManager(bounds=self.office_bounds, desk_pos=self.desk_pos)
        self.complaints = ComplaintManager(bounds=self.office_bounds)
        self.chaos = ChaosEventManager()
        self.panic = PanicModeManager(duration=self.duration)

        self.toast_text = ""
        self.toast_timer = 0.0

        self.screen_flash = 0.0
        self.flicker_strength = 0.0
        self.action_lock = 0.0

        self.in_launch_window = False
        self.launch_timer = 0.0
        self.automation_on = False

    def _load_meta(self) -> dict[str, int | float]:
        default: dict[str, int | float] = {"best_features": 0, "clears": 0}
        if not os.path.exists(PROGRESS_FILE):
            return default
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                for key in default:
                    value = loaded.get(key, default[key])
                    if isinstance(value, (int, float)):
                        default[key] = value
        except Exception:
            pass
        return default

    def _save_meta(self) -> None:
        try:
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.meta, f, indent=2)
        except Exception:
            pass

    def reset(self, player: Player) -> None:
        player.reset(self.desk_pos[0] - 80, self.desk_pos[1])
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.grade = "-"

        self.systems = CoreSystems(progress=10.0, stability=92.0, motivation=84.0)
        self.difficulty = Difficulty()

        self.abilities = AbilitySystem()
        self.features.on_reset()
        self.bugs = BugManager(bounds=self.office_bounds, desk_pos=self.desk_pos)
        self.complaints = ComplaintManager(bounds=self.office_bounds)
        self.chaos = ChaosEventManager()
        self.panic = PanicModeManager(duration=self.duration)

        self.toast_text = "Ship features. Survive chaos. Launch anyway."
        self.toast_timer = 2.4
        self.screen_flash = 0.0
        self.flicker_strength = 0.0
        self.action_lock = 0.0

        self.in_launch_window = False
        self.launch_timer = 0.0
        self.automation_on = False

        self.shake = 0.0
        self.particles = []

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.update_particles(dt)
        self.toast_timer = max(0.0, self.toast_timer - dt)
        self.screen_flash = max(0.0, self.screen_flash - dt)
        self.action_lock = max(0.0, self.action_lock - dt)

        time_ratio = 1.0 - (self.timer / self.duration if self.duration > 0 else 0.0)
        self.difficulty.advance(self.features.shipped, time_ratio)

        self.abilities.tick(dt)
        panic_state = self.panic.update(dt, systems=self.systems, time_left=self.timer)
        chaos_fx = self.chaos.update(
            dt,
            systems=self.systems,
            bugs=self.bugs,
            complaints=self.complaints,
            difficulty=self.difficulty,
        )

        if self.chaos.toast_timer > 0.0:
            self.toast_text = self.chaos.toast_text
            self.toast_timer = max(self.toast_timer, self.chaos.toast_timer)

        bug_count = self.bugs.count()
        bug_mod = BugDifficultyScaler.modifiers(bug_count)
        self.flicker_strength = bug_mod.screen_flicker

        # Baseline drains (the "job"), scaled up by shipped features.
        self.systems.add_motivation(-(0.12 + 0.035 * self.difficulty.level) * dt)
        self.systems.add_motivation(-chaos_fx.motivation_drain * dt)
        if bug_count > 0:
            stability_drain = bug_mod.stability_drain_per_bug * bug_count
            stability_drain *= 1.0 + 0.12 * self.difficulty.level
            self.systems.add_stability(-stability_drain * dt)

        # Live Ops automation: if you're doing well, the build self-heals a little.
        if self.automation_on and self.systems.motivation >= 65.0 and bug_count <= 8:
            self.systems.add_stability(1.15 * dt)

        # Abilities (key taps) are evaluated before movement so the feedback feels instant.
        if self.action_lock <= 0.0:
            if self.abilities.try_dash(keys):
                self.shake = max(self.shake, 0.8)
                self._spawn_particles(player.x, player.y, "#65d6ff", 12, 240)
                self.action_lock = 0.05

            if self.abilities.try_coffee_boost(keys):
                self.systems.add_motivation(22.0)
                self.toast_text = "Coffee Boost: motivation up, tempo up."
                self.toast_timer = max(self.toast_timer, 1.9)
                self.screen_flash = max(self.screen_flash, 0.08)
                self.action_lock = 0.12

            if self.abilities.try_emergency_patch(keys):
                self.systems.add_stability(20.0)
                self.systems.add_motivation(-10.0)
                self.toast_text = "Emergency Patch: stability up, motivation down."
                self.toast_timer = max(self.toast_timer, 2.0)
                self.screen_flash = max(self.screen_flash, 0.12)
                self.shake = max(self.shake, 0.9)
                self._spawn_particles(self.desk_pos[0], self.desk_pos[1], "#50fa7b", 16, 210)
                self.action_lock = 0.14

            if "x" in keys and self.abilities.can_craft_patch_kit():
                if self.abilities.craft_patch_kit():
                    self.toast_text = "Crafted Patch Kit: E is stocked."
                    self.toast_timer = max(self.toast_timer, 1.8)
                    self.screen_flash = max(self.screen_flash, 0.08)
                    self.action_lock = 0.18

            if self.abilities.try_debug_burst(keys):
                removed = self.bugs.remove_near(x=player.x, y=player.y, radius=96.0)
                if removed > 0:
                    self.systems.add_progress(4.0 + removed * 1.1)
                    self.systems.add_stability(2.5 + removed * 0.35)
                self.systems.add_motivation(-8.0)
                self.toast_text = f"Debug Burst: purged {removed} bugs."
                self.toast_timer = max(self.toast_timer, 1.8)
                self.screen_flash = max(self.screen_flash, 0.12)
                self.shake = max(self.shake, 1.3)
                self._spawn_particles(player.x, player.y, "#ffb86c", 22, 260)
                self.action_lock = 0.14

        # Movement (with bug-glitch interference).
        effective_keys = set(keys)
        if bug_mod.input_glitch > 0.0 and random.random() < bug_mod.input_glitch:
            swapped = {
                "Left": "Right",
                "Right": "Left",
                "Up": "Down",
                "Down": "Up",
                "a": "d",
                "d": "a",
                "w": "s",
                "s": "w",
            }
            effective_keys = {swapped.get(k, k) for k in effective_keys}

        original_speed = player.speed
        original_accel = player.accel
        speed = 245.0
        speed *= 0.72 + 0.55 * (self.systems.motivation / 100.0)
        speed *= self.abilities.dash_multiplier()
        speed *= 1.0 + (0.18 if self.abilities.coffee_boost.active > 0.0 else 0.0)
        if panic_state.active:
            speed *= 1.05
        player.speed = speed
        player.accel = 12.0
        player.update(dt, effective_keys, self.office_bounds)
        player.speed = original_speed
        player.accel = original_accel

        # Coding (active, not walking): hold SPACE anywhere; desk is a bonus zone.
        coding = "space" in keys and not self.in_launch_window
        if coding:
            desk_bonus = 1.45 if math.hypot(player.x - self.desk_pos[0], player.y - self.desk_pos[1]) < 90 else 1.0
            progress_rate = 15.0 + 1.6 * self.difficulty.level
            progress_mult = chaos_fx.progress_mult * self.abilities.coffee_multiplier()
            self.systems.add_progress(progress_rate * desk_bonus * progress_mult * dt)
            self.systems.add_motivation(-(0.85 + 0.12 * self.difficulty.level) * dt)

        # Spawns and entity updates.
        spawn_mult = (1.0 + 0.10 * self.difficulty.level) * chaos_fx.bug_spawn_mult * panic_state.bug_spawn_mult
        if coding:
            spawn_mult *= 1.15
        speed_base = 64.0 + 6.0 * self.difficulty.level
        self.bugs.update_spawning(dt, spawn_mult=spawn_mult, speed_base=speed_base)
        self.bugs.update(
            dt,
            player=player,
            systems=self.systems,
            speed_bonus=bug_mod.speed_bonus + chaos_fx.bug_speed_bonus,
            on_squash=self.abilities.on_bug_squashed,
        )

        complaint_mult = 1.0 + 0.10 * self.difficulty.level
        if panic_state.active:
            complaint_mult *= 1.12
        self.complaints.update_spawning(dt, spawn_mult=complaint_mult)
        self.complaints.update(dt, player=player, systems=self.systems)

        # Crash risk spikes (13+ bugs and/or System Failure).
        crash_per_sec = bug_mod.crash_risk_per_sec + chaos_fx.crash_risk_bonus
        if crash_per_sec > 0.0 and random.random() < crash_per_sec * dt:
            spike = 30.0 + 6.0 * self.difficulty.level
            self.systems.add_stability(-spike)
            self.toast_text = "Crash spike: stack trace everywhere."
            self.toast_timer = max(self.toast_timer, 2.0)
            self.screen_flash = max(self.screen_flash, 0.18)
            self.shake = max(self.shake, 1.8)
            self._spawn_particles(self.desk_pos[0], self.desk_pos[1], "#ff5555", 28, 320)

        # Ship features.
        shipped = self.features.try_ship(systems=self.systems, abilities=self.abilities)
        if shipped:
            self.systems.add_stability(-(7.0 + 2.0 * self.difficulty.level))
            self.systems.add_motivation(-(6.0 + 1.5 * self.difficulty.level))
            self.toast_text = f"FEATURE SHIPPED: {shipped.name}  |  {shipped.hook}"
            self.toast_timer = max(self.toast_timer, 3.0)
            self.screen_flash = max(self.screen_flash, 0.14)
            self.shake = max(self.shake, 1.2)
            self.bugs.spawn(n=3 + self.difficulty.level, speed_base=78.0 + 5.0 * self.difficulty.level)
            self.complaints.spawn(n=1 + self.difficulty.level // 2)
            if shipped.name == "Upgrade Menu":
                self.abilities.cooldown_scale = 0.85
            if shipped.name == "Live Ops":
                self.automation_on = True
                self.in_launch_window = True
                self.launch_timer = 12.0
                self.toast_text = "LAUNCH WINDOW: keep stability alive for 12 seconds."
                self.toast_timer = max(self.toast_timer, 3.2)

        # Launch window logic (high intensity finale).
        if self.in_launch_window:
            self.launch_timer = max(0.0, self.launch_timer - dt)
            self.systems.add_motivation(-0.55 * dt)
            self.bugs.update_spawning(dt, spawn_mult=2.0 + panic_state.intensity, speed_base=92.0 + 8.0 * self.difficulty.level)
            if self.launch_timer <= 0.0:
                self.finished = True
                self.success = True
                self.message = "Launch survived. Patch notes are already on fire."

        # Failure checks.
        if self.systems.stability <= 0.0 and not self.finished:
            self.finished = True
            self.success = False
            self.message = "Build crashed. The deadline kept moving anyway."
        if self.systems.motivation <= 0.0 and not self.finished:
            self.finished = True
            self.success = False
            self.message = "Burnout. You stared at the bug list until it stared back."
        if self.timer <= 0.0 and not self.finished:
            self.finished = True
            self.success = self.in_launch_window and self.launch_timer <= 0.0
            self.message = "Deadline reached. The build is whatever it is."

        if panic_state.active:
            self.shake = max(self.shake, panic_state.shake)
            self.screen_flash = max(self.screen_flash, panic_state.flash)

        if chaos_fx.shake > 0.0:
            self.shake = max(self.shake, chaos_fx.shake)
        if chaos_fx.screen_flash > 0.0:
            self.screen_flash = max(self.screen_flash, chaos_fx.screen_flash)

        self.systems.clamp_all()
        self.draw(canvas, player)

        if self.finished and self.success:
            shipped_count = int(self.features.shipped)
            self.meta["best_features"] = max(float(self.meta.get("best_features", 0)), shipped_count)
            self.meta["clears"] = float(self.meta.get("clears", 0)) + 1
            self._save_meta()

    def _spawn_particles(self, x: float, y: float, color: str, n: int, speed: float) -> None:
        for _ in range(n):
            ang = random.uniform(0.0, math.tau)
            mag = random.uniform(speed * 0.35, speed)
            self.particles.append(Particle(x, y, color, math.cos(ang) * mag, math.sin(ang) * mag, random.uniform(0.25, 0.55), size=random.uniform(2.0, 4.0)))

    def _draw_player(self, canvas: tk.Canvas, *, x: float, y: float, size: float) -> None:
        canvas.create_oval(x - size - 4, y - size + 6, x + size + 4, y + size + 8, fill="#0a2235", outline="")
        canvas.create_rectangle(x - size, y - size, x + size, y + size, fill="#61dafb", outline="#0d8db6", width=2)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")

        ox = 0.0
        oy = 0.0
        if self.shake > 0.0:
            strength = 6.0 * clamp(self.shake, 0.0, 2.0)
            ox = random.uniform(-strength, strength)
            oy = random.uniform(-strength, strength)

        x1, y1, x2, y2 = self.office_bounds
        x1 += ox
        y1 += oy
        x2 += ox
        y2 += oy
        desk_x, desk_y = self.desk_pos[0] + ox, self.desk_pos[1] + oy

        # Background (studio vibe).
        for i in range(7):
            blend = i / 6
            red = int(7 + 18 * blend)
            green = int(15 + 34 * blend)
            blue = int(30 + 55 * blend)
            canvas.create_rectangle(0, i * HEIGHT / 7, WIDTH, (i + 1) * HEIGHT / 7, fill=f"#{red:02x}{green:02x}{blue:02x}", outline="")

        canvas.create_rectangle(x1 - 30, y1 - 30, x2 + 30, y2 + 30, fill="#101828", outline="#2d3952", width=4)
        canvas.create_rectangle(x1, y1, x2, y2, fill="#0c1626", outline="#3b4c6b", width=3)
        for line_y in range(int(y1), int(y2), 30):
            canvas.create_line(x1, line_y, x2, line_y, fill="#17243a", dash=(4, 6))
        for line_x in range(int(x1), int(x2), 40):
            canvas.create_line(line_x, y1, line_x, y2, fill="#17243a", dash=(6, 6))

        # Dev Desk (bonus zone).
        canvas.create_rectangle(desk_x - 74, desk_y - 34, desk_x + 74, desk_y + 34, fill="#111d2d", outline="#65d6ff", width=3)
        canvas.create_text(desk_x, desk_y - 12, text="DEV DESK", fill="#cbe2ff", font=("Helvetica", 12, "bold"))
        canvas.create_text(desk_x, desk_y + 12, text="SPACE to code", fill="#8fb4cf", font=("Helvetica", 10, "bold"))

        # Bugs.
        for bug in self.bugs.bugs:
            bx = bug.x + ox
            by = bug.y + oy
            r = bug.radius
            outline = "#ffd1d1" if bug.attached else "#0a0b10"
            width = 3 if bug.attached else 2
            canvas.create_oval(bx - r - 3, by - r - 3, bx + r + 3, by + r + 3, fill="#2a0b12", outline="")
            canvas.create_oval(bx - r, by - r, bx + r, by + r, fill="#ff3355", outline=outline, width=width)
            canvas.create_line(bx - r + 3, by - r + 3, bx + r - 3, by + r - 3, fill="#ffd1e0")

        # Complaints (moving targets).
        for popup in self.complaints.popups:
            px = popup.x + ox
            py = popup.y + oy
            canvas.create_rectangle(px - 72, py - 18, px + 72, py + 18, fill="#0e1826", outline="#ffb86c", width=2)
            canvas.create_text(px, py, text=popup.text, fill="#ffe6c7", font=("Helvetica", 9, "bold"), width=140)

        # Player (shake-aware draw).
        self._draw_player(canvas, x=player.x + ox, y=player.y + oy, size=player.size)

        # Particles (no offset; they still read fine with shake).
        self.draw_particles(canvas)

        # Visual warnings.
        if self.flicker_strength > 0.0 and random.random() < self.flicker_strength:
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#ff3344", outline="", stipple="gray25")
        if self.screen_flash > 0.0:
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#ffffff", outline="", stipple="gray25")

        # HUD: core systems + feature + abilities.
        self.draw_hud(canvas)
        draw_bar(canvas, x=14, y=46, w=300, h=18, value=self.systems.progress, label="Progress", fill="#5fb6ff")
        draw_bar(canvas, x=14, y=68, w=300, h=18, value=self.systems.stability, label="Stability", fill="#50fa7b" if self.systems.stability >= 40 else "#ff5555")
        draw_bar(canvas, x=14, y=90, w=300, h=18, value=self.systems.motivation, label="Motivation", fill="#ffb86c" if self.systems.motivation >= 40 else "#ff5555")

        feature_name = self.features.current().name if not self.features.is_done() else "Launch"
        canvas.create_text(340, 56, anchor="w", fill="#dbeeff", font=("Helvetica", 12, "bold"), text=f"Next: {feature_name}")
        canvas.create_text(340, 78, anchor="w", fill="#8fb4cf", font=("Helvetica", 10, "bold"), text=f"Shipped: {self.features.shipped}/{len(self.features.UNLOCKS)}")
        canvas.create_text(340, 98, anchor="w", fill="#8fb4cf", font=("Helvetica", 10, "bold"), text=f"Bugs: {self.bugs.count()}  Complaints: {self.complaints.count()}")

        ax = WIDTH - 280
        canvas.create_rectangle(ax, 46, WIDTH - 14, 138, fill="#0b1220", outline="#21486b", width=2)
        canvas.create_text(ax + 10, 56, anchor="w", fill="#e7f3ff", font=("Helvetica", 10, "bold"), text="Abilities")
        canvas.create_text(ax + 10, 76, anchor="w", fill=TEXT, font=("Helvetica", 10, "bold"), text=f"Shift Dash  CD {self.abilities.dash.cooldown:0.1f}s")
        canvas.create_text(ax + 10, 92, anchor="w", fill=TEXT, font=("Helvetica", 10, "bold"), text=f"E Patch    CD {self.abilities.emergency_patch.cooldown:0.1f}s  Kits {self.abilities.patch_kits}")
        canvas.create_text(
            ax + 10,
            108,
            anchor="w",
            fill=TEXT,
            font=("Helvetica", 10, "bold"),
            text=f"C Coffee   CD {self.abilities.coffee_boost.cooldown:0.1f}s  Coffee {self.abilities.coffee_charges}",
        )
        if self.abilities.has_skill_tree:
            canvas.create_text(ax + 10, 124, anchor="w", fill=TEXT, font=("Helvetica", 10, "bold"), text=f"F Debug    CD {self.abilities.debug_burst.cooldown:0.1f}s")

        if self.toast_timer > 0.0:
            draw_toast(canvas, text=self.toast_text, timer=self.toast_timer)

        # Panic banner (must be loud).
        panic_active = self.panic.state.active
        draw_panic_banner(canvas, active=panic_active, intensity=self.panic.state.intensity)

        if self.in_launch_window:
            canvas.create_text(
                WIDTH / 2,
                126,
                fill="#ffdddd",
                font=("Helvetica", 14, "bold"),
                text=f"LAUNCH WINDOW: {self.launch_timer:0.1f}s",
            )

        if self.finished:
            self.draw_result(canvas)
