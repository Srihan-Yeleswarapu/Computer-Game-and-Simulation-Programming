import random

WIDTH, HEIGHT = 960, 600
BG = "#0f1326"
TEXT = "#f5f6f7"
ACCENT = "#5fb6ff"
DANGER = "#ff5555"
SUCCESS = "#50fa7b"
GOLD = "#ffb86c"

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

class Audio:
    @staticmethod
    def play(sound_name: str):
        try:
             import pygame
             import os
             if pygame.mixer.get_init():
                 # Future expansion: load from src/assets/sounds/
                 pass 
        except:
             pass

class Particle:
    def __init__(self, x: float, y: float, color: str, vx: float, vy: float, life: float, size: float = 2.0):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def is_dead(self) -> bool:
        return self.life <= 0
