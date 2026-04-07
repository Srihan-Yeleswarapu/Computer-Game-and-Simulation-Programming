from __future__ import annotations

import json
import math
import os
import random
import tkinter as tk
from dataclasses import dataclass

from src.player import Player
from src.utils import ACCENT, DANGER, HEIGHT, SUCCESS, TEXT, WIDTH, Particle, clamp
from src.worlds.base import BaseWorld


@dataclass(slots=True)
class AbilityState:
    cooldown: float = 0.0
    active: float = 0.0


class AbilitySystem:
    """Active abilities that encourage movement and tactical resource trades."""

    def __init__(self) -> None:
        self.dash = AbilityState()
        self.emergency_patch = AbilityState()
        self.coffee_boost = AbilityState()
        self.debug_burst = AbilityState()

        self.cooldown_scale = 1.0
        self.coffee_charges = 0
        self.patch_kits = 0
        self.has_inventory = False
        self.has_crafting = False
        self.has_skill_tree = False

    def unlock_inventory(self) -> None:
        self.has_inventory = True

    def unlock_crafting(self) -> None:
        self.has_crafting = True

    def unlock_skill_tree(self) -> None:
        self.has_skill_tree = True

    def tick(self, dt: float) -> None:
        for ability in (self.dash, self.emergency_patch, self.coffee_boost, self.debug_burst):
            ability.cooldown = max(0.0, ability.cooldown - dt)
            ability.active = max(0.0, ability.active - dt)

    def try_dash(self, pressed: bool) -> bool:
        if self.dash.cooldown > 0.0 or not pressed:
            return False
        self.dash.active = 0.38
        self.dash.cooldown = 1.6 * self.cooldown_scale
        return True

    def dash_multiplier(self) -> float:
        return 2.25 if self.dash.active > 0.0 else 1.0

    def try_emergency_patch(self, pressed: bool) -> bool:
        if self.emergency_patch.cooldown > 0.0 or not pressed:
            return False
        if self.has_crafting and self.patch_kits <= 0:
            return False
        if self.has_crafting:
            self.patch_kits -= 1
        self.emergency_patch.cooldown = 6.0 * self.cooldown_scale
        return True

    def try_coffee_boost(self, pressed: bool) -> bool:
        if self.coffee_boost.cooldown > 0.0 or not pressed:
            return False
        if self.has_inventory:
            if self.coffee_charges <= 0:
                return False
            self.coffee_charges -= 1
        self.coffee_boost.active = 4.0
        base_cd = 9.5 if self.has_inventory else 13.0
        self.coffee_boost.cooldown = base_cd * self.cooldown_scale
        return True

    def coffee_multiplier(self) -> float:
        return 1.25 if self.coffee_boost.active > 0.0 else 1.0

    def try_debug_burst(self, pressed: bool) -> bool:
        if not self.has_skill_tree or self.debug_burst.cooldown > 0.0 or not pressed:
            return False
        self.debug_burst.cooldown = 9.5 * self.cooldown_scale
        return True

    def can_craft_patch_kit(self) -> bool:
        return self.has_crafting and self.coffee_charges >= 3

    def craft_patch_kit(self) -> bool:
        if not self.can_craft_patch_kit():
            return False
        self.coffee_charges -= 3
        self.patch_kits += 1
        return True

    def on_bug_squashed(self) -> None:
        if self.has_inventory:
            self.coffee_charges = int(clamp(self.coffee_charges + 1, 0, 9))


@dataclass(slots=True)
class CoreSystems:
    progress: float = 0.0
    stability: float = 100.0
    motivation: float = 100.0

    def clamp_all(self) -> None:
        self.progress = clamp(self.progress, 0.0, 100.0)
        self.stability = clamp(self.stability, 0.0, 100.0)
        self.motivation = clamp(self.motivation, 0.0, 100.0)

    def add_progress(self, amount: float) -> None:
        self.progress = clamp(self.progress + amount, 0.0, 100.0)

    def add_stability(self, amount: float) -> None:
        self.stability = clamp(self.stability + amount, 0.0, 100.0)

    def add_motivation(self, amount: float) -> None:
        self.motivation = clamp(self.motivation + amount, 0.0, 100.0)


@dataclass(slots=True)
class Difficulty:
    level: int = 0
    chaos_meter: float = 0.0

    def advance(self, shipped_features: int, time_ratio: float) -> None:
        self.level = shipped_features
        self.chaos_meter = clamp(0.15 + shipped_features * 0.12 + time_ratio * 0.55, 0.0, 1.3)


@dataclass(slots=True)
class Feature:
    name: str
    hook: str


