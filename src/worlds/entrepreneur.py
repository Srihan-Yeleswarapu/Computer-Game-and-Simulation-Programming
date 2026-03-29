import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class EntrepreneurWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Cashflow Entrepreneur",
            summary="Achieve financial freedom by building passive income",
            duration=90.0,
        )
        self.briefing = [
             "FINANCIAL CHALLENGE: Get out of the Rat Race!",
             "Collect ASSETS to build your passive income.",
             "Avoid LIABILITIES and DOODADS that drain your cash.",
             "Your goal is to make your Passive Income exceed your Expenses.",
             "Monopoly strategy: Buy high-ROI assets first!"
        ]
        self.hints = [
             "Tip: Green items are ASSETS (Passive Income up).",
             "Tip: Red items are LIABILITIES (Expenses up).",
             "Tip: Gold items are OPPORTUNITIES (Cash injection).",
             "Tip: Balance your cash flow to win."
        ]
        self.cash = 1000
        self.passive_income = 0
        self.expenses = 500
        self.items: list[dict[str, Any]] = []
        self.item_spawn_timer = 1.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.cash = 1000
        self.passive_income = 0
        self.expenses = 500
        self.items = []
        self.item_spawn_timer = 1.0
        self.shake = 0.0
        self.particles = []

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)

        # Monthly Cashflow every 5 seconds
        if int(self.timer) % 5 == 0 and int(self.timer - dt) % 5 != 0:
             self.cash += (self.passive_income - self.expenses)
             if self.cash < 0: self.cash = 0

        # Spawn items
        self.item_spawn_timer -= dt
        if self.item_spawn_timer <= 0:
            self.item_spawn_timer = random.uniform(1.0, 2.5)
            r = random.random()
            if r < 0.4: # Asset
                 typ = "ASSET"; color = "#2ecc71"; cost = 500; val = 150
            elif r < 0.7: # Liability
                 typ = "LIABILITY"; color = "#e74c3c"; cost = 0; val = 100 # val is expense increase
            else: # Doodad/Opp
                 typ = "OPPORTUNITY"; color = "#f1c40f"; cost = 0; val = 400
            
            self.items.append({
                "x": random.uniform(50, WIDTH-50),
                "y": random.uniform(50, HEIGHT-50),
                "type": typ,
                "color": color,
                "cost": cost,
                "val": val,
                "timer": 6.0
            })

        new_items = []
        for it in self.items:
            it["timer"] -= dt
            # Interaction
            if math.hypot(player.x - it["x"], player.y - it["y"]) < 40:
                if it["type"] == "ASSET":
                    if self.cash >= it["cost"]:
                        self.cash -= it["cost"]
                        self.passive_income += it["val"]
                elif it["type"] == "LIABILITY":
                    self.expenses += it["val"]
                    self.shake = 2.0
                elif it["type"] == "OPPORTUNITY":
                    self.cash += it["val"]
            elif it["timer"] > 0:
                new_items.append(it)
        self.items = new_items

        if self.passive_income > self.expenses:
            self.finished = True
            self.success = True
            self.message = "Financial Freedom! You have exited the rat race."
            # Grade based on surplus
            surplus = self.passive_income - self.expenses
            if surplus > 1000: self.grade = "S"
            elif surplus > 500: self.grade = "A"
            else: self.grade = "B"

        if self.timer <= 0:
            self.finished = True
            self.success = False
            self.message = "Stuck in the Rat Race! Time ran out."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        # Monopoly board style background
        bg = "#e8f5e9" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)
        
        # Board segments
        for i in range(0, WIDTH, 100):
             canvas.create_line(i, 0, i, 50, fill="#aaa")
             canvas.create_line(i, HEIGHT-50, i, HEIGHT, fill="#aaa")
        for i in range(0, HEIGHT, 100):
             canvas.create_line(0, i, 50, i, fill="#aaa")
             canvas.create_line(WIDTH-50, i, WIDTH, i, fill="#aaa")

        for it in self.items:
            canvas.create_rectangle(it["x"]-25, it["y"]-25, it["x"]+25, it["y"]+25, fill=it["color"], outline="#fff", width=2)
            canvas.create_text(it["x"], it["y"], text=it["type"][0], fill="#fff", font=("Arial", 12, "bold"))
            if it["type"] == "ASSET":
                 canvas.create_text(it["x"], it["y"]+35, text=f"${it['cost']}", fill="#27ae60", font=("Arial", 8, "bold"))

        player.draw(canvas)
        
        # HUD
        canvas.create_rectangle(10, 60, 300, 160, fill="#2c3e50", outline="#ecf0f1", width=2)
        canvas.create_text(20, 80, anchor="w", text=f"Cash: ${int(self.cash)}", fill="#f1c40f", font=("Arial", 12, "bold"))
        canvas.create_text(20, 105, anchor="w", text=f"Passive Income: ${self.passive_income}", fill="#2ecc71", font=("Arial", 11, "bold"))
        canvas.create_text(20, 130, anchor="w", text=f"Expenses: ${self.expenses}", fill="#e74c3c", font=("Arial", 11, "bold"))
        
        # Progress Bar to Freedom
        canvas.create_rectangle(20, 145, 280, 155, fill="#111")
        progress = clamp(self.passive_income / max(1.0, self.expenses), 0.0, 1.0)
        canvas.create_rectangle(22, 147, 22 + 256*progress, 153, fill="#2ecc71")

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

