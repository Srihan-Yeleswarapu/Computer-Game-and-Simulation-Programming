from __future__ import annotations

import math
import random
from dataclasses import dataclass

from src.player import Player
from src.utils import clamp

from .systems import CoreSystems


@dataclass(slots=True)
class Bug:
    x: float
    y: float
    speed: float
    radius: float = 13.0
    attached: bool = False  # attached to the dev desk (drains stability hard)


@dataclass(slots=True)
class BugDifficultyModifiers:
    stability_drain_per_bug: float
    speed_bonus: float
    input_glitch: float  # 0..1 chance each frame to "misread" direction
    screen_flicker: float  # 0..1 strength
    crash_risk_per_sec: float  # 0..1 chance per second to crash-proc


class BugDifficultyScaler:
    """Escalates the build instability based on current bug count."""

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
        # 13+ bugs: you're playing with fire.
        return BugDifficultyModifiers(0.68, 28.0, 0.16, 0.55, 0.08)


class BugManager:
    def __init__(self, *, bounds: tuple[float, float, float, float], desk_pos: tuple[float, float]) -> None:
        self.bounds = bounds
        self.desk_pos = desk_pos
        self.bugs: list[Bug] = []
        self.spawn_cooldown = 0.6
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
        # Spawn pacing stays tight to avoid "walking simulator" vibes.
        base = self.spawn_cooldown / max(0.35, spawn_mult)
        self.spawn_timer = random.uniform(base * 0.75, base * 1.25)
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
            # If it attaches to the desk, it becomes a stability leak until stomped.
            if not bug.attached and math.hypot(bug.x - desk_x, bug.y - desk_y) < 24:
                bug.attached = True

            if not bug.attached:
                dx = desk_x - bug.x
                dy = desk_y - bug.y
                dist = math.hypot(dx, dy) or 1.0
                vx = dx / dist
                vy = dy / dist
                bug.x += vx * (bug.speed + speed_bonus) * dt
                bug.y += vy * (bug.speed + speed_bonus) * dt
                bug.x = clamp(bug.x, x1 + 10, x2 - 10)
                bug.y = clamp(bug.y, y1 + 10, y2 - 10)
            else:
                attached_drain += 1.25

            if math.hypot(player.x - bug.x, player.y - bug.y) < player.size + bug.radius:
                # Squash: instant reward, plus feeds inventory once unlocked.
                systems.add_progress(3.2)
                systems.add_stability(0.8)
                systems.add_motivation(0.45)
                if on_squash:
                    on_squash()
                continue

            kept.append(bug)

        self.bugs = kept

        if attached_drain > 0.0:
            systems.add_stability(-attached_drain * dt * 3.4)

