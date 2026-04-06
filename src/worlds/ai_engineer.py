import random
import math
import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import WIDTH, HEIGHT, clamp
from src.worlds.base import BaseWorld

class AIEngineerWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="AI Engineer",
            summary="Review datasets, filter out bias, and collect enough quality data to train your model.",
            duration=120.0,
        )
        self.briefing = [
            "REVIEW 20 datasets to train your AI model.",
            "ADD (D or Right) datasets with High Credibility and Low Bias.",
            "DISCARD (A or Left) low-quality or highly biased data.",
            "TRAIN (SPACE) once all files are reviewed."
        ]
        self.hints = [
            "Tip: Bias heavily hurts your model. Avoid highly biased datasets.",
            "Tip: You need a decent amount of Total Size, so don't discard everything!",
            "Tip: Credibility and Peer Review increase your data score."
        ]
        
        self.data_templates = [
            {"title": "Global Climate Records", "body": "Verified satellite and ground temperature readings from multiple space agencies.", "cred": (85, 100), "peer": (80, 100), "size": (60, 90), "bias": (5, 15)},
            {"title": "Social Media Sentiments", "body": "A massive scrape of public user posts regarding consumer retail brands.", "cred": (30, 50), "peer": (10, 30), "size": (80, 100), "bias": (60, 85)},
            {"title": "Anonymized Medical Scans", "body": "MRI datasets provided by partnered hospitals for diagnostic AI research.", "cred": (90, 100), "peer": (80, 95), "size": (40, 70), "bias": (5, 20)},
            {"title": "Conspiracy Forum Dumps", "body": "Unmoderated internet forum posts discussing alternative histories and theories.", "cred": (5, 20), "peer": (0, 5), "size": (70, 95), "bias": (85, 100)},
            {"title": "Academic Physics Papers", "body": "Decades of peer-reviewed publications on quantum mechanics.", "cred": (95, 100), "peer": (95, 100), "size": (30, 60), "bias": (0, 10)},
            {"title": "Online Product Reviews", "body": "Web-scraped e-commerce reviews. Contains some bot-generated text.", "cred": (45, 65), "peer": (15, 30), "size": (85, 100), "bias": (50, 70)},
            {"title": "Synthesized Voice Lines", "body": "AI-generated voice patterns based on public domain audiobooks.", "cred": (60, 80), "peer": (40, 60), "size": (75, 95), "bias": (20, 40)},
            {"title": "Stock Market Tickers", "body": "Historical financial data from the top 500 companies over 20 years.", "cred": (85, 95), "peer": (70, 85), "size": (65, 85), "bias": (15, 30)},
            {"title": "Celebrity Gossip Blogs", "body": "Tabloid articles and rumors covering pop culture icons.", "cred": (15, 35), "peer": (0, 10), "size": (70, 90), "bias": (70, 95)},
            {"title": "Open Source Code", "body": "Millions of commits from popular software repositories.", "cred": (75, 90), "peer": (60, 80), "size": (90, 100), "bias": (10, 25)},
        ]
        
        self.max_cards = 20
        self.current_card_index = 0
        self.cards: list[dict[str, Any]] = []
        self.selected_cards: list[dict[str, Any]] = []
        
        self.state = "reviewing" # reviewing, ready_to_train, training, done
        self.training_progress = 0.0
        self.accuracy = 0.0

    def reset(self, player: Player) -> None:
        player.reset(-100, -100) # Hide player offscreen or ignore them
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.grade = "-"
        
        self.current_card_index = 0
        self.cards = []
        self.selected_cards = []
        self.state = "reviewing"
        self.training_progress = 0.0
        self.accuracy = 0.0
        
        # Generate 20 random cards
        for _ in range(self.max_cards):
            template = random.choice(self.data_templates)
            self.cards.append({
                "title": template["title"],
                "body": template["body"],
                "cred": int(random.uniform(*template["cred"])),
                "peer": int(random.uniform(*template["peer"])),
                "size": int(random.uniform(*template["size"])),
                "bias": int(random.uniform(*template["bias"])),
            })

    def just_pressed(self, keys: set[str], key: str) -> bool:
        if not hasattr(self, '_last_keys'):
            self._last_keys = set()
        is_pressed = key in keys and key not in self._last_keys
        return is_pressed

    def evaluate_model(self) -> float:
        if not self.selected_cards:
            return 0.0
            
        total_score = 0
        total_size = 0
        
        for card in self.selected_cards:
            # Score formula per card:
            # High cred and peer are good. High bias is bad.
            # Max possible quality score per card ~ 100 (Cred) + 100 (Peer) + 100 (100 - Bias) = 300
            quality = card["cred"] + card["peer"] + (100 - card["bias"])
            card_score = quality / 3.0 # Maps to roughly 0-100 quality
            
            total_score += card_score * card["size"]
            total_size += card["size"]
            
        if total_size == 0:
            return 0.0
            
        # Average quality weighted by size
        avg_quality = total_score / float(total_size)
        
        # Penalize if total size is too small (need at least ~300 total size for a solid model)
        size_penalty = min(1.0, total_size / 350.0)
        
        accuracy = avg_quality * size_penalty
        return clamp(accuracy, 0.0, 100.0)

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        
        if self.state == "reviewing":
            if self.current_card_index < self.max_cards:
                if self.just_pressed(keys, "d") or self.just_pressed(keys, "Right"):
                    self.selected_cards.append(self.cards[self.current_card_index])
                    self.current_card_index += 1
                elif self.just_pressed(keys, "a") or self.just_pressed(keys, "Left"):
                    self.current_card_index += 1
                    
            if self.current_card_index >= self.max_cards:
                self.state = "ready_to_train"
                
        elif self.state == "ready_to_train":
            if self.just_pressed(keys, "space"):
                self.state = "training"
                self.accuracy = self.evaluate_model()
                
        elif self.state == "training":
            self.training_progress += dt * 35.0 # Takes ~3 seconds to train
            if self.training_progress >= 100.0:
                self.state = "done"
                
        elif self.state == "done":
            self.finished = True
            self.success = self.accuracy >= 65.0
            self.message = f"Training Complete! Model Accuracy: {self.accuracy:.1f}%"
            
            if self.accuracy >= 90.0:
                self.grade = "S"
            elif self.accuracy >= 75.0:
                self.grade = "A"
            elif self.accuracy >= 65.0:
                self.grade = "B"
            else:
                self.grade = "C"

        if not hasattr(self, '_last_keys'):
            self._last_keys = set()
        self._last_keys = keys.copy()
        
        if self.timer <= 0 and not self.finished:
            self.finished = True
            self.success = False
            self.message = "Deadline missed! Model was not trained in time."
            self.grade = "F"

        self.update_particles(dt)
        self.draw(canvas, player)

    def draw_bar(self, canvas: tk.Canvas, x: float, y: float, w: float, h: float, val: int, color: str, label: str) -> None:
        canvas.create_rectangle(x, y, x + w, y + h, fill="#2a3b4c", outline="#445c75")
        canvas.create_rectangle(x + 2, y + 2, x + 2 + (w - 4) * (val / 100.0), y + h - 2, fill=color, outline="")
        canvas.create_text(x + w + 10, y + h/2, anchor="w", text=f"{label}: {val}", fill="#cdd9e5", font=("Helvetica", 10, "bold"))

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        bg = "#111822" if not self.high_contrast else "#000000"
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)
        
        # Header
        canvas.create_rectangle(0, 0, WIDTH, 50, fill="#0d141e", outline="")
        canvas.create_text(20, 25, anchor="w", text="AI Data Engineer Workspace", fill="#5fb6ff", font=("Helvetica", 16, "bold"))
        canvas.create_text(WIDTH - 20, 25, anchor="e", text=f"Time: {max(0, self.timer):.1f}s", fill="#ff5555", font=("Helvetica", 12, "bold"))
        
        if self.state == "reviewing":
            canvas.create_text(WIDTH/2, 80, text=f"Reviewing Dataset {self.current_card_index + 1} of {self.max_cards}", fill="#cdd9e5", font=("Helvetica", 14, "bold"))
            
            # Draw Data Card
            if self.current_card_index < self.max_cards:
                card = self.cards[self.current_card_index]
                
                cx, cy = WIDTH/2, HEIGHT/2
                cw, ch = 480, 280
                
                # Card Background
                canvas.create_rectangle(cx - cw/2, cy - ch/2, cx + cw/2, cy + ch/2, fill="#1c2838", outline="#5fb6ff", width=2)
                
                # Title & Body
                canvas.create_text(cx, cy - ch/2 + 30, text=card["title"], fill="#ffffff", font=("Helvetica", 18, "bold"))
                canvas.create_text(cx, cy - ch/2 + 70, text=card["body"], fill="#9ab6d1", font=("Helvetica", 11), width=cw - 40, justify="center")
                
                # Attribute Bars
                bar_start_y = cy - 20
                bar_x = cx - 180
                bar_w = 200
                
                self.draw_bar(canvas, bar_x, bar_start_y, bar_w, 16, card["cred"], "#50fa7b", "Credibility")
                self.draw_bar(canvas, bar_x, bar_start_y + 30, bar_w, 16, card["peer"], "#8be9fd", "Peer Review")
                self.draw_bar(canvas, bar_x, bar_start_y + 60, bar_w, 16, card["size"], "#f1fa8c", "Data Size")
                self.draw_bar(canvas, bar_x, bar_start_y + 90, bar_w, 16, card["bias"], "#ff5555", "Bias Level")
                
                # Controls
                canvas.create_text(cx - 140, cy + ch/2 + 30, text="[A] / [Left Arrow] DISCARD", fill="#ff5555", font=("Helvetica", 12, "bold"))
                canvas.create_text(cx + 140, cy + ch/2 + 30, text="[D] / [Right Arrow] ADD", fill="#50fa7b", font=("Helvetica", 12, "bold"))
                
        elif self.state == "ready_to_train":
            canvas.create_text(WIDTH/2, HEIGHT/2 - 40, text=f"Data Selection Complete! ({len(self.selected_cards)} datasets added)", fill="#ffffff", font=("Helvetica", 18, "bold"))
            canvas.create_rectangle(WIDTH/2 - 120, HEIGHT/2 + 10, WIDTH/2 + 120, HEIGHT/2 + 60, fill="#5fb6ff", outline="")
            canvas.create_text(WIDTH/2, HEIGHT/2 + 35, text="Press [SPACE] to Train", fill="#000000", font=("Helvetica", 14, "bold"))
            
        elif self.state == "training":
            canvas.create_text(WIDTH/2, HEIGHT/2 - 40, text="Training AI Model...", fill="#ffffff", font=("Helvetica", 18, "bold"))
            
            # Progress bar
            pw = 400
            canvas.create_rectangle(WIDTH/2 - pw/2, HEIGHT/2, WIDTH/2 + pw/2, HEIGHT/2 + 20, fill="#2a3b4c", outline="#5fb6ff")
            canvas.create_rectangle(WIDTH/2 - pw/2 + 2, HEIGHT/2 + 2, WIDTH/2 - pw/2 + 2 + (pw-4) * (self.training_progress/100.0), HEIGHT/2 + 18, fill="#50fa7b", outline="")
            
        elif self.state == "done":
            # Just rendering the background info, handled by draw_result
            pass
            
        if self.finished:
            self.draw_result(canvas)
