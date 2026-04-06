from __future__ import annotations

import json
import math
import os
import random
import tkinter as tk
from dataclasses import dataclass

from src.player import Player
from src.utils import HEIGHT, WIDTH, Particle, clamp
from src.worlds.base import BaseWorld


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROGRESS_FILE = os.path.join(PROJECT_ROOT, "game_dev_progress.json")


@dataclass
class BugEnemy:
    x: float
    y: float
    speed: float
    radius: float = 13.0


@dataclass
class Complaint:
    text: str
    timer: float
    mood: str


class GameDeveloperWorld(BaseWorld):
    FEATURE_SEQUENCE = [
        ("Core Loop", "Ship a playable loop before your scope gets ideas."),
        ("Inventory", "A backpack system appears because players want more loot."),
        ("Crafting", "Now every item wants recipes, ingredients, and UI."),
        ("Skill Tree", "Progression gets bolted on halfway through production."),
        ("Upgrade Menu", "The pause screen becomes its own side project."),
        ("Live Ops", "Post-launch plans somehow arrive before launch itself."),
    ]
    FEATURE_STATIONS = {
        "Core Loop": {"label": "Code Desk", "x": 218.0, "y": 208.0, "color": "#69d2e7"},
        "Inventory": {"label": "Backpack UI", "x": 460.0, "y": 138.0, "color": "#86efac"},
        "Crafting": {"label": "Craft Bench", "x": 740.0, "y": 158.0, "color": "#facc15"},
        "Skill Tree": {"label": "Talent Board", "x": 738.0, "y": 420.0, "color": "#c084fc"},
        "Upgrade Menu": {"label": "Menu Forge", "x": 468.0, "y": 476.0, "color": "#fb7185"},
        "Live Ops": {"label": "Patch Terminal", "x": 208.0, "y": 428.0, "color": "#f97316"},
    }
    SYSTEM_EFFECTS = {
        "movement": "Movement code unstable",
        "jumping": "Traversal script broken",
        "ui": "UI renderer offline",
        "enemy ai": "Bug AI overclocked",
        "build tools": "Build pipeline jammed",
    }
    COMPLAINT_POOL = [
        "Game too hard.",
        "Game too easy.",
        "Add multiplayer.",
        "Graphics outdated.",
        "Too many bugs.",
        "Where is controller support?",
        "Why is the inventory nested?",
        "Needs more hats.",
        "Can you patch this before launch?",
        "I miss the old prototype.",
    ]
    PRAISE_POOL = [
        "This actually feels promising.",
        "Nice bug fix, weirdly satisfying.",
        "The build survives for almost minutes now.",
        "Okay, the new feature kind of rules.",
    ]

    def __init__(self) -> None:
        super().__init__(
            name="Game Developer",
            summary="Survive feature creep, chain-reaction bugs, and a deadline monster long enough to ship your own game.",
            duration=120.0,
        )
        self.briefing = [
            "You are a solo dev in the last stretch before release.",
            "Walk onto any unlocked station to build progress. The highlighted station gives a bonus.",
            "Use the Feedback Inbox with E, SPACE, or ENTER to clear complaints, and the Debug Console to start repairs.",
            "Red bugs crawl through the studio. Squash them by running through them before they wreck morale and stability.",
            "Every new feature makes the project stronger and harder to manage.",
            "In the repair puzzle, press 1-6 in the shown order. In release phase, keep stability alive until the countdown ends.",
        ]
        self.warning = "Clear loop: build on stations, stomp bugs, use interact on the inbox or console, then survive release."
        self.hints = [
            "Tip: Any unlocked station builds progress. The highlighted one builds faster.",
            "Tip: Walk into the Feedback Inbox to remove one complaint and recover morale.",
            "Tip: Walk into the Debug Console, then follow the highlighted repair node order.",
            "Tip: Low motivation slows movement and coding speed.",
            "Tip: In release phase, prioritize stability over progress.",
        ]
        self.auto_finish_on_timer = False
        self.meta = self.load_meta()
        self.review_log: list[str] = []
        self.office_bounds = (88.0, 88.0, 872.0, 548.0)
        self.progress = 0.0
        self.motivation = 0.0
        self.stability = 0.0
        self.complexity = 0.0
        self.deadline_distance = 0.0
        self.phase = "development"
        self.release_countdown = 18.0
        self.features_unlocked = 1
        self.last_feature_index = 0
        self.focus_feature = "Core Loop"
        self.active_glitches: dict[str, float] = {}
        self.bug_enemies: list[BugEnemy] = []
        self.complaints: list[Complaint] = []
        self.broken_systems: list[str] = []
        self.current_repair: dict[str, object] | None = None
        self.spawn_timer = 1.0
        self.event_timer = 4.0
        self.complaint_timer = 3.0
        self.praise_timer = 10.0
        self.station_task_timer = 0.0
        self.active_station_task = ""
        self.feedback_flash = 0.0
        self.screen_flash = 0.0
        self.review_score = 0.0
        self.section_checkpoint = {"progress": 0.0, "feature_index": 0}
        self.feedback_cooldown = 0.0
        self.interact_cooldown = 0.0
        self.deadline_overrun = 0.0

    def get_priority_text(self) -> str:
        if self.phase == "release":
            return "Hold any station to stabilize the build until the release timer ends."
        if self.current_repair:
            return f"Repair {self.current_repair['system']}: press 1-6 in the shown order."
        if self.broken_systems:
            return f"Broken system: {self.broken_systems[0]}. Go to the Debug Console and press E."
        active_complaints = sum(1 for complaint in self.complaints if complaint.mood != "praise")
        if active_complaints >= 3:
            return "Inbox overloaded. Go to the Feedback Inbox and press E to clear a complaint."
        if self.bug_enemies:
            return "Stomp nearby bugs before they reach the Code Desk."
        return f"Build at {self.active_station_task}. Any unlocked station works."

    def get_station_prompt(self, player: Player, feature_name: str) -> str:
        station = self.FEATURE_STATIONS[feature_name]
        if math.hypot(player.x - station["x"], player.y - station["y"]) < 42:
            if self.phase == "release":
                return "Stabilizing"
            if feature_name == self.active_station_task:
                return "Coding + bonus"
            return "Coding"
        if feature_name == self.active_station_task:
            return "Priority"
        return "Optional"

    def load_meta(self) -> dict[str, int | float]:
        default = {"best_review": 0, "best_features": 1, "clears": 0}
        if not os.path.exists(PROGRESS_FILE):
            return default
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
                loaded = json.load(file)
            if not isinstance(loaded, dict):
                return default
            for key in default:
                value = loaded.get(key, default[key])
                if isinstance(value, (int, float)):
                    default[key] = value
        except Exception:
            return default
        return default

    def save_meta(self) -> None:
        try:
            with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
                json.dump(self.meta, file, indent=2)
        except Exception:
            pass

    def reset(self, player: Player) -> None:
        player.reset(180, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.grade = "-"
        self.phase = "development"
        self.release_countdown = 18.0
        self.progress = 6.0
        self.motivation = 84.0
        self.stability = 92.0
        self.complexity = 8.0
        self.deadline_distance = 1.0
        self.features_unlocked = 1
        self.last_feature_index = 0
        self.focus_feature = "Core Loop"
        self.active_glitches = {}
        self.bug_enemies = []
        self.complaints = []
        self.broken_systems = []
        self.current_repair = None
        self.spawn_timer = 1.0
        self.event_timer = 4.5
        self.complaint_timer = 2.5
        self.praise_timer = 11.0
        self.station_task_timer = 1.5
        self.active_station_task = "Core Loop"
        self.feedback_flash = 0.0
        self.screen_flash = 0.0
        self.review_log = []
        self.review_score = 0.0
        self.shake = 0.0
        self.particles = []
        self.section_checkpoint = {"progress": self.progress, "feature_index": 0}
        self.feedback_cooldown = 0.0
        self.interact_cooldown = 0.0
        self.deadline_overrun = 0.0

    def update(
        self,
        dt: float,
        canvas: tk.Canvas,
        player: Player,
        keys: set[str],
        mouse_pos: tuple[int, int],
    ) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        self.feedback_flash = max(0.0, self.feedback_flash - dt)
        self.screen_flash = max(0.0, self.screen_flash - dt)
        self.feedback_cooldown = max(0.0, self.feedback_cooldown - dt)
        self.interact_cooldown = max(0.0, self.interact_cooldown - dt)
        self.update_particles(dt)
        self.update_glitches(dt)
        self.update_player(dt, player, keys)
        self.update_deadline(dt, player)
        if self.finished:
            self.draw(canvas, player)
            return
        self.update_bug_spawns(dt)
        self.update_bug_enemies(dt, player)
        self.update_complaints(dt)
        self.update_station_task(dt, player, keys)
        self.update_repair_puzzle(dt, player, keys)
        self.update_phase_logic(dt, player)
        self.draw(canvas, player)

    def update_player(self, dt: float, player: Player, keys: set[str]) -> None:
        effective_keys = set(keys)
        if "reverse_controls" in self.active_glitches:
            swapped = {"Left": "Right", "Right": "Left", "Up": "Down", "Down": "Up", "a": "d", "d": "a", "w": "s", "s": "w"}
            effective_keys = {swapped.get(key, key) for key in effective_keys}

        original_speed = player.speed
        original_accel = player.accel
        speed_scalar = 0.58 + (self.motivation / 100.0) * 0.62
        if "movement" in self.broken_systems:
            speed_scalar *= 0.72
        if "jumping" in self.broken_systems:
            player.accel = 6.0
        if "enemy ai" in self.broken_systems:
            speed_scalar *= 0.92
        player.speed = 360.0 * speed_scalar
        player.update(dt, effective_keys, self.office_bounds)
        player.speed = original_speed
        player.accel = original_accel

    def update_glitches(self, dt: float) -> None:
        for name in list(self.active_glitches):
            self.active_glitches[name] = max(0.0, self.active_glitches[name] - dt)

        if "crash_risk" in self.active_glitches and self.active_glitches["crash_risk"] <= 0.75:
            self.trigger_crash()
        expired = [name for name, timer in self.active_glitches.items() if timer <= 0.0]
        for name in expired:
            self.active_glitches.pop(name, None)

        if "screen_flicker" in self.active_glitches:
            self.screen_flash = max(self.screen_flash, 0.14)

    def update_deadline(self, dt: float, player: Player) -> None:
        pressure = 1.0 - (self.timer / self.duration)
        advance = clamp((pressure - 0.62) / 0.38, 0.0, 1.0)
        self.deadline_distance = 0.18 if self.phase == "release" else 1.0 - advance
        deadline_x = self.get_deadline_x()
        desk_x = self.FEATURE_STATIONS["Core Loop"]["x"]
        if self.phase == "development" and deadline_x <= desk_x + 24:
            self.deadline_overrun += dt
            self.progress = max(0.0, self.progress - 0.9 * dt)
            self.stability = max(0.0, self.stability - 1.1 * dt)
            self.motivation = max(0.0, self.motivation - 0.8 * dt)
            self.message = "Deadline pressure is crushing the sprint. Keep shipping anyway."
        else:
            self.deadline_overrun = max(0.0, self.deadline_overrun - dt * 0.5)

        pressure_drain = (0.18 + self.complexity * 0.006) * dt
        if self.phase == "release":
            pressure_drain *= 1.2
        self.motivation = max(0.0, self.motivation - pressure_drain)

    def update_bug_spawns(self, dt: float) -> None:
        self.spawn_timer -= dt
        spawn_rate = 2.7 - min(0.95, self.complexity * 0.008)
        if self.phase == "release":
            spawn_rate *= 0.78
        if self.spawn_timer > 0.0:
            return

        self.spawn_timer = random.uniform(max(0.25, spawn_rate * 0.7), max(0.4, spawn_rate + 0.35))
        side = random.choice(["top", "right", "bottom", "left"])
        if side == "top":
            x, y = random.uniform(self.office_bounds[0] + 20, self.office_bounds[2] - 20), self.office_bounds[1]
        elif side == "right":
            x, y = self.office_bounds[2], random.uniform(self.office_bounds[1] + 20, self.office_bounds[3] - 20)
        elif side == "bottom":
            x, y = random.uniform(self.office_bounds[0] + 20, self.office_bounds[2] - 20), self.office_bounds[3]
        else:
            x, y = self.office_bounds[0], random.uniform(self.office_bounds[1] + 20, self.office_bounds[3] - 20)

        speed = random.uniform(42.0, 64.0) + self.complexity * 0.32
        if "enemy ai" in self.broken_systems:
            speed += 18.0
        self.bug_enemies.append(BugEnemy(x=x, y=y, speed=speed))

    def update_bug_enemies(self, dt: float, player: Player) -> None:
        new_bugs: list[BugEnemy] = []
        desk = self.FEATURE_STATIONS["Core Loop"]
        for bug in self.bug_enemies:
            target_x = player.x if random.random() < 0.45 else desk["x"]
            target_y = player.y if random.random() < 0.45 else desk["y"]
            angle = math.atan2(target_y - bug.y, target_x - bug.x)
            bug.x += math.cos(angle) * bug.speed * dt
            bug.y += math.sin(angle) * bug.speed * dt

            if math.hypot(player.x - bug.x, player.y - bug.y) <= player.size + bug.radius:
                self.squash_bug(bug)
                continue

            if math.hypot(desk["x"] - bug.x, desk["y"] - bug.y) < 42:
                self.stability = max(0.0, self.stability - 3.6 * dt)
                self.progress = max(0.0, self.progress - 1.7 * dt)
                self.shake = max(self.shake, 2.5)
            else:
                new_bugs.append(bug)

        self.bug_enemies = new_bugs

    def squash_bug(self, bug: BugEnemy) -> None:
        self.motivation = min(100.0, self.motivation + 2.4)
        self.stability = min(100.0, self.stability + 0.7)
        self.feedback_flash = 0.16
        self.shake = max(self.shake, 1.3)
        for _ in range(5):
            self.particles.append(
                Particle(
                    bug.x,
                    bug.y,
                    "#ff5d73",
                    random.uniform(-90, 90),
                    random.uniform(-90, 90),
                    0.45,
                    size=random.uniform(2.0, 4.0),
                )
            )

    def update_complaints(self, dt: float) -> None:
        self.complaint_timer -= dt
        self.praise_timer -= dt
        self.complaints = [complaint for complaint in self.complaints if complaint.timer - dt > 0.0]
        for complaint in self.complaints:
            complaint.timer -= dt

        complaint_limit = 2 + self.features_unlocked
        if self.complaint_timer <= 0.0 and len(self.complaints) < complaint_limit:
            mood = "angry" if random.random() < 0.72 else "chaotic"
            self.complaints.append(Complaint(random.choice(self.COMPLAINT_POOL), random.uniform(8.0, 13.0), mood))
            self.complaint_timer = random.uniform(3.0, 5.0)

        if self.praise_timer <= 0.0 and random.random() < 0.4:
            self.complaints.append(Complaint(random.choice(self.PRAISE_POOL), 5.0, "praise"))
            self.praise_timer = random.uniform(11.0, 17.0)
            self.motivation = min(100.0, self.motivation + 4.0)

        complaint_pressure = sum(1 for complaint in self.complaints if complaint.mood != "praise")
        self.motivation = max(0.0, self.motivation - complaint_pressure * 0.07 * dt)

    def update_station_task(self, dt: float, player: Player, keys: set[str]) -> None:
        self.station_task_timer -= dt
        available_features = [name for name, _ in self.FEATURE_SEQUENCE[: self.features_unlocked]]
        if self.station_task_timer <= 0.0:
            self.active_station_task = random.choice(available_features)
            self.station_task_timer = random.uniform(6.0, 10.0)

        touched_feature = ""
        for feature_name in available_features:
            station = self.FEATURE_STATIONS[feature_name]
            if math.hypot(player.x - station["x"], player.y - station["y"]) < 42:
                touched_feature = feature_name
                break

        code_rate = (2.8 + self.features_unlocked * 0.42) * (0.58 + self.motivation / 100.0)
        if "build tools" in self.broken_systems:
            code_rate *= 0.58
        if touched_feature and touched_feature == self.active_station_task:
            code_rate += 2.4 * (0.55 + self.motivation / 100.0)
        elif touched_feature and touched_feature != "Core Loop":
            code_rate *= 0.92

        if self.phase == "development" and touched_feature:
            self.progress = min(100.0, self.progress + code_rate * dt)
            self.motivation = min(100.0, self.motivation + 1.0 * dt)
            self.station_task_timer = max(self.station_task_timer - 1.6 * dt, 0.2)

        if self.phase == "release" and touched_feature:
            self.stability = min(100.0, self.stability + 5.8 * dt)
            self.motivation = min(100.0, self.motivation + 1.8 * dt)

        if self.active_station_task != "Core Loop" and self.station_task_timer < 1.5:
            self.motivation = max(0.0, self.motivation - 0.25 * dt)

        inbox_x, inbox_y = 800.0, 292.0
        interact_pressed = bool({"e", "Return", "space"} & keys)
        if (
            math.hypot(player.x - inbox_x, player.y - inbox_y) < 48
            and self.feedback_cooldown <= 0.0
            and self.interact_cooldown <= 0.0
            and interact_pressed
        ):
            for index, complaint in enumerate(self.complaints):
                if complaint.mood == "praise":
                    continue
                self.complaints.pop(index)
                self.motivation = min(100.0, self.motivation + 4.5)
                self.stability = min(100.0, self.stability + 2.5)
                self.feedback_cooldown = 1.0
                self.interact_cooldown = 0.1
                self.message = "Responded to player feedback. Three more requests immediately appeared in spirit."
                break

    def update_repair_puzzle(self, dt: float, player: Player, keys: set[str]) -> None:
        debug_x, debug_y = 337.0, 470.0
        near_console = math.hypot(player.x - debug_x, player.y - debug_y) < 56
        interact_pressed = bool({"e", "Return", "space"} & keys)
        if self.broken_systems and self.current_repair is None and near_console and interact_pressed and self.interact_cooldown <= 0.0:
            system = self.broken_systems[0]
            node_ids = random.sample(range(6), 3)
            self.current_repair = {"system": system, "sequence": node_ids, "progress": 0}
            self.interact_cooldown = 0.0
            self.message = f"Repair started for {system}. Press the shown numbers in order."

        if not self.current_repair:
            return

        progress_index = int(self.current_repair["progress"])
        sequence = self.current_repair["sequence"]
        for index in range(6):
            key_name = str(index + 1)
            if key_name not in keys or self.interact_cooldown > 0.0:
                continue
            self.interact_cooldown = 0.05
            if index == sequence[progress_index]:
                self.current_repair["progress"] = progress_index + 1
                self.motivation = min(100.0, self.motivation + 2.2)
                self.feedback_flash = 0.22
                if self.current_repair["progress"] >= len(sequence):
                    self.complete_repair()
                else:
                    next_step = int(sequence[self.current_repair["progress"]]) + 1
                    self.message = f"Repair locked in. Next input: {next_step}."
                return

            self.current_repair["progress"] = 0
            self.motivation = max(0.0, self.motivation - 1.0)
            self.shake = max(self.shake, 0.8)
            self.message = "Wrong repair input. Sequence reset, but the console kept your notes."
            return

    def complete_repair(self) -> None:
        if not self.current_repair:
            return

        fixed_system = str(self.current_repair["system"])
        if fixed_system in self.broken_systems:
            self.broken_systems.remove(fixed_system)
        self.stability = min(100.0, self.stability + 12.0)
        self.motivation = min(100.0, self.motivation + 5.0)
        self.message = f"Patched {fixed_system}. Something else will probably break."
        self.current_repair = None

        if random.random() < 0.28 and len(self.broken_systems) < 2:
            candidates = [name for name in self.SYSTEM_EFFECTS if name != fixed_system and name not in self.broken_systems]
            if candidates:
                chained = random.choice(candidates)
                self.broken_systems.append(chained)
                self.message = f"Patched {fixed_system}. Chain reaction: {chained} broke instead."
                self.stability = max(0.0, self.stability - 5.0)

    def update_phase_logic(self, dt: float, player: Player) -> None:
        if self.phase == "development":
            self.event_timer -= dt
            if self.event_timer <= 0.0:
                self.trigger_bug_event()
                self.event_timer = random.uniform(7.5, 11.0)

            unlock_progress = [18, 34, 50, 68, 86]
            while self.last_feature_index < len(unlock_progress) and self.progress >= unlock_progress[self.last_feature_index]:
                self.unlock_feature()
                self.last_feature_index += 1

            if self.progress >= 100.0:
                self.start_release_phase()
        else:
            self.release_countdown = max(0.0, self.release_countdown - dt)
            self.event_timer -= dt
            if self.event_timer <= 0.0:
                self.trigger_bug_event(force_heavy=True)
                self.event_timer = random.uniform(3.2, 4.8)

            self.stability = max(0.0, self.stability - (0.32 + self.complexity * 0.012) * dt)
            if self.release_countdown <= 0.0:
                self.finish_release()

        if self.stability <= 0.0:
            self.force_release("The build imploded before launch. Reviewers found the ashes.")
            return

        if self.timer <= 0.0 and not self.finished:
            self.force_release("Time expired. The unfinished build was pushed live anyway.")

    def trigger_bug_event(self, force_heavy: bool = False) -> None:
        events = ["reverse_controls", "screen_flicker", "ui_hidden", "crash_risk", "system_break"]
        weights = [2, 2, 2, 2, 3] if force_heavy else [3, 3, 2, 1, 3]
        event = random.choices(events, weights=weights, k=1)[0]

        if event == "system_break":
            options = [name for name in self.SYSTEM_EFFECTS if name not in self.broken_systems]
            if options:
                broken = random.choice(options)
                self.broken_systems.append(broken)
                self.message = f"{self.SYSTEM_EFFECTS[broken]}. Route to the Debug Console."
                self.stability = max(0.0, self.stability - 4.5)
                self.screen_flash = 0.18
                return

        if event == "crash_risk":
            self.active_glitches["crash_risk"] = random.uniform(4.8, 6.4)
            self.message = "Random crash incoming. Stabilize the build or lose ground."
        elif event == "reverse_controls":
            self.active_glitches["reverse_controls"] = random.uniform(4.0, 6.0)
            self.message = "Input mapping inverted itself. Classic."
        elif event == "screen_flicker":
            self.active_glitches["screen_flicker"] = random.uniform(3.6, 5.8)
            self.message = "Rendering flicker detected. Pretend it is intentional."
        elif event == "ui_hidden":
            self.active_glitches["ui_hidden"] = random.uniform(4.0, 6.5)
            self.message = "UI vanished. Ship mode is now trust-based."

        self.motivation = max(0.0, self.motivation - 3.5)

    def trigger_crash(self) -> None:
        self.active_glitches.pop("crash_risk", None)
        checkpoint_progress = float(self.section_checkpoint["progress"])
        checkpoint_feature_index = int(self.section_checkpoint["feature_index"])
        self.progress = max(checkpoint_progress, self.progress - 8.0)
        self.features_unlocked = max(1, checkpoint_feature_index + 1)
        self.last_feature_index = checkpoint_feature_index
        self.active_station_task = self.FEATURE_SEQUENCE[checkpoint_feature_index][0]
        self.stability = max(24.0, self.stability - 10.0)
        self.motivation = max(18.0, self.motivation - 7.0)
        self.bug_enemies = self.bug_enemies[: max(1, len(self.bug_enemies) // 2)]
        self.current_repair = None
        self.shake = 4.0
        self.screen_flash = 0.42
        self.message = "The editor crashed, but autosave kept most of your work."

    def unlock_feature(self) -> None:
        if self.features_unlocked >= len(self.FEATURE_SEQUENCE):
            return

        self.features_unlocked += 1
        feature_name, _ = self.FEATURE_SEQUENCE[self.features_unlocked - 1]
        self.focus_feature = feature_name
        self.active_station_task = feature_name
        self.station_task_timer = 9.0
        self.complexity = min(100.0, self.complexity + 16.0)
        self.stability = max(0.0, self.stability - 6.0)
        self.motivation = min(100.0, self.motivation + 4.0)
        self.message = f"Feature creep unlocked {feature_name}. The scope got bigger."
        self.section_checkpoint = {"progress": self.progress, "feature_index": self.features_unlocked - 1}

    def start_release_phase(self) -> None:
        self.phase = "release"
        self.release_countdown = 22.0
        self.event_timer = 2.8
        self.complexity = min(100.0, self.complexity + 6.0)
        self.message = "Final Boss: The Release. Hold the build together through the countdown."

    def finish_release(self) -> None:
        score = self.stability * 0.54 + self.motivation * 0.34 + self.progress * 0.2 - len(self.broken_systems) * 5
        self.review_score = clamp(score, 0.0, 100.0)
        self.review_log = self.generate_reviews()
        self.finished = True
        self.success = self.review_score >= 50.0
        self.message = f"Release shipped with a review score of {int(self.review_score)}."

        if self.success:
            if self.review_score >= 88:
                self.grade = "S"
            elif self.review_score >= 76:
                self.grade = "A"
            elif self.review_score >= 64:
                self.grade = "B"
            else:
                self.grade = "C"
        self.meta["best_review"] = max(int(self.meta["best_review"]), int(self.review_score))
        self.meta["best_features"] = max(int(self.meta["best_features"]), self.features_unlocked)
        if self.success:
            self.meta["clears"] = int(self.meta["clears"]) + 1
        self.save_meta()

    def force_release(self, reason: str) -> None:
        self.finished = True
        self.success = False
        self.review_score = clamp(self.progress * 0.32 + self.stability * 0.18 + self.motivation * 0.12 - 28.0, 0.0, 100.0)
        self.review_log = [
            "Review: 'Ambitious, unstable, accidentally fascinating.'",
            "Review: 'I can see the good game trapped inside this launch build.'",
            "Review: 'Please let the solo dev sleep before the next patch.'",
        ]
        self.message = reason
        self.grade = "-"
        self.meta["best_features"] = max(int(self.meta["best_features"]), self.features_unlocked)
        self.save_meta()

    def generate_reviews(self) -> list[str]:
        reviews = []
        if self.review_score >= 85:
            reviews.append("Review: 'Chaotic, funny, and somehow polished under pressure.'")
        elif self.review_score >= 70:
            reviews.append("Review: 'Messy in spots, but deeply charming.'")
        else:
            reviews.append("Review: 'A compelling near-miss with a lot of emergency duct tape.'")

        if len(self.broken_systems) == 0:
            reviews.append("Review: 'Miraculously stable for a launch-day indie.'")
        else:
            reviews.append(f"Review: 'Still shipped with broken {self.broken_systems[0]} code, naturally.'")

        if self.features_unlocked >= 5:
            reviews.append("Review: 'Feature creep nearly killed it, but the ambition is real.'")
        else:
            reviews.append("Review: 'Could have used a little more scope and a lot less panic.'")

        if self.motivation >= 70:
            reviews.append("Review: 'The developer's stubborn optimism carries the whole project.'")
        else:
            reviews.append("Review: 'You can feel the burnout in the final act.'")
        return reviews

    def calculate_grade(self) -> str:
        if self.grade != "-":
            return self.grade
        if not self.success:
            return "-"
        if self.review_score >= 88:
            return "S"
        if self.review_score >= 76:
            return "A"
        if self.review_score >= 64:
            return "B"
        return "C"

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0
        sy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0

        self.draw_background(canvas, sx, sy)
        self.draw_stations(canvas, player, sx, sy)
        self.draw_deadline_monster(canvas, sx, sy)
        self.draw_bugs(canvas, sx, sy)
        self.draw_complaints(canvas)
        self.draw_puzzle(canvas)
        player.draw(canvas)
        self.draw_particles(canvas)
        self.draw_custom_hud(canvas)

        if self.feedback_flash > 0.0:
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#ffffff", outline="", stipple="gray50")
        if self.screen_flash > 0.0:
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#ff3b30", outline="", stipple="gray50")
        if self.finished:
            self.draw_result(canvas)

    def draw_background(self, canvas: tk.Canvas, sx: float, sy: float) -> None:
        colors = ["#111827", "#0f172a", "#10233c", "#0b1424"]
        for index, color in enumerate(colors):
            canvas.create_rectangle(0, index * HEIGHT / len(colors), WIDTH, (index + 1) * HEIGHT / len(colors), fill=color, outline="")
        canvas.create_rectangle(
            self.office_bounds[0] + sx,
            self.office_bounds[1] + sy,
            self.office_bounds[2] + sx,
            self.office_bounds[3] + sy,
            fill="#17212f",
            outline="#3a506b",
            width=3,
        )
        for x in range(120, 860, 92):
            canvas.create_line(x + sx, self.office_bounds[1] + sy, x + sx, self.office_bounds[3] + sy, fill="#213244")
        for y in range(120, 530, 74):
            canvas.create_line(self.office_bounds[0] + sx, y + sy, self.office_bounds[2] + sx, y + sy, fill="#213244")

    def draw_stations(self, canvas: tk.Canvas, player: Player, sx: float, sy: float) -> None:
        for feature_name, _ in self.FEATURE_SEQUENCE[: self.features_unlocked]:
            station = self.FEATURE_STATIONS[feature_name]
            is_active = feature_name == self.active_station_task
            is_near = math.hypot(player.x - station["x"], player.y - station["y"]) < 42
            width = 44 if feature_name == "Core Loop" else 38
            height = 34 if feature_name == "Core Loop" else 30
            outline = "#f8fafc" if is_active else "#243b53"
            canvas.create_rectangle(
                station["x"] - width + sx,
                station["y"] - height + sy,
                station["x"] + width + sx,
                station["y"] + height + sy,
                fill=station["color"],
                outline=outline,
                width=3 if is_active else 2,
            )
            if is_active:
                canvas.create_oval(
                    station["x"] - 58 + sx,
                    station["y"] - 48 + sy,
                    station["x"] + 58 + sx,
                    station["y"] + 48 + sy,
                    outline="#fef08a",
                    width=2,
                )
            if is_near:
                canvas.create_oval(
                    station["x"] - 66 + sx,
                    station["y"] - 56 + sy,
                    station["x"] + 66 + sx,
                    station["y"] + 56 + sy,
                    outline="#ffffff",
                    width=2,
                )
            canvas.create_text(station["x"] + sx, station["y"] - 6 + sy, text=station["label"], fill="#08111d", font=("Helvetica", 9, "bold"))
            canvas.create_text(station["x"] + sx, station["y"] + 11 + sy, text=feature_name, fill="#08111d", font=("Helvetica", 8))
            canvas.create_text(
                station["x"] + sx,
                station["y"] + height + 14 + sy,
                text=self.get_station_prompt(player, feature_name),
                fill="#e5e7eb" if is_active or is_near else "#94a3b8",
                font=("Helvetica", 8, "bold"),
            )

        canvas.create_rectangle(292 + sx, 438 + sy, 382 + sx, 504 + sy, fill="#334155", outline="#7dd3fc", width=2)
        canvas.create_text(337 + sx, 459 + sy, text="Debug", fill="#e2e8f0", font=("Helvetica", 10, "bold"))
        canvas.create_text(337 + sx, 476 + sy, text="Console", fill="#e2e8f0", font=("Helvetica", 9, "bold"))
        if math.hypot(player.x - 337.0, player.y - 470.0) < 56:
            repair_text = "Press E to repair" if self.broken_systems and not self.current_repair else "Enter repair input"
            canvas.create_text(337 + sx, 520 + sy, text=repair_text, fill="#bfdbfe", font=("Helvetica", 9, "bold"))
        canvas.create_rectangle(758 + sx, 252 + sy, 842 + sx, 332 + sy, fill="#1f2937", outline="#fda4af", width=2)
        canvas.create_text(800 + sx, 280 + sy, text="Feedback", fill="#fee2e2", font=("Helvetica", 10, "bold"))
        canvas.create_text(800 + sx, 298 + sy, text="Inbox", fill="#fee2e2", font=("Helvetica", 9, "bold"))
        if math.hypot(player.x - 800.0, player.y - 292.0) < 48:
            canvas.create_text(800 + sx, 348 + sy, text="Press E to clear 1 complaint", fill="#fecdd3", font=("Helvetica", 9, "bold"))

    def draw_deadline_monster(self, canvas: tk.Canvas, sx: float, sy: float) -> None:
        deadline_x = self.get_deadline_x() + sx
        canvas.create_rectangle(deadline_x, self.office_bounds[1] - 12 + sy, WIDTH + 10, self.office_bounds[3] + 12 + sy, fill="#7f1d1d", outline="")
        for offset in range(0, 380, 34):
            canvas.create_arc(deadline_x - 40, 108 + offset, deadline_x + 56, 160 + offset, start=270, extent=180, fill="#ef4444", outline="")
        canvas.create_oval(deadline_x - 18, 166 + sy, deadline_x + 26, 210 + sy, fill="#fee2e2", outline="")
        canvas.create_oval(deadline_x - 18, 338 + sy, deadline_x + 26, 382 + sy, fill="#fee2e2", outline="")
        canvas.create_text(deadline_x + 28, 272 + sy, angle=90, text="DEADLINE", fill="#fecaca", font=("Helvetica", 16, "bold"))

    def draw_bugs(self, canvas: tk.Canvas, sx: float, sy: float) -> None:
        for bug in self.bug_enemies:
            canvas.create_oval(
                bug.x - bug.radius + sx,
                bug.y - bug.radius + sy,
                bug.x + bug.radius + sx,
                bug.y + bug.radius + sy,
                fill="#ef4444",
                outline="#fee2e2",
                width=2,
            )
            canvas.create_line(bug.x - 16 + sx, bug.y + sy, bug.x + 16 + sx, bug.y + sy, fill="#fecaca", width=2)
            canvas.create_line(bug.x + sx, bug.y - 16 + sy, bug.x + sx, bug.y + 16 + sy, fill="#fecaca", width=2)

    def draw_complaints(self, canvas: tk.Canvas) -> None:
        canvas.create_text(800, 108, text="Players", fill="#f8fafc", font=("Helvetica", 12, "bold"))
        for index, complaint in enumerate(self.complaints[:5]):
            y = 132 + index * 54
            fill = "#1e293b" if complaint.mood != "praise" else "#113b2b"
            outline = "#fb7185" if complaint.mood != "praise" else "#86efac"
            text_fill = "#ffe4e6" if complaint.mood != "praise" else "#dcfce7"
            canvas.create_rectangle(690, y, 910, y + 40, fill=fill, outline=outline, width=2)
            canvas.create_text(800, y + 20, text=complaint.text, fill=text_fill, font=("Helvetica", 10), width=200)

    def draw_puzzle(self, canvas: tk.Canvas) -> None:
        if not self.current_repair:
            if self.broken_systems:
                canvas.create_text(338, 524, text=f"Repair queued: {self.broken_systems[0]}", fill="#fde68a", font=("Helvetica", 10, "bold"))
                canvas.create_text(338, 540, text="Stand here and press E to begin.", fill="#cbd5e1", font=("Helvetica", 9))
            return

        sequence = self.current_repair["sequence"]
        progress = int(self.current_repair["progress"])
        canvas.create_text(336, 518, text=f"Reconnect {self.current_repair['system']}", fill="#bfdbfe", font=("Helvetica", 10, "bold"))
        remaining = [str(node + 1) for node in sequence[progress:]]
        canvas.create_text(336, 536, text=f"Press: {' -> '.join(remaining)}", fill="#e2e8f0", font=("Helvetica", 9))
        for index in range(6):
            x = 258 + index * 30
            y = 494
            is_done = index in sequence[:progress]
            is_next = progress < len(sequence) and index == sequence[progress]
            fill = "#22c55e" if is_done else "#334155"
            outline = "#fef08a" if is_next else "#93c5fd"
            canvas.create_rectangle(x - 12, y - 12, x + 12, y + 12, fill=fill, outline=outline, width=3)
            canvas.create_text(x, y, text=str(index + 1), fill="#f8fafc", font=("Helvetica", 9, "bold"))

    def draw_custom_hud(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, 0, WIDTH, 92, fill="#050b14", outline="")
        canvas.create_text(18, 18, anchor="w", text=self.name, fill="#f8fafc", font=("Helvetica", 16, "bold"))
        phase_label = "Release" if self.phase == "release" else "Development"
        timer_text = f"Release: {self.release_countdown:04.1f}s" if self.phase == "release" else f"Time: {self.timer:04.1f}s"
        canvas.create_text(18, 46, anchor="w", text=f"{phase_label} Phase", fill="#93c5fd", font=("Helvetica", 11, "bold"))
        canvas.create_text(WIDTH - 18, 20, anchor="e", text=timer_text, fill="#f8fafc", font=("Helvetica", 14, "bold"))

        if "ui_hidden" not in self.active_glitches:
            self.draw_meter(canvas, 178, 16, 360, 36, self.progress, "#38bdf8", "Build")
            self.draw_meter(canvas, 178, 40, 360, 60, self.motivation, "#fbbf24", "Motivation")
            self.draw_meter(canvas, 380, 16, 562, 36, self.stability, "#4ade80", "Stability")
            self.draw_meter(canvas, 380, 40, 562, 60, self.complexity, "#fb7185", "Complexity")

        glitch_text = ", ".join(name.replace("_", " ") for name in self.active_glitches) or "none"
        system_text = ", ".join(self.broken_systems) or "all green"
        canvas.create_text(590, 18, anchor="w", text=f"Glitches: {glitch_text}", fill="#fda4af", font=("Helvetica", 10, "bold"))
        canvas.create_text(590, 40, anchor="w", text=f"Broken: {system_text}", fill="#fde68a", font=("Helvetica", 10, "bold"))
        canvas.create_text(590, 60, anchor="w", text=f"Task: {self.active_station_task}", fill="#c4b5fd", font=("Helvetica", 10, "bold"))
        canvas.create_text(18, 74, anchor="w", text=f"Priority: {self.get_priority_text()}", fill="#f8fafc", font=("Helvetica", 10, "bold"), width=620)
        canvas.create_text(
            WIDTH - 18,
            74,
            anchor="e",
            text="Build stations | Stomp bugs | Inbox clears complaints | Debug console repairs",
            fill="#94a3b8",
            font=("Helvetica", 9),
        )
        canvas.create_text(WIDTH / 2, HEIGHT - 18, text=self.message or self.hints[self.current_hint_index], fill="#dbeafe", font=("Helvetica", 11, "italic"))

    def draw_meter(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, value: float, fill: str, label: str) -> None:
        canvas.create_rectangle(x1, y1, x2, y2, fill="#0f172a", outline="#334155", width=1)
        width = max(0.0, x2 - x1 - 4)
        canvas.create_rectangle(x1 + 2, y1 + 2, x1 + 2 + width * clamp(value / 100.0, 0.0, 1.0), y2 - 2, fill=fill, outline="")
        canvas.create_text(x1 + 8, (y1 + y2) / 2, anchor="w", text=f"{label} {int(value)}", fill="#f8fafc", font=("Helvetica", 9, "bold"))

    def draw_result(self, canvas: tk.Canvas) -> None:
        overlay = "#03111f"
        panel = "#0f172a"
        accent = "#4ade80" if self.success else "#fb7185"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=overlay, outline="", stipple="gray50")
        canvas.create_rectangle(118, 70, WIDTH - 118, HEIGHT - 66, fill=panel, outline=accent, width=3)
        title = "RELEASE COMPLETE" if self.success else "POSTMORTEM"
        canvas.create_text(WIDTH / 2, 110, text=title, fill=accent, font=("Helvetica", 24, "bold"))
        canvas.create_text(WIDTH / 2, 146, text=self.message, fill="#e2e8f0", font=("Helvetica", 12, "bold"), width=560)

        canvas.create_rectangle(WIDTH / 2 - 72, 178, WIDTH / 2 + 72, 256, fill="#111827", outline=accent, width=2)
        canvas.create_text(WIDTH / 2, 200, text="REVIEW", fill="#cbd5e1", font=("Helvetica", 11, "bold"))
        canvas.create_text(WIDTH / 2, 232, text=f"{int(self.review_score)}", fill=accent, font=("Helvetica", 28, "bold"))

        canvas.create_text(180, 292, anchor="w", text="Launch Notes", fill="#93c5fd", font=("Helvetica", 14, "bold"))
        notes = [
            f"Features shipped: {self.features_unlocked}/{len(self.FEATURE_SEQUENCE)}",
            f"Best saved review: {int(self.meta['best_review'])}",
            f"Saved clears: {int(self.meta['clears'])}",
            f"Persistent milestone: feature tier {int(self.meta['best_features'])}",
        ]
        y = 320
        for note in notes:
            canvas.create_text(180, y, anchor="w", text=note, fill="#e2e8f0", font=("Helvetica", 11))
            y += 28

        canvas.create_text(180, 446, anchor="w", text="Reviews", fill="#93c5fd", font=("Helvetica", 14, "bold"))
        y = 474
        for review in self.review_log[:4]:
            canvas.create_text(180, y, anchor="w", text=review, fill="#f8fafc", font=("Helvetica", 11), width=590)
            y += 34

        canvas.create_rectangle(WIDTH / 2 - 188, HEIGHT - 116, WIDTH / 2 + 188, HEIGHT - 66, fill="#f8fafc", outline="")
        canvas.create_text(WIDTH / 2, HEIGHT - 91, text="Press SPACE To Return To The Hub", fill="#0f172a", font=("Helvetica", 13, "bold"))

    def draw_briefing(self, canvas: tk.Canvas) -> None:
        super().draw_briefing(canvas)
        canvas.create_text(
            WIDTH / 2,
            HEIGHT - 112,
            text=f"Saved milestone: best review {int(self.meta['best_review'])}, best feature tier {int(self.meta['best_features'])}, clears {int(self.meta['clears'])}",
            fill="#8dd3ff",
            font=("Helvetica", 10, "bold"),
        )

    def get_deadline_x(self) -> float:
        left = self.office_bounds[0] + 70
        right = self.office_bounds[2] + 48
        return right - (right - left) * (1.0 - self.deadline_distance)

    def get_puzzle_nodes(self) -> list[tuple[float, float]]:
        return [
            (280.0, 372.0),
            (334.0, 352.0),
            (388.0, 372.0),
            (280.0, 420.0),
            (334.0, 442.0),
            (388.0, 420.0),
        ]