class FeatureUnlockManager:
    BASELINE = Feature("Core Loop", "Dash is online. Ship features before the build collapses.")
    UNLOCKS = [
        Feature("Inventory", "Coffee drops from squashed bugs. C now consumes coffee."),
        Feature("Crafting", "Craft patch kits from 3 coffee. E consumes a patch kit."),
        Feature("Skill Tree", "Debug Burst unlocked (F). Emergency control of swarms."),
        Feature("Upgrade Menu", "Cooldowns shrink. Momentum becomes a build strategy."),
        Feature("Live Ops", "Automation enabled. High motivation slowly restores stability."),
    ]

    def __init__(self) -> None:
        self.index = 0
        self.shipped = 0

    def current(self) -> Feature:
        if self.index >= len(self.UNLOCKS):
            return self.UNLOCKS[-1]
        return self.UNLOCKS[self.index]

    def is_done(self) -> bool:
        return self.shipped >= len(self.UNLOCKS)

    def on_reset(self) -> None:
        self.index = 0
        self.shipped = 0

    def try_ship(self, *, systems: CoreSystems, abilities: AbilitySystem) -> Feature | None:
        if systems.progress < 100.0 or self.index >= len(self.UNLOCKS):
            return None
        shipped = self.UNLOCKS[self.index]
        self.shipped += 1
        if shipped.name == "Inventory":
            abilities.unlock_inventory()
        elif shipped.name == "Crafting":
            abilities.unlock_crafting()
        elif shipped.name == "Skill Tree":
            abilities.unlock_skill_tree()
        systems.progress = 10.0
        self.index += 1
        return shipped


@dataclass(slots=True)
class Bug:
    x: float
    y: float
    speed: float
    radius: float = 13.0
    attached: bool = False


@dataclass(slots=True)
class BugDifficultyModifiers:
    stability_drain_per_bug: float
    speed_bonus: float
    input_glitch: float
    screen_flicker: float
    crash_risk_per_sec: float


class BugDifficultyScaler:
    @staticmethod
    def stage(bug_count: int) -> int:
        if bug_count <= 0:
            return 0
        if bug_count <= 3:
            return 1
        if bug_count <= 8:
            return 2
        if bug_count <= 12:
            return 3
        return 4

    @staticmethod
    def modifiers(bug_count: int) -> BugDifficultyModifiers:
        stg = BugDifficultyScaler.stage(bug_count)
        if stg == 0:
            return BugDifficultyModifiers(0.0, 0.0, 0.0, 0.0, 0.0)
        if stg == 1:
            return BugDifficultyModifiers(0.32, 0.0, 0.0, 0.0, 0.0)
        if stg == 2:
            return BugDifficultyModifiers(0.40, 10.0, 0.06, 0.0, 0.0)
        if stg == 3:
            return BugDifficultyModifiers(0.52, 18.0, 0.10, 0.35, 0.0)
        return BugDifficultyModifiers(0.68, 28.0, 0.16, 0.55, 0.08)


