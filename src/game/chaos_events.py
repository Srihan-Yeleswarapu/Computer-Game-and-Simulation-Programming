from __future__ import annotations

import random
from dataclasses import dataclass

from src.utils import clamp

from .bugs import BugManager
from .complaints import ComplaintManager
from .systems import CoreSystems, Difficulty


@dataclass(slots=True)
class ChaosEffects:
    bug_spawn_mult: float = 1.0
    bug_speed_bonus: float = 0.0
    progress_mult: float = 1.0
    motivation_drain: float = 0.0  # per second
    crash_risk_bonus: float = 0.0  # per second
    screen_flash: float = 0.0
    shake: float = 0.0


@dataclass(slots=True)
class ActiveChaosEvent:
    name: str
    description: str
    time_left: float


class ChaosEventManager:
    """Random high-impact events that create dramatic swings and urgency."""

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

            # Trigger chance ramps hard as you ship features and the deadline approaches.
            trigger_chance = clamp(0.16 + difficulty.chaos_meter * 0.55, 0.0, 0.85)
            self.timer = random.uniform(4.2, 6.6) / max(0.6, 1.0 + difficulty.chaos_meter)
            if random.random() > trigger_chance:
                return effects

            self.active = self._roll_event(difficulty)
            self.set_toast(f"CHAOS EVENT: {self.active.name}", 2.4)
            # One-time impact on start.
            if self.active.name == "System Failure":
                systems.add_stability(-(10.0 + 2.5 * difficulty.level))
            elif self.active.name == "Mass Bug Spawn":
                bugs.spawn(n=4 + 2 * difficulty.level, speed_base=70.0 + 4.0 * difficulty.level)
            elif self.active.name == "Complaint Storm":
                complaints.spawn(n=2 + difficulty.level)
            return effects

        # Active event effects.
        self.active.time_left -= dt
        if self.active.time_left <= 0.0:
            self.set_toast(f"{self.active.name} ended.", 1.4)
            self.active = None
            return effects

        name = self.active.name
        if name == "Mass Bug Spawn":
            effects.bug_spawn_mult = 1.55 + 0.10 * difficulty.level
            effects.bug_speed_bonus = 10.0
            effects.screen_flash = 0.08
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
            effects.bug_spawn_mult = 1.75
            effects.shake = 0.55
        elif name == "System Failure":
            effects.bug_speed_bonus = 18.0 + 4.0 * difficulty.level
            effects.bug_spawn_mult = 1.25
            effects.crash_risk_bonus = 0.06 + 0.02 * difficulty.level
            effects.screen_flash = 0.10
            effects.shake = 0.8

        # Small ongoing random spikes during storms.
        if name in {"Mass Bug Spawn", "Complaint Storm"} and random.random() < 0.25 * dt:
            if name == "Mass Bug Spawn":
                bugs.spawn(n=1, speed_base=80.0 + 3.0 * difficulty.level)
            else:
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
        # More failure events later.
        weights = []
        for name, _desc, _dur, base_w in events:
            w = base_w
            if name == "System Failure":
                w += int(difficulty.level * 1.2)
            if name == "Deadline Rush":
                w += int(difficulty.chaos_meter * 3)
            weights.append(max(1, w))
        choice = random.choices(events, weights=weights, k=1)[0]
        name, desc, dur, _ = choice
        dur = dur + 0.3 * difficulty.level
        return ActiveChaosEvent(name=name, description=desc, time_left=dur)

