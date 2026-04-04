"""Compatibility wrapper.

The project has a shared `src.player.Player` used across many worlds.
The Game Developer world uses abilities and modifiers, but still uses the same Player class.
"""

from src.player import Player

__all__ = ["Player"]