class BugManager:
    def __init__(self, *, bounds: tuple[float, float, float, float], desk_pos: tuple[float, float]) -> None:
        self.bounds = bounds
        self.desk_pos = desk_pos
        self.bugs: list[Bug] = []
        self.spawn_cooldown = 1.3
        self.spawn_timer = self.spawn_cooldown

    def count(self) -> int:
        return len(self.bugs)

    def clear(self) -> None:
        self.bugs.clear()

    def spawn(self, *, n: int, speed_base: float) -> None:
        if n <= 0:
            return
        x1, y1, x2, y2 = self.bounds
        for _ in range(n):
            side = random.choice(["top", "right", "bottom", "left"])
            if side == "top":
                x, y = random.uniform(x1 + 20, x2 - 20), y1
            elif side == "right":
                x, y = x2, random.uniform(y1 + 20, y2 - 20)
            elif side == "bottom":
                x, y = random.uniform(x1 + 20, x2 - 20), y2
            else:
                x, y = x1, random.uniform(y1 + 20, y2 - 20)
            speed = random.uniform(speed_base * 0.85, speed_base * 1.25)
            self.bugs.append(Bug(x=x, y=y, speed=speed))

    def update_spawning(self, dt: float, *, spawn_mult: float, speed_base: float) -> None:
        self.spawn_timer -= dt
        if self.spawn_timer > 0.0:
            return
        effective_mult = max(0.45, min(spawn_mult, 1.35))
        base = self.spawn_cooldown / effective_mult
        self.spawn_timer = base
        self.spawn(n=1, speed_base=speed_base)

    def remove_near(self, *, x: float, y: float, radius: float) -> int:
        removed = 0
        keep: list[Bug] = []
        r2 = radius * radius
        for bug in self.bugs:
            if (bug.x - x) * (bug.x - x) + (bug.y - y) * (bug.y - y) <= r2:
                removed += 1
            else:
                keep.append(bug)
        self.bugs = keep
        return removed

    def remove_attached(self) -> int:
        removed = sum(1 for bug in self.bugs if bug.attached)
        if removed:
            self.bugs = [bug for bug in self.bugs if not bug.attached]
        return removed

    def update(
        self,
        dt: float,
        *,
        player: Player,
        systems: CoreSystems,
        speed_bonus: float,
        on_squash: callable | None = None,
    ) -> None:
        x1, y1, x2, y2 = self.bounds
        desk_x, desk_y = self.desk_pos
        attached_drain = 0.0
        kept: list[Bug] = []
        for bug in self.bugs:
            if not bug.attached and math.hypot(bug.x - desk_x, bug.y - desk_y) < 24:
                bug.attached = True
            if not bug.attached:
                dx = desk_x - bug.x
                dy = desk_y - bug.y
                dist = math.hypot(dx, dy) or 1.0
                bug.x += (dx / dist) * (bug.speed + speed_bonus) * dt
                bug.y += (dy / dist) * (bug.speed + speed_bonus) * dt
                bug.x = clamp(bug.x, x1 + 10, x2 - 10)
                bug.y = clamp(bug.y, y1 + 10, y2 - 10)
            else:
                attached_drain += 1.25
            if math.hypot(player.x - bug.x, player.y - bug.y) < player.size + bug.radius:
                systems.add_progress(3.2)
                systems.add_stability(0.8)
                systems.add_motivation(0.45)
                if on_squash:
                    on_squash()
                continue
            kept.append(bug)
        self.bugs = kept
        if attached_drain > 0.0:
            systems.add_stability(-attached_drain * dt * 2.2)


@dataclass(slots=True)
class ComplaintPopup:
    x: float
    y: float
    vx: float
    vy: float
    text: str
    timer: float


class ComplaintManager:
    POOL = [
        "Add multiplayer.",
        "Controller support when?",
        "Too many bugs.",
        "UI is confusing.",
        "Needs more hats.",
        "Balance feels off.",
        "My save deleted itself.",
        "Patch this before launch.",
        "Why is crafting mandatory?",
        "This is fun but broken.",
    ]

    def __init__(self, *, bounds: tuple[float, float, float, float]) -> None:
        self.bounds = bounds
        self.popups: list[ComplaintPopup] = []
        self.spawn_timer = 2.8

    def count(self) -> int:
        return len(self.popups)

    def clear(self) -> None:
        self.popups.clear()

    def spawn(self, *, n: int) -> None:
        if n <= 0:
            return
        x1, y1, x2, y2 = self.bounds
        for _ in range(n):
            x = random.uniform(x1 + 60, x2 - 60)
            y = random.uniform(y1 + 50, y2 - 50)
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(24.0, 48.0)
            self.popups.append(
                ComplaintPopup(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    text=random.choice(self.POOL),
                    timer=random.uniform(7.0, 11.0),
                )
            )

    def update_spawning(self, dt: float, *, spawn_mult: float) -> None:
        self.spawn_timer -= dt
        if self.spawn_timer > 0.0:
            return
        self.spawn_timer = random.uniform(3.0, 5.2) / max(0.6, spawn_mult)
        self.spawn(n=1)

    def update(self, dt: float, *, player: Player, systems: CoreSystems) -> None:
        x1, y1, x2, y2 = self.bounds
        kept: list[ComplaintPopup] = []
        for popup in self.popups:
            popup.timer -= dt
            popup.x += popup.vx * dt
            popup.y += popup.vy * dt
            if popup.x < x1 + 24 or popup.x > x2 - 24:
                popup.vx *= -1
            if popup.y < y1 + 24 or popup.y > y2 - 24:
                popup.vy *= -1
            popup.x = clamp(popup.x, x1 + 30, x2 - 30)
            popup.y = clamp(popup.y, y1 + 30, y2 - 30)
            if math.hypot(player.x - popup.x, player.y - popup.y) < player.size + 20:
                systems.add_motivation(6.0)
                systems.add_stability(1.5)
                continue
            if popup.timer > 0.0:
                kept.append(popup)
        self.popups = kept
        if self.popups:
            systems.add_motivation(-(0.22 + 0.06 * len(self.popups)) * dt)
            if len(self.popups) >= 6:
                systems.add_stability(-(0.22 * (len(self.popups) - 5)) * dt)


