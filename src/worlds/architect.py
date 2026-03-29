import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import HEIGHT, TEXT, WIDTH, clamp
from src.worlds.base import BaseWorld


class ArchitectWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Lead Architect",
            summary="Lay out a civic library that meets budget, program, adjacencies, and circulation goals.",
            duration=75.0,
        )
        self.auto_finish_on_timer = False
        self.briefing = [
            "CITY BRIEF: Deliver a realistic concept plan for a new public eco-library.",
            "As lead architect, place the required spaces, keep within budget, and build a coherent plan.",
            "Good plans connect the lobby to the core, keep archives protected, and place the roof garden at the top.",
            "Press ENTER to run the design review once your layout is ready.",
        ]
        self.hints = [
            "Tip: Move over a grid cell and press SPACE to place the selected space.",
            "Tip: Use keys 1-5 to switch between the program spaces.",
            "Tip: Backspace removes the space under the cursor and refunds its cost.",
            "Tip: Press ENTER only after the brief, budget, and score panel look healthy.",
        ]
        self.grid_size = 36
        self.grid_w = 10
        self.grid_h = 9
        self.offset_x = 250
        self.offset_y = 118
        self.bounds = (
            self.offset_x,
            self.offset_y,
            self.offset_x + self.grid_w * self.grid_size,
            self.offset_y + self.grid_h * self.grid_size,
        )
        self.room_types = [
            {"key": "1", "name": "Lobby", "color": "#dfe6e9", "cost": 90, "short": "LB"},
            {"key": "2", "name": "Reading Room", "color": "#74b9ff", "cost": 120, "short": "RD"},
            {"key": "3", "name": "Archive", "color": "#a29bfe", "cost": 150, "short": "AR"},
            {"key": "4", "name": "Core", "color": "#636e72", "cost": 170, "short": "CR"},
            {"key": "5", "name": "Roof Garden", "color": "#55efc4", "cost": 110, "short": "RG"},
        ]
        self.requirements = {
            "Lobby": 1,
            "Reading Room": 3,
            "Archive": 1,
            "Core": 1,
            "Roof Garden": 1,
        }
        self.blocks: list[dict[str, Any]] = []
        self.selected_room = 0
        self.budget_limit = 1200
        self.budget = self.budget_limit
        self.phase = "build"
        self.review_timer = 0.0
        self.review_score = 0.0
        self.review_notes: list[str] = []
        self.message = ""
        self.last_space_down = False
        self.last_delete_down = False
        self.last_enter_down = False

    def reset(self, player: Player) -> None:
        player.reset(self.offset_x + self.grid_size / 2, self.offset_y + self.grid_size / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.phase = "build"
        self.blocks = []
        self.selected_room = 0
        self.budget = self.budget_limit
        self.review_timer = 0.0
        self.review_score = 0.0
        self.review_notes = []
        self.last_space_down = False
        self.last_delete_down = False
        self.last_enter_down = False
        self.tutorial_timer = 4.0
        self.hint_display_timer = 0.0
        self.current_hint_index = 0

    def occupied_block(self, gx: int, gy: int) -> dict[str, Any] | None:
        for block in self.blocks:
            if block["gx"] == gx and block["gy"] == gy:
                return block
        return None

    def grid_position(self, player: Player) -> tuple[int, int]:
        gx = int((player.x - self.offset_x) // self.grid_size)
        gy = int((player.y - self.offset_y) // self.grid_size)
        return gx, gy

    def place_selected_room(self, gx: int, gy: int) -> None:
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h):
            return
        if self.occupied_block(gx, gy):
            self.message = "That space is already assigned."
            return
        room = self.room_types[self.selected_room]
        if self.budget < room["cost"]:
            self.message = "Budget too low for that space."
            return
        self.blocks.append(
            {
                "gx": gx,
                "gy": gy,
                "type": room["name"],
                "color": room["color"],
                "cost": room["cost"],
                "short": room["short"],
            }
        )
        self.budget -= int(room["cost"])
        self.message = f"Placed {room['name']}."

    def remove_room(self, gx: int, gy: int) -> None:
        block = self.occupied_block(gx, gy)
        if not block:
            self.message = "No assigned space under the cursor."
            return
        self.blocks.remove(block)
        self.budget += int(block["cost"])
        self.message = f"Removed {block['type']}."

    def counts_by_type(self) -> dict[str, int]:
        counts = {room["name"]: 0 for room in self.room_types}
        for block in self.blocks:
            counts[block["type"]] = counts.get(block["type"], 0) + 1
        return counts

    def adjacent_to_type(self, block: dict[str, Any], target_type: str) -> bool:
        for other in self.blocks:
            if other["type"] != target_type:
                continue
            if abs(other["gx"] - block["gx"]) + abs(other["gy"] - block["gy"]) == 1:
                return True
        return False

    def evaluate_design(self) -> tuple[float, list[str]]:
        score = 0.0
        notes: list[str] = []
        counts = self.counts_by_type()

        missing_program = False
        for room_name, minimum in self.requirements.items():
            placed = counts.get(room_name, 0)
            if placed >= minimum:
                score += 14.0
            else:
                missing_program = True
                notes.append(f"Add more {room_name}: {placed}/{minimum}.")

        if self.budget >= 0:
            score += 10.0
        else:
            notes.append("Budget exceeded.")

        lobby_blocks = [block for block in self.blocks if block["type"] == "Lobby"]
        core_blocks = [block for block in self.blocks if block["type"] == "Core"]
        reading_blocks = [block for block in self.blocks if block["type"] == "Reading Room"]
        archive_blocks = [block for block in self.blocks if block["type"] == "Archive"]
        roof_blocks = [block for block in self.blocks if block["type"] == "Roof Garden"]

        if lobby_blocks and core_blocks and any(self.adjacent_to_type(block, "Core") for block in lobby_blocks):
            score += 10.0
        else:
            notes.append("Place the lobby next to the core for clear entry circulation.")

        if reading_blocks and any(self.adjacent_to_type(block, "Lobby") or self.adjacent_to_type(block, "Core") for block in reading_blocks):
            score += 12.0
        else:
            notes.append("Reading rooms should connect to the lobby or core.")

        if archive_blocks and all(not self.adjacent_to_type(block, "Lobby") for block in archive_blocks):
            score += 12.0
        else:
            notes.append("Keep archives away from the noisy public lobby.")

        if core_blocks:
            core_x = sum(block["gx"] for block in core_blocks) / len(core_blocks)
            if 3.0 <= core_x <= 6.0:
                score += 12.0
            else:
                notes.append("A central core would serve the building more efficiently.")
        else:
            notes.append("The plan needs a circulation core.")

        if roof_blocks:
            top_row = min(block["gy"] for block in self.blocks) if self.blocks else 0
            if all(block["gy"] <= top_row + 1 for block in roof_blocks):
                score += 10.0
            else:
                notes.append("Place the roof garden at the top of the building mass.")

        footprint = {(block["gx"], block["gy"]) for block in self.blocks}
        unsupported = 0
        for block in self.blocks:
            below = (block["gx"], block["gy"] + 1)
            if block["gy"] < self.grid_h - 1 and below not in footprint:
                unsupported += 1
        if unsupported == 0:
            score += 10.0
        else:
            notes.append("Some spaces are floating without support below.")

        if len(self.blocks) >= 7:
            score += 10.0
        else:
            notes.append("The scheme is too small to satisfy the civic brief.")

        if missing_program:
            score = min(score, 64.0)

        return clamp(score, 0.0, 100.0), notes[:4]

    def calculate_grade(self) -> str:
        if not self.success:
            return "-"
        if self.review_score >= 92:
            return "S"
        if self.review_score >= 82:
            return "A"
        if self.review_score >= 70:
            return "B"
        return "C"

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        player.update(dt, keys, self.bounds)

        if self.phase == "build":
            self.tick_timer(dt)
            if self.finished:
                self.success = False
                self.message = "Deadline missed before the design review."
                self.draw(canvas, player)
                return

            for index, room in enumerate(self.room_types):
                if room["key"] in keys:
                    self.selected_room = index

            gx, gy = self.grid_position(player)
            space_down = "space" in keys
            delete_down = "BackSpace" in keys or "Delete" in keys
            enter_down = "Return" in keys

            if space_down and not self.last_space_down:
                self.place_selected_room(gx, gy)
            if delete_down and not self.last_delete_down:
                self.remove_room(gx, gy)
            if enter_down and not self.last_enter_down:
                self.phase = "review"
                self.review_timer = 2.8
                self.review_score = 0.0
                self.review_notes = []
                self.message = "Running design review..."

            self.last_space_down = space_down
            self.last_delete_down = delete_down
            self.last_enter_down = enter_down

        elif self.phase == "review":
            self.review_timer = max(0.0, self.review_timer - dt)
            if self.review_timer == 0.0:
                self.review_score, self.review_notes = self.evaluate_design()
                self.finished = True
                self.success = self.review_score >= 70.0
                self.grade = self.calculate_grade()
                if self.success:
                    self.message = f"Design approved. Review score: {int(self.review_score)}."
                else:
                    self.message = f"Design rejected. Review score: {int(self.review_score)}."

        self.draw(canvas, player)

    def draw_workspace(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#f4efe6", outline="")
        canvas.create_rectangle(0, 0, WIDTH, 90, fill="#1f2937", outline="")
        canvas.create_rectangle(20, 110, 220, 560, fill="#fffaf0", outline="#8d6e63", width=2)
        canvas.create_rectangle(235, 110, 625, 500, fill="#fcfcfc", outline="#8d6e63", width=2)
        canvas.create_rectangle(645, 110, 940, 560, fill="#fffaf0", outline="#8d6e63", width=2)
        canvas.create_rectangle(235, 515, 625, 585, fill="#fffaf0", outline="#8d6e63", width=2)

    def draw_grid(self, canvas: tk.Canvas, player: Player) -> None:
        for i in range(self.grid_w + 1):
            x = self.offset_x + i * self.grid_size
            canvas.create_line(x, self.offset_y, x, self.offset_y + self.grid_h * self.grid_size, fill="#d7ccc8")
        for i in range(self.grid_h + 1):
            y = self.offset_y + i * self.grid_size
            canvas.create_line(self.offset_x, y, self.offset_x + self.grid_w * self.grid_size, y, fill="#d7ccc8")

        for block in self.blocks:
            x = self.offset_x + block["gx"] * self.grid_size
            y = self.offset_y + block["gy"] * self.grid_size
            canvas.create_rectangle(x + 2, y + 2, x + self.grid_size - 2, y + self.grid_size - 2, fill=block["color"], outline="#2d3436", width=2)
            canvas.create_text(x + self.grid_size / 2, y + self.grid_size / 2, text=block["short"], fill="#111111", font=("Helvetica", 9, "bold"))

        player.draw(canvas)
        gx, gy = self.grid_position(player)
        if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h and self.phase == "build":
            x = self.offset_x + gx * self.grid_size
            y = self.offset_y + gy * self.grid_size
            canvas.create_rectangle(x, y, x + self.grid_size, y + self.grid_size, outline="#ffb300", width=3)

    def draw_program_panel(self, canvas: tk.Canvas) -> None:
        canvas.create_text(120, 132, text="PROGRAM", fill="#5d4037", font=("Helvetica", 15, "bold"))
        y = 165
        counts = self.counts_by_type()
        for index, room in enumerate(self.room_types):
            selected = index == self.selected_room
            outline = "#ffb300" if selected else "#bcaaa4"
            canvas.create_rectangle(35, y - 18, 205, y + 18, fill=room["color"], outline=outline, width=3 if selected else 1)
            required = self.requirements.get(room["name"], 0)
            placed = counts.get(room["name"], 0)
            canvas.create_text(48, y, anchor="w", text=f"[{room['key']}] {room['name']}", fill="#111111", font=("Helvetica", 10, "bold"))
            canvas.create_text(193, y, anchor="e", text=f"{placed}/{required}", fill="#111111", font=("Helvetica", 10, "bold"))
            y += 48

        canvas.create_text(120, 430, text="CONTROLS", fill="#5d4037", font=("Helvetica", 15, "bold"))
        controls = [
            "SPACE: place selected space",
            "BACKSPACE: remove selected space",
            "1-5: choose space type",
            "ENTER: run design review",
        ]
        y = 462
        for line in controls:
            canvas.create_text(40, y, anchor="w", text=line, fill="#3e2723", font=("Helvetica", 9))
            y += 24

    def draw_brief_panel(self, canvas: tk.Canvas) -> None:
        canvas.create_text(792, 132, text="DESIGN REVIEW", fill="#5d4037", font=("Helvetica", 15, "bold"))
        lines = [
            "Client: Public eco-library",
            "Must include: lobby, core, archive, 3 reading rooms, roof garden",
            "Adjacency: lobby by core, reading near access, archive away from lobby",
            "Quality: central circulation, supported floors, roof garden at top",
        ]
        y = 165
        for line in lines:
            canvas.create_text(662, y, anchor="w", text=line, fill="#3e2723", font=("Helvetica", 9), width=255)
            y += 42

        if self.phase == "review":
            canvas.create_text(792, 350, text="Review in progress...", fill="#c0392b", font=("Helvetica", 14, "bold"))
        elif self.finished:
            canvas.create_text(792, 350, text=f"Score: {int(self.review_score)}", fill="#2e7d32" if self.success else "#c0392b", font=("Helvetica", 18, "bold"))
            y = 390
            if self.review_notes:
                for note in self.review_notes:
                    canvas.create_text(662, y, anchor="w", text=f"- {note}", fill="#4e342e", font=("Helvetica", 9), width=255)
                    y += 42
            else:
                canvas.create_text(792, 400, text="All major review checks passed.", fill="#2e7d32", font=("Helvetica", 10, "bold"), width=255)
        else:
            canvas.create_text(792, 350, text="Press ENTER when the plan is ready.", fill="#0d47a1", font=("Helvetica", 11, "bold"), width=255)

    def draw_status_bar(self, canvas: tk.Canvas) -> None:
        spent = self.budget_limit - self.budget
        canvas.create_text(28, 24, anchor="w", text="Lead Architect Studio", fill="#fef3c7", font=("Helvetica", 20, "bold"))
        canvas.create_text(28, 56, anchor="w", text=f"Budget Remaining: ${self.budget}", fill="#ffffff", font=("Helvetica", 12, "bold"))
        canvas.create_text(280, 56, anchor="w", text=f"Spent: ${spent}", fill="#d1fae5", font=("Helvetica", 12, "bold"))
        canvas.create_text(420, 56, anchor="w", text=f"Spaces Placed: {len(self.blocks)}", fill="#e0f2fe", font=("Helvetica", 12, "bold"))
        phase_label = "Design Review" if self.phase == "review" else "Concept Plan"
        canvas.create_text(610, 56, anchor="w", text=f"Stage: {phase_label}", fill="#fce7f3", font=("Helvetica", 12, "bold"))

    def draw_message_bar(self, canvas: tk.Canvas) -> None:
        canvas.create_text(430, 537, text="STATUS", fill="#5d4037", font=("Helvetica", 13, "bold"))
        status_text = self.message or "Build out the program and submit for review."
        canvas.create_text(430, 563, text=status_text, fill="#3e2723", font=("Helvetica", 10, "bold"), width=360)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        self.draw_workspace(canvas)
        self.draw_status_bar(canvas)
        self.draw_program_panel(canvas)
        self.draw_grid(canvas, player)
        self.draw_brief_panel(canvas)
        self.draw_message_bar(canvas)

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)
