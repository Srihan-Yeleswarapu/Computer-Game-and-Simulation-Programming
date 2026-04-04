from __future__ import annotations

from dataclasses import dataclass

from src.utils import clamp


@dataclass(slots=True)
class CoreSystems:
    """The only 3 player-facing resources for the Game Developer world."""

    progress: float = 0.0  # 0..100, fills to ship the next feature
    stability: float = 100.0  # 0..100, when 0 the build crashes
    motivation: float = 100.0  # 0..100, when 0 the dev burns out

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
    """Tuning knobs that scale up as features ship and chaos escalates."""

    level: int = 0  # grows as features ship
    chaos_meter: float = 0.0  # grows slowly over the run (0..1-ish)

    def advance(self, shipped_features: int, time_ratio: float) -> None:
        # time_ratio: 0 at start, 1 at end
        self.level = shipped_features
        self.chaos_meter = clamp(0.15 + shipped_features * 0.12 + time_ratio * 0.55, 0.0, 1.3)

