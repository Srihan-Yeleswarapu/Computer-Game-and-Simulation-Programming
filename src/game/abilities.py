from __future__ import annotations

from dataclasses import dataclass

from src.utils import clamp


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

        self.cooldown_scale = 1.0  # lowered by later feature unlocks

        # Charges are used once "Inventory" ships.
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

    def try_dash(self, keys: set[str]) -> bool:
        if self.dash.cooldown > 0.0:
            return False
        if not ({"Shift_L", "Shift_R"} & keys):
            return False
        self.dash.active = 0.22
        self.dash.cooldown = 1.8 * self.cooldown_scale
        return True

    def dash_multiplier(self) -> float:
        return 2.25 if self.dash.active > 0.0 else 1.0

    def try_emergency_patch(self, keys: set[str]) -> bool:
        if self.emergency_patch.cooldown > 0.0:
            return False
        if "e" not in keys:
            return False
        if self.has_crafting and self.patch_kits <= 0:
            return False
        if self.has_crafting:
            self.patch_kits -= 1
        self.emergency_patch.cooldown = 7.5 * self.cooldown_scale
        return True

    def try_coffee_boost(self, keys: set[str]) -> bool:
        if self.coffee_boost.cooldown > 0.0:
            return False
        if "c" not in keys:
            return False
        if self.has_inventory:
            if self.coffee_charges <= 0:
                return False
            self.coffee_charges -= 1
        self.coffee_boost.active = 3.0
        base_cd = 9.5 if self.has_inventory else 13.0
        self.coffee_boost.cooldown = base_cd * self.cooldown_scale
        return True

    def coffee_multiplier(self) -> float:
        return 1.25 if self.coffee_boost.active > 0.0 else 1.0

    def try_debug_burst(self, keys: set[str]) -> bool:
        if not self.has_skill_tree:
            return False
        if self.debug_burst.cooldown > 0.0:
            return False
        if "f" not in keys:
            return False
        self.debug_burst.cooldown = 11.5 * self.cooldown_scale
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
        if not self.has_inventory:
            return
        # Coffee drops keep abilities flowing without forcing extra travel.
        self.coffee_charges = int(clamp(self.coffee_charges + 1, 0, 9))
