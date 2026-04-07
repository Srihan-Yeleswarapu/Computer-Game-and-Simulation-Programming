import math
import random
import tkinter as tk
from src.player import Player
from src.utils import HEIGHT, TEXT, WIDTH, clamp
from src.worlds.base import BaseWorld

class FireRescueWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Fire Rescue",
            summary="Navigate a burning building, save trapped survivors, and suppress flames.",
            duration=72.0,
        )
        self.briefing = [
            "RESCUE 5 survivors trapped in the industrial complex.",
            "LOCATE the yellow civilian icons deep in the smoke.",
            "HOLD near a survivor to free them, then CARRY a freed survivor.",
            "EVACUATE to the left-side Crew Door to deposit the survivor.",
            "USE SPACE to suppress flames. High heat exposure drains time fast."
        ]
        self.hints = [
            "Tip: You can only carry one survivor at a time.",
            "Tip: The left door is the only safe evacuation point.",
            "Tip: Flame proximity drains your mission timer – stay back if possible.",
            "Tip: Suppressed flames will stay out for a short period before reigniting."
        ]
        self.bounds = (120, 100, WIDTH - 120, HEIGHT - 100)
        self.DOOR_ZONE = (0, HEIGHT/2-70, 80, HEIGHT/2+70)
        self.flames = []
        self.smoke = []
        self.survivors = []
        self.saved = 0
        self.carrying = None
        self.heat = 0.0
        self.spread_cap = 25
        self.shake = 0.0

    def reset(self, player: Player) -> None:
        player.reset(self.bounds[0] + 40, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.carrying = None
        self.saved = 0
        self.heat = 0.0
        self.shake = 0.0
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        
        x1, y1, x2, y2 = self.bounds
        self.flames = []
        for _ in range(12):
            self.flames.append({
                "x": random.uniform(x1 + 100, x2 - 50),
                "y": random.uniform(y1 + 50, y2 - 50),
                "dx": random.choice([-1, 1]) * random.uniform(60, 110),
                "dy": random.choice([-1, 1]) * random.uniform(50, 100),
                "r": random.uniform(18, 28),
                "spread": random.uniform(5.5, 9.5)
            })
            
        self.smoke = []
        for _ in range(15):
            self.smoke.append({
                "x": random.uniform(x1, x2),
                "y": random.uniform(y1, y2),
                "r": random.uniform(20, 50),
                "rise": random.uniform(40, 90)
            })
            
        self.survivors = []
        for i in range(5):
            self.survivors.append({
                "x": random.uniform(x1 + 150, x2 - 40),
                "y": random.uniform(y1 + 40, y2 - 40),
                "state": "trapped",
                "progress": 0.0
            })

    def get_adaptive_hint(self, player: Player) -> tuple[str, tuple[float, float] | None]:
        if self.carrying:
            dist_door = math.hypot(player.x - 40, player.y - HEIGHT/2)
            if dist_door > 80:
                return ("Survivor on board! Carry them to the Fire Exit (left door) for immediate evacuation.", (40.0, HEIGHT/2.0))
            else:
                return ("Evacuate! Drop the survivor at the exit zone to clear them.", (20.0, HEIGHT/2.0))
                
        trapped = [s for s in self.survivors if s["state"] == "trapped"]
        if trapped:
             survivor = min(trapped, key=lambda s: math.hypot(player.x - s["x"], player.y - s["y"]))
             dist_s = math.hypot(player.x - survivor["x"], player.y - survivor["y"])
             target_pos = (float(survivor["x"]), float(survivor["y"]))
             if dist_s > 80:
                  return ("Search and Rescue: Locate trapped civilians (yellow) deep in the burning structure.", target_pos)
             else:
                  return ("Victim located! Stay near the survivor until you can lift them for evacuation.", target_pos)

        freed = [s for s in self.survivors if s["state"] == "freed"]
        if freed:
             survivor = min(freed, key=lambda s: math.hypot(player.x - s["x"], player.y - s["y"]))
             return ("Survivor is mobile. Move to them to pick them up for transport to the exit.", (float(survivor["x"]), float(survivor["y"])))

        if self.flames:
             nearest_flame = min(self.flames, key=lambda f: math.hypot(player.x - f["x"], player.y - f["y"]))
             return ("Fire Containment: Use your hose (SPACE) to clear paths and suppress the spread.", (float(nearest_flame["x"]), float(nearest_flame["y"])))
                  
        return ("Fire contained. Monitor for hot spots and maintain structural safety.", None)

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        player.update(dt, keys, self.bounds)
        self.update_adaptive_guidance(dt, player, keys)

        # Update environment
        x1, y1, x2, y2 = self.bounds
        for flame in self.flames:
            flame["x"] += flame["dx"] * dt
            flame["y"] += flame["dy"] * dt
            if flame["x"] < x1 + 10 or flame["x"] > x2 - 20: flame["dx"] *= -1
            if flame["y"] < y1 + 10 or flame["y"] > y2 - 10: flame["dy"] *= -1
            flame["spread"] -= dt
            if flame["spread"] <= 0 and len(self.flames) < self.spread_cap:
                flame["spread"] = random.uniform(7.0, 11.0)
                self.flames.append({
                    "x": clamp(flame["x"] + random.uniform(-30, 30), x1 + 20, x2 - 20),
                    "y": clamp(flame["y"] + random.uniform(-30, 30), y1 + 20, y2 - 20),
                    "dx": random.choice([-1, 1]) * random.uniform(70, 120),
                    "dy": random.choice([-1, 1]) * random.uniform(60, 110),
                    "r": clamp(flame["r"] + random.uniform(-4, 6), 14, 34),
                    "spread": random.uniform(7.0, 11.0)
                })

        for puff in self.smoke:
            puff["y"] -= puff["rise"] * dt
            if puff["y"] < y1 - 40:
                puff["y"] = y2 + random.uniform(10, 40)
                puff["x"] = random.uniform(x1, x2)

        # Interaction
        if not self.carrying:
            for s in self.survivors:
                dist = math.hypot(player.x - s["x"], player.y - s["y"])
                if s["state"] == "trapped" and dist < 60:
                    s["state"] = "freeing"
                elif s["state"] == "freeing" and dist >= 60:
                    s["state"] = "trapped"
                
                if s["state"] == "freeing":
                    s["progress"] = min(1.0, s["progress"] + dt * 0.45)
                    if s["progress"] >= 1.0: s["state"] = "freed"
                
                if s["state"] == "freed" and dist < 30:
                    self.carrying = s
                    s["state"] = "carried"

        if self.carrying:
            self.carrying["x"], self.carrying["y"] = player.x, player.y - 12
            dx1, dy1, dx2, dy2 = self.DOOR_ZONE
            if dx1 <= player.x <= dx2 and dy1 <= player.y <= dy2:
                self.carrying["state"] = "saved"
                self.carrying = None
                self.saved += 1
                self.message = f"Survivor evacuated! {self.saved}/5 secure."

        if "space" in keys:
             self.flames = [f for f in self.flames if math.hypot(player.x - f["x"], player.y - f["y"]) > 65]

        # Damage
        for f in self.flames:
            if math.hypot(player.x - f["x"], player.y - f["y"]) < player.size + f["r"]:
                self.heat += dt * 35
                self.shake = 4.0
                self.timer = max(0.0, self.timer - dt * 2)

        if self.timer <= 0:
            self.finished = True
            self.success = self.saved >= 2
            if self.success:
                self.grade = "A" if self.saved >= 4 else "B" if self.saved >= 3 else "C"
                self.message = f"Shift Over! {self.saved}/5 rescued."
            else:
                self.grade = "F"
                self.message = "The complex was lost to the inferno."

        if self.saved >= 5:
            self.finished, self.success, self.grade = True, True, "S"
            self.message = "Outstanding! All 5 civilians saved."

        self.draw(canvas, player)

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        x1, y1, x2, y2 = self.bounds
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#1c2533")
        canvas.create_rectangle(x1, y1, x2, y2, fill="#2c3444", outline="#4e5b75", width=3)
        
        dx1, dy1, dx2, dy2 = self.DOOR_ZONE
        canvas.create_rectangle(dx1, dy1, dx2, dy2, fill="#d63031", outline="#ff7675", width=3)
        canvas.create_text(dx1 + 40, dy1 - 15, text="CREW EXIT", fill="#ff9f43", font=("Helvetica", 14, "bold"))

        for s in self.survivors:
            if s["state"] == "saved": continue
            sx, sy = s["x"], s["y"]
            col = "#f1c40f" if s["state"] in ("trapped", "freeing") else "#2ecc71"
            canvas.create_oval(sx-12, sy-12, sx+12, sy+12, fill=col, outline="#fff")
            if s["state"] == "freeing":
                canvas.create_rectangle(sx-15, sy+15, sx+15, sy+20, fill="#333")
                canvas.create_rectangle(sx-15, sy+15, sx-15+30*s["progress"], sy+20, fill="#f1c40f")

        for f in self.flames:
            canvas.create_oval(f["x"]-f["r"], f["y"]-f["r"], f["x"]+f["r"], f["y"]+f["r"], fill="#ff5e3a", outline="#ffbd45", width=2)
            
        player.draw(canvas)
        self.draw_hud(canvas)
        if self.finished: self.draw_result(canvas)
