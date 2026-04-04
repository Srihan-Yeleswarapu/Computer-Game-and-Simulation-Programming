from __future__ import annotations

from dataclasses import dataclass

from src.utils import clamp

from .systems import CoreSystems


@dataclass(slots=True)
class PanicState:
    active: bool = False
    intensity: float = 0.0  # 0..1
    bug_spawn_mult: float = 1.0
    shake: float = 0.0
    flash: float = 0.0


class PanicModeManager:
    """High-intensity mode that kicks in when the run is about to collapse."""

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
        self.state.bug_spawn_mult = 1.0 + intensity * 1.05
        self.state.shake = intensity * 1.25
        self.state.flash = max(0.0, self.state.flash - dt)
        if active:
            # The warning needs to be visually loud, even with placeholder audio.
            self.state.flash = max(self.state.flash, 0.12 + intensity * 0.18)
        return self.state

