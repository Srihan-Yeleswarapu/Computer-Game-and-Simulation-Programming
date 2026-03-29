import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class StartupFounderWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Startup Founder",
            summary="Achieve profitability by balancing equity and expenses",
            duration=90.0,
        )
        self.briefing = [
             "STARTUP CHALLENGE: Break even to survive!",
             "Collect EQUITY to build your recurring revenue.",
             "Avoid DEBT and LIFESTYLE BLOAT that drain your cash.",
             "Your goal is to make your Monthly Revenue exceed your Burn Rate.",
             "Venture Strategy: Invest in high-growth equity first!"
        ]
        self.hints = [
             "Tip: Green items are EQUITY (Revenue up).",
             "Tip: Red items are DEBT (Burn Rate up).",
             "Tip: Gold items are VENTURE CAP (Cash injection).",
             "Tip: Balance your cash flow to win."
        ]
        self.cash = 1000
        self.tutorial_timer = 4.0
        self.revenue = 0
        self.burn_rate = 500
        self.items: list[dict[str, Any]] = []
        self.item_spawn_timer = 1.0

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.cash = 1000
        self.revenue = 0
        self.burn_rate = 500
        self.items = []
        self.item_spawn_timer = 1.0
        self.shake = 0.0
        self.particles = []

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        self.tick_timer(dt)
        if self.tutorial_timer > 0:
            self.draw(canvas, player)
            return
            
        player.update(dt, keys, self.bounds)

        # Monthly Cashflow every 5 seconds
        if int(self.timer) % 5 == 0 and int(self.timer - dt) % 5 != 0:
             self.cash += (self.revenue - self.burn_rate)
             if self.cash < 0: self.cash = 0

        # Spawn items
        self.item_spawn_timer -= dt
        if self.item_spawn_timer <= 0:
            self.item_spawn_timer = random.uniform(1.0, 2.5)
            r = random.random()
            if r < 0.4: # Equity
                 typ = "EQUITY"; color = "#2ecc71"; cost = 500; val = 150
            elif r < 0.7: # Debt
                 typ = "DEBT"; color = "#e74c3c"; cost = 0; val = 100 
            else: # Venture
                 typ = "VENTURE CAP"; color = "#f1c40f"; cost = 0; val = 400
            
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
        
        # Monthly finance cycle
        self.cash += (self.revenue - self.burn_rate) * dt * 0.5
        self.valuation = (self.revenue * 12) * (1 + self.market_share/100)

        # Spawn task opportunities
        if random.random() < 1.0 * dt:
            self.tasks.append({"x": random.uniform(100, WIDTH-100), "y": random.uniform(100, HEIGHT-200), "value": random.randint(50, 200)})

        new_tasks = []
        self.tasks = new_tasks
        for t in new_tasks:
            if math.hypot(player.x - t["x"], player.y - t["y"]) < 40:
                self.cash += t["value"]
                self.market_share += 0.1
            else:
                new_tasks.append(t)
        self.tasks = new_tasks

        # Upgrade collisions
        for u in self.upgrades:
            if self.cash >= u["cost"] and math.hypot(player.x - u["x"], player.y - u["y"]) < 50:
                 if "space" in keys:
                      self.cash -= u["cost"]
                      self.revenue += u.get("rev_boost", 0)
                      self.market_share += u.get("market_boost", 0)
                      self.burn_rate += u.get("burn_inc", 0)
                      u["cost"] = int(u["cost"] * 1.5) # Increase cost for next time
                      self.shake = 3.0

        if self.cash <= 0:
            self.finished = True
            self.success = False
            self.message = "Bankrupt! The startup ran out of runway."
            self.grade = "F"

        if self.timer <= 0:
            self.finished = True
            self.success = self.cash > 0
            if self.success:
                self.message = f"Shift Over! Valuation: ${int(self.valuation)}. Cash: ${int(self.cash)}"
                self.grade = self.calculate_grade()
            else:
                self.message = "Failed to secure the business model."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#1e272e" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)

        # Draw tasks
        for t in self.tasks:
             canvas.create_oval(t["x"]-15, t["y"]-15, t["x"]+15, t["y"]+15, fill="#2ed573", outline="#fff")
             canvas.create_text(t["x"], t["y"], text="$", fill="#fff", font=("Arial", 10, "bold"))

        # Draw upgrades
        for u in self.upgrades:
             color = "#f1c40f" if self.cash >= u["cost"] else "#7f8c8d"
             canvas.create_rectangle(u["x"]-60, u["y"]-40, u["x"]+60, u["y"]+40, outline=color, width=2)
             canvas.create_text(u["x"], u["y"]-15, text=u["name"], fill=color, font=("Arial", 10, "bold"))
             canvas.create_text(u["x"], u["y"]+10, text=f"${u['cost']}", fill=color, font=("Arial", 12, "bold"))

        player.draw(canvas)
        
        # HUD
        canvas.create_rectangle(10, 60, 300, 160, fill="#2c3e50", outline="#ecf0f1", width=2)
        canvas.create_text(20, 80, anchor="w", text=f"Cash: ${int(self.cash)}", fill="#f1c40f", font=("Arial", 12, "bold"))
        canvas.create_text(20, 105, anchor="w", text=f"Monthly Revenue: ${self.revenue}", fill="#2ecc71", font=("Arial", 11, "bold"))
        canvas.create_text(20, 130, anchor="w", text=f"Burn Rate: ${self.burn_rate}", fill="#e74c3c", font=("Arial", 11, "bold"))
        
        # Profitability Bar
        canvas.create_rectangle(20, 145, 280, 155, fill="#111")
        progress = clamp(self.revenue / max(1.0, self.burn_rate), 0.0, 1.0)
        canvas.create_rectangle(22, 147, 22 + 256*progress, 153, fill="#2ecc71")

        if self.finished:
            self.draw_result(canvas)
        self.draw_hud(canvas)

