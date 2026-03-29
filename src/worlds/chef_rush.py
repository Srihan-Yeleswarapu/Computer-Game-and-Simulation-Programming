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
            summary="Take orders, follow the recipe book, and deliver food to impatient customers!",
            duration=75.0,
        )
        self.briefing = [
            "KITCHEN RUSH: Manage 3 simultaneous customers!",
            "1. Walk up to the COUNTER to see a customer's order.",
            "2. Stand by the RECIPE BOOK to memorize the steps.",
            "3. Visit the required stations (PANTRY, PREP, STOVE) in order.",
            "4. Deliver back to the COUNTER before their patience runs out!",
            "Faster delivery = Higher tip = Better Grade!"
        ]
        self.hints = [
            "Tip: Settle in at a station to complete the current step.",
            "Tip: You can only cook for the currently active customer.",
            "Tip: Keep an eye on the Patience Bars!"
        ]
        
        self.recipes = {
            "BURGER": ["PANTRY", "PREP", "STOVE"],
            "SALAD": ["PANTRY", "PREP"],
            "SOUP": ["PANTRY", "STOVE"]
        }
        
        self.customers = []
        self.money = 0
        self.customers_served = 0
        self.customers_failed = 0
        
        # Player state
        self.active_order = None # The customer index they are focusing on
        self.current_steps = []
        self.step_progress = 0.0
        
        # Positions
        self.counter_pos = (WIDTH/2, 100)
        self.book_pos = (100, HEIGHT/2)
        self.pantry_pos = (WIDTH-100, HEIGHT/2 - 100)
        self.prep_pos = (WIDTH-100, HEIGHT/2 + 100)
        self.stove_pos = (WIDTH/2, HEIGHT - 100)

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.money = 0
        self.customers_served = 0
        self.customers_failed = 0
        self.shake = 0.0
        self.particles = []
        
        self.active_order = None
        self.current_steps = []
        self.step_progress = 0.0

        # Spawn 3 customers
        self.customers = [
             {"id": 0, "order": random.choice(list(self.recipes.keys())), "patience": 50.0, "max_patience": 50.0, "x": WIDTH/2 - 150, "y": 40},
             {"id": 1, "order": random.choice(list(self.recipes.keys())), "patience": 55.0, "max_patience": 55.0, "x": WIDTH/2, "y": 40},
             {"id": 2, "order": random.choice(list(self.recipes.keys())), "patience": 60.0, "max_patience": 60.0, "x": WIDTH/2 + 150, "y": 40}
        ]

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        
        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)

        # Update customers
        for c in self.customers:
            c["patience"] -= dt
            if c["patience"] <= 0:
                 self.customers_failed += 1
                 self.shake = 3.0
                 c["order"] = random.choice(list(self.recipes.keys()))
                 c["patience"] = c["max_patience"]
                 if self.active_order == c["id"]:
                      self.active_order = None
                      self.current_steps = []

        # Stations logic
        # 1. Counter (Select order & Deliver)
        for c in self.customers:
             if math.hypot(player.x - c["x"], player.y - c["y"]) < 60:
                  if self.active_order is None and len(self.current_steps) == 0:
                       self.active_order = c["id"]
                  elif self.active_order == c["id"] and len(self.current_steps) == 0 and self.step_progress == -1:
                       # Delivered!
                       tip = int((c["patience"] / c["max_patience"]) * 50)
                       self.money += 100 + tip
                       self.customers_served += 1
                       c["order"] = random.choice(list(self.recipes.keys()))
                       c["patience"] = c["max_patience"]
                       self.active_order = None
                       self.step_progress = 0.0

        if self.active_order is not None and self.step_progress != -1:
             c = next((cust for cust in self.customers if cust["id"] == self.active_order), None)
             if c:
                  # 2. Recipe Book
                  if len(self.current_steps) == 0:
                       if math.hypot(player.x - self.book_pos[0], player.y - self.book_pos[1]) < 60:
                            self.current_steps = self.recipes[c["order"]].copy()
                            self.step_progress = 0.0
                  # 3. Work Stations
                  elif len(self.current_steps) > 0:
                       next_station = self.current_steps[0]
                       station_pos = {"PANTRY": self.pantry_pos, "PREP": self.prep_pos, "STOVE": self.stove_pos}[next_station]
                       
                       if math.hypot(player.x - station_pos[0], player.y - station_pos[1]) < 50:
                            self.step_progress += 40.0 * dt
                            if self.step_progress >= 100.0:
                                 self.current_steps.pop(0)
                                 self.step_progress = 0.0
                                 if len(self.current_steps) == 0:
                                      self.step_progress = -1 # Ready for delivery

        if self.timer <= 0:
            self.finished = True
            self.success = self.customers_served >= 3
            if self.success:
                self.message = f"Shift over! Served {self.customers_served} meals. Earned ${self.money}!"
                if self.customers_served >= 7: self.grade = "S"
                elif self.customers_served >= 5: self.grade = "A"
                elif self.customers_served >= 3: self.grade = "B"
            else:
                self.message = f"Restaurant failed! Only served {self.customers_served} meals."
                self.grade = "C"

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        sx = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0
        sy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0.0
        
        bg = "#f3f3f3" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0+sx, 0+sy, WIDTH+sx, HEIGHT+sy, fill=bg)

        # Counter Floor
        canvas.create_rectangle(0+sx, 0+sy, WIDTH+sx, 120+sy, fill="#bdc3c7", outline="")

        # Stations
        for name, pos, color in [("RECIPE BOOK", self.book_pos, "#8e44ad"), 
                                 ("PANTRY", self.pantry_pos, "#d35400"), 
                                 ("PREP", self.prep_pos, "#27ae60"), 
                                 ("STOVE", self.stove_pos, "#c0392b")]:
             canvas.create_rectangle(pos[0]-45+sx, pos[1]-45+sy, pos[0]+45+sx, pos[1]+45+sy, fill=color, outline="#fff", width=2)
             canvas.create_text(pos[0]+sx, pos[1]+sy, text=name, fill="#fff", font=("Arial", 9, "bold"))
             
             # Draw progress rings if working here
             if self.active_order is not None and len(self.current_steps) > 0 and self.current_steps[0] == name:
                  if math.hypot(player.x - pos[0], player.y - pos[1]) < 50:
                       canvas.create_rectangle(pos[0]-40+sx, pos[1]+30+sy, pos[0]+40+sx, pos[1]+40+sy, fill="#fff")
                       canvas.create_rectangle(pos[0]-38+sx, pos[1]+32+sy, pos[0]-38+76*(self.step_progress/100)+sx, pos[1]+38+sy, fill="#f1c40f")

        # Customers
        for c in self.customers:
             cx, cy = c["x"]+sx, c["y"]+sy
             canvas.create_oval(cx-20, cy-20, cx+20, cy+20, fill="#34495e", outline="#fff")
             # Order bubble
             canvas.create_rectangle(cx-30, cy+25, cx+30, cy+45, fill="#fff", outline="#2c3e50")
             canvas.create_text(cx, cy+35, text=c["order"], fill="#2c3e50", font=("Arial", 8, "bold"))
             
             # Patience bar
             p_ratio = c["patience"] / c["max_patience"]
             p_color = "#2ecc71" if p_ratio > 0.5 else "#e67e22" if p_ratio > 0.25 else "#e74c3c"
             canvas.create_rectangle(cx-20, cy+50, cx+20, cy+55, fill="#111")
             canvas.create_rectangle(cx-20, cy+50, cx-20+40*p_ratio, cy+55, fill=p_color)

             # Active indicator
             if self.active_order == c["id"]:
                  canvas.create_oval(cx-25, cy-25, cx+25, cy+25, outline="#f1c40f", width=3)
                  if self.step_progress == -1:
                       canvas.create_text(cx, cy-35, text="DELIVER!", fill="#2ecc71", font=("Arial", 10, "bold"))
                  elif len(self.current_steps) == 0:
                       canvas.create_text(cx, cy-35, text="READ BOOK!", fill="#8e44ad", font=("Arial", 10, "bold"))
                  else:
                       canvas.create_text(cx, cy-35, text=f"GO TO {self.current_steps[0]}", fill="#e67e22", font=("Arial", 10, "bold"))

        player.draw(canvas)
        
        # HUD
        canvas.create_text(WIDTH-20, 150, anchor="e", text=f"CASH: ${self.money}", fill="#2ecc71", font=("Arial", 18, "bold"))

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

