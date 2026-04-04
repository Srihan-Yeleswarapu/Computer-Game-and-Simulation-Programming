"""Quick entrypoint for iterating on the Game Developer world.

This keeps the repo's root `main.py` unchanged.
"""

from src.game_engine import GameEngine


def run_game_developer_world() -> None:
    engine = GameEngine()
    # "e" is the shortcut key for Game Developer in `src/game_engine.py`.
    engine.start_world("e")
    engine.run()


if __name__ == "__main__":
    run_game_developer_world()

