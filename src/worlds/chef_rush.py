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
            summary="Prepare a specific recipe by gathering and cooking ingredients",
            duration=60.0,
        )
        self.briefing = [
            "KITCHEN RUSH: The VIP table just ordered!",
            "Follow the recipe: Gather ingredients from the PANTRY,",
            "cook them at the STOVE, and deliver to the SERVICE window.",
            "Complete as many dishes as possible before time runs out!"
        ]
        self.hints = [
            "Tip: Check the 'Needs' list in the top corner.",
            "Tip: You can only carry one ingredient at a time.",
            "Tip: Cooking takes a few moments at the stove.",
            "Tip: Stay organized for a higher grade!"
        ]
        self.ingredients = ["Tomato", "Cheese", "Bread", "Meat", "Onion"]
        self.current_recipe = []
        self.held_item = ""
        self.is_cooked = False
        self.cooked_count = 0
        self.dishes_completed = 0
        self.cooking_progress = 0.0
        
        # Positions
        self.pantry_pos = (150, 150)
        self.stove_pos = (WIDTH/2, HEIGHT/2)
        self.service_pos = (WIDTH-150, HEIGHT-150)

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT - 100)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.dishes_completed = 0
        self.new_recipe()
        self.shake = 0.0
        self.particles = []

    def new_recipe(self) -> None:
        self.current_recipe = random.sample(self.ingredients, 3)
        self.cooked_count = 0
        self.held_item = ""
        self.is_cooked = False
        self.cooking_progress = 0.0

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)

        # 1. Interaction with Pantry
        if math.hypot(player.x - self.pantry_pos[0], player.y - self.pantry_pos[1]) < 60:
            if not self.held_item and self.cooked_count < 3:
                self.held_item = self.current_recipe[self.cooked_count]
                self.is_cooked = False
        
        # 2. Interaction with Stove
        if math.hypot(player.x - self.stove_pos[0], player.y - self.stove_pos[1]) < 60:
            if self.held_item and not self.is_cooked:
                self.cooking_progress += dt * 40.0
                if self.cooking_progress >= 100.0:
                    self.is_cooked = True
                    self.cooking_progress = 0.0
        else:
             self.cooking_progress = max(0.0, self.cooking_progress - dt * 20.0)

        # 3. Interaction with Service
        if math.hypot(player.x - self.service_pos[0], player.y - self.service_pos[1]) < 60:
            if self.held_item and self.is_cooked:
                self.held_item = ""
                self.is_cooked = False
                self.cooked_count += 1
                if self.cooked_count >= 3:
                    self.dishes_completed += 1
                    self.new_recipe()
                    self.timer += 5.0 # Bonus time

        if self.timer <= 0:
            self.finished = True
            self.success = self.dishes_completed >= 2
            self.message = f"Shift Over! Dishes served: {self.dishes_completed}"
            if self.dishes_completed >= 5: self.grade = "S"
            elif self.dishes_completed >= 3: self.grade = "A"
            elif self.dishes_completed >= 2: self.grade = "B"
            else: self.grade = "C"

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#f3f3f3" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)

        # Zones
        # Pantry
        canvas.create_rectangle(self.pantry_pos[0]-60, self.pantry_pos[1]-60, self.pantry_pos[0]+60, self.pantry_pos[1]+60, fill="#d9b08c", outline="#a67c52", width=3)
        canvas.create_text(self.pantry_pos[0], self.pantry_pos[1], text="PANTRY", fill="#4b3621", font=("Arial", 12, "bold"))
        
        # Stove
        canvas.create_rectangle(self.stove_pos[0]-60, self.stove_pos[1]-60, self.stove_pos[0]+60, self.stove_pos[1]+60, fill="#2f3640", outline="#eb3b5a", width=3)
        canvas.create_text(self.stove_pos[0], self.stove_pos[1], text="STOVE", fill="#fff", font=("Arial", 12, "bold"))
        if self.cooking_progress > 0:
             canvas.create_rectangle(self.stove_pos[0]-50, self.stove_pos[1]+40, self.stove_pos[0]+50, self.stove_pos[1]+50, fill="#111")
             canvas.create_rectangle(self.stove_pos[0]-48, self.stove_pos[1]+42, self.stove_pos[0]-48+96*(self.cooking_progress/100.0), self.stove_pos[1]+48, fill="#eb3b5a")

        # Service
        canvas.create_rectangle(self.service_pos[0]-60, self.service_pos[1]-60, self.service_pos[0]+60, self.service_pos[1]+60, fill="#dcdde1", outline="#3dc1d3", width=3)
        canvas.create_text(self.service_pos[0], self.service_pos[1], text="SERVICE", fill="#2f3640", font=("Arial", 12, "bold"))

        # Recipe HUD
        canvas.create_rectangle(10, 60, 250, 150, fill="#fff", outline="#ddd", width=2)
        canvas.create_text(20, 75, anchor="w", text="CURRENT RECIPE:", fill="#333", font=("Arial", 10, "bold"))
        for i, ing in enumerate(self.current_recipe):
            color = "#a5b1c2" if i < self.cooked_count else "#333"
            canvas.create_text(30, 95 + i*15, anchor="w", text=f"- {ing}", fill=color, font=("Arial", 9))

        # Carry HUD
        if self.held_item:
             state = "COOKED" if self.is_cooked else "RAW"
             color = "#4cd137" if self.is_cooked else "#e84118"
             canvas.create_text(player.x, player.y-40, text=f"{state} {self.held_item.upper()}", fill=color, font=("Arial", 10, "bold"))

        player.draw(canvas)
        
        # HUD
        canvas.create_text(WIDTH-20, 75, anchor="e", text=f"Dishes: {self.dishes_completed}", fill="#2ecc71", font=("Arial", 16, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