@dataclass(slots=True)
class PanicState:
    active: bool = False
    intensity: float = 0.0
    bug_spawn_mult: float = 1.0
    shake: float = 0.0
    flash: float = 0.0


class PanicModeManager:
    def __init__(self, *, duration: float) -> None:
        self.duration = max(1.0, duration)
        self.state = PanicState()

    def update(self, dt: float, *, systems: CoreSystems, time_left: float) -> PanicState:
        stability_risk = clamp((30.0 - systems.stability) / 30.0, 0.0, 1.0)
        motivation_risk = clamp((30.0 - systems.motivation) / 30.0, 0.0, 1.0)
        deadline_window = self.duration * 0.25
        deadline_risk = clamp((deadline_window - time_left) / max(1.0, deadline_window), 0.0, 1.0)
        intensity = max(stability_risk, motivation_risk, deadline_risk)
        active = intensity > 0.0
        self.state.active = active
        self.state.intensity = intensity
        self.state.bug_spawn_mult = 1.0 + intensity * 0.55
        self.state.shake = intensity * 1.25
        self.state.flash = max(0.0, self.state.flash - dt)
        if active:
            self.state.flash = max(self.state.flash, 0.12 + intensity * 0.18)
        return self.state


@dataclass(slots=True)
class ChaosEffects:
    bug_spawn_mult: float = 1.0
    bug_speed_bonus: float = 0.0
    progress_mult: float = 1.0
    motivation_drain: float = 0.0
    crash_risk_bonus: float = 0.0
    screen_flash: float = 0.0
    shake: float = 0.0


@dataclass(slots=True)
class ActiveChaosEvent:
    name: str
    description: str
    time_left: float


class ChaosEventManager:
    def __init__(self) -> None:
        self.cooldown = 5.2
        self.timer = self.cooldown
        self.active: ActiveChaosEvent | None = None
        self.toast_text = ""
        self.toast_timer = 0.0

    def set_toast(self, text: str, duration: float = 2.2) -> None:
        self.toast_text = text
        self.toast_timer = max(self.toast_timer, duration)

    def update(
        self,
        dt: float,
        *,
        systems: CoreSystems,
        bugs: BugManager,
        complaints: ComplaintManager,
        difficulty: Difficulty,
    ) -> ChaosEffects:
        effects = ChaosEffects()
        self.toast_timer = max(0.0, self.toast_timer - dt)
        if self.active is None:
            self.timer -= dt
            if self.timer > 0.0:
                return effects
            trigger_chance = clamp(0.16 + difficulty.chaos_meter * 0.55, 0.0, 0.85)
            self.timer = random.uniform(4.2, 6.6) / max(0.6, 1.0 + difficulty.chaos_meter)
            if random.random() > trigger_chance:
                return effects
            self.active = self._roll_event(difficulty)
            self.set_toast(f"CHAOS EVENT: {self.active.name}", 2.4)
            if self.active.name == "System Failure":
                systems.add_stability(-(10.0 + 2.5 * difficulty.level))
            elif self.active.name == "Mass Bug Spawn":
                bugs.spawn(n=max(1, 1 + difficulty.level), speed_base=66.0 + 3.0 * difficulty.level)
            elif self.active.name == "Complaint Storm":
                complaints.spawn(n=2 + difficulty.level)
            return effects
        self.active.time_left -= dt
        if self.active.time_left <= 0.0:
            self.set_toast(f"{self.active.name} ended.", 1.4)
            self.active = None
            return effects
        name = self.active.name
        if name == "Mass Bug Spawn":
            effects.bug_spawn_mult = 1.15 + 0.05 * difficulty.level
            effects.bug_speed_bonus = 4.0
            effects.screen_flash = 0.03
        elif name == "Complaint Storm":
            effects.motivation_drain = 1.2 + 0.35 * difficulty.level
            effects.screen_flash = 0.06
        elif name == "Feature Creep Overload":
            effects.progress_mult = 0.62
            effects.motivation_drain = 0.9 + 0.25 * difficulty.level
            effects.bug_spawn_mult = 1.15
        elif name == "Deadline Rush":
            effects.progress_mult = 1.15
            effects.motivation_drain = 1.15
            effects.bug_spawn_mult = 1.35
            effects.shake = 0.35
        elif name == "System Failure":
            effects.bug_speed_bonus = 10.0 + 3.0 * difficulty.level
            effects.bug_spawn_mult = 1.15
            effects.crash_risk_bonus = 0.04 + 0.01 * difficulty.level
            effects.screen_flash = 0.08
            effects.shake = 0.5
        if name == "Complaint Storm" and random.random() < 0.25 * dt:
            complaints.spawn(n=1)
        return effects

    def _roll_event(self, difficulty: Difficulty) -> ActiveChaosEvent:
        events: list[tuple[str, str, float, int]] = [
            ("Mass Bug Spawn", "A refactor unleashed a nest of bugs.", 5.5, 4),
            ("Complaint Storm", "Influencers found your build.", 6.0, 3),
            ("Feature Creep Overload", "Someone said 'it would be cool if...'", 7.0, 3),
            ("Deadline Rush", "Producer: 'We can still make it, right?'", 6.0, 2),
            ("System Failure", "Build pipeline exploded. Again.", 5.0, 2),
        ]
        weights = []
        for name, _desc, _dur, base_w in events:
            weight = base_w
            if name == "System Failure":
                weight += int(difficulty.level * 1.2)
            if name == "Deadline Rush":
                weight += int(difficulty.chaos_meter * 3)
            weights.append(max(1, weight))
        name, desc, dur, _ = random.choices(events, weights=weights, k=1)[0]
        return ActiveChaosEvent(name=name, description=desc, time_left=dur + 0.3 * difficulty.level)


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
    stipple = "gray25" if alpha < 0.6 else "gray12"
    width = min(680, max(320, 14 * len(text)))
    x1 = (WIDTH - width) / 2
    x2 = x1 + width
    y1 = 52
    y2 = 96
    canvas.create_rectangle(x1, y1, x2, y2, fill="#0b1220", outline="#5fb6ff", width=2, stipple=stipple)
    canvas.create_text(WIDTH / 2, (y1 + y2) / 2, fill="#e7f3ff", font=("Helvetica", 13, "bold"), text=text)


