import random
import math
import time
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any, cast

class ChefRushWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Executive Chef",
            summary="Prepare recipes using interactive mouse techniques",
            duration=50.0,
        )
        self.briefing = [
            "KITCHEN TYCOON: The VIP table wants quality food!",
            "1. Grab ingredients from the PANTRY.",
            "2. Take to PREP and MOVE MOUSE to chop.",
            "3. Take to STOVE and CIRCLE MOUSE to stir.",
            "4. Deliver at SERVICE to earn CASH!"
        ]
        self.hints = [
            "Tip: You must physically MOVE the mouse over stations to work.",
            "Tip: Settle in at a station and move your mouse to cook.",
            "Tip: Earn money by delivering finished meals.",
            "Tip: Check your HUD for the current order."
        ]
        self.ingredients = ["Tomato", "Cheese", "Bread", "Meat", "Onion"]
        self.recipe_item = ""
        self.held_item = ""
        self.state = "RAW" # RAW -> CHOPPED -> COOKED
        self.money = 0
        self.progress = 0.0
        self.last_mouse = (0, 0)
        
        # Positions
        self.pantry_pos = (150, 150)
        self.prep_pos = (WIDTH/2 - 100, HEIGHT/2)
        self.stove_pos = (WIDTH/2 + 100, HEIGHT/2)
        self.service_pos = (WIDTH-150, HEIGHT-150)

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 100)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.money = 0
        self.progress = 0.0
        self.new_recipe()
        self.shake = 0.0
        self.particles = []

    def new_recipe(self) -> None:
        self.recipe_item = random.choice(self.ingredients)
        self.held_item = ""
        self.state = "RAW"
        self.progress = 0.0

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        
        # tick_timer handled by engine
        if self.tutorial_timer > 0:
             self.draw(canvas, player)
             return
             
        player.update(dt, keys, self.bounds)

        mx, my = mouse_pos
        dx, dy = mx - self.last_mouse[0], my - self.last_mouse[1]
        mouse_move_dist = math.hypot(dx, dy)
        self.last_mouse = mouse_pos

        # 1. Pantry
        if math.hypot(player.x - self.pantry_pos[0], player.y - self.pantry_pos[1]) < 60:
             if not self.held_item:
                  self.held_item = self.recipe_item
                  self.state = "RAW"
                  self.progress = 0.0

        # 2. Prep Board (Chopping - Slash movement)
        if math.hypot(player.x - self.prep_pos[0], player.y - self.prep_pos[1]) < 60:
             if self.held_item and self.state == "RAW":
                  # Requires active mouse movement
                  self.progress += mouse_move_dist * 0.15
                  if self.progress >= 100.0:
                       self.state = "CHOPPED"
                       self.progress = 0.0
        
        # 3. Stove (Stirring - requires mouse movement)
        if math.hypot(player.x - self.stove_pos[0], player.y - self.stove_pos[1]) < 60:
             if self.held_item and self.state == "CHOPPED":
                  self.progress += mouse_move_dist * 0.12
                  if self.progress >= 100.0:
                       self.state = "COOKED"
                       self.progress = 0.0
                       
        # 4. Service
        if math.hypot(player.x - self.service_pos[0], player.y - self.service_pos[1]) < 60:
             if self.held_item and self.state == "COOKED":
                  self.money += 50
                  self.orders_completed += 1
                  self.new_recipe()
                  self.timer += 3.0

        if self.timer <= 0:
            self.finished = True
            self.success = self.money > 0
            if self.success:
                self.message = f"Shift over! Kitchen served {self.orders_completed} orders. Profit: ${self.money}"
                self.grade = self.calculate_grade()
            else:
                self.message = "Deadline missed! The restaurant failed to break even."
                self.grade = "F"

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#f3f3f3" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)

        # Zones
        canvas.create_rectangle(self.pantry_pos[0]-50, self.pantry_pos[1]-50, self.pantry_pos[0]+50, self.pantry_pos[1]+50, fill="#d9b08c", outline="#4b3621", width=2)
        canvas.create_text(self.pantry_pos[0], self.pantry_pos[1], text="PANTRY\n(Touch)", fill="#4b3621", justify="center", font=("Arial", 9, "bold"))

        canvas.create_rectangle(self.prep_pos[0]-50, self.prep_pos[1]-50, self.prep_pos[0]+50, self.prep_pos[1]+50, fill="#fff", outline="#ddd", width=2)
        canvas.create_text(self.prep_pos[0], self.prep_pos[1], text="PREP BOARD\n(Move Mouse)", fill="#333", justify="center", font=("Arial", 9, "bold"))
        if self.state == "RAW" and math.hypot(player.x - self.prep_pos[0], player.y - self.prep_pos[1]) < 60:
             canvas.create_rectangle(self.prep_pos[0]-40, self.prep_pos[1]+30, self.prep_pos[0]+40, self.prep_pos[1]+40, fill="#333")
             canvas.create_rectangle(self.prep_pos[0]-38, self.prep_pos[1]+32, self.prep_pos[0]-38+76*(self.progress/100.0), self.prep_pos[1]+38, fill="#ffa502")

        canvas.create_rectangle(self.stove_pos[0]-50, self.stove_pos[1]-50, self.stove_pos[0]+50, self.stove_pos[1]+50, fill="#2f3640", outline="#eb3b5a", width=3)
        canvas.create_text(self.stove_pos[0], self.stove_pos[1], text="STOVE\n(Circle Mouse)", fill="#fff", justify="center", font=("Arial", 9, "bold"))
        if self.state == "CHOPPED" and math.hypot(player.x - self.stove_pos[0], player.y - self.stove_pos[1]) < 60:
             canvas.create_rectangle(self.stove_pos[0]-40, self.stove_pos[1]+30, self.stove_pos[0]+40, self.stove_pos[1]+40, fill="#111")
             canvas.create_rectangle(self.stove_pos[0]-38, self.stove_pos[1]+32, self.stove_pos[0]-38+76*(self.progress/100.0), self.stove_pos[1]+38, fill="#eb3b5a")

        canvas.create_rectangle(self.service_pos[0]-50, self.service_pos[1]-50, self.service_pos[0]+50, self.service_pos[1]+50, fill="#dcdde1", outline="#3dc1d3", width=2)
        canvas.create_text(self.service_pos[0], self.service_pos[1], text="SERVICE\n(Deliver)", fill="#2f3640", justify="center", font=("Arial", 9, "bold"))

        # Order HUD
        canvas.create_rectangle(10, 60, 200, 110, fill="#fff", outline="#ddd", width=2)
        canvas.create_text(20, 85, anchor="w", text=f"ORDER: {self.recipe_item}", fill="#1e272e", font=("Arial", 11, "bold"))

        # Held item
        if self.held_item:
             canvas.create_text(player.x, player.y-40, text=f"{self.state} {self.held_item.upper()}", fill="#eb3b5a", font=("Arial", 10, "bold"))

        player.draw(canvas)
        canvas.create_text(WIDTH-20, 75, anchor="e", text=f"CASH: ${self.money}", fill="#2ecc71", font=("Arial", 16, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

