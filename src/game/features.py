from __future__ import annotations

from dataclasses import dataclass

from .abilities import AbilitySystem
from .systems import CoreSystems


@dataclass(slots=True)
class Feature:
    name: str
    hook: str


class FeatureUnlockManager:
    """Turns progress into discrete feature ships with meaningful new mechanics."""

    BASELINE = Feature("Core Loop", "Dash is online. Ship features before the build collapses.")

    UNLOCKS = [
        Feature("Inventory", "Coffee drops from squashed bugs. C now consumes coffee."),
        Feature("Crafting", "Craft patch kits from 3 coffee. E consumes a patch kit."),
        Feature("Skill Tree", "Debug Burst unlocked (F). Emergency control of swarms."),
        Feature("Upgrade Menu", "Cooldowns shrink. Momentum becomes a build strategy."),
        Feature("Live Ops", "Automation enabled. High motivation slowly restores stability."),
    ]

    def __init__(self) -> None:
        self.index = 0  # 0..len(UNLOCKS) (next unlock)
        self.shipped = 0  # number of unlocks shipped

    def current(self) -> Feature:
        if self.index >= len(self.UNLOCKS):
            return self.UNLOCKS[-1]
        return self.UNLOCKS[self.index]

    def is_done(self) -> bool:
        return self.shipped >= len(self.UNLOCKS)

    def on_reset(self) -> None:
        self.index = 0
        self.shipped = 0

    def try_ship(
        self,
        *,
        systems: CoreSystems,
        abilities: AbilitySystem,
    ) -> Feature | None:
        """Ship the next feature if progress is full.

        Returns the shipped feature if a ship happened.
        """
        if systems.progress < 100.0:
            return None

        if self.index >= len(self.UNLOCKS):
            return None

        shipped = self.UNLOCKS[self.index]
        self.shipped += 1

        # Apply unlock effects.
        if shipped.name == "Inventory":
            abilities.unlock_inventory()
        elif shipped.name == "Crafting":
            abilities.unlock_crafting()
        elif shipped.name == "Skill Tree":
            abilities.unlock_skill_tree()
        elif shipped.name == "Upgrade Menu":
            # Light, readable "upgrade menu": just reduce cooldowns via world-level multipliers.
            pass
        elif shipped.name == "Live Ops":
            pass

        # Prepare next sprint.
        systems.progress = 10.0
        self.index += 1
        return shipped