def draw_panic_banner(canvas: tk.Canvas, *, active: bool, intensity: float) -> None:
    if not active:
        return
    pulse = 0.55 + 0.45 * clamp(intensity, 0.0, 1.0)
    canvas.create_rectangle(0, 40, WIDTH, 44, fill="#ff2f2f", outline="", stipple="gray12" if pulse < 0.75 else "gray25")
    canvas.create_text(WIDTH / 2, 62, fill="#ffdddd", font=("Helvetica", 16, "bold"), text="PANIC MODE: STABILIZE THE BUILD")


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

        self.office_bounds = (80.0, 80.0, 880.0, 520.0)
        self.desk_pos = (220.0, 180.0)
        self.support_pos = (740.0, 420.0)

        self.briefing = [
            "SHIP the game by building features at the DEV DESK (SPACE).",
            "SQUASH bugs (Red) and CLEAR complaints (Orange) by moving over them.",
            "USE abilities: Shift (Dash), C (Coffee), E (Patch), X (Craft).",
            "MAINTAIN high stability and motivation to reach the launch window."
        ]
        self.warning = "If Stability hits 0: crash. If Motivation hits 0: burnout."
        self.hints = [
            "Tip: If SPACE is doing nothing, move back to the glowing Dev Desk.",
            "Tip: Emergency Patch clears desk-attached bugs and restores stability.",
            "Tip: Coffee gives a longer work burst; after Inventory it costs one coffee charge.",
            "Tip: Craft patch kits with X after Crafting unlocks, then spend them with E.",
            "Tip: Clear bugs before they hit double digits or the room starts glitching.",
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

        self.automation_on = False
        self.slack_pings: list[dict[str, Any]] = []
        self.ping_timer = 5.0
        self.status_text = ""
        self.in_launch_window = False

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

        self.systems = CoreSystems(progress=18.0, stability=96.0, motivation=90.0)
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
        self.status_text = "Code at the Dev Desk. Stomp bugs. Clear complaints."

        self.automation_on = False
        self.slack_pings = []
        self.ping_timer = 4.0
        self.in_launch_window = False

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

        desk_dist = math.hypot(player.x - self.desk_pos[0], player.y - self.desk_pos[1])
        at_desk = desk_dist < 96.0
        build_pressed = "space" in keys and not self.in_launch_window
        shift_pressed = self.just_pressed(keys, "Shift_L") or self.just_pressed(keys, "Shift_R")
        coffee_pressed = self.just_pressed(keys, "c")
        patch_pressed = self.just_pressed(keys, "e")
        craft_pressed = self.just_pressed(keys, "x")
        debug_pressed = self.just_pressed(keys, "f")
        ping_pressed = self.just_pressed(keys, "q")

        # Baseline drains (the "job"), scaled up by shipped features.
        self.systems.add_motivation(-(0.08 + 0.025 * self.difficulty.level) * dt)
        self.systems.add_motivation(-chaos_fx.motivation_drain * dt)
        if bug_count > 0:
            stability_drain = bug_mod.stability_drain_per_bug * bug_count
            stability_drain *= 0.82 + 0.10 * self.difficulty.level
            self.systems.add_stability(-stability_drain * dt)

        # Live Ops automation: if you're doing well, the build self-heals a little.
        if self.automation_on and self.systems.motivation >= 65.0 and bug_count <= 8:
            self.systems.add_stability(1.15 * dt)

        # Abilities (key taps) are evaluated before movement so the feedback feels instant.
        if self.action_lock <= 0.0:
            if self.abilities.try_dash(shift_pressed):
                removed = self.bugs.remove_near(x=player.x, y=player.y, radius=54.0)
                if removed > 0:
                    self.systems.add_stability(removed * 0.9)
                    self.systems.add_progress(removed * 1.0)
                self.shake = max(self.shake, 0.8)
                self._spawn_particles(player.x, player.y, "#65d6ff", 12, 240)
                self.toast_text = "Dash: burst through bugs and reposition fast."
                self.toast_timer = max(self.toast_timer, 1.3)
                self.action_lock = 0.05

            if self.abilities.try_coffee_boost(coffee_pressed):
                self.systems.add_motivation(22.0)
                self.toast_text = "Coffee Boost: move faster and build faster for a short burst."
                self.toast_timer = max(self.toast_timer, 1.9)
                self.screen_flash = max(self.screen_flash, 0.08)
                self.action_lock = 0.12

            if self.abilities.try_emergency_patch(patch_pressed):
                fixed_attached = self.bugs.remove_attached()
                self.systems.add_stability(16.0 + fixed_attached * 4.0)
                self.systems.add_motivation(-6.0)
                self.toast_text = f"Emergency Patch: restored stability and cleared {fixed_attached} desk bugs."
                self.toast_timer = max(self.toast_timer, 2.0)
                self.screen_flash = max(self.screen_flash, 0.12)
                self.shake = max(self.shake, 0.9)
                self._spawn_particles(self.desk_pos[0], self.desk_pos[1], "#50fa7b", 16, 210)
                self.action_lock = 0.14

            if craft_pressed and self.abilities.can_craft_patch_kit():
                if self.abilities.craft_patch_kit():
                    self.toast_text = "Crafted Patch Kit: E is stocked."
                    self.toast_timer = max(self.toast_timer, 1.8)
                    self.screen_flash = max(self.screen_flash, 0.08)
                    self.action_lock = 0.18

            if self.abilities.try_debug_burst(debug_pressed):
                removed = self.bugs.remove_near(x=player.x, y=player.y, radius=96.0)
                if removed > 0:
                    self.systems.add_progress(6.0 + removed * 1.4)
                    self.systems.add_stability(4.0 + removed * 0.5)
                self.systems.add_motivation(-5.0)
                self.toast_text = f"Debug Burst: purged {removed} bugs in a radius."
                self.toast_timer = max(self.toast_timer, 1.8)
                self.screen_flash = max(self.screen_flash, 0.12)
                self.shake = max(self.shake, 1.3)
                self._spawn_particles(player.x, player.y, "#ffb86c", 22, 260)
                self.action_lock = 0.14

            # Slack Pings (Q)
            if ping_pressed:
                for ping in list(self.slack_pings):
                    if math.hypot(player.x - ping["x"], player.y - ping["y"]) < 60:
                        self.slack_pings.remove(ping)
                        self.systems.add_motivation(8.0)
                        self.systems.add_stability(2.0)
                        self.toast_text = "Ping cleared: Technical debt addressed."
                        self.toast_timer = 1.2
                        self.shake = 0.5
                        break

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
        speed = 380.0
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

        # Coding is anchored to the desk so the objective reads clearly.
        coding = build_pressed and at_desk
        if coding:
            progress_rate = 19.0 + 1.8 * self.difficulty.level
            progress_mult = chaos_fx.progress_mult * self.abilities.coffee_multiplier()
            self.systems.add_progress(progress_rate * progress_mult * dt)
            self.systems.add_motivation(-(0.55 + 0.10 * self.difficulty.level) * dt)
        elif build_pressed and not at_desk:
            self.status_text = "Move to the glowing Dev Desk to build progress."

        # Spawns and entity updates.
        base_spawn = 0.72 + 0.05 * self.difficulty.level
        spawn_mult = base_spawn * chaos_fx.bug_spawn_mult * panic_state.bug_spawn_mult
        if coding:
            spawn_mult *= 1.05
        speed_base = 50.0 + 3.5 * self.difficulty.level
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

        # Update Pings spawning
        self.ping_timer -= dt
        if self.ping_timer <= 0 and len(self.slack_pings) < 13:
            px = random.uniform(self.office_bounds[0] + 50, self.office_bounds[2] - 50)
            py = random.uniform(self.office_bounds[1] + 50, self.office_bounds[3] - 50)
            # Avoid stations
            if math.hypot(px - self.desk_pos[0], py - self.desk_pos[1]) > 100 and \
               math.hypot(px - self.support_pos[0], py - self.support_pos[1]) > 100:
                self.slack_pings.append({"x": px, "y": py, "life": random.uniform(7.0, 10.0)})
                self.ping_timer = random.uniform(1.5, 3.5)

        for ping in list(self.slack_pings):
            ping["life"] -= dt
            if ping["life"] <= 0:
                self.slack_pings.remove(ping)
                self.systems.add_motivation(-5.0)
                self.shake = 1.0

        # Crash risk spikes (13+ bugs and/or System Failure).
        crash_per_sec = bug_mod.crash_risk_per_sec + chaos_fx.crash_risk_bonus
        if crash_per_sec > 0.0 and random.random() < crash_per_sec * dt:
            spike = 20.0 + 4.0 * self.difficulty.level
            self.systems.add_stability(-spike)
            self.toast_text = "Crash spike: stack trace everywhere."
            self.toast_timer = max(self.toast_timer, 2.0)
            self.screen_flash = max(self.screen_flash, 0.18)
            self.shake = max(self.shake, 1.8)
            self._spawn_particles(self.desk_pos[0], self.desk_pos[1], "#ff5555", 28, 320)

        # Ship features.
        shipped = self.features.try_ship(systems=self.systems, abilities=self.abilities)
        if shipped:
            self.systems.add_stability(-(4.0 + 1.3 * self.difficulty.level))
            self.systems.add_motivation(-(3.5 + 1.0 * self.difficulty.level))
            self.toast_text = f"FEATURE SHIPPED: {shipped.name}  |  {shipped.hook}"
            self.toast_timer = max(self.toast_timer, 3.0)
            self.screen_flash = max(self.screen_flash, 0.14)
            self.shake = max(self.shake, 1.2)
            self.bugs.spawn(n=1 + self.difficulty.level // 2, speed_base=74.0 + 4.0 * self.difficulty.level)
            self.complaints.spawn(n=1 + self.difficulty.level // 2)
            if shipped.name == "Upgrade Menu":
                self.abilities.cooldown_scale = 0.85
            if shipped.name == "Live Ops":
                self.automation_on = True
                self.in_launch_window = True
                self.launch_timer = 9.0
                self.toast_text = "LAUNCH WINDOW: survive 9 seconds with stability above zero."
                self.toast_timer = max(self.toast_timer, 3.2)

        # Launch window logic (high intensity finale).
        if self.in_launch_window:
            self.launch_timer = max(0.0, self.launch_timer - dt)
            self.systems.add_motivation(-0.35 * dt)
            self.bugs.update_spawning(dt, spawn_mult=1.45 + panic_state.intensity, speed_base=78.0 + 6.0 * self.difficulty.level)
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

        if self.in_launch_window:
            self.status_text = "Hold the build together until the launch timer ends."
        elif bug_count >= 9:
            self.status_text = "Bug swarm building. Clear red bugs before crash pressure spikes."
        elif self.complaints.count() >= 5:
            self.status_text = "Community backlash rising. Run through complaint cards."
        elif self.systems.progress >= 100.0:
            self.status_text = "Feature ready. Shipping now."
        elif at_desk:
            self.status_text = "At desk: hold SPACE to build the next feature."
        else:
            self.status_text = "Move to the Dev Desk to code, then clean bugs and complaints."

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

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        if self.in_launch_window:
            return ("STABILIZE the build! Use E to patch and Shift to dash until the launch timer ends.", (self.desk_pos[0], self.desk_pos[1]))
            
        if self.bugs.count() >= 8:
            # Target the nearest bug
            bug = min(self.bugs.bugs, key=lambda b: math.hypot(player.x - b.x, player.y - b.y))
            return ("Bug infestation! Shift-Dash through red bugs to squash them and restore stability.", (float(bug.x), float(bug.y)))
            
        if self.complaints.count() >= 5:
            # Target the nearest complaint
            popup = min(self.complaints.popups, key=lambda p: math.hypot(player.x - p.x, player.y - p.y))
            return ("Community backlash! Run through the orange complaint cards to restore motivation.", (float(popup.x), float(popup.y)))
            
        if self.slack_pings:
            # Target the nearest ping
            ping = min(self.slack_pings, key=lambda p: math.hypot(player.x - p["x"], player.y - p["y"]))
            return ("Technical debt! Press Q near BLUE PINGS to clear them and boost motivation.", (float(ping["x"]), float(ping["y"])))
            
        if self.systems.progress < 100.0:
            if math.hypot(player.x - self.desk_pos[0], player.y - self.desk_pos[1]) > 100:
                return ("Move to the glowing Dev Desk to code and build the next feature.", (self.desk_pos[0], self.desk_pos[1]))
            return ("Hold SPACE at the Dev Desk to ship the next feature.", (self.desk_pos[0], self.desk_pos[1]))
            
        return ("Ship the ready feature and monitor stability.", (self.desk_pos[0], self.desk_pos[1]))

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
        support_x, support_y = self.support_pos[0] + ox, self.support_pos[1] + oy

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

        canvas.create_rectangle(support_x - 88, support_y - 30, support_x + 88, support_y + 30, fill="#121a27", outline="#ffb86c", width=2)
        canvas.create_text(support_x, support_y - 8, text="COMMUNITY FEED", fill="#ffe6c7", font=("Helvetica", 11, "bold"))
        canvas.create_text(support_x, support_y + 12, text="Run through cards to reply", fill="#d9b88d", font=("Helvetica", 9, "bold"))

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

        # Draw Pings
        for ping in self.slack_pings:
            px, py = ping["x"] + ox, ping["y"] + oy
            pulse = 4 * math.sin(time.time() * 10)
            canvas.create_oval(px - 20 - pulse, py - 20 - pulse, px + 20 + pulse, py + 20 + pulse, fill="#65d6ff", outline="#fff", width=2)
            canvas.create_text(px, py, text="PING", fill="#000", font=("Helvetica", 10, "bold"))
            canvas.create_text(px, py + 14, text="Q", fill="#000", font=("Helvetica", 8, "bold"))

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
        canvas.create_text(340, 118, anchor="w", fill="#f7d794", font=("Helvetica", 10, "bold"), text=self.status_text)

        ax = WIDTH - 280
        canvas.create_rectangle(ax, 46, WIDTH - 14, 176, fill="#0b1220", outline="#21486b", width=2)
        canvas.create_text(ax + 10, 56, anchor="w", fill="#e7f3ff", font=("Helvetica", 10, "bold"), text="Abilities")
        dash_state = "READY" if self.abilities.dash.cooldown <= 0.0 else f"CD {self.abilities.dash.cooldown:0.1f}s"
        canvas.create_text(ax + 10, 76, anchor="w", fill=TEXT, font=("Helvetica", 10, "bold"), text=f"Shift Dash   {dash_state}  Burst move + squash")
        patch_state = "READY" if self.abilities.emergency_patch.cooldown <= 0.0 else f"CD {self.abilities.emergency_patch.cooldown:0.1f}s"
        patch_suffix = f"Kits {self.abilities.patch_kits}" if self.abilities.has_crafting else "No kit needed yet"
        canvas.create_text(ax + 10, 92, anchor="w", fill=TEXT, font=("Helvetica", 10, "bold"), text=f"E Patch      {patch_state}  {patch_suffix}")
        canvas.create_text(
            ax + 10,
            108,
            anchor="w",
            fill=TEXT,
            font=("Helvetica", 10, "bold"),
            text=f"C Coffee     {'READY' if self.abilities.coffee_boost.cooldown <= 0.0 else f'CD {self.abilities.coffee_boost.cooldown:0.1f}s'}  Coffee {self.abilities.coffee_charges}",
        )
        craft_text = "X Craft Kit  LOCKED" if not self.abilities.has_crafting else f"X Craft Kit  {'READY' if self.abilities.can_craft_patch_kit() else 'Need 3 coffee'}"
        canvas.create_text(ax + 10, 124, anchor="w", fill=TEXT, font=("Helvetica", 10, "bold"), text=craft_text)
        debug_text = "F Debug      LOCKED" if not self.abilities.has_skill_tree else f"F Debug      {'READY' if self.abilities.debug_burst.cooldown <= 0.0 else f'CD {self.abilities.debug_burst.cooldown:0.1f}s'}"
        canvas.create_text(ax + 10, 140, anchor="w", fill=TEXT, font=("Helvetica", 10, "bold"), text=debug_text)
        canvas.create_text(ax + 10, 158, anchor="w", fill="#8fb4cf", font=("Helvetica", 9, "bold"), text="Inventory unlock makes coffee drop from bugs.")

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
