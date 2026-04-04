from __future__ import annotations

import math
import random
from dataclasses import dataclass

from src.player import Player
from src.utils import clamp

from .systems import CoreSystems


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
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.popups.append(
                ComplaintPopup(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
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
                # "Reply" by running into it. No inbox walking, just momentum.
                systems.add_motivation(6.0)
                systems.add_stability(1.5)
                continue

            if popup.timer > 0.0:
                kept.append(popup)

        self.popups = kept

        if self.popups:
            # Passive drain scales up quickly, making popups urgent.
            systems.add_motivation(-(0.22 + 0.06 * len(self.popups)) * dt)
            if len(self.popups) >= 6:
                systems.add_stability(-(0.22 * (len(self.popups) - 5)) * dt)

